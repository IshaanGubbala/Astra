# Astra Stage 1: Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the working spine — one `/goal` → Orchestrator → Legal Agent → `/result` loop that returns a real founder agreement document.

**Architecture:** FastAPI async app with Orchestrator running as a background coroutine. Orchestrator parses goals via Gemini Flash, builds a task DAG, dispatches tasks to agents via Redis queues, and collects results. Legal Agent (only agent in Stage 1) calls Gemma4 via llama.cpp OpenAI-compatible endpoint, retrieves memory from Vertex AI, and returns structured JSON. Gate: `/goal 'draft a founder agreement'` returns a real document.

**Tech Stack:** Python 3.12, FastAPI, Supabase (supabase-py), Redis (redis.asyncio + Upstash), Vertex AI (google-cloud-aiplatform), Gemini Flash (google-generativeai), OpenAI SDK (agent model calls), pydantic-settings, pytest + pytest-asyncio + fakeredis

**Plan series:** This is Plan 1 of 4. Plan 2 = Stage 2 (all 6 agents, Engineer 1). Plan 3 = Stage 3 (Next.js dashboard, Engineer 2). Plan 4 = Stage 4 (integration + Computer Use).

---

## File Structure

```
astra/
├── backend/
│   ├── main.py                     # FastAPI app, lifespan, mounts routes
│   ├── config.py                   # pydantic-settings, all env vars
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # /goal /approve /reject /ask /status endpoints
│   │   └── schemas.py              # Pydantic request/response models
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── loop.py                 # async execution loop (dispatch/poll/update)
│   │   ├── goal_parser.py          # Gemini Flash: text → structured goal JSON
│   │   ├── dag_builder.py          # Gemini Flash: goal → task DAG JSON
│   │   └── context_builder.py      # pull vector memory + build context bundle
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # AstraAgent class, Task, AgentResult dataclasses
│   │   └── legal.py                # Legal Agent instantiation
│   ├── memory/
│   │   ├── __init__.py
│   │   └── vector_store.py         # Vertex AI embed + upsert + query
│   ├── bus/
│   │   ├── __init__.py
│   │   └── redis_bus.py            # async Redis push/pop for task/result queues
│   ├── db/
│   │   ├── __init__.py
│   │   ├── client.py               # Supabase client singleton + query helpers
│   │   └── models.py               # Python dataclasses matching DB rows
│   └── tools/
│       ├── __init__.py
│       └── doc_generator.py        # Format agent output as legal document + disclaimer
├── supabase/
│   └── schema.sql                  # All 5 table definitions
├── tests/
│   ├── conftest.py                 # Fixtures: fake Redis, mock Supabase, mock model
│   ├── test_goal_parser.py
│   ├── test_dag_builder.py
│   ├── test_agent_base.py
│   ├── test_redis_bus.py
│   ├── test_vector_store.py
│   └── test_e2e_spine.py           # Gate test
├── .env.example
├── requirements.txt
├── pyproject.toml                  # pytest config
└── docker-compose.yml              # local Redis
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `pyproject.toml`
- Create: `backend/__init__.py` (empty)
- Create all `__init__.py` files listed in structure above (empty)

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic-settings==2.3.0
supabase==2.5.0
redis==5.0.4
google-generativeai==0.7.0
google-cloud-aiplatform==1.60.0
openai==1.35.0
python-dotenv==1.0.1
pytest==8.2.0
pytest-asyncio==0.23.7
fakeredis==2.23.0
pytest-mock==3.14.0
httpx==0.27.0
```

- [ ] **Step 2: Create `.env.example`**

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your-gemini-key
AGENT_MODEL_BASE_URL=http://localhost:8080/v1
AGENT_MODEL_API_KEY=dummy
AGENT_MODEL_NAME=gemma4
VERTEX_PROJECT=your-gcp-project
VERTEX_LOCATION=us-central1
```

- [ ] **Step 3: Create `docker-compose.yml`**

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

- [ ] **Step 4: Create `pyproject.toml`**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 5: Create all empty `__init__.py` files**

```bash
touch backend/__init__.py \
      backend/api/__init__.py \
      backend/orchestrator/__init__.py \
      backend/agents/__init__.py \
      backend/memory/__init__.py \
      backend/bus/__init__.py \
      backend/db/__init__.py \
      backend/tools/__init__.py \
      supabase/.gitkeep \
      tests/__init__.py
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "chore: project setup — deps, docker, pytest config"
```

---

## Task 2: Config

**Files:**
- Create: `backend/config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_config.py
from backend.config import settings

def test_settings_has_required_fields():
    assert hasattr(settings, "supabase_url")
    assert hasattr(settings, "redis_url")
    assert hasattr(settings, "gemini_api_key")
    assert hasattr(settings, "agent_model_base_url")
    assert hasattr(settings, "vertex_project")
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_config.py -v
```
Expected: `ImportError` or `AttributeError`

- [ ] **Step 3: Create `backend/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    redis_url: str = "redis://localhost:6379"
    gemini_api_key: str = ""
    agent_model_base_url: str = "http://localhost:8080/v1"
    agent_model_api_key: str = "dummy"
    agent_model_name: str = "gemma4"
    vertex_project: str = ""
    vertex_location: str = "us-central1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 4: Run to verify it passes**

```bash
pytest tests/test_config.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/config.py tests/test_config.py
git commit -m "feat: settings with pydantic-settings"
```

---

## Task 3: DB Models + Schema

**Files:**
- Create: `backend/db/models.py`
- Create: `supabase/schema.sql`

- [ ] **Step 1: Write failing test**

```python
# tests/test_db_models.py
from backend.db.models import Founder, Goal, Task, Approval, MemoryDocument

def test_founder_defaults():
    f = Founder(id="f1", email="a@b.com")
    assert f.plan == "launch"
    assert f.credit_balance == 0

def test_task_defaults():
    t = Task(id="t1", goal_id="g1", founder_id="f1", agent="legal", instruction="draft NDA")
    assert t.status == "pending"
    assert t.depends_on == []
    assert t.approval_required is False

def test_memory_document_fields():
    doc = MemoryDocument(
        id="d1", founder_id="f1", namespace="legal", agent="legal",
        doc_type="document", content="full text", summary="short summary"
    )
    assert doc.metadata == {}
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_db_models.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/db/models.py`**

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Founder:
    id: str
    email: str
    plan: str = "launch"
    credit_balance: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Goal:
    id: str
    founder_id: str
    instruction: str
    status: str = "pending"
    constraints: dict = field(default_factory=dict)
    elapsed_seconds: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class Task:
    id: str
    goal_id: str
    founder_id: str
    agent: str
    instruction: str
    context_bundle: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)
    status: str = "pending"
    result: Optional[dict] = None
    approval_required: bool = False
    tools_available: list = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class Approval:
    id: str
    task_id: str
    founder_id: str
    agent: str
    action: str
    consequence: str
    approval_token: str
    expires_at: datetime
    documents_ready: list = field(default_factory=list)
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MemoryDocument:
    id: str
    founder_id: str
    namespace: str
    agent: str
    doc_type: str
    content: str
    summary: str
    task_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

- [ ] **Step 4: Create `supabase/schema.sql`**

