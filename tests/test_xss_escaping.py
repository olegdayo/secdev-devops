from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_echo_should_escape_script_tags():
    resp = client.get("/echo", params={"msg": "<script>alert(1)</script>"})
    assert "<script>" not in resp.text


def test_echo_should_escape_img_onerror():
    resp = client.get("/echo", params={"msg": "<img src=x onerror=alert(1)>"})
    assert "<img" not in resp.text
    assert "&lt;img" in resp.text
