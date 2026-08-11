#!/usr/bin/env python
from __future__ import annotations

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"


def check_and_remediate() -> bool:
    """Automated Watchdog: Monitors API metrics & SLOs, automatically auto-healing active incidents."""
    print("[Auto-Remediation Watchdog] Checking system health and SLO metrics...")

    with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
        # 1. Fetch health
        try:
            health_res = client.get("/health")
            health_data = health_res.json()
        except Exception as e:
            print(f"[ERROR] Cannot connect to API server at {BASE_URL}: {e}")
            return False

        # 2. Fetch metrics
        metrics_res = client.get("/metrics")
        metrics_data = metrics_res.json()

        incidents = health_data.get("incidents", {})
        active_incidents = [name for name, active in incidents.items() if active]
        p95_latency = metrics_data.get("latency_p95", 0)
        error_rate = metrics_data.get("error_rate_pct", 0.0)

        print(f"[METRICS] Latency P95: {p95_latency}ms | Error Rate: {error_rate}%")
        print(f"[INCIDENTS] Active: {active_incidents if active_incidents else 'None'}")

        if not active_incidents and p95_latency <= 2000 and error_rate <= 5.0:
            print("[OK] System health is good and operating within SLO targets (< 2000ms). No action required.")
            return True

        print("[WARN] SLO violation or active incident detected! Initiating Automated Self-Healing...")

        remediated_any = False
        for incident_name in active_incidents:
            print(f"[SELF-HEALING] Disabling active incident '{incident_name}'...")
            disable_res = client.post(f"/incidents/{incident_name}/disable")
            if disable_res.status_code == 200:
                print(f"[SUCCESS] Successfully remediated incident '{incident_name}'!")
                remediated_any = True
            else:
                print(f"[ERROR] Failed to disable incident '{incident_name}': {disable_res.text}")

        # Re-verify health after remediation
        health_after = client.get("/health").json()
        print(f"[STATUS] Incident state after remediation: {health_after.get('incidents')}")
        return remediated_any


if __name__ == "__main__":
    success = check_and_remediate()
    sys.exit(0 if success else 1)
