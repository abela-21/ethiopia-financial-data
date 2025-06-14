#!/usr/bin/env python3
"""
Test the Bootstrap 5 modal functionality directly
"""

import requests
from urllib.parse import urljoin
import json

BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = "admin@ethiopia-economic.com"
ADMIN_PASSWORD = "EthiopiaAdmin2024!"

def test_bootstrap_modal_fix():
    """Test the fixed Bootstrap 5 modal functionality"""
    
    print("TESTING BOOTSTRAP 5 MODAL FIX")
    print("=" * 50)
    
    session = requests.Session()
    
    # Login
    login_data = {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD}
    login_response = session.post(urljoin(BASE_URL, "/auth/login"), data=login_data, allow_redirects=True)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return False
    
    print("✓ Admin login successful")
    
    # Get updated indicators page
    indicators_page = session.get(urljoin(BASE_URL, "/admin/data/economic-indicators"))
    
    if indicators_page.status_code != 200:
        print(f"Indicators page failed: {indicators_page.status_code}")
        return False
    
    content = indicators_page.text
    
    # Check for Bootstrap 5 modal syntax
    bootstrap5_checks = [
        ("new bootstrap.Modal", "Bootstrap 5 modal initialization"),
        ("bootstrap.Modal.getInstance", "Bootstrap 5 modal instance method"),
        ("viewModal.show()", "Bootstrap 5 show method"),
        ("editModal.show()", "Bootstrap 5 edit show method")
    ]
    
    print("\nChecking Bootstrap 5 compatibility:")
    all_present = True
    for check, description in bootstrap5_checks:
        if check in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - MISSING")
            all_present = False
    
    # Test view functionality
    print("\nTesting view functionality:")
    view_response = session.get(urljoin(BASE_URL, "/admin/api/indicator/13"))
    if view_response.status_code == 200:
        try:
            view_data = view_response.json()
            if view_data.get('success'):
                indicator = view_data['indicator']
                print(f"  ✓ View API working - ID: {indicator['id']}, Date: {indicator['date']}")
                print(f"    GDP: {indicator.get('gdp_growth_rate', 'N/A')}, Inflation: {indicator.get('inflation_rate', 'N/A')}")
            else:
                print(f"  ✗ View API error: {view_data.get('error')}")
                return False
        except:
            print("  ✗ View API returned invalid JSON")
            return False
    else:
        print(f"  ✗ View API failed: {view_response.status_code}")
        return False
    
    # Test edit functionality
    print("\nTesting edit functionality:")
    # Get current data
    current_response = session.get(urljoin(BASE_URL, "/admin/api/indicator/13"))
    if current_response.status_code == 200:
        current_data = current_response.json()
        if current_data.get('success'):
            indicator = current_data['indicator']
            
            # Prepare test edit (minimal change)
            original_gdp = indicator.get('gdp_growth_rate', 0)
            test_gdp = original_gdp + 0.001 if original_gdp else 0.001
            
            edit_data = {
                'id': indicator['id'],
                'date': indicator['date'],
                'year': indicator['year'],
                'quarter': indicator['quarter'],
                'gdp_growth_rate': test_gdp,
                'inflation_rate': indicator.get('inflation_rate'),
                'exchange_rate_usd': indicator.get('exchange_rate_usd'),
                'central_bank_rate': indicator.get('central_bank_rate'),
                'unemployment_rate': indicator.get('unemployment_rate')
            }
            
            # Submit edit
            edit_response = session.put(
                urljoin(BASE_URL, "/admin/api/indicator/13"),
                json=edit_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if edit_response.status_code == 200:
                edit_result = edit_response.json()
                if edit_result.get('success'):
                    print(f"  ✓ Edit API working - GDP changed from {original_gdp} to {test_gdp}")
                    
                    # Verify change
                    verify_response = session.get(urljoin(BASE_URL, "/admin/api/indicator/13"))
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        if verify_data.get('success'):
                            updated_gdp = verify_data['indicator'].get('gdp_growth_rate')
                            if abs(updated_gdp - test_gdp) < 0.0001:
                                print("  ✓ Change verified in database")
                                
                                # Restore original
                                restore_data = edit_data.copy()
                                restore_data['gdp_growth_rate'] = original_gdp
                                restore_response = session.put(
                                    urljoin(BASE_URL, "/admin/api/indicator/13"),
                                    json=restore_data,
                                    headers={'Content-Type': 'application/json'}
                                )
                                if restore_response.status_code == 200:
                                    print("  ✓ Original value restored")
                                    return all_present
                            else:
                                print(f"  ✗ Change not verified: expected {test_gdp}, got {updated_gdp}")
                        else:
                            print("  ✗ Verification failed")
                    else:
                        print("  ✗ Verification request failed")
                else:
                    print(f"  ✗ Edit failed: {edit_result.get('error')}")
            else:
                print(f"  ✗ Edit API failed: {edit_response.status_code}")
        else:
            print(f"  ✗ Could not get current data: {current_data.get('error')}")
    else:
        print(f"  ✗ Could not retrieve current data: {current_response.status_code}")
    
    return False

if __name__ == '__main__':
    success = test_bootstrap_modal_fix()
    
    print("\n" + "=" * 50)
    print("BOOTSTRAP 5 MODAL FIX TEST RESULTS")
    print("=" * 50)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✓ Bootstrap 5 modal syntax implemented")
        print("✓ View functionality working")
        print("✓ Edit functionality working")
        print("✓ Data persistence confirmed")
        print("\nThe edit functionality should now work in manual testing.")
        print("Try clicking the eye and edit icons in the Economic Indicators table.")
    else:
        print("❌ TESTS FAILED")
        print("Manual testing may still have issues.")