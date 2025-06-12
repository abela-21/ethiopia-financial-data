#!/usr/bin/env python3
"""
Create Excel Templates for Bulk Data Import
Generates professionally formatted Excel templates with data validation
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import ColorScaleRule
import os

def create_companies_excel_template():
    """Create Excel template for companies bulk import"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Companies Import"
    
    # Headers
    headers = [
        "name", "ticker", "industry", "description", "sector", 
        "website", "established_date", "shares_outstanding"
    ]
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="075056", end_color="075056", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header.replace("_", " ").title())
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Add sample data
    sample_data = [
        ["Ethiopian Airlines Group", "ET", "Aviation", "Ethiopia's national airline", "Transportation", 
         "https://www.ethiopianairlines.com", "1945-12-30", 50000000],
        ["Commercial Bank of Ethiopia", "CBE", "Banking", "Ethiopia's largest commercial bank", "Financial Services",
         "https://www.combanketh.et", "1963-01-01", 2000000000]
    ]
    
    for row_num, row_data in enumerate(sample_data, 2):
        for col_num, value in enumerate(row_data, 1):
            ws.cell(row=row_num, column=col_num, value=value)
    
    # Data validation for sectors
    sectors = ["Financial Services", "Technology", "Transportation", "Energy", "Materials", 
               "Healthcare", "Consumer Goods", "Industrials", "Utilities", "Real Estate"]
    sector_validation = DataValidation(type="list", formula1=f'"{",".join(sectors)}"')
    ws.add_data_validation(sector_validation)
    sector_validation.add(f"E2:E1000")
    
    # Adjust column widths
    column_widths = [25, 8, 15, 40, 18, 35, 15, 18]
    for col_num, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = width
    
    # Add instructions sheet
    instructions = wb.create_sheet("Instructions")
    instructions_text = [
        "COMPANIES BULK IMPORT TEMPLATE",
        "",
        "Required Fields:",
        "- name: Company full legal name",
        "- ticker: Stock ticker symbol (unique)",
        "- industry: Primary business industry",
        "",
        "Optional Fields:",
        "- description: Brief company description",
        "- sector: Business sector category",
        "- website: Company website URL",
        "- established_date: Date format YYYY-MM-DD",
        "- shares_outstanding: Number of outstanding shares",
        "",
        "Notes:",
        "- All ticker symbols must be unique",
        "- Date format must be YYYY-MM-DD",
        "- Remove sample data before importing",
        "- Maximum 1000 companies per import"
    ]
    
    for row_num, text in enumerate(instructions_text, 1):
        instructions.cell(row=row_num, column=1, value=text)
    
    return wb

