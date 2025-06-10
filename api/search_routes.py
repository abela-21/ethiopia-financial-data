"""
Advanced Search API Routes
Handles complex company search with multiple filter criteria
"""

from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, ListedCompany, CompanyFinancialMetric
from sqlalchemy import func, desc, and_, or_, text
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/companies', methods=['POST'])
@limiter.limit("60 per minute")
def search_companies():
    """
    Advanced company search with multiple filter criteria
    Supports sector, market cap, financial metrics, and custom filters
    """
    try:
        start_time = datetime.now()
        
        # Get search filters from request
        filters = request.get_json() or {}
        
        # Build base query
        query = db.session.query(ListedCompany).filter(
            ListedCompany.is_active == True
        )
        
        # Apply text search filter
        if filters.get('query'):
            search_term = f"%{filters['query']}%"
            query = query.filter(
                or_(
                    ListedCompany.name.ilike(search_term),
                    ListedCompany.ticker_symbol.ilike(search_term),
                    ListedCompany.description.ilike(search_term)
                )
            )
        
        # Apply sector filter
        if filters.get('sectors'):
            sectors = [s for s in filters['sectors'] if s]
            if sectors:
                query = query.filter(ListedCompany.sector.in_(sectors))
        
        # Apply market cap range filter
        market_cap = filters.get('market_cap', {})
        if market_cap.get('min') is not None:
            query = query.filter(ListedCompany.market_cap >= market_cap['min'])
        if market_cap.get('max') is not None:
            query = query.filter(ListedCompany.market_cap <= market_cap['max'])
        
        # Get companies that match basic filters
        companies = query.all()
        
        # Apply financial metric filters
        filtered_companies = []
        metrics_filter = filters.get('metrics', {})
        custom_metrics = filters.get('custom_metrics', [])
        performance_filters = filters.get('performance_filters', {})
        
        for company in companies:
            # Get financial metrics for this company
            company_metrics = db.session.query(CompanyFinancialMetric).filter(
                CompanyFinancialMetric.company_id == company.id
            ).all()
            
            metrics_dict = {m.metric_name: float(m.metric_value) for m in company_metrics}
            
            # Check financial metric ranges
            if not check_metric_ranges(metrics_dict, metrics_filter):
                continue
            
            # Check custom metric rules
            if not check_custom_metrics(metrics_dict, custom_metrics):
                continue
            
            # Check performance classifications
            if not check_performance_filters(company, metrics_dict, performance_filters):
                continue
            
            # Calculate performance score and add to company data
            performance_score = calculate_performance_score(metrics_dict, company.sector)
            
            # Create enriched company data
            company_data = {
                'id': company.id,
                'name': company.name,
                'ticker_symbol': company.ticker_symbol,
                'sector': company.sector,
                'industry': company.industry,
                'market_cap': company.market_cap,
                'description': company.description,
                'employee_count': company.employee_count,
                'performance_score': performance_score,
                'total_revenue': metrics_dict.get('total_revenue', 0),
                'total_assets': metrics_dict.get('total_assets', 0),
                'net_income': metrics_dict.get('net_income', 0),
                'return_on_assets': metrics_dict.get('return_on_assets', 0),
                'return_on_equity': metrics_dict.get('return_on_equity', 0)
            }
            
            filtered_companies.append(company_data)
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'name')
        filtered_companies = sort_companies(filtered_companies, sort_by)
        
        # Apply pagination
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 10)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_companies = filtered_companies[start_idx:end_idx]
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        # Log search request
        logger.info({
            'endpoint': 'search_companies',
            'filters_applied': len([k for k, v in filters.items() if v]),
            'results_count': len(filtered_companies),
            'execution_time_ms': execution_time,
            'ip': request.remote_addr
        })
        
        return jsonify({
            'success': True,
            'companies': paginated_companies,
            'total': len(filtered_companies),
            'page': page,
            'page_size': page_size,
            'total_pages': (len(filtered_companies) + page_size - 1) // page_size,
            'execution_time': round(execution_time, 2),
            'filters_applied': {
                'text_search': bool(filters.get('query')),
                'sector_filter': bool(filters.get('sectors')),
                'market_cap_filter': bool(market_cap.get('min') or market_cap.get('max')),
                'metrics_filter': bool(any(metrics_filter.values())),
                'custom_metrics': len(custom_metrics),
                'performance_filters': any(performance_filters.values())
            }
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': 'An error occurred while searching companies'
        }), 500