```sql
create extension if not exists "pgcrypto";

create table founders (
  id          uuid primary key default gen_random_uuid(),
  email       text unique not null,
  plan        text not null default 'launch',
  credit_balance integer not null default 0,
  created_at  timestamptz not null default now()
);

create table goals (
  id              text primary key,
  founder_id      uuid not null references founders(id),
  instruction     text not null,
  status          text not null default 'pending',
  constraints     jsonb default '{}',
  elapsed_seconds float,
  created_at      timestamptz not null default now(),
  completed_at    timestamptz
);

create table tasks (
  id               text primary key,
  goal_id          text not null references goals(id),
  founder_id       uuid not null references founders(id),
  agent            text not null,
  instruction      text not null,
  context_bundle   jsonb default '{}',
  depends_on       text[] not null default '{}',
  tools_available  text[] not null default '{}',
  constraints      jsonb default '{}',
  status           text not null default 'pending',
  result           jsonb,
  approval_required boolean not null default false,
  created_at       timestamptz not null default now(),
  completed_at     timestamptz
);

create table approvals (
  id              uuid primary key default gen_random_uuid(),
  task_id         text not null references tasks(id),
  founder_id      uuid not null references founders(id),
  agent           text not null,
  action          text not null,
  consequence     text not null,
  documents_ready text[] default '{}',
  approval_token  text unique not null,
  expires_at      timestamptz not null,
  approved_at     timestamptz,
  rejected_at     timestamptz,
  reject_reason   text,
  created_at      timestamptz not null default now()
);

create table memory_documents (
  id          uuid primary key default gen_random_uuid(),
  founder_id  uuid not null references founders(id),
  namespace   text not null,
  agent       text not null,
  task_id     text references tasks(id),
  doc_type    text not null,
  content     text not null,
  summary     text not null,
  metadata    jsonb default '{}',
  created_at  timestamptz not null default now()
);

create index on tasks(goal_id, status);
create index on memory_documents(founder_id, namespace);
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_db_models.py -v
```
Expected: 3 PASS

- [ ] **Step 6: Commit**

```bash
git add backend/db/models.py supabase/schema.sql tests/test_db_models.py
git commit -m "feat: DB models and Supabase schema"
```

---

## Task 4: Supabase DB Client

**Files:**
- Create: `backend/db/client.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_db_client.py
import pytest
from unittest.mock import MagicMock, patch
from backend.db.client import (
    get_ready_tasks,
    persist_task_graph,
    update_task_status,
    store_memory_document,
)


@pytest.fixture
def mock_supabase(mocker):
    mock = MagicMock()
    mocker.patch("backend.db.client.get_supabase", return_value=mock)
    return mock


@pytest.mark.asyncio
async def test_get_ready_tasks_returns_tasks_with_deps_done(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "t1", "status": "done",    "depends_on": []},
        {"id": "t2", "status": "pending", "depends_on": ["t1"]},
        {"id": "t3", "status": "pending", "depends_on": ["t2"]},
    ]
    ready = await get_ready_tasks("g1")
    assert len(ready) == 1
    assert ready[0]["id"] == "t2"


@pytest.mark.asyncio
async def test_persist_task_graph_inserts_rows(mock_supabase):
    tasks = [
        {"task_id": "t1", "agent": "legal", "depends_on": [], "instruction": "draft NDA"},
    ]
    await persist_task_graph("g1", "f1", tasks)
    mock_supabase.table.return_value.insert.assert_called_once()


@pytest.mark.asyncio
async def test_update_task_status_calls_update(mock_supabase):
    await update_task_status("t1", "done", result={"doc": "content"})
    mock_supabase.table.return_value.update.assert_called_once()
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_db_client.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/db/client.py`**

```python
import asyncio
from datetime import datetime
from typing import Optional

from supabase import create_client, Client

from backend.config import settings

_client: Optional[Client] = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


async def get_ready_tasks(goal_id: str) -> list[dict]:
    def _query():
        return get_supabase().table("tasks").select("*").eq("goal_id", goal_id).execute().data

    all_tasks = await asyncio.to_thread(_query)
    done_ids = {t["id"] for t in all_tasks if t["status"] == "done"}
    return [
        t for t in all_tasks
        if t["status"] == "pending"
        and all(dep in done_ids for dep in t["depends_on"])
    ]


async def has_in_progress_tasks(goal_id: str) -> bool:
    def _query():
        return get_supabase().table("tasks").select("id").eq("goal_id", goal_id).eq("status", "in_progress").execute().data

    result = await asyncio.to_thread(_query)
    return len(result) > 0


async def persist_goal(goal_id: str, founder_id: str, instruction: str, constraints: dict):
    def _insert():
        get_supabase().table("goals").insert({
            "id": goal_id,
            "founder_id": founder_id,
            "instruction": instruction,
            "constraints": constraints,
            "status": "pending",
        }).execute()

    await asyncio.to_thread(_insert)


async def persist_task_graph(goal_id: str, founder_id: str, tasks: list[dict]):
    def _insert():
        rows = [
            {
                "id": t["task_id"],
                "goal_id": goal_id,
                "founder_id": founder_id,
                "agent": t["agent"],
                "instruction": t.get("instruction", ""),
                "depends_on": t.get("depends_on", []),
                "tools_available": t.get("tools_available", []),
                "constraints": t.get("constraints", {}),
                "status": "pending",
            }
            for t in tasks
        ]
        get_supabase().table("tasks").insert(rows).execute()

    await asyncio.to_thread(_insert)


async def update_task_status(task_id: str, status: str, result: Optional[dict] = None):
    def _update():
        payload: dict = {"status": status}
        if result is not None:
            payload["result"] = result
        if status in ("done", "failed", "awaiting_approval"):
            payload["completed_at"] = datetime.utcnow().isoformat()
        get_supabase().table("tasks").update(payload).eq("id", task_id).execute()

    await asyncio.to_thread(_update)


async def store_memory_document(doc: dict):
    def _insert():
        get_supabase().table("memory_documents").insert(doc).execute()

    await asyncio.to_thread(_insert)


async def update_goal_status(goal_id: str, status: str, elapsed_seconds: Optional[float] = None):
    def _update():
        payload: dict = {"status": status}
        if elapsed_seconds is not None:
            payload["elapsed_seconds"] = elapsed_seconds
        if status == "done":
            payload["completed_at"] = datetime.utcnow().isoformat()
        get_supabase().table("goals").update(payload).eq("id", goal_id).execute()

    await asyncio.to_thread(_update)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_db_client.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/db/client.py tests/test_db_client.py
git commit -m "feat: Supabase DB client with async wrappers"
```

---

## Task 5: Redis Message Bus

**Files:**
- Create: `backend/bus/redis_bus.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_redis_bus.py
import json
import pytest
import fakeredis.aioredis
from backend.bus.redis_bus import RedisBus


@pytest.fixture
async def bus():
    fake = fakeredis.aioredis.FakeRedis()
    return RedisBus(redis_client=fake)


@pytest.mark.asyncio
async def test_push_and_pop_task(bus):
    task_payload = {"task_id": "t1", "agent": "legal", "instruction": "draft NDA"}
    await bus.push_task("f1", task_payload)
    result = await bus.pop_task("f1", timeout=1)
    assert result == task_payload


@pytest.mark.asyncio
async def test_push_and_poll_result(bus):
    result_payload = {"task_id": "t1", "status": "done", "output": {"doc": "content"}}
    await bus.push_result("f1", result_payload)
    results = await bus.poll_results("f1")
    assert len(results) == 1
    assert results[0]["task_id"] == "t1"


@pytest.mark.asyncio
async def test_poll_results_empty_returns_empty_list(bus):
    results = await bus.poll_results("f1")
    assert results == []
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_redis_bus.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/bus/redis_bus.py`**

