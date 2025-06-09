from flask import Flask, render_template, jsonify, send_file # Make sure send_file is imported
from flask_migrate import Migrate
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
import logging
from datetime import timedelta, date # Import date for generating current dates
import pandas as pd # Import pandas for CSV generation
import io # Import io for in-memory CSV
import random # For initial mock data in placeholders if you don't have DB data yet

# Load environment variables
load_dotenv()

# App config
from config import SQLALCHEMY_DATABASE_URI
from api.models.models import db, bcrypt, Company # Assuming your data models are accessible via db
from api import init_api

# --- IMPORTANT: ADD THESE IMPORTS FOR DATABASE MODELS ---
# You need to import the specific models for your financial data
# Replace 'YourInflationModel', 'YourGapGrowthModel', 'YourExchangeRateModel'
# and 'YourFinancialDatasetModel' with your actual model names.
# For example: from api.models.models import InflationData, GapGrowthData, ExchangeRateData, FinancialDataset
# If your models are in a different file, adjust the import path accordingly.
try:
    from api.models.models import InflationData, GapGrowthData, ExchangeRateData, FinancialDatasetMetadata # Placeholder for your models
    # If you don't have specific models for each, you might query a generic FinancialData table
    # or views. Adjust the placeholder functions below accordingly.
except ImportError:
    logging.warning("Financial data models not found. Using internal mock data for placeholders.")
    # This block will be used if your models are not yet defined/imported.
    # The placeholder functions below already contain mock data as a fallback.


class Config:
    """Base configuration."""
    # ... (Your existing Config class here) ...
    # Database
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

    # CORS
    CORS_HEADERS = "Content-Type"

    # Debug mode
    DEBUG = os.getenv("FLASK_ENV") == "development"

    # Templates & Static
    TEMPLATE_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "templates"
    )
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

    # Cache
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"


def setup_logging(app):
    # ... (Your existing setup_logging function here) ...
    """Configure logging to file and optionally to console."""
    log_dir = os.path.join(app.root_path, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_level = logging.DEBUG if app.debug else logging.INFO
    log_file = os.path.join(log_dir, "app.log")

    # File handler
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler in development
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)


# --- PLACEHOLDER DATABASE INTERACTION FUNCTIONS ---
# YOU MUST REPLACE THESE WITH YOUR ACTUAL DATABASE QUERIES USING 'db' (SQLAlchemy)
# OR YOUR PREFERRED DATABASE INTERFACE.
# The `db.session` context is available within Flask routes.

def get_data_from_db_for_chart(data_type: str) -> list[dict]:
    """
    Fetches time-series data for a chart from the database.
    YOU MUST REPLACE THE IMPLEMENTATION OF THIS FUNCTION.
    """
    logging.info(f"Attempting to fetch data for chart type: {data_type}")
    try:
        if data_type == 'gap_growth':
            # Example using SQLAlchemy model:
            # Assumes GapGrowthData model has 'date' and 'value' columns.
            results = db.session.query(GapGrowthData.date, GapGrowthData.value)\
                        .order_by(GapGrowthData.date.asc()).all()
            return [{"date": r.date.strftime('%Y-%m-%d'), "value": r.value} for r in results]
        elif data_type == 'inflation':
            # Example using SQLAlchemy model:
            # Assumes InflationData model has 'date' and 'rate' columns.
            results = db.session.query(InflationData.date, InflationData.rate)\
                        .order_by(InflationData.date.asc()).all()
            return [{"date": r.date.strftime('%Y-%m-%d'), "value": r.rate} for r in results]
        elif data_type == 'exchange_rate_usdetb':
            # Example using SQLAlchemy model:
            # Assumes ExchangeRateData model has 'date' and 'usd_etb' columns.
            results = db.session.query(ExchangeRateData.date, ExchangeRateData.usd_etb)\
                        .order_by(ExchangeRateData.date.asc()).all()
            return [{"date": r.date.strftime('%Y-%m-%d'), "value": r.usd_etb} for r in results]
        else:
            logging.warning(f"Unknown chart data type requested: {data_type}")
            return []
    except Exception as e:
        logging.error(f"Error fetching chart data for {data_type} from DB: {e}")
        # --- FALLBACK MOCK DATA IF DB FETCH FAILS OR MODELS AREN'T SET UP ---
        # REMOVE THIS MOCK DATA BLOCK ONCE YOUR DB LOGIC IS FULLY IMPLEMENTED AND TESTED
        today = date.today()
        data = []
        initial, fluctuation = 0, 0
        if data_type == 'gap_growth': initial, fluctuation = 2.5, 1.0
        elif data_type == 'inflation': initial, fluctuation = 10.0, 1.5
        elif data_type == 'exchange_rate_usdetb': initial, fluctuation = 58.0, 0.5
        
        current_val = initial
        for i in range(24): # 24 months of mock data
            d = today - timedelta(days=(23 - i) * 30)
            current_val += (random.random() - 0.5) * fluctuation
            if data_type == 'gap_growth': current_val = max(-5.0, min(10.0, current_val))
            elif data_type == 'inflation': current_val = max(0.5, min(25.0, current_val))
            elif data_type == 'exchange_rate_usdetb': current_val = max(50.0, min(65.0, current_val))
            data.append({"date": d.strftime('%Y-%m-%d'), "value": round(current_val, 2)})
        return data
        # --- END FALLBACK MOCK DATA ---


