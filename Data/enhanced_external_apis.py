#!/usr/bin/env python3
"""
Enhanced External API Integration System
Optimized integration with World Bank, UN Stats, FRED (Federal Reserve), and African Development Bank
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedExternalDataIntegrator:
    """Enhanced integration with multiple international economic data sources"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url) if self.database_url else None
        
        # Optimized API endpoints
        self.apis = {
            'world_bank': 'https://api.worldbank.org/v2',
            'un_stats': 'https://unstats.un.org/SDGAPI/v1',
            'fred': 'https://api.stlouisfed.org/fred',
            'adb': 'https://data.adb.org/api/3/action'
        }
        
    def get_world_bank_ethiopia_data(self, start_year=2015, end_year=2024):
        """Fetch comprehensive World Bank data for Ethiopia"""
        
        # Key indicators for Ethiopia's economy
        indicators = {
            'NY.GDP.MKTP.CD': 'GDP (current US$)',
            'NY.GDP.PCAP.CD': 'GDP per capita (current US$)', 
            'NY.GDP.MKTP.KD.ZG': 'GDP growth (annual %)',
            'FP.CPI.TOTL.ZG': 'Inflation, consumer prices (annual %)',
            'SL.UEM.TOTL.ZS': 'Unemployment, total (% of total labor force)',
            'NE.EXP.GNFS.CD': 'Exports of goods and services (current US$)',
            'NE.IMP.GNFS.CD': 'Imports of goods and services (current US$)',
            'BX.KLT.DINV.CD.WD': 'Foreign direct investment, net inflows',
            'SP.POP.TOTL': 'Population, total',
            'PA.NUS.FCRF': 'Official exchange rate (ETB per US$)',
            'GC.REV.XGRT.GD.ZS': 'Revenue, excluding grants (% of GDP)',
            'GC.XPN.TOTL.GD.ZS': 'Expense (% of GDP)',
            'DT.DOD.DECT.CD': 'External debt stocks, total',
            'NV.AGR.TOTL.ZS': 'Agriculture, value added (% of GDP)',
            'NV.IND.TOTL.ZS': 'Industry, value added (% of GDP)',
            'NV.SRV.TOTL.ZS': 'Services, value added (% of GDP)',
            'SE.PRM.NENR': 'School enrollment, primary (% net)',
            'SH.XPD.CHEX.GD.ZS': 'Current health expenditure (% of GDP)',
            'AG.LND.ARBL.ZS': 'Arable land (% of land area)',
            'EG.USE.ELEC.KH.PC': 'Electric power consumption (kWh per capita)'
        }
        
        all_records = []
        
        for indicator_code, indicator_name in indicators.items():
            try:
                url = f"{self.apis['world_bank']}/country/ET/indicator/{indicator_code}"
                params = {
                    'format': 'json',
                    'date': f"{start_year}:{end_year}",
                    'per_page': 1000
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                if len(data) > 1 and data[1]:
                    for item in data[1]:
                        if item['value'] is not None:
                            all_records.append({
                                'date': f"{item['date']}-12-31",
                                'indicator_code': indicator_code,
                                'indicator_name': indicator_name,
                                'value': float(item['value']),
                                'country': 'Ethiopia',
                                'source': 'World Bank',
                                'unit': self._get_indicator_unit(indicator_code),
                                'category': self._get_indicator_category(indicator_code)
                            })
                
                logger.info(f"Fetched {indicator_name}: {len([r for r in all_records if r['indicator_code'] == indicator_code])} records")
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching {indicator_name}: {str(e)}")
                continue
        
        return all_records
    
    def get_un_sdg_data(self):
        """Fetch UN Sustainable Development Goals data for Ethiopia"""
        try:
            # UN SDG API for Ethiopia
            url = f"{self.apis['un_stats']}/sdg/Series/Data"
            params = {
                'area': '231',  # Ethiopia's UN code
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                records = []
                for item in data.get('data', []):
                    if 'value' in item and item['value'] is not None:
                        records.append({
                            'date': f"{item.get('timePeriod', '2023')}-12-31",
                            'indicator_code': item.get('seriesCode', 'UN_SDG'),
                            'indicator_name': item.get('seriesDescription', 'UN SDG Indicator'),
                            'value': float(item['value']),
                            'country': 'Ethiopia',
                            'source': 'UN Statistics',
                            'unit': item.get('unit', ''),
                            'category': 'Sustainable Development'
                        })
                
                return records
                
        except Exception as e:
            logger.error(f"Error fetching UN SDG data: {str(e)}")
        
        return []
    
    def get_african_development_bank_data(self):
        """Fetch African Development Bank data for Ethiopia"""
        try:
            # ADB API for country statistics
            url = f"{self.apis['adb']}/datastore_search"
            params = {
                'resource_id': 'country-statistics',
                'filters': '{"country":"Ethiopia"}',
                'limit': 1000
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                records = []
                for item in data.get('result', {}).get('records', []):
                    if 'value' in item and item['value'] is not None:
                        try:
                            value = float(item['value'])
                            records.append({
                                'date': f"{item.get('year', '2023')}-12-31",
                                'indicator_code': item.get('indicator_code', 'ADB_STAT'),
                                'indicator_name': item.get('indicator_name', 'ADB Indicator'),
                                'value': value,
                                'country': 'Ethiopia',
                                'source': 'African Development Bank',
                                'unit': item.get('unit', ''),
                                'category': 'Development Finance'
                            })
                        except (ValueError, TypeError):
                            continue
                
                return records
                
        except Exception as e:
            logger.error(f"Error fetching ADB data: {str(e)}")
        
        return []
    
    def get_ethiopia_trade_data(self):
        """Fetch trade data for Ethiopia from UN Comtrade"""
        try:
            # UN Comtrade API for Ethiopia trade statistics
            url = "https://comtrade.un.org/api/get"
            params = {
                'max': 1000,
                'type': 'C',
                'freq': 'A',
                'px': 'HS',
                'ps': '2020,2021,2022,2023',
                'r': '231',  # Ethiopia
                'p': '0',    # World
                'rg': '1,2', # Import, Export
                'cc': 'TOTAL',
                'fmt': 'json'
            }
            
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                
                records = []
                for item in data.get('dataset', []):
                    trade_value = item.get('TradeValue')
                    if trade_value:
                        flow_type = 'Export' if item.get('rgDesc') == 'Export' else 'Import'
                        records.append({
                            'date': f"{item.get('yr', '2023')}-12-31",
                            'indicator_code': f"TRADE_{flow_type.upper()}",
                            'indicator_name': f"Total {flow_type}s (US$)",
                            'value': float(trade_value),
                            'country': 'Ethiopia',
                            'source': 'UN Comtrade',
                            'unit': 'US Dollars',
                            'category': 'International Trade'
                        })
                
                return records
                
        except Exception as e:
            logger.error(f"Error fetching trade data: {str(e)}")
        
        return []
    
    def _get_indicator_unit(self, indicator_code):
        """Get appropriate unit for World Bank indicators"""
        unit_mapping = {
            'NY.GDP.MKTP.CD': 'Current US$',
            'NY.GDP.PCAP.CD': 'Current US$ per capita',
            'NY.GDP.MKTP.KD.ZG': 'Annual %',
            'FP.CPI.TOTL.ZG': 'Annual %',
            'SL.UEM.TOTL.ZS': '% of labor force',
            'NE.EXP.GNFS.CD': 'Current US$',
            'NE.IMP.GNFS.CD': 'Current US$',
            'BX.KLT.DINV.CD.WD': 'Current US$',
            'SP.POP.TOTL': 'Number of people',
            'PA.NUS.FCRF': 'ETB per US$',
            'GC.REV.XGRT.GD.ZS': '% of GDP',
            'GC.XPN.TOTL.GD.ZS': '% of GDP',
            'DT.DOD.DECT.CD': 'Current US$',
            'NV.AGR.TOTL.ZS': '% of GDP',
            'NV.IND.TOTL.ZS': '% of GDP',
            'NV.SRV.TOTL.ZS': '% of GDP',
            'SE.PRM.NENR': '% net enrollment',
            'SH.XPD.CHEX.GD.ZS': '% of GDP',
            'AG.LND.ARBL.ZS': '% of land area',
            'EG.USE.ELEC.KH.PC': 'kWh per capita'
        }
        return unit_mapping.get(indicator_code, 'Units')
    
    def _get_indicator_category(self, indicator_code):
        """Categorize World Bank indicators"""
        categories = {
            'NY.GDP.MKTP.CD': 'Economic Growth',
            'NY.GDP.PCAP.CD': 'Economic Growth',
            'NY.GDP.MKTP.KD.ZG': 'Economic Growth',
            'FP.CPI.TOTL.ZG': 'Monetary Policy',
            'SL.UEM.TOTL.ZS': 'Labor Market',
            'NE.EXP.GNFS.CD': 'International Trade',
            'NE.IMP.GNFS.CD': 'International Trade',
            'BX.KLT.DINV.CD.WD': 'Capital Flows',
            'SP.POP.TOTL': 'Demographics',
            'PA.NUS.FCRF': 'Exchange Rate',
            'GC.REV.XGRT.GD.ZS': 'Public Finance',
            'GC.XPN.TOTL.GD.ZS': 'Public Finance',
            'DT.DOD.DECT.CD': 'External Debt',
            'NV.AGR.TOTL.ZS': 'Sectoral GDP',
            'NV.IND.TOTL.ZS': 'Sectoral GDP',
            'NV.SRV.TOTL.ZS': 'Sectoral GDP',
            'SE.PRM.NENR': 'Education',
            'SH.XPD.CHEX.GD.ZS': 'Health',
            'AG.LND.ARBL.ZS': 'Agriculture',
            'EG.USE.ELEC.KH.PC': 'Energy'
        }
        return categories.get(indicator_code, 'Economic Indicator')
    
    def fetch_all_external_data(self):
        """Fetch data from all external sources"""
        all_data = []
        
        print("Fetching World Bank data for Ethiopia...")
        wb_data = self.get_world_bank_ethiopia_data()
        all_data.extend(wb_data)
        print(f"Retrieved {len(wb_data)} World Bank records")
        
        print("Fetching UN SDG data...")
        un_data = self.get_un_sdg_data()
        all_data.extend(un_data)
        print(f"Retrieved {len(un_data)} UN Statistics records")
        
        print("Fetching African Development Bank data...")
        adb_data = self.get_african_development_bank_data()
        all_data.extend(adb_data)
        print(f"Retrieved {len(adb_data)} ADB records")
        
        print("Fetching Ethiopia trade data...")
        trade_data = self.get_ethiopia_trade_data()
        all_data.extend(trade_data)
        print(f"Retrieved {len(trade_data)} Trade records")
        
        return all_data
    
    def store_in_database(self, data_records):
        """Store external data in database with improved handling"""
        if not self.engine or not data_records:
            return 0
        
        stored_count = 0
        updated_count = 0
        
        with self.engine.connect() as conn:
            for record in data_records:
                try:
                    # Check if record exists
                    existing = conn.execute(
                        text("""
                            SELECT id FROM external_economic_data 
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
                                UPDATE external_economic_data SET
                                    indicator_name = :name,
                                    value = :value,
                                    unit = :unit,
                                    last_updated = NOW()
                                WHERE id = :id
                            """),
                            {
                                'name': record['indicator_name'],
                                'value': record['value'],
                                'unit': record.get('unit', ''),
                                'id': existing.id
                            }
                        )
                        updated_count += 1
                    else:
                        # Insert new record
                        conn.execute(
                            text("""
                                INSERT INTO external_economic_data (
                                    indicator_code, indicator_name, date, value, 
                                    country, source, unit, created_at, last_updated
                                )
                                VALUES (
                                    :code, :name, :date, :value, 
                                    :country, :source, :unit, NOW(), NOW()
                                )
                            """),
                            {
                                'code': record['indicator_code'],
                                'name': record['indicator_name'],
                                'date': record['date'],
                                'value': record['value'],
                                'country': record['country'],
                                'source': record['source'],
                                'unit': record.get('unit', '')
                            }
                        )
                        stored_count += 1
                        
                except Exception as e:
                    logger.error(f"Error storing record {record.get('indicator_code', 'unknown')}: {str(e)}")
                    continue
            
            conn.commit()
        
        return {'new': stored_count, 'updated': updated_count}
    
    def export_to_files(self, data_records):
        """Export data to multiple file formats"""
        if not data_records:
            return {}
        
        results = {}
        
        try:
            df = pd.DataFrame(data_records)
            
            # Export to CSV
            csv_file = 'Data/ethiopia_external_data_comprehensive.csv'
            df.to_csv(csv_file, index=False)
            results['csv'] = csv_file
            
            # Export to Excel with multiple sheets
            excel_file = 'Data/ethiopia_external_data_comprehensive.xlsx'
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # All data
                df.to_excel(writer, sheet_name='All Data', index=False)
                
                # By source
                for source in df['source'].unique():
                    source_data = df[df['source'] == source]
                    sheet_name = source.replace(' ', '_')[:31]  # Excel sheet name limit
                    source_data.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # By category if available
                if 'category' in df.columns:
                    for category in df['category'].unique():
                        if pd.notna(category):
                            cat_data = df[df['category'] == category]
                            sheet_name = category.replace(' ', '_')[:31]
                            cat_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            results['excel'] = excel_file
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
        
        return results

def main():
    """Test enhanced external API integrations"""
    print("Enhanced External API Integration - Task #3")
    print("=" * 55)
    
    integrator = EnhancedExternalDataIntegrator()
    
    # Fetch all external data
    all_data = integrator.fetch_all_external_data()
    
    if all_data:
        print(f"\nTotal records retrieved: {len(all_data)}")
        
        # Export to files
        export_results = integrator.export_to_files(all_data)
        for format_type, file_path in export_results.items():
            print(f"Exported {format_type.upper()}: {file_path}")
        
        # Store in database
        if integrator.engine:
            db_results = integrator.store_in_database(all_data)
            print(f"Database storage: {db_results['new']} new, {db_results['updated']} updated")
        
        # Data summary by source
        df = pd.DataFrame(all_data)
        print("\nData Summary by Source:")
        for source, count in df['source'].value_counts().items():
            print(f"  {source}: {count} records")
        
        print("\n✅ External API Integration Complete")
    else:
        print("No data retrieved from external sources")

if __name__ == "__main__":
    main()