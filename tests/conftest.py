import pytest
import fakeredis.aioredis


@pytest.fixture(autouse=False)
def fake_redis(mocker):
    fake = fakeredis.aioredis.FakeRedis()
    mocker.patch("backend.bus.redis_bus.RedisBus._get_redis", return_value=fake)
    return fake
