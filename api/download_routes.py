from flask import Blueprint, send_file, request, jsonify
from models import Company, Financial, Stock, MacroIndicators
from utils.errors import APIError
from utils.cache import cache
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
