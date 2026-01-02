#!/bin/bash

################################################################################
# FraiseQL Performance Assessment - Comprehensive Benchmark Runner
#
# Runs a complete, unattended performance test suite across all GraphQL frameworks
# with multiple workloads and load configurations.
#
# Usage:
#   ./run-comprehensive-benchmark.sh [--quick] [--medium] [--full]
#
# Options:
#   --quick    Run quick baseline tests (20 mins total)
#   --medium   Run moderate load tests (1 hour total) [DEFAULT]
#   --full     Run comprehensive stress tests (2+ hours)
#   --workload NAME   Run only specific workload (simple, aggregation, etc)
#   --framework NAME  Run only specific framework (fraiseql, strawberry, etc)
#   --config CONFIG   Run only specific config (smoke, small, medium, large)
#
# Examples:
#   ./run-comprehensive-benchmark.sh --quick
#   ./run-comprehensive-benchmark.sh --full --framework strawberry
#   ./run-comprehensive-benchmark.sh --workload simple --config medium
#
################################################################################

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/tests/perf/scripts"

# Default to medium testing
TEST_PROFILE="medium"
SPECIFIC_WORKLOAD=""
SPECIFIC_FRAMEWORK=""
SPECIFIC_CONFIG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --quick)
      TEST_PROFILE="quick"
      shift
      ;;
    --medium)
      TEST_PROFILE="medium"
      shift
      ;;
    --full)
      TEST_PROFILE="full"
      shift
      ;;
    --workload)
      SPECIFIC_WORKLOAD="$2"
      shift 2
      ;;
    --framework)
      SPECIFIC_FRAMEWORK="$2"
      shift 2
      ;;
    --config)
      SPECIFIC_CONFIG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Define test matrices based on profile
case "$TEST_PROFILE" in
   quick)
     echo "🏃 QUICK Profile - Baseline Tests (45 mins for 32 frameworks)"
     WORKLOADS=(simple)
     # All 32 frameworks
     FRAMEWORKS=(fraiseql strawberry graphene fastapi-rest flask-rest strawberry-orm-naive fastapi-orm-naive apollo apollo-orm express-rest express-orm apollo-orm-naive express-orm-naive spring-boot spring-boot-orm spring-boot-orm-naive go-graphql-go gin-rest go-gqlgen go-gqlgen-alt gqlgen-orm-naive gin-orm-naive async-graphql actix-web-rest csharp-dotnet php-laravel ruby-rails hasura)
     CONFIGS=(smoke)
     ;;
   medium)
     echo "⚡ MEDIUM Profile - Standard Tests (2.5-3 hours for 32 frameworks)"
     WORKLOADS=(simple parameterized aggregation)
     # All 32 frameworks
     FRAMEWORKS=(fraiseql strawberry graphene fastapi-rest flask-rest strawberry-orm-naive fastapi-orm-naive apollo apollo-orm express-rest express-orm apollo-orm-naive express-orm-naive spring-boot spring-boot-orm spring-boot-orm-naive go-graphql-go gin-rest go-gqlgen go-gqlgen-alt gqlgen-orm-naive gin-orm-naive async-graphql actix-web-rest csharp-dotnet php-laravel ruby-rails hasura)
     CONFIGS=(smoke small medium)
     ;;
   full)
     echo "🚀 FULL Profile - Comprehensive Stress Tests (8-10 hours for 32 frameworks)"
     WORKLOADS=(simple parameterized aggregation pagination fulltext deep-traversal mutations mixed)
     # All 32 frameworks
     FRAMEWORKS=(fraiseql strawberry graphene fastapi-rest flask-rest strawberry-orm-naive fastapi-orm-naive apollo apollo-orm express-rest express-orm apollo-orm-naive express-orm-naive spring-boot spring-boot-orm spring-boot-orm-naive go-graphql-go gin-rest go-gqlgen go-gqlgen-alt gqlgen-orm-naive gin-orm-naive async-graphql actix-web-rest csharp-dotnet php-laravel ruby-rails hasura)
     CONFIGS=(smoke small medium large)
    ;;
esac

# Allow command-line overrides
if [ -n "$SPECIFIC_WORKLOAD" ]; then
  WORKLOADS=($SPECIFIC_WORKLOAD)
fi
if [ -n "$SPECIFIC_FRAMEWORK" ]; then
  FRAMEWORKS=($SPECIFIC_FRAMEWORK)
fi
if [ -n "$SPECIFIC_CONFIG" ]; then
  CONFIGS=($SPECIFIC_CONFIG)
