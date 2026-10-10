"""
Load companies, financials, macro indicators and stock prices from the CSV files in Data/.

Usage:
    python Data/load_data.py            # load only into tables that are empty
    python Data/load_data.py --reset    # delete company/financial/macro data first

User accounts are never touched; create the admin with scripts/create_admin.py.
"""
import argparse
import pandas as pd
from datetime import datetime
import sys
from typing import Dict, Any
import logging
import os
from sqlalchemy import func
from sqlalchemy.sql import text

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DATA_DIR)
sys.path.insert(0, PROJECT_ROOT)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join(DATA_DIR, 'data_loading.log')
)

from app import create_app, db
from models import MacroIndicators, Company, Financial, Stock


def data_file(name):
    return os.path.join(DATA_DIR, name)

# Global variable for the Flask app instance, will be initialized in main()
app = None

def validate_financial_data(row: Dict[str, Any]) -> bool:
    """Validate financial data before insertion"""
    try:
        # Balance sheet validation
        if round(row["total_assets"] - (row["total_liabilities"] + row["total_equity"]), 2) != 0:
            logging.error(f"Balance sheet doesn't balance for company {row['company_id']}, year {row['year']}")
            return False

        # Income statement validation (EBITDA consistency check added here)
        # Assuming operating_income and depreciation/amortization contribute to EBITDA
        # For simplicity, if EBITDA is provided, we can validate gross_profit as before
        if round(row["gross_profit"] - (row["revenue"] - row["cost_of_revenue"]), 2) != 0:
            logging.error(f"Gross profit calculation error for company {row['company_id']}, year {row['year']}")
            return False

        # Asset composition validation
        if row["total_current_assets"] > row["total_assets"]:
            logging.error(f"Current assets exceed total assets for company {row['company_id']}, year {row['year']}")
            return False

        # Ratio validations
        if row["current_ratio"] < 0 or row["current_ratio"] > 5:
            logging.error(f"Unusual current ratio for company {row['company_id']}, year {row['year']}")
            return False

        if row["return_on_equity"] < -100 or row["return_on_equity"] > 100:
            logging.error(f"Unusual ROE for company {row['company_id']}, year {row['year']}")
            return False

        return True
    except KeyError as e:
        logging.error(f"Missing required field in financial data: {e} for row {row.get('company_id')}, year {row.get('year')}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in financial data validation: {e} for row {row.get('company_id')}, year {row.get('year')}")
        return False

def validate_macro_data(row: Dict[str, Any]) -> bool:
    """Validate macro indicators data with comprehensive checks"""
    try:
        # Basic range validations
        validations = {
            "gdp_growth": (-15, 15),        # Historical range for Ethiopia
            "inflation_rate": (0, 50),       # Max observed was around 44%
            "interest_rate": (0, 20),        # NBE policy rates range
            "npl_ratio": (0, 15),           # Banking sector health threshold
            "etb_usd": (20, 150),           # Exchange rate range
            "fx_reserves": (1000, 10000)     # In millions USD
        }

        for field, (min_val, max_val) in validations.items():
            if row.get(field) is not None:
                try:
                    if not min_val <= float(row[field]) <= max_val:
                        logging.error(f"{field} ({row[field]}) out of range ({min_val}-{max_val}) for date {row['date']}")
                        return False
                except ValueError:
                    logging.error(f"Invalid numeric value for {field}: {row[field]} for date {row['date']}")
                    return False

        # Trade balance validation
        if row.get("exports") and row.get("imports"):
            try:
                calculated_balance = round(float(row["exports"]) - float(row["imports"]), 2)
                if row.get("trade_balance") is not None and round(float(row["trade_balance"]), 2) != calculated_balance:
                    logging.error(f"Trade balance mismatch for date {row['date']}")
                    return False
            except ValueError:
                logging.error(f"Invalid numeric value for exports/imports/trade_balance for date {row['date']}")
                return False

        # Required fields validation
        required_fields = ["date", "gdp_growth", "inflation_rate", "interest_rate", "etb_usd"]
        for field in required_fields:
            if field not in row or pd.isna(row[field]):
                logging.error(f"Missing required field: {field} for date {row.get('date')}")
                return False

        return True
    except Exception as e:
        logging.error(f"Validation error in macro data: {e} for date {row.get('date')}")
        return False

