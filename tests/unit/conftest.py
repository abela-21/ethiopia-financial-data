"""
Pytest fixtures for the in-process test suite.

Runs the Flask app with its test client against a throwaway database,
so no live server or network is needed. Set TEST_DATABASE_URL to a
PostgreSQL database to exercise the Postgres-only raw SQL (NOW(), etc.);
otherwise a temporary SQLite file is used and those tests are skipped.
"""
import os
import sys
import tempfile
from datetime import date, datetime

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

_tmpdir = tempfile.mkdtemp(prefix="ethdata-tests-")
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", f"sqlite:///{os.path.join(_tmpdir, 'test.db')}"
)

from app import app as flask_app, db, limiter  # noqa: E402
from models import (  # noqa: E402
    User, Company, Financial, MacroIndicators, Bank, BankFinancialMetric,
    EconomicSector, ResearchDocument, ListedCompany, FinancialStatement,
)

IS_POSTGRES = os.environ["DATABASE_URL"].startswith("postgres")
postgres_only = pytest.mark.skipif(not IS_POSTGRES, reason="raw SQL in this route is PostgreSQL-specific")

ADMIN_EMAIL = "admin@test.local"
ADMIN_PASSWORD = "AdminPass123!"
USER_EMAIL = "user@test.local"
USER_PASSWORD = "UserPass123!"


def _seed():
    admin = User(username="admin", email=ADMIN_EMAIL, first_name="Ad", last_name="Min", role="admin")
    admin.set_password(ADMIN_PASSWORD)
    user = User(username="user", email=USER_EMAIL, first_name="Us", last_name="Er", role="user")
    user.set_password(USER_PASSWORD)
    db.session.add_all([admin, user])

    company = Company(name="Test Bank S.C.", ticker="TBK", sector="Banking",
                      industry="Commercial Banking", shares_outstanding=1_000_000)
    db.session.add(company)
    db.session.flush()
    db.session.add(Financial(company_id=company.id, year=2024, period="Annual",
                             revenue=1000.0, net_income=100.0,
                             total_assets=5000.0, total_liabilities=4000.0, total_equity=1000.0))

    db.session.add_all([
        MacroIndicators(date=date(2024, 3, 31), gdp_growth=7.2, inflation_rate=26.6,
                        unemployment_rate=3.5, etb_usd=56.5),
        MacroIndicators(date=date(2024, 6, 30), gdp_growth=7.0, inflation_rate=23.9,
                        unemployment_rate=3.4, etb_usd=57.1),
    ])

    bank = Bank(name="Commercial Bank of Ethiopia", bank_type="Commercial",
                ownership_type="State", license_number="LB/001")
    db.session.add(bank)
    db.session.add(EconomicSector(sector_name="Agriculture", sector_code="AGR"))
    db.session.add(ResearchDocument(title="Ethiopia Economic Outlook", document_type="report",
                                    entity_type="economy", publication_date=date(2024, 1, 15)))

    listed = ListedCompany(name="Ethio Telecom", ticker_symbol="ETHT", sector="Telecommunications", industry="Telecom Services",
                           listing_date=date(2021, 6, 14),
                           fiscal_year_end="December 31")
    db.session.add(listed)
    db.session.flush()
    db.session.add(FinancialStatement(company_id=listed.id, statement_type="income_statement",
                                      reporting_period="FY-2024", fiscal_year=2024,
                                      period_start_date=date(2023, 7, 1),
                                      period_end_date=date(2024, 6, 30), revenue=1e9))
    db.session.commit()


@pytest.fixture(scope="session")
def app():
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    limiter.enabled = False
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        _seed()
    yield flask_app
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """External APIs must never be hit from unit tests."""
    import requests

    def blocked(*args, **kwargs):
        raise requests.ConnectionError("network disabled in tests")

    monkeypatch.setattr(requests.Session, "request", blocked)


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, email, password):
    return client.post("/auth/login", data={"email": email, "password": password})


@pytest.fixture
def admin_client(app):
    c = app.test_client()
    resp = _login(c, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert resp.status_code == 302
    return c


@pytest.fixture
def user_client(app):
    c = app.test_client()
    resp = _login(c, USER_EMAIL, USER_PASSWORD)
    assert resp.status_code == 302
    return c
