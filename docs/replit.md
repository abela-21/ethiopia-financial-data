# Ethiopia Economic Data Platform

## Overview

The Ethiopia Economic Data Platform is a comprehensive web application built with Flask that provides financial, economic, and business intelligence for Ethiopia's emerging capital market. The platform serves as a centralized hub for banking sector analysis, economic research, company data, and market intelligence, targeting investors, analysts, researchers, and financial professionals.

## System Architecture

### Backend Architecture
- **Framework**: Flask 3.1.1 with Python 3.11
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0.41 ORM
- **Authentication**: Flask-Login with session management and JWT tokens for API access
- **API Design**: RESTful endpoints with JSON responses
- **Caching**: Flask-Caching for performance optimization
- **Rate Limiting**: Flask-Limiter to prevent abuse
- **Migration**: Flask-Migrate for database schema management

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **CSS Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Charts**: Chart.js for data visualizations
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

### Database Design
- **User Management**: User accounts with role-based access (admin/user)
- **Company Data**: Corporate profiles, financial statements, stock prices
- **Economic Data**: Macro indicators, banking sector metrics
- **Research Documents**: Economic publications and reports
- **Financial Records**: Income statements, balance sheets, cash flows

## Key Components

### 1. Authentication & Authorization
- User registration and login system
- Role-based access control (admin/user)
- Session management with secure cookies
- JWT tokens for API authentication
- Password hashing with Werkzeug security

### 2. Data Management System
- Admin panel for data entry and management
- CRUD operations for all data types
- Bulk import functionality for CSV/Excel files
- Data validation and error handling
- External API integrations for real-time data

### 3. User Interface Components
- Dashboard with personalized metrics
- Company listings with search and filtering
- Economic indicators with interactive charts
- Banking sector analysis tools
- Research document library
- Data export capabilities

### 4. API Layer
- RESTful endpoints for data access
- JSON responses with error handling
- Rate limiting and caching
- Admin-only endpoints for data management
- Public endpoints for general data access

## Data Flow

### 1. Data Input Flow
- Manual data entry through admin interface
- Bulk imports via CSV/Excel uploads
- External API integrations (World Bank, etc.)
- Real-time data feeds for market updates

### 2. Data Processing Flow
- Input validation and sanitization
- Database storage with relationship mapping
- Caching frequently accessed data
- Background processing for large datasets

### 3. Data Output Flow
- Web interface rendering with Jinja2 templates
- API responses in JSON format
- Data exports in CSV/Excel formats
- Real-time updates via AJAX calls

## External Dependencies

### Core Dependencies
- **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-JWT-Extended
- **Database**: PostgreSQL with psycopg2-binary driver
- **Security**: Werkzeug for password hashing, Flask-CORS for cross-origin requests
- **Data Processing**: Pandas for data manipulation, OpenPyXL for Excel handling
- **Web Scraping**: Trafilatura for content extraction
- **Authentication**: OAuth support via Flask-Dance

### Frontend Dependencies
- **Bootstrap 5**: CSS framework and components
- **Chart.js**: Data visualization library
- **Font Awesome**: Icon library
- **jQuery**: JavaScript utilities (implied by Bootstrap usage)

### Production Dependencies
- **Gunicorn**: WSGI server for production deployment
- **Flask-Caching**: Performance optimization
- **Flask-Limiter**: Rate limiting protection

## Deployment Strategy

### Development Environment
- Local SQLite database for development
- Flask development server with debug mode
- Hot reload for rapid development

### Production Environment
- **Server**: Gunicorn WSGI server
- **Database**: PostgreSQL 16
- **Deployment**: Replit autoscale deployment
- **Port Configuration**: Internal port 5000, external port 80
- **Process Management**: Replit workflows for automated deployment

### Configuration Management
- Environment variables for sensitive data
- Separate configurations for development/production
- Database URL configuration via environment
- Secret key management for security

### Security Considerations
- HTTPS enforcement in production
- Secure session cookies
- Password hashing with salt
- SQL injection prevention via SQLAlchemy ORM
- CORS policy configuration
- Rate limiting to prevent abuse

## Changelog
- June 14, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.