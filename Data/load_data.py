import pandas as pd
from datetime import datetime
import sys
from typing import Dict, Any
import logging
import os
from sqlalchemy.sql import text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/Users/abela/Downloads/Project X/Data/data_loading.log'
)

# Dynamically add your project path so imports work correctly
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
sys.path.append(project_root)

# Now these imports should work
from app import create_app
from api.models.models import db, MacroIndicators, Company, User, Financial # Import Financial model

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
    """Clear all existing data from tables"""
    print("🗑️  Clearing existing data...")
    with app.app_context():
        try:
            # Order matters due to foreign key constraints
            db.session.execute(text("DELETE FROM financials"))
            db.session.execute(text("DELETE FROM company_news"))
            db.session.execute(text("DELETE FROM macro_indicators"))
            db.session.execute(text("DELETE FROM stock")) # Added stock table clear
            db.session.execute(text("DELETE FROM company_audit")) # Added company_audit clear
            db.session.execute(text("DELETE FROM company"))
            db.session.execute(text("DELETE FROM user")) # User should be cleared last if other tables reference it via created_by/updated_by
            db.session.commit()
            print("✅ Existing data cleared successfully")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing data: {e}")
            logging.error(f"Error clearing data: {e}")


def load_companies():
    """ Load company data with logging"""
    logging.info("Starting to load company data")
    print("📥 Loading companies...")
    try:
        df = pd.read_csv("/users/abela/Downloads/Project X/Data/companies.csv")
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
        df = pd.read_csv("/users/abela/Downloads/Project X/Data/financials.csv")
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
        df = pd.read_csv("/users/abela/Downloads/Project X/Data/macro_monthly.csv")
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

def load_users():
    """Load user data with comprehensive logging"""
    logging.info("Starting user data loading")
    print("📥 Loading users...")
    try:
        df = pd.read_csv("/users/abela/Downloads/Project X/Data/users.csv")
        # Replace NaN with None for SQLAlchemy to handle NULLs
        df = df.where(pd.notna(df), None)
        logging.info(f"Found {len(df)} user records to process")

        with app.app_context():
            for _, row_series in df.iterrows():
                row = row_series.to_dict()
                try:
                    record = User(
                        id=row["id"],
                        username=row["username"],
                        password=row["password"],
                        email=row["email"],
                        # Assuming role and is_active are handled by defaults or not in CSV
                        # created_at=datetime.utcnow(), # If not in CSV, add
                        # last_login=None # If not in CSV, add
                    )
                    db.session.add(record)
                    logging.info(f"Added user: {row['username']}")
                except KeyError as ke:
                    logging.error(f"Missing column in users.csv for user {row.get('username')}: {ke}")
                    print(f"❌ Missing column in users.csv for user {row.get('username')}: {ke}")
                    continue
                except Exception as e:
                    logging.error(f"Error adding user {row.get('username')}: {e}")
                    print(f"❌ Error adding user {row.get('username')}: {e}")
                    continue
            try:
                db.session.commit()
                logging.info("Users committed successfully")
                print("✅ Users loaded successfully")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error committing users: {e}")
                print(f"❌ Error committing users: {e}")
    except FileNotFoundError:
        logging.warning("users.csv not found, skipping User data import")
        print("⚠️ users.csv not found, skipping User data import")
    except Exception as e:
        logging.error(f"Unexpected error loading users: {e}")
        print(f"❌ Unexpected error loading users: {e}")

