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
        
        from models import FinancialStatement
        financial_data = FinancialStatement.query.order_by(desc(FinancialStatement.period_end_date)).paginate(
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
            # Core economic indicators
            'gdp_growth': float(indicator.gdp_growth) if indicator.gdp_growth else None,
            'gdp_per_capita': float(indicator.gdp_per_capita) if indicator.gdp_per_capita else None,
            'inflation_rate': float(indicator.inflation_rate) if indicator.inflation_rate else None,
            'food_inflation': float(indicator.food_inflation) if indicator.food_inflation else None,
            'interest_rate': float(indicator.interest_rate) if indicator.interest_rate else None,
            'unemployment_rate': float(indicator.unemployment_rate) if indicator.unemployment_rate else None,
            'industrial_production': float(indicator.industrial_production) if indicator.industrial_production else None,
            'agricultural_production': float(indicator.agricultural_production) if indicator.agricultural_production else None,
            # Trade and foreign exchange
            'exports': float(indicator.exports) if indicator.exports else None,
            'imports': float(indicator.imports) if indicator.imports else None,
            'trade_balance': float(indicator.trade_balance) if indicator.trade_balance else None,
            'current_account_balance': float(indicator.current_account_balance) if indicator.current_account_balance else None,
            'fdi_inflow': float(indicator.fdi_inflow) if indicator.fdi_inflow else None,
            'remittances': float(indicator.remittances) if indicator.remittances else None,
            'fx_reserves': float(indicator.fx_reserves) if indicator.fx_reserves else None,
            'etb_usd': float(indicator.etb_usd) if indicator.etb_usd else None,
            'etb_eur': float(indicator.etb_eur) if indicator.etb_eur else None,
            'etb_gbp': float(indicator.etb_gbp) if indicator.etb_gbp else None,
            'etb_jpy': float(indicator.etb_jpy) if indicator.etb_jpy else None,
            'etb_cny': float(indicator.etb_cny) if indicator.etb_cny else None,
            # Banking and monetary
            'total_deposits': float(indicator.total_deposits) if indicator.total_deposits else None,
            'total_loans': float(indicator.total_loans) if indicator.total_loans else None,
            'npl_ratio': float(indicator.npl_ratio) if indicator.npl_ratio else None,
            'loan_to_deposit': float(indicator.loan_to_deposit) if indicator.loan_to_deposit else None,
            'money_supply_m1': float(indicator.money_supply_m1) if indicator.money_supply_m1 else None,
            'money_supply_m2': float(indicator.money_supply_m2) if indicator.money_supply_m2 else None,
            'private_sector_credit': float(indicator.private_sector_credit) if indicator.private_sector_credit else None,
            # Government finances
            'govt_revenue': float(indicator.govt_revenue) if indicator.govt_revenue else None,
            'govt_expenditure': float(indicator.govt_expenditure) if indicator.govt_expenditure else None,
            'budget_deficit': float(indicator.budget_deficit) if indicator.budget_deficit else None,
            'govt_debt': float(indicator.govt_debt) if indicator.govt_debt else None,
            'tax_revenue': float(indicator.tax_revenue) if indicator.tax_revenue else None,
            # Commodities
            'coffee_price': float(indicator.coffee_price) if indicator.coffee_price else None,
            'gold_price': float(indicator.gold_price) if indicator.gold_price else None,
            'oil_price': float(indicator.oil_price) if indicator.oil_price else None,
            'wheat_price': float(indicator.wheat_price) if indicator.wheat_price else None
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
            
        # Core economic indicators
        if 'gdp_growth' in data:
            indicator.gdp_growth = data['gdp_growth']
        if 'gdp_per_capita' in data:
            indicator.gdp_per_capita = data['gdp_per_capita']
        if 'inflation_rate' in data:
            indicator.inflation_rate = data['inflation_rate']
        if 'food_inflation' in data:
            indicator.food_inflation = data['food_inflation']
        if 'interest_rate' in data:
            indicator.interest_rate = data['interest_rate']
        if 'unemployment_rate' in data:
            indicator.unemployment_rate = data['unemployment_rate']
        if 'industrial_production' in data:
            indicator.industrial_production = data['industrial_production']
        if 'agricultural_production' in data:
            indicator.agricultural_production = data['agricultural_production']
            
        # Trade and foreign exchange
        if 'exports' in data:
            indicator.exports = data['exports']
        if 'imports' in data:
            indicator.imports = data['imports']
        if 'trade_balance' in data:
            indicator.trade_balance = data['trade_balance']
        if 'current_account_balance' in data:
            indicator.current_account_balance = data['current_account_balance']
        if 'fdi_inflow' in data:
            indicator.fdi_inflow = data['fdi_inflow']
        if 'remittances' in data:
            indicator.remittances = data['remittances']
        if 'fx_reserves' in data:
            indicator.fx_reserves = data['fx_reserves']
        if 'etb_usd' in data:
            indicator.etb_usd = data['etb_usd']
        if 'etb_eur' in data:
            indicator.etb_eur = data['etb_eur']
        if 'etb_gbp' in data:
            indicator.etb_gbp = data['etb_gbp']
        if 'etb_jpy' in data:
            indicator.etb_jpy = data['etb_jpy']
        if 'etb_cny' in data:
            indicator.etb_cny = data['etb_cny']
            
        # Banking and monetary
        if 'total_deposits' in data:
            indicator.total_deposits = data['total_deposits']
        if 'total_loans' in data:
            indicator.total_loans = data['total_loans']
        if 'npl_ratio' in data:
            indicator.npl_ratio = data['npl_ratio']
        if 'loan_to_deposit' in data:
            indicator.loan_to_deposit = data['loan_to_deposit']
        if 'money_supply_m1' in data:
            indicator.money_supply_m1 = data['money_supply_m1']
        if 'money_supply_m2' in data:
            indicator.money_supply_m2 = data['money_supply_m2']
        if 'private_sector_credit' in data:
            indicator.private_sector_credit = data['private_sector_credit']
            
        # Government finances
        if 'govt_revenue' in data:
            indicator.govt_revenue = data['govt_revenue']
        if 'govt_expenditure' in data:
            indicator.govt_expenditure = data['govt_expenditure']
        if 'budget_deficit' in data:
            indicator.budget_deficit = data['budget_deficit']
        if 'govt_debt' in data:
            indicator.govt_debt = data['govt_debt']
        if 'tax_revenue' in data:
            indicator.tax_revenue = data['tax_revenue']
            
        # Commodities
        if 'coffee_price' in data:
            indicator.coffee_price = data['coffee_price']
        if 'gold_price' in data:
            indicator.gold_price = data['gold_price']
        if 'oil_price' in data:
            indicator.oil_price = data['oil_price']
        if 'wheat_price' in data:
            indicator.wheat_price = data['wheat_price']
            
        # Auto-calculate derived fields
        if 'exports' in data and 'imports' in data:
            indicator.trade_balance = indicator.exports - indicator.imports
        if 'govt_revenue' in data and 'govt_expenditure' in data:
            indicator.budget_deficit = indicator.govt_expenditure - indicator.govt_revenue
        if 'total_loans' in data and 'total_deposits' in data and indicator.total_deposits:
            indicator.loan_to_deposit = (indicator.total_loans / indicator.total_deposits) * 100
        
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



# Financial Statement API endpoints
@main_bp.route('/admin/api/financial-statement/<int:statement_id>', methods=['GET'])
@login_required
@admin_required
def get_financial_statement_api(statement_id):
    """API endpoint to get financial statement details"""
    try:
        from models import FinancialStatement
        statement = FinancialStatement.query.get_or_404(statement_id)
        
        statement_data = {
            'id': statement.id,
            'company_id': statement.company_id,
            'company_name': statement.company.name if statement.company else None,
            'ticker_symbol': statement.company.ticker_symbol if statement.company else None,
            'statement_type': statement.statement_type,
            'reporting_period': statement.reporting_period,
            'fiscal_year': statement.fiscal_year,
            'period_start_date': statement.period_start_date.strftime('%Y-%m-%d') if statement.period_start_date else None,
            'period_end_date': statement.period_end_date.strftime('%Y-%m-%d') if statement.period_end_date else None,
            'filing_date': statement.filing_date.strftime('%Y-%m-%d') if statement.filing_date else None,
            
            # Income Statement Data
            'revenue': float(statement.revenue) if statement.revenue else None,
            'cost_of_goods_sold': float(statement.cost_of_goods_sold) if statement.cost_of_goods_sold else None,
            'gross_profit': float(statement.gross_profit) if statement.gross_profit else None,
            'operating_expenses': float(statement.operating_expenses) if statement.operating_expenses else None,
            'operating_income': float(statement.operating_income) if statement.operating_income else None,
            'interest_expense': float(statement.interest_expense) if statement.interest_expense else None,
            'interest_income': float(statement.interest_income) if statement.interest_income else None,
            'net_income': float(statement.net_income) if statement.net_income else None,
            'earnings_per_share': float(statement.earnings_per_share) if statement.earnings_per_share else None,
            
            # Balance Sheet Data
            'total_assets': float(statement.total_assets) if statement.total_assets else None,
            'current_assets': float(statement.current_assets) if statement.current_assets else None,
            'cash_and_equivalents': float(statement.cash_and_equivalents) if statement.cash_and_equivalents else None,
            'accounts_receivable': float(statement.accounts_receivable) if statement.accounts_receivable else None,
            'inventory': float(statement.inventory) if statement.inventory else None,
            'total_liabilities': float(statement.total_liabilities) if statement.total_liabilities else None,
            'current_liabilities': float(statement.current_liabilities) if statement.current_liabilities else None,
            'long_term_debt': float(statement.long_term_debt) if statement.long_term_debt else None,
            'shareholders_equity': float(statement.shareholders_equity) if statement.shareholders_equity else None,
            
            # Cash Flow Data
            'operating_cash_flow': float(statement.operating_cash_flow) if statement.operating_cash_flow else None,
            'investing_cash_flow': float(statement.investing_cash_flow) if statement.investing_cash_flow else None,
            'financing_cash_flow': float(statement.financing_cash_flow) if statement.financing_cash_flow else None,
            'free_cash_flow': float(statement.free_cash_flow) if statement.free_cash_flow else None,
            
            # Banking-specific metrics
            'deposits': float(statement.deposits) if statement.deposits else None,
            'loans_and_advances': float(statement.loans_and_advances) if statement.loans_and_advances else None,
            'loan_loss_provisions': float(statement.loan_loss_provisions) if statement.loan_loss_provisions else None,
            'net_interest_income': float(statement.net_interest_income) if statement.net_interest_income else None,
            'non_interest_income': float(statement.non_interest_income) if statement.non_interest_income else None,
            
            # Metadata
            'currency': statement.currency,
            'is_audited': statement.is_audited,
            'auditor_name': statement.auditor_name,
            'data_source': statement.data_source
        }
        
        return jsonify({
            'success': True,
            'statement': statement_data
        })
        
    except Exception as e:
        logger.error(f"Error in get_financial_statement_api: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving financial statement: {str(e)}'
        }), 500

