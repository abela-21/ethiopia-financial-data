#!/usr/bin/env python3
"""
Ethiopia Capital Market Platform - Database Seeding Script

This script populates the database with sample data for development and testing.
Run this script after initializing the database with init_db.py.
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_db_connection():
    """Get database connection"""
    db_path = 'market.db'
    if not os.path.exists(db_path):
        print("❌ Database file not found! Please run init_db.py first.")
        sys.exit(1)
    return sqlite3.connect(db_path)

def seed_users():
    """Create sample users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("👥 Seeding users...")
    
    users = [
        {
            'username': 'admin',
            'email': 'admin@ethiopiacapitalmarket.com',
            'password': 'admin123',
            'role': 'admin',
            'is_active': True
        },
        {
            'username': 'analyst',
            'email': 'analyst@ethiopiacapitalmarket.com', 
            'password': 'analyst123',
            'role': 'user',
            'is_active': True
        },
        {
            'username': 'researcher',
            'email': 'researcher@ethiopiacapitalmarket.com',
            'password': 'researcher123', 
            'role': 'user',
            'is_active': True
        }
    ]
    
    for user in users:
        password_hash = generate_password_hash(user['password'])
        cursor.execute("""
            INSERT INTO User (username, email, password_hash, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user['username'],
            user['email'], 
            password_hash,
            user['role'],
            user['is_active'],
            datetime.utcnow()
        ))
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created {len(users)} users")

def seed_companies():
    """Create sample Ethiopian companies"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🏢 Seeding companies...")
    
    # Get admin user ID for created_by field
    cursor.execute("SELECT id FROM User WHERE username = 'admin'")
    admin_user_id = cursor.fetchone()[0]
    
    companies = [
        {
            'name': 'Commercial Bank of Ethiopia',
            'ticker': 'CBE',
            'industry': 'Banking',
            'sector': 'Financial Services',
            'description': 'The largest commercial bank in Ethiopia, providing comprehensive banking services nationwide.',
            'website': 'https://www.combanketh.et',
            'established_date': date(1963, 1, 1),
            'shares_outstanding': 50000000
        },
        {
            'name': 'Ethiopian Airlines Group',
            'ticker': 'ETH',
            'industry': 'Airlines',
            'sector': 'Transportation',
            'description': 'The flag carrier of Ethiopia and one of the largest airlines in Africa.',
            'website': 'https://www.ethiopianairlines.com',
            'established_date': date(1945, 12, 21),
            'shares_outstanding': 75000000
        },
        {
            'name': 'Awash Bank S.C.',
            'ticker': 'AWSH',
            'industry': 'Banking',
            'sector': 'Financial Services', 
            'description': 'One of the leading private banks in Ethiopia offering modern banking services.',
            'website': 'https://www.awashbank.com',
            'established_date': date(1994, 2, 10),
            'shares_outstanding': 30000000
        },
        {
            'name': 'Dashen Bank S.C.',
            'ticker': 'DASH',
            'industry': 'Banking',
            'sector': 'Financial Services',
            'description': 'A premier private bank in Ethiopia known for innovation in banking technology.',
            'website': 'https://www.dashenbanksc.com',
            'established_date': date(1995, 9, 20),
            'shares_outstanding': 35000000
        },
        {
            'name': 'East African Holding S.C.',
            'ticker': 'EAHS',
            'industry': 'Investment',
            'sector': 'Financial Services',
            'description': 'A diversified investment holding company with interests across multiple sectors.',
            'website': 'https://www.eastafricanholding.com',
            'established_date': date(2007, 5, 15),
            'shares_outstanding': 20000000
        },
        {
            'name': 'Ethiopian Shipping & Logistics Services Enterprise',
            'ticker': 'ESLSE',
            'industry': 'Logistics',
            'sector': 'Transportation',
            'description': 'The national maritime transport and logistics service provider of Ethiopia.',
            'website': 'https://www.eslse.gov.et',
            'established_date': date(1964, 3, 12),
            'shares_outstanding': 40000000
        },
        {
            'name': 'Habesha Brewery S.C.',
            'ticker': 'HABS',
            'industry': 'Beverages',
            'sector': 'Consumer Goods',
            'description': 'A leading brewery in Ethiopia producing popular beer and beverage brands.',
            'website': 'https://www.habeshabrewery.com',
            'established_date': date(2009, 8, 3),
            'shares_outstanding': 15000000
        },
        {
            'name': 'Nyala Insurance S.C.',
            'ticker': 'NYAL',
            'industry': 'Insurance',
            'sector': 'Financial Services',
            'description': 'One of the largest insurance companies in Ethiopia offering comprehensive coverage.',
            'website': 'https://www.nyalainsurance.com',
            'established_date': date(1995, 12, 8),
            'shares_outstanding': 25000000
        },
        {
            'name': 'Ethiopian Telecommunications Corporation',
            'ticker': 'ETC',
            'industry': 'Telecommunications',
            'sector': 'Technology',
            'description': 'The national telecommunications service provider of Ethiopia.',
            'website': 'https://www.ethiotelecom.et',
            'established_date': date(1894, 1, 1),
            'shares_outstanding': 100000000
        },
        {
            'name': 'Guna Trading House P.L.C.',
            'ticker': 'GUNA',
            'industry': 'Trading',
            'sector': 'Consumer Goods',
            'description': 'A major trading and distribution company serving the Ethiopian market.',
            'website': 'https://www.guna.com.et',
            'established_date': date(2001, 6, 20),
            'shares_outstanding': 18000000
        }
    ]
    
    for company in companies:
        cursor.execute("""
            INSERT INTO Company (
                name, ticker, industry, sector, description, website, 
                established_date, shares_outstanding, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company['name'],
            company['ticker'],
            company['industry'],
            company['sector'],
            company['description'],
            company['website'],
            company['established_date'],
            company['shares_outstanding'],
            datetime.utcnow(),
            admin_user_id
        ))
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created {len(companies)} companies")

def seed_stock_data():
    """Generate stock price data for companies"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("📈 Seeding stock data...")
    
    # Get all companies
    cursor.execute("SELECT id, ticker FROM Company")
    companies = cursor.fetchall()
    
    # Base prices for different companies (in ETB)
    base_prices = {
        'CBE': 850.0,
        'ETH': 1200.0,
        'AWSH': 650.0,
        'DASH': 720.0,
        'EAHS': 450.0,
        'ESLSE': 320.0,
        'HABS': 280.0,
        'NYAL': 380.0,
        'ETC': 950.0,
        'GUNA': 180.0
    }
    
    # Generate data for the last 90 days
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    stock_records = []
    
    for company_id, ticker in companies:
        base_price = base_prices.get(ticker, 500.0)
        current_price = base_price
        
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends (Ethiopian market trades Mon-Fri)
            if current_date.weekday() < 5:
                # Generate daily price movement (-3% to +3%)
                daily_change = random.uniform(-0.03, 0.03)
                
                # Add some trend and volatility
                trend = random.uniform(-0.001, 0.001)
                volatility = random.uniform(0.5, 1.5)
                
                open_price = current_price
                close_price = current_price * (1 + daily_change + trend) * volatility
                
                # Ensure reasonable price bounds
                close_price = max(close_price, base_price * 0.5)
                close_price = min(close_price, base_price * 2.0)
                
                # Generate high and low
                high_price = max(open_price, close_price) * random.uniform(1.0, 1.05)
                low_price = min(open_price, close_price) * random.uniform(0.95, 1.0)
                
                # Generate volume (varies by company size)
                base_volume = base_prices.get(ticker, 500) * 100
                volume = int(base_volume * random.uniform(0.5, 2.0))
                
                stock_records.append((
                    company_id,
                    current_date,
                    round(open_price, 2),
                    round(high_price, 2),
                    round(low_price, 2),
                    round(close_price, 2),
                    volume,
                    datetime.utcnow()
                ))
                
                current_price = close_price
            
            current_date += timedelta(days=1)
    
    # Insert stock data
    cursor.executemany("""
        INSERT INTO Stock (
            company_id, date, open, high, low, close, volume, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, stock_records)
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created {len(stock_records)} stock records")

def seed_financial_data():
    """Generate financial data for companies"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("💰 Seeding financial data...")
    
    # Get admin user ID
    cursor.execute("SELECT id FROM User WHERE username = 'admin'")
    admin_user_id = cursor.fetchone()[0]
    
    # Get all companies
    cursor.execute("SELECT id, ticker, industry FROM Company")
    companies = cursor.fetchall()
    
    financial_records = []
    
    # Generate data for 2022-2024
    for year in range(2022, 2025):
        for company_id, ticker, industry in companies:
            # Base financial metrics by industry
            if industry == 'Banking':
                base_revenue = random.uniform(5000000000, 15000000000)  # 5-15 billion ETB
                profit_margin = random.uniform(0.15, 0.25)
            elif industry == 'Airlines':
                base_revenue = random.uniform(20000000000, 35000000000)  # 20-35 billion ETB
                profit_margin = random.uniform(0.05, 0.12)
            elif industry == 'Telecommunications':
                base_revenue = random.uniform(15000000000, 25000000000)  # 15-25 billion ETB
                profit_margin = random.uniform(0.20, 0.30)
            elif industry == 'Insurance':
                base_revenue = random.uniform(2000000000, 5000000000)  # 2-5 billion ETB
                profit_margin = random.uniform(0.08, 0.15)
            else:
                base_revenue = random.uniform(1000000000, 8000000000)  # 1-8 billion ETB
                profit_margin = random.uniform(0.05, 0.15)
            
            # Add year-over-year growth
            growth_rate = random.uniform(0.05, 0.20)  # 5-20% annual growth
            revenue = base_revenue * ((1 + growth_rate) ** (year - 2022))
            
            # Calculate other financial metrics
            cost_of_revenue = revenue * random.uniform(0.40, 0.70)
            gross_profit = revenue - cost_of_revenue
            operating_expenses = gross_profit * random.uniform(0.30, 0.60)
            operating_income = gross_profit - operating_expenses
            ebitda = operating_income * random.uniform(1.1, 1.3)
            net_income = revenue * profit_margin
            
            # Balance sheet items
            total_assets = revenue * random.uniform(2.0, 8.0)
            total_liabilities = total_assets * random.uniform(0.40, 0.70)
            total_equity = total_assets - total_liabilities
            
            # Calculate ratios
            current_ratio = random.uniform(1.0, 2.5)
            debt_to_equity = total_liabilities / total_equity if total_equity > 0 else 0
            return_on_equity = net_income / total_equity if total_equity > 0 else 0
            return_on_assets = net_income / total_assets if total_assets > 0 else 0
            profit_margin_calc = net_income / revenue if revenue > 0 else 0
            
            financial_records.append((
                company_id,
                year,
                'Annual',
                revenue,
                cost_of_revenue,
                gross_profit,
                operating_expenses,
                operating_income,
                ebitda,
                net_income,
                total_assets,
                total_liabilities, 
                total_equity,
                current_ratio,
                debt_to_equity,
                return_on_equity,
                return_on_assets,
                profit_margin_calc,
                datetime.utcnow(),
                admin_user_id
            ))
    
    # Insert financial data
    cursor.executemany("""
        INSERT INTO Financials (
            company_id, year, period, revenue, cost_of_revenue, gross_profit,
            operating_expenses, operating_income, ebitda, net_income,
            total_assets, total_liabilities, total_equity,
            current_ratio, debt_to_equity, return_on_equity, 
            return_on_assets, profit_margin, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, financial_records)
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created {len(financial_records)} financial records")

def seed_macro_indicators():
    """Generate macroeconomic indicators for Ethiopia"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🌍 Seeding macroeconomic indicators...")
    
    # Get admin user ID
    cursor.execute("SELECT id FROM User WHERE username = 'admin'")
    admin_user_id = cursor.fetchone()[0]
    
    # Generate monthly data for the last 24 months
    end_date = date.today().replace(day=1)  # First day of current month
    start_date = end_date - timedelta(days=730)  # Approximately 24 months
    
    macro_records = []
    
    # Base values for Ethiopian economy
    base_gdp_growth = 8.5
    base_inflation = 15.0
    base_interest_rate = 13.0
    base_usd_rate = 55.0
    base_eur_rate = 60.0
    base_gbp_rate = 68.0
    base_jpy_rate = 0.40
    
    current_date = start_date
    while current_date <= end_date:
        # Add some randomness and trends to economic indicators
        gdp_growth = base_gdp_growth + random.uniform(-1.5, 1.5)
        inflation_rate = max(0, base_inflation + random.uniform(-3.0, 5.0))
        interest_rate = max(0, base_interest_rate + random.uniform(-2.0, 3.0))
        unemployment_rate = random.uniform(18.0, 25.0)
        
        # Exchange rates with some volatility
        etb_usd = base_usd_rate * random.uniform(0.95, 1.15)
        etb_eur = base_eur_rate * random.uniform(0.95, 1.15)
        etb_gbp = base_gbp_rate * random.uniform(0.95, 1.15)
        etb_jpy = base_jpy_rate * random.uniform(0.95, 1.15)
        
        # Other economic indicators
        fx_reserves = random.uniform(3000000000, 5000000000)  # 3-5 billion USD
        trade_balance = random.uniform(-2000000000, -500000000)  # Deficit
        current_account_balance = random.uniform(-3000000000, -1000000000)  # Deficit
        
        # Banking sector
        total_deposits = random.uniform(1500000000000, 2500000000000)  # 1.5-2.5 trillion ETB
        total_loans = random.uniform(1200000000000, 2000000000000)  # 1.2-2.0 trillion ETB
        npl_ratio = random.uniform(2.5, 8.0)  # 2.5-8% NPL ratio
        
        macro_records.append((
            current_date,
            gdp_growth,
            random.uniform(800, 1200),  # GDP per capita USD
            inflation_rate,
            interest_rate,
            unemployment_rate,
            etb_usd,
            etb_eur,
            etb_gbp,
            etb_jpy,
            fx_reserves,
            trade_balance,
            current_account_balance,
            total_deposits,
            total_loans,
            npl_ratio,
            datetime.utcnow(),
            admin_user_id
        ))
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Insert macro data
    cursor.executemany("""
        INSERT INTO MacroIndicators (
            date, gdp_growth, gdp_per_capita, inflation_rate, interest_rate,
            unemployment_rate, etb_usd, etb_eur, etb_gbp, etb_jpy,
            fx_reserves, trade_balance, current_account_balance,
            total_deposits, total_loans, npl_ratio, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, macro_records)
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created {len(macro_records)} macro indicator records")

def seed_company_news():
    """Generate sample company news"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("📰 Seeding company news...")
    
    # Get admin user ID
    cursor.execute("SELECT id FROM User WHERE username = 'admin'")
    admin_user_id = cursor.fetchone()[0]
    
    # Get all companies
    cursor.execute("SELECT id, name, ticker FROM Company")
    companies = cursor.fetchall()
    
    news_templates = [
        {
            'title': '{company} Announces Strong Q{quarter} Financial Results',
            'content': '{company} reported strong financial performance for Q{quarter}, with revenue growth and improved profitability across key business segments.',
            'category': 'Company'
        },
        {
            'title': '{company} Expands Operations in Regional Markets',
            'content': '{company} announced expansion plans to strengthen its presence in regional markets, focusing on digital transformation and customer service improvements.',
            'category': 'Company'
        },
        {
            'title': 'Regulatory Update Affects {industry} Sector',
            'content': 'New regulatory guidelines have been announced that will impact companies in the {industry} sector, including {company}.',
            'category': 'Regulatory'
        },
        {
            'title': '{company} Launches New Digital Banking Services',
            'content': '{company} has unveiled new digital banking platforms to enhance customer experience and compete in the evolving financial services landscape.',
            'category': 'Company'
        },
        {
            'title': 'Market Analysis: {industry} Sector Shows Promise',
            'content': 'Industry analysts are optimistic about the {industry} sector, with companies like {company} leading innovation and growth initiatives.',
            'category': 'Industry'
        }
    ]
    
    news_records = []
    
    # Generate news for each company
    for company_id, company_name, ticker in companies:
        # Get company industry
        cursor.execute("SELECT industry FROM Company WHERE id = ?", (company_id,))
        industry = cursor.fetchone()[0]
        
        # Generate 3-5 news items per company
        num_news = random.randint(3, 5)
        
        for i in range(num_news):
            template = random.choice(news_templates)
            
            # Generate content based on template
            title = template['title'].format(
                company=company_name,
                quarter=random.randint(1, 4),
                industry=industry
            )
            
            content = template['content'].format(
                company=company_name,
                quarter=random.randint(1, 4),
                industry=industry
            )
            
            # Random date in the last 6 months
            days_ago = random.randint(1, 180)
            published_date = datetime.now() - timedelta(days=days_ago)
            
            news_records.append((
                company_id,
                title,
                content,
                'Ethiopian Business Journal',
                published_date,
                template['category'],
                f'https://www.ethiopianbusiness.com/news/{ticker.lower()}-{i+1}',
                datetime.utcnow(),
                admin_user_id
            ))
    
    # Insert news data
    cursor.executemany("""
        INSERT INTO CompanyNews (
            company_id, title, content, source, published_date, 
            category, url, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, news_records)
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created {len(news_records)} news records")

def verify_seeded_data():
    """Verify that data was seeded correctly"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n📊 Verifying seeded data...")
    
    # Count records in each table
    tables = ['User', 'Company', 'Stock', 'Financials', 'MacroIndicators', 'CompanyNews']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table}: {count:,} records")
    
    # Show date ranges for time-series data
    cursor.execute("SELECT MIN(date), MAX(date) FROM Stock")
    stock_dates = cursor.fetchone()
    if stock_dates[0]:
        print(f"   Stock data range: {stock_dates[0]} to {stock_dates[1]}")
    
    cursor.execute("SELECT MIN(date), MAX(date) FROM MacroIndicators")
    macro_dates = cursor.fetchone()
    if macro_dates[0]:
        print(f"   Macro data range: {macro_dates[0]} to {macro_dates[1]}")
    
    # Show financial data years
    cursor.execute("SELECT MIN(year), MAX(year) FROM Financials")
    financial_years = cursor.fetchone()
    if financial_years[0]:
        print(f"   Financial data years: {financial_years[0]} to {financial_years[1]}")
    
    conn.close()
    print("   ✅ Data verification completed")

def main():
    """Main function to seed all data"""
    print("🇪🇹 Ethiopia Capital Market Platform - Database Seeding")
    print("=" * 60)
    
    try:
        # Seed data in order (respecting foreign key constraints)
        seed_users()
        seed_companies()
        seed_stock_data()
        seed_financial_data()
        seed_macro_indicators()
        seed_company_news()
        
        # Verify the seeded data
        verify_seeded_data()
        
        print("\n🎉 Database seeding completed successfully!")
        print("\nYou can now:")
        print("1. Run 'python main.py' to start the application")
        print("2. Login with username 'admin' and password 'admin123'")
        print("3. Explore the market data at http://localhost:5000")
        
    except Exception as e:
        print(f"\n❌ Error during database seeding: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
