# System Architecture

## Project Structure

```
ethiopia-capital-market/
├── api/                    # API endpoints and routes
│   ├── __init__.py
│   ├── company_routes.py   # Company data endpoints
│   ├── download_routes.py  # Data export endpoints
│   ├── financial_routes.py # Financial data endpoints
│   ├── macro_routes.py     # Macroeconomic endpoints
│   ├── market_routes.py    # Market summary endpoints
│   ├── news_routes.py      # News data endpoints
│   └── stock_routes.py     # Stock price endpoints
├── Data/                   # Data files and loading scripts
│   ├── companies.csv       # Company master data
│   ├── financials.csv      # Financial statements
│   ├── macro.csv           # Macroeconomic indicators
│   ├── stocks.csv          # Stock price data
│   └── load_data.py        # Data import script
├── static/                 # Frontend assets
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── downloads.js    # Download functionality
├── templates/              # HTML templates
│   ├── auth/               # Authentication pages
│   ├── components/         # Reusable components
│   ├── base.html           # Base template
│   ├── companies.html      # Company listing
│   ├── company_detail.html # Company details
│   ├── downloads.html      # Data export page
│   ├── index.html          # Dashboard
│   ├── macro.html          # Macro indicators
│   └── market.html         # Market overview
├── utils/                  # Utility modules
│   ├── cache.py            # Caching configuration
│   ├── errors.py           # Error handling
│   ├── limiter.py          # Rate limiting
│   └── validators.py       # Data validation
├── app.py                  # Flask application factory
├── main.py                 # Application entry point
├── models.py               # Database models
└── routes.py               # Web page routes
```

## Database Schema

### Core Tables

**Company**: Public company information
- id, name, ticker, industry, sector
- description, website, established_date
- shares_outstanding, audit fields

**Financial**: Financial statements and ratios
- company_id, year, period (Annual/Q1-Q4)
- Income statement: revenue, expenses, net_income
- Balance sheet: assets, liabilities, equity
- Cash flow: operating, investing, financing
- Ratios: current_ratio, debt_to_equity, ROE, ROA

**Stock**: Daily price and volume data
- company_id, date, open, high, low, close, volume
- Unique constraint on (company_id, date)

**MacroIndicators**: Economic indicators
- date, economic growth metrics
- Inflation and interest rates
- Trade and external balance
- Exchange rates (ETB vs major currencies)
- Government finance and banking

**CompanyNews**: News articles
- company_id, title, content, source
- published_date, category, url

**User**: Authentication and audit
- username, email, password_hash, role
- created_at, last_login, is_active

## API Design

### RESTful Endpoints

All APIs follow consistent patterns:
- GET for data retrieval
- Query parameters for filtering
- Pagination support
- Rate limiting (30/minute)
- Response caching (5 minutes)
- Error handling with status codes

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

### Download Endpoints

Support both CSV and Excel formats:
- Variable selection for customized exports
- Date range filtering
- Company-specific filtering
- Streaming responses for large datasets

## Frontend Architecture

### Technology Stack
- Bootstrap 5 for responsive design
- Chart.js for data visualization
- Vanilla JavaScript for interactions
- Flask-rendered HTML templates

### Color Scheme
Professional palette optimized for financial data:
- Midnight Green (#075056): Primary branding
- Ivory Cream (#FDF6E3): Background
- Gunmetal (#233038): Text and borders
- Orange Pantone (#FF5B04): Highlights and CTAs
- Sand Yellow (#F4D47C): Warnings and accents
- Light Silver (#D3DBDD): Secondary elements

### Component Structure
- Base template with navigation
- Reusable card components
- Consistent form styling
- Mobile-responsive layouts

## Security Features

### Authentication
- Flask-Login session management
- Password hashing with Werkzeug
- Role-based access control

### API Protection
- Rate limiting per endpoint
- Input validation and sanitization
- SQL injection prevention via ORM
- CORS configuration

### Data Protection
- Environment variable configuration
- Database connection pooling
- Secure session management

## Performance Optimization

### Caching Strategy
- Flask-Caching with configurable backend
- Query result caching (5 minutes)
- Static asset caching
- Database connection pooling

### Database Optimization
- Proper indexing on foreign keys
- Compound indexes for common queries
- Query optimization with SQLAlchemy
- Connection pooling and recycling

### Frontend Performance
- Minified CSS and JavaScript
- Responsive image loading
- Efficient DOM manipulation
- Progressive enhancement

## Deployment Architecture

### Replit Deployment
- Gunicorn WSGI server
- PostgreSQL database
- Automatic TLS/SSL
- Health check monitoring
- Environment variable management

### Scalability Considerations
- Stateless application design
- Database connection pooling
- Caching layer separation
- Load balancer compatibility