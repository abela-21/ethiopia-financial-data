"""
Vercel demo entry point (deploy-only; not part of the repository).

Each serverless instance gets its own SQLite database in /tmp, seeded on
cold start with the project's demo data. Changes made in the demo are lost
when the instance is recycled.
"""
import fcntl
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/ethiopia_demo.db")
os.chdir(ROOT)

from app import app, db  # noqa: E402


def _seed():
    from datetime import datetime
    from models import User, Company, Bank
    from werkzeug.security import generate_password_hash

    with app.app_context():
        db.create_all()
        if User.query.first() is not None:
            return

        db.session.add(User(
            username="admin", email=os.environ.get("DEMO_ADMIN_EMAIL", "admin@ethiopia-economic.com"),
            first_name="Demo", last_name="Admin", role="admin", active=True, created_at=datetime.utcnow(),
            password_hash=generate_password_hash(os.environ["DEMO_ADMIN_PASSWORD"]),
        ))
        db.session.commit()

        # data_migration opens a log file in the working directory on import.
        os.chdir("/tmp")
        try:
            from scripts.data_migration import EthiopianDataMigration
        finally:
            os.chdir(ROOT)
        migration = EthiopianDataMigration()
        migration.load_ethiopian_banks()
        migration.load_economic_sectors()
        migration.load_research_documents()
        db.session.commit()

        import Data.load_data as load_data
        load_data.app = app
        for loader in (load_data.load_companies, load_data.load_financials,
                       load_data.load_macro_indicators, load_data.load_stocks):
            loader()

        from scripts.populate_listed_companies import (
            populate_listed_companies, populate_wegagen_financial_metrics,
            populate_ethio_telecom_metrics, populate_other_companies_metrics)
        populate_listed_companies()
        populate_wegagen_financial_metrics()
        populate_ethio_telecom_metrics()
        populate_other_companies_metrics()
        from scripts.populate_financial_statements import populate_financial_statements
        populate_financial_statements()


# One seeding run per instance, even with concurrent first requests.
with open("/tmp/ethiopia_demo.lock", "w") as _lock:
    fcntl.flock(_lock, fcntl.LOCK_EX)
    _seed()
    fcntl.flock(_lock, fcntl.LOCK_UN)
