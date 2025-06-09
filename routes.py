from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import Company, Stock, Financial, MacroIndicators, db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page with market overview"""
    try:
        # Get basic market stats
        total_companies = Company.query.count()
        
        # Get latest stock data
        latest_date = db.session.query(func.max(Stock.date)).scalar()
        active_companies = 0
        total_volume = 0
        
        if latest_date:
            # Count companies with stock data on latest date
            active_companies = db.session.query(Stock.company_id).filter(
                Stock.date == latest_date
            ).distinct().count()
            
            # Sum total volume for latest date
            volume_sum = db.session.query(func.sum(Stock.volume)).filter(
                Stock.date == latest_date
            ).scalar()
            total_volume = volume_sum if volume_sum else 0
        
        # Get latest macro indicators
        latest_macro = MacroIndicators.query.order_by(desc(MacroIndicators.date)).first()
        
        market_summary = {
            'total_companies': total_companies,
            'active_companies': active_companies,
            'total_volume': total_volume,
            'last_updated': latest_date.strftime('%Y-%m-%d') if latest_date else 'N/A'
        }
        
        return render_template('index.html', 
                             market_summary=market_summary,
                             latest_macro=latest_macro)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash('Error loading market data', 'error')
        return render_template('index.html', market_summary={}, latest_macro=None)

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard page - redirect to index for now"""
    return redirect(url_for('main.index'))

@main_bp.route('/companies')
def companies():
    """Companies listing page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '')
        industry = request.args.get('industry', '')
        
        query = Company.query
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Company.name.ilike(search_term) | 
                Company.ticker.ilike(search_term)
            )
        
        if industry:
            query = query.filter(Company.industry == industry)
        
        companies = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get available industries for filter
        industries = db.session.query(Company.industry).distinct().all()
        industries = [i[0] for i in industries if i[0]]
        
        return render_template('companies.html', 
                             companies=companies,
                             industries=industries,
                             current_search=search,
                             current_industry=industry)
    except Exception as e:
        logger.error(f"Error in companies route: {str(e)}")
        flash('Error loading companies data', 'error')
        return render_template('companies.html', companies=None, industries=[])

@main_bp.route('/companies/<int:company_id>')
def company_detail(company_id):
    """Company detail page"""
    try:
        company = Company.query.get_or_404(company_id)
        
        # Get latest stock data
        latest_stock = Stock.query.filter_by(company_id=company_id)\
            .order_by(desc(Stock.date)).first()
        
        # Get recent stock history (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        stock_history = Stock.query.filter_by(company_id=company_id)\
            .filter(Stock.date >= thirty_days_ago)\
            .order_by(Stock.date.asc()).all()
        
        # Get latest financial data
        latest_financial = Financial.query.filter_by(company_id=company_id)\
            .order_by(desc(Financial.year), desc(Financial.period)).first()
        
        return render_template('company_detail.html',
                             company=company,
                             latest_stock=latest_stock,
                             stock_history=stock_history,
                             latest_financial=latest_financial)
    except Exception as e:
        logger.error(f"Error in company_detail route: {str(e)}")
        flash('Error loading company details', 'error')
        return redirect(url_for('main.companies'))

@main_bp.route('/market')
def market():
    """Market overview page"""
    try:
        # Get market summary data
        latest_date = db.session.query(func.max(Stock.date)).scalar()
        
        market_data = {
            'summary': {},
            'top_performers': [],
            'latest_date': latest_date.strftime('%Y-%m-%d') if latest_date else None
        }
        
        if latest_date:
            # Get top performers
            top_performers = db.session.query(
                Company, Stock
            ).join(Stock).filter(
                Stock.date == latest_date
            ).order_by(desc(Stock.volume)).limit(10).all()
            
            market_data['top_performers'] = [
                {
                    'company': company,
                    'stock': stock,
                    'change': round(((stock.close - stock.open) / stock.open) * 100, 2) if stock.open else 0
                }
                for company, stock in top_performers
            ]
        
        return render_template('market.html', market_data=market_data)
    except Exception as e:
        logger.error(f"Error in market route: {str(e)}")
        flash('Error loading market data', 'error')
        return render_template('market.html', market_data={'summary': {}, 'top_performers': []})

@main_bp.route('/macro')
def macro():
    """Macroeconomic indicators page"""
    try:
        # Get latest macro indicators
        latest_indicators = MacroIndicators.query.order_by(
            desc(MacroIndicators.date)
        ).limit(12).all()
        
        # Get historical data for charts (last 12 months)
        historical_data = MacroIndicators.query.order_by(
            desc(MacroIndicators.date)
        ).limit(12).all()
        
        return render_template('macro.html',
                             latest_indicators=latest_indicators,
                             historical_data=historical_data)
    except Exception as e:
        logger.error(f"Error in macro route: {str(e)}")
        flash('Error loading macro indicators', 'error')
        return render_template('macro.html', latest_indicators=[], historical_data=[])

@main_bp.route('/downloads')
def downloads():
    """Downloads page"""
    try:
        # Get available data counts
        stats = {
            'companies_count': Company.query.count(),
            'financials_count': Financial.query.count(),
            'stocks_count': Stock.query.count(),
            'macro_count': MacroIndicators.query.count()
        }
        
        # Get available industries and date ranges
        industries = db.session.query(Company.industry).distinct().all()
        industries = [i[0] for i in industries if i[0]]
        
        # Get date ranges
        stock_date_range = db.session.query(
            func.min(Stock.date), func.max(Stock.date)
        ).first()
        
        macro_date_range = db.session.query(
            func.min(MacroIndicators.date), func.max(MacroIndicators.date)
        ).first()
        
        return render_template('downloads.html',
                             stats=stats,
                             industries=industries,
                             stock_date_range=stock_date_range,
                             macro_date_range=macro_date_range)
    except Exception as e:
        logger.error(f"Error in downloads route: {str(e)}")
        flash('Error loading downloads page', 'error')
        return render_template('downloads.html', stats={}, industries=[])

@main_bp.route('/api/search/companies')
def search_companies_api():
    """API endpoint for company search"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify([])
        
        search_term = f"%{query}%"
        companies = Company.query.filter(
            Company.name.ilike(search_term) | 
            Company.ticker.ilike(search_term)
        ).limit(limit).all()
        
        results = [{
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker,
            'industry': c.industry
        } for c in companies]
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in search_companies_api: {str(e)}")
        return jsonify([])
