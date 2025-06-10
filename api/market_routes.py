from flask import Blueprint, jsonify, request
from models import Company, Stock, db
from app import cache
from utils.limiter import limiter
from utils.errors import APIError
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

market_api = Blueprint("market_api", __name__)

def calculate_market_metrics(companies, date=None):
    """Calculate key market metrics"""
    total_market_cap = 0
    active_companies = 0
    total_volume = 0
    gainers = 0
    losers = 0

    for company in companies:
        query = Stock.query.filter_by(company_id=company.id)
        if date:
            query = query.filter(Stock.date <= date)

        latest_stock = query.order_by(desc(Stock.date)).first()
        if latest_stock and company.shares_outstanding:
            market_cap = latest_stock.close * company.shares_outstanding
            total_market_cap += market_cap
            total_volume += latest_stock.volume if latest_stock.volume else 0
            active_companies += 1

            prev_stock = (
                Stock.query.filter_by(company_id=company.id)
                .filter(Stock.date < latest_stock.date)
                .order_by(desc(Stock.date))
                .first()
            )

            if prev_stock:
                if latest_stock.close > prev_stock.close:
                    gainers += 1
                elif latest_stock.close < prev_stock.close:
                    losers += 1

    return {
        "total_market_cap": round(total_market_cap, 2),
        "active_companies": active_companies,
        "total_volume": total_volume,
        "gainers": gainers,
        "losers": losers,
    }

@market_api.route("/market/summary")

@limiter.limit("60/minute")
def get_market_summary():
    """Get market summary with key metrics"""
    try:
        companies = Company.query.all()
        if not companies:
            return jsonify({"message": "No companies found in the market"}), 200

        latest_date = db.session.query(func.max(Stock.date)).scalar()
        if not latest_date:
            return jsonify({"message": "No trading data available"}), 200

        metrics = calculate_market_metrics(companies, latest_date)

        response = {
            "summary": {
                "total_companies": len(companies),
                "active_companies": metrics["active_companies"],
                "market_cap": metrics["total_market_cap"],
                "daily_volume": metrics["total_volume"],
                "gainers": metrics["gainers"],
                "losers": metrics["losers"],
                "unchanged": metrics["active_companies"] - metrics["gainers"] - metrics["losers"],
            },
            "metadata": {
                "last_updated": latest_date.strftime("%Y-%m-%d"),
                "currency": "ETB",
            },
        }

        return jsonify(response), 200

    except APIError as e:
        logger.warning(f"API Error in get_market_summary: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_market_summary: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@market_api.route("/market/trends")

@limiter.limit("30/minute")
def get_market_trends():
    """Get market trends over time"""
    try:
        days = request.args.get("days", default=30, type=int)
        if days <= 0:
            raise APIError("Days parameter must be positive", status_code=400)

        latest_date = db.session.query(func.max(Stock.date)).scalar()
        if not latest_date:
            return jsonify({"message": "No trading data available"}), 200

        start_date = latest_date - timedelta(days=days)
        companies = Company.query.all()

        daily_metrics = []
        # Get data for specific dates with trading activity
        trading_dates = db.session.query(Stock.date.distinct()).filter(
            Stock.date.between(start_date, latest_date)
        ).order_by(Stock.date).all()
        
        for date_tuple in trading_dates:
            current_date = date_tuple[0]
            try:
                metrics = calculate_market_metrics(companies, current_date)
                if metrics["active_companies"] > 0:
                    daily_metrics.append(
                        {
                            "date": current_date.strftime("%Y-%m-%d"),
                            "market_cap": metrics["total_market_cap"],
                            "volume": metrics["total_volume"],
                            "gainers": metrics["gainers"],
                            "losers": metrics["losers"],
                        }
                    )
            except Exception as e:
                logger.warning(f"Error calculating metrics for date {current_date}: {str(e)}")
                continue

        response = {
            "trends": daily_metrics,
            "metadata": {
                "period": f"Last {days} days",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": latest_date.strftime("%Y-%m-%d"),
            },
        }

        return jsonify(response), 200

    except APIError as e:
        logger.warning(f"API Error in get_market_trends: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_market_trends: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@market_api.route("/market/leaders")

@limiter.limit("60/minute")
def get_market_leaders():
    """Get market leaders (top gainers and losers)"""
    try:
        limit = request.args.get("limit", default=10, type=int)
        if limit <= 0 or limit > 50:
            raise APIError("Limit must be between 1 and 50", status_code=400)

        # Get companies with recent stock data
        companies = Company.query.all()
        if not companies:
            return jsonify({"message": "No companies found"}), 200

        leaders_data = []

        for company in companies:
            # Get latest stock price
            latest_stock = (
                Stock.query.filter_by(company_id=company.id)
                .order_by(desc(Stock.date))
                .first()
            )
            
            if not latest_stock:
                continue

            # Get previous stock price for comparison
            prev_stock = (
                Stock.query.filter_by(company_id=company.id)
                .filter(Stock.date < latest_stock.date)
                .order_by(desc(Stock.date))
                .first()
            )

            if prev_stock and prev_stock.close and prev_stock.close > 0:
                price_change = latest_stock.close - prev_stock.close
                percent_change = (price_change / prev_stock.close) * 100

                leaders_data.append({
                    "company_id": company.id,
                    "name": company.name,
                    "ticker": company.ticker,
                    "current_price": latest_stock.close,
                    "previous_price": prev_stock.close,
                    "price_change": round(price_change, 2),
                    "percent_change": round(percent_change, 2),
                    "volume": latest_stock.volume or 0,
                    "date": latest_stock.date.strftime("%Y-%m-%d")
                })

        # Sort by percent change to get gainers and losers
        gainers = sorted(
            [stock for stock in leaders_data if stock["percent_change"] > 0],
            key=lambda x: x["percent_change"],
            reverse=True
        )[:limit]

        losers = sorted(
            [stock for stock in leaders_data if stock["percent_change"] < 0],
            key=lambda x: x["percent_change"]
        )[:limit]

        response = {
            "gainers": gainers,
            "losers": losers,
            "metadata": {
                "total_companies": len(companies),
                "companies_with_data": len(leaders_data),
                "limit": limit
            }
        }

        return jsonify(response), 200

    except APIError as e:
        logger.warning(f"API Error in get_market_leaders: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in get_market_leaders: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
