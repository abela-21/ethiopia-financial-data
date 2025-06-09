from flask import Blueprint, jsonify, request
from models import Stock, Company
from utils.cache import cache
from utils.limiter import limiter
from utils.errors import APIError
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import desc, asc
import logging

logger = logging.getLogger(__name__)

stock_api = Blueprint("stock_api", __name__)

def validate_date_params(start_date, end_date):
    """Validate date parameters"""
    try:
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            if start_date and end < start:
                raise ValueError("end_date cannot be earlier than start_date")
        return True
    except ValueError as e:
        raise APIError(str(e), status_code=400)

def serialize_stock(stock):
    """Serialize stock data"""
    return {
        "date": stock.date.strftime("%Y-%m-%d"),
        "open": float(stock.open) if stock.open else None,
        "close": float(stock.close) if stock.close else None,
        "high": float(stock.high) if stock.high else None,
        "low": float(stock.low) if stock.low else None,
        "volume": stock.volume,
        "change": round(((stock.close - stock.open) / stock.open) * 100, 2) if stock.open and stock.close else None
    }

@stock_api.route("/stocks/<int:company_id>", methods=["GET"])
@cache.cached(timeout=300, query_string=True)
@limiter.limit("30/minute")
def get_stocks(company_id):
    """Get stock prices for a company with optional date filters"""
    try:
        company = Company.query.get_or_404(company_id)

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = request.args.get("limit", type=int)
        sort = request.args.get("sort", "asc")

        validate_date_params(start_date, end_date)

        query = Stock.query.filter_by(company_id=company_id)

        if start_date:
            query = query.filter(Stock.date >= datetime.strptime(start_date, "%Y-%m-%d"))
        if end_date:
            query = query.filter(Stock.date <= datetime.strptime(end_date, "%Y-%m-%d"))

        sort_func = asc if sort == "asc" else desc
        query = query.order_by(sort_func(Stock.date))

        if limit:
            query = query.limit(limit)

        stocks = query.all()

        response = {
            "company": {
                "id": company.id,
                "name": company.name,
                "ticker": company.ticker
            },
            "data": [serialize_stock(stock) for stock in stocks],
            "metadata": {
                "count": len(stocks),
                "start_date": start_date,
                "end_date": end_date,
                "sort": sort
            }
        }

        return jsonify(response), 200

    except APIError as e:
        logger.warning(f"API Error in get_stocks: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_stocks: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@stock_api.route("/stocks/<int:company_id>/latest", methods=["GET"])
@cache.cached(timeout=60)
@limiter.limit("60/minute")
def get_latest_stock(company_id):
    """Get latest stock price for a company"""
    try:
        company = Company.query.get_or_404(company_id)
        
        latest_stock = Stock.query.filter_by(company_id=company_id)\
            .order_by(Stock.date.desc())\
            .first()

        if not latest_stock:
            raise APIError("No stock data available", status_code=404)

        response = {
            "company": {
                "id": company.id,
                "name": company.name,
                "ticker": company.ticker
            },
            "latest_stock": serialize_stock(latest_stock)
        }

        return jsonify(response), 200

    except APIError as e:
        logger.warning(f"API Error in get_latest_stock: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_stock: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
