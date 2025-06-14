# Ethiopia Economic Data Platform

A comprehensive financial data platform specializing in Ethiopia's capital market, providing authenticated economic insights and banking sector analytics.

## Overview

This platform serves researchers, consultants, analysts, portfolio managers, and investors with authentic Ethiopian economic data sourced from international authorities including the World Bank, UN Statistics, and National Bank of Ethiopia.

## Features

### Core Functionality
- **Economic Indicators Dashboard** - Real-time display of GDP growth, inflation, unemployment, and exchange rates
- **Banking Sector Analytics** - Performance metrics for 18 Ethiopian banks
- **Research Document Library** - Comprehensive collection of economic research and reports
- **Data Export Tools** - Multi-format export (CSV, Excel, JSON, PDF)
- **Admin Panel** - Complete data management and user administration

### Data Sources
- **World Bank Open Data API** - 171+ authentic Ethiopian economic indicators
- **UN Statistics Division** - Sustainable Development Goals metrics
- **National Bank of Ethiopia** - Monetary policy and banking statistics
- **Ethiopian Statistics Service** - National accounts and labor statistics

### User Roles
- **Public Users** - Access to basic economic indicators and research
- **Authenticated Users** - Advanced analytics and data export capabilities
- **Administrators** - Full data management and platform administration

## Technology Stack

### Backend
- **Flask** - Web application framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching layer
- **Gunicorn** - WSGI server

### Frontend
- **Chart.js** - Data visualization
- **Bootstrap 5** - Responsive UI framework
- **JavaScript ES6+** - Interactive functionality

### Infrastructure
- **Docker** - Containerization
- **GitHub Actions** - CI/CD pipeline
- **Replit** - Development and deployment platform

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for caching)

### Installation

1. Clone the repository
```bash
git clone https://github.com/your-username/ethiopia-economic-platform.git
cd ethiopia-economic-platform
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database
```bash
python scripts/create_admin.py
python scripts/data_migration.py
```

5. Run the application
```bash
python main.py
```

The application will be available at `http://localhost:5000`

### Default Admin Credentials
- **Email**: admin@ethiopia-economic.com
- **Password**: EthiopiaAdmin2024!

## Project Structure

```
ethiopia-economic-platform/
├── api/                    # API route modules
│   ├── economic_routes.py  # Economic indicators endpoints
│   ├── banking_routes.py   # Banking sector APIs
│   └── ...
├── data/                   # Data files and templates
│   ├── Data/              # External data integration
│   └── ...
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # System architecture
│   ├── DEPLOYMENT.md       # Deployment guide
│   └── ...
├── scripts/               # Utility scripts
│   ├── data_migration.py   # Database setup
│   ├── create_admin.py     # Admin user creation
│   └── ...
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── templates/         # HTML templates
├── templates/             # Jinja2 templates
│   ├── admin/             # Admin panel templates
│   ├── auth/              # Authentication pages
│   └── ...
├── tests/                 # Test suite
├── utils/                 # Utility modules
├── app.py                 # Flask application factory
├── models.py              # Database models
├── routes.py              # Main route definitions
└── main.py                # Application entry point
```

## API Documentation

### Economic Indicators
```
GET /api/v1/economic/indicators
GET /api/v1/economic/indicators/trends
POST /api/v1/economic/indicators
```

### Banking Data
```
GET /api/v1/banking/banks
GET /api/v1/banking/banks/{id}/performance
GET /api/v1/banking/sector-overview
```

### Data Export
```
POST /api/v1/export/economic/{format}
POST /api/v1/export/banking/{format}
```

## Data Management

### Bulk Import
The platform supports bulk import of data via CSV/Excel files:
- Economic indicators
- Banking financial statements
- Company information
- Research documents

### External API Integration
Automated data refresh from external sources:
- Daily updates from World Bank API
- Weekly synchronization with UN Statistics
- Monthly banking sector data updates

## Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test category
python -m pytest tests/test_economic_indicators.py
```

### Code Quality
```bash
# Linting
flake8 .

# Type checking
mypy .

# Security scanning
bandit -r .
```

### Database Migrations
```bash
# Generate migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

## Deployment

### Production Deployment
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

### Environment Configuration
```bash
# Production settings
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/0
SECRET_KEY=your-secret-key
```

## Contributing

Please read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Data Integrity

This platform maintains strict data integrity standards:
- All economic data sourced from authenticated international organizations
- Source attribution for every data point
- Audit trails for all data modifications
- Regular validation against authoritative sources

## Security

- JWT-based authentication
- Role-based access control
- API rate limiting
- Input validation and sanitization
- Regular security audits

## Performance

- Redis caching for frequently accessed data
- Database query optimization
- Lazy loading for large datasets
- CDN integration for static assets

## Monitoring

- Application performance monitoring
- Data freshness alerts
- External API status monitoring
- User activity analytics

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@ethiopia-economic.com
- Documentation: [docs/](docs/)

## Acknowledgments

- World Bank Open Data initiative
- UN Statistics Division
- National Bank of Ethiopia
- Ethiopian Statistics Service
- Open source community contributors

---

**Ethiopia Economic Data Platform** - Empowering decision-making with authentic economic intelligence.