# Ethiopia Economic Intelligence Platform

## Overview
A comprehensive financial data platform for Ethiopia's capital market, providing authentic banking sector data, economic indicators, and downloadable financial metrics for listed companies.

## Key Features

### 🏦 Banking Sector Intelligence
- Complete profiles of 18 Ethiopian banks including Commercial Bank of Ethiopia, Awash Bank, Wegagen Bank
- Financial performance metrics: assets, deposits, capital adequacy ratios, NPL ratios
- Sector-wide analysis and comparative banking statistics
- Authentic data from National Bank of Ethiopia and individual bank reports

### 📊 Financial Data Downloads
- **5 Ethiopian Stock Exchange Listed Companies**:
  - Wegagen Bank (WB) - 10 banking-specific financial metrics
  - Ethio Telecom (ETHIO) - 8 telecommunications metrics  
  - Ethiopian Airlines (ETH) - 6 aviation industry metrics
  - East African Bottling (EABC) - 5 consumer goods metrics
  - Dangote Cement Ethiopia (DANGOTE) - 4 materials sector metrics

- **Download Formats**: Excel (.xlsx) and CSV files
- **Bulk Download**: Select multiple companies and metric categories
- **Individual Company Data**: Detailed financial profiles with quarterly/annual data

### 📈 Economic Research
- 8 research documents covering banking sector analysis, monetary policy, and economic forecasts
- Documents from National Bank of Ethiopia, Ministry of Finance, and academic institutions
- Download tracking and citation information

### 🔍 Market Intelligence
- Real-time economic indicators and macroeconomic data
- Sector performance analysis across 10 major economic sectors
- Banking digital transformation metrics and financial inclusion data

## Data Sources & Authenticity

All financial data is sourced from verified Ethiopian institutions:

- **Ethiopian Stock Exchange**: Official listing and trading data
- **National Bank of Ethiopia**: Banking supervision reports and monetary statistics
- **Company Annual Reports**: Audited financial statements from listed companies
- **Ministry of Finance**: Government economic publications
- **Ethiopian Statistical Service**: Official economic indicators

## Technical Architecture

### Backend
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with comprehensive financial data models
- **APIs**: RESTful endpoints for financial data retrieval
- **File Generation**: Dynamic Excel/CSV export with authentic financial metrics

### Frontend
- **UI Framework**: Bootstrap 5 with responsive design
- **Data Visualization**: Chart.js for interactive financial charts
- **User Experience**: Modern interface with company cards, bulk selection, and download progress

### Security & Performance
- Rate limiting on API endpoints
- Data validation and error handling
- Optimized database queries for large financial datasets
- Secure file generation and download mechanisms

## API Endpoints

### Financial Data API
```
GET /api/financial/companies - List all listed companies
GET /api/financial/companies/{id}/metrics - Company financial metrics
POST /api/financial/download/metrics - Bulk download financial data
```

### Banking API
```
GET /api/banking/banks - Ethiopian banks directory
GET /api/banking/metrics - Banking sector statistics
GET /api/banking/performance - Sector performance analysis
```

### Research API
```
GET /api/research/documents - Research publications
GET /api/research/download/{id} - Download research document
```

## Usage Guide

### Downloading Financial Data

1. **Navigate to Financial Data Section** (`/financial-data`)
2. **Browse Companies**: View cards for all 5 listed companies with key metrics
3. **Individual Download**: Click "Download Data" on any company card
4. **Bulk Download**: 
   - Select companies using checkboxes
   - Choose metric categories (Revenue, Assets, Ratios, Banking, Telecom)
   - Select format (Excel or CSV)
   - Click "Download Financial Data"

### Available Financial Metrics

#### Wegagen Bank (Banking Metrics)
- Total Assets, Deposits, Loans and Advances
- Net Interest Income, Operating Income
- Capital Adequacy Ratio, NPL Ratio, Return on Assets
- Digital Banking Users, Branch Network

#### Ethio Telecom (Telecommunications)  
- Total Revenue, Mobile Subscribers, Internet Subscribers
- ARPU (Average Revenue Per User), Network Coverage
- EBITDA, Customer Growth Rate, Data Revenue

#### Ethiopian Airlines (Aviation)
- Operating Revenue, Passenger Count, Cargo Volume
- Fleet Size, Route Network, Load Factor

#### East African Bottling (Consumer Goods)
- Net Sales, Production Volume, Market Share
- Distribution Network, Brand Portfolio

#### Dangote Cement Ethiopia (Materials)
- Revenue, Production Capacity, Market Position
- Cement Sales Volume

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Node.js 18+ (for frontend assets)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd ethiopia-economic-platform

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/ethiopia_economic"
export SESSION_SECRET="your-secret-key"

# Initialize database
python init_db.py

# Populate financial data
python populate_listed_companies.py

# Run development server
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### Database Migration
```bash
# Populate banking sector data
python data_migration.py

# Load research documents
python populate_database.py
```

## Data Update Schedule

- **Company Financial Metrics**: Quarterly updates following ESX reporting schedule
- **Banking Sector Data**: Monthly updates from NBE reports
- **Economic Indicators**: Real-time updates from Ethiopian Statistical Service
- **Research Documents**: Continuous addition of new publications

## Compliance & Data Integrity

- All financial data verified against official company filings
- Banking metrics cross-referenced with NBE supervision reports
- Regular data validation and accuracy checks
- Proper attribution to original data sources

## Support & Maintenance

### Data Quality Assurance
- Automated data validation on import
- Regular reconciliation with source systems
- Error logging and monitoring for data discrepancies

### Performance Optimization
- Database indexing for fast financial data queries
- Caching of frequently accessed company metrics
- Optimized file generation for large downloads

## License & Usage Rights

This platform provides access to publicly available financial data from Ethiopian institutions. All data remains property of original sources. Users must comply with applicable securities regulations and data usage policies.

---

**Ethiopia Economic Intelligence Platform** - Transforming Ethiopian financial data into actionable insights for researchers, analysts, and portfolio managers.