def clear_existing_data():
    """Delete company, financial and macro data (user accounts are kept)"""
    print("🗑️  Clearing existing data...")
    with app.app_context():
        try:
            # Order matters due to foreign key constraints
            for table in ("financials", "company_news", "stock", "company_audit",
                          "watchlist_companies", "user_alerts", "macro_indicators", "company"):
                db.session.execute(text(f"DELETE FROM {table}"))
            db.session.commit()
            print("✅ Existing data cleared successfully")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing data: {e}")
            logging.error(f"Error clearing data: {e}")
            raise


def table_has_rows(model):
    with app.app_context():
        return db.session.query(model.id).first() is not None


def reset_sequences():
    """CSV rows use explicit ids; move Postgres sequences past them."""
    with app.app_context():
        if db.engine.dialect.name != 'postgresql':
            return
        for table in ("company", "financials", "macro_indicators", "stock"):
            db.session.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
            ))
        db.session.commit()


def load_companies():
    """ Load company data with logging"""
    logging.info("Starting to load company data")
    print("📥 Loading companies...")
    try:
        df = pd.read_csv(data_file("companies.csv"))
        with app.app_context():
            for _, row in df.iterrows():
                try:
                    est_date = datetime.strptime(row["established_date"], "%Y-%m-%d").date() if pd.notna(row.get("established_date")) else None
                    shares_out = int(row["shares_outstanding"]) if pd.notna(row.get("shares_outstanding")) else None # Read shares_outstanding
                    record = Company(
                        id=row["id"],
                        name=row["name"],
                        ticker=row["ticker"],
                        industry=row["industry"],
                        description=row["description"],
                        sector=row.get("sector"),
                        website=row.get("website"),
                        established_date= est_date,
                        shares_outstanding= shares_out, # Assign shares_outstanding
                    )
                    db.session.add(record)
                    logging.info(f"Added company: {row['name']}")
                except KeyError as ke:
                    logging.error(f"Missing column in companies.csv for row {row.get('name')}: {ke}")
                    print(f"❌ Missing column in companies.csv for row {row.get('name')}: {ke}")
                    continue
                except Exception as e:
                    logging.error(f"Error adding company {row.get('name')}: {e}")
                    print(f"❌ Error adding company {row.get('name')}: {e}")
                    continue
            try:
                db.session.commit()
                logging.info("Companies committed successfully")
                print("✅ Companies loaded successfully")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error committing companies: {e}")
                print(f"❌ Error committing companies: {e}")
    except FileNotFoundError:
        logging.error("companies.csv not found")
        print("❌ companies.csv not found")
    except Exception as e:
        logging.error(f"Unexpected error loading companies: {e}")
        print(f"❌ Unexpected error loading companies: {e}")

