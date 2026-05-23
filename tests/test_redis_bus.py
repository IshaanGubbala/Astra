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
