from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="user", index=True)  # user/admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    companies_created = db.relationship('Company', 
                                      foreign_keys='Company.created_by',
                                      backref='creator', 
                                      lazy=True)
    companies_updated = db.relationship('Company', 
                                      foreign_keys='Company.updated_by',
                                      backref='updater', 
                                      lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, unique=True, index=True)
    industry = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    sector = db.Column(db.String(50), index=True)
    website = db.Column(db.String(200))
    established_date = db.Column(db.Date)
    shares_outstanding = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    # Relationships
    financials = db.relationship("Financial", backref="company", lazy=True, cascade="all, delete-orphan")
    news_items = db.relationship("CompanyNews", backref="company", lazy=True, cascade="all, delete-orphan")
    stocks = db.relationship("Stock", backref="company", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.ticker}: {self.name}>"

class CompanyAudit(db.Model):
    """Company Audit Model"""
    __tablename__ = "company_audit"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    details = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company', backref=db.backref('audit_logs', lazy=True))

class Financial(db.Model):
    __tablename__ = "financials"
    __table_args__ = (db.UniqueConstraint('company_id', 'year', 'period', name='unique_financial_period'),)

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    year = db.Column(db.Integer, nullable=False, index=True)
    period = db.Column(db.String(10), nullable=False, index=True)  # Annual/Q1/Q2/Q3/Q4

    # Income Statement
    revenue = db.Column(db.Float(precision=2))
    cost_of_revenue = db.Column(db.Float(precision=2))
    gross_profit = db.Column(db.Float(precision=2))
    operating_expenses = db.Column(db.Float(precision=2))
    operating_income = db.Column(db.Float(precision=2))
    ebitda = db.Column(db.Float(precision=2))
    interest_expense = db.Column(db.Float(precision=2))
    profit_before_tax = db.Column(db.Float(precision=2))
    net_income = db.Column(db.Float(precision=2))

    # Balance Sheet
    cash_equivalents = db.Column(db.Float(precision=2))
    accounts_receivable = db.Column(db.Float(precision=2))
    inventory = db.Column(db.Float(precision=2))
    total_current_assets = db.Column(db.Float(precision=2))
    fixed_assets = db.Column(db.Float(precision=2))
    total_assets = db.Column(db.Float(precision=2))
    accounts_payable = db.Column(db.Float(precision=2))
    short_term_debt = db.Column(db.Float(precision=2))
    total_current_liabilities = db.Column(db.Float(precision=2))
    long_term_debt = db.Column(db.Float(precision=2))
    total_liabilities = db.Column(db.Float(precision=2))
    total_equity = db.Column(db.Float(precision=2))

    # Cash Flow
    operating_cash_flow = db.Column(db.Float(precision=2))
    investing_cash_flow = db.Column(db.Float(precision=2))
    financing_cash_flow = db.Column(db.Float(precision=2))
    net_cash_flow = db.Column(db.Float(precision=2))

    # Key Ratios
    current_ratio = db.Column(db.Float(precision=4))
    debt_to_equity = db.Column(db.Float(precision=4))
    return_on_equity = db.Column(db.Float(precision=4))
    return_on_assets = db.Column(db.Float(precision=4))
    profit_margin = db.Column(db.Float(precision=4))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return f"<Financial {self.company.ticker} - {self.year} {self.period}>"

class Stock(db.Model):
    __tablename__ = "stock"
    __table_args__ = (db.UniqueConstraint('company_id', 'date', name='unique_stock_date'),)

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    open = db.Column(db.Float(precision=2))
    close = db.Column(db.Float(precision=2))
    high = db.Column(db.Float(precision=2))
    low = db.Column(db.Float(precision=2))
    volume = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Stock {self.company.ticker} {self.date}>"

class CompanyNews(db.Model):
    __tablename__ = "company_news"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100))
    published_date = db.Column(db.DateTime, nullable=False, index=True)
    category = db.Column(db.String(50), index=True)  # Company/Industry/Regulatory
    url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return f"<CompanyNews {self.company.ticker}: {self.title[:30]}...>"

class MacroIndicators(db.Model):
    __tablename__ = "macro_indicators"
    __table_args__ = (db.UniqueConstraint('date', name='unique_macro_date'),)

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)

    # Real Sector
    gdp_growth = db.Column(db.Float(precision=2))
    gdp_per_capita = db.Column(db.Float(precision=2))
    inflation_rate = db.Column(db.Float(precision=2))
    food_inflation = db.Column(db.Float(precision=2))
    interest_rate = db.Column(db.Float(precision=2))
    unemployment_rate = db.Column(db.Float(precision=2))
    industrial_production = db.Column(db.Float(precision=2))
    agricultural_production = db.Column(db.Float(precision=2))

    # External Trade & Investment
    exports = db.Column(db.Float(precision=2))
    imports = db.Column(db.Float(precision=2))
    trade_balance = db.Column(db.Float(precision=2))
    current_account_balance = db.Column(db.Float(precision=2))
    fdi_inflow = db.Column(db.Float(precision=2))
    remittances = db.Column(db.Float(precision=2))

    # Foreign Exchange
    fx_reserves = db.Column(db.Float(precision=2))
    etb_usd = db.Column(db.Float(precision=4))
    etb_eur = db.Column(db.Float(precision=4))
    etb_gbp = db.Column(db.Float(precision=4))
    etb_jpy = db.Column(db.Float(precision=4))
    etb_cny = db.Column(db.Float(precision=4))

    # Government Finance
    govt_revenue = db.Column(db.Float(precision=2))
    govt_expenditure = db.Column(db.Float(precision=2))
    budget_deficit = db.Column(db.Float(precision=2))
    govt_debt = db.Column(db.Float(precision=2))
    tax_revenue = db.Column(db.Float(precision=2))

    # Banking & Financial Sector
    total_deposits = db.Column(db.Float(precision=2))
    total_loans = db.Column(db.Float(precision=2))
    npl_ratio = db.Column(db.Float(precision=2))
    loan_to_deposit = db.Column(db.Float(precision=2))
    money_supply_m1 = db.Column(db.Float(precision=2))
    money_supply_m2 = db.Column(db.Float(precision=2))
    private_sector_credit = db.Column(db.Float(precision=2))

    # Key Commodities Prices
    coffee_price = db.Column(db.Float(precision=2))
    gold_price = db.Column(db.Float(precision=2))
    oil_price = db.Column(db.Float(precision=2))
    wheat_price = db.Column(db.Float(precision=2))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return f"<MacroIndicators {self.date}>"
