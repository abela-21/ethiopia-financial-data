# Ethiopia Economic Data Platform

## Overview

The Ethiopia Economic Data Platform is a comprehensive Flask-based web application designed to serve as a centralized hub for Ethiopian economic and financial data. The platform provides banking sector analysis, economic indicators, financial data management, and research document access for investors, analysts, and researchers interested in Ethiopia's emerging capital market.

## System Architecture

### Backend Architecture
- **Framework**: Flask with application factory pattern
- **Database**: SQLAlchemy ORM with PostgreSQL (production) / SQLite (development)
- **Authentication**: Flask-Login with session management and JWT tokens
- **Caching**: Flask-Caching for performance optimization
- **Rate Limiting**: Flask-Limiter for API protection
- **Migration**: Flask-Migrate for database schema management

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5
- **CSS Framework**: Bootstrap 5 with custom styling
- **JavaScript Libraries**: Chart.js for data visualization
- **Icons**: Font Awesome 6.4.0
- **Responsive Design**: Mobile-first approach

### Deployment Strategy
- **WSGI Server**: Gunicorn for production deployment
- **Platform**: Replit with auto-scaling deployment target
- **Port Configuration**: Application runs on port 5000
- **Environment**: Python 3.11 with PostgreSQL 16

## Key Components

### Models (models.py)
- **User**: Authentication and user management with role-based access
- **Company**: Listed companies with ticker symbols and industry classification
- **Additional Models**: Banking institutions, financial statements, economic indicators (referenced but not fully visible)

### Authentication System (auth_routes.py)
- User registration with email validation
- Password hashing using Werkzeug security
- Session-based authentication with Flask-Login
- Username generation from email addresses
- Form validation and error handling

### Data Management Routes (routes.py)
- Admin-only data management interface
- Company listings with search and filtering
- Financial data visualization
- Economic indicators dashboard
- Export functionality for data downloads

### Configuration Management
- Environment variable-based configuration
- Separate settings for development and production
- Database connection pooling and optimization
- JWT token expiration settings

## Data Flow

1. **User Authentication**: Users register/login through secure forms with password hashing
2. **Data Access**: Authenticated users access dashboard and financial data
3. **Admin Functions**: Admin users manage data through dedicated interfaces
4. **Data Export**: Users can download financial data in various formats
5. **Real-time Updates**: Economic indicators and market data refresh capabilities

## External Dependencies

### Python Packages
- **Core**: Flask, SQLAlchemy, Werkzeug
- **Authentication**: Flask-Login, Flask-JWT-Extended, PyJWT
- **Data Processing**: Pandas, OpenPyXL, XlsxWriter
- **Web Enhancement**: Flask-CORS, Flask-Caching, Flask-Limiter
- **Database**: psycopg2-binary for PostgreSQL connectivity
- **HTTP Requests**: requests, oauthlib for external API integration
- **Content Processing**: trafilatura for research document processing

### Frontend Dependencies
- **Bootstrap 5**: UI framework and components
- **Chart.js**: Data visualization and charting
- **Font Awesome**: Icon library
- **Custom CSS**: Platform-specific styling

### External Services
- **World Bank API**: Economic indicator data
- **UN Statistics**: Development indicators
- **African Development Bank**: Regional economic data

## Deployment Strategy

The application uses Gunicorn WSGI server with auto-scaling deployment on Replit platform. The deployment configuration includes:

- **Development**: Local SQLite database with debug mode
- **Production**: PostgreSQL database with connection pooling
- **Scaling**: Auto-scale deployment target for handling variable load
- **Security**: Environment-based secrets and JWT token management

## Changelog

- June 14, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.