```python
import json
from typing import Optional

import redis.asyncio as aioredis

from backend.config import settings


class RedisBus:
    def __init__(self, redis_client=None):
        self._redis = redis_client

    async def _get_redis(self):
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url)
        return self._redis

    def _task_queue_key(self, founder_id: str) -> str:
        return f"tasks:{founder_id}"

    def _result_queue_key(self, founder_id: str) -> str:
        return f"results:{founder_id}"

    async def push_task(self, founder_id: str, task_payload: dict):
        r = await self._get_redis()
        await r.lpush(self._task_queue_key(founder_id), json.dumps(task_payload))

    async def pop_task(self, founder_id: str, timeout: int = 5) -> Optional[dict]:
        r = await self._get_redis()
        result = await r.brpop(self._task_queue_key(founder_id), timeout=timeout)
        if result is None:
            return None
        _, value = result
        return json.loads(value)

    async def push_result(self, founder_id: str, result_payload: dict):
        r = await self._get_redis()
        await r.lpush(self._result_queue_key(founder_id), json.dumps(result_payload))

    async def poll_results(self, founder_id: str, max_results: int = 10) -> list[dict]:
        r = await self._get_redis()
        results = []
        for _ in range(max_results):
            value = await r.rpop(self._result_queue_key(founder_id))
            if value is None:
                break
            results.append(json.loads(value))
        return results


bus = RedisBus()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_redis_bus.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/bus/redis_bus.py tests/test_redis_bus.py
git commit -m "feat: Redis message bus for task/result queues"
```

---

## Task 6: Vector Store

**Files:**
- Create: `backend/memory/vector_store.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_vector_store.py
import pytest
from unittest.mock import patch, MagicMock
from backend.memory.vector_store import VectorStore


@pytest.fixture
def store(mocker):
    mocker.patch("backend.memory.vector_store.TextEmbeddingModel")
    return VectorStore()


@pytest.mark.asyncio
async def test_embed_returns_list_of_floats(store, mocker):
    store._model = MagicMock()
    store._model.get_embeddings.return_value = [MagicMock(values=[0.1, 0.2, 0.3])]
    result = await store.embed("test text")
    assert isinstance(result, list)
    assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_write_calls_store_memory_document(store, mocker):
    mock_store = mocker.patch("backend.memory.vector_store.store_memory_document")
    mock_store.return_value = None
    store._model = MagicMock()
    store._model.get_embeddings.return_value = [MagicMock(values=[0.1] * 768)]

    await store.write(
        doc_id="d1",
        founder_id="f1",
        namespace="legal",
        agent="legal",
        task_id="t1",
        doc_type="document",
        content="full agreement text",
        summary="founder agreement summary",
    )
    mock_store.assert_called_once()
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_vector_store.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/memory/vector_store.py`**

```python
import asyncio
import uuid
from typing import Optional

from vertexai.language_models import TextEmbeddingModel

from backend.config import settings
from backend.db.client import store_memory_document


class VectorStore:
    def __init__(self):
        self._model: Optional[TextEmbeddingModel] = None

    def _get_model(self) -> TextEmbeddingModel:
        if self._model is None:
            import vertexai
            vertexai.init(project=settings.vertex_project, location=settings.vertex_location)
            self._model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        return self._model

    async def embed(self, text: str) -> list[float]:
        def _embed():
            model = self._get_model()
            embeddings = model.get_embeddings([text])
            return embeddings[0].values

        return await asyncio.to_thread(_embed)

    async def write(
        self,
        doc_id: str,
        founder_id: str,
        namespace: str,
        agent: str,
        doc_type: str,
        content: str,
        summary: str,
        task_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        embedding = await self.embed(summary)
        doc = {
            "id": doc_id or str(uuid.uuid4()),
            "founder_id": founder_id,
            "namespace": namespace,
            "agent": agent,
            "task_id": task_id,
            "doc_type": doc_type,
            "content": content,
            "summary": summary,
            "metadata": {**(metadata or {}), "embedding": embedding},
        }
        await store_memory_document(doc)

    async def retrieve(
        self,
        founder_id: str,
        namespaces: list[str],
        query: str,
        k: int = 5,
    ) -> list[dict]:
        """
        Retrieve top-k relevant memory documents.
        In Stage 1, returns empty list if no Vertex AI configured.
        Full semantic search added in Stage 2.
        """
        if not settings.vertex_project:
            return []

        query_embedding = await self.embed(query)

        def _query():
            from backend.db.client import get_supabase
            rows = (
                get_supabase()
                .table("memory_documents")
                .select("*")
                .eq("founder_id", founder_id)
                .in_("namespace", namespaces)
                .limit(k * 3)
                .execute()
                .data
            )
            # cosine similarity against stored embeddings
            def cosine(a, b):
                dot = sum(x * y for x, y in zip(a, b))
                na = sum(x ** 2 for x in a) ** 0.5
                nb = sum(x ** 2 for x in b) ** 0.5
                return dot / (na * nb + 1e-9)

            scored = [
                (row, cosine(query_embedding, row["metadata"].get("embedding", [])))
                for row in rows
                if row["metadata"].get("embedding")
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            return [row for row, _ in scored[:k]]

        return await asyncio.to_thread(_query)


vector_store = VectorStore()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_vector_store.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/memory/vector_store.py tests/test_vector_store.py
git commit -m "feat: Vertex AI vector store with embed/write/retrieve"
```

---

## Task 7: Document Generator Tool

**Files:**
- Create: `backend/tools/doc_generator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_doc_generator.py
from backend.tools.doc_generator import format_legal_document, DISCLAIMER


def test_format_adds_disclaimer():
    doc = format_legal_document(
        doc_type="founder_agreement",
        company_name="AcmeCo",
        content="This is the agreement body.",
    )
    assert DISCLAIMER in doc


def test_format_includes_company_name():
    doc = format_legal_document(
        doc_type="founder_agreement",
        company_name="AcmeCo",
        content="Agreement body here.",
    )
    assert "AcmeCo" in doc


def test_format_includes_content():
    content = "Section 1: Equity split is 50/50."
    doc = format_legal_document(
        doc_type="nda",
        company_name="AcmeCo",
        content=content,
    )
    assert content in doc
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_doc_generator.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/tools/doc_generator.py`**

```python
from datetime import date

DISCLAIMER = (
    "AI-generated document preparation — not legal advice. "
    "Review with a licensed attorney before signing."
)

DOC_TYPE_LABELS = {
    "founder_agreement": "Founder Agreement",
    "nda": "Non-Disclosure Agreement",
    "ip_assignment": "IP Assignment Agreement",
    "vesting_schedule": "Vesting Schedule",
}


def format_legal_document(doc_type: str, company_name: str, content: str) -> str:
    label = DOC_TYPE_LABELS.get(doc_type, doc_type.replace("_", " ").title())
    today = date.today().isoformat()
    return f"""================================================================================
{label.upper()}
Company: {company_name}
Date: {today}
================================================================================

{content}

================================================================================
DISCLAIMER: {DISCLAIMER}
================================================================================
"""
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_doc_generator.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tools/doc_generator.py tests/test_doc_generator.py
git commit -m "feat: legal document formatter with disclaimer"
```

---

## Task 8: AstraAgent Base Class

