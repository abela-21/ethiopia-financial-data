import re
from typing import List, Dict, Any

def validate_company_data(data: Dict[str, Any]) -> List[str]:
    """Validate company data and return list of errors"""
    errors = []
    
    # Required fields
    required_fields = ['name', 'ticker', 'industry']
    for field in required_fields:
        if not data.get(field) or not str(data[field]).strip():
            errors.append(f"{field} is required")
    
    # Ticker validation
    ticker = data.get('ticker', '')
    if ticker:
        if len(ticker) > 10:
            errors.append("Ticker must be 10 characters or less")
        if not re.match(r'^[A-Z0-9]+$', ticker.upper()):
            errors.append("Ticker must contain only letters and numbers")
    
    # Name validation
    name = data.get('name', '')
    if name and len(name) > 100:
        errors.append("Company name must be 100 characters or less")
    
    # Website validation
    website = data.get('website', '')
    if website:
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(website):
            errors.append("Invalid website URL format")
    
    # Shares outstanding validation
    shares = data.get('shares_outstanding')
    if shares is not None:
        try:
            shares_int = int(shares)
            if shares_int < 0:
                errors.append("Shares outstanding must be a positive number")
        except (ValueError, TypeError):
            errors.append("Shares outstanding must be a valid number")
    
    return errors

def validate_financial_data(data: Dict[str, Any]) -> List[str]:
    """Validate financial data and return list of errors"""
    errors = []
    
    # Required fields
    required_fields = ['company_id', 'year', 'period']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
    
    # Year validation
    year = data.get('year')
    if year:
        try:
            year_int = int(year)
            if year_int < 1900 or year_int > 2100:
                errors.append("Year must be between 1900 and 2100")
        except (ValueError, TypeError):
            errors.append("Year must be a valid number")
    
    # Period validation
    period = data.get('period', '')
    valid_periods = ['Annual', 'Q1', 'Q2', 'Q3', 'Q4']
    if period and period not in valid_periods:
        errors.append(f"Period must be one of: {', '.join(valid_periods)}")
    
    # Validate numeric fields
    numeric_fields = [
        'revenue', 'cost_of_revenue', 'gross_profit', 'operating_expenses',
        'operating_income', 'ebitda', 'net_income', 'total_assets',
        'total_liabilities', 'total_equity'
    ]
    
    for field in numeric_fields:
        value = data.get(field)
        if value is not None:
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(f"{field} must be a valid number")
    
    return errors

def validate_stock_data(data: Dict[str, Any]) -> List[str]:
    """Validate stock data and return list of errors"""
    errors = []
    
    # Required fields
    required_fields = ['company_id', 'date', 'open', 'close', 'high', 'low']
    for field in required_fields:
        if data.get(field) is None:
            errors.append(f"{field} is required")
    
    # Price validations
    price_fields = ['open', 'close', 'high', 'low']
    prices = {}
    
    for field in price_fields:
        value = data.get(field)
        if value is not None:
            try:
                price = float(value)
                if price < 0:
                    errors.append(f"{field} price must be positive")
                prices[field] = price
            except (ValueError, TypeError):
                errors.append(f"{field} must be a valid number")
    
    # Price relationship validations
    if len(prices) == 4:  # All prices are valid
        if prices['high'] < max(prices['open'], prices['close']):
            errors.append("High price must be >= max(open, close)")
        if prices['low'] > min(prices['open'], prices['close']):
            errors.append("Low price must be <= min(open, close)")
    
    # Volume validation
    volume = data.get('volume')
    if volume is not None:
        try:
            volume_int = int(volume)
            if volume_int < 0:
                errors.append("Volume must be non-negative")
        except (ValueError, TypeError):
            errors.append("Volume must be a valid integer")
    
    # Date validation
    date_value = data.get('date')
    if date_value:
        try:
            from datetime import datetime
            datetime.strptime(str(date_value), '%Y-%m-%d')
        except ValueError:
            errors.append("Date must be in YYYY-MM-DD format")
    
    return errors
