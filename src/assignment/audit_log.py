"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, tuple[float, str]] = {}
        self._latest_by_user: dict[str, str] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None):
        """TODO: store input + start timestamp keyed by request_id/user_id."""
        request_id = request_id or f"req-{uuid4().hex}"
        started = perf_counter()
        self._open[request_id] = (started, user_id)
        self._latest_by_user[user_id] = request_id
        self.logs.append({
            "request_id": request_id,
            "user_id": user_id,
            "event": "input",
            "layer": "input",
            "timestamp": utc_now_iso(),
            "processing_time_ms": 0.0,
            "text": text if isinstance(text, str) else str(text),
        })
        return request_id

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
        decision: str | None = None,
        reviewer_decision: str | None = None,
        reviewer_id: str | None = None,
        action: str | None = None,
    ):
        """TODO: store output, layer decision, latency; append to self.logs."""
        if request_id is None:
            request_id = self._latest_by_user.get(user_id) or f"req-{uuid4().hex}"
        opened = self._open.pop(request_id, None)
        latency_ms = (perf_counter() - opened[0]) * 1000 if opened else None
        effective_decision = reviewer_decision or decision
        entry = {
            "request_id": request_id,
            "user_id": user_id,
            "event": "output",
            "layer": layer or self.name,
            "timestamp": utc_now_iso(),
            "processing_time_ms": round(latency_ms, 3) if latency_ms is not None else None,
            "latency_ms": round(latency_ms, 3) if latency_ms is not None else None,
            "blocked": bool(blocked),
            "text": text if isinstance(text, str) else str(text),
            "decision": effective_decision,
            "action": action,
        }
        if effective_decision is not None:
            entry["reviewer_decision"] = effective_decision
        if reviewer_id is not None:
            entry["reviewer_id"] = reviewer_id
        self.logs.append(entry)
        return request_id

    def export_json(self, filepath: str = "outputs/audit_log.json"):
        """Write logs to disk (JSON array)."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.logs, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
