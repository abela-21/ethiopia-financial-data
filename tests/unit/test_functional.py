"""Functional tests for user-facing features and admin data management."""
import io
import json
import os
import re

import pytest

from app import app as flask_app
from conftest import postgres_only

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --------------------------------------------------------------------------- #
# Public data APIs
# --------------------------------------------------------------------------- #

def test_macro_latest_returns_most_recent_quarter(client):
    resp = client.get("/api/macro/latest")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["as_of"] == "2024-06-30"


def test_companies_api_lists_seeded_company(client):
    resp = client.get("/api/companies")
    assert resp.status_code == 200
    assert "TBK" in resp.get_data(as_text=True)


def test_company_detail_page(client, app):
    from models import Company
    with app.app_context():
        cid = Company.query.filter_by(ticker="TBK").one().id
    assert client.get(f"/companies/{cid}").status_code == 200
    assert client.get("/companies/999999").status_code in (302, 404)


def test_banking_api_lists_bank(client):
    resp = client.get("/api/banking/banks")
    assert resp.status_code == 200
    assert "Commercial Bank of Ethiopia" in resp.get_data(as_text=True)


def test_research_documents_api(client):
    resp = client.get("/api/research/documents")
    assert resp.status_code == 200
    assert "Ethiopia Economic Outlook" in resp.get_data(as_text=True)


# --------------------------------------------------------------------------- #
# Advanced search (POST /api/search/companies is what static/js/search.js calls)
# --------------------------------------------------------------------------- #

def test_advanced_search_post(client):
    resp = client.post("/api/search/companies", json={"query": "Ethio"})
    assert resp.status_code == 200
    assert "ETHT" in resp.get_data(as_text=True)


def test_advanced_search_sector_filter_excludes(client):
    resp = client.post("/api/search/companies", json={"sectors": ["Mining"]})
    assert resp.status_code == 200
    assert "ETHT" not in resp.get_data(as_text=True)


def test_search_filter_options(client):
    assert client.get("/api/search/filters/options").status_code == 200


# --------------------------------------------------------------------------- #
# User dashboard: watchlists (paths match static/js/dashboard.js)
# --------------------------------------------------------------------------- #

def test_dashboard_requires_login(client):
    assert client.get("/api/dashboard/stats").status_code in (302, 401)


def test_dashboard_stats(user_client):
    assert user_client.get("/api/dashboard/stats").status_code == 200


def test_watchlist_lifecycle(user_client, app):
    from models import Company
    with app.app_context():
        cid = Company.query.filter_by(ticker="TBK").one().id

    resp = user_client.post("/api/dashboard/watchlists", json={"name": "Banks"})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    wid = resp.get_json()["data"]["id"]

    resp = user_client.post(f"/api/dashboard/watchlists/{wid}/companies", json={"company_id": cid})
    assert resp.status_code == 200, resp.get_data(as_text=True)

    resp = user_client.get(f"/api/dashboard/watchlists/{wid}/companies")
    assert resp.status_code == 200
    assert "TBK" in resp.get_data(as_text=True)

    assert user_client.put(f"/api/dashboard/watchlists/{wid}", json={"name": "Renamed"}).status_code == 200
    assert user_client.delete(f"/api/dashboard/watchlists/{wid}").status_code == 200
    assert user_client.get(f"/api/dashboard/watchlists/{wid}/companies").status_code == 404


def test_watchlist_requires_name(user_client):
    assert user_client.post("/api/dashboard/watchlists", json={}).status_code == 400


def test_watchlist_is_private_to_owner(user_client, admin_client):
    wid = user_client.post("/api/dashboard/watchlists", json={"name": "Mine"}).get_json()["data"]["id"]
    assert admin_client.get(f"/api/dashboard/watchlists/{wid}/companies").status_code == 404
    assert admin_client.delete(f"/api/dashboard/watchlists/{wid}").status_code == 404


# --------------------------------------------------------------------------- #
# Exports
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("fmt,ctype", [("csv", "text/csv"), ("json", "application/json"),
                                       ("excel", "spreadsheet")])
def test_macro_export_formats(user_client, fmt, ctype):
    resp = user_client.post("/api/export/macro-indicators", json={"format": fmt})
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    assert ctype in resp.headers["Content-Type"]


def test_export_rejects_unknown_format(user_client):
    resp = user_client.post("/api/export/macro-indicators", json={"format": "docx"})
    assert resp.status_code == 400


def test_companies_export_csv(user_client):
    resp = user_client.post("/api/export/companies", json={"format": "csv"})
    assert resp.status_code == 200
    assert b"TBK" in resp.data or b"Test Bank" in resp.data


# --------------------------------------------------------------------------- #
# Admin data management
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("ttype", ["companies", "financial", "macro"])
def test_admin_template_downloads(admin_client, ttype, monkeypatch):
    monkeypatch.chdir(ROOT)
    resp = admin_client.get(f"/admin/bulk-import/templates/{ttype}")
    assert resp.status_code == 200
    assert resp.data[:2] == b"PK"  # xlsx is a zip


def test_admin_template_unknown_type(admin_client):
    assert admin_client.get("/admin/bulk-import/templates/nope").status_code == 404


def test_admin_get_indicator(admin_client, app):
    from models import MacroIndicators
    with app.app_context():
        iid = MacroIndicators.query.order_by(MacroIndicators.date).first().id
    resp = admin_client.get(f"/admin/api/indicator/{iid}")
    assert resp.status_code == 200
    assert resp.get_json()["indicator"]["gdp_growth"] == pytest.approx(7.2)


@pytest.mark.xfail(reason="get_or_404 inside a broad except: missing indicator returns 500, not 404",
                   strict=True)
def test_admin_get_missing_indicator_is_404(admin_client):
    assert admin_client.get("/admin/api/indicator/999999").status_code == 404


def test_admin_update_indicator(admin_client, app):
    from models import MacroIndicators
    with app.app_context():
        iid = MacroIndicators.query.order_by(MacroIndicators.date.desc()).first().id
    resp = admin_client.put(f"/admin/api/indicator/{iid}", json={"inflation_rate": 22.2})
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    with app.app_context():
        assert MacroIndicators.query.get(iid).inflation_rate == pytest.approx(22.2)


@postgres_only
def test_admin_create_company(admin_client):
    resp = admin_client.post("/admin/api/companies",
                             json={"name": "New Co", "ticker_symbol": "NCO", "industry": "Retail"})
    assert resp.status_code in (200, 201), resp.get_data(as_text=True)[:300]


def test_bulk_import_companies_csv(admin_client, monkeypatch):
    monkeypatch.chdir(ROOT)
    csv = b"name,ticker,sector,industry\nBulk Co,BLK,Retail,Supermarkets\n"
    resp = admin_client.post("/admin/bulk-import/upload",
                             data={"data_type": "companies", "file": (io.BytesIO(csv), "c.csv")},
                             content_type="multipart/form-data")
    assert resp.status_code in (200, 302), resp.get_data(as_text=True)[:300]


def test_bulk_import_rejects_missing_file(admin_client):
    resp = admin_client.post("/admin/bulk-import/upload", data={"data_type": "companies"},
                             content_type="multipart/form-data")
    assert resp.status_code in (200, 302, 400)
    if resp.is_json:
        assert resp.get_json()["success"] is False


# --------------------------------------------------------------------------- #
# Frontend <-> backend contract: every fetch() URL in the JS must have a route.
# --------------------------------------------------------------------------- #

KNOWN_MISSING = {
    "/admin/api/banks", "/admin/api/listed-companies", "/admin/api/research-documents",
    "/admin/api/users", "/api/dashboard/alerts/1", "/api/research/documents/1/download",
    "/api/watchlist/add",
}


def _frontend_urls():
    urls = set()
    for base in ("static/js", "templates"):
        for dirpath, _, files in os.walk(os.path.join(ROOT, base)):
            for f in files:
                text = open(os.path.join(dirpath, f), encoding="utf-8").read()
                for m in re.finditer(r"fetch\(\s*[`'\"](/[^`'\"?]+)", text):
                    urls.add(re.sub(r"\$\{[^}]*\}", "1", m.group(1)))
    return sorted(urls)


def _has_route(path):
    adapter = flask_app.url_map.bind("localhost")
    for method in ("GET", "POST", "PUT", "DELETE"):
        try:
            adapter.match(path, method=method)
            return True
        except Exception:
            continue
    return False


@pytest.mark.parametrize("url", [
    pytest.param(u, marks=pytest.mark.xfail(reason="frontend calls an endpoint that was never implemented",
                                            strict=True))
    if u in KNOWN_MISSING else u
    for u in _frontend_urls()
])
def test_frontend_fetch_url_has_backend_route(url):
    assert _has_route(url)
