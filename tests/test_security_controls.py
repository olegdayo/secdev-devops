import hashlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app


@app.get("/__test__/boom")
def _boom():
    raise RuntimeError("boom secret=42")


def test_security_headers_present():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert resp.headers["Content-Security-Policy"] == "default-src 'self'"


def test_unhandled_exception_returns_generic_body(caplog: pytest.LogCaptureFixture):
    caplog.set_level("ERROR", logger="secdev")
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/__test__/boom")
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal error"}
    assert "secret=42" not in caplog.text


def test_login_failure_does_not_log_password(caplog: pytest.LogCaptureFixture):
    caplog.set_level("INFO", logger="secdev")
    main_module._attempts.clear()
    client = TestClient(app)
    resp = client.post("/login", json={"username": "admin", "password": "wrongpass"})
    assert resp.status_code == 401
    assert "wrongpass" not in caplog.text
    assert "adm***" in caplog.text


def test_app_uses_env_configuration():
    project_root = Path(__file__).resolve().parents[1]
    script = textwrap.dedent(
        """
        import json
        import os
        from fastapi.testclient import TestClient
        import importlib
        import app.main as main_module

        os.environ["APP_NAME"] = "env-app"
        os.environ["SECRET_KEY"] = "env-secret"
        importlib.reload(main_module)
        client = TestClient(main_module.app)
        response = client.post("/login", json={"username": "admin", "password": "admin"})
        data = response.json()
        print(json.dumps({"title": main_module.app.title, "token": data.get("token")}))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=os.environ.copy(),
    )
    assert result.returncode == 0, result.stderr
    output = result.stdout.strip().splitlines()[-1]
    payload = json.loads(output)
    assert payload["title"] == "env-app"
    expected_token = hashlib.sha256(b"admin:env-secret").hexdigest()
    assert payload["token"] == expected_token
