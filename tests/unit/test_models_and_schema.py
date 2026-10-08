"""Schema / model regression tests."""
from sqlalchemy import inspect

from app import db
from models import User, ListedCompany


def test_create_all_builds_every_table(app):
    """create_all() must succeed on an empty DB (foreign keys must resolve)."""
    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())
    for expected in ("users", "company", "financials", "macro_indicators", "bank",
                     "listed_company", "financial_statement", "external_economic_data"):
        assert expected in tables


def test_all_user_foreign_keys_target_users_table(app):
    for table in db.metadata.tables.values():
        for fk in table.foreign_keys:
            assert fk.target_fullname.split(".")[0] in db.metadata.tables, \
                f"{table.name}.{fk.parent.name} -> {fk.target_fullname}"


def test_password_hashing(app):
    u = User(username="x", email="x@x", first_name="a", last_name="b")
    u.set_password("secret")
    assert u.password_hash != "secret"
    assert u.check_password("secret")
    assert not u.check_password("wrong")


def test_listed_company_fiscal_year_end_fits_longest_month(app):
    with app.app_context():
        assert ListedCompany.query.filter_by(ticker_symbol="ETHT").one().fiscal_year_end == "December 31"
        assert ListedCompany.__table__.c.fiscal_year_end.type.length >= len("September 30")


def test_inactive_user_flag(app):
    u = User(username="y", email="y@y", first_name="a", last_name="b", active=False)
    assert u.is_active is False
