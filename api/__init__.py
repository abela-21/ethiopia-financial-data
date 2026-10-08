from flask import Blueprint

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Import route modules
from . import company_routes, stock_routes, macro_routes, market_routes, news_routes
from . import banking_routes, research_routes, economic_routes, financial_routes, search_routes, dashboard_routes, external_data_routes, export_routes

# Register existing sub-blueprints
api_bp.register_blueprint(company_routes.company_api)
api_bp.register_blueprint(stock_routes.stock_api)
api_bp.register_blueprint(macro_routes.macro_api)
api_bp.register_blueprint(market_routes.market_api)
api_bp.register_blueprint(news_routes.news_api, url_prefix='/news')

# Register economic data platform blueprints
api_bp.register_blueprint(banking_routes.banking_api, url_prefix='/banking')
api_bp.register_blueprint(research_routes.research_api, url_prefix='/research')
api_bp.register_blueprint(economic_routes.economic_api, url_prefix='/economic')
api_bp.register_blueprint(financial_routes.financial_bp, url_prefix='/financial')

api_bp.register_blueprint(search_routes.search_bp)
api_bp.register_blueprint(dashboard_routes.dashboard_bp)
api_bp.register_blueprint(external_data_routes.external_data_bp, url_prefix='/external-data')
api_bp.register_blueprint(export_routes.export_bp, url_prefix='/export')

# Register download tracking routes
from . import download_routes
api_bp.register_blueprint(download_routes.download_bp, name='download_tracking')
