#!/usr/bin/env python3
"""
Debug user issue with edit functionality
"""

import os
import requests
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@ethiopia-economic.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

def debug_user_experience():
    """Debug the actual user experience step by step"""
    
    print("DEBUGGING USER EXPERIENCE")
    print("=" * 50)
    
    session = requests.Session()
    
    # Step 1: Login
    print("Step 1: Attempting login...")
    login_data = {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD}
    login_response = session.post(urljoin(BASE_URL, "/auth/login"), data=login_data, allow_redirects=True)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return
    
    print("Login successful")
    
    # Step 2: Check indicators page content
    print("\nStep 2: Checking indicators page...")
    indicators_page = session.get(urljoin(BASE_URL, "/admin/data/economic-indicators"))
    
    if indicators_page.status_code != 200:
        print(f"Indicators page failed: {indicators_page.status_code}")
        return
    
    content = indicators_page.text
    
    # Debug: Check specific elements
    print("Checking for key elements:")
    
    checks = [
        ("viewIndicator(", "View function"),
        ("editIndicator(", "Edit function"), 
        ("btn-outline-primary", "View button"),
        ("btn-outline-secondary", "Edit button"),
        ("fas fa-eye", "Eye icon"),
        ("fas fa-edit", "Edit icon"),
        ("modal fade", "Modal dialogs"),
        ("editIndicatorModal", "Edit modal"),
        ("viewIndicatorModal", "View modal")
    ]
    
    for check, description in checks:
        if check in content:
            print(f"  ✓ {description}: Found")
        else:
            print(f"  ✗ {description}: MISSING")
    
    # Step 3: Check if data is present
    print("\nStep 3: Checking for data in table...")
    if "<tbody>" in content and "</tbody>" in content:
        tbody_start = content.find("<tbody>")
        tbody_end = content.find("</tbody>")
        tbody_content = content[tbody_start:tbody_end]
        
        if "<tr>" in tbody_content:
            print("  ✓ Table has data rows")
        else:
            print("  ✗ Table appears empty")
    else:
        print("  ✗ No table body found")
    
    # Step 4: Test API endpoints directly
    print("\nStep 4: Testing API endpoints...")
    
    # Test view API
    view_response = session.get(urljoin(BASE_URL, "/admin/api/indicator/1"))
    if view_response.status_code == 200:
        try:
            view_data = view_response.json()
            if view_data.get('success'):
                print("  ✓ View API working")
            else:
                print(f"  ✗ View API error: {view_data.get('error')}")
        except:
            print("  ✗ View API returned invalid JSON")
    else:
        print(f"  ✗ View API failed: {view_response.status_code}")
    
    # Step 5: Extract and display actual HTML around buttons
    print("\nStep 5: Extracting button HTML...")
    if "btn-outline-primary" in content:
        start_idx = content.find("btn-outline-primary") - 100
        end_idx = content.find("btn-outline-primary") + 200
        button_html = content[max(0, start_idx):min(len(content), end_idx)]
        print("Button HTML context:")
        print(button_html)
    
    # Step 6: Check JavaScript errors
    print("\nStep 6: Checking JavaScript functions...")
    js_functions = ["viewIndicator", "editIndicator", "saveIndicator"]
    for func in js_functions:
        if f"function {func}" in content or f"{func}(" in content:
            print(f"  ✓ {func} function found")
        else:
            print(f"  ✗ {func} function missing")

if __name__ == '__main__':
    debug_user_experience()