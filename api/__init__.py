from flask import Blueprint

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Import route modules
from . import company_routes, financial_routes, stock_routes, macro_routes, market_routes, download_routes

# Register sub-blueprints
api_bp.register_blueprint(company_routes.company_api)
api_bp.register_blueprint(financial_routes.financials_api)
api_bp.register_blueprint(stock_routes.stock_api)
api_bp.register_blueprint(macro_routes.macro_api)
api_bp.register_blueprint(market_routes.market_api)
api_bp.register_blueprint(download_routes.download_api)
