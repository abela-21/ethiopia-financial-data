from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models import Company, Stock, Financial, MacroIndicators, Bank, ResearchDocument, EconomicSector, db
from functools import wraps
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

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
@login_required
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

@main_bp.route('/admin')
@login_required
def admin_panel():
    """Admin panel for platform management"""
    from models import User
    
    # Check admin permissions
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Get user statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(active=True).count()
        admin_users = User.query.filter_by(role='admin').count()
        
        # Get recent users (last 10)
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        admin_stats = {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'recent_users': recent_users
        }
        
        return render_template('admin/panel.html', admin_stats=admin_stats)
    except Exception as e:
        logger.error(f"Error in admin_panel route: {str(e)}")
        flash('Error loading admin panel', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/admin/manage-data')
@login_required
def admin_manage_data():
    """Admin data management interface"""
    from models import (User, Company, Financial, Bank, ResearchDocument, MacroIndicators, 
                       ListedCompany, CompanyFinancialMetric, FinancialStatement, 
                       BankFinancialMetric, EconomicDataSource, DocumentCategory)
    
    # Check admin permissions
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Get comprehensive data statistics
        data_stats = {
            'companies': Company.query.count(),
            'financial_records': Financial.query.count(),
            'banks': Bank.query.count(),
            'research_docs': ResearchDocument.query.count(),
            'economic_indicators': MacroIndicators.query.count(),
            'users': User.query.count(),
            'listed_companies': ListedCompany.query.count(),
            'company_metrics': CompanyFinancialMetric.query.count(),
            'financial_statements': FinancialStatement.query.count(),
            'bank_metrics': BankFinancialMetric.query.count(),
            'data_sources': EconomicDataSource.query.count(),
            'document_categories': DocumentCategory.query.count()
        }
        
        # Get recent activity
        recent_companies = Company.query.order_by(Company.id.desc()).limit(5).all()
        recent_financial = Financial.query.order_by(Financial.year.desc()).limit(5).all()
        recent_research = ResearchDocument.query.order_by(ResearchDocument.publication_date.desc()).limit(5).all()
        
        return render_template('admin/manage_data.html', 
                             data_stats=data_stats,
                             recent_companies=recent_companies,
                             recent_financial=recent_financial,
                             recent_research=recent_research)
    except Exception as e:
        logger.error(f"Error in admin_manage_data route: {str(e)}")
        flash('Error loading data management panel', 'error')
        return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/data/companies')
@login_required
def admin_view_companies():
    """View and manage companies data"""
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        companies = Company.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/companies_data.html', companies=companies)
    except Exception as e:
        logger.error(f"Error in admin_view_companies: {str(e)}")
        flash('Error loading companies data', 'error')
        return redirect(url_for('main.admin_manage_data'))

@main_bp.route('/admin/data/financial')
@login_required
def admin_view_financial():
    """View and manage financial data"""
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        financial_data = Financial.query.join(Company).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/financial_data.html', financial_data=financial_data)
    except Exception as e:
        logger.error(f"Error in admin_view_financial: {str(e)}")
        flash('Error loading financial data', 'error')
        return redirect(url_for('main.admin_manage_data'))

@main_bp.route('/admin/data/refresh', methods=['POST'])
@login_required
def admin_refresh_data():
    """Refresh platform data from migration scripts"""
    if not current_user.role == 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Import and run data migration
        from data_migration import EthiopianDataMigration
        
        migration = EthiopianDataMigration()
        migration.run_full_migration()
        
        return jsonify({
            'success': True,
            'message': 'Data refresh completed successfully'
        })
    except Exception as e:
        logger.error(f"Error in admin_refresh_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Data refresh failed: {str(e)}'
        }), 500

@main_bp.route('/admin/data/banks')
@login_required
def admin_view_banks():
    """View and manage banks data"""
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        banks = Bank.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/banks_data.html', banks=banks)
    except Exception as e:
        logger.error(f"Error in admin_view_banks: {str(e)}")
        flash('Error loading banks data', 'error')
        return redirect(url_for('main.admin_manage_data'))

@main_bp.route('/admin/data/research')
@login_required
def admin_view_research():
    """View and manage research documents"""
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        research = ResearchDocument.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/research_data.html', research=research)
    except Exception as e:
        logger.error(f"Error in admin_view_research: {str(e)}")
        flash('Error loading research data', 'error')
        return redirect(url_for('main.admin_manage_data'))