def get_dataset_metadata_from_db() -> list[dict]:
    """
    Fetches metadata for all downloadable datasets from the database.
    YOU MUST REPLACE THE IMPLEMENTATION OF THIS FUNCTION.
    """
    logging.info("Attempting to fetch dataset metadata from DB")
    try:
        # Example using SQLAlchemy model:
        # Assumes FinancialDatasetMetadata model has 'id', 'name', 'description' columns.
        results = db.session.query(FinancialDatasetMetadata.id,
                                   FinancialDatasetMetadata.name,
                                   FinancialDatasetMetadata.description).all()
        datasets_info = []
        for r_id, r_name, r_description in results:
            datasets_info.append({
                "id": r_id,
                "name": r_name,
                "description": r_description,
                "download_url": f"/api/macro/download/{r_id}.csv" # Construct URL
            })
        return datasets_info
    except Exception as e:
        logging.error(f"Error fetching dataset metadata from DB: {e}")
        # --- FALLBACK MOCK DATA IF DB FETCH FAILS OR MODELS AREN'T SET UP ---
        # REMOVE THIS MOCK DATA BLOCK ONCE YOUR DB LOGIC IS FULLY IMPLEMENTED AND TESTED
        mock_datasets = [
            {"id": "inflation_cpi", "name": "Consumer Price Index (CPI) Inflation", "description": "Monthly year-on-year inflation rate.", "download_url": "/api/macro/download/inflation_cpi.csv"},
            {"id": "gdp_gap_growth", "name": "GDP Output Gap Growth", "description": "Estimated annual GDP output gap growth.", "download_url": "/api/macro/download/gdp_gap_growth.csv"},
            {"id": "exchange_rate_usdetb", "name": "USD to ETB Exchange Rate (Official)", "description": "Monthly average official exchange rate.", "download_url": "/api/macro/download/exchange_rate_usdetb.csv"},
            {"id": "unemployment_rate", "name": "National Unemployment Rate", "description": "Quarterly unemployment rate data.", "download_url": "/api/macro/download/unemployment_rate.csv"},
            {"id": "interest_rates", "name": "Central Bank Policy Interest Rate", "description": "Monthly central bank lending rate.", "download_url": "/api/macro/download/interest_rates.csv"}
        ]
        return mock_datasets
        # --- END FALLBACK MOCK DATA ---


