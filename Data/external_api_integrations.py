#!/usr/bin/env python3
"""
External API Integration System
Integrates with international data sources: World Bank, IMF, UNCTAD, WTO
for Ethiopia Economic Data Platform
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExternalDataIntegrator:
    """Handles integration with international economic data APIs"""
    
    def __init__(self, database_url=None):
        """Initialize with database connection"""
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url) if self.database_url else None
        
        # API Base URLs
        self.apis = {
            'world_bank': 'http://api.worldbank.org/v2/country/ET/indicator',
            'imf': 'http://dataservices.imf.org/REST/SDMX_JSON.svc',
            'unctad': 'https://unctadstat-api.unctad.org/api/v1',
            'wto': 'https://api.wto.org/timeseries/v1'
        }
        
        # Ethiopia country codes
        self.country_codes = {
            'world_bank': 'ET',
            'imf': 'ET',
            'iso3': 'ETH',
            'iso2': 'ET'
        }
    
    def get_world_bank_data(self, indicator_code, start_year=2015, end_year=2024):
        """Fetch data from World Bank API for Ethiopia"""
        try:
            url = f"{self.apis['world_bank']}/{indicator_code}"
            params = {
                'format': 'json',
                'date': f"{start_year}:{end_year}",
                'per_page': 1000
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if len(data) > 1 and data[1]:
                records = []
                for item in data[1]:
                    if item['value'] is not None:
                        records.append({
                            'date': f"{item['date']}-12-31",
                            'indicator_code': indicator_code,
                            'indicator_name': item['indicator']['value'],
                            'value': float(item['value']),
                            'country': item['country']['value'],
                            'source': 'World Bank'
                        })
                return records
            
        except Exception as e:
            logger.error(f"Error fetching World Bank data for {indicator_code}: {str(e)}")
        
        return []
    
    def get_imf_data(self, dataset_code, indicator_code, start_year=2015):
        """Fetch data from IMF API for Ethiopia"""
        try:
            # IMF uses different API structure
            url = f"{self.apis['imf']}/CompactData/{dataset_code}/A.ET.{indicator_code}"
            params = {
                'startPeriod': start_year,
                'endPeriod': datetime.now().year,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                records = []
                if 'CompactData' in data and 'DataSet' in data['CompactData']:
                    series = data['CompactData']['DataSet']['Series']
                    if isinstance(series, dict):
                        series = [series]
                    
                    for serie in series:
                        if 'Obs' in serie:
                            obs_data = serie['Obs']
                            if isinstance(obs_data, dict):
                                obs_data = [obs_data]
                            
                            for obs in obs_data:
                                if '@OBS_VALUE' in obs:
                                    records.append({
                                        'date': f"{obs['@TIME_PERIOD']}-12-31",
                                        'indicator_code': indicator_code,
                                        'indicator_name': f"IMF {dataset_code} - {indicator_code}",
                                        'value': float(obs['@OBS_VALUE']),
                                        'country': 'Ethiopia',
                                        'source': 'IMF'
                                    })
                
                return records
            
        except Exception as e:
            logger.error(f"Error fetching IMF data for {indicator_code}: {str(e)}")
        
        return []
    
    def get_unctad_data(self, indicator_code, start_year=2015):
        """Fetch data from UNCTAD API for Ethiopia"""
        try:
            # UNCTAD API endpoint
            url = f"{self.apis['unctad']}/data"
            params = {
                'countries': 'ETH',
                'indicators': indicator_code,
                'years': f"{start_year}-{datetime.now().year}",
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                records = []
                if 'data' in data:
                    for item in data['data']:
                        if 'value' in item and item['value'] is not None:
                            records.append({
                                'date': f"{item['year']}-12-31",
                                'indicator_code': indicator_code,
                                'indicator_name': item.get('indicator_name', f"UNCTAD {indicator_code}"),
                                'value': float(item['value']),
                                'country': 'Ethiopia',
                                'source': 'UNCTAD'
                            })
                
                return records
                
        except Exception as e:
            logger.error(f"Error fetching UNCTAD data for {indicator_code}: {str(e)}")
        
        return []
    
    def get_wto_data(self, indicator_code, start_year=2015):
        """Fetch data from WTO API for Ethiopia"""
        try:
            url = f"{self.apis['wto']}/data"
            params = {
                'reporters': 'ET',
                'periods': f"{start_year},{datetime.now().year}",
                'indicators': indicator_code,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                records = []
                if 'dataset' in data:
                    for item in data['dataset']:
                        if 'value' in item and item['value'] is not None:
                            records.append({
                                'date': f"{item['period']}-12-31",
                                'indicator_code': indicator_code,
                                'indicator_name': item.get('indicator_label', f"WTO {indicator_code}"),
                                'value': float(item['value']),
                                'country': 'Ethiopia',
                                'source': 'WTO'
                            })
                
                return records
                
        except Exception as e:
            logger.error(f"Error fetching WTO data for {indicator_code}: {str(e)}")
        
        return []
    
    def fetch_comprehensive_ethiopia_data(self):
        """Fetch comprehensive economic data for Ethiopia from all sources"""
        all_data = []
        
        # World Bank indicators for Ethiopia
        wb_indicators = {
            'NY.GDP.MKTP.CD': 'GDP (current US$)',
            'NY.GDP.PCAP.CD': 'GDP per capita (current US$)',
            'FP.CPI.TOTL.ZG': 'Inflation, consumer prices (annual %)',
            'SL.UEM.TOTL.ZS': 'Unemployment, total (% of total labor force)',
            'NE.EXP.GNFS.CD': 'Exports of goods and services (current US$)',
            'NE.IMP.GNFS.CD': 'Imports of goods and services (current US$)',
            'BX.KLT.DINV.CD.WD': 'Foreign direct investment, net inflows (BoP, current US$)',
            'SP.POP.TOTL': 'Population, total',
            'NV.AGR.TOTL.ZS': 'Agriculture, forestry, and fishing, value added (% of GDP)',
            'NV.IND.TOTL.ZS': 'Industry (including construction), value added (% of GDP)',
            'NV.SRV.TOTL.ZS': 'Services, value added (% of GDP)',
            'PA.NUS.FCRF': 'Official exchange rate (LCU per US$, period average)',
            'GC.REV.XGRT.GD.ZS': 'Revenue, excluding grants (% of GDP)',
            'GC.XPN.TOTL.GD.ZS': 'Expense (% of GDP)',
            'GC.FIN.FRGN.ZS': 'Net lending (+) / net borrowing (-) (% of GDP)',
            'DT.DOD.DECT.CD': 'Total debt stocks (current US$)'
        }
        
        print("Fetching World Bank data for Ethiopia...")
        for code, name in wb_indicators.items():
            print(f"  Fetching {name}...")
            data = self.get_world_bank_data(code)
            all_data.extend(data)
            time.sleep(0.5)  # Rate limiting
        
        # IMF indicators for Ethiopia
        imf_indicators = {
            'IFS': {
                'NGDP': 'Gross Domestic Product, current prices',
                'NGDP_R': 'Gross Domestic Product, constant prices',
                'PCPI': 'Consumer Price Index',
                'LUR': 'Unemployment Rate',
                'BCA': 'Current Account Balance',
                'GGXWDG': 'General government gross debt'
            }
        }
        
        print("Fetching IMF data for Ethiopia...")
        for dataset, indicators in imf_indicators.items():
            for code, name in indicators.items():
                print(f"  Fetching {name}...")
                data = self.get_imf_data(dataset, code)
                all_data.extend(data)
                time.sleep(0.5)  # Rate limiting
        
        return all_data
    
    def store_external_data(self, data_records):
        """Store external data in database"""
        if not self.engine or not data_records:
            return 0
        
        stored_count = 0
        
        with self.engine.connect() as conn:
            for record in data_records:
                try:
                    # Check if record already exists
                    existing = conn.execute(
                        text("""
                            SELECT id FROM external_data_sources 
                            WHERE indicator_code = :code AND date = :date AND source = :source
                        """),
                        {
                            'code': record['indicator_code'],
                            'date': record['date'],
                            'source': record['source']
                        }
                    ).fetchone()
                    
                    if existing:
                        # Update existing record
                        conn.execute(
                            text("""
                                UPDATE external_data_sources SET
                                    indicator_name = :name,
                                    value = :value,
                                    country = :country,
                                    last_updated = NOW()
                                WHERE id = :id
                            """),
                            {
                                'name': record['indicator_name'],
                                'value': record['value'],
                                'country': record['country'],
                                'id': existing.id
                            }
                        )
                    else:
                        # Insert new record
                        conn.execute(
                            text("""
                                INSERT INTO external_data_sources (
                                    indicator_code, indicator_name, date, value, 
                                    country, source, created_at, last_updated
                                )
                                VALUES (
                                    :code, :name, :date, :value, 
                                    :country, :source, NOW(), NOW()
                                )
                            """),
                            {
                                'code': record['indicator_code'],
                                'name': record['indicator_name'],
                                'date': record['date'],
                                'value': record['value'],
                                'country': record['country'],
                                'source': record['source']
                            }
                        )
                    
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"Error storing record: {str(e)}")
                    continue
            
            conn.commit()
        
        return stored_count
    
    def export_data_to_csv(self, data_records, filename):
        """Export fetched data to CSV file"""
        if not data_records:
            return False
        
        try:
            df = pd.DataFrame(data_records)
            df.to_csv(filename, index=False)
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def get_data_summary(self, data_records):
        """Generate summary statistics for fetched data"""
        if not data_records:
            return {}
        
        df = pd.DataFrame(data_records)
        
        summary = {
            'total_records': len(df),
            'sources': df['source'].value_counts().to_dict(),
            'indicators': df['indicator_code'].nunique(),
            'date_range': {
                'start': df['date'].min(),
                'end': df['date'].max()
            },
            'countries': df['country'].unique().tolist()
        }
        
        return summary

def main():
    """Test external API integrations"""
    print("Testing External API Integrations - Task #3")
    print("=" * 50)
    
    integrator = ExternalDataIntegrator()
    
    # Test individual APIs
    print("\n1. Testing World Bank API...")
    wb_data = integrator.get_world_bank_data('NY.GDP.MKTP.CD', 2020, 2023)
    print(f"   Retrieved {len(wb_data)} World Bank records")
    
    print("\n2. Testing IMF API...")
    imf_data = integrator.get_imf_data('IFS', 'NGDP', 2020)
    print(f"   Retrieved {len(imf_data)} IMF records")
    
    # Fetch comprehensive data
    print("\n3. Fetching comprehensive Ethiopia data...")
    all_data = integrator.fetch_comprehensive_ethiopia_data()
    
    # Generate summary
    summary = integrator.get_data_summary(all_data)
    print(f"\nData Summary:")
    print(f"  Total records: {summary['total_records']}")
    print(f"  Sources: {summary['sources']}")
    print(f"  Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
    
    # Export to CSV
    export_file = 'Data/ethiopia_external_data_export.csv'
    if integrator.export_data_to_csv(all_data, export_file):
        print(f"\n✅ Data exported to {export_file}")
    
    # Store in database if available
    if integrator.engine:
        stored = integrator.store_external_data(all_data)
        print(f"✅ Stored {stored} records in database")
    
    print("\n🎉 External API Integration Test Complete!")

if __name__ == "__main__":
    main()