**Files:**
- Create: `backend/agents/base.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_agent_base.py
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.agents.base import AstraAgent, AgentTask, AgentResult


@pytest.fixture
def agent(mocker):
    mocker.patch("backend.agents.base.vector_store")
    mocker.patch("backend.agents.base.openai")
    return AstraAgent(
        agent_id="legal",
        system_prompt="You are the Legal Agent.",
        model="gemma4",
        tools=["doc_generator"],
        memory_namespaces=["legal", "shared"],
    )


def test_agent_builds_prompt_includes_instruction(agent):
    task = AgentTask(
        task_id="t1", goal_id="g1", founder_id="f1",
        agent="legal", instruction="Draft an NDA",
        context_bundle={"company_name": "AcmeCo"},
        constraints={}, tools_available=["doc_generator"],
    )
    prompt = agent._build_prompt(task, memory_docs=[])
    assert "Draft an NDA" in prompt
    assert "AcmeCo" in prompt


@pytest.mark.asyncio
async def test_agent_run_done_returns_agent_result(mocker):
    mocker.patch("backend.agents.base.vector_store.retrieve", new=AsyncMock(return_value=[]))

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({
        "status": "done",
        "output": {"document": "Agreement text here"},
        "confidence": 0.95,
        "reasoning": "Generated founder agreement",
    })
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch("backend.agents.base.openai.OpenAI", return_value=mock_client)

    agent = AstraAgent(
        agent_id="legal",
        system_prompt="You are the Legal Agent.",
        model="gemma4",
        tools=["doc_generator"],
        memory_namespaces=["legal", "shared"],
    )

    task = AgentTask(
        task_id="t1", goal_id="g1", founder_id="f1",
        agent="legal", instruction="Draft NDA",
        context_bundle={}, constraints={}, tools_available=[],
    )
    result = await agent.run(task)
    assert isinstance(result, AgentResult)
    assert result.status == "done"
    assert "document" in result.output


@pytest.mark.asyncio
async def test_agent_run_approval_required_returns_approval_result(mocker):
    mocker.patch("backend.agents.base.vector_store.retrieve", new=AsyncMock(return_value=[]))

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({
        "status": "approval_required",
        "output": {},
        "confidence": 0.99,
        "reasoning": "About to charge $500",
        "approval_action": "File Delaware LLC — $500 charge",
        "approval_consequence": "Irreversible. Company legally formed.",
    })
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch("backend.agents.base.openai.OpenAI", return_value=mock_client)

    agent = AstraAgent(
        agent_id="legal", system_prompt="Legal.", model="gemma4",
        tools=[], memory_namespaces=["legal"],
    )
    task = AgentTask(
        task_id="t2", goal_id="g1", founder_id="f1",
        agent="legal", instruction="File LLC",
        context_bundle={}, constraints={}, tools_available=[],
    )
    result = await agent.run(task)
    assert result.status == "approval_required"
    assert result.approval_action is not None
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_agent_base.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/agents/base.py`**

```python
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import openai

from backend.config import settings
from backend.memory.vector_store import vector_store

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    task_id: str
    goal_id: str
    founder_id: str
    agent: str
    instruction: str
    context_bundle: dict
    constraints: dict
    tools_available: list


@dataclass
class AgentResult:
    task_id: str
    agent: str
    status: str  # "done" | "blocked" | "approval_required"
    output: dict
    confidence: float
    reasoning: str
    approval_action: Optional[str] = None
    approval_consequence: Optional[str] = None
    blocked_reason: Optional[str] = None
    blocked_needs: Optional[str] = None
    cost_usd: float = 0.0


class AstraAgent:
    def __init__(
        self,
        agent_id: str,
        system_prompt: str,
        model: str,
        tools: list[str],
        memory_namespaces: list[str],
    ):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.model = model
        self.tools = tools
        self.memory_namespaces = memory_namespaces
        self._client: Optional[openai.OpenAI] = None

    def _get_client(self) -> openai.OpenAI:
        if self._client is None:
            self._client = openai.OpenAI(
                base_url=settings.agent_model_base_url,
                api_key=settings.agent_model_api_key,
            )
        return self._client

    def _build_prompt(self, task: AgentTask, memory_docs: list[dict]) -> str:
        memory_text = "\n\n".join(
            f"[{doc.get('doc_type', 'doc')}] {doc.get('summary', '')}"
            for doc in memory_docs
        )
        return (
            f"GOAL: {task.instruction}\n\n"
            f"COMPANY CONTEXT:\n{json.dumps(task.context_bundle, indent=2)}\n\n"
            f"RELEVANT MEMORY:\n{memory_text or '(none)'}\n\n"
            f"CONSTRAINTS:\n{json.dumps(task.constraints, indent=2)}\n\n"
            f"AVAILABLE TOOLS: {', '.join(task.tools_available) or '(none)'}\n\n"
            "Respond ONLY with valid JSON:\n"
            "{\n"
            '  "status": "done" | "blocked" | "approval_required",\n'
            '  "output": {},\n'
            '  "confidence": 0.0,\n'
            '  "reasoning": "...",\n'
            '  "approval_action": "...",\n'
            '  "approval_consequence": "...",\n'
            '  "blocked_reason": "...",\n'
            '  "blocked_needs": "..."\n'
            "}"
        )

    def _call_model(self, messages: list[dict]) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    async def run(self, task: AgentTask) -> AgentResult:
        memory_docs = await vector_store.retrieve(
            founder_id=task.founder_id,
            namespaces=self.memory_namespaces,
            query=task.instruction,
            k=5,
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._build_prompt(task, memory_docs)},
        ]

        raw = await asyncio.to_thread(self._call_model, messages)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Agent %s returned invalid JSON: %s", self.agent_id, raw[:200])
            parsed = {
                "status": "blocked",
                "output": {},
                "confidence": 0.0,
                "reasoning": "Model returned non-JSON response",
                "blocked_reason": "invalid_json",
                "blocked_needs": "retry or model swap",
            }

        return AgentResult(
            task_id=task.task_id,
            agent=self.agent_id,
            status=parsed.get("status", "blocked"),
            output=parsed.get("output", {}),
            confidence=parsed.get("confidence", 0.0),
            reasoning=parsed.get("reasoning", ""),
            approval_action=parsed.get("approval_action"),
            approval_consequence=parsed.get("approval_consequence"),
            blocked_reason=parsed.get("blocked_reason"),
            blocked_needs=parsed.get("blocked_needs"),
        )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_agent_base.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agents/base.py tests/test_agent_base.py
git commit -m "feat: AstraAgent base class with Task/AgentResult dataclasses"
```

---

## Task 9: Legal Agent

**Files:**
- Create: `backend/agents/legal.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_legal_agent.py
from backend.agents.legal import LEGAL_AGENT


def test_legal_agent_id():
    assert LEGAL_AGENT.agent_id == "legal"


def test_legal_agent_namespaces():
    assert "legal" in LEGAL_AGENT.memory_namespaces
    assert "shared" in LEGAL_AGENT.memory_namespaces


def test_legal_agent_system_prompt_has_disclaimer():
    assert "not legal advice" in LEGAL_AGENT.system_prompt


def test_legal_agent_has_doc_generator_tool():
    assert "doc_generator" in LEGAL_AGENT.tools
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_legal_agent.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/agents/legal.py`**

```python
from backend.agents.base import AstraAgent
from backend.config import settings

LEGAL_AGENT = AstraAgent(
    agent_id="legal",
    system_prompt=(
        "You are the Legal Agent for Astra. You form companies and draft legal documents. "
        "You draft founder agreements, NDAs, IP assignment agreements, and vesting schedules. "
        "When drafting documents, include all relevant sections with placeholder text the founder can review. "
        "For irreversible actions (filing an LLC, charging a payment method), always return "
        'status: "approval_required" with a clear action and consequence description. '
        "Always append to every document: "
        "AI-generated document preparation — not legal advice. "
        "Review with a licensed attorney before signing."
    ),
    model=settings.agent_model_name,
    tools=["doc_generator", "compliance_monitor"],
    memory_namespaces=["legal", "shared"],
)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_legal_agent.py -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agents/legal.py tests/test_legal_agent.py
git commit -m "feat: Legal Agent instantiation"
```

---

## Task 10: Goal Parser (Gemini Flash)

