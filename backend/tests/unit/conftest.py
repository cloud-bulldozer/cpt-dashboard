import pytest
from vyper import Vyper

from app.services.crucible_svc import CrucibleService
from tests.unit.fake_elastic import FakeAsyncElasticsearch
from tests.unit.fake_elastic_service import FakeElasticService
from tests.unit.fake_splunk import FakeSplunkService


@pytest.fixture
def fake_config(monkeypatch):
    """Provide a fake configuration"""
    vyper = Vyper(config_name="ocpperf")
    vyper.set("TEST.url", "http://elastic.example.com:9200")
    vyper.set("TEST.indice", "cdmv9dev-hce")  # Created for test_hce.py
    vyper.set(
        "telco.config.job_url", "https://jenkins.telco.example.com/job/telco-tests"
    )  # Created for test_telco.py
    monkeypatch.setattr("app.config.get_config", lambda: vyper)


@pytest.fixture
def fake_elastic(monkeypatch, fake_config):
    """Replace the actual elastic client with a fake"""
    fake_elastic = FakeAsyncElasticsearch("http://elastic.example.com:9200")
    monkeypatch.setattr(
        "app.services.crucible_svc.AsyncElasticsearch",
        lambda *args, **kwargs: fake_elastic,
    )
    return fake_elastic


@pytest.fixture
def fake_elastic_service(monkeypatch, fake_config):
    """Replace the actual ElasticService with fake for commons testing"""
    fake_elastic_service = FakeElasticService("TEST")
    monkeypatch.setattr(
        "app.api.v1.commons.hce.ElasticService",
        lambda *args, **kwargs: fake_elastic_service,
    )
    monkeypatch.setattr(
        "app.api.v1.commons.ocm.ElasticService",
        lambda *args, **kwargs: fake_elastic_service,
    )
    monkeypatch.setattr(
        "app.api.v1.commons.ols.ElasticService",
        lambda *args, **kwargs: fake_elastic_service,
    )
    monkeypatch.setattr(
        "app.api.v1.commons.ocp.ElasticService",
        lambda *args, **kwargs: fake_elastic_service,
    )
    monkeypatch.setattr(
        "app.api.v1.commons.quay.ElasticService",
        lambda *args, **kwargs: fake_elastic_service,
    )
    monkeypatch.setattr(
        "app.api.v1.commons.utils.ElasticService",
        lambda *args, **kwargs: fake_elastic_service,
    )
    return fake_elastic_service


@pytest.fixture
def fake_splunk(monkeypatch, fake_config):
    """Replace the actual SplunkService with fake for telco testing"""
    fake_splunk = FakeSplunkService("TEST")
    monkeypatch.setattr(
        "app.api.v1.commons.telco.SplunkService", lambda configpath: fake_splunk
    )
    return fake_splunk


@pytest.fixture
async def fake_crucible(monkeypatch, fake_elastic):
    crucible = CrucibleService("TEST")
    crucible.versions = {"v8dev"}
    yield crucible
    await crucible.close()
