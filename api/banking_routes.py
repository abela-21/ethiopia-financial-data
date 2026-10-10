from flask import Blueprint, jsonify, request
from werkzeug.exceptions import HTTPException
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import Bank, BankFinancialMetric, ResearchDocument, db
from utils.cache import cache
from utils.limiter import limiter
from utils.errors import APIError
import logging

logger = logging.getLogger(__name__)

banking_api = Blueprint('banking_api', __name__)

@banking_api.before_request
def before_request():
    """Enhanced request logging for banking API"""
    logger.info({
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'params': dict(request.args),
        'banking_endpoint': True
    })

def serialize_bank(bank):
    """Serialize bank data with comprehensive metrics"""
    return {
        "id": bank.id,
        "name": bank.name,
        "license_number": bank.license_number,
        "establishment_date": bank.establishment_date.strftime('%Y-%m-%d') if bank.establishment_date else None,
        "headquarters_location": bank.headquarters_location,
        "branch_count": bank.branch_count,
        "atm_count": bank.atm_count,
        "digital_banking_users": bank.digital_banking_users,
        "nbe_rating": bank.nbe_rating,
        "website_url": bank.website_url,
        "swift_code": bank.swift_code,
        "bank_type": bank.bank_type,
        "ownership_type": bank.ownership_type,
        "created_at": bank.created_at.strftime('%Y-%m-%d %H:%M:%S') if bank.created_at else None,
        "updated_at": bank.updated_at.strftime('%Y-%m-%d %H:%M:%S') if bank.updated_at else None
    }

def serialize_bank_metrics(metric):
    """Serialize banking financial metrics"""
    return {
        "id": metric.id,
        "bank_id": metric.bank_id,
        "bank_name": metric.bank.name if metric.bank else None,
        "reporting_date": metric.reporting_date.strftime('%Y-%m-%d') if metric.reporting_date else None,
        "total_assets": metric.total_assets,
        "total_deposits": metric.total_deposits,
        "total_loans": metric.total_loans,
        "shareholders_equity": metric.shareholders_equity,
        "cash_and_bank_balances": metric.cash_and_bank_balances,
        "net_interest_income": metric.net_interest_income,
        "non_interest_income": metric.non_interest_income,
        "operating_expenses": metric.operating_expenses,
        "net_profit": metric.net_profit,
        "loan_loss_provisions": metric.loan_loss_provisions,
        "npl_ratio": metric.npl_ratio,
        "capital_adequacy_ratio": metric.capital_adequacy_ratio,
        "return_on_assets": metric.return_on_assets,
        "return_on_equity": metric.return_on_equity,
        "loan_to_deposit_ratio": metric.loan_to_deposit_ratio,
        "cost_to_income_ratio": metric.cost_to_income_ratio,
        "net_interest_margin": metric.net_interest_margin,
        "mobile_banking_users": metric.mobile_banking_users,
        "internet_banking_users": metric.internet_banking_users,
        "digital_transaction_volume": metric.digital_transaction_volume
    }

