import json
from pathlib import Path

from backend.config import settings
from backend.storage_adapter import list_document_keys, load_document, mirror_document, schema_status, storage_status


def test_storage_adapter_local_mirror_writes_document(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "astra_storage_backend", "local")

    result = mirror_document("runs", "session_1", {"session_id": "session_1", "status": "done"})

    assert result["ok"] is True
    path = Path(result["local"]["path"])
    assert path.exists()
    payload = json.loads(path.read_text())
    assert payload["collection"] == "runs"
    assert payload["key"] == "session_1"
    assert payload["payload"]["status"] == "done"
    assert storage_status()["local_mirror_documents"] == 1


def test_storage_adapter_supabase_upsert_path(monkeypatch):
    calls = []

    class FakeExecute:
        def execute(self):
            calls.append(("execute",))

    class FakeTable:
        def upsert(self, document, on_conflict):
            calls.append((document, on_conflict))
            return FakeExecute()

    class FakeClient:
        def table(self, name):
            calls.append(("table", name))
            return FakeTable()

    monkeypatch.setattr(settings, "astra_storage_backend", "supabase")
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_key", "service-key")
    monkeypatch.setattr("backend.storage_adapter._supabase_client", lambda: FakeClient())

    result = mirror_document("accounts", "org_1", {"org_id": "org_1"})

    assert result["ok"] is True
    assert calls[0] == ("table", "astra_documents")
    assert calls[1][0]["collection"] == "accounts"
    assert calls[1][0]["key"] == "org_1"
    assert calls[1][1] == "collection,key"


def test_storage_adapter_supabase_loads_document(monkeypatch):
    class FakeExecute:
        data = [{"payload": {"founder_id": "founder_1", "records": [{"title": "Loaded"}]}}]

        def execute(self):
            return self

    class FakeQuery:
        def __init__(self):
            self.filters = []

        def select(self, columns):
            assert columns == "payload"
            return self

        def eq(self, key, value):
            self.filters.append((key, value))
            return self

        def limit(self, value):
            assert value == 1
            return self

        def execute(self):
            assert ("collection", "company_brains") in self.filters
            assert ("key", "founder_1") in self.filters
            return FakeExecute().execute()

    class FakeClient:
        def table(self, name):
            assert name == "astra_documents"
            return FakeQuery()

    monkeypatch.setattr(settings, "astra_storage_backend", "supabase")
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_key", "service-key")
    monkeypatch.setattr("backend.storage_adapter._supabase_client", lambda: FakeClient())

    loaded = load_document("company_brains", "founder_1")

    assert loaded["founder_id"] == "founder_1"
    assert loaded["records"][0]["title"] == "Loaded"


def test_storage_adapter_lists_supabase_keys(monkeypatch):
    class FakeExecute:
        data = [{"key": "founder_1"}, {"key": "founder_2"}]

        def execute(self):
            return self

    class FakeQuery:
        def select(self, columns):
            assert columns == "key"
            return self

        def eq(self, key, value):
            assert (key, value) == ("collection", "company_brains")
            return self

        def execute(self):
            return FakeExecute().execute()

    class FakeClient:
        def table(self, name):
            assert name == "astra_documents"
            return FakeQuery()

    monkeypatch.setattr(settings, "astra_storage_backend", "supabase")
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_key", "service-key")
    monkeypatch.setattr("backend.storage_adapter._supabase_client", lambda: FakeClient())

    assert list_document_keys("company_brains") == ["founder_1", "founder_2"]


def test_storage_status_checks_supabase_schema(monkeypatch):
    class FakeExecute:
        def execute(self):
            return None

    class FakeSelect:
        def limit(self, value):
            assert value == 1
            return FakeExecute()

    class FakeTable:
        def select(self, columns):
            assert columns == "collection"
            return FakeSelect()

    class FakeClient:
        def table(self, name):
            assert name == "astra_documents"
            return FakeTable()

    monkeypatch.setattr(settings, "astra_storage_backend", "supabase")
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_key", "service-key")
    monkeypatch.setattr("backend.storage_adapter._supabase_client", lambda: FakeClient())

    assert schema_status()["ok"] is True
    status = storage_status()
    assert status["ok"] is True
    assert status["schema"]["table"] == "astra_documents"


def test_supabase_schema_declares_document_mirror_table():
    schema = Path("supabase/schema.sql").read_text()
    assert "create table if not exists astra_documents" in schema
    assert "primary key (collection, key)" in schema
