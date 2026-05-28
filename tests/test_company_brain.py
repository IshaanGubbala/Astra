from backend.tools.company_brain import (
    add_company_brain_record,
    ask_company_brain,
    company_brain_agent_context,
    configure_company_brain_sync,
    get_company_brain,
    ingest_company_brain_records,
    maintain_company_brain,
    resolve_company_brain_proposal,
    run_due_company_brain_syncs,
    run_company_brain_sync,
    search_company_brain,
    sync_company_brain,
)
from backend.tools.company_brain_connectors import import_company_brain_sources


def test_company_brain_sync_add_and_search(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_test"

    added = add_company_brain_record(
        founder_id=founder_id,
        source="manual",
        title="Pricing decision",
        content="Use team pricing with a founder plan and enterprise tier.",
        canonical=True,
        stale_risk="low",
    )
    assert added["ok"] is True

    synced = sync_company_brain(founder_id, ["github", "notion"])
    assert synced["ok"] is True
    assert synced["record_count"] >= 3

    results = search_company_brain(founder_id, "enterprise pricing", 5)
    assert results["count"] >= 1
    assert results["results"][0]["title"] == "Pricing decision"

    brain = get_company_brain(founder_id)
    assert brain["sources"]["github"]["record_count"] >= 1
    assert any(record["canonical"] for record in brain["records"])
    assert brain["sources"]["github"]["credential_fields"] == ["token"]
    assert brain["sources"]["slack"]["credential_fields"] == ["bot_token"]
    assert brain["sources"]["granola"]["importer"] is False


def test_company_brain_ingest_detects_conflicts_and_resolves_proposals(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_maintenance"

    ingest = ingest_company_brain_records(
        founder_id,
        "notion",
        [
            {
                "title": "Architecture source of truth",
                "content": "The backend uses FastAPI, Postgres, Supabase, Clerk auth, and Vercel deployment.",
                "canonical": True,
                "domain": "architecture",
            },
        ],
    )
    assert ingest["ok"] is True

    ingest_company_brain_records(
        founder_id,
        "slack",
        [
            {
                "title": "Old launch thread",
                "text": "Decision: use Django, MySQL, custom JWT auth, and AWS for the architecture.",
                "channel": "eng",
                "domain": "architecture",
            },
        ],
    )

    maintained = maintain_company_brain(founder_id)
    assert maintained["maintenance"]["contradiction_count"] >= 1
    assert maintained["proposals"]
    proposal = maintained["proposals"][0]
    assert proposal["kind"] == "contradiction"

    resolved = resolve_company_brain_proposal(founder_id, proposal["id"], "resolved")
    assert resolved["ok"] is True
    assert resolved["proposal"]["status"] == "resolved"


def test_company_brain_github_import_normalizes_provider_payload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_github"

    monkeypatch.setattr(
        "backend.tools.company_brain_connectors.load_credentials",
        lambda fid, service: {"token": "ghp_test"} if fid == founder_id and service == "github" else None,
    )

    def fake_get(url, headers, params=None, timeout=20):
        class Resp:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        if url.endswith("/user/repos"):
            return Resp([{
                "full_name": "acme/app",
                "name": "app",
                "description": "Company operating system",
                "language": "TypeScript",
                "default_branch": "main",
                "html_url": "https://github.com/acme/app",
                "updated_at": "2026-05-01T00:00:00Z",
            }])
        if url.endswith("/readme"):
            import base64
            return Resp({
                "content": base64.b64encode(b"# Acme App\nFastAPI and Supabase architecture").decode(),
                "html_url": "https://github.com/acme/app/blob/main/README.md",
            })
        if url.endswith("/issues"):
            return Resp([{
                "number": 7,
                "title": "Add Slack importer",
                "body": "Import Slack decisions into the company brain",
                "state": "open",
                "html_url": "https://github.com/acme/app/issues/7",
                "updated_at": "2026-05-02T00:00:00Z",
            }])
        if url.endswith("/pulls"):
            return Resp([{
                "number": 8,
                "title": "Company brain graph",
                "body": "Adds graph relationships",
                "state": "closed",
                "html_url": "https://github.com/acme/app/pull/8",
                "updated_at": "2026-05-03T00:00:00Z",
            }])
        raise AssertionError(url)

    monkeypatch.setattr("backend.tools.company_brain_connectors.requests.get", fake_get)

    imported = import_company_brain_sources(founder_id, ["github"], limit=1)
    assert imported["ok"] is True
    assert imported["imported_sources"] == ["github"]

    brain = get_company_brain(founder_id)
    titles = {record["title"] for record in brain["records"]}
    assert "Repository: acme/app" in titles
    assert "README: acme/app" in titles
    assert any("Slack importer" in title for title in titles)


def test_company_brain_slack_import_includes_thread_replies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_slack"
    monkeypatch.setattr(
        "backend.tools.company_brain_connectors.load_credentials",
        lambda fid, service: {"bot_token": "xoxb-test"} if fid == founder_id and service == "slack" else None,
    )

    def fake_get(url, headers, params=None, timeout=20):
        class Resp:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        if url.endswith("/conversations.list"):
            return Resp({"ok": True, "channels": [{"id": "C1", "name": "eng"}]})
        if url.endswith("/conversations.history"):
            return Resp({"ok": True, "messages": [{"ts": "1.0", "thread_ts": "1.0", "user": "U1", "text": "Decision: ship the company brain"}]})
        if url.endswith("/conversations.replies"):
            return Resp({"ok": True, "messages": [
                {"ts": "1.0", "user": "U1", "text": "Decision: ship the company brain"},
                {"ts": "1.1", "user": "U2", "text": "Also import Slack threads"},
            ]})
        raise AssertionError(url)

    monkeypatch.setattr("backend.tools.company_brain_connectors.requests.get", fake_get)
    imported = import_company_brain_sources(founder_id, ["slack"], limit=1)
    assert imported["ok"] is True
    brain = get_company_brain(founder_id)
    assert any("Also import Slack threads" in record["content"] for record in brain["records"])


def test_company_brain_google_drive_import_exports_doc_text(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_drive"
    monkeypatch.setattr(
        "backend.tools.company_brain_connectors.load_credentials",
        lambda fid, service: {"access_token": "ya29.test"} if fid == founder_id and service == "google_drive" else None,
    )

    def fake_get(url, headers, params=None, timeout=20):
        class Resp:
            text = "Launch plan\nUse the company brain as source of truth."

            def __init__(self, payload=None):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        if url.endswith("/drive/v3/files"):
            return Resp({"files": [{
                "id": "doc1",
                "name": "Launch plan",
                "mimeType": "application/vnd.google-apps.document",
                "webViewLink": "https://docs.google.com/document/d/doc1",
                "modifiedTime": "2026-05-01T00:00:00Z",
            }]})
        if url.endswith("/export"):
            return Resp()
        raise AssertionError(url)

    monkeypatch.setattr("backend.tools.company_brain_connectors.requests.get", fake_get)
    imported = import_company_brain_sources(founder_id, ["google_drive"], limit=1)
    assert imported["ok"] is True
    brain = get_company_brain(founder_id)
    assert any("source of truth" in record["content"] for record in brain["records"])


def test_company_brain_linear_zendesk_confluence_importers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_more_sources"

    def fake_creds(fid, service):
        if fid != founder_id:
            return None
        return {
            "linear": {"api_key": "lin_test"},
            "zendesk": {"subdomain": "acme", "email": "ops@example.com", "token": "zd_test"},
            "confluence": {"base_url": "https://acme.atlassian.net", "email": "ops@example.com", "token": "conf_test"},
        }.get(service)

    monkeypatch.setattr("backend.tools.company_brain_connectors.load_credentials", fake_creds)

    def fake_get(url, headers=None, params=None, timeout=20, auth=None):
        class Resp:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        if "zendesk.com" in url:
            return Resp({"tickets": [{"id": 42, "subject": "Importer bug", "description": "Customer cannot sync Zendesk", "status": "open", "priority": "high", "updated_at": "2026-05-02"}]})
        if "confluence" in url or "atlassian.net" in url:
            return Resp({"results": [{"id": "p1", "title": "Runbook", "body": {"storage": {"value": "<p>Restart the sync worker</p>"}}, "version": {"when": "2026-05-03"}, "_links": {"webui": "/wiki/spaces/ENG/pages/p1"}}]})
        raise AssertionError(url)

    def fake_post(url, headers=None, json=None, timeout=20):
        class Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"data": {"issues": {"nodes": [{
                    "id": "lin1",
                    "identifier": "ENG-1",
                    "title": "Build importer",
                    "description": "Add Linear to company brain",
                    "url": "https://linear.app/acme/issue/ENG-1",
                    "priority": 2,
                    "updatedAt": "2026-05-04",
                    "state": {"name": "In Progress", "type": "started"},
                    "assignee": {"name": "Ishaan", "email": "i@example.com"},
                    "team": {"name": "Engineering", "key": "ENG"},
                }]}}}

        assert "linear.app" in url
        return Resp()

    monkeypatch.setattr("backend.tools.company_brain_connectors.requests.get", fake_get)
    monkeypatch.setattr("backend.tools.company_brain_connectors.requests.post", fake_post)

    imported = import_company_brain_sources(founder_id, ["linear", "zendesk", "confluence"], limit=1)
    assert imported["ok"] is True
    assert set(imported["imported_sources"]) == {"linear", "zendesk", "confluence"}
    brain = get_company_brain(founder_id)
    content = "\n".join(record["content"] for record in brain["records"])
    assert "Add Linear to company brain" in content
    assert "Customer cannot sync Zendesk" in content
    assert "Restart the sync worker" in content


def test_company_brain_sync_runner_and_agent_context(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_sync"

    add_company_brain_record(
        founder_id,
        "manual",
        "Canonical architecture",
        "Use FastAPI, Supabase, Clerk, and Vercel for the production architecture.",
        canonical=True,
        stale_risk="low",
    )
    configured = configure_company_brain_sync(
        founder_id,
        enabled=True,
        sources=["github"],
        interval_minutes=15,
    )
    assert configured["sync"]["enabled"] is True
    assert configured["sync"]["interval_minutes"] == 15

    def fake_import(founder_id_arg, sources, limit=20):
        assert founder_id_arg == founder_id
        assert sources == ["github"]
        return {"ok": True, "imported_sources": ["github"], "failed_sources": [], "results": []}

    monkeypatch.setattr("backend.tools.company_brain_connectors.import_company_brain_sources", fake_import)

    run = run_company_brain_sync(founder_id, force=True)
    assert run["ok"] is True
    assert run["sync"]["last_status"] == "ok"
    assert run["sync"]["history"][0]["imported_sources"] == ["github"]

    ctx = company_brain_agent_context(founder_id, "production architecture", 5)
    assert ctx["ok"] is True
    assert "Canonical architecture" in ctx["context"]
    assert ctx["canonical_sources"]


def test_company_brain_due_sync_discovers_enabled_founders(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_due"
    configure_company_brain_sync(founder_id, enabled=True, sources=["github"], interval_minutes=15)

    called = []

    def fake_import(founder_id_arg, sources, limit=20):
        called.append((founder_id_arg, sources))
        return {"ok": True, "imported_sources": ["github"], "failed_sources": [], "results": []}

    monkeypatch.setattr("backend.tools.company_brain_connectors.import_company_brain_sources", fake_import)
    brain = get_company_brain(founder_id)
    brain["sync"]["next_run_at"] = "2000-01-01T00:00:00Z"
    path = tmp_path / ".astra" / "company_brain" / f"{founder_id}.json"
    import json
    path.write_text(json.dumps(brain))

    result = run_due_company_brain_syncs()
    assert result["ok"] is True
    assert result["ran"] == 1
    assert called == [(founder_id, ["github"])]


def test_company_brain_ask_returns_citations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_ask"
    add_company_brain_record(
        founder_id=founder_id,
        source="manual",
        title="Onboarding strategy",
        content="Use founder-led onboarding first, then self-serve checklists for expansion.",
        canonical=True,
        stale_risk="low",
    )
    add_company_brain_record(
        founder_id=founder_id,
        source="notion",
        title="Onboarding notes",
        content="Track activation milestones and first-week retention.",
        canonical=False,
        stale_risk="medium",
    )
    asked = ask_company_brain(founder_id, "What is our onboarding strategy?", limit=5)
    assert asked["ok"] is True
    assert asked["citations"]
    assert "Top source" in asked["answer"]
    assert asked["citations"][0]["title"] == "Onboarding strategy"