@banking_api.route('/banks')
@limiter.limit("50/minute")
def get_banks():
    """Get all Ethiopian banks with filtering and sorting"""
    try:
        # Query parameters
        bank_type = request.args.get('bank_type')
        ownership_type = request.args.get('ownership_type')
        nbe_rating = request.args.get('nbe_rating')
        min_branches = request.args.get('min_branches', type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        # Build query
        query = Bank.query
        
        if bank_type:
            query = query.filter(Bank.bank_type == bank_type)
        if ownership_type:
            query = query.filter(Bank.ownership_type == ownership_type)
        if nbe_rating:
            query = query.filter(Bank.nbe_rating == nbe_rating)
        if min_branches:
            query = query.filter(Bank.branch_count >= min_branches)

        # Sorting
        if hasattr(Bank, sort_by):
            sort_column = getattr(Bank, sort_by)
            if order.lower() == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Pagination
        banks = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            "data": [serialize_bank(bank) for bank in banks.items],
            "pagination": {
                "page": banks.page,
                "pages": banks.pages,
                "per_page": banks.per_page,
                "total": banks.total
            },
            "filters_applied": {
                "bank_type": bank_type,
                "ownership_type": ownership_type,
                "nbe_rating": nbe_rating,
                "min_branches": min_branches
            }
        })

    except Exception as e:
        logger.error(f"Error in get_banks: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@banking_api.route('/banks/<int:bank_id>')
@limiter.limit("100/minute")

def get_bank_by_id(bank_id):
    """Get detailed bank information by ID"""
    try:
        bank = Bank.query.get_or_404(bank_id)
        
        # Get latest financial metrics
        latest_metrics = BankFinancialMetric.query.filter_by(bank_id=bank_id).order_by(
            BankFinancialMetric.reporting_date.desc()
        ).first()
        
        # Get research documents
        documents = ResearchDocument.query.filter_by(
            entity_id=bank_id, entity_type='bank'
        ).order_by(ResearchDocument.publication_date.desc()).limit(10).all()
        
        bank_data = serialize_bank(bank)
        bank_data['latest_metrics'] = serialize_bank_metrics(latest_metrics) if latest_metrics else None
        bank_data['recent_documents'] = [
            {
                "title": doc.title,
                "document_type": doc.document_type,
                "publication_date": doc.publication_date.strftime('%Y-%m-%d'),
                "file_url": doc.file_url,
                "summary": doc.summary
            } for doc in documents
        ]
        
        return jsonify(bank_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_bank_by_id: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@banking_api.route('/banks/<int:bank_id>/financial-metrics')
@limiter.limit("50/minute")

def get_bank_financial_metrics(bank_id):
    """Get financial metrics for a specific bank"""
    try:
        bank = Bank.query.get_or_404(bank_id)
        
        # Query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = BankFinancialMetric.query.filter_by(bank_id=bank_id)
        
        if date_from:
            from datetime import datetime
            query = query.filter(BankFinancialMetric.reporting_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            from datetime import datetime
            query = query.filter(BankFinancialMetric.reporting_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            
        metrics = query.order_by(BankFinancialMetric.reporting_date.desc()).all()
        
        return jsonify({
            "bank_name": bank.name,
            "bank_id": bank_id,
            "metrics": [serialize_bank_metrics(metric) for metric in metrics]
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_bank_financial_metrics: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@banking_api.route('/banking-sector/overview')
@limiter.limit("30/minute")
def get_banking_sector_overview():
    """Get comprehensive banking sector overview and statistics"""
    try:
        # Basic sector statistics
        total_banks = Bank.query.count()
        commercial_banks = Bank.query.filter_by(bank_type='Commercial').count()
        development_banks = Bank.query.filter_by(bank_type='Development').count()
        
        # Aggregate metrics from latest reporting period
        latest_metrics = db.session.query(
            db.func.sum(BankFinancialMetric.total_assets).label('sector_assets'),
            db.func.sum(BankFinancialMetric.total_deposits).label('sector_deposits'),
            db.func.sum(BankFinancialMetric.total_loans).label('sector_loans'),
            db.func.avg(BankFinancialMetric.npl_ratio).label('avg_npl_ratio'),
            db.func.avg(BankFinancialMetric.capital_adequacy_ratio).label('avg_car'),
            db.func.sum(BankFinancialMetric.mobile_banking_users).label('total_mobile_users')
        ).join(Bank).filter(
            BankFinancialMetric.reporting_date == db.session.query(
                db.func.max(BankFinancialMetric.reporting_date)
            ).scalar()
        ).first()
        
        # Top banks by assets
        top_banks = db.session.query(Bank, BankFinancialMetric).join(
            BankFinancialMetric
        ).filter(
            BankFinancialMetric.reporting_date == db.session.query(
                db.func.max(BankFinancialMetric.reporting_date)
            ).scalar()
        ).order_by(BankFinancialMetric.total_assets.desc()).limit(5).all()
        
        return jsonify({
            "sector_statistics": {
                "total_banks": total_banks,
                "commercial_banks": commercial_banks,
                "development_banks": development_banks,
                "total_assets": float(latest_metrics.sector_assets) if latest_metrics and latest_metrics.sector_assets else 0,
                "total_deposits": float(latest_metrics.sector_deposits) if latest_metrics and latest_metrics.sector_deposits else 0,
                "total_loans": float(latest_metrics.sector_loans) if latest_metrics and latest_metrics.sector_loans else 0,
                "average_npl_ratio": round(float(latest_metrics.avg_npl_ratio), 2) if latest_metrics and latest_metrics.avg_npl_ratio else 0,
                "average_car": round(float(latest_metrics.avg_car), 2) if latest_metrics and latest_metrics.avg_car else 0,
                "total_mobile_banking_users": int(latest_metrics.total_mobile_users) if latest_metrics and latest_metrics.total_mobile_users else 0
            },
            "top_banks_by_assets": [
                {
                    "bank_name": bank.name,
                    "total_assets": metrics.total_assets,
                    "market_share": round((metrics.total_assets / latest_metrics.sector_assets * 100), 2) if latest_metrics.sector_assets else 0
                } for bank, metrics in top_banks
            ]
        })

    except Exception as e:
        logger.error(f"Error in get_banking_sector_overview: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@banking_api.route('/banking-sector/performance-comparison')
@limiter.limit("30/minute")

def get_banking_performance_comparison():
    """Compare performance metrics across banks"""
    try:
        metric_type = request.args.get('metric', 'return_on_assets')
        period = request.args.get('period', 'latest')
        
        # Get latest metrics for all banks
        query = db.session.query(Bank, BankFinancialMetric).join(BankFinancialMetric)
        
        if period == 'latest':
            query = query.filter(
                BankFinancialMetric.reporting_date == db.session.query(
                    db.func.max(BankFinancialMetric.reporting_date)
                ).scalar()
            )
        
        results = query.order_by(getattr(BankFinancialMetric, metric_type).desc()).all()
        
        return jsonify({
            "metric_type": metric_type,
            "period": period,
            "bank_rankings": [
                {
                    "rank": idx + 1,
                    "bank_name": bank.name,
                    "metric_value": getattr(metrics, metric_type),
                    "bank_type": bank.bank_type,
                    "ownership_type": bank.ownership_type
                } for idx, (bank, metrics) in enumerate(results) 
                if getattr(metrics, metric_type) is not None
            ]
        })

    except Exception as e:
        logger.error(f"Error in get_banking_performance_comparison: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500