from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path("data/audit.jsonl")


def log_audit_event(
    action: str,
    actor: str = "system",
    target: str = "api",
    status: str = "success",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a security or administrative audit event to data/audit.jsonl."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    event = {
        "audit_id": f"aud-{uuid.uuid4().hex[:8]}",
        "ts": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "target": target,
        "status": status,
        "details": details or {},
    }

    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def get_recent_audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve the most recent audit events."""
    if not AUDIT_LOG_PATH.exists():
        return []

    logs: list[dict[str, Any]] = []
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return logs[-limit:]