def get_full_dataset_from_db(dataset_id: str) -> pd.DataFrame:
    """
    Fetches a complete dataset from the database as a Pandas DataFrame.
    YOU MUST REPLACE THE IMPLEMENTATION OF THIS FUNCTION.
    """
    logging.info(f"Attempting to fetch full dataset for ID: {dataset_id} from DB")
    try:
        # Example: Fetch data based on dataset_id. This is highly dependent on your schema.
        # You might have a single table with a 'dataset_id' column, or separate tables.
        # For simplicity, assuming separate models/tables for each specific dataset.
        if dataset_id == 'inflation_cpi':
            query_results = db.session.query(InflationData).order_by(InflationData.date).all()
            return pd.DataFrame([{'Date': r.date, 'Inflation_Rate': r.rate, 'Source': 'Your DB'} for r in query_results])
        elif dataset_id == 'gdp_gap_growth':
            query_results = db.session.query(GapGrowthData).order_by(GapGrowthData.date).all()
            return pd.DataFrame([{'Date': r.date, 'GDP_Gap_Growth': r.value, 'Units': 'Percent'} for r in query_results])
        elif dataset_id == 'exchange_rate_usdetb':
            query_results = db.session.query(ExchangeRateData).order_by(ExchangeRateData.date).all()
            return pd.DataFrame([{'Date': r.date, 'USD_ETB_Rate': r.usd_etb, 'Currency': 'ETB'} for r in query_results])
        elif dataset_id == 'unemployment_rate':
            # Placeholder for another specific dataset
            # results = db.session.query(UnemploymentData).order_by(UnemploymentData.date).all()
            # return pd.DataFrame([{'Date': r.date, 'Unemployment_Rate': r.rate} for r in results])
            pass # No specific model example, so it falls to mock/error
        elif dataset_id == 'interest_rates':
            # Placeholder for another specific dataset
            pass
        
        logging.warning(f"No specific DB query logic for dataset_id: {dataset_id}. Returning empty or mock.")
        return pd.DataFrame({'Error': [f'Dataset ID "{dataset_id}" not found in DB query logic or model not implemented.']})

    except Exception as e:
        logging.error(f"Error fetching full dataset '{dataset_id}' from DB: {e}")
        # --- FALLBACK MOCK DATA IF DB FETCH FAILS OR MODELS AREN'T SET UP ---
        # REMOVE THIS MOCK DATA BLOCK ONCE YOUR DB LOGIC IS FULLY IMPLEMENTED AND TESTED
        today = date.today()
        dates = [today - timedelta(days=(99 - i) * 7) for i in range(100)] # 100 weeks of mock data
        if dataset_id == 'inflation_cpi':
            data = [round(random.uniform(5.0, 15.0), 2) for _ in range(100)]
            return pd.DataFrame({'Date': dates, 'Inflation_Rate': data, 'Source': 'Mock DB Fallback'})
        elif dataset_id == 'gdp_gap_growth':
            data = [round(random.uniform(-3.0, 5.0), 2) for _ in range(100)]
            return pd.DataFrame({'Date': dates, 'GDP_Gap_Growth': data, 'Units': 'Percent', 'Source': 'Mock DB Fallback'})
        elif dataset_id == 'exchange_rate_usdetb':
            data = [round(random.uniform(55.0, 62.0), 2) for _ in range(100)]
            return pd.DataFrame({'Date': dates, 'USD_ETB_Rate': data, 'Currency': 'ETB', 'Source': 'Mock DB Fallback'})
        elif dataset_id == 'unemployment_rate':
            data = [round(random.uniform(3.0, 8.0), 2) for _ in range(100)]
            return pd.DataFrame({'Date': dates, 'Unemployment_Rate': data, 'Region': 'National', 'Source': 'Mock DB Fallback'})
        elif dataset_id == 'interest_rates':
            data = [round(random.uniform(7.0, 12.0), 2) for _ in range(100)]
            return pd.DataFrame({'Date': dates, 'Policy_Rate': data, 'Type': 'Central Bank', 'Source': 'Mock DB Fallback'})
        else:
            return pd.DataFrame({'Error': [f'Dataset not found in mock DB fallback: {dataset_id}']})
        # --- END FALLBACK MOCK DATA ---


# --- End Placeholder Functions ---


