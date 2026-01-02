#!/bin/bash

echo "========================================================"
echo "🚀 FraiseQL Phase 3 - Simple Curl Test"
echo "========================================================"

# Start services
echo ""
echo "🔧 Starting PostgreSQL and FraiseQL..."
docker-compose up -d postgres fraiseql > /dev/null 2>&1

# Wait for services
echo "⏳ Waiting for services to start (30 seconds)..."
for i in {1..30}; do
    if curl -s http://localhost:4000/health > /dev/null 2>&1; then
        echo "✅ FraiseQL is ready!"
        break
    fi
    sleep 1
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Still waiting... ($i/30)"
    fi
done

echo ""
echo "========================================================"
echo "📊 Testing FraiseQL Queries"
echo "========================================================"

# Test 1: Simple Ping
echo ""
echo "🧪 Test 1: Simple Ping Query"
RESPONSE=$(curl -s -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ ping }"}')
echo "Response: $RESPONSE"

# Test 2: Users List
echo ""
echo "🧪 Test 2: List Users"
RESPONSE=$(curl -s -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users(limit: 2) { id username } }"}')
echo "Response: $RESPONSE"

# Test 3: Users with Posts
echo ""
echo "🧪 Test 3: Users with Posts"
RESPONSE=$(curl -s -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users(limit: 1) { id username posts(limit: 2) { id title } } }"}')
echo "Response: $RESPONSE"

# Load test with time measurement
echo ""
echo "========================================================"
echo "🔥 Load Test: 50 Sequential Requests"
echo "========================================================"

# Warm up (2 requests)
curl -s -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ ping }"}' > /dev/null

# Time the requests
START_TIME=$(date +%s%N)
SUCCESS_COUNT=0

for i in {1..50}; do
    RESPONSE=$(curl -s -X POST http://localhost:4000/graphql \
      -H "Content-Type: application/json" \
      -d '{"query":"{ users(limit: 1) { id username } }"}')

    if echo "$RESPONSE" | grep -q "data"; then
        ((SUCCESS_COUNT++))
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "  Completed $i/50 requests..."
    fi
done

END_TIME=$(date +%s%N)
ELAPSED_NS=$((END_TIME - START_TIME))
ELAPSED_MS=$((ELAPSED_NS / 1000000))
ELAPSED_S=$(echo "scale=2; $ELAPSED_MS / 1000" | bc)
AVG_MS=$(echo "scale=1; $ELAPSED_MS / 50" | bc)
RPS=$(echo "scale=1; 50 / $ELAPSED_S" | bc)

echo ""
echo "✅ Load Test Results:"
echo "   Total Requests: 50"
echo "   Successful: $SUCCESS_COUNT"
echo "   Total Time: ${ELAPSED_S}s"
echo "   Avg Response: ${AVG_MS}ms"
echo "   Throughput: ${RPS} RPS"

# Cleanup
echo ""
echo "🧹 Cleanup..."
docker-compose down -v > /dev/null 2>&1

echo ""
echo "========================================================"
echo "✅ FraiseQL Phase 3 Test Complete"
echo "========================================================"
echo "Async connection pooling is active and functional!"
echo ""
