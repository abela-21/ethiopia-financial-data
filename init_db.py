#!/usr/bin/env python3
"""
Ethiopia Capital Market Platform - Database Initialization Script

This script creates the database tables and sets up the initial schema.
Run this script once before starting the application.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_database():
    """Create SQLite database and execute schema"""
    
    # Database file path
    db_path = 'market.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create new database connection
    print(f"Creating new database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # SQL schema from the attached file
    schema_sql = """
    -- Drop existing tables to ensure a clean setup
    DROP TABLE IF EXISTS User;
    DROP TABLE IF EXISTS MacroIndicators;
    DROP TABLE IF EXISTS Financials;
    DROP TABLE IF EXISTS Stock;
    DROP TABLE IF EXISTS Company;
    DROP TABLE IF EXISTS CompanyNews;
    DROP TABLE IF EXISTS CompanyAudit;

    -- Create Company table
    CREATE TABLE Company (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ticker TEXT NOT NULL UNIQUE,
        industry TEXT NOT NULL,
        sector TEXT,
        description TEXT,
        website TEXT,
        established_date DATE,
        shares_outstanding INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES User(id),
        FOREIGN KEY (updated_by) REFERENCES User(id)
    );

    -- Create Stock table
    CREATE TABLE Stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        date DATE NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES Company(id) ON DELETE CASCADE,
        UNIQUE(company_id, date)
    );

    -- Create Financials table
    CREATE TABLE Financials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        period TEXT NOT NULL CHECK (period IN ('Annual', 'Q1', 'Q2', 'Q3', 'Q4')),
        
        -- Income Statement
        revenue REAL,
        cost_of_revenue REAL,
        gross_profit REAL,
        operating_expenses REAL,
        operating_income REAL,
        ebitda REAL,
        interest_expense REAL,
        profit_before_tax REAL,
        net_income REAL,
        
        -- Balance Sheet
        cash_equivalents REAL,
        accounts_receivable REAL,
        inventory REAL,
        total_current_assets REAL,
        fixed_assets REAL,
        total_assets REAL,
        accounts_payable REAL,
        short_term_debt REAL,
        total_current_liabilities REAL,
        long_term_debt REAL,
        total_liabilities REAL,
        total_equity REAL,
        
        -- Cash Flow
        operating_cash_flow REAL,
        investing_cash_flow REAL,
        financing_cash_flow REAL,
        net_cash_flow REAL,
        
        -- Key Ratios
        current_ratio REAL,
        debt_to_equity REAL,
        return_on_equity REAL,
        return_on_assets REAL,
        profit_margin REAL,
        
        -- Metadata
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_by INTEGER,
        
        FOREIGN KEY (company_id) REFERENCES Company(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES User(id),
        FOREIGN KEY (updated_by) REFERENCES User(id),
        UNIQUE(company_id, year, period)
    );

    -- Create MacroIndicators table
    CREATE TABLE MacroIndicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL UNIQUE,
        
        -- Real Sector
        gdp_growth REAL,
        gdp_per_capita REAL,
        inflation_rate REAL,
        food_inflation REAL,
        interest_rate REAL,
        unemployment_rate REAL,
        industrial_production REAL,
        agricultural_production REAL,
        
        -- External Trade & Investment
        exports REAL,
        imports REAL,
        trade_balance REAL,
        current_account_balance REAL,
        fdi_inflow REAL,
        remittances REAL,
        
        -- Foreign Exchange
        fx_reserves REAL,
        etb_usd REAL,
        etb_eur REAL,
        etb_gbp REAL,
        etb_jpy REAL,
        etb_cny REAL,
        
        -- Government Finance
        govt_revenue REAL,
        govt_expenditure REAL,
        budget_deficit REAL,
        govt_debt REAL,
        tax_revenue REAL,
        
        -- Banking & Financial Sector
        total_deposits REAL,
        total_loans REAL,
        npl_ratio REAL,
        loan_to_deposit REAL,
        money_supply_m1 REAL,
        money_supply_m2 REAL,
        private_sector_credit REAL,
        
        -- Key Commodities Prices
        coffee_price REAL,
        gold_price REAL,
        oil_price REAL,
        wheat_price REAL,
        
        -- Metadata
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_by INTEGER,
        
        FOREIGN KEY (created_by) REFERENCES User(id),
        FOREIGN KEY (updated_by) REFERENCES User(id)
    );

    -- Create User table
    CREATE TABLE User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME
    );

    -- Create CompanyNews table
    CREATE TABLE CompanyNews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        source TEXT,
        published_date DATETIME NOT NULL,
        category TEXT CHECK (category IN ('Company', 'Industry', 'Regulatory')),
        url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (company_id) REFERENCES Company(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES User(id)
    );

    -- Create CompanyAudit table
    CREATE TABLE CompanyAudit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        details TEXT, -- JSON data
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES Company(id),
        FOREIGN KEY (user_id) REFERENCES User(id)
    );

    -- Add indexes for performance
    CREATE INDEX idx_stock_company_id ON Stock(company_id);
    CREATE INDEX idx_stock_date ON Stock(date);
    CREATE INDEX idx_stock_company_date ON Stock(company_id, date);
    
    CREATE INDEX idx_financials_company_id ON Financials(company_id);
    CREATE INDEX idx_financials_year ON Financials(year);
    CREATE INDEX idx_financials_company_year ON Financials(company_id, year);
    
    CREATE INDEX idx_macro_date ON MacroIndicators(date);
    
    CREATE INDEX idx_company_ticker ON Company(ticker);
    CREATE INDEX idx_company_industry ON Company(industry);
    CREATE INDEX idx_company_sector ON Company(sector);
    
    CREATE INDEX idx_user_username ON User(username);
    CREATE INDEX idx_user_email ON User(email);
    
    CREATE INDEX idx_news_company_id ON CompanyNews(company_id);
    CREATE INDEX idx_news_published_date ON CompanyNews(published_date);
    CREATE INDEX idx_news_category ON CompanyNews(category);
    
    CREATE INDEX idx_audit_company_id ON CompanyAudit(company_id);
    CREATE INDEX idx_audit_user_id ON CompanyAudit(user_id);
    CREATE INDEX idx_audit_timestamp ON CompanyAudit(timestamp);
    """
    
    try:
        # Execute schema
        cursor.executescript(schema_sql)
        conn.commit()
        print("✅ Database schema created successfully!")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
            
        # Show database file size
        file_size = os.path.getsize(db_path)
        print(f"💾 Database file size: {file_size:,} bytes")
        
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        return False
    finally:
        conn.close()
    
    return True

def verify_database():
    """Verify the database was created correctly"""
    db_path = 'market.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if all required tables exist
        required_tables = [
            'Company', 'Stock', 'Financials', 'MacroIndicators', 
            'User', 'CompanyNews', 'CompanyAudit'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = set(required_tables) - set(existing_tables)
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Check table structures
        for table in required_tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            print(f"📋 Table '{table}' has {len(columns)} columns")
        
        conn.close()
        print("✅ Database verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main function"""
    print("🇪🇹 Ethiopia Capital Market Platform - Database Initialization")
    print("=" * 60)
    
    # Create database
    if not create_database():
        print("❌ Database creation failed!")
        sys.exit(1)
    
    print()
    
    # Verify database
    if not verify_database():
        print("❌ Database verification failed!")
        sys.exit(1)
    
    print()
    print("🎉 Database initialization completed successfully!")
    print()
    print("Next steps:")
    print("1. Run 'python seed_data.py' to populate with sample data")
    print("2. Run 'python main.py' to start the application")
    print("3. Open http://localhost:5000 in your browser")

if __name__ == '__main__':
    main()
