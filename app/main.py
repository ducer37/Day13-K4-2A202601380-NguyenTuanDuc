from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import flush_langfuse, tracing_enabled

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled()},
    )


@app.on_event("shutdown")
async def shutdown() -> None:
    # Flush buffered Langfuse events before the process exits.
    # Without this, events sent near shutdown are silently dropped.
    flush_langfuse()
    log.info("app_shutdown", service=os.getenv("APP_NAME", "day13-observability-lab"))


@app.get("/")
async def root() -> dict:
    return {
        "message": "Day 13 Observability Lab API is running",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/dashboard", response_class=JSONResponse)
async def dashboard_view() -> HTMLResponse:
    from fastapi.responses import HTMLResponse
    html_content = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Day 13 AI Observability Dashboard (Langfuse Style)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #090d16;
            --card-bg: #111827;
            --border-color: #1f2937;
            --text-main: #f9fafb;
            --text-sub: #9ca3af;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-pink: #ec4899;
            --accent-green: #10b981;
            --accent-red: #ef4444;
        }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 24px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }
        .title { font-size: 24px; font-weight: 700; color: var(--accent-cyan); display: flex; align-items: center; gap: 8px; }
        .meta { color: var(--text-sub); font-size: 14px; margin-top: 4px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 20px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .card-full {
            grid-column: 1 / -1;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .card-title { font-size: 16px; font-weight: 600; color: var(--text-main); }
        .badge {
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
        }
        .badge-ok { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-alert { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.3); }
        .metric-value { font-size: 32px; font-weight: 700; margin: 8px 0; }
        .metric-sub { font-size: 13px; color: var(--text-sub); }
        .metric-list { display: flex; gap: 12px; margin-top: 12px; }
        .sub-box {
            background: #0f172a;
            border: 1px solid var(--border-color);
            padding: 10px 14px;
            border-radius: 8px;
            flex: 1;
            text-align: center;
        }
        .sub-value { font-size: 20px; font-weight: 700; margin-top: 4px; }
        .chart-container {
            position: relative;
            height: 200px;
            width: 100%;
            margin-top: 16px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="title">⚡ Day 13 AI Observability Dashboard <span style="font-size:12px; background:#1e293b; color:#06b6d4; padding:2px 8px; border-radius:4px;">Langfuse Style UI</span></div>
            <div class="meta">Contract: config/dashboard.yaml | Refresh: 10s | Latency P95 SLO Target: &lt; 2000ms</div>
        </div>
        <button onclick="fetchMetrics()" style="background: var(--accent-cyan); border:none; color:#000; padding: 8px 16px; font-weight:700; border-radius:6px; cursor:pointer;">🔄 Refresh Now</button>
    </div>

    <div class="grid">
        <!-- 1. Latency Panel (Langfuse Style Cyan Bar Chart) -->
        <div class="card card-full">
            <div class="card-header">
                <div class="card-title">1. Latency (p95 / p50 / p99 Bar Chart - Langfuse Style)</div>
                <div id="badge-latency" class="badge badge-ok">SLO OK (&lt; 2000ms)</div>
            </div>
            
            <div class="metric-list">
                <div class="sub-box">
                    <div class="metric-sub">Single Value P50</div>
                    <div class="sub-value" id="val-p50" style="color: var(--accent-cyan);">0 ms</div>
                </div>
                <div class="sub-box">
                    <div class="metric-sub">Single Value P95 (SLO Target)</div>
                    <div class="sub-value" id="val-p95" style="color: var(--accent-purple);">0 ms</div>
                </div>
                <div class="sub-box">
                    <div class="metric-sub">Single Value P99</div>
                    <div class="sub-value" id="val-p99" style="color: var(--accent-pink);">0 ms</div>
                </div>
            </div>

            <div class="chart-container">
                <canvas id="latencyChart"></canvas>
            </div>
        </div>

        <!-- 2. Request Traffic Panel (Purple Bar Chart) -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">2. Request Traffic (Count)</div>
                <div class="badge badge-ok">LIVE</div>
            </div>
            <div class="metric-value" id="val-traffic" style="color: var(--accent-purple);">0</div>
            <div class="metric-sub">Total Processed Requests</div>
            <div class="chart-container" style="height: 120px;">
                <canvas id="trafficChart"></canvas>
            </div>
        </div>

        <!-- 3. Error Rate Panel -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">3. Error Rate & Breakdown</div>
                <div id="badge-error" class="badge badge-ok">0.0% Errors</div>
            </div>
            <div class="metric-value" id="val-error-rate">0.0%</div>
            <div class="metric-sub" id="val-error-breakdown">Error Breakdown: None</div>
        </div>

        <!-- 4. Cost Panel (Blue Bar Chart) -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">4. Cost Over Time ($)</div>
                <div class="badge badge-ok">Budget OK</div>
            </div>
            <div class="metric-value" id="val-total-cost" style="color: var(--accent-cyan);">$0.0000</div>
            <div class="metric-sub">Total USD | Avg/req: <span id="val-avg-cost">$0.0000</span></div>
            <div class="chart-container" style="height: 120px;">
                <canvas id="costChart"></canvas>
            </div>
        </div>

        <!-- 5. Tokens Panel -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">5. Input & Output Tokens</div>
                <div class="badge badge-ok">Usage OK</div>
            </div>
            <div class="metric-value" id="val-tokens-total">0</div>
            <div class="metric-list">
                <div class="sub-box"><div class="metric-sub">Tokens In</div><strong id="val-tokens-in">0</strong></div>
                <div class="sub-box"><div class="metric-sub">Tokens Out</div><strong id="val-tokens-out">0</strong></div>
            </div>
        </div>

        <!-- 6. Quality Proxy Panel -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">6. Quality Proxy Score</div>
                <div class="badge badge-ok">Quality High</div>
            </div>
            <div class="metric-value" id="val-quality" style="color: var(--accent-green);">0.00</div>
            <div class="metric-sub">Average Answer Quality Score (0.0 to 1.0)</div>
        </div>
    </div>

    <script>
        let latencyChart, trafficChart, costChart;

        function renderCharts(historyData) {
            const labels = historyData.map(h => h.time || ('Req #' + h.req_id));
            const latencies = historyData.map(h => h.latency_ms);
            const costs = historyData.map(h => h.cost_usd || 0.001);
            const counts = historyData.map((_, i) => i + 1);

            // 1. Latency Bar Chart (Cyan)
            const ctxLat = document.getElementById('latencyChart').getContext('2d');
            if (latencyChart) {
                latencyChart.data.labels = labels;
                latencyChart.data.datasets[0].data = latencies;
                latencyChart.update();
            } else {
                latencyChart = new Chart(ctxLat, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Latency p95 (ms)',
                                data: latencies,
                                backgroundColor: '#06b6d4',
                                hoverBackgroundColor: '#22d3ee',
                                borderRadius: 4,
                                barPercentage: 0.6
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: { grid: { display: false }, ticks: { color: '#6b7280' } },
                            y: { grid: { color: '#1f2937' }, ticks: { color: '#6b7280' }, beginAtZero: true }
                        },
                        plugins: { legend: { labels: { color: '#9ca3af' } } }
                    }
                });
            }

            // 2. Traffic Bar Chart (Purple)
            const ctxTraf = document.getElementById('trafficChart').getContext('2d');
            if (trafficChart) {
                trafficChart.data.labels = labels;
                trafficChart.data.datasets[0].data = counts;
                trafficChart.update();
            } else {
                trafficChart = new Chart(ctxTraf, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{ label: 'Count', data: counts, backgroundColor: '#a855f7', borderRadius: 3 }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { x: { display: false }, y: { display: false } },
                        plugins: { legend: { display: false } }
                    }
                });
            }

            // 3. Cost Bar Chart (Blue)
            const ctxCost = document.getElementById('costChart').getContext('2d');
            if (costChart) {
                costChart.data.labels = labels;
                costChart.data.datasets[0].data = costs;
                costChart.update();
            } else {
                costChart = new Chart(ctxCost, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{ label: 'Cost ($)', data: costs, backgroundColor: '#3b82f6', borderRadius: 3 }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { x: { display: false }, y: { display: false } },
                        plugins: { legend: { display: false } }
                    }
                });
            }
        }

        async function fetchMetrics() {
            try {
                const res = await fetch('/metrics');
                const data = await res.json();
                
                // 1. Latency Single Values
                document.getElementById('val-p50').innerText = data.latency_p50 + ' ms';
                document.getElementById('val-p95').innerText = data.latency_p95 + ' ms';
                document.getElementById('val-p99').innerText = data.latency_p99 + ' ms';
                
                const bLatency = document.getElementById('badge-latency');
                if (data.latency_p95 > 2000) {
                    bLatency.innerText = 'SLO VIOLATED (> 2000ms)';
                    bLatency.className = 'badge badge-alert';
                } else {
                    bLatency.innerText = 'SLO OK (< 2000ms)';
                    bLatency.className = 'badge badge-ok';
                }

                // Render Bar Charts
                if (data.latency_history && data.latency_history.length > 0) {
                    renderCharts(data.latency_history);
                }

                // 2. Traffic
                document.getElementById('val-traffic').innerText = data.traffic;

                // 3. Error
                const errPct = data.error_rate_pct || 0;
                document.getElementById('val-error-rate').innerText = errPct + '%';
                const bErr = document.getElementById('badge-error');
                bErr.innerText = errPct + '% Errors';
                bErr.className = errPct > 5 ? 'badge badge-alert' : 'badge badge-ok';
                const errBreakdown = JSON.stringify(data.error_breakdown || {});
                document.getElementById('val-error-breakdown').innerText = 'Breakdown: ' + errBreakdown;

                // 4. Cost
                document.getElementById('val-total-cost').innerText = '$' + (data.total_cost_usd || 0).toFixed(4);
                document.getElementById('val-avg-cost').innerText = '$' + (data.avg_cost_usd || 0).toFixed(4);

                // 5. Tokens
                const tIn = data.tokens_in_total || 0;
                const tOut = data.tokens_out_total || 0;
                document.getElementById('val-tokens-in').innerText = tIn;
                document.getElementById('val-tokens-out').innerText = tOut;
                document.getElementById('val-tokens-total').innerText = (tIn + tOut);

                // 6. Quality
                document.getElementById('val-quality').innerText = (data.quality_avg || 0).toFixed(2);

            } catch (err) {
                console.error('Error fetching metrics:', err);
            }
        }

        fetchMetrics();
        setInterval(fetchMetrics, 10000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    # Enrich structlog contextvars so every log line in this request automatically
    # carries the full request context — critical for Checkpoint 1
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=agent.model,
        env=os.getenv("APP_ENV", "dev"),
    )

    log.info(
        "request_received",
        service="api",
        payload={"message_preview": summarize_text(body.message)},
    )
    try:
        result = agent.run(
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            message=body.message,
        )
        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
            payload={"answer_preview": summarize_text(result.answer)},
        )
        return ChatResponse(
            answer=result.answer,
            correlation_id=request.state.correlation_id,
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
        )
    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
        )
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=500,
            content={"detail": error_type},
            headers={"x-request-id": correlation_id},
        )


from .audit import get_recent_audit_logs, log_audit_event


@app.get("/audit", response_class=JSONResponse)
async def audit_logs(limit: int = 50) -> dict:
    logs = get_recent_audit_logs(limit=limit)
    return {"total": len(logs), "audit_logs": logs}


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        log_audit_event(
            action="incident_enable",
            actor="admin",
            target=f"incident:{name}",
            status="success",
            details={"incident_name": name},
        )
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        log_audit_event(
            action="incident_enable",
            actor="admin",
            target=f"incident:{name}",
            status="error",
            details={"error": str(exc)},
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        log_audit_event(
            action="incident_disable",
            actor="admin",
            target=f"incident:{name}",
            status="success",
            details={"incident_name": name},
        )
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        log_audit_event(
            action="incident_disable",
            actor="admin",
            target=f"incident:{name}",
            status="error",
            details={"error": str(exc)},
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc