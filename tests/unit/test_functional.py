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


def test_admin_create_company(admin_client):
    resp = admin_client.post("/admin/api/companies",
                             json={"name": "New Co", "ticker_symbol": "NCO", "industry": "Retail"})
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    dup = admin_client.post("/admin/api/companies",
                            json={"name": "New Co", "ticker_symbol": "nco", "industry": "Retail"})
    assert dup.status_code == 400 and "already exists" in dup.get_json()["error"]


def test_admin_create_company_validation(admin_client):
    resp = admin_client.post("/admin/api/companies", json={"name": "No ticker"})
    assert resp.status_code == 400
    assert "ticker_symbol" in resp.get_json()["error"]


def test_admin_create_bank(admin_client, app):
    from models import Bank
    body = {"name": "Siinqee Bank", "license_number": "LB/099", "bank_type": "Commercial Bank",
            "headquarters": "Addis Ababa", "established_year": "2021", "swift_code": "siqeetaa"}
    resp = admin_client.post("/admin/api/banks", json=body)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    with app.app_context():
        bank = Bank.query.filter_by(license_number="LB/099").one()
        assert bank.establishment_date.year == 2021 and bank.swift_code == "SIQEETAA"
    assert admin_client.post("/admin/api/banks", json=body).status_code == 400  # duplicate license


@pytest.mark.parametrize("body,fragment", [
    ({"name": "No License"}, "license_number"),
    ({"name": "Bad Year", "license_number": "LB/X1", "established_year": "abc"}, "number"),
    ({"name": "Future", "license_number": "LB/X2", "established_year": "3000"}, "out of range"),
])
def test_admin_create_bank_validation(admin_client, body, fragment):
    resp = admin_client.post("/admin/api/banks", json=body)
    assert resp.status_code == 400 and fragment in resp.get_json()["error"]


def test_admin_create_research_document(admin_client, client):
    body = {"title": "Coffee Export Outlook", "author": "NBE Research", "publication_date": "2025-02-01",
            "category": "Market Report", "document_type": "Market Analysis", "summary": "Exports up",
            "document_url": "https://example.org/coffee.pdf"}
    resp = admin_client.post("/admin/api/research-documents", json=body)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    doc_id = resp.get_json()["document"]["id"]
    doc = client.get(f"/api/research/documents/{doc_id}").get_json()
    assert doc["keywords"] == ["Market Report", "Author: NBE Research"]
    bad = admin_client.post("/admin/api/research-documents", json={**body, "publication_date": "01/02/2025"})
    assert bad.status_code == 400


def test_admin_create_listed_company(admin_client, client):
    body = {"name": "Zemen Bank", "ticker_symbol": "zmn", "sector": "Banking", "industry": "Commercial Banking",
            "listing_date": "2025-01-15", "market_cap": "1500000000", "description": ""}
    resp = admin_client.post("/admin/api/listed-companies", json=body)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert resp.get_json()["company"]["ticker_symbol"] == "ZMN"
    assert admin_client.post("/admin/api/listed-companies", json=body).status_code == 400
    found = client.post("/api/search/companies", json={"query": "Zemen"}).get_data(as_text=True)
    assert "ZMN" in found


def test_admin_create_user_then_login(admin_client, app):
    body = {"first_name": "Ana", "last_name": "Lyst", "email": "Analyst@Test.local", "username": "analyst1",
            "password": "longenough", "role": "analyst"}
    resp = admin_client.post("/admin/api/users", json=body)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    c = app.test_client()
    assert c.post("/auth/login", data={"email": "analyst@test.local", "password": "longenough"}).status_code == 302
    # analysts are not admins
    assert c.get("/admin").status_code in (302, 403)


@pytest.mark.parametrize("override,fragment", [
    ({"role": "superuser"}, "role"),
    ({"password": "short"}, "8 characters"),
    ({"email": "not-an-email"}, "email"),
    ({"email": "user@test.local"}, "already exists"),
    ({"username": "admin"}, "already taken"),
])
def test_admin_create_user_validation(admin_client, override, fragment):
    body = {"first_name": "A", "last_name": "B", "email": "new-user@test.local", "username": "newuser",
            "password": "longenough", "role": "user", **override}
    resp = admin_client.post("/admin/api/users", json=body)
    assert resp.status_code == 400 and fragment in resp.get_json()["error"]


@pytest.mark.parametrize("path", ["/admin/api/banks", "/admin/api/research-documents",
                                  "/admin/api/listed-companies", "/admin/api/users"])
def test_admin_create_endpoints_reject_regular_user(user_client, path):
    assert user_client.post(path, json={}).status_code in (302, 403)


# --------------------------------------------------------------------------- #
# Alerts, quick watchlist add, research downloads
# --------------------------------------------------------------------------- #

@pytest.fixture
def user_alert(app):
    from app import db
    from models import User, UserAlert
    with app.app_context():
        uid = User.query.filter_by(email="user@test.local").one().id
        alert = UserAlert(user_id=uid, alert_type="price", title="TBK above 100", message="m")
        db.session.add(alert)
        db.session.commit()
        return alert.id


def test_toggle_alert(user_client, user_alert):
    resp = user_client.put(f"/api/dashboard/alerts/{user_alert}", json={"is_active": False})
    assert resp.status_code == 200 and resp.get_json()["data"]["is_active"] is False
    assert user_client.put(f"/api/dashboard/alerts/{user_alert}", json={"is_active": "no"}).status_code == 400
    assert user_client.put(f"/api/dashboard/alerts/{user_alert}", json={"frequency": "hourly"}).status_code == 400


def test_alerts_are_private(admin_client, user_alert):
    assert admin_client.put(f"/api/dashboard/alerts/{user_alert}", json={"is_active": False}).status_code == 404
    assert admin_client.delete(f"/api/dashboard/alerts/{user_alert}").status_code == 404


def test_delete_alert(user_client, user_alert):
    assert user_client.delete(f"/api/dashboard/alerts/{user_alert}").status_code == 200
    assert user_client.delete(f"/api/dashboard/alerts/{user_alert}").status_code == 404


def test_quick_add_to_watchlist_by_ticker(app):
    c = app.test_client()
    c.post("/auth/register", data={"first_name": "W", "last_name": "L", "email": "wl@test.local",
                                   "password": "abcdef1", "confirm_password": "abcdef1"})
    c.post("/auth/login", data={"email": "wl@test.local", "password": "abcdef1"})
    resp = c.post("/api/watchlist/add", json={"ticker": "tbk"})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    wid = resp.get_json()["watchlist_id"]
    again = c.post("/api/watchlist/add", json={"ticker": "TBK"})
    assert again.status_code == 200 and "already" in again.get_json()["message"]
    lists = c.get("/api/dashboard/watchlists").get_json()["data"]
    assert [w["id"] for w in lists] == [wid]
    assert c.post("/api/watchlist/add", json={"ticker": "NOPE"}).status_code == 404
    assert c.post("/api/watchlist/add", json={}).status_code == 400


def test_quick_add_requires_login(client):
    assert client.post("/api/watchlist/add", json={"ticker": "TBK"}).status_code in (302, 401)


def test_research_download_tracking(client, app):
    from models import ResearchDocument
    with app.app_context():
        doc = ResearchDocument.query.order_by(ResearchDocument.id).first()
        doc_id, before = doc.id, doc.download_count or 0
    resp = client.post(f"/api/research/documents/{doc_id}/download")
    assert resp.status_code == 200 and resp.get_json()["download_count"] == before + 1
    # Viewing details is not a download.
    client.get(f"/api/research/documents/{doc_id}")
    with app.app_context():
        assert ResearchDocument.query.get(doc_id).download_count == before + 1
    assert client.post("/api/research/documents/999999/download").status_code == 404


@pytest.mark.parametrize("path", ["/api/research/documents/999999", "/api/banking/banks/999999",
                                  "/api/economic/sectors/999999", "/api/companies/999999"])
def test_missing_records_return_404_not_500(client, path):
    assert client.get(path).status_code == 404


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

# Pages the JS navigates to that were never built (window.location.href targets).
KNOWN_MISSING = {"/analytics", "/settings", "/research/documents/1", "/banking/1"}


def _frontend_urls():
    urls = set()
    for base in ("static/js", "templates"):
        for dirpath, _, files in os.walk(os.path.join(ROOT, base)):
            for f in files:
                text = open(os.path.join(dirpath, f), encoding="utf-8").read()
                for m in re.finditer(r"(?:fetch\(\s*|location\.href\s*=\s*)[`'\"](/[^`'\"?]+)", text):
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
    pytest.param(u, marks=pytest.mark.xfail(reason="frontend links to a page that was never implemented",
                                            strict=True))
    if u in KNOWN_MISSING else u
    for u in _frontend_urls()
])
def test_frontend_fetch_url_has_backend_route(url):
    assert _has_route(url)


# --------------------------------------------------------------------------- #
# Admin: financial statements and indicators
# --------------------------------------------------------------------------- #

def test_statement_dropdown_lists_listed_companies(admin_client):
    data = admin_client.get("/admin/api/listed-companies").get_json()
    assert data["success"] and "ETHT" in [c["ticker_symbol"] for c in data["companies"]]


def test_admin_create_financial_statement(admin_client, app):
    from models import FinancialStatement, ListedCompany
    with app.app_context():
        lid = ListedCompany.query.filter_by(ticker_symbol="ETHT").one().id
    body = {"company_id": str(lid), "statement_type": "income_statement", "reporting_period": "Q1-2025",
            "fiscal_year": "2025", "period_start_date": "2025-01-01", "period_end_date": "2025-03-31",
            "revenue": "1000", "net_income": "", "total_assets": None, "total_liabilities": None}
    resp = admin_client.post("/admin/api/financial-statements", json=body)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    with app.app_context():
        st = FinancialStatement.query.get(resp.get_json()["statement"]["id"])
        assert st.company_id == lid and float(st.revenue) == 1000 and st.net_income is None


@pytest.mark.parametrize("override,fragment", [
    ({"company_id": "999999"}, "not found"),
    ({"statement_type": "made_up"}, "statement_type"),
    ({"period_end_date": "2024-12-31"}, "on or after"),
    ({"revenue": "lots"}, "revenue must be a number"),
    ({"reporting_period": ""}, "reporting_period"),
])
def test_admin_create_financial_statement_validation(admin_client, app, override, fragment):
    from models import ListedCompany
    with app.app_context():
        lid = ListedCompany.query.first().id
    body = {"company_id": lid, "statement_type": "income_statement", "reporting_period": "Q1-2025",
            "fiscal_year": 2025, "period_start_date": "2025-01-01", "period_end_date": "2025-03-31", **override}
    resp = admin_client.post("/admin/api/financial-statements", json=body)
    assert resp.status_code == 400 and fragment in resp.get_json()["error"]


def test_admin_create_indicator_saves_all_fields(admin_client, app):
    from models import MacroIndicators
    body = {"date": "2031-03-31", "gdp_growth": "7.5", "inflation_rate": "18.2", "unemployment_rate": "3.1",
            "etb_usd": "120.5", "interest_rate": "15"}
    resp = admin_client.post("/admin/api/economic-indicators", json=body)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    with app.app_context():
        row = MacroIndicators.query.get(resp.get_json()["indicator"]["id"])
        assert (row.gdp_growth, row.inflation_rate, row.unemployment_rate, row.etb_usd, row.interest_rate) == \
            pytest.approx((7.5, 18.2, 3.1, 120.5, 15.0))
    dup = admin_client.post("/admin/api/economic-indicators", json=body)
    assert dup.status_code == 400 and "already exist" in dup.get_json()["error"]


@pytest.mark.parametrize("body,fragment", [
    ({}, "date"),
    ({"date": "31/03/2031", "gdp_growth": 1}, "YYYY-MM-DD"),
    ({"date": "2032-01-01"}, "at least one"),
    ({"date": "2032-01-01", "inflation_rate": "high"}, "number"),
])
def test_admin_create_indicator_validation(admin_client, body, fragment):
    resp = admin_client.post("/admin/api/economic-indicators", json=body)
    assert resp.status_code == 400 and fragment in resp.get_json()["error"]