def load_financials():
    """Load financial data with logging"""
    logging.info("Starting financial data loading")
    print("📥 Loading financials...")
    try:
        df = pd.read_csv(data_file("financials.csv"))
        # Replace NaN with None for SQLAlchemy to handle NULLs
        df = df.where(pd.notna(df), None)

        with app.app_context():
            for _, row_series in df.iterrows():
                row = row_series.to_dict() # Convert Series to dict for easier access and validation
                if validate_financial_data(row):
                    try:
                        db.session.execute(
                            text("""
                                INSERT INTO financials (
                                    id, company_id, year, period,
                                    revenue, cost_of_revenue, gross_profit,
                                    operating_expenses, operating_income, ebitda,
                                    interest_expense, profit_before_tax, net_income,
                                    cash_equivalents, accounts_receivable,
                                    inventory, total_current_assets,
                                    fixed_assets, total_assets,
                                    accounts_payable, short_term_debt,
                                    total_current_liabilities, long_term_debt,
                                    total_liabilities, total_equity,
                                    operating_cash_flow, investing_cash_flow,
                                    financing_cash_flow, net_cash_flow,
                                    current_ratio, debt_to_equity,
                                    return_on_equity, return_on_assets,
                                    profit_margin, created_at, updated_at
                                ) VALUES (
                                    :id, :company_id, :year, :period,
                                    :revenue, :cost_of_revenue, :gross_profit,
                                    :operating_expenses, :operating_income, :ebitda,
                                    :interest_expense, :profit_before_tax, :net_income,
                                    :cash_equivalents, :accounts_receivable,
                                    :inventory, :total_current_assets,
                                    :fixed_assets, :total_assets,
                                    :accounts_payable, :short_term_debt,
                                    :total_current_liabilities, :long_term_debt,
                                    :total_liabilities, :total_equity,
                                    :operating_cash_flow, :investing_cash_flow,
                                    :financing_cash_flow, :net_cash_flow,
                                    :current_ratio, :debt_to_equity,
                                    :return_on_equity, :return_on_assets,
                                    :profit_margin, :created_at, :updated_at
                                )
                            """),
                            {
                                "id": row["id"],
                                "company_id": row["company_id"],
                                "year": row["year"],
                                "period": row["period"],
                                "revenue": row["revenue"],
                                "cost_of_revenue": row["cost_of_revenue"],
                                "gross_profit": row["gross_profit"],
                                "operating_expenses": row["operating_expenses"],
                                "operating_income": row["operating_income"],
                                "ebitda": row["ebitda"], # Corrected placeholder
                                "interest_expense": row["interest_expense"],
                                "profit_before_tax": row["profit_before_tax"],
                                "net_income": row["net_income"],
                                "cash_equivalents": row["cash_equivalents"],
                                "accounts_receivable": row["accounts_receivable"],
                                "inventory": row["inventory"],
                                "total_current_assets": row["total_current_assets"],
                                "fixed_assets": row["fixed_assets"],
                                "total_assets": row["total_assets"],
                                "accounts_payable": row["accounts_payable"],
                                "short_term_debt": row["short_term_debt"],
                                "total_current_liabilities": row["total_current_liabilities"],
                                "long_term_debt": row["long_term_debt"],
                                "total_liabilities": row["total_liabilities"],
                                "total_equity": row["total_equity"],
                                "operating_cash_flow": row["operating_cash_flow"],
                                "investing_cash_flow": row["investing_cash_flow"],
                                "financing_cash_flow": row["financing_cash_flow"],
                                "net_cash_flow": row["net_cash_flow"],
                                "current_ratio": row["current_ratio"],
                                "debt_to_equity": row["debt_to_equity"],
                                "return_on_equity": row["return_on_equity"],
                                "return_on_assets": row["return_on_assets"],
                                "profit_margin": row["profit_margin"],
                                "created_at": datetime.utcnow(), # Add created_at
                                "updated_at": datetime.utcnow(), # Add updated_at
                            }
                        )
                        logging.info(f"Added financial record for company {row['company_id']}, year {row['year']}")
                    except KeyError as ke:
                        logging.error(f"Missing column in financials.csv for company {row.get('company_id')}, year {row.get('year')}: {ke}")
                        print(f"❌ Missing column in financials.csv for company {row.get('company_id')}, year {row.get('year')}: {ke}")
                        continue
                    except Exception as e:
                        logging.error(f"Error inserting financial record for company {row.get('company_id')}, year {row.get('year')}: {e}")
                        print(f"❌ Error inserting financial record for company {row.get('company_id')}, year {row.get('year')}: {e}")
                        continue
            try:
                db.session.commit()
                logging.info("Financial data committed successfully")
                print("✅ Financial data loaded successfully")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error committing financial data: {e}")
                print(f"❌ Error committing financial data: {e}")
    except FileNotFoundError:
        logging.error("financials.csv not found")
        print("❌ financials.csv not found")
    except Exception as e:
        logging.error(f"Unexpected error loading financials: {e}")
        print(f"❌ Unexpected error loading financials: {e}")