**Files:**
- Create: `backend/orchestrator/goal_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_goal_parser.py
import pytest
from unittest.mock import MagicMock, patch
from backend.orchestrator.goal_parser import parse_goal


@pytest.mark.asyncio
async def test_parse_goal_returns_structured_output(mocker):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"instruction": "launch a SaaS for restaurants", "entities": {"company_name": "RestaurantIQ", "icp": "restaurant owners"}, "priority_agents": ["legal", "research"]}'
    mock_model.generate_content.return_value = mock_response
    mocker.patch("backend.orchestrator.goal_parser.genai.GenerativeModel", return_value=mock_model)

    result = await parse_goal(
        goal_id="g1",
        founder_id="f1",
        raw_instruction="I want to build a restaurant inventory SaaS called RestaurantIQ",
    )
    assert result["instruction"] == "launch a SaaS for restaurants"
    assert "entities" in result
    assert "priority_agents" in result


@pytest.mark.asyncio
async def test_parse_goal_falls_back_on_invalid_json(mocker):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "not valid json at all"
    mock_model.generate_content.return_value = mock_response
    mocker.patch("backend.orchestrator.goal_parser.genai.GenerativeModel", return_value=mock_model)

    result = await parse_goal(goal_id="g1", founder_id="f1", raw_instruction="Build something")
    assert result["instruction"] == "Build something"
    assert result["entities"] == {}
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_goal_parser.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/orchestrator/goal_parser.py`**

```python
import asyncio
import json
import logging

import google.generativeai as genai

from backend.config import settings

logger = logging.getLogger(__name__)

_PARSE_PROMPT = """\
You are an AI goal parser. Extract structured information from this founder's goal.

Founder input: {raw_instruction}

Respond ONLY with valid JSON:
{{
  "instruction": "clean 1-sentence description of the goal",
  "entities": {{
    "company_name": "if mentioned, else null",
    "icp": "ideal customer profile if mentioned, else null",
    "problem": "problem being solved",
    "pricing_hypothesis": "pricing if mentioned, else null"
  }},
  "constraints": {{}},
  "priority_agents": ["list of agents to prioritize: legal, research, web, marketing, technical, ops"]
}}
"""


async def parse_goal(goal_id: str, founder_id: str, raw_instruction: str) -> dict:
    def _call():
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = _PARSE_PROMPT.format(raw_instruction=raw_instruction)
        response = model.generate_content(prompt)
        return response.text

    raw = await asyncio.to_thread(_call)

    try:
        parsed = json.loads(raw)
        parsed.setdefault("entities", {})
        parsed.setdefault("constraints", {})
        parsed.setdefault("priority_agents", [])
        return parsed
    except json.JSONDecodeError:
        logger.warning("Goal parser returned invalid JSON for goal %s", goal_id)
        return {
            "instruction": raw_instruction,
            "entities": {},
            "constraints": {},
            "priority_agents": [],
        }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_goal_parser.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/orchestrator/goal_parser.py tests/test_goal_parser.py
git commit -m "feat: Gemini Flash goal parser with JSON fallback"
```

---

## Task 11: DAG Builder (Gemini Flash)

**Files:**
- Create: `backend/orchestrator/dag_builder.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_dag_builder.py
import pytest
from unittest.mock import MagicMock
from backend.orchestrator.dag_builder import build_task_dag


@pytest.mark.asyncio
async def test_dag_builder_returns_tasks_list(mocker):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"tasks": [{"task_id": "t_001", "agent": "legal", "depends_on": [], "instruction": "Draft a founder agreement for AcmeCo"}]}'
    mock_model.generate_content.return_value = mock_response
    mocker.patch("backend.orchestrator.dag_builder.genai.GenerativeModel", return_value=mock_model)

    dag = await build_task_dag(
        goal_id="g1",
        parsed_goal={"instruction": "draft a founder agreement", "entities": {"company_name": "AcmeCo"}, "priority_agents": ["legal"]},
    )
    assert isinstance(dag, list)
    assert len(dag) == 1
    assert dag[0]["agent"] == "legal"
    assert dag[0]["depends_on"] == []


@pytest.mark.asyncio
async def test_dag_builder_falls_back_on_invalid_json(mocker):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    mock_model.generate_content.return_value = mock_response
    mocker.patch("backend.orchestrator.dag_builder.genai.GenerativeModel", return_value=mock_model)

    dag = await build_task_dag(
        goal_id="g1",
        parsed_goal={"instruction": "do something", "entities": {}, "priority_agents": []},
    )
    assert isinstance(dag, list)
    assert len(dag) >= 1


@pytest.mark.asyncio
async def test_dag_builder_assigns_unique_task_ids(mocker):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"tasks": [{"task_id": "t_001", "agent": "legal", "depends_on": []}, {"task_id": "t_002", "agent": "research", "depends_on": []}]}'
    mock_model.generate_content.return_value = mock_response
    mocker.patch("backend.orchestrator.dag_builder.genai.GenerativeModel", return_value=mock_model)

    dag = await build_task_dag(goal_id="g1", parsed_goal={"instruction": "launch", "entities": {}, "priority_agents": []})
    ids = [t["task_id"] for t in dag]
    assert len(ids) == len(set(ids))
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_dag_builder.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/orchestrator/dag_builder.py`**

```python
import asyncio
import json
import logging

import google.generativeai as genai

from backend.config import settings

logger = logging.getLogger(__name__)

_DAG_PROMPT = """\
You are an AI task planner for a startup automation system.

Given this founder goal, build a dependency graph of tasks to complete it.
Available agents: legal, research, web, marketing, technical, ops

Goal: {instruction}
Entities: {entities}
Priority agents: {priority_agents}

Rules:
- research and legal can run in parallel (no dependencies)
- web and marketing depend on research
- technical depends on web
- ops depends on all others
- Only include agents relevant to the goal
- Each task must have a specific instruction for the agent

Respond ONLY with valid JSON:
{{
  "tasks": [
    {{
      "task_id": "t_001",
      "agent": "legal",
      "depends_on": [],
      "instruction": "specific instruction for this agent",
      "tools_available": ["doc_generator"],
      "constraints": {{}}
    }}
  ]
}}
"""

_FALLBACK_TASK = {
    "task_id": "t_001",
    "agent": "legal",
    "depends_on": [],
    "instruction": "",
    "tools_available": ["doc_generator"],
    "constraints": {},
}


async def build_task_dag(goal_id: str, parsed_goal: dict) -> list[dict]:
    def _call():
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = _DAG_PROMPT.format(
            instruction=parsed_goal.get("instruction", ""),
            entities=json.dumps(parsed_goal.get("entities", {})),
            priority_agents=parsed_goal.get("priority_agents", []),
        )
        return model.generate_content(prompt).text

    raw = await asyncio.to_thread(_call)

    try:
        data = json.loads(raw)
        tasks = data.get("tasks", [])
        if not tasks:
            raise ValueError("empty task list")
        # prefix task_ids with goal_id to ensure uniqueness
        for i, task in enumerate(tasks):
            if not task.get("task_id"):
                task["task_id"] = f"{goal_id}_t_{i+1:03d}"
            task.setdefault("depends_on", [])
            task.setdefault("tools_available", [])
            task.setdefault("constraints", {})
        return tasks
    except (json.JSONDecodeError, ValueError):
        logger.warning("DAG builder fallback for goal %s", goal_id)
        fallback = {**_FALLBACK_TASK, "task_id": f"{goal_id}_t_001", "instruction": parsed_goal.get("instruction", "")}
        return [fallback]
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_dag_builder.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/orchestrator/dag_builder.py tests/test_dag_builder.py
git commit -m "feat: Gemini Flash DAG builder with fallback"
```

---

## Task 12: Context Builder

