from backend.config import settings
from backend.tools.company_brain import get_company_brain, list_company_brain_founders
from backend.workflow_state import load_session_state


def test_company_brain_loads_from_storage_adapter_without_local_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "astra_storage_backend", "supabase")
    stored = {
        "founder_id": "founder_remote",
        "sources": {},
        "records": [{"title": "Remote strategy", "content": "Use Astra as the company brain.", "source": "notion"}],
        "relationships": [],
        "proposals": [],
    }
    monkeypatch.setattr(
        "backend.storage_adapter.load_document",
        lambda collection, key: stored if collection == "company_brains" and key == "founder_remote" else None,
    )

    brain = get_company_brain("founder_remote")

    assert brain["founder_id"] == "founder_remote"
    assert any(record["title"] == "Remote strategy" for record in brain["records"])


def test_company_brain_founder_listing_includes_storage_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "backend.storage_adapter.list_document_keys",
        lambda collection: ["founder_remote"] if collection == "company_brains" else [],
    )

    assert "founder_remote" in list_company_brain_founders()


def test_workflow_state_loads_from_storage_adapter_without_local_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    stored = {"session_id": "session_remote", "status": "done", "event_count": 9}
    monkeypatch.setattr(
        "backend.storage_adapter.load_document",
        lambda collection, key: stored if collection == "workflow_states" and key == "session_remote" else None,
    )

    state = load_session_state("session_remote")

    assert state == stored
