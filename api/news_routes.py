from flask import Blueprint, jsonify, request
from models import CompanyNews, Company, db
from app import cache
from utils.limiter import limiter
from utils.errors import APIError
from sqlalchemy import desc
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

news_api = Blueprint("news_api", __name__)

def serialize_news(news):
    """Helper function to serialize news data"""
    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "source": news.source,
        "published_date": news.published_date.strftime("%Y-%m-%d %H:%M:%S"),
        "category": news.category,
        "url": news.url,
        "company_name": news.company.name if news.company else None,
        "company_ticker": news.company.ticker if news.company else None
    }

@news_api.route("/latest", methods=["GET"])
@limiter.limit("30 per minute")

def get_latest_news():
    """Get latest news articles"""
    try:
        limit = min(int(request.args.get("limit", 6)), 20)
        
        news_items = db.session.query(CompanyNews)\
            .join(Company)\
            .order_by(desc(CompanyNews.published_date))\
            .limit(limit)\
            .all()
        
        return jsonify({
            "success": True,
            "data": [serialize_news(news) for news in news_items],
            "total": len(news_items)
        })
        
    except Exception as e:
        logger.error(f"Error fetching latest news: {e}")
        raise APIError("Failed to fetch latest news", status_code=500)

@news_api.route("/company/<int:company_id>", methods=["GET"])
@limiter.limit("30 per minute")

def get_company_news(company_id):
    """Get news articles for a specific company"""
    try:
        limit = min(int(request.args.get("limit", 10)), 50)
        
        news_items = db.session.query(CompanyNews)\
            .join(Company)\
            .filter(CompanyNews.company_id == company_id)\
            .order_by(desc(CompanyNews.published_date))\
            .limit(limit)\
            .all()
        
        return jsonify({
            "success": True,
            "data": [serialize_news(news) for news in news_items],
            "total": len(news_items)
        })
        
    except Exception as e:
        logger.error(f"Error fetching company news: {e}")
        raise APIError("Failed to fetch company news", status_code=500)