from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="user", index=True)  # user/admin
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_active(self):
        return self.active

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


# NEW BANKING SECTOR MODELS

class EconomicDataSource(db.Model):
    """Data source tracking for credibility and lineage"""
    __tablename__ = "economic_data_source"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # NBE, Statistics Service, etc.
    abbreviation = db.Column(db.String(20), nullable=False)
    website = db.Column(db.String(200))
    data_types = db.Column(db.JSON)  # Types of data provided
    update_frequency = db.Column(db.String(50))  # Daily, Monthly, Quarterly
    reliability_score = db.Column(db.Float(precision=2))  # 1-10 scale
    last_updated = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<EconomicDataSource {self.name}>"


class Bank(db.Model):
    """Enhanced bank profiles with banking-specific metrics"""
    __tablename__ = "bank"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    license_number = db.Column(db.String(20), unique=True, nullable=False)
    establishment_date = db.Column(db.Date)
    headquarters_location = db.Column(db.String(100))
    branch_count = db.Column(db.Integer)
    atm_count = db.Column(db.Integer)
    digital_banking_users = db.Column(db.Integer)
    nbe_rating = db.Column(db.String(10))  # A, B, C, etc.
    website_url = db.Column(db.String(200))
    logo_url = db.Column(db.String(200))
    swift_code = db.Column(db.String(11))
    bank_type = db.Column(db.String(50))  # Commercial, Development, Microfinance
    ownership_type = db.Column(db.String(50))  # State, Private, Mixed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    financial_metrics = db.relationship("BankFinancialMetric", backref="bank", lazy=True, cascade="all, delete-orphan")
    research_documents = db.relationship("ResearchDocument", 
                                       foreign_keys="ResearchDocument.entity_id",
                                       primaryjoin="and_(Bank.id==ResearchDocument.entity_id, ResearchDocument.entity_type=='bank')",
                                       backref="bank_entity", lazy=True)
    
    def __repr__(self):
        return f"<Bank {self.name}>"


class BankFinancialMetric(db.Model):
    """Banking-specific financial metrics and KPIs"""
    __tablename__ = "bank_financial_metric"
    __table_args__ = (db.UniqueConstraint('bank_id', 'reporting_date', name='unique_bank_metric_date'),)
    
    id = db.Column(db.Integer, primary_key=True)
    bank_id = db.Column(db.Integer, db.ForeignKey("bank.id", ondelete="CASCADE"), nullable=False)
    reporting_date = db.Column(db.Date, nullable=False, index=True)
    
    # Balance Sheet Items
    total_assets = db.Column(db.Float(precision=2))
    total_deposits = db.Column(db.Float(precision=2))
    total_loans = db.Column(db.Float(precision=2))
    shareholders_equity = db.Column(db.Float(precision=2))
    cash_and_bank_balances = db.Column(db.Float(precision=2))
    
    # Income Statement Items
    net_interest_income = db.Column(db.Float(precision=2))
    non_interest_income = db.Column(db.Float(precision=2))
    operating_expenses = db.Column(db.Float(precision=2))
    net_profit = db.Column(db.Float(precision=2))
    loan_loss_provisions = db.Column(db.Float(precision=2))
    
    # Banking-Specific Ratios
    npl_ratio = db.Column(db.Float(precision=4))  # Non-performing loan ratio
    capital_adequacy_ratio = db.Column(db.Float(precision=4))  # CAR
    return_on_assets = db.Column(db.Float(precision=4))  # ROA
    return_on_equity = db.Column(db.Float(precision=4))  # ROE
    loan_to_deposit_ratio = db.Column(db.Float(precision=4))
    cost_to_income_ratio = db.Column(db.Float(precision=4))
    net_interest_margin = db.Column(db.Float(precision=4))
    
    # Digital Banking Metrics
    mobile_banking_users = db.Column(db.Integer)
    internet_banking_users = db.Column(db.Integer)
    digital_transaction_volume = db.Column(db.Float(precision=2))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BankFinancialMetric {self.bank.name} {self.reporting_date}>"


class EconomicSector(db.Model):
    """Economic sector analysis and contribution tracking"""
    __tablename__ = "economic_sector"
    
    id = db.Column(db.Integer, primary_key=True)
    sector_name = db.Column(db.String(50), nullable=False, unique=True)
    sector_code = db.Column(db.String(10))  # ISIC codes
    gdp_contribution = db.Column(db.Float(precision=2))  # Percentage
    employment_share = db.Column(db.Float(precision=2))  # Percentage
    growth_rate = db.Column(db.Float(precision=2))  # Annual growth
    investment_share = db.Column(db.Float(precision=2))  # Percentage of total investment
    export_contribution = db.Column(db.Float(precision=2))  # Percentage of total exports
    last_updated = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<EconomicSector {self.sector_name}>"


class ResearchDocument(db.Model):
    """Research documents and publication repository"""
    __tablename__ = "research_document"
    
    id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.Integer)  # Bank ID, Government agency ID, etc.
    entity_type = db.Column(db.String(20), nullable=False, index=True)  # 'bank', 'government', 'nbe'
    title = db.Column(db.String(200), nullable=False)
    document_type = db.Column(db.String(50), nullable=False, index=True)  # 'annual_report', 'press_release', etc.
    publication_date = db.Column(db.Date, nullable=False, index=True)
    file_url = db.Column(db.String(500))
    summary = db.Column(db.Text)
    keywords = db.Column(db.JSON)  # Searchable keywords
    language = db.Column(db.String(10), default='en')
    file_size = db.Column(db.Integer)  # In bytes
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ResearchDocument {self.title[:50]}>"


class DocumentCategory(db.Model):
    """Document categorization for research organization"""
    __tablename__ = "document_category"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    parent_category_id = db.Column(db.Integer, db.ForeignKey('document_category.id'))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for hierarchical categories
    subcategories = db.relationship('DocumentCategory', backref=db.backref('parent_category', remote_side=[id]), lazy=True)
    
    def __repr__(self):
        return f"<DocumentCategory {self.name}>"


class ListedCompany(db.Model):
    """Ethiopian Stock Exchange listed companies"""
    __tablename__ = "listed_company"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    ticker_symbol = db.Column(db.String(20), nullable=False, unique=True, index=True)
    sector = db.Column(db.String(50), nullable=False, index=True)  # 'Banking', 'Telecommunications', 'Manufacturing'
    industry = db.Column(db.String(100), nullable=False)
    market_cap = db.Column(db.BigInteger)  # In Ethiopian Birr
    shares_outstanding = db.Column(db.BigInteger)
    listing_date = db.Column(db.Date, nullable=False)
    headquarters = db.Column(db.String(100))
    website_url = db.Column(db.String(200))
    logo_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    ceo_name = db.Column(db.String(100))
    employee_count = db.Column(db.Integer)
    fiscal_year_end = db.Column(db.String(10))  # 'June 30', 'December 31'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    financial_metrics = db.relationship('CompanyFinancialMetric', backref='company', lazy=True, cascade='all, delete-orphan')
    financial_statements = db.relationship('FinancialStatement', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ListedCompany {self.name} ({self.ticker_symbol})>"


class CompanyFinancialMetric(db.Model):
    """Financial metrics for listed companies"""
    __tablename__ = "company_financial_metric"
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('listed_company.id'), nullable=False, index=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)  # 'revenue', 'net_income', 'total_assets'
    metric_value = db.Column(db.Numeric(20, 2))  # Monetary values in ETB
    metric_unit = db.Column(db.String(20))  # 'ETB', 'USD', 'percentage', 'ratio'
    reporting_period = db.Column(db.String(20), nullable=False, index=True)  # 'Q1-2024', 'FY-2023'
    fiscal_year = db.Column(db.Integer, nullable=False, index=True)
    quarter = db.Column(db.Integer)  # 1, 2, 3, 4 (null for annual data)
    reporting_date = db.Column(db.Date, nullable=False, index=True)
    currency = db.Column(db.String(10), default='ETB')
    data_source = db.Column(db.String(100))  # 'ESX', 'Company Report', 'NBE'
    is_audited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CompanyFinancialMetric {self.metric_name}: {self.metric_value} ({self.reporting_period})>"


