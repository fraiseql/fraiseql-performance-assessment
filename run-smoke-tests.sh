#!/bin/bash

# Simple smoke test runner
echo "🚀 Running FraiseQL Smoke Tests (ALL Frameworks)"
echo ""

FRAMEWORKS=(fraiseql strawberry apollo gqlgen async-graphql go-graphql-go graphene fastapi flask express actix gin-rest spring-boot spring-boot-orm spring-boot-orm-naive express-orm apollo-orm hasura laravel rails csharp-dotnet)
PASSED=0
FAILED=0

for framework in "${FRAMEWORKS[@]}"; do
  echo "=== Testing $framework ==="

  # Get the port for this framework
  PORT=""
  case $framework in
    fraiseql) PORT="4000" ;;
    strawberry) PORT="8011" ;;
    graphene) PORT="8002" ;;
    apollo) PORT="4001" ;;
    express) PORT="8005" ;;
    actix) PORT="8015" ;;
    fastapi) PORT="8003" ;;
    flask) PORT="8004" ;; 
    gqlgen) PORT="4003" ;;
    async-graphql) PORT="8016" ;;
    go-graphql-go) PORT="8014" ;;
    gin-rest) PORT="8006" ;;
    spring-boot) PORT="8010" ;;
    spring-boot-orm) PORT="8011" ;;
    spring-boot-orm-naive) PORT="8014" ;;
    express-orm) PORT="8008" ;;
    apollo-orm) PORT="4004" ;;
    hasura) PORT="8081" ;;
    laravel) PORT="8009" ;;
    rails) PORT="8013" ;;
    csharp-dotnet) PORT="8012" ;;
  esac

  # Test endpoint based on framework type
  if [[ "$framework" =~ ^(fraiseql|strawberry|graphene|apollo|gqlgen|async-graphql|apollo-orm|hasura|csharp-dotnet)$ ]]; then
    # GraphQL frameworks
    if [ "$framework" = "apollo" ]; then
      # Apollo requires POST with content-type
      RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"query": "{ __typename }"}' \
                 -w "HTTPSTATUS:%{http_code}" "http://localhost:$PORT/graphql" 2>/dev/null || echo "HTTPSTATUS:000")
    elif [ "$framework" = "rails" ]; then
    # Rails uses /api/health
    RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:$PORT/api/health" 2>/dev/null || echo "HTTPSTATUS:000")
    elif [ "$framework" = "hasura" ]; then
    # Hasura uses /healthz endpoint
    RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:$PORT/healthz" 2>/dev/null || echo "HTTPSTATUS:000")
  else
      RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"query": "{ __typename }"}' \
                 -w "HTTPSTATUS:%{http_code}" "http://localhost:$PORT/graphql" 2>/dev/null || echo "HTTPSTATUS:000")
    fi
  elif [ "$framework" = "rails" ]; then
    # Rails uses /api/health
    RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:$PORT/api/health" 2>/dev/null || echo "HTTPSTATUS:000")
  else
    # REST frameworks
    RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:$PORT/health" 2>/dev/null || echo "HTTPSTATUS:000")
  fi

  HTTP_CODE=$(echo "$RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ $framework PASSED (HTTP $HTTP_CODE)"
    ((PASSED++))
  elif [ "$framework" = "rails" ]; then
    # Rails uses /api/health
    RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:$PORT/api/health" 2>/dev/null || echo "HTTPSTATUS:000")
  else
    echo "❌ $framework FAILED (HTTP $HTTP_CODE)"
    ((FAILED++))
  fi
  echo ""
done

echo "=== Smoke Test Results ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
  echo "🎉 All smoke tests passed!"
else
  echo "⚠️  Some smoke tests failed"
fi