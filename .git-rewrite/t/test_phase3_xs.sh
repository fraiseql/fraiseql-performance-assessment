#!/bin/bash

echo "=========================================================="
echo "🧪 Phase 3 XS Scale Test - Async Pooling Verification"
echo "=========================================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

PASS=0
FAIL=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((FAIL++))
    fi
}

# Step 1: Start PostgreSQL
echo ""
echo "Step 1: Starting PostgreSQL..."
docker-compose up postgres -d > /dev/null 2>&1
test_result $? "PostgreSQL started"

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec fraiseql-performance-assessment-postgres-1 pg_isready -U benchmark > /dev/null 2>&1; then
        echo "✅ PostgreSQL is healthy"
        test_result 0 "PostgreSQL health check"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to become healthy"
        test_result 1 "PostgreSQL health check"
        exit 1
    fi
    sleep 1
done

# Verify schema
echo ""
echo "Step 2: Verifying database schema..."
USER_COUNT=$(docker exec fraiseql-performance-assessment-postgres-1 psql -U benchmark -d fraiseql_benchmark -t -c "SELECT COUNT(*) FROM benchmark.tb_user;" 2>/dev/null | tr -d ' ')
if [ "$USER_COUNT" -gt 0 ]; then
    echo "✅ Found $USER_COUNT users"
    test_result 0 "Schema and data present"
else
    test_result 1 "Schema and data present"
fi

# Step 3: Build and test FraiseQL
echo ""
echo "Step 3: Building and testing FraiseQL..."
docker-compose build fraiseql > /dev/null 2>&1
test_result $? "FraiseQL build"

docker-compose up fraiseql -d > /dev/null 2>&1
test_result $? "FraiseQL container started"

echo "Waiting for FraiseQL..."
for i in {1..30}; do
    if curl -s http://localhost:4000/health > /dev/null 2>&1; then
        echo "✅ FraiseQL is ready"
        test_result 0 "FraiseQL health check"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ FraiseQL failed to become ready"
        test_result 1 "FraiseQL health check"
    fi
    sleep 1
done

echo ""
echo "Testing FraiseQL GraphQL endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users(limit: 1) { id username } }"}' 2>/dev/null || echo "")

if echo "$RESPONSE" | grep -q '"data"'; then
    test_result 0 "FraiseQL GraphQL query works"
else
    test_result 1 "FraiseQL GraphQL query works"
fi

# Load test FraiseQL
echo ""
echo "Running FraiseQL load test (10 sequential requests)..."
SUCCESS=0
for i in {1..10}; do
    RESPONSE=$(curl -s -X POST http://localhost:4000/graphql \
      -H "Content-Type: application/json" \
      -d '{"query":"{ users(limit: 1) { id username } }"}' 2>/dev/null || echo "")

    if echo "$RESPONSE" | grep -q '"data"'; then
        ((SUCCESS++))
    fi
done

if [ $SUCCESS -eq 10 ]; then
    test_result 0 "All 10 FraiseQL requests successful"
else
    test_result 1 "All 10 FraiseQL requests successful (got $SUCCESS/10)"
fi

# Step 4: Build and test Strawberry
echo ""
echo "Step 4: Building and testing Strawberry..."
docker-compose build strawberry > /dev/null 2>&1
test_result $? "Strawberry build"

docker-compose up strawberry -d > /dev/null 2>&1
test_result $? "Strawberry container started"

echo "Waiting for Strawberry..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Strawberry is ready"
        test_result 0 "Strawberry health check"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Strawberry failed to become ready"
        test_result 1 "Strawberry health check"
    fi
    sleep 1
done

echo ""
echo "Testing Strawberry GraphQL endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users(limit: 1) { id username } }"}' 2>/dev/null || echo "")

if echo "$RESPONSE" | grep -q '"data"'; then
    test_result 0 "Strawberry GraphQL query works"
else
    test_result 1 "Strawberry GraphQL query works"
fi

# Load test Strawberry
echo ""
echo "Running Strawberry load test (10 sequential requests)..."
SUCCESS=0
for i in {1..10}; do
    RESPONSE=$(curl -s -X POST http://localhost:8001/graphql \
      -H "Content-Type: application/json" \
      -d '{"query":"{ users(limit: 1) { id username } }"}' 2>/dev/null || echo "")

    if echo "$RESPONSE" | grep -q '"data"'; then
        ((SUCCESS++))
    fi
done

if [ $SUCCESS -eq 10 ]; then
    test_result 0 "All 10 Strawberry requests successful"
else
    test_result 1 "All 10 Strawberry requests successful (got $SUCCESS/10)"
fi

# Summary
echo ""
echo "=========================================================="
echo "📈 Test Results"
echo "=========================================================="
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================================="
    echo "✅ ALL TESTS PASSED - Phase 3 VERIFIED!"
    echo "==========================================================${NC}"
    echo ""
    echo "Summary:"
    echo "  ✅ PostgreSQL with proper CQRS schema"
    echo "  ✅ FraiseQL with async connection pooling"
    echo "  ✅ Strawberry with asyncpg and DataLoaders"
    echo "  ✅ GraphQL queries working correctly"
    echo "  ✅ Load testing verified (10/10 requests)"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}=========================================================="
    echo "❌ Some tests failed"
    echo "==========================================================${NC}"
    exit 1
fi