fi

# Display test plan
echo ""
echo "╔═════════════════════════════════════════════════════════════════════════════╗"
echo "║     FraiseQL Performance Assessment - Comprehensive Benchmark Suite        ║"
echo "╚═════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Test Configuration:"
echo "  Profile:    $TEST_PROFILE"
echo "  Workloads:  $WORKLOADS"
echo "  Frameworks: ${FRAMEWORKS[*]}"
echo "  Configs:    $CONFIGS"
echo ""

# Calculate total tests
TOTAL_TESTS=0
for workload in "${WORKLOADS[@]}"; do
  for framework in "${FRAMEWORKS[@]}"; do
    for config in "${CONFIGS[@]}"; do
      ((TOTAL_TESTS++))
    done
  done
done

echo "  Total Tests: $TOTAL_TESTS"
echo "  Estimated Duration: ~$((TOTAL_TESTS * 5)) minutes"
echo ""

# Verify containers are running
echo "✓ Verifying framework containers..."
for framework in "${FRAMEWORKS[@]}"; do
  PORT=""
  HEALTH_ENDPOINT="/health"
  HEALTH_METHOD="GET"

  # Port mapping for all 32 frameworks (from FRAMEWORK_MAPPING.md)
  case $framework in
    # Python
    fraiseql) PORT="4000" ;;
    strawberry) PORT="8011" ;;
    graphene) PORT="8002" ;;
    fastapi-rest) PORT="8003" ;;
    flask-rest) PORT="8004" ;;
    strawberry-orm-naive) PORT="8019" ;;
    fastapi-orm-naive) PORT="8020" ;;
    # Node.js
    apollo) PORT="4001"; HEALTH_METHOD="POST"; HEALTH_ENDPOINT="/graphql" ;;
    apollo-orm) PORT="4005" ;;
    express-rest) PORT="8005" ;;
    express-orm) PORT="8007" ;;
    apollo-orm-naive) PORT="8021" ;;
    express-orm-naive) PORT="8022" ;;
    # Java
    spring-boot) PORT="8010"; HEALTH_ENDPOINT="/actuator/health" ;;
    spring-boot-orm) PORT="8013"; HEALTH_ENDPOINT="/actuator/health" ;;
    spring-boot-orm-naive) PORT="8014"; HEALTH_ENDPOINT="/actuator/health" ;;
    # Go
    go-graphql-go) PORT="8008" ;;
    gin-rest) PORT="8006" ;;
    go-gqlgen) PORT="4010" ;;
    go-gqlgen-alt) PORT="4003" ;;
    gqlgen-orm-naive) PORT="8023" ;;
    gin-orm-naive) PORT="8024" ;;
    # Rust
    async-graphql) PORT="8016" ;;
    actix-web-rest) PORT="8015" ;;
    # C#/.NET
    csharp-dotnet) PORT="8025" ;;
    # PHP
    php-laravel) PORT="8009"; HEALTH_ENDPOINT="/api/health" ;;
    # Ruby
    ruby-rails) PORT="8012"; HEALTH_ENDPOINT="/api/health" ;;
    # Managed GraphQL
    hasura) PORT="8081"; HEALTH_ENDPOINT="/healthz" ;;
  esac

  # Skip if no port found
  if [ -z "$PORT" ]; then
    echo "  ⚠️  $framework - Unknown framework (no port mapping)"
    continue
  fi

  # Health check with appropriate method and endpoint
  if [ "$HEALTH_METHOD" = "POST" ]; then
    # Apollo Server requires POST with GraphQL query
    HEALTH=$(curl -s -X POST -H "Content-Type: application/json" -d '{"query":"{__typename}"}' -o /dev/null -w "%{http_code}" "http://localhost:${PORT}${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")
  else
    # Standard GET request
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")
  fi

  if [ "$HEALTH" != "200" ]; then
    echo "  ❌ $framework (port $PORT, endpoint $HEALTH_ENDPOINT) - Health: $HEALTH"
    exit 1
  else
    echo "  ✅ $framework (port $PORT) - Healthy"
  fi
done
echo ""

# Create master results directory
MASTER_RESULTS_DIR="../results/benchmark_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$MASTER_RESULTS_DIR"
echo "📂 Results Directory: $MASTER_RESULTS_DIR"
echo ""

# Run tests
CURRENT_TEST=0
echo "╔═════════════════════════════════════════════════════════════════════════════╗"
echo "║                          Starting Benchmark Suite                           ║"
echo "╚═════════════════════════════════════════════════════════════════════════════╝"
echo ""

