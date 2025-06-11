#!/usr/bin/env python3
"""
Comprehensive test script for all data management endpoints
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"

def test_endpoint(path, expected_status=200, description=""):
    """Test a single endpoint and return results"""
    url = urljoin(BASE_URL, path)
    try:
        response = requests.get(url, timeout=10)
        status = "✅ PASS" if response.status_code == expected_status else f"❌ FAIL ({response.status_code})"
        return {
            'path': path,
            'status_code': response.status_code,
            'expected': expected_status,
            'result': status,
            'description': description,
            'content_length': len(response.content),
            'has_error': 'Internal Server Error' in response.text or 'error' in response.text.lower()
        }
    except Exception as e:
        return {
            'path': path,
            'status_code': 'ERROR',
            'expected': expected_status,
            'result': f"❌ EXCEPTION: {str(e)}",
            'description': description,
            'content_length': 0,
            'has_error': True
        }

def run_data_management_tests():
    """Test all data management endpoints"""
    
    print("🧪 TESTING ALL DATA MANAGEMENT ENDPOINTS")
    print("=" * 60)
    
    # Define all endpoints to test
    endpoints = [
        # Main data management page
        ("/admin/manage-data", 302, "Main data management page (requires auth)"),
        
        # Individual data view endpoints
        ("/admin/data/companies", 302, "Companies data view (requires auth)"),
        ("/admin/data/financial", 302, "Financial data view (requires auth)"),
        ("/admin/data/banks", 302, "Banks data view (requires auth)"),
        ("/admin/data/research", 302, "Research documents view (requires auth)"),
        ("/admin/data/economic-indicators", 302, "Economic indicators view (requires auth)"),
        ("/admin/data/listed-companies", 302, "Listed companies view (requires auth)"),
        ("/admin/data/users", 302, "Users management view (requires auth)"),
        
        # Other admin endpoints
        ("/admin", 302, "Admin panel (requires auth)"),
        
        # Public endpoints that should work
        ("/", 200, "Homepage (public)"),
        ("/banking", 200, "Banking sector page (public)"),
        
        # API endpoints
        ("/api/companies", 200, "Companies API (public)"),
    ]
    
    results = []
    for path, expected, description in endpoints:
        result = test_endpoint(path, expected, description)
        results.append(result)
        
        # Print immediate result
        print(f"{result['result']} {path}")
        if result['has_error'] and result['status_code'] != 302:
            print(f"    ⚠️  Warning: Error detected in response")
        if result['content_length'] < 100 and result['status_code'] == 200:
            print(f"    ⚠️  Warning: Very small response ({result['content_length']} bytes)")
    
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['status_code'] == r['expected'])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Show failed tests
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in results:
            if result['status_code'] != result['expected']:
                print(f"   {result['path']} - Expected {result['expected']}, got {result['status_code']}")
    
    # Show endpoints with errors
    error_endpoints = [r for r in results if r['has_error'] and r['status_code'] != 302]
    if error_endpoints:
        print(f"\n⚠️  ENDPOINTS WITH ERRORS:")
        for result in error_endpoints:
            print(f"   {result['path']} - {result['description']}")
    
    return results

if __name__ == '__main__':
    results = run_data_management_tests()