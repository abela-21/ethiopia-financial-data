# Ethiopia Economic Data Platform

## Overview

The Ethiopia Economic Data Platform is a comprehensive Flask-based web application that provides financial, economic, and banking sector data for Ethiopia. It serves as a centralized platform for researchers, analysts, portfolio managers, and investors to access authentic Ethiopian economic data from international sources including the World Bank, UN Statistics, and National Bank of Ethiopia.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL for production (configurable to SQLite for development)
- **Authentication**: Flask-Login with JWT support
- **Caching**: Redis for performance optimization
- **API Rate Limiting**: Flask-Limiter for request throttling
- **Session Management**: Flask sessions with CSRF protection

### Frontend Architecture
- **UI Framework**: Bootstrap 5 for responsive design
- **Data Visualization**: Chart.js for economic charts and graphs
- **Icons**: Font Awesome 6.4.0
- **JavaScript**: ES6+ for interactive functionality
- **Styling**: Custom CSS with Ethiopian brand colors

### Database Schema
The application uses a relational database with key entities:
- **Users**: Authentication and user management
- **Companies**: Listed companies on Ethiopian Securities Exchange
- **Banks**: Ethiopian banking sector institutions (18 licensed banks)
- **Economic Indicators**: Macroeconomic data from external sources
- **Financial Statements**: Company financial data
- **Research Documents**: Economic research and publications

## Key Components

### Authentication System
- Role-based access control (public, authenticated, admin)
- User registration and login functionality
- Admin panel for user management
- Session-based authentication with Flask-Login
- Password hashing with Werkzeug security

### Data Management System
- Admin interface for managing economic data
- CRUD operations for companies, banks, and indicators
- Bulk import functionality for CSV/Excel files
- Data export capabilities (CSV, Excel, JSON, PDF)
- Real-time data refresh from external APIs

### External API Integration
- World Bank Open Data API (171+ Ethiopian indicators)
- UN Statistics Division integration
- National Bank of Ethiopia data feeds
- African Development Bank statistics
- Automated data synchronization

### User Interface Components
- Dashboard for authenticated users
- Banking sector analytics
- Economic indicators visualization
- Research document library
- Advanced search and filtering
- Mobile-responsive design

## Data Flow

### Data Input
1. **External APIs**: Automated fetching from World Bank, UN Statistics
2. **Admin Interface**: Manual data entry through web forms
3. **Bulk Import**: CSV/Excel file uploads with validation
4. **Real-time Refresh**: Scheduled updates from external sources

### Data Processing
1. **Validation**: Input sanitization and business rule validation
2. **Storage**: PostgreSQL database with optimized indexing
3. **Caching**: Redis caching for frequently accessed data
4. **Aggregation**: Real-time calculation of derived metrics

### Data Output
1. **Web Interface**: Interactive charts and tables
2. **API Endpoints**: RESTful API for data access
3. **Export Formats**: CSV, Excel, JSON, PDF downloads
4. **Real-time Updates**: WebSocket connections for live data

## External Dependencies

### Core Dependencies
- **Flask 3.1.1**: Web application framework
- **SQLAlchemy 2.0.41**: Database ORM
- **PostgreSQL**: Primary database (psycopg2-binary driver)
- **Redis**: Caching and session storage
- **Gunicorn**: WSGI server for production

### Data Processing
- **Pandas 2.3.0**: Data manipulation and analysis
- **XlsxWriter 3.2.3**: Excel file generation
- **OpenPyXL 3.1.5**: Excel file reading
- **Requests 2.32.4**: HTTP client for external APIs

### Authentication & Security
- **Flask-Login**: User session management
- **Flask-JWT-Extended**: JWT token handling
- **Werkzeug**: Password hashing and security utilities
- **Flask-CORS**: Cross-origin resource sharing

### UI & Visualization
- **Bootstrap 5**: Frontend framework
- **Chart.js**: Data visualization library
- **Font Awesome**: Icon library

## Deployment Strategy

### Development Environment
- **Replit**: Primary development platform
- **SQLite**: Development database option
- **Flask debug mode**: For development debugging
- **Hot reload**: Automatic server restart on code changes

### Production Environment
- **Docker**: Containerized deployment
- **PostgreSQL**: Production database
- **Redis**: Production caching
- **Nginx**: Reverse proxy and static file serving
- **Gunicorn**: Multi-worker WSGI server

### Infrastructure
- **Auto-scaling**: Replit autoscale deployment target
- **Health Checks**: Docker health check endpoints
- **SSL/TLS**: HTTPS encryption support
- **CDN**: Static asset delivery optimization

### Monitoring & Logging
- **Application Logs**: Structured logging with Python logging
- **Error Tracking**: Exception handling and reporting
- **Performance Monitoring**: Response time and throughput metrics
- **Database Monitoring**: Query performance and connection pooling

## Changelog

- June 14, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.