@main_bp.route('/admin/data/economic-indicators')
@login_required
def admin_view_economic_indicators():
    """View and manage economic indicators"""
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        indicators = MacroIndicators.query.order_by(desc(MacroIndicators.date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/indicators_data.html', indicators=indicators)
    except Exception as e:
        logger.error(f"Error in admin_view_economic_indicators: {str(e)}")
        flash('Error loading economic indicators', 'error')
        return redirect(url_for('main.admin_manage_data'))

@main_bp.route('/admin/data/listed-companies')
@login_required
def admin_view_listed_companies():
    """View and manage listed companies"""
    from models import ListedCompany
    
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        listed_companies = ListedCompany.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/listed_companies_data.html', listed_companies=listed_companies)
    except Exception as e:
        logger.error(f"Error in admin_view_listed_companies: {str(e)}")
        flash('Error loading listed companies', 'error')
        return redirect(url_for('main.admin_manage_data'))

@main_bp.route('/admin/data/users')
@login_required
def admin_view_users():
    """View and manage users"""
    from models import User
    
    if not current_user.role == 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        users = User.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/users_data.html', users=users)
    except Exception as e:
        logger.error(f"Error in admin_view_users: {str(e)}")
        flash('Error loading users data', 'error')
        return redirect(url_for('main.admin_manage_data'))

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

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User personalized dashboard"""
    # Create a mock user context for testing
    from flask import g
    g.current_user = type('MockUser', (), {
        'first_name': 'Test',
        'email': 'test@example.com',
        'is_authenticated': True
    })()
    return render_template('dashboard.html', current_user=g.current_user)

@main_bp.route('/search')
@login_required
def search():
    """Advanced search and filtering interface"""
    return render_template('search.html')

@main_bp.route('/banking')
def banking():
    """Banking sector analysis page"""
    try:
        # Get banking sector statistics
        total_banks = Bank.query.count()
        total_branches = db.session.query(func.sum(Bank.branch_count)).scalar() or 0
        total_digital_users = db.session.query(func.sum(Bank.digital_banking_users)).scalar() or 0
        
        banking_stats = {
            'total_banks': total_banks,
            'total_branches': total_branches,
            'total_digital_users': total_digital_users
        }
        
        return render_template('banking.html', banking_stats=banking_stats)
    except Exception as e:
        logger.error(f"Error in banking route: {str(e)}")
        flash('Error loading banking data', 'error')
        return render_template('banking.html', banking_stats={})

@main_bp.route('/research')
def research():
    """Research documents page"""
    try:
        # Get research statistics
        total_docs = ResearchDocument.query.count()
        total_downloads = db.session.query(func.sum(ResearchDocument.download_count)).scalar() or 0
        
        # Get document type counts
        doc_types = db.session.query(
            ResearchDocument.document_type,
            func.count(ResearchDocument.id)
        ).group_by(ResearchDocument.document_type).all()
        
        research_stats = {
            'total_docs': total_docs,
            'total_downloads': total_downloads,
            'doc_types': dict(doc_types)
        }
        
        return render_template('research.html', research_stats=research_stats)
    except Exception as e:
        logger.error(f"Error in research route: {str(e)}")
        flash('Error loading research data', 'error')
        return render_template('research.html', research_stats={})

@main_bp.route('/financial-data')
@login_required
def financial_data():
    """Financial data downloads page for Ethiopian listed companies"""
    try:
        from models import ListedCompany, CompanyFinancialMetric
        
        # Get basic statistics
        total_companies = ListedCompany.query.filter_by(is_active=True).count()
        total_metrics = CompanyFinancialMetric.query.count()
        total_market_cap = db.session.query(func.sum(ListedCompany.market_cap)).scalar() or 0
        
        # Get sector distribution
        sectors = db.session.query(
            ListedCompany.sector,
            func.count(ListedCompany.id)
        ).filter_by(is_active=True).group_by(ListedCompany.sector).all()
        
        financial_stats = {
            'total_companies': total_companies,
            'total_metrics': total_metrics,
            'total_market_cap': total_market_cap,
            'sectors': dict(sectors)
        }
        
        return render_template('financial_data.html', financial_stats=financial_stats)
    except Exception as e:
        logger.error(f"Error in financial_data route: {str(e)}")
        flash('Error loading financial data', 'error')
        return render_template('financial_data.html', financial_stats={})


# API endpoints for data management actions
@main_bp.route('/admin/api/indicator/<int:indicator_id>', methods=['GET'])
@login_required
@admin_required
def get_indicator_api(indicator_id):
    """API endpoint to get economic indicator details"""
    try:
        indicator = MacroIndicators.query.get_or_404(indicator_id)
        
        # Extract year and quarter from date
        year = indicator.date.year if indicator.date else None
        quarter = ((indicator.date.month - 1) // 3) + 1 if indicator.date else None
        
        indicator_data = {
            'id': indicator.id,
            'date': indicator.date.strftime('%Y-%m-%d') if indicator.date else '',
            'gdp_growth': float(indicator.gdp_growth) if indicator.gdp_growth else None,
            'inflation_rate': float(indicator.inflation_rate) if indicator.inflation_rate else None,
            'etb_usd': float(indicator.etb_usd) if indicator.etb_usd else None,
            'interest_rate': float(indicator.interest_rate) if indicator.interest_rate else None,
            'unemployment_rate': float(indicator.unemployment_rate) if indicator.unemployment_rate else None
        }
        
        return jsonify({
            'success': True,
            'indicator': indicator_data
        })
        
    except Exception as e:
        logger.error(f"Error getting indicator {indicator_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/admin/api/indicator/<int:indicator_id>', methods=['PUT'])
@login_required
@admin_required
def update_indicator_api(indicator_id):
    """API endpoint to update economic indicator"""
    try:
        indicator = MacroIndicators.query.get_or_404(indicator_id)
        data = request.get_json()
        
        # Update fields
        if 'date' in data:
            from datetime import datetime
            indicator.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
        if 'gdp_growth' in data:
            indicator.gdp_growth = data['gdp_growth']
            
        if 'inflation_rate' in data:
            indicator.inflation_rate = data['inflation_rate']
            
        if 'etb_usd' in data:
            indicator.etb_usd = data['etb_usd']
            
        if 'interest_rate' in data:
            indicator.interest_rate = data['interest_rate']
            
        if 'unemployment_rate' in data:
            indicator.unemployment_rate = data['unemployment_rate']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Economic indicator updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating indicator {indicator_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


