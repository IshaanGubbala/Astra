from backend.connector_sync_ledger import (
    connector_sync_metrics,
    get_connector_sync_status,
    record_connector_sync,
    record_connector_webhook,
)
from backend.tools.company_brain_connectors import import_company_brain_source


def test_connector_sync_ledger_tracks_import_and_webhook(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_sync"

    first = record_connector_sync(
        founder_id,
        "slack",
        status="ok",
        imported=3,
        changed_records=2,
        cursor="cursor_1",
    )
    assert first["status"] == "ok"
    assert first["total_imported"] == 3
    assert first["cursor"] == "cursor_1"

    webhook = record_connector_webhook(
        founder_id,
        "slack",
        event_id="evt_1",
        event_type="message.created",
        changed_records=1,
    )
    assert webhook["webhook_events"] == 1
    assert webhook["total_imported"] == 4
    assert webhook["cursor"] == "evt_1"

    status = get_connector_sync_status(founder_id)
    assert status["sources"]["slack"]["last_success_at"]
    assert status["sources"]["slack"]["history"][0]["mode"] == "webhook"

    metrics = connector_sync_metrics()
    assert metrics["connector_ledgers"] == 1
    assert metrics["connector_sources"] == 1
    assert metrics["connector_webhook_events"] == 1


def test_connector_sync_ledger_records_importer_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = import_company_brain_source("founder_import_error", "unknown_source")
    assert result["ok"] is False

    status = get_connector_sync_status("founder_import_error")
    source = status["sources"]["unknown_source"]
    assert source["status"] == "error"
    assert "No importer implemented" in source["last_error"]