@main_bp.route('/admin/api/financial-statement/<int:statement_id>', methods=['PUT'])
@login_required
@admin_required
def update_financial_statement_api(statement_id):
    """API endpoint to update financial statement"""
    try:
        from models import FinancialStatement
        statement = FinancialStatement.query.get_or_404(statement_id)
        data = request.get_json()
        
        # Update basic information
        if 'reporting_period' in data:
            statement.reporting_period = data['reporting_period']
        if 'fiscal_year' in data:
            statement.fiscal_year = data['fiscal_year']
        if 'period_start_date' in data and data['period_start_date']:
            from datetime import datetime
            statement.period_start_date = datetime.strptime(data['period_start_date'], '%Y-%m-%d').date()
        if 'period_end_date' in data and data['period_end_date']:
            from datetime import datetime
            statement.period_end_date = datetime.strptime(data['period_end_date'], '%Y-%m-%d').date()
            
        # Update Income Statement fields
        income_fields = [
            'revenue', 'cost_of_goods_sold', 'gross_profit', 'operating_expenses', 
            'operating_income', 'interest_expense', 'interest_income', 'net_income', 'earnings_per_share'
        ]
        for field in income_fields:
            if field in data:
                setattr(statement, field, data[field])
        
        # Update Balance Sheet fields
        balance_fields = [
            'total_assets', 'current_assets', 'cash_and_equivalents', 'accounts_receivable',
            'inventory', 'total_liabilities', 'current_liabilities', 'long_term_debt', 'shareholders_equity'
        ]
        for field in balance_fields:
            if field in data:
                setattr(statement, field, data[field])
        
        # Update Cash Flow fields
        cashflow_fields = [
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'free_cash_flow'
        ]
        for field in cashflow_fields:
            if field in data:
                setattr(statement, field, data[field])
        
        # Update Banking-specific fields
        banking_fields = [
            'deposits', 'loans_and_advances', 'loan_loss_provisions', 'net_interest_income', 'non_interest_income'
        ]
        for field in banking_fields:
            if field in data:
                setattr(statement, field, data[field])
        
        # Auto-calculate derived fields
        if 'revenue' in data and 'cost_of_goods_sold' in data:
            if statement.revenue and statement.cost_of_goods_sold:
                statement.gross_profit = statement.revenue - statement.cost_of_goods_sold
        
        if 'gross_profit' in data and 'operating_expenses' in data:
            if statement.gross_profit and statement.operating_expenses:
                statement.operating_income = statement.gross_profit - statement.operating_expenses
        
        if 'operating_cash_flow' in data and 'investing_cash_flow' in data:
            if statement.operating_cash_flow and statement.investing_cash_flow:
                statement.free_cash_flow = statement.operating_cash_flow + statement.investing_cash_flow
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Financial statement updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in update_financial_statement_api: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error updating financial statement: {str(e)}'
        }), 500

