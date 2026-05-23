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