**Files:**
- Create: `backend/orchestrator/context_builder.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_context_builder.py
import pytest
from unittest.mock import AsyncMock
from backend.orchestrator.context_builder import build_context
from backend.db.models import Task


@pytest.mark.asyncio
async def test_build_context_includes_company_context(mocker):
    mocker.patch(
        "backend.orchestrator.context_builder.vector_store.retrieve",
        new=AsyncMock(return_value=[
            {"doc_type": "report", "summary": "Market is large", "content": "..."}
        ]),
    )
    task = Task(
        id="t1", goal_id="g1", founder_id="f1", agent="legal",
        instruction="Draft NDA",
        context_bundle={"company_name": "AcmeCo", "icp": "restaurant owners"},
    )
    context = await build_context(task, namespaces=["legal", "shared"])
    assert "company_name" in context
    assert context["company_name"] == "AcmeCo"
    assert "memory_docs" in context


@pytest.mark.asyncio
async def test_build_context_memory_docs_are_summaries(mocker):
    mocker.patch(
        "backend.orchestrator.context_builder.vector_store.retrieve",
        new=AsyncMock(return_value=[
            {"doc_type": "document", "summary": "Prior NDA drafted", "content": "full content"},
        ]),
    )
    task = Task(id="t1", goal_id="g1", founder_id="f1", agent="legal", instruction="Draft NDA")
    context = await build_context(task, namespaces=["legal"])
    assert any("Prior NDA drafted" in doc for doc in context["memory_docs"])
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_context_builder.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/orchestrator/context_builder.py`**

```python
from backend.db.models import Task
from backend.memory.vector_store import vector_store


async def build_context(task: Task, namespaces: list[str]) -> dict:
    memory_docs = await vector_store.retrieve(
        founder_id=task.founder_id,
        namespaces=namespaces,
        query=task.instruction,
        k=5,
    )
    context = {
        **task.context_bundle,
        "memory_docs": [
            f"[{doc.get('doc_type', 'doc')}] {doc.get('summary', '')}"
            for doc in memory_docs
        ],
    }
    return context
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_context_builder.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/orchestrator/context_builder.py tests/test_context_builder.py
git commit -m "feat: context builder pulls vector memory per task"
```

---

## Task 13: Orchestrator Loop

**Files:**
- Create: `backend/orchestrator/loop.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_orchestrator_loop.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.orchestrator.loop import OrchestratorLoop
from backend.agents.base import AgentTask, AgentResult


@pytest.fixture
def loop(mocker):
    mocker.patch("backend.orchestrator.loop.parse_goal", new=AsyncMock(return_value={
        "instruction": "draft a founder agreement",
        "entities": {"company_name": "AcmeCo"},
        "constraints": {},
        "priority_agents": ["legal"],
    }))
    mocker.patch("backend.orchestrator.loop.build_task_dag", new=AsyncMock(return_value=[
        {"task_id": "t_001", "agent": "legal", "depends_on": [], "instruction": "Draft founder agreement", "tools_available": ["doc_generator"], "constraints": {}}
    ]))
    mocker.patch("backend.orchestrator.loop.persist_goal", new=AsyncMock())
    mocker.patch("backend.orchestrator.loop.persist_task_graph", new=AsyncMock())
    mocker.patch("backend.orchestrator.loop.update_task_status", new=AsyncMock())
    mocker.patch("backend.orchestrator.loop.update_goal_status", new=AsyncMock())
    mocker.patch("backend.orchestrator.loop.vector_store.write", new=AsyncMock())
    return OrchestratorLoop()


@pytest.mark.asyncio
async def test_process_goal_dispatches_task_to_agent(loop, mocker):
    ready_tasks = [
        {"id": "t_001", "agent": "legal", "depends_on": [], "instruction": "Draft founder agreement",
         "context_bundle": {"company_name": "AcmeCo"}, "tools_available": [], "constraints": {}, "goal_id": "g_001"}
    ]
    mocker.patch("backend.orchestrator.loop.get_ready_tasks", new=AsyncMock(side_effect=[ready_tasks, []]))
    mocker.patch("backend.orchestrator.loop.has_in_progress_tasks", new=AsyncMock(side_effect=[True, False]))

    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value=AgentResult(
        task_id="t_001", agent="legal", status="done",
        output={"document": "Agreement text"}, confidence=0.95, reasoning="Generated",
    ))
    mocker.patch("backend.orchestrator.loop.AGENTS", {"legal": mock_agent})

    result = await loop.run_goal("g_001", "f_001", "draft a founder agreement", {})
    assert result["status"] == "done"
    mock_agent.run.assert_called_once()
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_orchestrator_loop.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/orchestrator/loop.py`**

```python
import asyncio
import logging
import time
import uuid
from typing import Any

from backend.agents.base import AgentTask, AgentResult
from backend.agents.legal import LEGAL_AGENT
from backend.db.client import (
    get_ready_tasks,
    has_in_progress_tasks,
    persist_goal,
    persist_task_graph,
    update_goal_status,
    update_task_status,
)
from backend.memory.vector_store import vector_store
from backend.orchestrator.context_builder import build_context
from backend.orchestrator.dag_builder import build_task_dag
from backend.orchestrator.goal_parser import parse_goal
from backend.db.models import Task

logger = logging.getLogger(__name__)

AGENTS = {
    "legal": LEGAL_AGENT,
    # stages 2+ add: research, web, marketing, technical, ops
}


class OrchestratorLoop:
    async def run_goal(
        self,
        goal_id: str,
        founder_id: str,
        raw_instruction: str,
        constraints: dict,
    ) -> dict[str, Any]:
        start = time.time()

        parsed = await parse_goal(goal_id, founder_id, raw_instruction)
        dag = await build_task_dag(goal_id, parsed)

        await persist_goal(goal_id, founder_id, parsed["instruction"], constraints)
        await persist_task_graph(goal_id, founder_id, dag)
        await update_goal_status(goal_id, "in_progress")

        results: list[AgentResult] = []
        approvals: list[dict] = []

        while True:
            ready = await get_ready_tasks(goal_id)
            in_progress = await has_in_progress_tasks(goal_id)

            if not ready and not in_progress:
                break

            # Dispatch all ready tasks concurrently
            if ready:
                task_coroutines = []
                for row in ready:
                    await update_task_status(row["id"], "in_progress")
                    task_coroutines.append(self._run_task(row, founder_id, parsed))

                task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

                for result in task_results:
                    if isinstance(result, Exception):
                        logger.error("Task failed with exception: %s", result)
                        continue

                    if result.status == "done":
                        await update_task_status(result.task_id, "done", result.output)
                        await vector_store.write(
                            doc_id=str(uuid.uuid4()),
                            founder_id=founder_id,
                            namespace=result.agent,
                            agent=result.agent,
                            doc_type="result",
                            content=str(result.output),
                            summary=result.reasoning[:500] if result.reasoning else "Task completed",
                            task_id=result.task_id,
                        )
                        results.append(result)

                    elif result.status == "approval_required":
                        await update_task_status(result.task_id, "awaiting_approval")
                        approvals.append({
                            "task_id": result.task_id,
                            "agent": result.agent,
                            "action": result.approval_action,
                            "consequence": result.approval_consequence,
                        })

                    elif result.status == "blocked":
                        logger.warning("Task %s blocked: %s", result.task_id, result.blocked_reason)
                        await update_task_status(result.task_id, "blocked")

            else:
                await asyncio.sleep(0.5)

        elapsed = time.time() - start
        await update_goal_status(goal_id, "done", elapsed_seconds=elapsed)

        return {
            "goal_id": goal_id,
            "status": "done",
            "results": [
                {"task_id": r.task_id, "agent": r.agent, "output": r.output}
                for r in results
            ],
            "pending_approvals": approvals,
            "elapsed_seconds": elapsed,
        }

    async def _run_task(self, row: dict, founder_id: str, parsed_goal: dict) -> AgentResult:
        agent_id = row["agent"]
        agent = AGENTS.get(agent_id)

        if agent is None:
            return AgentResult(
                task_id=row["id"], agent=agent_id, status="blocked",
                output={}, confidence=0.0, reasoning="",
                blocked_reason=f"No agent registered for '{agent_id}'",
                blocked_needs="Register agent in AGENTS dict",
            )

        task = Task(
            id=row["id"],
            goal_id=row["goal_id"],
            founder_id=founder_id,
            agent=agent_id,
            instruction=row["instruction"],
            context_bundle={**row.get("context_bundle", {}), **parsed_goal.get("entities", {})},
            constraints=row.get("constraints", {}),
            tools_available=row.get("tools_available", []),
        )

        context = await build_context(task, agent.memory_namespaces)
        task.context_bundle = context

        agent_task = AgentTask(
            task_id=task.id,
            goal_id=task.goal_id,
            founder_id=task.founder_id,
            agent=task.agent,
            instruction=task.instruction,
            context_bundle=task.context_bundle,
            constraints=task.constraints,
            tools_available=task.tools_available,
        )

        return await agent.run(agent_task)


orchestrator = OrchestratorLoop()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_orchestrator_loop.py -v
```
Expected: 1 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/orchestrator/loop.py tests/test_orchestrator_loop.py
git commit -m "feat: async orchestrator loop with parallel task dispatch"
```

---

## Task 14: FastAPI App + API Endpoints

**Files:**
- Create: `backend/api/schemas.py`
- Create: `backend/api/routes.py`
- Create: `backend/main.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from backend.main import app