class FinancialStatement(db.Model):
    """Complete financial statements for listed companies"""
    __tablename__ = "financial_statement"
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('listed_company.id'), nullable=False, index=True)
    statement_type = db.Column(db.String(50), nullable=False, index=True)  # 'income_statement', 'balance_sheet', 'cash_flow'
    reporting_period = db.Column(db.String(20), nullable=False, index=True)  # 'Q1-2024', 'FY-2023'
    fiscal_year = db.Column(db.Integer, nullable=False, index=True)
    period_start_date = db.Column(db.Date, nullable=False)
    period_end_date = db.Column(db.Date, nullable=False)
    filing_date = db.Column(db.Date)
    
    # Income Statement Data
    revenue = db.Column(db.Numeric(20, 2))
    cost_of_goods_sold = db.Column(db.Numeric(20, 2))
    gross_profit = db.Column(db.Numeric(20, 2))
    operating_expenses = db.Column(db.Numeric(20, 2))
    operating_income = db.Column(db.Numeric(20, 2))
    interest_expense = db.Column(db.Numeric(20, 2))
    interest_income = db.Column(db.Numeric(20, 2))
    net_income = db.Column(db.Numeric(20, 2))
    earnings_per_share = db.Column(db.Numeric(10, 4))
    
    # Balance Sheet Data
    total_assets = db.Column(db.Numeric(20, 2))
    current_assets = db.Column(db.Numeric(20, 2))
    cash_and_equivalents = db.Column(db.Numeric(20, 2))
    accounts_receivable = db.Column(db.Numeric(20, 2))
    inventory = db.Column(db.Numeric(20, 2))
    total_liabilities = db.Column(db.Numeric(20, 2))
    current_liabilities = db.Column(db.Numeric(20, 2))
    long_term_debt = db.Column(db.Numeric(20, 2))
    shareholders_equity = db.Column(db.Numeric(20, 2))
    
    # Cash Flow Data
    operating_cash_flow = db.Column(db.Numeric(20, 2))
    investing_cash_flow = db.Column(db.Numeric(20, 2))
    financing_cash_flow = db.Column(db.Numeric(20, 2))
    free_cash_flow = db.Column(db.Numeric(20, 2))
    
    # Banking-specific metrics (for Wegagen Bank)
    deposits = db.Column(db.Numeric(20, 2))
    loans_and_advances = db.Column(db.Numeric(20, 2))
    loan_loss_provisions = db.Column(db.Numeric(20, 2))
    net_interest_income = db.Column(db.Numeric(20, 2))
    non_interest_income = db.Column(db.Numeric(20, 2))
    
    # Metadata
    currency = db.Column(db.String(10), default='ETB')
    is_audited = db.Column(db.Boolean, default=False)
    auditor_name = db.Column(db.String(100))
    data_source = db.Column(db.String(100))
    file_url = db.Column(db.String(500))  # Link to original filing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FinancialStatement {self.statement_type} - {self.reporting_period}>"


class DataCitation(db.Model):
    """Data citation tracking for academic and professional use"""
    __tablename__ = "data_citation"
    
    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("economic_data_source.id"))
    citation_format = db.Column(db.String(20))  # 'APA', 'MLA', 'Chicago', 'Custom'
    citation_text = db.Column(db.Text, nullable=False)
    access_date = db.Column(db.Date, nullable=False)
    data_range = db.Column(db.String(100))  # "2020-2024" or "Latest available"
    usage_purpose = db.Column(db.String(100))  # "Academic research", "Policy analysis"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    data_source = db.relationship("EconomicDataSource", backref="citations")
    
    def __repr__(self):
        return f"<DataCitation {self.citation_format}>"


