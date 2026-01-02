#!/bin/bash
set -e

echo "🧪 Testing JMeter Infrastructure Fix"
echo "===================================="

# Cleanup
docker-compose down -v 2>/dev/null || true
sleep 2

echo "📦 Starting PostgreSQL and FraiseQL..."
docker-compose up -d postgres fraiseql
sleep 20

echo "🔍 Checking if services are ready..."
curl -s http://localhost:4000/health || echo "Health check failed"

echo "📝 Checking database schema..."
docker-compose exec -T postgres psql -U benchmark -d fraiseql_benchmark -c "SELECT COUNT(*) as user_count FROM benchmark.tb_user;"

echo "🚀 Running simplified JMeter test (1 thread, 10 loops)..."
cd /home/lionel/code/fraiseql-performance-assessment

# Run JMeter from the project root directory to resolve relative paths
jmeter -n \
  -t tests/perf/jmeter/comparative-test-plan-fraiseql.jmx \
  -l test_results.jtl \
  -e -o test_results_html \
  -Jthreads=1 \
  -Jloops=10 \
  -Jrampup=1 \
  -Jframework.port=4000 \
  2>&1 | tail -50

echo ""
echo "✅ Test completed"
echo "📊 Results file: test_results.jtl"
echo ""
echo "Sample results:"
head -5 test_results.jtl

echo ""
echo "🛑 Cleaning up..."
docker-compose down -v