@search_bp.route('/filters/options', methods=['GET'])
@limiter.limit("30 per minute")
def get_filter_options():
    """
    Get available filter options for search interface
    Returns sectors, metric ranges, and other filter options
    """
    try:
        # Get unique sectors
        sectors = db.session.query(ListedCompany.sector).distinct().all()
        sectors = [s[0] for s in sectors if s[0]]
        
        # Get market cap range
        market_cap_stats = db.session.query(
            func.min(ListedCompany.market_cap),
            func.max(ListedCompany.market_cap),
            func.avg(ListedCompany.market_cap)
        ).filter(ListedCompany.market_cap.isnot(None)).first()
        
        if not market_cap_stats:
            market_cap_stats = (0, 0, 0)
        
        # Get metric ranges
        metric_ranges = {}
        common_metrics = ['total_revenue', 'total_assets', 'net_income', 'return_on_assets', 'return_on_equity']
        
        for metric in common_metrics:
            metric_stats = db.session.query(
                func.min(CompanyFinancialMetric.metric_value),
                func.max(CompanyFinancialMetric.metric_value),
                func.avg(CompanyFinancialMetric.metric_value)
            ).filter(
                CompanyFinancialMetric.metric_name == metric
            ).first()
            
            if metric_stats and metric_stats[0] is not None:
                metric_ranges[metric] = {
                    'min': float(metric_stats[0]),
                    'max': float(metric_stats[1]),
                    'avg': float(metric_stats[2])
                }
        
        # Get available metrics
        available_metrics = db.session.query(
            CompanyFinancialMetric.metric_name
        ).distinct().all()
        available_metrics = [m[0] for m in available_metrics if m[0]]
        
        return jsonify({
            'success': True,
            'data': {
                'sectors': sorted(sectors),
                'market_cap_range': {
                    'min': float(market_cap_stats[0]) if market_cap_stats[0] else 0,
                    'max': float(market_cap_stats[1]) if market_cap_stats[1] else 0,
                    'avg': float(market_cap_stats[2]) if market_cap_stats[2] else 0
                },
                'metric_ranges': metric_ranges,
                'available_metrics': sorted(available_metrics),
                'performance_classifications': [
                    'top_performers',
                    'growth_companies', 
                    'undervalued_companies',
                    'dividend_stocks',
                    'small_cap',
                    'large_cap'
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Filter options error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load filter options'
        }), 500

@search_bp.route('/suggestions', methods=['GET'])
@limiter.limit("120 per minute")
def get_search_suggestions():
    """
    Get search suggestions for autocomplete
    Returns company names and ticker symbols
    """
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 20)
        
        if len(query) < 2:
            return jsonify({'success': True, 'suggestions': []})
        
        search_term = f"%{query}%"
        
        companies = db.session.query(
            ListedCompany.id,
            ListedCompany.name,
            ListedCompany.ticker_symbol,
            ListedCompany.sector
        ).filter(
            and_(
                ListedCompany.is_active == True,
                or_(
                    ListedCompany.name.ilike(search_term),
                    ListedCompany.ticker_symbol.ilike(search_term)
                )
            )
        ).limit(limit).all()
        
        suggestions = []
        for company in companies:
            suggestions.append({
                'id': company.id,
                'name': company.name,
                'ticker_symbol': company.ticker_symbol,
                'sector': company.sector,
                'display_text': f"{company.name} ({company.ticker_symbol})"
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Suggestions error: {str(e)}")
        return jsonify({
            'success': False,
            'suggestions': []
        })

# Helper Functions

def check_metric_ranges(metrics_dict, metrics_filter):
    """Check if company metrics fall within specified ranges"""
    for metric_type, ranges in metrics_filter.items():
        if not ranges:
            continue
            
        metric_value = metrics_dict.get(metric_type.replace('_', '_'))
        if metric_value is None:
            continue
            
        if ranges.get('min') is not None and metric_value < ranges['min']:
            return False
        if ranges.get('max') is not None and metric_value > ranges['max']:
            return False
    
    return True

def check_custom_metrics(metrics_dict, custom_metrics):
    """Check if company meets custom metric criteria"""
    for rule in custom_metrics:
        metric_name = rule.get('metric')
        operator = rule.get('operator')
        target_value = rule.get('value')
        
        if not all([metric_name, operator, target_value is not None]):
            continue
            
        actual_value = metrics_dict.get(metric_name)
        if actual_value is None:
            return False
            
        if not evaluate_condition(actual_value, operator, target_value):
            return False
    
    return True

def evaluate_condition(actual_value, operator, target_value):
    """Evaluate a single metric condition"""
    if operator == 'gt':
        return actual_value > target_value
    elif operator == 'lt':
        return actual_value < target_value
    elif operator == 'eq':
        return abs(actual_value - target_value) < 0.01
    elif operator == 'gte':
        return actual_value >= target_value
    elif operator == 'lte':
        return actual_value <= target_value
    return True

def check_performance_filters(company, metrics_dict, performance_filters):
    """Check if company meets performance classification criteria"""
    if not any(performance_filters.values()):
        return True
    
    performance_score = calculate_performance_score(metrics_dict, company.sector)
    market_cap = company.market_cap or 0
    
    matches = []
    
    if performance_filters.get('top_performers'):
        matches.append(performance_score >= 80)
    
    if performance_filters.get('growth_companies'):
        # High revenue growth indicator (simplified)
        growth_score = metrics_dict.get('return_on_assets', 0)
        matches.append(growth_score >= 8)
    
    if performance_filters.get('undervalued'):
        # Low P/E ratio indicator (simplified)
        pe_ratio = calculate_pe_ratio(metrics_dict, market_cap)
        matches.append(pe_ratio > 0 and pe_ratio < 15)
    
    # Return True if any filter matches
    return any(matches) if matches else True

def calculate_performance_score(metrics_dict, sector):
    """Calculate overall performance score for a company"""
    score = 50  # Base score
    
    # ROA contribution
    roa = metrics_dict.get('return_on_assets', 0)
    if roa > 15:
        score += 20
    elif roa > 10:
        score += 15
    elif roa > 5:
        score += 10
    
    # ROE contribution
    roe = metrics_dict.get('return_on_equity', 0)
    if roe > 20:
        score += 15
    elif roe > 15:
        score += 10
    elif roe > 10:
        score += 5
    
    # Revenue size contribution
    revenue = metrics_dict.get('total_revenue', 0)
    if revenue > 10000000000:  # 10B+
        score += 10
    elif revenue > 1000000000:  # 1B+
        score += 8
    elif revenue > 100000000:  # 100M+
        score += 5
    
    # Sector adjustments
    sector_multipliers = {
        'Banking': 0.95,
        'Telecommunications': 1.1,
        'Transportation': 1.0,
        'Consumer Goods': 1.05,
        'Materials': 0.9
    }
    
    multiplier = sector_multipliers.get(sector, 1.0)
    score = score * multiplier
    
    return min(100, max(0, round(score)))

def calculate_pe_ratio(metrics_dict, market_cap):
    """Calculate Price-to-Earnings ratio"""
    net_income = metrics_dict.get('net_income', 0)
    if net_income <= 0 or market_cap <= 0:
        return 0
    return market_cap / net_income

def sort_companies(companies, sort_by):
    """Sort companies based on specified criteria"""
    reverse = True  # Default to descending
    
    if sort_by == 'name':
        reverse = False
        key_func = lambda x: x['name'].lower()
    elif sort_by == 'market_cap':
        key_func = lambda x: x['market_cap'] or 0
    elif sort_by == 'revenue':
        key_func = lambda x: x['total_revenue'] or 0
    elif sort_by == 'assets':
        key_func = lambda x: x['total_assets'] or 0
    elif sort_by == 'performance':
        key_func = lambda x: x['performance_score'] or 0
    else:
        key_func = lambda x: x['name'].lower()
        reverse = False
    
    return sorted(companies, key=key_func, reverse=reverse)

# Register error handlers
@search_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad Request',
        'message': 'Invalid search parameters'
    }), 400

@search_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': 'Search service temporarily unavailable'
    }), 500