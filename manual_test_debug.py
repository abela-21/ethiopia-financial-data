#!/usr/bin/env python3
"""
Debug manual testing issues with edit functionality
"""

import requests
from urllib.parse import urljoin
import re

BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = "admin@ethiopia-economic.com"
ADMIN_PASSWORD = "EthiopiaAdmin2024!"

def extract_button_html(content):
    """Extract actual button HTML from page"""
    # Find the table body section
    tbody_match = re.search(r'<tbody>(.*?)</tbody>', content, re.DOTALL)
    if tbody_match:
        tbody = tbody_match.group(1)
        # Find button sections
        button_sections = re.findall(r'<td[^>]*>.*?<div class="btn-group[^>]*">.*?</div>.*?</td>', tbody, re.DOTALL)
        return button_sections
    return []

def check_javascript_loading(content):
    """Check if JavaScript functions are properly loaded"""
    functions_to_check = [
        'function viewIndicator',
        'function editIndicator', 
        'function saveIndicator',
        'viewIndicator(',
        'editIndicator(',
        'saveIndicator('
    ]
    
    results = {}
    for func in functions_to_check:
        results[func] = func in content
    
    return results

def debug_manual_issue():
    """Debug why manual testing isn't working"""
    
    print("DEBUGGING MANUAL EDIT FUNCTIONALITY ISSUES")
    print("=" * 60)
    
    session = requests.Session()
    
    # Login
    print("Logging in...")
    login_data = {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD}
    login_response = session.post(urljoin(BASE_URL, "/auth/login"), data=login_data, allow_redirects=True)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return
    
    # Get indicators page
    print("Fetching economic indicators page...")
    indicators_page = session.get(urljoin(BASE_URL, "/admin/data/economic-indicators"))
    
    if indicators_page.status_code != 200:
        print(f"Indicators page failed: {indicators_page.status_code}")
        return
    
    content = indicators_page.text
    
    # Check for jQuery/Bootstrap
    print("\n1. Checking JavaScript dependencies:")
    jquery_present = 'jquery' in content.lower() or '$(' in content
    bootstrap_present = 'bootstrap' in content.lower()
    print(f"   jQuery: {'✓' if jquery_present else '✗'}")
    print(f"   Bootstrap: {'✓' if bootstrap_present else '✗'}")
    
    # Check button HTML structure
    print("\n2. Extracting actual button HTML:")
    button_sections = extract_button_html(content)
    for i, section in enumerate(button_sections[:2]):  # Show first 2 for brevity
        print(f"\n   Button section {i+1}:")
        # Clean up the HTML for display
        clean_section = re.sub(r'\s+', ' ', section).strip()
        print(f"   {clean_section[:200]}...")
    
    # Check JavaScript functions
    print("\n3. Checking JavaScript function availability:")
    js_results = check_javascript_loading(content)
    for func, present in js_results.items():
        print(f"   {func}: {'✓' if present else '✗'}")
    
    # Check modal HTML
    print("\n4. Checking modal structures:")
    modals = [
        ('viewIndicatorModal', 'View modal'),
        ('editIndicatorModal', 'Edit modal'),
        ('modal-dialog', 'Modal dialog structure'),
        ('modal-content', 'Modal content structure')
    ]
    
    for modal_id, description in modals:
        present = modal_id in content
        print(f"   {description}: {'✓' if present else '✗'}")
    
    # Check for specific onclick handlers
    print("\n5. Checking onclick handlers:")
    view_onclick = re.findall(r'onclick="viewIndicator\((\d+)\)"', content)
    edit_onclick = re.findall(r'onclick="editIndicator\((\d+)\)"', content)
    print(f"   View onclick handlers found: {len(view_onclick)} (IDs: {view_onclick[:3]})")
    print(f"   Edit onclick handlers found: {len(edit_onclick)} (IDs: {edit_onclick[:3]})")
    
    # Test API endpoint directly
    print("\n6. Testing API endpoint directly:")
    if view_onclick:
        test_id = view_onclick[0]
        api_response = session.get(urljoin(BASE_URL, f"/admin/api/indicator/{test_id}"))
        print(f"   API test for ID {test_id}: {api_response.status_code}")
        if api_response.status_code == 200:
            try:
                data = api_response.json()
                print(f"   API response: {data.get('success', 'No success field')}")
            except:
                print("   API response: Invalid JSON")
    
    # Check for console errors in HTML
    print("\n7. Checking for potential JavaScript errors:")
    script_sections = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    for i, script in enumerate(script_sections):
        if 'viewIndicator' in script or 'editIndicator' in script:
            print(f"   Script section {i+1} contains edit functions")
            # Check for syntax issues
            if script.count('{') != script.count('}'):
                print("   WARNING: Unmatched braces in script")
            if script.count('(') != script.count(')'):
                print("   WARNING: Unmatched parentheses in script")
    
    # Save page content for manual inspection
    with open('debug_page_content.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n8. Full page content saved to 'debug_page_content.html' for manual inspection")
    
    print("\nDEBUG SUMMARY:")
    print("=" * 60)
    if not jquery_present:
        print("ISSUE: jQuery not detected - modals won't work")
    if not bootstrap_present:
        print("ISSUE: Bootstrap not detected - modals won't work")
    if not view_onclick:
        print("ISSUE: No view onclick handlers found")
    if not edit_onclick:
        print("ISSUE: No edit onclick handlers found")
    
    return {
        'jquery': jquery_present,
        'bootstrap': bootstrap_present,
        'view_handlers': len(view_onclick),
        'edit_handlers': len(edit_onclick),
        'js_functions': js_results
    }

if __name__ == '__main__':
    debug_manual_issue()