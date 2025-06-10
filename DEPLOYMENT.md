# Deployment Guide

## Replit Deployment

This application is configured for deployment on Replit Deployments.

### Prerequisites
- PostgreSQL database configured
- Environment variables set:
  - `DATABASE_URL`
  - `SESSION_SECRET`

### Configuration Files

1. **`.replit`** - Replit configuration (already configured)
2. **`main.py`** - Entry point for the application
3. **`pyproject.toml`** - Python dependencies

### Deployment Steps

1. Click the "Deploy" button in Replit
2. Configure environment variables if not already set
3. Replit Deployments will:
   - Build the application
   - Install dependencies
   - Start the Gunicorn server
   - Provide TLS/SSL certificates
   - Set up health checks

### Environment Variables Required

```bash
DATABASE_URL=postgresql://user:password@host:port/database
SESSION_SECRET=your-secure-random-secret-key
```

### Health Check

The application includes health check endpoints:
- `GET /` - Returns 200 OK when healthy
- `GET /api/companies?per_page=1` - Database connectivity check

## Alternative Deployment Options

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

### Traditional Server Deployment

1. Install Python 3.11+
2. Install PostgreSQL
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables
5. Initialize database: `python -c "from app import app, db; app.app_context().push(); db.create_all()"`
6. Load data: `python Data/load_data.py`
7. Run: `gunicorn --bind 0.0.0.0:5000 --workers 4 main:app`

### Production Considerations

1. **Database**: Use managed PostgreSQL service
2. **Static Files**: Serve via CDN or reverse proxy
3. **SSL/TLS**: Enable HTTPS
4. **Monitoring**: Set up application monitoring
5. **Backup**: Regular database backups
6. **Scaling**: Use multiple workers or containers