@pytest.mark.asyncio
async def test_goal_endpoint_returns_202(mocker):
    mocker.patch(
        "backend.api.routes.orchestrator.run_goal",
        new=AsyncMock(return_value={
            "goal_id": "g_abc123",
            "status": "done",
            "results": [{"task_id": "t_001", "agent": "legal", "output": {"document": "Agreement text"}}],
            "pending_approvals": [],
            "elapsed_seconds": 1.2,
        }),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/goal", json={
            "founder_id": "f_001",
            "instruction": "Draft a founder agreement for AcmeCo",
            "constraints": {},
        })
    assert response.status_code == 200
    body = response.json()
    assert body["goal_id"] == "g_abc123"
    assert body["status"] == "done"


@pytest.mark.asyncio
async def test_status_endpoint_returns_goal_info(mocker):
    mocker.patch(
        "backend.api.routes.get_supabase",
        return_value=_mock_supabase_with_goal(),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/status/g_abc123")
    assert response.status_code == 200


def _mock_supabase_with_goal():
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "g_abc123", "status": "in_progress", "instruction": "draft NDA"}
    ]
    return mock
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_api.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create `backend/api/schemas.py`**

```python
from pydantic import BaseModel
from typing import Optional


class GoalRequest(BaseModel):
    founder_id: str
    instruction: str
    constraints: dict = {}


class ApproveRequest(BaseModel):
    task_id: str
    approval_token: str
    note: Optional[str] = None


class RejectRequest(BaseModel):
    task_id: str
    reason: str
    redirect_instruction: Optional[str] = None


class AskRequest(BaseModel):
    target_agent: str
    question: str
    context: Optional[str] = None
    founder_id: str
```

- [ ] **Step 4: Create `backend/api/routes.py`**

```python
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.api.schemas import AskRequest, ApproveRequest, GoalRequest, RejectRequest
from backend.db.client import get_supabase, update_task_status
from backend.orchestrator.loop import orchestrator

router = APIRouter()


@router.post("/goal")
async def submit_goal(body: GoalRequest):
    goal_id = f"g_{uuid.uuid4().hex[:8]}"
    result = await orchestrator.run_goal(
        goal_id=goal_id,
        founder_id=body.founder_id,
        raw_instruction=body.instruction,
        constraints=body.constraints,
    )
    return result


@router.post("/approve")
async def approve_task(body: ApproveRequest):
    await update_task_status(body.task_id, "approved")
    return {"task_id": body.task_id, "status": "approved"}


@router.post("/reject")
async def reject_task(body: RejectRequest):
    await update_task_status(body.task_id, "rejected")
    return {"task_id": body.task_id, "status": "rejected", "reason": body.reason}


@router.post("/ask")
async def ask_agent(body: AskRequest):
    from backend.orchestrator.loop import AGENTS
    from backend.agents.base import AgentTask

    agent = AGENTS.get(body.target_agent)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{body.target_agent}' not found")

    task = AgentTask(
        task_id=f"ask_{uuid.uuid4().hex[:8]}",
        goal_id="direct_ask",
        founder_id=body.founder_id,
        agent=body.target_agent,
        instruction=body.question,
        context_bundle={"context": body.context or ""},
        constraints={},
        tools_available=[],
    )
    result = await agent.run(task)
    return {"agent": body.target_agent, "response": result.output, "reasoning": result.reasoning}


@router.get("/status/{goal_id}")
async def get_status(goal_id: str):
    db = get_supabase()
    goals = db.table("goals").select("*").eq("id", goal_id).execute().data
    if not goals:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal = goals[0]
    tasks = db.table("tasks").select("*").eq("goal_id", goal_id).execute().data
    return {"goal": goal, "tasks": tasks}
```

- [ ] **Step 5: Create `backend/main.py`**

```python
from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(title="Astra API", version="1.0.0")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_api.py -v
```
Expected: 2 PASS

- [ ] **Step 7: Commit**

```bash
git add backend/api/schemas.py backend/api/routes.py backend/main.py tests/test_api.py
git commit -m "feat: FastAPI app with /goal /approve /reject /ask /status endpoints"
```

---

## Task 15: End-to-End Gate Test

**Files:**
- Create: `tests/test_e2e_spine.py`
- Create: `tests/conftest.py`

This is the gate test. It runs the full spine: `/goal 'draft a founder agreement'` → Legal Agent → document returned. Uses mocked Gemini Flash and mocked llama.cpp model.

- [ ] **Step 1: Create `tests/conftest.py`**

```python
import pytest
import fakeredis.aioredis


@pytest.fixture(autouse=False)
def fake_redis(mocker):
    fake = fakeredis.aioredis.FakeRedis()
    mocker.patch("backend.bus.redis_bus.RedisBus._get_redis", return_value=fake)
    return fake
```

- [ ] **Step 2: Write the gate test**