class EconomicForecast(db.Model):
    """Economic forecasting and projections"""
    __tablename__ = "economic_forecast"
    
    id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(100), nullable=False)
    forecast_period = db.Column(db.String(20))  # "2025 Q1", "2025", etc.
    forecast_value = db.Column(db.Float(precision=4))
    confidence_interval_lower = db.Column(db.Float(precision=4))
    confidence_interval_upper = db.Column(db.Float(precision=4))
    forecasting_method = db.Column(db.String(50))  # "Econometric", "Time Series", etc.
    source_organization = db.Column(db.String(100))  # "NBE", "IMF", "World Bank"
    created_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<EconomicForecast {self.indicator_name} {self.forecast_period}>"


class EconomicEvent(db.Model):
    """Economic calendar and significant events"""
    __tablename__ = "economic_event"
    
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # "Policy", "Data Release", "Meeting"
    event_date = db.Column(db.Date, nullable=False, index=True)
    importance = db.Column(db.String(10))  # "High", "Medium", "Low"
    actual_value = db.Column(db.String(100))
    forecast_value = db.Column(db.String(100))
    previous_value = db.Column(db.String(100))
    description = db.Column(db.Text)
    source_organization = db.Column(db.String(100))
    market_impact = db.Column(db.String(20))  # "Positive", "Negative", "Neutral"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<EconomicEvent {self.event_name} {self.event_date}>"


# User Dashboard & Personalization Models

class UserWatchlist(db.Model):
    __tablename__ = 'user_watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='watchlists')
    companies = db.relationship('WatchlistCompany', back_populates='watchlist', cascade='all, delete-orphan')

class WatchlistCompany(db.Model):
    __tablename__ = 'watchlist_companies'
    
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('user_watchlists.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    price_alert_enabled = db.Column(db.Boolean, default=False)
    target_price = db.Column(db.Numeric(15, 2))
    alert_type = db.Column(db.String(20))  # 'above', 'below', 'change'
    
    # Relationships
    watchlist = db.relationship('UserWatchlist', back_populates='companies')
    company = db.relationship('Company')
    
    __table_args__ = (db.UniqueConstraint('watchlist_id', 'company_id'),)

class DownloadHistory(db.Model):
    __tablename__ = 'download_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    download_type = db.Column(db.String(50), nullable=False)  # 'company_data', 'sector_report', 'bulk_export'
    resource_id = db.Column(db.String(100))  # Company ID, sector name, etc.
    resource_name = db.Column(db.String(200))  # Human readable name
    file_format = db.Column(db.String(20))  # 'xlsx', 'csv', 'pdf'
    file_size = db.Column(db.Integer)  # Size in bytes
    parameters = db.Column(db.Text)  # JSON with download parameters
    download_url = db.Column(db.String(500))  # Temporary download URL
    status = db.Column(db.String(20), default='completed')  # 'pending', 'completed', 'failed'
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # When the download link expires
    
    # Relationships
    user = db.relationship('User', backref='download_history')

class UserAlert(db.Model):
    __tablename__ = 'user_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'price', 'financial', 'news', 'research'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    trigger_conditions = db.Column(db.Text)  # JSON with alert conditions
    is_active = db.Column(db.Boolean, default=True)
    frequency = db.Column(db.String(20), default='immediate')  # 'immediate', 'daily', 'weekly'
    delivery_method = db.Column(db.String(20), default='email')  # 'email', 'sms', 'push'
    last_triggered = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='alerts')
    company = db.relationship('Company')

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preference_key = db.Column(db.String(100), nullable=False)
    preference_value = db.Column(db.Text)  # JSON or string value
    category = db.Column(db.String(50))  # 'display', 'notifications', 'data'
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='preferences')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'preference_key'),)

class SavedSearch(db.Model):
    __tablename__ = 'saved_searches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    search_criteria = db.Column(db.Text, nullable=False)  # JSON with search parameters
    alert_enabled = db.Column(db.Boolean, default=False)
    alert_frequency = db.Column(db.String(20), default='weekly')
    last_executed = db.Column(db.DateTime)
    results_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='saved_searches')
