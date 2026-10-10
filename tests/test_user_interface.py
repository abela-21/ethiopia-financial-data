#!/usr/bin/env python3
"""
Test the data management edit functionality from user interface perspective
"""

import os
import requests
import json
from urllib.parse import urljoin
import time

BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@ethiopia-economic.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

def test_complete_user_workflow():
    """Test the complete user workflow for editing economic indicators"""
    
    print("🔐 TESTING COMPLETE USER EDIT WORKFLOW")
    print("=" * 60)
    
    session = requests.Session()
    
    # Step 1: Navigate to login page
    print("📝 Step 1: Navigating to login page...")
    try:
        login_page = session.get(urljoin(BASE_URL, "/auth/login"), timeout=10)
        if login_page.status_code == 200 and "login" in login_page.text.lower():
            print("✅ Login page loaded successfully")
        else:
            print(f"❌ Login page issue: {login_page.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing login page: {str(e)}")
        return False
    
    # Step 2: Submit login credentials
    print("\n🔑 Step 2: Submitting admin credentials...")
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
        
        # Check if redirected to admin area
        if login_response.status_code == 200:
            print("✅ Login successful - accessing admin area")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False
    
    # Step 3: Navigate to admin panel
    print("\n🏠 Step 3: Accessing admin panel...")
    try:
        admin_panel = session.get(urljoin(BASE_URL, "/admin"), timeout=10)
        if admin_panel.status_code == 200 and "admin" in admin_panel.text.lower():
            print("✅ Admin panel accessible")
        else:
            print(f"❌ Admin panel access failed: {admin_panel.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin panel error: {str(e)}")
        return False
    
    # Step 4: Navigate to data management
    print("\n📊 Step 4: Accessing data management section...")
    try:
        data_mgmt = session.get(urljoin(BASE_URL, "/admin/manage-data"), timeout=10)
        if data_mgmt.status_code == 200:
            print("✅ Data management section loaded")
        else:
            print(f"❌ Data management access failed: {data_mgmt.status_code}")
            return False
    except Exception as e:
        print(f"❌ Data management error: {str(e)}")
        return False
    
    # Step 5: Access economic indicators table
    print("\n📈 Step 5: Opening economic indicators table...")
    try:
        indicators_page = session.get(urljoin(BASE_URL, "/admin/data/economic-indicators"), timeout=10)
        if indicators_page.status_code == 200:
            page_content = indicators_page.text
            
            # Check for required elements
            checks = [
                ('table', 'Data table present'),
                ('editIndicator(', 'Edit functions available'),
                ('viewIndicator(', 'View functions available'),
                ('btn-outline-primary', 'Action buttons present'),
                ('modal', 'Modal dialogs included')
            ]
            
            print("✅ Economic indicators page loaded")
            print("   Checking page elements:")
            
            all_elements_present = True
            for element, description in checks:
                if element in page_content:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ❌ {description} - MISSING")
                    all_elements_present = False
            
            if not all_elements_present:
                return False
                
        else:
            print(f"❌ Indicators page failed: {indicators_page.status_code}")
            return False
    except Exception as e:
        print(f"❌ Indicators page error: {str(e)}")
        return False
    
    # Step 6: Test view functionality (simulating button click)
    print("\n👁️ Step 6: Testing view functionality...")
    try:
        # Simulate clicking view button by calling the API directly
        view_response = session.get(urljoin(BASE_URL, "/admin/api/indicator/1"), timeout=10)
        
        if view_response.status_code == 200:
            view_data = view_response.json()
            if view_data.get('success'):
                indicator = view_data['indicator']
                print("✅ View functionality working:")
                print(f"   - Indicator ID: {indicator['id']}")
                print(f"   - Date: {indicator['date']}")
                print(f"   - GDP Growth: {indicator.get('gdp_growth_rate', 'N/A')}")
                print(f"   - Inflation: {indicator.get('inflation_rate', 'N/A')}")
                print(f"   - Exchange Rate: {indicator.get('exchange_rate_usd', 'N/A')}")
            else:
                print(f"❌ View API error: {view_data.get('error')}")
                return False
        else:
            print(f"❌ View API failed: {view_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ View functionality error: {str(e)}")
        return False
    
    # Step 7: Test edit functionality (simulating form submission)
    print("\n✏️ Step 7: Testing edit functionality...")
    try:
        # Get current data first
        current_data = session.get(urljoin(BASE_URL, "/admin/api/indicator/1"), timeout=10).json()
        if not current_data.get('success'):
            print("❌ Could not retrieve current data for editing")
            return False
        
        indicator = current_data['indicator']
        
        # Prepare update data (making a small test change)
        original_gdp = indicator.get('gdp_growth_rate')
        test_gdp = original_gdp + 0.001 if original_gdp else 0.001  # Small test change
        
        update_data = {
            'id': indicator['id'],
            'date': indicator['date'],
            'year': indicator['year'],
            'quarter': indicator['quarter'],
            'gdp_growth_rate': test_gdp,  # Test change
            'inflation_rate': indicator.get('inflation_rate'),
            'exchange_rate_usd': indicator.get('exchange_rate_usd'),
            'central_bank_rate': indicator.get('central_bank_rate'),
            'unemployment_rate': indicator.get('unemployment_rate')
        }
        
        # Submit update
        edit_response = session.put(
            urljoin(BASE_URL, "/admin/api/indicator/1"),
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if edit_response.status_code == 200:
            edit_result = edit_response.json()
            if edit_result.get('success'):
                print("✅ Edit functionality working:")
                print(f"   - Update submitted successfully")
                print(f"   - GDP Growth changed from {original_gdp} to {test_gdp}")
                
                # Verify the change was saved
                verify_response = session.get(urljoin(BASE_URL, "/admin/api/indicator/1"), timeout=10)
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    if verify_data.get('success'):
                        updated_gdp = verify_data['indicator'].get('gdp_growth_rate')
                        if abs(updated_gdp - test_gdp) < 0.0001:  # Account for floating point precision
                            print("✅ Changes verified in database")
                            
                            # Restore original value
                            restore_data = update_data.copy()
                            restore_data['gdp_growth_rate'] = original_gdp
                            restore_response = session.put(
                                urljoin(BASE_URL, "/admin/api/indicator/1"),
                                json=restore_data,
                                headers={'Content-Type': 'application/json'},
                                timeout=10
                            )
                            if restore_response.status_code == 200:
                                print("✅ Original value restored")
                            
                        else:
                            print(f"❌ Change not saved correctly: expected {test_gdp}, got {updated_gdp}")
                            return False
                    else:
                        print("❌ Could not verify changes")
                        return False
                else:
                    print("❌ Verification request failed")
                    return False
            else:
                print(f"❌ Edit failed: {edit_result.get('error')}")
                return False
        else:
            print(f"❌ Edit API failed: {edit_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Edit functionality error: {str(e)}")
        return False
    
    return True

def main():
    """Run the complete user interface test"""
    
    success = test_complete_user_workflow()
    
    print("\n" + "=" * 60)
    print("📋 COMPLETE USER WORKFLOW TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("🎉 ALL USER WORKFLOW TESTS PASSED!")
        print()
        print("✅ Login process: Working")
        print("✅ Admin panel access: Working") 
        print("✅ Data management navigation: Working")
        print("✅ Economic indicators table: Working")
        print("✅ View modal functionality: Working")
        print("✅ Edit form functionality: Working")
        print("✅ Data persistence: Working")
        print("✅ Change verification: Working")
        print()
        print("The complete user interface workflow for editing economic")
        print("indicators is fully functional from login to data modification.")
    else:
        print("❌ USER WORKFLOW TESTS FAILED")
        print("Some aspects of the user interface need attention.")
    
    return success

if __name__ == '__main__':
    main()