"""
Populate external data sources and sample data for testing
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, ExternalDataSource, DataIntegration, RealTimeQuote, CurrencyRate
from datetime import datetime, timedelta
import random

def populate_external_data_sources():
    """Populate external data sources configuration"""
    print("Populating external data sources...")
    
    sources = [
        {
            'name': 'Ethiopian Securities Exchange',
            'source_type': 'api',
            'description': 'Official Ethiopian Securities Exchange API for real-time market data',
            'endpoint_url': 'https://api.ethiopianexchange.com/v1',
            'api_key_required': True,
            'update_frequency': 'real-time',
            'status': 'healthy'
        },
        {
            'name': 'National Bank of Ethiopia',
            'source_type': 'api',
            'description': 'Central bank API for currency rates and monetary policy data',
            'endpoint_url': 'https://api.nbe.gov.et/v1',
            'api_key_required': True,
            'update_frequency': 'daily',
            'status': 'healthy'
        },
        {
            'name': 'Ethiopian Investment Commission',
            'source_type': 'api',
            'description': 'Investment data and economic indicators from EIC',
            'endpoint_url': 'https://api.investethiopia.gov.et/v1',
            'api_key_required': False,
            'update_frequency': 'weekly',
            'status': 'healthy'
        },
        {
            'name': 'World Bank Ethiopia Data',
            'source_type': 'api',
            'description': 'World Bank macroeconomic indicators for Ethiopia',
            'endpoint_url': 'https://api.worldbank.org/v2/country/ETH',
            'api_key_required': False,
            'update_frequency': 'monthly',
            'status': 'healthy'
        },
        {
            'name': 'IMF Ethiopia Statistics',
            'source_type': 'api',
            'description': 'International Monetary Fund economic statistics',
            'endpoint_url': 'https://api.imf.org/v1/country/ETH',
            'api_key_required': True,
            'update_frequency': 'quarterly',
            'status': 'maintenance'
        }
    ]
    
    for source_data in sources:
        source = ExternalDataSource(
            name=source_data['name'],
            source_type=source_data['source_type'],
            description=source_data['description'],
            endpoint_url=source_data['endpoint_url'],
            api_key_required=source_data['api_key_required'],
            update_frequency=source_data['update_frequency'],
            status=source_data['status'],
            last_updated=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            created_at=datetime.utcnow()
        )
        db.session.add(source)
    
    db.session.commit()
    print(f"Added {len(sources)} external data sources")

def populate_data_integrations():
    """Populate sample data integration logs"""
    print("Populating data integration logs...")
    
    sources = ExternalDataSource.query.all()
    if not sources:
        print("No external data sources found. Please run populate_external_data_sources first.")
        return
    
    integration_types = ['market_data', 'currency_rates', 'economic_indicators', 'company_financials']
    statuses = ['completed', 'completed', 'completed', 'failed', 'running']
    
    integrations = []
    for _ in range(50):
        source = random.choice(sources)
        status = random.choice(statuses)
        
        integration = DataIntegration(
            source_id=source.id,
            data_type=random.choice(integration_types),
            status=status,
            records_processed=random.randint(10, 1000) if status == 'completed' else None,
            error_message='Connection timeout' if status == 'failed' else None,
            last_sync=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
            duration_seconds=random.randint(5, 300) if status == 'completed' else None
        )
        integrations.append(integration)
    
    db.session.add_all(integrations)
    db.session.commit()
    print(f"Added {len(integrations)} data integration records")

def populate_real_time_quotes():
    """Populate sample real-time market quotes"""
    print("Populating real-time quotes...")
    
    # Ethiopian listed companies symbols
    symbols = [
        'CBE', 'ELIC', 'UIC', 'NIC', 'OIC', 'GIC', 'LIC', 'AIC',
        'AAIT', 'ABB', 'EEU', 'BGI', 'MOHA', 'DAN', 'SABA'
    ]
    
    quotes = []
    for symbol in symbols:
        # Generate quotes for last 24 hours
        for i in range(24):
            base_price = random.uniform(50, 500)
            change = random.uniform(-10, 10)
            change_percent = (change / base_price) * 100
            
            quote = RealTimeQuote(
                symbol=symbol,
                price=round(base_price + change, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=random.randint(1000, 50000),
                timestamp=datetime.utcnow() - timedelta(hours=i),
                market_status='open' if 9 <= (datetime.utcnow() - timedelta(hours=i)).hour <= 16 else 'closed',
                source_id=1  # Ethiopian Securities Exchange
            )
            quotes.append(quote)
    
    db.session.add_all(quotes)
    db.session.commit()
    print(f"Added {len(quotes)} real-time quotes")

def populate_currency_rates():
    """Populate currency exchange rates"""
    print("Populating currency rates...")
    
    # Currency pairs with ETB
    currency_pairs = [
        ('ETB', 'USD'), ('ETB', 'EUR'), ('ETB', 'GBP'), ('ETB', 'JPY'),
        ('USD', 'ETB'), ('EUR', 'ETB'), ('GBP', 'ETB'), ('JPY', 'ETB')
    ]
    
    # Base rates (approximate)
    base_rates = {
        ('ETB', 'USD'): 0.018,
        ('ETB', 'EUR'): 0.016,
        ('ETB', 'GBP'): 0.014,
        ('ETB', 'JPY'): 2.7,
        ('USD', 'ETB'): 55.0,
        ('EUR', 'ETB'): 62.0,
        ('GBP', 'ETB'): 70.0,
        ('JPY', 'ETB'): 0.37
    }
    
    rates = []
    # Generate rates for last 30 days
    for i in range(30):
        date = datetime.utcnow().date() - timedelta(days=i)
        
        for pair in currency_pairs:
            base_rate = base_rates[pair]
            # Add some daily variation
            variation = random.uniform(-0.05, 0.05)
            rate = base_rate * (1 + variation)
            
            currency_rate = CurrencyRate(
                base_currency=pair[0],
                target_currency=pair[1],
                rate=round(rate, 6),
                date=date,
                source='National Bank of Ethiopia',
                created_at=datetime.utcnow()
            )
            rates.append(currency_rate)
    
    db.session.add_all(rates)
    db.session.commit()
    print(f"Added {len(rates)} currency rates")

def main():
    """Main function to populate all external data"""
    app = create_app()
    
    with app.app_context():
        print("Starting external data population...")
        
        # Clear existing data
        print("Clearing existing external data...")
        DataIntegration.query.delete()
        RealTimeQuote.query.delete()
        CurrencyRate.query.delete()
        ExternalDataSource.query.delete()
        db.session.commit()
        
        # Populate new data
        populate_external_data_sources()
        populate_data_integrations()
        populate_real_time_quotes()
        populate_currency_rates()
        
        print("External data population completed successfully!")

if __name__ == '__main__':
    main()