#!/bin/bash

echo "🔥 Testing FraiseQL with 10 sequential requests..."
SUCCESS=0
for i in {1..10}; do
    RESPONSE=$(curl -s -X POST http://localhost:4000/graphql \
      -H "Content-Type: application/json" \
      -d '{"query":"{ users(limit: 1) { id username } }"}' 2>/dev/null || echo "")

    if echo "$RESPONSE" | grep -q '"data"'; then
        ((SUCCESS++))
    fi

    if [ $((i % 5)) -eq 0 ]; then
        echo "  Progress: $i/10"
    fi
done

echo ""
echo "✅ Results: $SUCCESS/10 successful requests"

if [ $SUCCESS -eq 10 ]; then
    echo "✅ All requests successful!"
else
    echo "⚠️  Some requests failed: $((10 - SUCCESS)) failures"
fi
