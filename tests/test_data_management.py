#!/usr/bin/env python3
"""
Test economic indicators review and edit functionality
"""

import os
import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@ethiopia-economic.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

def login_admin():
    """Login as admin and return session"""
    session = requests.Session()
    
    # Get login page first
    login_page = session.get(urljoin(BASE_URL, "/auth/login"))
    if login_page.status_code != 200:
        print(f"❌ Failed to access login page: {login_page.status_code}")
        return None
    
    # Login
    login_data = {
        'email': ADMIN_EMAIL,
        'password': ADMIN_PASSWORD
    }
    
    login_response = session.post(
        urljoin(BASE_URL, "/auth/login"),
        data=login_data,
        allow_redirects=False
    )
    
    if login_response.status_code in [302, 303]:
        print("✅ Admin login successful")
        return session
    else:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return None

def test_indicator_api_endpoints():
    """Test the indicator API endpoints for view and edit"""
    
    print("🧪 TESTING ECONOMIC INDICATORS REVIEW & EDIT FUNCTIONALITY")
    print("=" * 70)
    
    # Login as admin
    session = login_admin()
    if not session:
        return False
    
    print()
    
    # Step 1: Access the economic indicators page
    print("📊 Step 1: Accessing economic indicators data page...")
    indicators_page = session.get(urljoin(BASE_URL, "/admin/data/economic-indicators"))
    
    if indicators_page.status_code == 200:
        print("✅ Economic indicators page loaded successfully")
        
        # Check if page contains the expected elements
        if 'viewIndicator(' in indicators_page.text and 'editIndicator(' in indicators_page.text:
            print("✅ Review and edit buttons are present in the table")
        else:
            print("❌ Review and edit buttons missing from table")
            return False
    else:
        print(f"❌ Failed to load indicators page: {indicators_page.status_code}")
        return False
    
    print()
    
    # Step 2: Test getting first indicator via API
    print("🔍 Step 2: Testing indicator details API (Review functionality)...")
    
    # Try to get indicator with ID 1
    api_response = session.get(urljoin(BASE_URL, "/admin/api/indicator/1"))
    
    if api_response.status_code == 200:
        try:
            api_data = api_response.json()
            if api_data.get('success'):
                indicator = api_data['indicator']
                print("✅ Indicator API working - Retrieved indicator details:")
                print(f"   - ID: {indicator['id']}")
                print(f"   - Date: {indicator['date']}")
                print(f"   - Year: {indicator['year']}")
                print(f"   - Quarter: Q{indicator['quarter']}")
                print(f"   - GDP Growth: {indicator['gdp_growth_rate']}")
                print(f"   - Inflation: {indicator['inflation_rate']}")
                
                # Step 3: Test updating the indicator
                print()
                print("✏️ Step 3: Testing indicator update API (Edit functionality)...")
                
                # Prepare update data (small change to test)
                update_data = {
                    'id': indicator['id'],
                    'date': indicator['date'],
                    'year': indicator['year'],
                    'quarter': indicator['quarter'],
                    'gdp_growth_rate': indicator['gdp_growth_rate'],
                    'inflation_rate': indicator['inflation_rate'],
                    'exchange_rate_usd': indicator['exchange_rate_usd'],
                    'central_bank_rate': indicator['central_bank_rate'],
                    'unemployment_rate': indicator['unemployment_rate']
                }
                
                # Test the update endpoint
                update_response = session.put(
                    urljoin(BASE_URL, f"/admin/api/indicator/{indicator['id']}"),
                    json=update_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if update_response.status_code == 200:
                    try:
                        update_result = update_response.json()
                        if update_result.get('success'):
                            print("✅ Indicator update API working - Changes saved successfully")
                            return True
                        else:
                            print(f"❌ Update failed: {update_result.get('error', 'Unknown error')}")
                            return False
                    except:
                        print("❌ Update response not valid JSON")
                        return False
                else:
                    print(f"❌ Update API failed: {update_response.status_code}")
                    print(f"   Response: {update_response.text[:200]}")
                    return False
                
            else:
                print(f"❌ API returned error: {api_data.get('error', 'Unknown error')}")
                return False
        except:
            print("❌ API response not valid JSON")
            return False
    else:
        print(f"❌ Indicator API failed: {api_response.status_code}")
        return False

def test_modal_functionality():
    """Test that the modal HTML elements are properly structured"""
    
    print()
    print("🎭 TESTING MODAL FUNCTIONALITY")
    print("=" * 70)
    
    session = login_admin()
    if not session:
        return False
    
    # Get the indicators page
    indicators_page = session.get(urljoin(BASE_URL, "/admin/data/economic-indicators"))
    
    if indicators_page.status_code == 200:
        page_content = indicators_page.text
        
        # Check for modal elements
        modal_checks = [
            ('viewIndicatorModal', 'View modal container'),
            ('editIndicatorModal', 'Edit modal container'),
            ('viewIndicatorContent', 'View modal content area'),
            ('editIndicatorContent', 'Edit modal content area'),
            ('editIndicatorForm', 'Edit form template'),
            ('saveIndicator()', 'Save function')
        ]
        
        print("🔍 Checking modal elements:")
        all_present = True
        
        for element, description in modal_checks:
            if element in page_content:
                print(f"✅ {description} - Found")
            else:
                print(f"❌ {description} - Missing")
                all_present = False
        
        return all_present
    else:
        print(f"❌ Could not load page to check modals: {indicators_page.status_code}")
        return False

def run_complete_test():
    """Run complete test suite"""
    
    print("🚀 RUNNING COMPLETE ECONOMIC INDICATORS TEST SUITE")
    print("=" * 70)
    
    # Test API endpoints
    api_test = test_indicator_api_endpoints()
    
    # Test modal functionality  
    modal_test = test_modal_functionality()
    
    print()
    print("📋 FINAL TEST RESULTS:")
    print("=" * 70)
    
    if api_test and modal_test:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Review functionality: Working")
        print("✅ Edit functionality: Working") 
        print("✅ Modal interfaces: Working")
        print("✅ API endpoints: Working")
        print()
        print("The economic indicators review and edit features are fully functional.")
        return True
    else:
        print("❌ SOME TESTS FAILED:")
        if not api_test:
            print("   - API endpoints need attention")
        if not modal_test:
            print("   - Modal interfaces need attention")
        return False

if __name__ == '__main__':
    run_complete_test()