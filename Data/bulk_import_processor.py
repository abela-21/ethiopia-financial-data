#!/usr/bin/env python3
"""
Bulk Import Processing System
Handles CSV/Excel file uploads and batch data processing for Ethiopian Economic Data Platform
"""

import pandas as pd
import openpyxl
from sqlalchemy import create_engine, text
import os
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulkImportProcessor:
    """Handles bulk data import from CSV/Excel files"""
    
    def __init__(self, database_url=None):
        """Initialize with database connection"""
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url)
        
    def validate_companies_data(self, df):
        """Validate companies data before import"""
        errors = []
        
        # Check required fields
        required_fields = ['name', 'ticker', 'industry']
        for field in required_fields:
            if field not in df.columns:
                errors.append(f"Missing required field: {field}")
            elif df[field].isnull().any():
                errors.append(f"Empty values found in required field: {field}")
        
        # Check ticker uniqueness
        if 'ticker' in df.columns:
            if df['ticker'].duplicated().any():
                errors.append("Duplicate ticker symbols found in import data")
        
        # Validate date format
        if 'established_date' in df.columns:
            try:
                pd.to_datetime(df['established_date'], format='%Y-%m-%d', errors='coerce')
            except:
                errors.append("Invalid date format in established_date (use YYYY-MM-DD)")
        
        return errors
    
    def import_companies_data(self, file_path):
        """Import companies data from CSV/Excel file"""
        try:
            # Read file based on extension
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name='Companies Import')
            else:
                df = pd.read_csv(file_path)
            
            # Validate data
            errors = self.validate_companies_data(df)
            if errors:
                return {'success': False, 'errors': errors}
            
            # Process each row
            success_count = 0
            error_count = 0
            import_errors = []
            
            with self.engine.connect() as conn:
                for index, row in df.iterrows():
                    try:
                        # Check if ticker already exists
                        existing = conn.execute(
                            text("SELECT id FROM company WHERE ticker = :ticker"),
                            {'ticker': row['ticker']}
                        ).fetchone()
                        
                        if existing:
                            import_errors.append(f"Row {index + 2}: Ticker {row['ticker']} already exists")
                            error_count += 1
                            continue
                        
                        # Insert company
                        conn.execute(
                            text("""
                                INSERT INTO company (name, ticker, industry, description, sector, 
                                                   website, established_date, shares_outstanding, 
                                                   created_at, updated_at)
                                VALUES (:name, :ticker, :industry, :description, :sector, 
                                       :website, :established_date, :shares_outstanding, 
                                       NOW(), NOW())
                            """),
                            {
                                'name': row['name'],
                                'ticker': row['ticker'], 
                                'industry': row['industry'],
                                'description': row.get('description'),
                                'sector': row.get('sector'),
                                'website': row.get('website'),
                                'established_date': row.get('established_date'),
                                'shares_outstanding': row.get('shares_outstanding')
                            }
                        )
                        success_count += 1
                        
                    except Exception as e:
                        import_errors.append(f"Row {index + 2}: {str(e)}")
                        error_count += 1
                
                conn.commit()
            
            return {
                'success': True,
                'imported': success_count,
                'errors': error_count,
                'error_details': import_errors
            }
            
        except Exception as e:
            logger.error(f"Error importing companies data: {str(e)}")
            return {'success': False, 'errors': [str(e)]}
    
    def validate_financial_statements_data(self, df):
        """Validate financial statements data"""
        errors = []
        
        # Check required fields
        required_fields = ['company_ticker', 'statement_type', 'reporting_period', 
                          'fiscal_year', 'period_start_date', 'period_end_date']
        for field in required_fields:
            if field not in df.columns:
                errors.append(f"Missing required field: {field}")
        
        # Validate statement types
        valid_types = ['Income Statement', 'Balance Sheet', 'Cash Flow', 'Banking Metrics', 'Financial Metrics']
        if 'statement_type' in df.columns:
            invalid_types = df[~df['statement_type'].isin(valid_types)]['statement_type'].unique()
            if len(invalid_types) > 0:
                errors.append(f"Invalid statement types: {list(invalid_types)}")
        
        # Validate reporting periods
        valid_periods = ['Annual', 'Quarterly', 'Monthly']
        if 'reporting_period' in df.columns:
            invalid_periods = df[~df['reporting_period'].isin(valid_periods)]['reporting_period'].unique()
            if len(invalid_periods) > 0:
                errors.append(f"Invalid reporting periods: {list(invalid_periods)}")
        
        return errors
    
    def import_financial_statements_data(self, file_path):
        """Import financial statements data from CSV/Excel file"""
        try:
            # Read file
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name='Financial Statements')
            else:
                df = pd.read_csv(file_path)
            
            # Validate data
            errors = self.validate_financial_statements_data(df)
            if errors:
                return {'success': False, 'errors': errors}
            
            success_count = 0
            error_count = 0
            import_errors = []
            
            with self.engine.connect() as conn:
                for index, row in df.iterrows():
                    try:
                        # Get company ID from ticker
                        company = conn.execute(
                            text("SELECT id FROM company WHERE ticker = :ticker"),
                            {'ticker': row['company_ticker']}
                        ).fetchone()
                        
                        if not company:
                            import_errors.append(f"Row {index + 2}: Company ticker {row['company_ticker']} not found")
                            error_count += 1
                            continue
                        
                        # Insert financial statement
                        conn.execute(
                            text("""
                                INSERT INTO financial_statement (
                                    company_id, statement_type, reporting_period, fiscal_year,
                                    period_start_date, period_end_date, filing_date, revenue,
                                    cost_of_goods_sold, gross_profit, operating_expenses, operating_income,
                                    interest_expense, interest_income, net_income, earnings_per_share,
                                    total_assets, current_assets, cash_and_equivalents, accounts_receivable,
                                    inventory, total_liabilities, current_liabilities, long_term_debt,
                                    shareholders_equity, operating_cash_flow, investing_cash_flow,
                                    financing_cash_flow, free_cash_flow, deposits, loans_and_advances,
                                    loan_loss_provisions, net_interest_income, non_interest_income,
                                    currency, is_audited, auditor_name, data_source, created_at
                                )
                                VALUES (
                                    :company_id, :statement_type, :reporting_period, :fiscal_year,
                                    :period_start_date, :period_end_date, :filing_date, :revenue,
                                    :cost_of_goods_sold, :gross_profit, :operating_expenses, :operating_income,
                                    :interest_expense, :interest_income, :net_income, :earnings_per_share,
                                    :total_assets, :current_assets, :cash_and_equivalents, :accounts_receivable,
                                    :inventory, :total_liabilities, :current_liabilities, :long_term_debt,
                                    :shareholders_equity, :operating_cash_flow, :investing_cash_flow,
                                    :financing_cash_flow, :free_cash_flow, :deposits, :loans_and_advances,
                                    :loan_loss_provisions, :net_interest_income, :non_interest_income,
                                    :currency, :is_audited, :auditor_name, :data_source, NOW()
                                )
                            """),
                            {
                                'company_id': company.id,
                                'statement_type': row['statement_type'],
                                'reporting_period': row['reporting_period'],
                                'fiscal_year': row['fiscal_year'],
                                'period_start_date': row['period_start_date'],
                                'period_end_date': row['period_end_date'],
                                'filing_date': row.get('filing_date'),
                                'revenue': row.get('revenue'),
                                'cost_of_goods_sold': row.get('cost_of_goods_sold'),
                                'gross_profit': row.get('gross_profit'),
                                'operating_expenses': row.get('operating_expenses'),
                                'operating_income': row.get('operating_income'),
                                'interest_expense': row.get('interest_expense'),
                                'interest_income': row.get('interest_income'),
                                'net_income': row.get('net_income'),
                                'earnings_per_share': row.get('earnings_per_share'),
                                'total_assets': row.get('total_assets'),
                                'current_assets': row.get('current_assets'),
                                'cash_and_equivalents': row.get('cash_and_equivalents'),
                                'accounts_receivable': row.get('accounts_receivable'),
                                'inventory': row.get('inventory'),
                                'total_liabilities': row.get('total_liabilities'),
                                'current_liabilities': row.get('current_liabilities'),
                                'long_term_debt': row.get('long_term_debt'),
                                'shareholders_equity': row.get('shareholders_equity'),
                                'operating_cash_flow': row.get('operating_cash_flow'),
                                'investing_cash_flow': row.get('investing_cash_flow'),
                                'financing_cash_flow': row.get('financing_cash_flow'),
                                'free_cash_flow': row.get('free_cash_flow'),
                                'deposits': row.get('deposits'),
                                'loans_and_advances': row.get('loans_and_advances'),
                                'loan_loss_provisions': row.get('loan_loss_provisions'),
                                'net_interest_income': row.get('net_interest_income'),
                                'non_interest_income': row.get('non_interest_income'),
                                'currency': row.get('currency', 'ETB'),
                                'is_audited': row.get('is_audited'),
                                'auditor_name': row.get('auditor_name'),
                                'data_source': row.get('data_source', 'Bulk Import')
                            }
                        )
                        success_count += 1
                        
                    except Exception as e:
                        import_errors.append(f"Row {index + 2}: {str(e)}")
                        error_count += 1
                
                conn.commit()
            
            return {
                'success': True,
                'imported': success_count,
                'errors': error_count,
                'error_details': import_errors
            }
            
        except Exception as e:
            logger.error(f"Error importing financial statements: {str(e)}")
            return {'success': False, 'errors': [str(e)]}
    
    def import_macro_indicators_data(self, file_path):
        """Import macroeconomic indicators data from CSV/Excel file"""
        try:
            # Read file
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name='Macro Indicators')
            else:
                df = pd.read_csv(file_path)
            
            # Validate required date field
            if 'date' not in df.columns:
                return {'success': False, 'errors': ['Missing required field: date']}
            
            success_count = 0
            error_count = 0
            import_errors = []
            
            with self.engine.connect() as conn:
                for index, row in df.iterrows():
                    try:
                        # Check if date already exists
                        existing = conn.execute(
                            text("SELECT id FROM macro_indicators WHERE date = :date"),
                            {'date': row['date']}
                        ).fetchone()
                        
                        if existing:
                            # Update existing record
                            conn.execute(
                                text("""
                                    UPDATE macro_indicators SET
                                        gdp_growth = :gdp_growth, gdp_per_capita = :gdp_per_capita,
                                        inflation_rate = :inflation_rate, food_inflation = :food_inflation,
                                        interest_rate = :interest_rate, unemployment_rate = :unemployment_rate,
                                        industrial_production = :industrial_production, agricultural_production = :agricultural_production,
                                        exports = :exports, imports = :imports, trade_balance = :trade_balance,
                                        current_account_balance = :current_account_balance, fdi_inflow = :fdi_inflow,
                                        remittances = :remittances, fx_reserves = :fx_reserves,
                                        etb_usd = :etb_usd, etb_eur = :etb_eur, etb_gbp = :etb_gbp,
                                        etb_jpy = :etb_jpy, etb_cny = :etb_cny,
                                        govt_revenue = :govt_revenue, govt_expenditure = :govt_expenditure,
                                        budget_deficit = :budget_deficit, govt_debt = :govt_debt,
                                        tax_revenue = :tax_revenue, total_deposits = :total_deposits,
                                        total_loans = :total_loans, npl_ratio = :npl_ratio,
                                        loan_to_deposit = :loan_to_deposit, money_supply_m1 = :money_supply_m1,
                                        money_supply_m2 = :money_supply_m2, private_sector_credit = :private_sector_credit,
                                        coffee_price = :coffee_price, gold_price = :gold_price,
                                        oil_price = :oil_price, wheat_price = :wheat_price,
                                        updated_at = NOW()
                                    WHERE date = :date
                                """),
                                dict(row)
                            )
                        else:
                            # Insert new record
                            conn.execute(
                                text("""
                                    INSERT INTO macro_indicators (
                                        date, gdp_growth, gdp_per_capita, inflation_rate, food_inflation,
                                        interest_rate, unemployment_rate, industrial_production, agricultural_production,
                                        exports, imports, trade_balance, current_account_balance, fdi_inflow,
                                        remittances, fx_reserves, etb_usd, etb_eur, etb_gbp, etb_jpy, etb_cny,
                                        govt_revenue, govt_expenditure, budget_deficit, govt_debt, tax_revenue,
                                        total_deposits, total_loans, npl_ratio, loan_to_deposit,
                                        money_supply_m1, money_supply_m2, private_sector_credit,
                                        coffee_price, gold_price, oil_price, wheat_price,
                                        created_at, updated_at
                                    )
                                    VALUES (
                                        :date, :gdp_growth, :gdp_per_capita, :inflation_rate, :food_inflation,
                                        :interest_rate, :unemployment_rate, :industrial_production, :agricultural_production,
                                        :exports, :imports, :trade_balance, :current_account_balance, :fdi_inflow,
                                        :remittances, :fx_reserves, :etb_usd, :etb_eur, :etb_gbp, :etb_jpy, :etb_cny,
                                        :govt_revenue, :govt_expenditure, :budget_deficit, :govt_debt, :tax_revenue,
                                        :total_deposits, :total_loans, :npl_ratio, :loan_to_deposit,
                                        :money_supply_m1, :money_supply_m2, :private_sector_credit,
                                        :coffee_price, :gold_price, :oil_price, :wheat_price,
                                        NOW(), NOW()
                                    )
                                """),
                                dict(row)
                            )
                        
                        success_count += 1
                        
                    except Exception as e:
                        import_errors.append(f"Row {index + 2}: {str(e)}")
                        error_count += 1
                
                conn.commit()
            
            return {
                'success': True,
                'imported': success_count,
                'errors': error_count,
                'error_details': import_errors
            }
            
        except Exception as e:
            logger.error(f"Error importing macro indicators: {str(e)}")
            return {'success': False, 'errors': [str(e)]}
    
    def generate_import_report(self, results, data_type):
        """Generate detailed import report"""
        report = {
            'data_type': data_type,
            'timestamp': datetime.now().isoformat(),
            'success': results['success'],
            'summary': {
                'total_processed': results.get('imported', 0) + results.get('errors', 0),
                'successful_imports': results.get('imported', 0),
                'failed_imports': results.get('errors', 0),
                'success_rate': round((results.get('imported', 0) / max(1, results.get('imported', 0) + results.get('errors', 0))) * 100, 2)
            }
        }
        
        if 'error_details' in results:
            report['error_details'] = results['error_details']
        
        return report

def main():
    """Test bulk import functionality"""
    processor = BulkImportProcessor()
    
    # Test companies import
    print("Testing bulk import functionality...")
    
    companies_result = processor.import_companies_data('companies_import_template.csv')
    print("\nCompanies Import Result:")
    print(json.dumps(companies_result, indent=2))
    
    financial_result = processor.import_financial_statements_data('financial_statements_import_template.csv')
    print("\nFinancial Statements Import Result:")
    print(json.dumps(financial_result, indent=2))
    
    macro_result = processor.import_macro_indicators_data('macro_indicators_import_template.csv')
    print("\nMacro Indicators Import Result:")
    print(json.dumps(macro_result, indent=2))

if __name__ == "__main__":
    main()