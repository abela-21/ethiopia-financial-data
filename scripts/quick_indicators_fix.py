#!/usr/bin/env python3
"""
Quick fix for economic indicators data persistence
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text
from datetime import datetime
from models import MacroIndicators

def quick_fix_indicators():
    """Quick fix to populate macro indicators from existing external data"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Checking external data availability...")
            
            # Check if we have external data
            external_count = db.session.execute(text("SELECT COUNT(*) FROM external_economic_data")).scalar()
            print(f"External data records available: {external_count}")
            
            if external_count > 0:
                print("Populating macro indicators from existing external data...")
                
                # Get latest values for key indicators
                with db.engine.connect() as conn:
                    gdp_growth = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'NY.GDP.MKTP.KD.ZG' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    inflation = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'FP.CPI.TOTL.ZG' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    unemployment = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'SL.UEM.TOTL.ZS' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    exchange_rate = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'PA.NUS.FCRF' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    exports = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'NE.EXP.GNFS.CD' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    imports = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'NE.IMP.GNFS.CD' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    fdi = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'BX.KLT.DINV.CD.WD' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                
                # Clear existing indicators for today
                today = datetime.now().date()
                db.session.execute(text("DELETE FROM macro_indicators WHERE date = :date"), {"date": today})
                db.session.commit()
                
                # Create new indicator record
                indicator = MacroIndicators()
                indicator.date = today
                indicator.gdp_growth = float(gdp_growth) if gdp_growth else None
                indicator.inflation_rate = float(inflation) if inflation else None
                indicator.unemployment_rate = float(unemployment) if unemployment else None
                indicator.exports = float(exports) if exports else None
                indicator.imports = float(imports) if imports else None
                indicator.trade_balance = float(exports - imports) if exports and imports else None
                indicator.fdi_inflow = float(fdi) if fdi else None
                indicator.etb_usd = float(exchange_rate) if exchange_rate else None
                
                db.session.add(indicator)
                db.session.commit()
                
                print("✅ Macro indicators populated successfully!")
                
                # Verify
                indicator_count = db.session.execute(text("SELECT COUNT(*) FROM macro_indicators")).scalar()
                print(f"Total macro indicators: {indicator_count}")
                return True
            else:
                print("❌ No external data available. Running quick data fetch...")
                # Fetch minimal essential data
                from Data.enhanced_external_apis import EnhancedExternalDataIntegrator
                integrator = EnhancedExternalDataIntegrator()
                
                # Fetch only essential indicators
                essential_data = []
                indicators = ['NY.GDP.MKTP.KD.ZG', 'FP.CPI.TOTL.ZG', 'PA.NUS.FCRF']
                
                for indicator_code in indicators:
                    try:
                        data = integrator.fetch_world_bank_indicator(indicator_code)
                        if data:
                            essential_data.extend(data)
                    except Exception as e:
                        print(f"Warning: Could not fetch {indicator_code}: {e}")
                
                if essential_data:
                    integrator.store_in_database(essential_data)
                    print(f"✅ Fetched and stored {len(essential_data)} essential records")
                    # Recursively call to populate indicators
                    return quick_fix_indicators()
                else:
                    print("❌ Could not fetch essential data")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = quick_fix_indicators()
    print("✅ Quick fix completed!" if success else "❌ Quick fix failed!")