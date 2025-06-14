# Ethiopia Economic Intelligence Platform

## Overview

This is a comprehensive financial data platform for Ethiopia's capital market, providing authentic banking sector data, economic indicators, and downloadable financial metrics. The platform serves as a central hub for Ethiopian economic intelligence, featuring data on 18 licensed banks, listed companies, macroeconomic indicators, and research documents.

## System Architecture

### Frontend Architecture
- **Framework**: Server-side rendered HTML templates using Jinja2
- **CSS Framework**: Bootstrap 5 for responsive design
- **JavaScript**: Vanilla JavaScript with Chart.js for data visualization
- **UI Components**: Modular template system with reusable components
- **Responsive Design**: Mobile-first approach with responsive navigation

### Backend Architecture
- **Framework**: Flask web framework with application factory pattern
- **ORM**: SQLAlchemy for database operations
- **Authentication**: Flask-Login with role-based access control (user/admin)
- **API Design**: RESTful endpoints for data access and management
- **Caching**: Flask-Caching for performance optimization
- **Rate Limiting**: Flask-Limiter for API protection

### Database Architecture
- **Primary Database**: PostgreSQL for production, SQLite for development
- **Schema Design**: Normalized relational schema with proper foreign key relationships
- **Key Tables**: Users, Companies, Banks, MacroIndicators, FinancialStatements, ResearchDocuments
- **Data Integrity**: Referential integrity constraints and proper indexing

## Key Components

### Data Management System
- **Banking Sector**: 18 Ethiopian banks with financial metrics, NBE ratings, and branch networks
- **Listed Companies**: 5 ESX-listed companies with comprehensive financial data
- **Economic Indicators**: 35+ macroeconomic variables including GDP, inflation, exchange rates
- **Research Documents**: Academic and institutional research papers with download tracking

### Authentication & Authorization
- **User Management**: Registration, login, and profile management
- **Role-Based Access**: Admin and user roles with different permission levels
- **Session Management**: Secure session handling with Flask-Login
- **Admin Panel**: Comprehensive data management interface for administrators

### Export & Download System
- **Multi-Format Support**: Excel (.xlsx), CSV, JSON, and PDF exports
- **Bulk Downloads**: Select multiple companies and data categories
- **Real-Time Generation**: Dynamic report generation with proper formatting
- **Download Tracking**: User activity logging and analytics

### API Layer
- **Public APIs**: Company data, stock prices, economic indicators
- **Admin APIs**: Data management, user administration, bulk operations
- **External Integration**: World Bank, IMF, and NBE data integration capabilities
- **Error Handling**: Comprehensive error responses and logging

## Data Flow

### Data Input
1. **Manual Entry**: Admin interface for direct data entry and editing
2. **Bulk Import**: CSV/Excel template-based import system
3. **External APIs**: Integration with international data sources
4. **Database Migration**: Automated population scripts for initial setup

### Data Processing
1. **Validation**: Input validation and data integrity checks
2. **Transformation**: Data normalization and formatting
3. **Storage**: Optimized database storage with proper indexing
4. **Caching**: Performance optimization through strategic caching

### Data Output
1. **Web Interface**: Real-time data display with filtering and search
2. **API Endpoints**: Programmatic access to all data
3. **Export System**: Multi-format download capabilities
4. **Reporting**: Automated report generation and analytics

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and extensions (SQLAlchemy, Login, Migrate)
- **Database**: PostgreSQL with psycopg2-binary driver
- **Security**: Werkzeug for password hashing, JWT for API authentication
- **Data Processing**: Pandas for data manipulation, xlsxwriter for Excel generation
- **Web Server**: Gunicorn for production deployment

### Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **Chart.js**: JavaScript charting library for data visualization

### Development Dependencies
- **Flask-Migrate**: Database schema migrations
- **Flask-CORS**: Cross-origin resource sharing
- **Python 3.11+**: Runtime environment

## Deployment Strategy

### Replit Deployment (Primary)
- **Platform**: Replit Deployments with autoscale configuration
- **Runtime**: Python 3.11 with PostgreSQL 16
- **Process**: Gunicorn WSGI server on port 5000
- **Environment**: Production-ready with TLS/SSL certificates
- **Health Checks**: Automated health monitoring and restart capabilities

### Configuration Management
- **Environment Variables**: DATABASE_URL, SESSION_SECRET, JWT_SECRET_KEY
- **Database**: PostgreSQL connection with connection pooling
- **Static Assets**: Served directly through Flask in production
- **Logging**: Structured logging with multiple output handlers

### Scalability Considerations
- **Database**: Connection pooling and query optimization
- **Caching**: Redis-compatible caching layer for high-traffic scenarios
- **Rate Limiting**: API rate limiting to prevent abuse
- **Load Balancing**: Ready for horizontal scaling with load balancers

## Changelog

- June 14, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.