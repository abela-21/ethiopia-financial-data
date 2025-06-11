#!/usr/bin/env python3
"""
Test the edit functionality in data management section
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = "admin@ethiopia-economic.com"
ADMIN_PASSWORD = "EthiopiaAdmin2024!"

def login_and_test_edit():
    """Login as admin and test the edit functionality"""
    
    print("🔐 Testing Data Management Edit Functionality")
    print("=" * 50)
    
    session = requests.Session()
    
    # Step 1: Get login page to establish session
    print("📝 Step 1: Getting login page...")
    try:
        login_page = session.get(urljoin(BASE_URL, "/auth/login"), timeout=10)
        if login_page.status_code == 200:
            print("✅ Login page accessible")
        else:
            print(f"❌ Login page failed: {login_page.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login page error: {str(e)}")
        return False
    
    # Step 2: Perform login
    print("\n🔑 Step 2: Logging in as admin...")
    try:
        login_data = {
            'email': ADMIN_EMAIL,
            'password': ADMIN_PASSWORD
        }
        
        login_response = session.post(
            urljoin(BASE_URL, "/auth/login"),
            data=login_data,
            allow_redirects=True,
            timeout=10
        )
        
        # Check if login was successful
        if 'admin' in login_response.url.lower() or login_response.status_code == 200:
            print("✅ Admin login successful")
        else:
            print(f"❌ Login failed - redirected to: {login_response.url}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False
    
    # Step 3: Access economic indicators data page
    print("\n📊 Step 3: Accessing economic indicators page...")
    try:
        indicators_url = urljoin(BASE_URL, "/admin/data/economic-indicators")
        indicators_response = session.get(indicators_url, timeout=10)
        
        if indicators_response.status_code == 200:
            print("✅ Economic indicators page loaded")
            
            # Check for edit buttons in the page
            page_content = indicators_response.text
            if 'editIndicator(' in page_content and 'viewIndicator(' in page_content:
                print("✅ Edit and view buttons found in page")
            else:
                print("❌ Edit/view buttons missing from page")
                return False
                
        else:
            print(f"❌ Indicators page failed: {indicators_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Indicators page error: {str(e)}")
        return False
    
    # Step 4: Test API endpoint for getting indicator data
    print("\n🔍 Step 4: Testing indicator API (GET)...")
    try:
        api_url = urljoin(BASE_URL, "/admin/api/indicator/1")
        api_response = session.get(api_url, timeout=10)
        
        if api_response.status_code == 200:
            try:
                api_data = api_response.json()
                if api_data.get('success'):
                    indicator = api_data['indicator']
                    print("✅ Indicator API working - Retrieved data:")
                    print(f"   ID: {indicator['id']}")
                    print(f"   Date: {indicator['date']}")
                    print(f"   GDP Growth: {indicator.get('gdp_growth_rate', 'N/A')}")
                    print(f"   Inflation: {indicator.get('inflation_rate', 'N/A')}")
                    
                    # Step 5: Test updating the indicator
                    print("\n✏️ Step 5: Testing indicator update (PUT)...")
                    
                    # Prepare update with same data (no actual change)
                    update_data = {
                        'id': indicator['id'],
                        'date': indicator['date'],
                        'year': indicator['year'],
                        'quarter': indicator['quarter'],
                        'gdp_growth_rate': indicator.get('gdp_growth_rate'),
                        'inflation_rate': indicator.get('inflation_rate'),
                        'exchange_rate_usd': indicator.get('exchange_rate_usd'),
                        'central_bank_rate': indicator.get('central_bank_rate'),
                        'unemployment_rate': indicator.get('unemployment_rate')
                    }
                    
                    update_response = session.put(
                        api_url,
                        json=update_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if update_response.status_code == 200:
                        try:
                            update_result = update_response.json()
                            if update_result.get('success'):
                                print("✅ Update API working - Data saved successfully")
                                return True
                            else:
                                print(f"❌ Update failed: {update_result.get('error', 'Unknown')}")
                                return False
                        except:
                            print("❌ Update response invalid JSON")
                            return False
                    else:
                        print(f"❌ Update API failed: {update_response.status_code}")
                        print(f"   Response: {update_response.text[:200]}")
                        return False
                        
                else:
                    print(f"❌ API error: {api_data.get('error', 'Unknown')}")
                    return False
            except:
                print("❌ API response invalid JSON")
                return False
        else:
            print(f"❌ API failed: {api_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API error: {str(e)}")
        return False

def main():
    """Run the edit functionality test"""
    
    success = login_and_test_edit()
    
    print("\n" + "=" * 50)
    print("📋 EDIT FUNCTIONALITY TEST RESULTS")
    print("=" * 50)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Login: Working")
        print("✅ Data page access: Working")
        print("✅ Edit buttons: Present")
        print("✅ View API: Working")
        print("✅ Edit API: Working")
        print("\nThe data management edit functionality is working correctly.")
    else:
        print("❌ TESTS FAILED")
        print("The edit functionality needs attention.")
    
    return success

if __name__ == '__main__':
    main()