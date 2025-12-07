#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Tests all major features of the Xcellar API
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
PASS = "✓ PASS"
FAIL = "✗ FAIL"

class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_header(text):
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.NC}\n")

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}{PASS}{Colors.NC}" if passed else f"{Colors.RED}{FAIL}{Colors.NC}"
    print(f"  {status} - {name}")
    if details:
        print(f"      {details}")

def test_endpoint(method, endpoint, name, data=None, headers=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers or {})
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers or {})
        elif method == "PATCH":
            response = requests.patch(url, json=data, headers=headers or {})
        elif method == "DELETE":
            response = requests.delete(url, headers=headers or {})
        
        passed = response.status_code == expected_status
        details = f"HTTP {response.status_code}"
        
        if passed:
            try:
                result = response.json()
                if isinstance(result, dict) and 'status' in result:
                    details += f" - Status: {result.get('status')}"
            except:
                pass
        
        print_test(name, passed, details)
        
        if not passed:
            try:
                error = response.json()
                print(f"      Error: {error.get('error', 'Unknown error')}")
            except:
                print(f"      Response: {response.text[:100]}")
        
        return response, passed
    
    except Exception as e:
        print_test(name, False, f"Exception: {str(e)}")
        return None, False

def main():
    print(f"{Colors.BLUE}")
    print("="*60)
    print("  XCELLAR API - COMPREHENSIVE FEATURE TEST")
    print("="*60)
    print(f"{Colors.NC}")
    
    results = {"passed": 0, "failed": 0}
    user_token = None
    courier_token = None
    user_email = f"testuser{int(time.time())}@example.com"
    courier_email = f"courier{int(time.time())}@example.com"
    
    # 1. Health Check
    print_header("1. Health Check")
    resp, passed = test_endpoint("GET", "/health/", "Health Check")
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # 2. Marketplace - Public Endpoints
    print_header("2. Marketplace - Public Endpoints")
    
    resp, passed = test_endpoint("GET", "/marketplace/categories/", "List Categories")
    if passed: results["passed"] += 1
    else: results["failed"] += 1
    
    resp, passed = test_endpoint("GET", "/marketplace/stores/", "List Stores")
    if passed: results["passed"] += 1
    else: results["failed"] += 1
    
    resp, passed = test_endpoint("GET", "/marketplace/products/", "List Products")
    if passed: results["passed"] += 1
    else: results["failed"] += 1
    
    # 3. User Registration & Authentication
    print_header("3. User Registration & Authentication")
    
    user_data = {
        "email": user_email,
        "phone_number": "+1234567890",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    resp, passed = test_endpoint("POST", "/auth/register/user/", "Register User", data=user_data, expected_status=201)
    if passed:
        results["passed"] += 1
        if resp:
            try:
                data = resp.json()
                user_token = data.get("access")
                if user_token:
                    print(f"      User token obtained: {user_token[:30]}...")
            except:
                pass
    else:
        results["failed"] += 1
    
    # Try login if registration didn't return token
    if not user_token:
        login_data = {"email": user_email, "password": "TestPass123!"}
        resp, passed = test_endpoint("POST", "/auth/login/", "User Login", data=login_data)
        if passed and resp:
            try:
                data = resp.json()
                user_token = data.get("access")
                if user_token:
                    print(f"      User token obtained: {user_token[:30]}...")
                    results["passed"] += 1
            except:
                results["failed"] += 1
    
    # 4. Courier Registration
    print_header("4. Courier Registration")
    
    courier_data = {
        "email": courier_email,
        "phone_number": "+1234567891",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "first_name": "Test",
        "last_name": "Courier"
    }
    
    resp, passed = test_endpoint("POST", "/auth/register/courier/", "Register Courier", data=courier_data, expected_status=201)
    if passed:
        results["passed"] += 1
        if resp:
            try:
                data = resp.json()
                courier_token = data.get("access")
                if courier_token:
                    print(f"      Courier token obtained: {courier_token[:30]}...")
            except:
                pass
    else:
        results["failed"] += 1
    
    # 5. Marketplace - Authenticated Endpoints (User)
    if user_token:
        print_header("5. Marketplace - Authenticated Endpoints (User)")
        headers = {"Authorization": f"Bearer {user_token}"}
        
        resp, passed = test_endpoint("GET", "/marketplace/cart/", "Get Cart", headers=headers)
        if passed: results["passed"] += 1
        else: results["failed"] += 1
    
    # 6. Orders - User Endpoints
    if user_token:
        print_header("6. Orders - User Endpoints")
        headers = {"Authorization": f"Bearer {user_token}"}
        
        resp, passed = test_endpoint("GET", "/orders/list/", "List Orders (User)", headers=headers)
        if passed: results["passed"] += 1
        else: results["failed"] += 1
    
    # 7. Orders - Courier Endpoints
    if courier_token:
        print_header("7. Orders - Courier Endpoints")
        headers = {"Authorization": f"Bearer {courier_token}"}
        
        resp, passed = test_endpoint("GET", "/orders/available/", "Available Orders (Courier)", headers=headers)
        if passed: results["passed"] += 1
        else: results["failed"] += 1
    
    # 8. Help Endpoints
    print_header("8. Help Endpoints")
    
    help_data = {
        "subject": "Test Help Request",
        "message": "This is a test help request to verify the endpoint is working correctly.",
        "category": "GENERAL",
        "priority": "NORMAL"
    }
    
    resp, passed = test_endpoint("POST", "/help/request/", "Submit Help Request", data=help_data, expected_status=201)
    if passed: results["passed"] += 1
    else: results["failed"] += 1
    
    # 9. FAQ Endpoints
    print_header("9. FAQ Endpoints")
    
    resp, passed = test_endpoint("GET", "/faq/", "List FAQs")
    if passed: results["passed"] += 1
    else: results["failed"] += 1
    
    # 10. Core Endpoints
    print_header("10. Core Endpoints")
    
    resp, passed = test_endpoint("GET", "/core/states/", "List States")
    if passed: results["passed"] += 1
    else: results["failed"] += 1
    
    # Summary
    print_header("TEST SUMMARY")
    total = results["passed"] + results["failed"]
    print(f"  {Colors.GREEN}Passed: {results['passed']}{Colors.NC}")
    print(f"  {Colors.RED}Failed: {results['failed']}{Colors.NC}")
    print(f"  Total: {total}")
    print(f"\n  Success Rate: {(results['passed']/total*100):.1f}%")
    
    if results["failed"] == 0:
        print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.NC}\n")
        return 0
    else:
        print(f"\n{Colors.RED}❌ Some tests failed. Please check the output above.{Colors.NC}\n")
        return 1

if __name__ == "__main__":
    exit(main())



