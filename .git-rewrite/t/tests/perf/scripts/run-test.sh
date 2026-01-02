#!/bin/bash

# FraiseQL Performance Test Runner
# Usage: ./run-test.sh <workload> <framework> <config> [duration_override]

set -e

WORKLOAD=$1
FRAMEWORK=$2
CONFIG=$3
DURATION_OVERRIDE=$4

# Validate arguments
if [ -z "$WORKLOAD" ] || [ -z "$FRAMEWORK" ] || [ -z "$CONFIG" ]; then
  echo "Usage: $0 <workload> <framework> <config> [duration_override]"
  echo ""
  echo "Workloads: simple, parameterized, aggregation, pagination, fulltext, deep-traversal, mutations, mixed"
  echo "Frameworks: fraiseql, strawberry, graphene, fastapi, flask, apollo, express, gqlgen, gin"
  echo "Configs: smoke, small, medium, large"
  echo ""
  echo "Examples:"
  echo "  $0 simple fraiseql smoke          # Quick validation"
  echo "  $0 simple fraiseql small          # Baseline test"
  echo "  $0 aggregation strawberry medium  # Realistic load"
  exit 1
fi

# Framework port mapping
declare -A PORTS=(
  ["fraiseql"]="4000"
  ["strawberry"]="8011"
  ["graphene"]="8002"
  ["fastapi"]="8003"
  ["flask"]="8004"
  ["apollo"]="4001"
  ["express"]="8005"
  ["gqlgen"]="4003"
  ["gin"]="8006"
)

PORT=${PORTS[$FRAMEWORK]}
if [ -z "$PORT" ]; then
  echo "Error: Unknown framework '$FRAMEWORK'"
  exit 1
fi

# Load test configuration
CONFIG_FILE="../configs/${CONFIG}.properties"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found: $CONFIG_FILE"
  exit 1
fi

source "$CONFIG_FILE"

# Override duration if provided
if [ -n "$DURATION_OVERRIDE" ]; then
  duration=$DURATION_OVERRIDE
fi

# Create results directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="../results/${FRAMEWORK}/${WORKLOAD}/${CONFIG}/${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

# Test file path
TEST_FILE="../jmeter/workloads/${WORKLOAD}.jmx"
if [ ! -f "$TEST_FILE" ]; then
  echo "Error: Test file not found: $TEST_FILE"
  exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "  FraiseQL Performance Test"
echo "════════════════════════════════════════════════════════════════"
echo "  Workload:   $WORKLOAD"
echo "  Framework:  $FRAMEWORK (port $PORT)"
echo "  Config:     $CONFIG"
echo "  Threads:    $threads"
echo "  Ramp-up:    ${rampup}s"
echo "  Loops:      $loops"
echo "  Duration:   ${duration}s"
echo "  Results:    $RESULTS_DIR"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Health check
echo "Checking framework health..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/health" || echo "000")
if [ "$HEALTH_CHECK" != "200" ]; then
  echo "Warning: Framework health check returned $HEALTH_CHECK"
  echo "Continuing anyway..."
fi

# Run JMeter test
echo "Starting JMeter test..."
jmeter -n \
  -t "$TEST_FILE" \
  -Jhost=localhost \
  -Jport=$PORT \
  -Jthreads=$threads \
  -Jrampup=$rampup \
  -Jduration=$duration \
  -l "${RESULTS_DIR}/results.jtl" \
  -e -o "${RESULTS_DIR}/html" \
  2>&1 | tee "${RESULTS_DIR}/jmeter.log"

# Generate summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Test Complete"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Count results
TOTAL=$(wc -l < "${RESULTS_DIR}/results.jtl")
ERRORS=$(grep -c "false" "${RESULTS_DIR}/results.jtl" || echo 0)
SUCCESS=$(grep -c "true" "${RESULTS_DIR}/results.jtl" || echo 0)
ERROR_RATE=$(awk "BEGIN {print ($ERRORS / $TOTAL) * 100}")

echo "  Total Requests:  $TOTAL"
echo "  Successful:      $SUCCESS"
echo "  Errors:          $ERRORS"
echo "  Error Rate:      ${ERROR_RATE}%"
echo ""
echo "  Results saved to: $RESULTS_DIR"
echo "  HTML Report:      ${RESULTS_DIR}/html/index.html"
echo ""

# Open results
if command -v xdg-open &> /dev/null; then
  echo "Opening HTML report..."
  xdg-open "${RESULTS_DIR}/html/index.html" &
fi

echo "════════════════════════════════════════════════════════════════"