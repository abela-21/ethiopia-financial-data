#!/usr/bin/env python3
"""
Test and fix data refresh functionality
"""
import os
import sys
from datetime import datetime
from app import create_app, db
from sqlalchemy import text

def test_data_refresh():
    """Test the complete data refresh process"""
    print("🔧 Testing Data Refresh Functionality")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Test external API integration
            print("1. Testing external API integration...")
            from Data.enhanced_external_apis import EnhancedExternalDataIntegrator
            integrator = EnhancedExternalDataIntegrator()
            
            # Fetch limited data for testing
            print("   - Fetching World Bank data...")
            all_data = integrator.fetch_all_external_data()
            
            if all_data:
                print(f"   ✅ Successfully fetched {len(all_data)} external data records")
                
                # Store in database
                print("   - Storing in external_economic_data table...")
                integrator.store_in_database(all_data)
                print("   ✅ Data stored successfully")
                
                # Step 2: Test macro indicators population
                print("2. Testing macro indicators population...")
                from models import MacroIndicators
                
                # Check if external data exists
                with db.engine.connect() as conn:
                    # Get latest GDP growth
                    gdp_growth = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'NY.GDP.MKTP.KD.ZG' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    # Get latest inflation
                    inflation = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'FP.CPI.TOTL.ZG' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    # Get latest unemployment
                    unemployment = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'SL.UEM.TOTL.ZS' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    # Get latest exchange rate
                    exchange_rate = conn.execute(text("""
                        SELECT value FROM external_economic_data 
                        WHERE indicator_code = 'PA.NUS.FCRF' 
                        ORDER BY date DESC LIMIT 1
                    """)).scalar()
                    
                    print(f"   - GDP Growth: {gdp_growth}")
                    print(f"   - Inflation: {inflation}")
                    print(f"   - Unemployment: {unemployment}")
                    print(f"   - Exchange Rate: {exchange_rate}")
                
                # Clear existing macro indicators for today
                today = datetime.now().date()
                db.session.execute(text("DELETE FROM macro_indicators WHERE date = :date"), {"date": today})
                db.session.commit()
                
                # Create new macro indicator record
                macro_indicator = MacroIndicators()
                macro_indicator.date = today
                macro_indicator.gdp_growth = float(gdp_growth) if gdp_growth else None
                macro_indicator.inflation_rate = float(inflation) if inflation else None
                macro_indicator.unemployment_rate = float(unemployment) if unemployment else None
                macro_indicator.etb_usd = float(exchange_rate) if exchange_rate else None
                
                db.session.add(macro_indicator)
                db.session.commit()
                
                print("   ✅ Macro indicators populated successfully")
                
                # Step 3: Verify data persistence
                print("3. Verifying data persistence...")
                indicator_count = db.session.execute(text("SELECT COUNT(*) FROM macro_indicators")).scalar()
                external_count = db.session.execute(text("SELECT COUNT(*) FROM external_economic_data")).scalar()
                
                print(f"   - Macro indicators count: {indicator_count}")
                print(f"   - External data count: {external_count}")
                
                if indicator_count > 0 and external_count > 0:
                    print("   ✅ Data persistence verified")
                    print("\n🎉 Data refresh functionality is working correctly!")
                    return True
                else:
                    print("   ❌ Data persistence check failed")
                    return False
                    
            else:
                print("   ❌ No external data retrieved")
                return False
                
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_data_refresh()
    if success:
        print("\n✅ All tests passed! Data refresh is ready for production use.")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
    sys.exit(0 if success else 1)