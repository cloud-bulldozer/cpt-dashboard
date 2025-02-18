import pytest
from vyper import Vyper

from app.services.crucible_svc import CrucibleService
from tests.fake_elastic import FakeAsyncElasticsearch


@pytest.fixture
def fake_config(monkeypatch):
    """Provide a fake configuration"""

    vyper = Vyper(config_name="ocpperf")
    vyper.set("TEST.url", "http://elastic.example.com:9200")
    monkeypatch.setattr("app.config.get_config", lambda: vyper)


@pytest.fixture
def fake_elastic(monkeypatch, fake_config):
    """Replace the actual elastic client with a fake"""

    monkeypatch.setattr(
        "app.services.crucible_svc.AsyncElasticsearch", FakeAsyncElasticsearch
    )


@pytest.fixture
async def fake_crucible(fake_elastic):
    crucible = CrucibleService("TEST")
    yield crucible
    await crucible.close()
