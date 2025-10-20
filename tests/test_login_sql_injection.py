import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_attempts():
    main_module._attempts.clear()
    yield
    main_module._attempts.clear()


def test_login_should_not_allow_sql_injection():
    payload = {"username": "admin'-- ", "password": "x"}
    resp = client.post("/login", json=payload)
    assert resp.status_code in {401, 422}, "SQLi-бэйпас логина должен быть закрыт"


def test_login_succeeds_with_valid_credentials():
    payload = {"username": "admin", "password": "admin"}
    resp = client.post("/login", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"] == "admin"
    assert body["token"], "ожидаем получить токен"


def test_login_rejects_invalid_username_pattern():
    payload = {"username": "bad space", "password": "validpass"}
    resp = client.post("/login", json=payload)
    assert resp.status_code == 422


def test_login_rejects_too_long_username():
    payload = {"username": "a" * 60, "password": "validpass"}
    resp = client.post("/login", json=payload)
    assert resp.status_code == 422


def test_login_rate_limiter_blocks_after_threshold():
    payload = {"username": "admin", "password": "badpass"}
    for _ in range(5):
        resp = client.post("/login", json=payload)
        assert resp.status_code == 401
    resp = client.post("/login", json=payload)
    assert resp.status_code == 429
