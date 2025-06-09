-- Drop existing tables to ensure a clean setup (optional)
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS MacroIndicators;
DROP TABLE IF EXISTS Financials;
DROP TABLE IF EXISTS Stock;
DROP TABLE IF EXISTS Company;

-- Create Company table
CREATE TABLE Company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    industry TEXT NOT NULL,
    description TEXT
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
    FOREIGN KEY (company_id) REFERENCES Company(id)
);

-- Create Financials table
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

-- Create MacroIndicators table
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

-- Create User table (optional, for login functionality)
CREATE TABLE User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT
);

-- Add indexes for performance
CREATE INDEX idx_stock_company_id ON Stock(company_id);
CREATE INDEX idx_stock_date ON Stock(date);
CREATE INDEX idx_financials_company_id ON Financials(company_id);
CREATE INDEX idx_financials_year ON Financials(year);
CREATE INDEX idx_macro_date ON MacroIndicators(date);