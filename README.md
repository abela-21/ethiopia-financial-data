# Ethiopia Capital Market Platform

A comprehensive financial data platform for Ethiopia's capital market, delivering intuitive macroeconomic insights through advanced data visualization.

## Features

- **Company Database**: Complete profiles of Ethiopian public companies with financial metrics
- **Financial Data**: Revenue, assets, profitability ratios, and cash flow statements
- **Stock Prices**: Historical price data with OHLCV information
- **Macroeconomic Indicators**: GDP, inflation, exchange rates, trade data, and government finance
- **News Integration**: Company and market news with categorization
- **Data Downloads**: CSV and Excel exports with variable selection
- **Responsive Design**: Optimized for desktop and mobile devices

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with comprehensive data models
- **Frontend**: Bootstrap 5, Chart.js for visualization
- **API**: RESTful endpoints with rate limiting and caching
- **Deployment**: Gunicorn WSGI server

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ethiopia-capital-market
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost/dbname"
export SESSION_SECRET="your-secret-key"
```

4. Initialize the database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. Load sample data:
```bash
python Data/load_data.py
```

6. Run the application:
```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

## API Endpoints

### Companies
- `GET /api/companies` - List companies with filtering
- `GET /api/companies/{id}` - Get company details

### Financial Data
- `GET /api/financials/{company_id}` - Company financial records
- `GET /api/financials/{company_id}/latest` - Latest financials

### Stock Data
- `GET /api/stocks/{company_id}` - Stock price history
- `GET /api/stocks/{company_id}/latest` - Current stock price

### Macroeconomic Data
- `GET /api/macro` - Macro indicators with filtering
- `GET /api/macro/latest` - Current indicators

### Downloads
- `GET /api/download/companies` - Export company data
- `GET /api/download/financials` - Export financial data
- `GET /api/download/stocks` - Export stock data
- `GET /api/download/macro_indicators` - Export macro data

## Data Models

- **Company**: Name, ticker, industry, sector, description
- **Financial**: Income statement, balance sheet, cash flow, ratios
- **Stock**: OHLCV price data with volume
- **MacroIndicators**: Economic growth, inflation, trade, government finance
- **CompanyNews**: News articles with categorization
- **User**: Authentication and audit trails

## Color Scheme

- Midnight Green: #075056
- Ivory Cream: #FDF6E3
- Gunmetal: #233038
- Orange Pantone: #FF5B04
- Sand Yellow: #F4D47C
- Light Silver: #D3DBDD

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.