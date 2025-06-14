#!/usr/bin/env python3
"""
Test all data management endpoints with admin authentication
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = "admin@ethiopia-economic.com"
ADMIN_PASSWORD = "EthiopiaAdmin2024!"

def login_admin():
    """Login as admin and return session"""
    session = requests.Session()
    
    # Get login page first to establish session
    login_page = session.get(urljoin(BASE_URL, "/auth/login"))
    if login_page.status_code != 200:
        print(f"❌ Failed to access login page: {login_page.status_code}")
        return None
    
    # Attempt login
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

def test_authenticated_endpoint(session, path, description=""):
    """Test endpoint with authenticated session"""
    url = urljoin(BASE_URL, path)
    try:
        response = session.get(url, timeout=15)
        
        # Check for errors in response
        has_error = (
            'Internal Server Error' in response.text or 
            'error' in response.text.lower() or
            'exception' in response.text.lower() or
            'traceback' in response.text.lower()
        )
        
        # Check for expected content
        is_valid = (
            response.status_code == 200 and
            not has_error and
            len(response.content) > 1000  # Reasonable content size
        )
        
        status = "✅ WORKING" if is_valid else f"❌ ISSUE ({response.status_code})"
        
        return {
            'path': path,
            'status_code': response.status_code,
            'result': status,
            'description': description,
            'content_length': len(response.content),
            'has_error': has_error,
            'is_valid': is_valid
        }
    except Exception as e:
        return {
            'path': path,
            'status_code': 'ERROR',
            'result': f"❌ EXCEPTION: {str(e)}",
            'description': description,
            'content_length': 0,
            'has_error': True,
            'is_valid': False
        }

def run_authenticated_tests():
    """Test all data management endpoints with admin authentication"""
    
    print("🔐 TESTING DATA MANAGEMENT WITH ADMIN AUTHENTICATION")
    print("=" * 70)
    
    # Login as admin
    session = login_admin()
    if not session:
        print("❌ Cannot proceed without admin authentication")
        return []
    
    print()
    
    # Define endpoints to test
    endpoints = [
        ("/admin", "Admin panel main page"),
        ("/admin/manage-data", "Data management dashboard"),
        ("/admin/data/companies", "Companies data table"),
        ("/admin/data/financial", "Financial data table"),
        ("/admin/data/banks", "Banks data table"),
        ("/admin/data/research", "Research documents table"),
        ("/admin/data/economic-indicators", "Economic indicators table"),
        ("/admin/data/listed-companies", "Listed companies table"),
        ("/admin/data/users", "Users management table"),
    ]
    
    results = []
    working_count = 0
    
    print("📊 TESTING INDIVIDUAL ENDPOINTS:")
    print("-" * 70)
    
    for path, description in endpoints:
        result = test_authenticated_endpoint(session, path, description)
        results.append(result)
        
        print(f"{result['result']} {path}")
        print(f"    {description}")
        
        if result['has_error']:
            print(f"    ⚠️  Error detected in response content")
        elif result['content_length'] < 1000:
            print(f"    ⚠️  Small response size ({result['content_length']} bytes)")
        else:
            print(f"    ✅ Response size: {result['content_length']} bytes")
            
        if result['is_valid']:
            working_count += 1
            
        print()
    
    # Test data refresh endpoint
    print("🔄 TESTING DATA REFRESH FUNCTIONALITY:")
    print("-" * 70)
    
    try:
        refresh_response = session.post(
            urljoin(BASE_URL, "/admin/data/refresh"),
            timeout=30
        )
        
        if refresh_response.status_code == 200:
            try:
                refresh_data = refresh_response.json()
                if refresh_data.get('success'):
                    print("✅ Data refresh endpoint working")
                else:
                    print(f"❌ Data refresh failed: {refresh_data.get('error', 'Unknown error')}")
            except:
                print("❌ Data refresh returned invalid JSON")
        else:
            print(f"❌ Data refresh endpoint error: {refresh_response.status_code}")
    except Exception as e:
        print(f"❌ Data refresh exception: {str(e)}")
    
    print()
    
    # Summary
    print("📋 FINAL SUMMARY:")
    print("=" * 70)
    
    total_endpoints = len(results)
    print(f"Total Endpoints Tested: {total_endpoints}")
    print(f"Working Properly: {working_count}")
    print(f"Having Issues: {total_endpoints - working_count}")
    print(f"Success Rate: {(working_count/total_endpoints)*100:.1f}%")
    
    if working_count == total_endpoints:
        print("\n🎉 ALL DATA MANAGEMENT ENDPOINTS ARE WORKING PERFECTLY!")
    else:
        print(f"\n⚠️  ENDPOINTS WITH ISSUES:")
        for result in results:
            if not result['is_valid']:
                print(f"   {result['path']} - {result['description']}")
                if result['has_error']:
                    print(f"     └─ Contains errors in response")
    
    return results

if __name__ == '__main__':
    results = run_authenticated_tests()