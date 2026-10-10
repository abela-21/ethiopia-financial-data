"""CSRF protection, API tokens and secret handling."""
import re

import pytest

from conftest import ADMIN_EMAIL, ADMIN_PASSWORD, USER_EMAIL, USER_PASSWORD


@pytest.fixture
def csrf_on(app):
    app.config["WTF_CSRF_ENABLED"] = True
    yield
    app.config["WTF_CSRF_ENABLED"] = False


def _token(client, path="/auth/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


# --------------------------------------------------------------------------- #
# CSRF
# --------------------------------------------------------------------------- #

def test_login_form_without_token_is_rejected(client, csrf_on):
    resp = client.post("/auth/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 302 and "/auth/login" in resp.headers["Location"]
    # Not logged in: admin page still redirects to login.
    assert "/auth/login" in client.get("/admin").headers["Location"]


def test_login_form_with_token_succeeds(client, csrf_on):
    token = _token(client)
    resp = client.post("/auth/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
                                            "csrf_token": token})
    assert resp.status_code == 302 and "/dashboard" in resp.headers["Location"]


def test_login_form_contains_hidden_token(client):
    assert b'name="csrf_token"' in client.get("/auth/login").data
    assert b'name="csrf_token"' in client.get("/auth/register").data


def test_json_post_without_header_is_rejected(admin_client, csrf_on):
    resp = admin_client.post("/api/dashboard/watchlists", json={"name": "x"})
    assert resp.status_code == 400
    assert "CSRF" in resp.get_json()["error"]


def test_json_post_with_header_succeeds(admin_client, csrf_on):
    token = _token(admin_client, "/dashboard")
    resp = admin_client.post("/api/dashboard/watchlists", json={"name": "csrf ok"},
                             headers={"X-CSRFToken": token})
    assert resp.status_code == 200, resp.get_data(as_text=True)


def test_every_page_exposes_csrf_meta_tag(client):
    assert b'name="csrf-token"' in client.get("/").data


# --------------------------------------------------------------------------- #
# API tokens and the JWT-protected company API
# --------------------------------------------------------------------------- #

def _jwt(client, email, password):
    resp = client.post("/auth/token", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def test_token_endpoint_rejects_bad_credentials(client):
    assert client.post("/auth/token", json={"email": ADMIN_EMAIL, "password": "nope"}).status_code == 401
    assert client.post("/auth/token", json={}).status_code == 401


def test_token_endpoint_works_with_csrf_enabled(client, csrf_on):
    assert client.post("/auth/token", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).status_code == 200


def test_company_api_requires_token(client):
    assert client.post("/api/companies", json={"name": "X", "ticker": "X", "industry": "Y"}).status_code == 401


def test_company_api_rejects_non_admin(client):
    headers = _jwt(client, USER_EMAIL, USER_PASSWORD)
    resp = client.post("/api/companies", json={"name": "X", "ticker": "XUSR", "industry": "Y"}, headers=headers)
    assert resp.status_code == 403


def test_company_api_create_and_duplicate(client, csrf_on):
    headers = _jwt(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    body = {"name": "Api Co", "ticker": "APICO", "industry": "Retail"}
    resp = client.post("/api/companies", json=body, headers=headers)
    assert resp.status_code == 201, resp.get_data(as_text=True)
    assert resp.get_json()["ticker"] == "APICO"
    assert client.post("/api/companies", json=body, headers=headers).status_code == 409


def test_company_api_validation_error(client):
    headers = _jwt(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    resp = client.post("/api/companies", json={"name": "No Ticker"}, headers=headers)
    assert resp.status_code == 400
    assert "ticker is required" in resp.get_json()["error"]


# --------------------------------------------------------------------------- #
# Secrets and error pages
# --------------------------------------------------------------------------- #

def test_production_refuses_default_secrets(monkeypatch):
    from app import _check_secrets
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        _check_secrets()
    monkeypatch.setenv("SESSION_SECRET", "s")
    monkeypatch.setenv("JWT_SECRET_KEY", "j")
    _check_secrets()


def test_html_404_for_pages_json_404_for_api(client):
    page = client.get("/no-such-page", headers={"Accept": "text/html"})
    assert page.status_code == 404 and b"<html" in page.data
    api = client.get("/api/no-such-endpoint")
    assert api.status_code == 404 and api.is_json