def create_app(config_object=Config):
    """Application factory."""
    # Create necessary directories
    for folder in ["logs", "uploads"]:
        os.makedirs(os.path.join(os.path.dirname(__file__), folder), exist_ok=True)

    app = Flask(
        __name__,
        template_folder=config_object.TEMPLATE_FOLDER,
        static_folder=config_object.STATIC_FOLDER,
    )
    app.config.from_object(config_object)

    # Initialize logging
    setup_logging(app)

    # Initialize extensions
    CORS(app)
    db.init_app(app) # Correct initialization for SQLAlchemy
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    Migrate(app, db)
    # REMOVED: Cache(app) -> This was the redundant call causing the error.
    # The cache initialization is now handled correctly by init_api(app).

    # Rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[config_object.RATELIMIT_DEFAULT],
        storage_uri=config_object.RATELIMIT_STORAGE_URL,
    )

    # API routes (Registering blueprints via init_api)
    init_api(app) # This function calls cache.init_app(app) and registers all blueprints

    # Error handlers
    # NOTE: You already call init_error_handlers(app) inside api/__init__.py as part of init_api.
    # If you also call it here, it might lead to duplicate error handling.
    # It's usually better to have one place for this. Assuming init_api handles it.
    # If init_error_handlers is not being called by init_api, then uncomment this:
    # from api.utils.errors import init_error_handlers
    # init_error_handlers(app)


    # JWT callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        # Example: Add Redis/db blocklist check here
        return False

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Invalid token"}), 401

    # Health check endpoint
    @app.route("/health")
    @limiter.exempt
    def health_check():
        try:
            # Simple database check via SELECT 1
            db.session.execute(db.text("SELECT 1"))
            db_status = "connected"
            return jsonify(
                {
                    "status": "healthy",
                    "database": db_status,
                    "environment": os.getenv("FLASK_ENV", "production"),
                }
            ), 200
        except Exception as e:
            logging.error(f"Health check failed: {str(e)}")
            return jsonify({"status": "unhealthy", "error": str(e)}), 500

    # --- NEW API ROUTES FOR MACRO DATA ---
    @app.route('/api/macro/charts/gap_growth')
    def get_gap_growth_chart_data():
        data = get_data_from_db_for_chart('gap_growth')
        return jsonify(data)

    @app.route('/api/macro/charts/inflation')
    def get_inflation_chart_data():
        data = get_data_from_db_for_chart('inflation')
        return jsonify(data)

    @app.route('/api/macro/charts/exchange_rate_usdetb')
    def get_exchange_rate_chart_data():
        data = get_data_from_db_for_chart('exchange_rate_usdetb')
        return jsonify(data)

    @app.route('/api/macro/datasets')
    def list_macro_datasets():
        datasets_info = get_dataset_metadata_from_db()
        return jsonify(datasets_info)

    @app.route('/api/macro/download/<string:dataset_id>.csv')
    def download_macro_data(dataset_id):
        df = get_full_dataset_from_db(dataset_id)
        
        if df.empty or 'Error' in df.columns.values: # Check for specific 'Error' column from placeholder
            logging.error(f"Download request for '{dataset_id}' failed: Dataframe is empty or contains error.")
            return "Dataset not found or no data available", 404

        # Convert DataFrame to CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0) # Rewind to the beginning of the stream
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{dataset_id}_data.csv"
        )
    # --- END NEW API ROUTES ---


    # Frontend routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("pages/dashboard.html")

    @app.route("/search_results")
    def search_results():
        return render_template("pages/search_results.html")

    @app.route("/company/<identifier>")
    def company_details(identifier):
        try:
            return render_template("pages/company_detail.html", company_identifier=identifier)
        except Exception as e:
            logging.error(f"Error rendering company details page for {identifier}: {str(e)}")
            return render_template("errors/500.html"), 500

    @app.route("/macro-overview")
    def macro_overview():
        return render_template("pages/macro_overview.html")

    @app.route("/home")
    def home():
        return render_template("pages/home.html")

    @app.route("/companies")
    def companies_list():
        return render_template("companies_list.html")

    # Auth pages
    @app.route("/users/login")
    def login_page():
        return render_template("auth/login.html")

    @app.route("/users/register")
    def register_page():
        return render_template("auth/register.html")

    @app.route("/users/reset_password")
    def reset_password_page():
        return render_template("auth/reset_password.html")

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logging.error(f"Internal server error: {str(error)}")
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            logging.info("✅ Database tables created successfully.")
        except Exception as e:
            logging.error(f"❌ Error creating database tables: {e}")

    app.run(
        host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=app.config["DEBUG"]
    )