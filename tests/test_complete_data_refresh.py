#!/usr/bin/env python3
"""
Comprehensive test for data refresh functionality via web interface
"""
import os
import requests
import json
from datetime import datetime

def test_web_data_refresh():
    """Test data refresh through web interface"""
    base_url = "http://localhost:5000"
    
    print("Testing Data Refresh via Web Interface")
    print("=" * 50)
    
    # Step 1: Login as admin
    print("1. Logging in as admin...")
    login_data = {
        'email': 'admin@ethiopia-economic.com',
        'password': os.environ.get("ADMIN_PASSWORD", "")
    }
    
    session = requests.Session()
    
    # Get login page first to get CSRF token if needed
    login_page = session.get(f"{base_url}/auth/login")
    if login_page.status_code != 200:
        print(f"   ❌ Cannot access login page: {login_page.status_code}")
        return False
    
    # Attempt login
    login_response = session.post(f"{base_url}/auth/login", data=login_data)
    if login_response.status_code == 200 and "admin" in login_response.text.lower():
        print("   ✅ Admin login successful")
    else:
        print(f"   ❌ Login failed: {login_response.status_code}")
        return False
    
    # Step 2: Check current indicators status
    print("2. Checking current economic indicators...")
    indicators_response = session.get(f"{base_url}/admin/data/economic-indicators")
    if indicators_response.status_code == 200:
        print("   ✅ Economic indicators page accessible")
    else:
        print(f"   ❌ Cannot access indicators page: {indicators_response.status_code}")
    
    # Step 3: Test data refresh API
    print("3. Testing data refresh API...")
    refresh_response = session.post(f"{base_url}/admin/api/refresh-data")
    
    if refresh_response.status_code == 200:
        try:
            response_data = refresh_response.json()
            if response_data.get('success'):
                print(f"   ✅ Data refresh successful: {response_data.get('message')}")
            else:
                print(f"   ❌ Data refresh failed: {response_data.get('error')}")
                return False
        except json.JSONDecodeError:
            print("   ❌ Invalid JSON response from refresh API")
            return False
    else:
        print(f"   ❌ Refresh API failed: {refresh_response.status_code}")
        print(f"   Response: {refresh_response.text[:200]}")
        return False
    
    # Step 4: Verify indicators are now visible
    print("4. Verifying indicators after refresh...")
    post_refresh_response = session.get(f"{base_url}/admin/data/economic-indicators")
    if post_refresh_response.status_code == 200:
        content = post_refresh_response.text
        
        # Check for key economic indicators in the page
        indicators_found = []
        if "gdp" in content.lower() or "growth" in content.lower():
            indicators_found.append("GDP Growth")
        if "inflation" in content.lower():
            indicators_found.append("Inflation")
        if "unemployment" in content.lower():
            indicators_found.append("Unemployment")
        if "exchange" in content.lower() or "etb" in content.lower():
            indicators_found.append("Exchange Rate")
        
        if indicators_found:
            print(f"   ✅ Found indicators: {', '.join(indicators_found)}")
            print("   ✅ Economic indicators are displaying correctly")
            return True
        else:
            print("   ⚠️ No indicators visible on page")
            return False
    else:
        print(f"   ❌ Cannot verify indicators: {post_refresh_response.status_code}")
        return False

def test_database_directly():
    """Test database state directly"""
    print("\n5. Direct database verification...")
    try:
        from app import create_app, db
        from sqlalchemy import text
        
        app = create_app()
        with app.app_context():
            # Check macro indicators
            indicator_count = db.session.execute(text("SELECT COUNT(*) FROM macro_indicators")).scalar()
            print(f"   - Macro indicators count: {indicator_count}")
            
            # Check external data
            external_count = db.session.execute(text("SELECT COUNT(*) FROM external_economic_data")).scalar()
            print(f"   - External data count: {external_count}")
            
            # Get latest indicator values
            if indicator_count > 0:
                latest_indicator = db.session.execute(text("""
                    SELECT date, gdp_growth, inflation_rate, unemployment_rate, etb_usd
                    FROM macro_indicators ORDER BY date DESC LIMIT 1
                """)).fetchone()
                
                if latest_indicator:
                    print(f"   - Latest indicator date: {latest_indicator.date}")
                    print(f"   - GDP Growth: {latest_indicator.gdp_growth}%")
                    print(f"   - Inflation: {latest_indicator.inflation_rate}%")
                    print(f"   - Unemployment: {latest_indicator.unemployment_rate}%")
                    print(f"   - ETB/USD: {latest_indicator.etb_usd}")
            
            return indicator_count > 0 and external_count > 0
            
    except Exception as e:
        print(f"   ❌ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Comprehensive Data Refresh Test")
    print("=" * 50)
    
    web_test_success = test_web_data_refresh()
    db_test_success = test_database_directly()
    
    print("\n" + "=" * 50)
    if web_test_success and db_test_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Data refresh functionality is working correctly")
        print("✅ Economic indicators are properly populated and displayed")
    else:
        print("❌ TESTS FAILED!")
        if not web_test_success:
            print("❌ Web interface test failed")
        if not db_test_success:
            print("❌ Database verification failed")
    
    print("=" * 50)