def load_macro_indicators():
    """Load monthly macro indicators with comprehensive logging"""
    logging.info("Starting macro indicators data loading")
    print("📥 Loading macro indicators...")
    try:
        df = pd.read_csv(data_file("macro_monthly.csv"))
        # Replace NaN with None for SQLAlchemy to handle NULLs
        df = df.where(pd.notna(df), None)
        logging.info(f"Found {len(df)} macro indicator records to process")

        with app.app_context():
            for _, row_series in df.iterrows():
                row = row_series.to_dict()
                if validate_macro_data(row):
                    try:
                        record = MacroIndicators(
                            date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                            gdp_growth=row["gdp_growth"],
                            inflation_rate=row["inflation_rate"],
                            interest_rate=row["interest_rate"],
                            etb_usd=row["etb_usd"],
                            etb_eur=row["etb_eur"],
                            etb_gbp=row["etb_gbp"],
                            etb_jpy=row["etb_jpy"],
                            etb_cny=row.get("etb_cny"), # Added etb_cny
                            fx_reserves=row.get("fx_reserves"),
                            trade_balance=row.get("trade_balance"),
                            current_account_balance=row.get("current_account_balance"),
                            fdi_inflow=row.get("fdi_inflow"), # Added fdi_inflow
                            remittances=row.get("remittances"), # Added remittances
                            govt_revenue=row.get("govt_revenue"), # Added govt_revenue
                            govt_expenditure=row.get("govt_expenditure"), # Added govt_expenditure
                            budget_deficit=row.get("budget_deficit"), # Added budget_deficit
                            govt_debt=row.get("govt_debt"), # Added govt_debt
                            tax_revenue=row.get("tax_revenue"), # Added tax_revenue
                            total_deposits=row.get("total_deposits"),
                            total_loans=row.get("total_loans"),
                            npl_ratio=row.get("npl_ratio"),
                            loan_to_deposit=row.get("loan_to_deposit"), # Added loan_to_deposit
                            money_supply_m1=row.get("money_supply_m1"), # Added money_supply_m1
                            money_supply_m2=row.get("money_supply_m2"), # Added money_supply_m2
                            private_sector_credit=row.get("private_sector_credit"), # Added private_sector_credit
                            coffee_price=row.get("coffee_price"), # Added coffee_price
                            gold_price=row.get("gold_price"), # Added gold_price
                            oil_price=row.get("oil_price"), # Added oil_price
                            wheat_price=row.get("wheat_price"), # Added wheat_price
                            gdp_per_capita=row.get("gdp_per_capita"), # Added gdp_per_capita
                            food_inflation=row.get("food_inflation"), # Added food_inflation
                            unemployment_rate=row.get("unemployment_rate"), # Added unemployment_rate
                            industrial_production=row.get("industrial_production"), # Added industrial_production
                            agricultural_production=row.get("agricultural_production"), # Added agricultural_production
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        db.session.add(record)
                        logging.info(f"Added macro indicators for date {row['date']}")
                    except KeyError as ke:
                        logging.error(f"Missing column in macro_monthly.csv for date {row.get('date')}: {ke}")
                        print(f"❌ Missing column in macro_monthly.csv for date {row.get('date')}: {ke}")
                        continue
                    except Exception as e:
                        logging.error(f"Error adding macro indicator for date {row.get('date')}: {e}")
                        print(f"❌ Error adding macro indicator for date {row.get('date')}: {e}")
                        continue

            try:
                db.session.commit()
                logging.info("Macro indicators committed successfully")
                print("✅ Macro indicators loaded successfully")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error committing macro indicators: {e}")
                print(f"❌ Error committing macro indicators: {e}")

    except FileNotFoundError:
        logging.error("macro_monthly.csv not found")
        print("❌ macro_monthly.csv not found")
    except Exception as e:
        logging.error(f"Unexpected error loading macro indicators: {e}")
        print(f"❌ Unexpected error loading macro indicators: {e}")

def load_stocks():
    """Load daily stock prices (used by the Market page)"""
    logging.info("Starting stock price loading")
    print("📥 Loading stock prices...")
    try:
        df = pd.read_csv(data_file("stocks.csv"), encoding="utf-8-sig")
        df = df.where(pd.notna(df), None)
        with app.app_context():
            known = {cid for (cid,) in db.session.query(Company.id)}
            skipped = 0
            for row in df.to_dict("records"):
                if int(row["company_id"]) not in known:
                    skipped += 1
                    continue
                db.session.add(Stock(
                    id=int(row["id"]),
                    company_id=int(row["company_id"]),
                    date=datetime.strptime(str(row["date"]), "%Y-%m-%d").date(),
                    open=row["open"], high=row["high"], low=row["low"], close=row["close"],
                    volume=int(row["volume"]) if row["volume"] is not None else None,
                ))
            db.session.commit()
            print(f"✅ Stock prices loaded successfully ({len(df) - skipped} rows"
                  + (f", {skipped} skipped for unknown companies)" if skipped else ")"))
    except Exception as e:
        logging.error(f"Error loading stock prices: {e}")
        print(f"❌ Error loading stock prices: {e}")


def generate_enhanced_report():
    """Print a short data quality report (portable across databases)"""
    print("\n📊 Data Quality Report")
    print("=" * 50)

    def r(value):
        return None if value is None else round(float(value), 2)

    with app.app_context():
        print("\n📊 Sector Distribution:")
        sectors = (db.session.query(Company.sector, func.count(Company.id),
                                    func.count(func.distinct(Company.industry)))
                   .filter(Company.sector.isnot(None))
                   .group_by(Company.sector)
                   .order_by(func.count(Company.id).desc())
                   .all())
        for sector, companies, industries in sectors:
            print(f"{sector}: {companies} companies, {industries} industries")

        print("\n📈 Financial Trends by Year:")
        years = (db.session.query(Financial.year, func.count(Financial.id), func.avg(Financial.revenue),
                                  func.avg(Financial.return_on_equity), func.avg(Financial.profit_margin))
                 .group_by(Financial.year)
                 .order_by(Financial.year.desc())
                 .all())
        for year, records, revenue, roe, margin in years:
            avg_revenue_m = r(revenue / 1_000_000) if revenue is not None else None
            print(f"Year {year}: {records} reports, avg revenue {avg_revenue_m}M ETB, "
                  f"ROE {r(roe)}, profit margin {r(margin)}")

        print("\n🌍 Latest Macro Indicators:")
        for row in MacroIndicators.query.order_by(MacroIndicators.date.desc()).limit(6):
            print(f"{row.date}: GDP growth {row.gdp_growth}%, inflation {row.inflation_rate}%, "
                  f"ETB/USD {row.etb_usd}, NPL {row.npl_ratio}%")

        companies_with_data = db.session.query(func.count(func.distinct(Financial.company_id))).scalar()
        print("\n📋 Data Coverage:")
        print(f"Companies with Financial Data: {companies_with_data} of {Company.query.count()}")
        print(f"Total Financial Records: {Financial.query.count()}")

def main(argv=None):
    """Main function to orchestrate data loading"""
    global app
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true",
                        help="delete existing company, financial and macro data before loading")
    args = parser.parse_args(argv)

    app = create_app()

    print("🚀 Starting data import...")
    with app.app_context():
        db.create_all()

    if args.reset:
        clear_existing_data()

    steps = [(Company, load_companies), (Financial, load_financials),
             (MacroIndicators, load_macro_indicators), (Stock, load_stocks)]
    for model, loader in steps:
        if table_has_rows(model):
            print(f"⏭️  {model.__tablename__} already has data, skipping (use --reset to reload)")
            continue
        loader()

    reset_sequences()
    print("✅ Data loading finished")
    generate_enhanced_report()


if __name__ == "__main__":
    main()
