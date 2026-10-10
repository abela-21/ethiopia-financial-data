import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
cache = Cache()
csrf = CSRFProtect()
from utils.limiter import limiter

def _check_secrets():
    """Never run production with the hard-coded development secrets."""
    missing = [name for name in ("SESSION_SECRET", "JWT_SECRET_KEY") if not os.environ.get(name)]
    if not missing:
        return
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError(f"Missing required secrets in production: {', '.join(missing)}")
    logger.warning(f"Using insecure development defaults for: {', '.join(missing)}")

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    _check_secrets()
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///market.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    
    # Cache Configuration
    app.config["CACHE_TYPE"] = "simple"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    
    # CSRF: tokens are tied to the session rather than expiring after an hour,
    # so long-open admin pages keep working. WTF_CSRF_ENABLED=false disables it
    # (only for local tooling such as the legacy live-server test scripts).
    app.config["WTF_CSRF_ENABLED"] = os.environ.get("WTF_CSRF_ENABLED", "true").lower() != "false"
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    
    # CORS Configuration
    app.config["CORS_HEADERS"] = "Content-Type"
    
    # Proxy fix for production
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    csrf.init_app(app)
    
    # Initialize cache with app context
    with app.app_context():
        cache.init_app(app)
    
    limiter.init_app(app)
    
    # Import models to ensure they're registered
    from models import (User, Company, Stock, Financial, MacroIndicators, CompanyNews, CompanyAudit,
                       EconomicDataSource, Bank, BankFinancialMetric, EconomicSector, 
                       ResearchDocument, DocumentCategory, DataCitation, EconomicForecast, EconomicEvent,
                       ListedCompany, CompanyFinancialMetric, UserWatchlist, WatchlistCompany, 
                       UserAlert, UserPreference, SavedSearch,
                       ExternalDataSource, DataIntegration, RealTimeQuote, CurrencyRate, DataExportLog,
                       ExternalEconomicData)
    
    # Initialize Flask-Login
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes import main_bp
    from api import api_bp
    from auth_routes import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Token-authenticated API clients don't use the session cookie, so they
    # don't need (and can't send) a CSRF token.
    from api.company_routes import company_api
    from auth_routes import issue_token
    csrf.exempt(company_api)
    csrf.exempt(issue_token)
    
    # Error handlers
    from utils.errors import register_error_handlers
    register_error_handlers(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
