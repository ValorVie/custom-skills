from typer.testing import CliRunner

from script.commands import mem as mem_cmd
from script.main import app


runner = CliRunner()


def test_normalize_summaries_maps_memory_session_id():
    summaries = [
        {
            "memory_session_id": "ms-001",
            "request": "req",
            "created_at_epoch": 1,
        }
    ]

    normalized, skipped = mem_cmd._normalize_summaries_for_push(summaries)

    assert skipped == 0
    assert len(normalized) == 1
    assert normalized[0]["session_id"] == "ms-001"


def test_mem_push_uses_normalized_summary_session_id(monkeypatch):
    captured = {}

    monkeypatch.setattr(mem_cmd, "load_server_config", lambda: {"last_push_epoch": 0})
    monkeypatch.setattr(mem_cmd, "save_server_config", lambda *_args, **_kwargs: None)

    def _fake_query(sql, _params=()):
        if "FROM session_summaries" in sql:
            return [{"memory_session_id": "ms-123", "created_at_epoch": 1}]
        return []

    monkeypatch.setattr(mem_cmd, "query_local_db", _fake_query)

    def _fake_api_request(_config, _method, path, body=None, extra_headers=None):
        if path == "/api/sync/push":
            captured["body"] = body
            return {"server_epoch": 123, "stats": {}}
        return {}

    monkeypatch.setattr(mem_cmd, "api_request", _fake_api_request)

    result = runner.invoke(app, ["mem", "push"])

    assert result.exit_code == 0
    assert captured["body"]["summaries"][0]["session_id"] == "ms-123"


def test_mem_push_skips_invalid_summary_without_session_id(monkeypatch):
    monkeypatch.setattr(mem_cmd, "load_server_config", lambda: {"last_push_epoch": 0})
    monkeypatch.setattr(mem_cmd, "save_server_config", lambda *_args, **_kwargs: None)

    def _fake_query(sql, _params=()):
        if "FROM session_summaries" in sql:
            return [{"memory_session_id": None, "created_at_epoch": 1}]
        return []

    monkeypatch.setattr(mem_cmd, "query_local_db", _fake_query)

    def _should_not_call_api(*_args, **_kwargs):
        raise AssertionError("api_request should not be called when no valid payload")

    monkeypatch.setattr(mem_cmd, "api_request", _should_not_call_api)

    result = runner.invoke(app, ["mem", "push"])

    assert result.exit_code == 0
    assert "已略過 1 筆 summaries" in result.stdout


def test_mem_push_handles_invalid_api_key_with_hint(monkeypatch):
    monkeypatch.setattr(
        mem_cmd,
        "load_server_config",
        lambda: {
            "last_push_epoch": 0,
            "server_url": "https://example.com",
            "device_name": "my-device",
            "api_key": "cm_sync_xxx",
        },
    )

    def _fake_query(sql, _params=()):
        if "FROM sdk_sessions" in sql:
            return [{"content_session_id": "cs-1", "started_at_epoch": 1}]
        return []

    monkeypatch.setattr(mem_cmd, "query_local_db", _fake_query)
    monkeypatch.setattr(mem_cmd, "save_server_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        mem_cmd,
        "api_request",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError('HTTP 401: {"error":"Invalid API key"}')
        ),
    )

    result = runner.invoke(app, ["mem", "push"])

    assert result.exit_code == 1
    assert "API key 無效或已失效" in result.stdout
    assert (
        "ai-dev mem register --server https://example.com --name my-device"
        in result.stdout
    )


def test_mem_register_existing_device_prints_rotation_message(monkeypatch):
    monkeypatch.setattr(mem_cmd, "save_server_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        mem_cmd,
        "api_request",
        lambda *_args, **_kwargs: {
            "api_key": "cm_sync_new",
            "device_id": 7,
            "rotated": True,
        },
    )

    result = runner.invoke(
        app,
        [
            "mem",
            "register",
            "--server",
            "https://example.com",
            "--name",
            "my-device",
            "--admin-secret",
            "secret",
        ],
    )

    assert result.exit_code == 0
    assert "重新註冊成功" in result.stdout
