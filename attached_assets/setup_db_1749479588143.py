import sqlite3

conn = sqlite3.connect('market.db')
cursor = conn.cursor()

# SQL script
sql_script = '''
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS MacroIndicators;
DROP TABLE IF EXISTS Financials;
DROP TABLE IF EXISTS Stock;
DROP TABLE IF EXISTS Company;

CREATE TABLE Company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    industry TEXT NOT NULL,
    description TEXT
);

CREATE TABLE Stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    FOREIGN KEY (company_id) REFERENCES Company(id)
);

CREATE TABLE Financials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    revenue REAL NOT NULL,
    net_profit REAL NOT NULL,
    ebitda REAL NOT NULL,
    total_assets REAL NOT NULL,
    total_liabilities REAL NOT NULL,
    equity REAL NOT NULL,
    debt_to_equity REAL NOT NULL,
    FOREIGN KEY (company_id) REFERENCES Company(id)
);

CREATE TABLE MacroIndicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    gdp_growth REAL NOT NULL,
    inflation_rate REAL NOT NULL,
    interest_rate REAL NOT NULL,
    etb_usd REAL NOT NULL,
    etb_eur REAL NOT NULL,
    etb_gbp REAL NOT NULL,
    etb_jpy REAL NOT NULL
);

CREATE TABLE User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT
);

CREATE INDEX idx_stock_company_id ON Stock(company_id);
CREATE INDEX idx_stock_date ON Stock(date);
CREATE INDEX idx_financials_company_id ON Financials(company_id);
CREATE INDEX idx_financials_year ON Financials(year);
CREATE INDEX idx_macro_date ON MacroIndicators(date);
'''

cursor.executescript(sql_script)
conn.commit()
conn.close()
print("Database schema created successfully.")