# Add New Record API endpoints
@main_bp.route('/admin/api/companies', methods=['POST'])
@login_required
@admin_required
def add_company_api():
    """API endpoint to add new company"""
    try:
        from models import Company
        data = request.get_json()
        
        company = Company(
            name=data['name'],
            ticker_symbol=data.get('ticker_symbol'),
            sector=data.get('sector'),
            industry=data.get('industry'),
            market_cap=data.get('market_cap'),
            shares_outstanding=data.get('shares_outstanding'),
            description=data.get('description')
        )
        
        db.session.add(company)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Company added successfully',
            'company_id': company.id
        })
        
    except Exception as e:
        logger.error(f"Error adding company: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/admin/api/companies', methods=['GET'])
@login_required
@admin_required
def get_companies_api():
    """API endpoint to get companies for dropdown"""
    try:
        from models import Company
        companies = Company.query.all()
        
        companies_data = [{
            'id': company.id,
            'name': company.name,
            'ticker_symbol': company.ticker_symbol
        } for company in companies]
        
        return jsonify({
            'success': True,
            'companies': companies_data
        })
        
    except Exception as e:
        logger.error(f"Error getting companies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/admin/api/financial-statements', methods=['POST'])
@login_required
@admin_required
def add_financial_statement_api():
    """API endpoint to add new financial statement"""
    try:
        from models import FinancialStatement
        from datetime import datetime
        data = request.get_json()
        
        statement = FinancialStatement(
            company_id=data['company_id'],
            statement_type=data['statement_type'],
            reporting_period=data['reporting_period'],
            fiscal_year=data['fiscal_year'],
            period_start_date=datetime.strptime(data['period_start_date'], '%Y-%m-%d').date(),
            period_end_date=datetime.strptime(data['period_end_date'], '%Y-%m-%d').date(),
            revenue=data.get('revenue'),
            net_income=data.get('net_income'),
            total_assets=data.get('total_assets'),
            total_liabilities=data.get('total_liabilities'),
            currency='ETB'
        )
        
        db.session.add(statement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Financial statement added successfully',
            'statement_id': statement.id
        })
        
    except Exception as e:
        logger.error(f"Error adding financial statement: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/admin/api/economic-indicators', methods=['POST'])
@login_required
@admin_required
def add_economic_indicator_api():
    """API endpoint to add new economic indicator"""
    try:
        from models import EconomicIndicator
        from datetime import datetime
        data = request.get_json()
        
        indicator = EconomicIndicator(
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            category=data['category'],
            gdp=data.get('gdp'),
            inflation_rate=data.get('inflation_rate'),
            exchange_rate=data.get('exchange_rate'),
            population=data.get('population')
        )
        
        db.session.add(indicator)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Economic indicator added successfully',
            'indicator_id': indicator.id
        })
        
    except Exception as e:
        logger.error(f"Error adding economic indicator: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/admin/api/refresh-data', methods=['POST'])
@login_required
@admin_required
def refresh_data_api():
    """API endpoint to refresh platform data"""
    try:
        # Run data migration scripts
        import subprocess
        import os
        
        # Execute data migration
        result = subprocess.run(
            ['python', 'data_migration.py'],
            cwd=os.getcwd(),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Platform data refreshed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Data refresh failed: {result.stderr}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error refreshing data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