def generate_enhanced_report():
    """Generate comprehensive data quality report with additional metrics"""
    print("\n📊 Enhanced Data Quality Report")
    print("=" * 50)

    with app.app_context():
        # Sector Analysis
        sector_stats = db.session.execute(text("""
            SELECT sector,
                   COUNT(*) as companies,
                   COUNT(DISTINCT industry) as industries,
                   GROUP_CONCAT(name) as company_names
            FROM company
            WHERE sector IS NOT NULL
            GROUP BY sector
            ORDER BY companies DESC
        """)).fetchall()

        print("\n📊 Sector Distribution:")
        for sector in sector_stats:
            print(f"{sector[0]}:")
            print(f"  Companies: {sector[1]}")
            print(f"  Industries: {sector[2]}")

        # Financial Health Metrics
        fin_health = db.session.execute(text("""
            SELECT
                f.year,
                COUNT(*) as records,
                ROUND(AVG(revenue)/1000000, 2) as avg_revenue_m,
                ROUND(AVG(return_on_equity), 2) as avg_roe,
                ROUND(AVG(return_on_assets), 2) as avg_roa,
                ROUND(AVG(current_ratio), 2) as avg_current_ratio,
                ROUND(AVG(debt_to_equity), 2) as avg_debt_to_equity,
                ROUND(AVG(profit_margin), 2) as avg_profit_margin,
                ROUND(AVG(ebitda)/1000000, 2) as avg_ebitda_m -- Added EBITDA to report
            FROM financials f
            GROUP BY year
            ORDER BY year DESC
        """)).fetchall()

        print("\n📈 Financial Trends by Year:")
        for metric in fin_health:
            print(f"\nYear {metric[0]}:")
            print(f"  Number of Reports: {metric[1]}")
            print(f"  Average Revenue: {metric[2]}M ETB")
            print(f"  Return on Equity: {metric[3]}%")
            print(f"  Return on Assets: {metric[4]}%")
            print(f"  Current Ratio: {metric[5]}")
            print(f"  Debt/Equity: {metric[6]}")
            print(f"  Profit Margin: {metric[7]}%")
            print(f"  Average EBITDA: {metric[8]}M ETB") # Display EBITDA

        # Macro Economic Overview
        macro_stats = db.session.execute(text("""
            SELECT
                strftime('%Y-%m', date) as month,
                ROUND(AVG(gdp_growth), 2) as gdp_growth,
                ROUND(AVG(inflation_rate), 2) as inflation,
                ROUND(AVG(etb_usd), 2) as exchange_rate,
                ROUND(AVG(npl_ratio), 2) as npl_ratio
            FROM macro_indicators
            GROUP BY strftime('%Y-%m', date)
            ORDER BY date DESC
            LIMIT 6
        """)).fetchall()

        print("\n🌍 Recent Macro Trends (Last 6 Months):")
        for macro in macro_stats:
            print(f"\n{macro[0]}:")
            print(f"  GDP Growth: {macro[1]}%")
            print(f"  Inflation: {macro[2]}%")
            print(f"  ETB/USD: {macro[3]}")
            print(f"  NPL Ratio: {macro[4]}%")

        # Data Quality Metrics
        quality_stats = db.session.execute(text("""
            SELECT
                COUNT(DISTINCT company_id) as companies_with_data,
                COUNT(DISTINCT year) as years_covered,
                COUNT(*) as total_records
            FROM financials
        """)).fetchone()

        print("\n📋 Data Coverage:")
        print(f"Companies with Financial Data: {quality_stats[0]} of {db.session.query(Company).count()}") # Total companies
        print(f"Years of Historical Data: {quality_stats[1]}")
        print(f"Total Financial Records: {quality_stats[2]}")

def main():
    """Main function to orchestrate data loading"""
    global app
    app = create_app()

    print("🚀 Starting data import...")
    with app.app_context(): # Ensure all operations run within the app context
        try:
            # Create all tables if they don't exist
            db.create_all()
            logging.info("✅ Database tables ensured to exist.")

            clear_existing_data()
            load_companies()
            load_financials()
            load_macro_indicators()
            load_users()
            print("✅ All data loaded successfully")
            generate_enhanced_report()
        except Exception as e:
            logging.error(f"Data import failed: {e}")
            print(f"❌ Data import failed: {e}")

if __name__ == "__main__":
    main()