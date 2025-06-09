from flask import Blueprint, request, jsonify, current_app
from api.models.models import MacroIndicators
from api.models import db
from api.utils.cache import cache
from api.utils.limiter import limiter
from api.utils.errors import APIError
from datetime import datetime, timedelta
from sqlalchemy import desc, asc
import logging

# Configure logger
logger = logging.getLogger(__name__)

macro_api = Blueprint("macro_api", __name__)

def validate_date_range(date_from, date_to):
    """Validate date range parameters"""
    try:
        if date_from:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        if date_to:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            if date_from and date_to < date_from:
                raise ValueError("end_date cannot be earlier than start_date")
        return True
    except ValueError as e:
        raise APIError(str(e), status_code=400)

def serialize_macro(record):
    """Helper function to serialize macro indicators"""
    return {
        "id": record.id,
        "date": record.date.strftime("%Y-%m-%d"),
        # Real Sector
        "gdp_growth": float(record.gdp_growth) if record.gdp_growth else None,
        "gdp_per_capita": float(record.gdp_per_capita) if record.gdp_per_capita else None,
        "inflation_rate": float(record.inflation_rate) if record.inflation_rate else None,
        "interest_rate": float(record.interest_rate) if record.interest_rate else None,
        "unemployment_rate": float(record.unemployment_rate) if record.unemployment_rate else None,
        # Foreign Exchange
        "etb_usd": float(record.etb_usd) if record.etb_usd else None,
        "etb_eur": float(record.etb_eur) if record.etb_eur else None,
        "etb_gbp": float(record.etb_gbp) if record.etb_gbp else None,
        "etb_jpy": float(record.etb_jpy) if record.etb_jpy else None,
        # External Sector
        "fx_reserves": float(record.fx_reserves) if record.fx_reserves else None,
        "trade_balance": float(record.trade_balance) if record.trade_balance else None,
        "current_account_balance": float(record.current_account_balance) if record.current_account_balance else None, # FIXED: Changed from current_account
        # Banking Sector
        "total_deposits": float(record.total_deposits) if record.total_deposits else None,
        "total_loans": float(record.total_loans) if record.total_loans else None,
        "npl_ratio": float(record.npl_ratio) if record.npl_ratio else None
    }

# api/macro_api.py

@macro_api.route("/macro-indicators", methods=["GET"])
@cache.cached(timeout=300)
@limiter.limit("5/minute")
def get_macro_indicators():
    try:
        limit = request.args.get('limit', type=int, default=12)
        date_from = request.args.get('date_from', type=str)
        date_to = request.args.get('date_to', type=str)

        if date_from or date_to:
            validate_date_range(date_from, date_to)

        query = MacroIndicators.query

        if date_from:
            query = query.filter(MacroIndicators.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        if date_to:
            query = query.filter(MacroIndicators.date <= datetime.strptime(date_to, "%Y-%m-%d").date())

        macro_indicators = query.order_by(desc(MacroIndicators.date)).limit(limit).all()

        # ADD THIS DEBUG PRINT STATEMENT
        print(f"DEBUG: In get_macro_indicators - Fetched {len(macro_indicators)} records.")
        if macro_indicators:
            print(f"DEBUG: First record date: {macro_indicators[0].date}")
        # END DEBUG PRINT STATEMENT

        if not macro_indicators:
            raise APIError("No macro indicators found", status_code=404)

        return jsonify({
            "macro_indicators": [serialize_macro(m) for m in macro_indicators]
        }), 200

    except APIError as e:
        logger.warning(f"API Error in get_macro_indicators: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_macro_indicators: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@macro_api.route("/macro/latest")
@cache.cached(timeout=60)
@limiter.limit("60/minute")
def get_latest_indicators():
    """Get latest macro indicators"""
    try:
        latest = MacroIndicators.query.order_by(desc(MacroIndicators.date)).first()
        
        if not latest:
            raise APIError("No macro data found", status_code=404)
        
        response = {
            "latest_indicators": serialize_macro(latest),
            "as_of": latest.date.strftime("%Y-%m-%d")
        }
        
        return jsonify(response), 200
        
    except APIError as e:
        logger.warning(f"API Error in get_latest_indicators: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_indicators: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@macro_api.route("/macro/summary")
@cache.cached(timeout=300)
@limiter.limit("30/minute")
def get_macro_summary():
    """Get macro indicators summary with trends"""
    try:
        # Get latest record
        latest = MacroIndicators.query.order_by(desc(MacroIndicators.date)).first()
        if not latest:
            raise APIError("No macro data found", status_code=404)
            
        # Get record from previous month
        prev_month = latest.date - timedelta(days=30)
        previous = MacroIndicators.query.filter(
            MacroIndicators.date <= prev_month
        ).order_by(desc(MacroIndicators.date)).first()
        
        # Calculate changes
        changes = {}
        if previous:
            changes = {
                "inflation_change": latest.inflation_rate - previous.inflation_rate if all([latest.inflation_rate, previous.inflation_rate]) else None,
                "interest_rate_change": latest.interest_rate - previous.interest_rate if all([latest.interest_rate, previous.interest_rate]) else None,
                "fx_usd_change": ((latest.etb_usd - previous.etb_usd) / previous.etb_usd * 100) if all([latest.etb_usd, previous.etb_usd]) else None,
                "fx_reserves_change": latest.fx_reserves - previous.fx_reserves if all([latest.fx_reserves, previous.fx_reserves]) else None,
                "trade_balance_change": latest.trade_balance - previous.trade_balance if all([latest.trade_balance, previous.trade_balance]) else None,
                "current_account_change": latest.current_account_balance - previous.current_account_balance if all([latest.current_account_balance, previous.current_account_balance]) else None # FIXED: Changed from current_account
            }
        
        response = {
            "current": serialize_macro(latest),
            "monthly_changes": changes,
            "as_of": latest.date.strftime("%Y-%m-%d")
        }
        
        return jsonify(response), 200
        
    except APIError as e:
        logger.warning(f"API Error in get_macro_summary: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_macro_summary: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# --- REMOVED DUMMY MARKET AND NEWS ENDPOINTS FROM HERE ---
# @macro_api.route("/market", methods=["GET"])
# def get_market_summary_dummy():
#     # ... (dummy code)
#     return jsonify(...)

# @macro_api.route("/api/news", methods=["GET"])
# def get_latest_news_dummy():
#     # ... (dummy code)
#     return jsonify(...)