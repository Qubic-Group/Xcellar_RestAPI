#!/bin/bash

# Comprehensive API Testing Script for Xcellar
# This script tests all major features of the API

BASE_URL="http://localhost:8000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to make API calls
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    local headers=$5
    
    echo -e "\n${YELLOW}Testing: $description${NC}"
    echo "  $method $endpoint"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" $headers)
    elif [ "$method" == "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" $headers)
    elif [ "$method" == "PATCH" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" $headers)
    elif [ "$method" == "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL$endpoint" $headers)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        echo "$body" | python3 -m json.tool 2>/dev/null | head -10 || echo "$body" | head -5
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "$body"
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo "$body" | head -5
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "$body"
    fi
}

echo "=========================================="
echo "Xcellar API Comprehensive Test Suite"
echo "=========================================="

# 1. Health Check
echo -e "\n${YELLOW}=== 1. Health Check ===${NC}"
test_endpoint "GET" "/health/" "Health Check" "" ""

# 2. Register Regular User
echo -e "\n${YELLOW}=== 2. User Registration ===${NC}"
USER_EMAIL="testuser$(date +%s)@example.com"
USER_DATA="{
    \"email\": \"$USER_EMAIL\",
    \"phone_number\": \"+1234567890\",
    \"password\": \"TestPass123!\",
    \"password_confirm\": \"TestPass123!\",
    \"first_name\": \"Test\",
    \"last_name\": \"User\"
}"
test_endpoint "POST" "/auth/register/user/" "Register Regular User" "$USER_DATA" ""

# Extract user token from response
USER_TOKEN=$(curl -s -X POST "$BASE_URL/auth/register/user/" \
    -H "Content-Type: application/json" \
    -d "$USER_DATA" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null)

if [ -z "$USER_TOKEN" ]; then
    # Try login instead
    USER_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$USER_EMAIL\", \"password\": \"TestPass123!\"}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null)
fi

# 3. Register Courier
echo -e "\n${YELLOW}=== 3. Courier Registration ===${NC}"
COURIER_EMAIL="courier$(date +%s)@example.com"
COURIER_DATA="{
    \"email\": \"$COURIER_EMAIL\",
    \"phone_number\": \"+1234567891\",
    \"password\": \"TestPass123!\",
    \"password_confirm\": \"TestPass123!\",
    \"first_name\": \"Test\",
    \"last_name\": \"Courier\"
}"
test_endpoint "POST" "/auth/register/courier/" "Register Courier" "$COURIER_DATA" ""

# Extract courier token
COURIER_TOKEN=$(curl -s -X POST "$BASE_URL/auth/register/courier/" \
    -H "Content-Type: application/json" \
    -d "$COURIER_DATA" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null)

if [ -z "$COURIER_TOKEN" ]; then
    COURIER_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$COURIER_EMAIL\", \"password\": \"TestPass123!\"}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null)
fi

USER_AUTH_HEADER="-H \"Authorization: Bearer $USER_TOKEN\""
COURIER_AUTH_HEADER="-H \"Authorization: Bearer $COURIER_TOKEN\""

# 4. Marketplace Endpoints
echo -e "\n${YELLOW}=== 4. Marketplace Endpoints ===${NC}"
test_endpoint "GET" "/marketplace/categories/" "List Categories" "" ""
test_endpoint "GET" "/marketplace/stores/" "List Stores" "" ""
test_endpoint "GET" "/marketplace/products/" "List Products" "" ""
test_endpoint "GET" "/marketplace/cart/" "Get Cart" "" "$USER_AUTH_HEADER"

# 5. Orders Endpoints (User)
echo -e "\n${YELLOW}=== 5. Orders Endpoints (User) ===${NC}"
test_endpoint "GET" "/orders/list/" "List Orders (User)" "" "$USER_AUTH_HEADER"

# 6. Orders Endpoints (Courier)
echo -e "\n${YELLOW}=== 6. Orders Endpoints (Courier) ===${NC}"
test_endpoint "GET" "/orders/available/" "Available Orders (Courier)" "" "$COURIER_AUTH_HEADER"

# 7. Help Endpoints
echo -e "\n${YELLOW}=== 7. Help Endpoints ===${NC}"
HELP_DATA="{
    \"subject\": \"Test Help Request\",
    \"message\": \"This is a test help request to verify the endpoint is working correctly.\",
    \"category\": \"GENERAL\",
    \"priority\": \"NORMAL\"
}"
test_endpoint "POST" "/help/request/" "Submit Help Request" "$HELP_DATA" ""

# 8. FAQ Endpoints
echo -e "\n${YELLOW}=== 8. FAQ Endpoints ===${NC}"
test_endpoint "GET" "/faq/" "List FAQs" "" ""

# 9. Core Endpoints
echo -e "\n${YELLOW}=== 9. Core Endpoints ===${NC}"
test_endpoint "GET" "/core/states/" "List States" "" ""

# Summary
echo -e "\n=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "Total: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
fi



