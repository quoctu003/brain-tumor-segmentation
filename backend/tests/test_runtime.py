import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from test_api import FakeModel


def test_two_api_instances_cannot_share_process_owned_storage(config):
    with TestClient(create_app(config, FakeModel())) as first:
        with pytest.raises(RuntimeError, match="Another BrainTumor API"):
            with TestClient(create_app(config, FakeModel())):
                pytest.fail("The second API must not start")
        assert first.get("/api/health").status_code == 200
    # The lock must be released on clean shutdown.
    with TestClient(create_app(config, FakeModel())) as restarted:
        assert restarted.get("/api/health").status_code == 200