def create_financial_statements_excel_template():
    """Create Excel template for financial statements bulk import"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Financial Statements"
    
    # Headers for financial statements
    headers = [
        "company_ticker", "statement_type", "reporting_period", "fiscal_year",
        "period_start_date", "period_end_date", "filing_date", "revenue",
        "cost_of_goods_sold", "gross_profit", "operating_expenses", "operating_income",
        "interest_expense", "interest_income", "net_income", "earnings_per_share",
        "total_assets", "current_assets", "cash_and_equivalents", "accounts_receivable",
        "inventory", "total_liabilities", "current_liabilities", "long_term_debt",
        "shareholders_equity", "operating_cash_flow", "investing_cash_flow",
        "financing_cash_flow", "free_cash_flow", "currency", "is_audited", "auditor_name"
    ]
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="FF5B04", end_color="FF5B04", fill_type="solid")
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header.replace("_", " ").title())
        cell.font = header_font
        cell.fill = header_fill
    
    # Data validation
    statement_types = ["Income Statement", "Balance Sheet", "Cash Flow", "Banking Metrics", "Financial Metrics"]
    type_validation = DataValidation(type="list", formula1=f'"{",".join(statement_types)}"')
    ws.add_data_validation(type_validation)
    type_validation.add("B2:B1000")
    
    periods = ["Annual", "Quarterly", "Monthly"]
    period_validation = DataValidation(type="list", formula1=f'"{",".join(periods)}"')
    ws.add_data_validation(period_validation)
    period_validation.add("C2:C1000")
    
    # Instructions sheet
    instructions = wb.create_sheet("Instructions")
    instructions_data = [
        "FINANCIAL STATEMENTS BULK IMPORT TEMPLATE",
        "",
        "Required Fields:",
        "- company_ticker: Must match existing company ticker",
        "- statement_type: Income Statement, Balance Sheet, Cash Flow, Banking Metrics, Financial Metrics",
        "- reporting_period: Annual, Quarterly, Monthly",
        "- fiscal_year: 4-digit year (e.g., 2024)",
        "- period_start_date: YYYY-MM-DD format",
        "- period_end_date: YYYY-MM-DD format",
        "",
        "Financial Fields (all optional, in millions ETB):",
        "- Revenue, expenses, assets, liabilities amounts",
        "- Use negative values for expenses and cash outflows",
        "",
        "Banking-specific fields (for banks only):",
        "- deposits, loans_and_advances, loan_loss_provisions",
        "- net_interest_income, non_interest_income",
        "",
        "Notes:",
        "- All monetary values in Ethiopian Birr (ETB)",
        "- Remove sample data before importing",
        "- Ensure company_ticker exists in companies table"
    ]
    
    for row_num, text in enumerate(instructions_data, 1):
        instructions.cell(row=row_num, column=1, value=text)
    
    return wb

def create_macro_indicators_excel_template():
    """Create Excel template for macroeconomic indicators"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Macro Indicators"
    
    # Headers
    headers = [
        "date", "gdp_growth", "gdp_per_capita", "inflation_rate", "food_inflation",
        "interest_rate", "unemployment_rate", "industrial_production", "agricultural_production",
        "exports", "imports", "trade_balance", "current_account_balance", "fdi_inflow",
        "remittances", "fx_reserves", "etb_usd", "etb_eur", "etb_gbp", "etb_jpy",
        "etb_cny", "govt_revenue", "govt_expenditure", "budget_deficit", "govt_debt",
        "tax_revenue", "total_deposits", "total_loans", "npl_ratio", "loan_to_deposit",
        "money_supply_m1", "money_supply_m2", "private_sector_credit", "coffee_price",
        "gold_price", "oil_price", "wheat_price"
    ]
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="233038", end_color="233038", fill_type="solid")
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header.replace("_", " ").title())
        cell.font = header_font
        cell.fill = header_fill
    
    # Sample data
    sample_data = [
        ["2024-01-31", 7.2, 850.5, 28.4, 32.1, 13.5, 19.8, 4.2, 6.8, 3.2, 15.8, -12.6, -4.8, 2.8, 5.9, 3.2, 57.45, 62.38, 72.85, 0.39, 7.94, 485.2, 592.8, -107.6, 1285.4, 398.7, 1245.8, 985.2, 4.8, 79.1, 285.9, 1485.3, 785.4, 5.85, 2058.45, 85.72, 425.38]
    ]
    
    for row_num, row_data in enumerate(sample_data, 2):
        for col_num, value in enumerate(row_data, 1):
            ws.cell(row=row_num, column=col_num, value=value)
    
    # Instructions
    instructions = wb.create_sheet("Instructions")
    instructions_data = [
        "MACROECONOMIC INDICATORS BULK IMPORT TEMPLATE",
        "",
        "Required Field:",
        "- date: YYYY-MM-DD format (monthly data)",
        "",
        "Economic Indicators (all percentages as decimals):",
        "- gdp_growth: GDP growth rate (%)",
        "- inflation_rate: Consumer price inflation (%)",
        "- unemployment_rate: Labor force unemployment (%)",
        "- interest_rate: Central bank policy rate (%)",
        "",
        "Trade & Balance of Payments (billions ETB):",
        "- exports, imports, trade_balance",
        "- current_account_balance, fdi_inflow, remittances",
        "",
        "Exchange Rates:",
        "- etb_usd, etb_eur, etb_gbp, etb_jpy, etb_cny",
        "",
        "Government Finance (billions ETB):",
        "- govt_revenue, govt_expenditure, budget_deficit, govt_debt",
        "",
        "Banking Sector (billions ETB):",
        "- total_deposits, total_loans, money_supply_m1, money_supply_m2",
        "",
        "Commodity Prices (USD per unit):",
        "- coffee_price, gold_price, oil_price, wheat_price"
    ]
    
    for row_num, text in enumerate(instructions_data, 1):
        instructions.cell(row=row_num, column=1, value=text)
    
    return wb

def main():
    """Generate all Excel templates"""
    print("Creating Excel bulk import templates...")
    
    # Create companies template
    companies_wb = create_companies_excel_template()
    companies_wb.save("companies_import_template.xlsx")
    print("✅ Created: companies_import_template.xlsx")
    
    # Create financial statements template
    financial_wb = create_financial_statements_excel_template()
    financial_wb.save("financial_statements_import_template.xlsx")
    print("✅ Created: financial_statements_import_template.xlsx")
    
    # Create macro indicators template
    macro_wb = create_macro_indicators_excel_template()
    macro_wb.save("macro_indicators_import_template.xlsx")
    print("✅ Created: macro_indicators_import_template.xlsx")
    
    print("\nExcel templates created successfully!")
    print("Templates include:")
    print("- Professional formatting with brand colors")
    print("- Data validation for dropdown fields") 
    print("- Sample data and comprehensive instructions")
    print("- Optimized column widths for readability")

if __name__ == "__main__":
    main()