from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_should_not_return_all_on_injection():
    resp_noise = client.get("/search", params={"q": "zzzzzzzzz"})
    inj = client.get("/search", params={"q": "' OR '1'='1"})
    assert resp_noise.status_code == 200
    assert inj.status_code == 200
    data_noise = resp_noise.json()
    data_inj = inj.json()
    assert len(data_inj["items"]) <= len(
        data_noise["items"]
    ), "Инъекция в LIKE не должна приводить к выдаче всех элементов"


def test_search_rejects_too_long_query():
    resp = client.get("/search", params={"q": "a" * 64})
    assert resp.status_code == 422