```python
# tests/test_e2e_spine.py
"""
Gate test for Stage 1 spine.
/goal 'draft a founder agreement' → Legal Agent → document returned.
All external calls (Gemini, llama.cpp, Supabase, Vertex AI) are mocked.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_gemini_parse(mocker):
    mock_model = MagicMock()
    mock_model.generate_content.return_value = MagicMock(text=json.dumps({
        "instruction": "draft a founder agreement for AcmeCo",
        "entities": {"company_name": "AcmeCo", "icp": "solo founders"},
        "constraints": {},
        "priority_agents": ["legal"],
    }))
    mocker.patch("backend.orchestrator.goal_parser.genai.GenerativeModel", return_value=mock_model)
    return mock_model


@pytest.fixture
def mock_gemini_dag(mocker):
    mock_model = MagicMock()
    mock_model.generate_content.return_value = MagicMock(text=json.dumps({
        "tasks": [{
            "task_id": "t_001",
            "agent": "legal",
            "depends_on": [],
            "instruction": "Draft a founder agreement for AcmeCo. Include equity split, roles, IP assignment, and vesting schedule.",
            "tools_available": ["doc_generator"],
            "constraints": {},
        }]
    }))
    mocker.patch("backend.orchestrator.dag_builder.genai.GenerativeModel", return_value=mock_model)
    return mock_model


@pytest.fixture
def mock_legal_agent_model(mocker):
    mock_client = MagicMock()
    founder_agreement_text = (
        "FOUNDER AGREEMENT\n\n"
        "1. EQUITY: Each founder receives 50% equity subject to 4-year vesting with 1-year cliff.\n"
        "2. ROLES: Founder A serves as CEO. Founder B serves as CTO.\n"
        "3. IP ASSIGNMENT: All IP created by founders is assigned to AcmeCo.\n"
        "4. VESTING: 4-year vesting schedule, 25% cliff after year 1, monthly thereafter.\n\n"
        "AI-generated document preparation — not legal advice. "
        "Review with a licensed attorney before signing."
    )
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({
            "status": "done",
            "output": {"document": founder_agreement_text, "doc_type": "founder_agreement"},
            "confidence": 0.92,
            "reasoning": "Generated founder agreement with standard clauses",
        })))]
    )
    mocker.patch("backend.agents.base.openai.OpenAI", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_db(mocker):
    tasks_store = {}
    goals_store = {}

    async def mock_persist_goal(goal_id, founder_id, instruction, constraints):
        goals_store[goal_id] = {"id": goal_id, "status": "pending", "instruction": instruction}

    async def mock_persist_tasks(goal_id, founder_id, tasks):
        for t in tasks:
            tasks_store[t["task_id"]] = {
                "id": t["task_id"], "goal_id": goal_id, "agent": t["agent"],
                "instruction": t["instruction"], "depends_on": t.get("depends_on", []),
                "context_bundle": {}, "tools_available": t.get("tools_available", []),
                "constraints": t.get("constraints", {}), "status": "pending",
            }

    call_count = {"get_ready": 0}

    async def mock_get_ready(goal_id):
        call_count["get_ready"] += 1
        if call_count["get_ready"] == 1:
            return [t for t in tasks_store.values() if t["status"] == "pending"]
        return []

    async def mock_has_in_progress(goal_id):
        return any(t["status"] == "in_progress" for t in tasks_store.values())

    async def mock_update_status(task_id, status, result=None):
        if task_id in tasks_store:
            tasks_store[task_id]["status"] = status

    async def mock_update_goal(goal_id, status, elapsed_seconds=None):
        if goal_id in goals_store:
            goals_store[goal_id]["status"] = status

    mocker.patch("backend.orchestrator.loop.persist_goal", side_effect=mock_persist_goal)
    mocker.patch("backend.orchestrator.loop.persist_task_graph", side_effect=mock_persist_tasks)
    mocker.patch("backend.orchestrator.loop.get_ready_tasks", side_effect=mock_get_ready)
    mocker.patch("backend.orchestrator.loop.has_in_progress_tasks", side_effect=mock_has_in_progress)
    mocker.patch("backend.orchestrator.loop.update_task_status", side_effect=mock_update_status)
    mocker.patch("backend.orchestrator.loop.update_goal_status", side_effect=mock_update_goal)
    mocker.patch("backend.orchestrator.loop.vector_store.write", new=AsyncMock())
    mocker.patch("backend.orchestrator.context_builder.vector_store.retrieve", new=AsyncMock(return_value=[]))
    mocker.patch("backend.agents.base.vector_store.retrieve", new=AsyncMock(return_value=[]))
    return tasks_store, goals_store


@pytest.mark.asyncio
async def test_spine_gate_draft_founder_agreement(
    mock_gemini_parse, mock_gemini_dag, mock_legal_agent_model, mock_db
):
    """
    GATE TEST — Stage 1 spine.
    /goal 'draft a founder agreement' must return a real document via Legal Agent.
    """
    from backend.orchestrator.loop import OrchestratorLoop

    loop = OrchestratorLoop()
    result = await loop.run_goal(
        goal_id="g_test_001",
        founder_id="f_test_001",
        raw_instruction="draft a founder agreement for AcmeCo",
        constraints={},
    )

    # Goal completed
    assert result["status"] == "done", f"Expected 'done', got: {result}"

    # At least one task result from Legal Agent
    assert len(result["results"]) >= 1
    legal_result = next(r for r in result["results"] if r["agent"] == "legal")

    # Output contains a document
    assert "document" in legal_result["output"], "Legal Agent must return a document in output"

    doc_text = legal_result["output"]["document"]
    assert len(doc_text) > 100, "Document must be non-trivial"

    # Disclaimer present
    assert "not legal advice" in doc_text.lower() or "not legal advice" in doc_text, \
        "Document must contain legal disclaimer"

    # No pending approvals for a draft (no payment taken)
    assert result["pending_approvals"] == [], "Draft document should not require approval"
```

- [ ] **Step 3: Run the gate test**

```bash
pytest tests/test_e2e_spine.py -v
```
Expected: 1 PASS — `test_spine_gate_draft_founder_agreement`

- [ ] **Step 4: Run full test suite**

```bash
pytest -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_e2e_spine.py
git commit -m "test: Stage 1 gate test — /goal → Legal Agent → document returned"
```

---

## Task 16: Start Server + Manual Smoke Test

- [ ] **Step 1: Copy env file and fill in values**

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY
# Leave AGENT_MODEL_BASE_URL=http://localhost:8080/v1 for llama.cpp
```

- [ ] **Step 2: Apply Supabase schema**

Run `supabase/schema.sql` in the Supabase dashboard SQL editor, or via CLI:
```bash
# If using Supabase CLI:
supabase db push
```

- [ ] **Step 3: Start llama.cpp server**

```bash
llama-server \
  -m /path/to/gemma-4-26B-A4B-it-Claude-Opus-Distill.q4_k_m.gguf \
  --host 0.0.0.0 --port 8080 \
  --ctx-size 32768 \
  -ngl 99
```

- [ ] **Step 4: Start Redis**

```bash
docker compose up -d
```

- [ ] **Step 5: Start FastAPI server**

```bash
uvicorn backend.main:app --reload --port 8000
```

- [ ] **Step 6: Send gate test request**

```bash
curl -X POST http://localhost:8000/goal \
  -H "Content-Type: application/json" \
  -d '{
    "founder_id": "f_test_001",
    "instruction": "draft a founder agreement for AcmeCo",
    "constraints": {}
  }'
```

Expected response shape:
```json
{
  "goal_id": "g_...",
  "status": "done",
  "results": [
    {
      "task_id": "t_...",
      "agent": "legal",
      "output": {
        "document": "FOUNDER AGREEMENT\n\n...\nAI-generated document preparation — not legal advice..."
      }
    }
  ],
  "pending_approvals": [],
  "elapsed_seconds": ...
}
```

- [ ] **Step 7: Verify gate**

Document in `results[0].output.document` must:
- Be non-empty
- Contain "not legal advice" disclaimer
- Contain real agreement content (equity, IP, vesting)

- [ ] **Step 8: Final commit**

```bash
git add .
git commit -m "chore: Stage 1 spine complete — gate test passing"
```

---

## Stage 1 Complete

**Gate achieved:** `/goal 'draft a founder agreement'` returns a real document via Legal Agent.

**Next plans:**
- `2026-05-23-stage2-agents.md` — Engineer 1: all 6 agents + orchestrator hardening
- `2026-05-23-stage3-dashboard.md` — Engineer 2: Next.js dashboard
- `2026-05-23-stage4-integration.md` — Both: Computer Use + onboarding + beta
