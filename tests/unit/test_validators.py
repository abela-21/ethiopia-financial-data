"""Unit tests for utils.validators."""
import pytest

from utils.validators import validate_company_data, validate_financial_data, validate_stock_data

GOOD_COMPANY = {"name": "Awash Bank", "ticker": "AWB", "industry": "Banking",
                "website": "https://awashbank.com", "shares_outstanding": 1000}


def test_valid_company_has_no_errors():
    assert validate_company_data(GOOD_COMPANY) == []


@pytest.mark.parametrize("field", ["name", "ticker", "industry"])
def test_company_required_fields(field):
    errors = validate_company_data({**GOOD_COMPANY, field: "  "})
    assert f"{field} is required" in errors


@pytest.mark.parametrize("override,fragment", [
    ({"ticker": "TOO-LONG-TICKER"}, "10 characters"),
    ({"ticker": "A-B"}, "letters and numbers"),
    ({"name": "x" * 101}, "100 characters"),
    ({"website": "not a url"}, "website URL"),
    ({"shares_outstanding": -5}, "positive"),
    ({"shares_outstanding": "abc"}, "valid number"),
])
def test_company_invalid_values(override, fragment):
    errors = validate_company_data({**GOOD_COMPANY, **override})
    assert any(fragment in e for e in errors), errors


def test_financial_required_fields():
    errors = validate_financial_data({})
    for f in ("company_id", "year", "period"):
        assert f"{f} is required" in errors


def test_valid_financial_minimal():
    assert validate_financial_data({"company_id": 1, "year": 2024, "period": "Annual"}) == []


@pytest.mark.parametrize("override,fragment", [
    ({"year": 1800}, "between 1900 and 2100"),
    ({"year": "abc"}, "valid number"),
    ({"period": "FY"}, "Period must be one of"),
    ({"revenue": "lots"}, "revenue must be a valid number"),
])
def test_financial_invalid_values(override, fragment):
    data = {"company_id": 1, "year": 2024, "period": "Annual", **override}
    assert any(fragment in e for e in validate_financial_data(data))


def test_stock_validator_returns_list():
    assert isinstance(validate_stock_data({}), list)
