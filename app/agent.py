from __future__ import annotations

import time
from dataclasses import dataclass

from . import metrics
from .cost_optimization import optimize_context
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .prompt_management import resolve_prompt
from .tracing import get_langfuse_client, observe, tracing_enabled


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    # capture_input=False so we control exactly what goes into the trace input
    # (we use update_current_generation(input=...) to set only the user message).
    # capture_output=False likewise — we set it explicitly below.
    @observe(name="chat-response", as_type="generation", capture_input=False, capture_output=False)
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()

        # Retrieval step — nested under the generation as a retriever span
        raw_docs = self._retrieve(message)
        docs, opt_metrics = optimize_context(raw_docs)
        metrics.record_cost_savings(opt_metrics["cost_saved_usd"])

        langfuse_client = get_langfuse_client()
        prompt = resolve_prompt(
            langfuse_client,
            feature=feature,
            docs=docs,
            message=message,
            enabled=tracing_enabled(),
        )
        response = self.llm.generate(prompt.text)
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        # Set trace-level attributes: user, session, tags, and metadata
        from structlog.contextvars import get_contextvars
        trace_meta = {
            "prompt_name": prompt.name,
            "prompt_label": prompt.label,
            "prompt_version": prompt.version,
            "prompt_source": prompt.source,
        }

        cid = get_contextvars().get("correlation_id")
        if cid:
            trace_meta["correlation_id"] = cid

        langfuse_client.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, self.model],
            metadata=trace_meta,
        )
        # Set generation-level attributes: explicit input (only user message, not all
        # function args), output, model, token usage, and cost.
        langfuse_client.update_current_generation(
            input=summarize_text(message),   # explicit safe input — no PII args exposed
            output=response.text,
            model=self.model,
            metadata={
                "doc_count": len(docs),
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
                "prompt_fetch_error": prompt.fetch_error,
                "cost_saved_usd": opt_metrics["cost_saved_usd"],
                "cost_reduction_pct": opt_metrics["reduction_pct"],
            },

            usage_details={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            cost_details={"total": cost_usd},
            prompt=prompt.managed_prompt,
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    @observe(name="rag-retrieval", as_type="retriever")
    def _retrieve(self, query: str) -> list[str]:
        """Retrieve relevant documents. Traced as a 'retriever' span nested under
        the parent generation so Langfuse shows the span hierarchy correctly."""
        return retrieve(query)

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)