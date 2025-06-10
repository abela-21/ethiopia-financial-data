from flask import Blueprint, send_file, request, jsonify
from models import Company, Financial, Stock, MacroIndicators
from utils.errors import APIError
from app import cache
from utils.limiter import limiter
from datetime import datetime
import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

download_api = Blueprint("download_api", __name__)

def validate_date_range(date_from, date_to):
    """Validate date range parameters"""
    try:
        if date_from:
            date_from = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to = datetime.strptime(date_to, "%Y-%m-%d")
            if date_from and date_to < date_from:
                raise ValueError("end_date cannot be earlier than start_date")
        return True
    except ValueError as e:
        raise APIError(str(e), status_code=400)

def create_excel_response(df, filename):
    """Create Excel file response"""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
        worksheet = writer.sheets['Data']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(idx, idx, max_length)
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@download_api.route("/download/companies")
@limiter.limit("30/minute")
@cache.cached(timeout=300, query_string=True)
def download_companies():
    """Download companies data in CSV or Excel format"""
    try:
        file_format = request.args.get("format", "csv")
        industry = request.args.get("industry")
        sector = request.args.get("sector")

        query = Company.query
        if industry:
            query = query.filter(Company.industry == industry)
        if sector:
            query = query.filter(Company.sector == sector)

        companies = query.all()
        if not companies:
            return jsonify({"message": "No companies found"}), 200

        data = [{
            "ID": c.id,
            "Name": c.name,
            "Ticker": c.ticker,
            "Industry": c.industry,
            "Sector": c.sector,
            "Description": c.description,
            "Website": c.website,
            "Established Date": c.established_date.strftime("%Y-%m-%d") if c.established_date else None,
            "Shares Outstanding": c.shares_outstanding
        } for c in companies]

        df = pd.DataFrame(data)
        
        if file_format.lower() == "excel":
            return create_excel_response(df, "companies.xlsx")
        else:
            buffer = BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name="companies.csv",
                mimetype="text/csv"
            )

    except APIError as e:
        logger.warning(f"API Error in download_companies: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in download_companies: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@download_api.route("/download/macro_indicators")
@limiter.limit("30/minute")
@cache.cached(timeout=300, query_string=True)
def download_macro():
    """Download macroeconomic indicators with filtering options"""
    try:
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        variables = request.args.get("variables")
        file_format = request.args.get("format", "csv")

        validate_date_range(date_from, date_to)

        query = MacroIndicators.query
        if date_from:
            query = query.filter(MacroIndicators.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        if date_to:
            query = query.filter(MacroIndicators.date <= datetime.strptime(date_to, "%Y-%m-%d").date())

        records = query.all()
        if not records:
            return jsonify({"message": "No data found for the specified criteria"}), 200

        data = [r.__dict__ for r in records]
        df = pd.DataFrame(data)
        
        if '_sa_instance_state' in df.columns:
            df.drop(columns=["_sa_instance_state"], inplace=True)

        if variables:
            selected_columns = ["date"] + variables.split(",")
            invalid_cols = [col for col in selected_columns if col not in df.columns]
            if invalid_cols:
                raise APIError(f"Invalid column(s) requested: {', '.join(invalid_cols)}", status_code=400)
            df = df[selected_columns]
            
        if 'date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        filename = f"macro_indicators_{date_from or 'start'}_to_{date_to or 'present'}"

        if file_format.lower() == "excel":
            return create_excel_response(df, f"{filename}.xlsx")
        else:
            buffer = BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{filename}.csv",
                mimetype="text/csv"
            )

    except APIError as e:
        logger.warning(f"API Error in download_macro: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in download_macro: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@download_api.route("/download/financials")
@limiter.limit("30/minute")
@cache.cached(timeout=300, query_string=True)
def download_financials():
    """Download financial data with company and variable filtering"""
    try:
        company_id = request.args.get("company_id")
        year_from = request.args.get("year_from")
        year_to = request.args.get("year_to")
        variables = request.args.get("variables")
        file_format = request.args.get("format", "csv")

        query = Financial.query.join(Company)
        
        if company_id:
            query = query.filter(Financial.company_id == company_id)
        if year_from:
            query = query.filter(Financial.year >= int(year_from))
        if year_to:
            query = query.filter(Financial.year <= int(year_to))

        records = query.all()
        if not records:
            return jsonify({"message": "No financial data found for the specified criteria"}), 200

        data = []
        for record in records:
            row = {
                "Company_ID": record.company_id,
                "Company_Name": record.company.name,
                "Company_Ticker": record.company.ticker,
                "Year": record.year,
                "Period": record.period,
                "Revenue": record.revenue,
                "Cost_of_Revenue": record.cost_of_revenue,
                "Gross_Profit": record.gross_profit,
                "Operating_Expenses": record.operating_expenses,
                "Operating_Income": record.operating_income,
                "EBITDA": record.ebitda,
                "Interest_Expense": record.interest_expense,
                "Profit_Before_Tax": record.profit_before_tax,
                "Net_Income": record.net_income,
                "Cash_Equivalents": record.cash_equivalents,
                "Accounts_Receivable": record.accounts_receivable,
                "Inventory": record.inventory,
                "Total_Current_Assets": record.total_current_assets,
                "Fixed_Assets": record.fixed_assets,
                "Total_Assets": record.total_assets,
                "Accounts_Payable": record.accounts_payable,
                "Short_Term_Debt": record.short_term_debt,
                "Total_Current_Liabilities": record.total_current_liabilities,
                "Long_Term_Debt": record.long_term_debt,
                "Total_Liabilities": record.total_liabilities,
                "Total_Equity": record.total_equity,
                "Operating_Cash_Flow": record.operating_cash_flow,
                "Investing_Cash_Flow": record.investing_cash_flow,
                "Financing_Cash_Flow": record.financing_cash_flow,
                "Net_Cash_Flow": record.net_cash_flow,
                "Current_Ratio": record.current_ratio,
                "Debt_to_Equity": record.debt_to_equity,
                "Return_on_Equity": record.return_on_equity,
                "Return_on_Assets": record.return_on_assets,
                "Profit_Margin": record.profit_margin
            }
            data.append(row)

        df = pd.DataFrame(data)
        
        if variables:
            base_columns = ["Company_ID", "Company_Name", "Company_Ticker", "Year", "Period"]
            selected_variables = variables.split(",")
            
            # Map frontend variable names to DataFrame column names
            variable_mapping = {
                "Revenue": "Revenue",
                "Net_Income": "Net_Income", 
                "Total_Assets": "Total_Assets",
                "Total_Liabilities": "Total_Liabilities",
                "Total_Equity": "Total_Equity",
                "Operating_Cash_Flow": "Operating_Cash_Flow",
                "Current_Ratio": "Current_Ratio",
                "Debt_to_Equity": "Debt_to_Equity",
                "Return_on_Equity": "Return_on_Equity",
                "Return_on_Assets": "Return_on_Assets",
                "Profit_Margin": "Profit_Margin"
            }
            
            mapped_variables = []
            for var in selected_variables:
                if var in variable_mapping:
                    mapped_variables.append(variable_mapping[var])
                elif var in df.columns:
                    mapped_variables.append(var)
                else:
                    raise APIError(f"Invalid variable requested: {var}", status_code=400)
            
            selected_columns = base_columns + mapped_variables
            df = df[selected_columns]

        filename = f"financial_data_{year_from or 'all'}_to_{year_to or 'latest'}"
        
        if file_format.lower() == "excel":
            return create_excel_response(df, f"{filename}.xlsx")
        else:
            buffer = BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{filename}.csv",
                mimetype="text/csv"
            )

    except APIError as e:
        logger.warning(f"API Error in download_financials: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in download_financials: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@download_api.route("/download/stocks")
@limiter.limit("30/minute")
@cache.cached(timeout=300, query_string=True)
def download_stocks():
    """Download stock price data with company and date filtering"""
    try:
        company_id = request.args.get("company_id")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        variables = request.args.get("variables")
        file_format = request.args.get("format", "csv")

        if date_from or date_to:
            validate_date_range(date_from, date_to)

        query = Stock.query.join(Company)
        
        if company_id:
            query = query.filter(Stock.company_id == company_id)
        if date_from:
            query = query.filter(Stock.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        if date_to:
            query = query.filter(Stock.date <= datetime.strptime(date_to, "%Y-%m-%d").date())

        records = query.all()
        if not records:
            return jsonify({"message": "No stock data found for the specified criteria"}), 200

        data = []
        for record in records:
            row = {
                "Company_ID": record.company_id,
                "Company_Name": record.company.name,
                "Company_Ticker": record.company.ticker,
                "Date": record.date.strftime("%Y-%m-%d"),
                "Open": record.open,
                "High": record.high,
                "Low": record.low,
                "Close": record.close,
                "Volume": record.volume
            }
            data.append(row)

        df = pd.DataFrame(data)
        
        if variables:
            base_columns = ["Company_ID", "Company_Name", "Company_Ticker", "Date"]
            selected_variables = variables.split(",")
            selected_columns = base_columns + selected_variables
            invalid_cols = [col for col in selected_columns if col not in df.columns]
            if invalid_cols:
                raise APIError(f"Invalid variable(s) requested: {', '.join(invalid_cols)}", status_code=400)
            df = df[selected_columns]

        filename = f"stock_data_{date_from or 'start'}_to_{date_to or 'present'}"
        
        if file_format.lower() == "excel":
            return create_excel_response(df, f"{filename}.xlsx")
        else:
            buffer = BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{filename}.csv",
                mimetype="text/csv"
            )

    except APIError as e:
        logger.warning(f"API Error in download_stocks: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in download_stocks: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
