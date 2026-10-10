"""The admin refresh actions must never lose existing data."""
from datetime import date

import pytest

from app import db
from models import Bank, ExternalEconomicData, MacroIndicators, ResearchDocument


class FakeIntegrator:
    def __init__(self, records=None, fail=False):
        self.records = records or []
        self.fail = fail

    def get_world_bank_ethiopia_data(self, only=None):
        if self.fail:
            raise ConnectionError("offline")
        return [r for r in self.records if not only or r["indicator_code"] in only]


def _record(code, value, year=2023):
    return {"date": f"{year}-12-31", "indicator_code": code, "indicator_name": code,
            "value": value, "country": "Ethiopia", "source": "World Bank", "unit": "%"}


@pytest.fixture
def clean_external(app):
    with app.app_context():
        ExternalEconomicData.query.delete()
        MacroIndicators.query.filter(MacroIndicators.date >= date(2030, 1, 1)).delete()
        db.session.commit()
    yield
    with app.app_context():
        ExternalEconomicData.query.delete()
        MacroIndicators.query.filter(MacroIndicators.date >= date(2030, 1, 1)).delete()
        db.session.commit()


def test_refresh_offline_with_no_cache_changes_nothing(app, clean_external):
    from utils.indicator_refresh import refresh_macro_indicators
    with app.app_context():
        before = MacroIndicators.query.count()
        result = refresh_macro_indicators(integrator=FakeIntegrator(fail=True), today=date(2030, 1, 1))
        assert result["success"] is False
        assert MacroIndicators.query.count() == before


def test_refresh_stores_fetched_data_and_creates_todays_row(app, clean_external):
    from utils.indicator_refresh import refresh_macro_indicators
    records = [_record("NY.GDP.MKTP.KD.ZG", 6.5), _record("NY.GDP.MKTP.KD.ZG", 7.1, 2022),
               _record("FP.CPI.TOTL.ZG", 30.2), _record("NE.EXP.GNFS.CD", 100.0),
               _record("NE.IMP.GNFS.CD", 160.0)]
    with app.app_context():
        before = MacroIndicators.query.count()
        result = refresh_macro_indicators(integrator=FakeIntegrator(records), today=date(2030, 1, 1))
        assert result["success"] and result["fetched"] == 5
        assert MacroIndicators.query.count() == before + 1
        row = MacroIndicators.query.filter_by(date=date(2030, 1, 1)).one()
        assert row.gdp_growth == pytest.approx(6.5)  # latest year wins
        assert row.trade_balance == pytest.approx(-60.0)


def test_refresh_falls_back_to_cache_and_keeps_other_fields(app, clean_external):
    from utils.indicator_refresh import refresh_macro_indicators
    with app.app_context():
        refresh_macro_indicators(integrator=FakeIntegrator([_record("FP.CPI.TOTL.ZG", 30.2)]),
                                 today=date(2030, 1, 1))
        row = MacroIndicators.query.filter_by(date=date(2030, 1, 1)).one()
        row.interest_rate = 15.0  # admin-entered value
        db.session.commit()

        result = refresh_macro_indicators(integrator=FakeIntegrator(fail=True), today=date(2030, 1, 1))
        assert result["success"] and result["used_cache"]
        row = MacroIndicators.query.filter_by(date=date(2030, 1, 1)).one()
        assert row.inflation_rate == pytest.approx(30.2)
        assert row.interest_rate == pytest.approx(15.0)


def test_refresh_api_offline_returns_503_and_keeps_data(admin_client, app, clean_external):
    with app.app_context():
        before = MacroIndicators.query.count()
    resp = admin_client.post("/admin/api/refresh-data")  # network is blocked in tests
    assert resp.status_code == 503
    assert resp.get_json()["success"] is False
    with app.app_context():
        assert MacroIndicators.query.count() == before


def test_full_reset_requires_confirmation(admin_client):
    resp = admin_client.post("/admin/data/refresh", json={})
    assert resp.status_code == 400


def test_full_reset_is_admin_only(user_client):
    resp = user_client.post("/admin/data/refresh", json={"confirm": "RESET"})
    assert resp.status_code in (302, 403)


def test_full_reset_failure_rolls_back_everything(admin_client, app, monkeypatch):
    from scripts.data_migration import EthiopianDataMigration

    def boom(self):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(EthiopianDataMigration, "load_research_documents", boom)
    with app.app_context():
        banks, docs, macro = Bank.query.count(), ResearchDocument.query.count(), MacroIndicators.query.count()
    resp = admin_client.post("/admin/data/refresh", json={"confirm": "RESET"})
    assert resp.status_code == 500
    with app.app_context():
        assert Bank.query.count() == banks
        assert ResearchDocument.query.count() == docs
        assert MacroIndicators.query.count() == macro


def test_full_reset_keeps_macro_history(admin_client, app):
    with app.app_context():
        macro = MacroIndicators.query.count()
    resp = admin_client.post("/admin/data/refresh", json={"confirm": "RESET"})
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    with app.app_context():
        assert MacroIndicators.query.count() == macro
        assert Bank.query.count() == 18
        # Sequences must be past the explicit seed ids so new banks can be added.
        db.session.add(Bank(name="New Bank", license_number="LB/NEW"))
        db.session.commit()
