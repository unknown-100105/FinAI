import json
import os
import time
from pathlib import Path

from xai import trace as trace_module
from xai.trace import XAITrace


def test_trace_id_is_independent_of_caller_session_and_path_is_contained(tmp_path, monkeypatch):
    monkeypatch.setattr(trace_module, "TRACE_DIR", tmp_path)
    monkeypatch.setenv("FINAI_TRACE_RETENTION_DAYS", "0")
    monkeypatch.delenv("FINAI_TRACE_STORE_CONTENTS", raising=False)

    trace = XAITrace("../../outside")
    trace.set_user_input("My account number is 123456789")
    trace.record_tool({
        "tool": "account_lookup",
        "success": True,
        "message": "Account balance retrieved",
        "data": {"account_id": "123456789", "balance": 5000},
    })
    trace.record_final("tool", "TOOL_EXECUTED", "Account balance is 5000")
    saved_path = trace.save()

    assert trace.data["trace_id"].startswith("trace-")
    assert ".." not in trace.data["trace_id"]
    assert saved_path.resolve().parent == Path(tmp_path).resolve()
    persisted = json.loads(saved_path.read_text(encoding="utf-8"))
    assert persisted["user_input"] is None
    assert persisted["tool"]["data"] == {}
    assert persisted["tool"]["message"] is None
    assert persisted["final"]["message"] is None


def test_explicit_trace_content_storage_still_redacts_sensitive_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(trace_module, "TRACE_DIR", tmp_path)
    monkeypatch.setenv("FINAI_TRACE_RETENTION_DAYS", "0")
    monkeypatch.setenv("FINAI_TRACE_STORE_CONTENTS", "true")

    trace = XAITrace("local-demo")
    trace.record_tool({
        "tool": "account_lookup",
        "success": True,
        "data": {
            "account_id": "123456789",
            "balance": 5000,
            "currency": "INR",
        },
    })
    saved_path = trace.save()
    persisted = json.loads(saved_path.read_text(encoding="utf-8"))

    assert persisted["tool"]["data"]["account_id"] == "[REDACTED]"
    assert persisted["tool"]["data"]["balance"] == "[REDACTED]"
    assert persisted["tool"]["data"]["currency"] == "INR"


def test_trace_retention_removes_expired_files(tmp_path, monkeypatch):
    monkeypatch.setattr(trace_module, "TRACE_DIR", tmp_path)
    monkeypatch.setenv("FINAI_TRACE_RETENTION_DAYS", "7")
    monkeypatch.delenv("FINAI_TRACE_STORE_CONTENTS", raising=False)

    expired = tmp_path / "trace-expired.json"
    expired.write_text("{}", encoding="utf-8")
    old_time = time.time() - 9 * 86400
    os.utime(expired, (old_time, old_time))

    XAITrace("session-retention-test").save()

    assert not expired.exists()