START_TIME=$(date +%s)
FAILED_TESTS=()

for workload in "${WORKLOADS[@]}"; do
  for framework in "${FRAMEWORKS[@]}"; do
    for config in "${CONFIGS[@]}"; do
      ((CURRENT_TEST++))

      echo "[$CURRENT_TEST/$TOTAL_TESTS] Running: $workload / $framework / $config"

      # Run test
      if ./run-test.sh "$workload" "$framework" "$config" 2>&1 | tee -a "$MASTER_RESULTS_DIR/benchmark.log"; then
        echo "  ✅ PASS"
      else
        echo "  ❌ FAIL"
        FAILED_TESTS+=("$workload / $framework / $config")
      fi
      echo ""
    done
  done
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MINS=$((DURATION / 60))
DURATION_SECS=$((DURATION % 60))

# Generate summary report
echo ""
echo "╔═════════════════════════════════════════════════════════════════════════════╗"
echo "║                          Benchmark Suite Complete                          ║"
echo "╚═════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📈 Summary:"
echo "  Total Tests:    $TOTAL_TESTS"
echo "  Passed:         $((TOTAL_TESTS - ${#FAILED_TESTS[@]}))"
echo "  Failed:         ${#FAILED_TESTS[@]}"
echo "  Duration:       ${DURATION_MINS}m ${DURATION_SECS}s"
echo ""

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
  echo "❌ Failed Tests:"
  for test in "${FAILED_TESTS[@]}"; do
    echo "  - $test"
  done
  echo ""
fi

echo "📂 Results Location: $MASTER_RESULTS_DIR"
echo ""

# Create analysis script reference
cat > "$MASTER_RESULTS_DIR/ANALYSIS_GUIDE.md" << 'EOF'
# Performance Analysis Guide

## Analyzing Results

### 1. View HTML Reports
Each test generates an HTML report. To view:
```bash
# Find and open any result's HTML report
find . -name "index.html" -path "*/html/*" | head -1 | xargs firefox
```

### 2. Extract Summary Statistics
```bash
# Generate CSV summary from all results
python3 ../scripts/analyze-results.py . > summary.csv
```

### 3. Compare Frameworks
Use the generated HTML reports to compare:
- Response times (min, avg, max, P95, P99)
- Throughput (requests per second)
- Error rates
- Memory usage (if monitoring enabled)

### 4. Key Metrics to Look For

**Response Time**:
- Lower is better
- P95 and P99 are more important than average for user experience

**Throughput**:
- Requests per second successfully processed
- Higher is better under same load

**Error Rate**:
- Should be 0% for normal tests
- Check for timeouts and connection issues

**Resource Usage**:
- CPU utilization
- Memory growth (shouldn't grow unbounded)
- Database connection pool utilization

## Interpreting Load Levels

- **smoke**: Validation only (1 thread, quick)
- **small**: Light load (5 threads, 30 seconds)
- **medium**: Moderate load (20 threads, 60 seconds)
- **large**: Heavy load (100 threads, 5 minutes)

## Workload Types

- **simple**: Basic single-level queries
- **parameterized**: Queries with parameters
- **aggregation**: Count/sum/group-by operations
- **pagination**: Cursor-based pagination
- **fulltext**: Text search queries
- **deep-traversal**: Multi-level nested queries
- **mutations**: Write operations
- **mixed**: Realistic mix of operations

## Performance Expectations (ORM-Refactored)

Baseline from smoke tests:
- FraiseQL: 13ms
- Strawberry: 11ms
- Graphene: 6ms
- Apollo: 14ms
- gqlgen: 11ms

Under load (small config), expect:
- Slight increase in response times (15-20ms)
- 95th percentile 20-30ms
- 99th percentile 30-50ms
- Error rate < 1%

## Common Issues & Solutions

### High Error Rate
- Check database connection limits
- Verify connection pool settings
- Look for database timeouts in logs

### Increasing Response Times
- Database is hitting limits (check CPU/memory)
- Connection pool exhaustion
- Network saturation

### Inconsistent Results
- Other processes using system resources
- Database warm-up time needed
- Check for GC pauses in application logs
EOF

cat "$MASTER_RESULTS_DIR/ANALYSIS_GUIDE.md"

echo ""
echo "📚 Analysis guide created: $MASTER_RESULTS_DIR/ANALYSIS_GUIDE.md"
echo ""
echo "✅ Benchmark complete! Check results directory for detailed analysis."
echo ""
