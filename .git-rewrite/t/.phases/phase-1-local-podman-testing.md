# FraiseQL Comprehensive Benchmarking - Phase 1: Local Podman Testing

## Phase Overview

**Goal**: Validate all frameworks work correctly in isolated podman containers before distributed testing

**Scope**: Local testing on single machine with podman containers for each framework

**Context**: This phase establishes a reliable baseline for framework performance comparison by ensuring all GraphQL and REST API implementations (FraiseQL, Strawberry, Graphene, FastAPI REST, Flask REST) can run concurrently in podman containers with proper database connectivity, API functionality, and JMeter integration.

**Success Criteria**:
- All 5 frameworks start successfully in podman containers within 30 seconds
- Database connections established and schema/data accessible from all frameworks
- Basic API endpoints (health, ping, user queries) respond correctly with <100ms latency
- JMeter can connect and execute test plans against all frameworks without connection errors
- Performance data collection (metrics endpoints) working for monitoring frameworks
- No container conflicts, port collisions, or resource exhaustion issues
- Concurrent framework execution stable for at least 30 minutes under light load

## Phase Prerequisites

### System Requirements
- **Podman**: Version 4.0+ installed and configured (`podman --version`)
- **Memory**: At least 12GB RAM available (6GB baseline + 2GB per framework container)
- **Disk**: 25GB free disk space (20GB for containers + 5GB for test data/logs)
- **CPU**: 4+ cores recommended for concurrent framework testing
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, or equivalent)

### Software Dependencies
- **PostgreSQL**: Version 15+ (will be run in podman container)
- **JMeter**: Version 5.5+ installed locally (`jmeter --version`)
- **curl**: For API testing (`curl --version`)
- **jq**: For JSON processing (`jq --version`)
- **Python**: Version 3.8+ with required packages (`python3 --version`)
- **Docker/Podman Compose**: Optional but recommended for orchestration

### Network Configuration
- **Inter-container communication**: Podman containers can reach each other via `host.containers.internal`
- **Host access**: All container ports (4000, 8001-8004, 5432, 9090, 3000) accessible from host
- **Firewall**: No blocking of localhost/container communication
- **DNS**: Local DNS resolution working (optional but helpful)

### Environment Setup Validation
```bash
# Verify podman installation
podman --version
podman info

# Check available resources
free -h
df -h .

# Verify JMeter installation
jmeter --version

# Check required tools
which curl jq python3

# Validate network connectivity
ping -c 1 host.containers.internal || echo "host.containers.internal not resolvable - may need /etc/hosts entry"
```

## Implementation Steps

### Step 1: Infrastructure Setup
**Estimated Time**: 30 minutes

#### 1.1 Start PostgreSQL Database
```bash
# Create database volume for persistence
podman volume create fraiseql-postgres-data

# Start PostgreSQL in podman with proper resource limits
podman run -d \
  --name fraiseql-postgres \
  --memory=2g \
  --cpus=1 \
  -e POSTGRES_DB=fraiseql_benchmark \
  -e POSTGRES_USER=benchmark \
  -e POSTGRES_PASSWORD=benchmark123 \
  -e POSTGRES_INITDB_ARGS="--encoding=UTF-8" \
  -p 5432:5432 \
  -v fraiseql-postgres-data:/var/lib/postgresql/data \
  -v $(pwd)/database:/docker-entrypoint-initdb.d:ro \
  postgres:15-alpine

# Wait for database initialization (may take 1-2 minutes)
echo "Waiting for PostgreSQL to initialize..."
sleep 60

# Check database logs for successful startup
podman logs fraiseql-postgres
```

#### 1.2 Verify Database Setup
```bash
# Test database connectivity
podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "SELECT version();"

# Verify schema creation (benchmark schema should exist)
podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'benchmark'
ORDER BY tablename;
"

# Check data population (should have test data)
podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "
SELECT 'users' as table_name, COUNT(*) as count FROM benchmark.users
UNION ALL
SELECT 'posts', COUNT(*) FROM benchmark.posts
UNION ALL
SELECT 'comments', COUNT(*) FROM benchmark.comments;
"

# Verify extensions are installed
podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "
SELECT name FROM pg_available_extensions WHERE name IN ('uuid-ossp', 'pg_stat_statements');
"

# Expected output: At least 1000 users, 5000 posts, 10000 comments
```

### Step 2: Framework Container Testing
**Estimated Time**: 2 hours

#### 2.1 Build All Framework Images
```bash
# Set build context and build all framework containers
PROJECT_ROOT=$(pwd)

# Build with build cache and proper tagging
for framework in fraiseql strawberry graphene fastapi-rest flask-rest; do
  echo "Building $framework framework..."
  cd "$PROJECT_ROOT/frameworks/$framework"

  # Build with resource limits and proper labels
  podman build \
    --memory=2g \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --label "benchmark.framework=$framework" \
    --label "benchmark.version=phase1" \
    -t "fraiseql-benchmark-$framework:latest" \
    .

  if [ $? -ne 0 ]; then
    echo "❌ Failed to build $framework framework"
    exit 1
  fi

  echo "✅ Successfully built $framework framework"
done

# Return to project root
cd "$PROJECT_ROOT"

# List built images with sizes
podman images | grep fraiseql-benchmark

# Verify all images exist
EXPECTED_IMAGES=("fraiseql-benchmark-fraiseql" "fraiseql-benchmark-strawberry" "fraiseql-benchmark-graphene" "fraiseql-benchmark-fastapi-rest" "fraiseql-benchmark-flask-rest")
for img in "${EXPECTED_IMAGES[@]}"; do
  if ! podman images | grep -q "$img"; then
    echo "❌ Missing image: $img"
    exit 1
  fi
done

echo "✅ All framework images built successfully"
```

#### 2.2 Test Framework Startup (Individual)

**Environment Variables Required for All Frameworks**:
- `DB_HOST`: Database hostname (use `host.containers.internal`)
- `DB_PORT`: Database port (5432)
- `DB_NAME`: Database name (`fraiseql_benchmark`)
- `DB_USER`: Database username (`benchmark`)
- `DB_PASSWORD`: Database password (`benchmark123`)
- `LOG_LEVEL`: Logging level (`INFO` for production, `DEBUG` for testing)

```bash
# Function to test individual framework
test_framework() {
  local framework=$1
  local port=$2
  local internal_port=$3
  local image_name="fraiseql-benchmark-$framework"

  echo "Testing $framework framework on port $port..."

  # Start container with resource limits and environment
  podman run -d \
    --name "test-$framework" \
    --memory=1g \
    --cpus=0.5 \
    -p "$port:$internal_port" \
    -e DB_HOST=host.containers.internal \
    -e DB_PORT=5432 \
    -e DB_NAME=fraiseql_benchmark \
    -e DB_USER=benchmark \
    -e DB_PASSWORD=benchmark123 \
    -e LOG_LEVEL=DEBUG \
    "$image_name"

  # Wait for startup (framework-specific times)
  case $framework in
    fraiseql) sleep 15 ;;
    strawberry|graphene) sleep 12 ;;
    fastapi-rest|flask-rest) sleep 10 ;;
  esac

  # Check container is running
  if ! podman ps | grep -q "test-$framework"; then
    echo "❌ Container failed to start"
    podman logs "test-$framework"
    return 1
  fi

  # Health check
  if ! curl -f -m 10 "http://localhost:$port/health" > /dev/null 2>&1; then
    echo "❌ Health check failed"
    podman logs "test-$framework"
    return 1
  fi

  # Framework-specific API tests
  case $framework in
    fraiseql|strawberry|graphene)
      # GraphQL ping test
      if ! curl -f -m 10 -X POST "http://localhost:$port/graphql" \
        -H "Content-Type: application/json" \
        -d '{"query": "{ ping }"}' | jq -e '.data.ping' > /dev/null; then
        echo "❌ GraphQL ping failed"
        return 1
      fi

      # GraphQL user query test
      if ! curl -f -m 10 -X POST "http://localhost:$port/graphql" \
        -H "Content-Type: application/json" \
        -d '{"query": "query { users(limit: 1) { id username } }"}' | jq -e '.data.users[0].id' > /dev/null; then
        echo "❌ GraphQL user query failed"
        return 1
      fi
      ;;
    fastapi-rest|flask-rest)
      # REST ping test
      if ! curl -f -m 10 "http://localhost:$port/ping" > /dev/null; then
        echo "❌ REST ping failed"
        return 1
      fi

      # REST user endpoint test
      if ! curl -f -m 10 "http://localhost:$port/users?limit=1" | jq -e '.[0].id' > /dev/null; then
        echo "❌ REST user endpoint failed"
        return 1
      fi
      ;;
  esac

  # Performance baseline check (< 100ms for simple queries)
  local start_time=$(date +%s%3N)
  curl -s -X POST "http://localhost:$port/graphql" \
    -H "Content-Type: application/json" \
    -d '{"query": "{ ping }"}' > /dev/null
  local end_time=$(date +%s%3N)
  local response_time=$((end_time - start_time))

  if [ $response_time -gt 100 ]; then
    echo "⚠️  Slow response time: ${response_time}ms (expected < 100ms)"
  else
    echo "✅ Response time: ${response_time}ms"
  fi

  # Cleanup
  podman stop "test-$framework" && podman rm "test-$framework"
  echo "✅ $framework framework test passed"
  return 0
}

# Test each framework individually
test_framework fraiseql 4000 4000
test_framework strawberry 8001 8000
test_framework graphene 8002 8000
test_framework fastapi-rest 8003 8003
test_framework flask-rest 8004 8004

echo "✅ All individual framework tests completed"
```

#### 2.3 Start All Frameworks Concurrently
```bash
# Function to start framework with proper resource allocation
start_framework() {
  local framework=$1
  local port=$2
  local internal_port=$3
  local memory=$4
  local cpus=$5

  echo "Starting $framework framework on port $port..."

  podman run -d \
    --name "$framework" \
    --memory="$memory" \
    --cpus="$cpus" \
    --restart=unless-stopped \
    --label "benchmark.framework=$framework" \
    --label "benchmark.phase=1" \
    -p "$port:$internal_port" \
    -e DB_HOST=host.containers.internal \
    -e DB_PORT=5432 \
    -e DB_NAME=fraiseql_benchmark \
    -e DB_USER=benchmark \
    -e DB_PASSWORD=benchmark123 \
    -e LOG_LEVEL=INFO \
    "fraiseql-benchmark-$framework:latest"

  if [ $? -ne 0 ]; then
    echo "❌ Failed to start $framework framework"
    return 1
  fi

  echo "✅ $framework framework started"
}

# Start all frameworks with resource allocation
# Resource allocation: Total 8GB RAM, 3 CPUs available
start_framework fraiseql 4000 4000 1.5g 0.6
start_framework strawberry 8001 8000 1.2g 0.5
start_framework graphene 8002 8000 1.2g 0.5
start_framework fastapi-rest 8003 8003 1.0g 0.4
start_framework flask-rest 8004 8004 1.0g 0.4

# Wait for all frameworks to start
echo "Waiting for all frameworks to initialize..."
sleep 30

# Verify all containers are running
echo "Checking container status..."
RUNNING_CONTAINERS=$(podman ps --filter "label=benchmark.phase=1" --format "{{.Names}}" | wc -l)
if [ "$RUNNING_CONTAINERS" -ne 5 ]; then
  echo "❌ Expected 5 containers, found $RUNNING_CONTAINERS"
  podman ps --filter "label=benchmark.phase=1"
  exit 1
fi

# Check resource usage
echo "Current resource usage:"
podman stats --no-stream --filter "label=benchmark.phase=1"

# Verify no port conflicts
echo "Checking for port conflicts..."
netstat -tlnp 2>/dev/null | grep -E ":(4000|8001|8002|8003|8004) " || echo "No port conflicts detected"

echo "✅ All frameworks started successfully"
```

### Step 3: Framework Validation
**Estimated Time**: 45 minutes

#### 3.1 Health Check All Frameworks
```bash
# Comprehensive health check script
#!/bin/bash
set -e

FRAMEWORKS=(
  "fraiseql:4000:graphql"
  "strawberry:8001:graphql"
  "graphene:8002:graphql"
  "fastapi-rest:8003:rest"
  "flask-rest:8004:rest"
)

echo "Starting comprehensive health checks..."

for fw in "${FRAMEWORKS[@]}"; do
  IFS=':' read -r name port type <<< "$fw"

  echo "🔍 Checking $name ($type) on port $port..."

  # Basic connectivity check
  if ! timeout 10 bash -c "echo > /dev/tcp/localhost/$port" 2>/dev/null; then
    echo "❌ $name: Port $port not accessible"
    continue
  fi

  # Health endpoint check
  if ! curl -f -m 5 -s "http://localhost:$port/health" > /dev/null; then
    echo "❌ $name: Health endpoint failed"
    continue
  fi

  # Type-specific checks
  if [ "$type" = "graphql" ]; then
    # GraphQL schema introspection
    if ! curl -f -m 5 -s -X POST "http://localhost:$port/graphql" \
      -H "Content-Type: application/json" \
      -d '{"query": "query { __typename }"}' | jq -e '.data.__typename' > /dev/null; then
      echo "❌ $name: GraphQL introspection failed"
      continue
    fi
  else
    # REST API check
    if ! curl -f -m 5 -s "http://localhost:$port/ping" > /dev/null; then
      echo "❌ $name: REST ping failed"
      continue
    fi
  fi

  # Response time check
  start_time=$(date +%s%3N)
  curl -s "http://localhost:$port/health" > /dev/null
  end_time=$(date +%s%3N)
  response_time=$((end_time - start_time))

  if [ $response_time -gt 100 ]; then
    echo "⚠️  $name: Slow health response (${response_time}ms)"
  else
    echo "✅ $name: Healthy (${response_time}ms)"
  fi
done

# Database connectivity check from containers
echo "🔍 Checking database connectivity..."
for fw in "${FRAMEWORKS[@]}"; do
  IFS=':' read -r name port type <<< "$fw"

  # Check if framework can access database (via logs or metrics)
  if podman logs "$name" 2>&1 | grep -q -i "database\|postgres\|connected"; then
    echo "✅ $name: Database connection detected in logs"
  else
    echo "⚠️  $name: Database connection status unclear"
  fi
done

echo "✅ Health checks completed"
```

#### 3.2 Functional Testing
```bash
# Comprehensive functional testing script
#!/bin/bash
set -e

echo "Starting functional API tests..."

# Test GraphQL Frameworks
GRAPHQL_FRAMEWORKS=("fraiseql:4000" "strawberry:8001" "graphene:8002")

for fw in "${GRAPHQL_FRAMEWORKS[@]}"; do
  IFS=':' read -r name port <<< "$fw"
  echo "Testing GraphQL framework: $name on port $port"

  # Test cases with expected responses
  test_cases=(
    # Description:Query:Expected_Field
    "Ping:{ ping }:ping"
    "Users:query { users(limit: 5) { id username email } }:users"
    "Posts:query { posts(limit: 3) { id title content author { username } } }:posts"
    "Comments:query { comments(limit: 2) { id content post { title } author { username } } }:comments"
  )

  for test_case in "${test_cases[@]}"; do
    IFS=':' read -r desc query expected_field <<< "$test_case"

    echo "  $desc test..."
    response=$(curl -s -m 10 -X POST "http://localhost:$port/graphql" \
      -H "Content-Type: application/json" \
      -d "{\"query\": \"$query\"}")

    # Check for GraphQL errors
    if echo "$response" | jq -e '.errors' > /dev/null 2>&1; then
      echo "    ❌ GraphQL errors found:"
      echo "$response" | jq '.errors'
      continue
    fi

    # Check expected data exists
    if echo "$response" | jq -e ".data.$expected_field" > /dev/null 2>&1; then
      count=$(echo "$response" | jq ".data.$expected_field | length")
      echo "    ✅ Found $count $expected_field"
    else
      echo "    ❌ Expected field $expected_field not found"
      echo "    Response: $response"
    fi
  done
done

# Test REST Frameworks
REST_FRAMEWORKS=("fastapi-rest:8003" "flask-rest:8004")

for fw in "${REST_FRAMEWORKS[@]}"; do
  IFS=':' read -r name port <<< "$fw"
  echo "Testing REST framework: $name on port $port"

  # Ping endpoint
  if curl -f -s "http://localhost:$port/ping" > /dev/null; then
    echo "  ✅ Ping endpoint working"
  else
    echo "  ❌ Ping endpoint failed"
  fi

  # Users endpoint
  response=$(curl -s -m 10 "http://localhost:$port/users?limit=5")
  if echo "$response" | jq -e '.[0].id' > /dev/null 2>&1; then
    count=$(echo "$response" | length)
    echo "  ✅ Users endpoint: $count users returned"
  else
    echo "  ❌ Users endpoint failed or returned invalid data"
  fi

  # Posts endpoint
  response=$(curl -s -m 10 "http://localhost:$port/posts?limit=3")
  if echo "$response" | jq -e '.[0].id' > /dev/null 2>&1; then
    count=$(echo "$response" | length)
    echo "  ✅ Posts endpoint: $count posts returned"
  else
    echo "  ❌ Posts endpoint failed or returned invalid data"
  fi
done

# Cross-framework consistency check
echo "Checking data consistency across frameworks..."

# Get user count from each framework
declare -A user_counts
for fw in "${GRAPHQL_FRAMEWORKS[@]}"; do
  IFS=':' read -r name port <<< "$fw"
  count=$(curl -s -X POST "http://localhost:$port/graphql" \
    -H "Content-Type: application/json" \
    -d '{"query": "query { users { id } }"}' | jq '.data.users | length')
  user_counts[$name]=$count
done

for fw in "${REST_FRAMEWORKS[@]}"; do
  IFS=':' read -r name port <<< "$fw"
  count=$(curl -s "http://localhost:$port/users" | jq 'length')
  user_counts[$name]=$count
done

# Check consistency
expected_count=""
for name in "${!user_counts[@]}"; do
  count=${user_counts[$name]}
  if [ -z "$expected_count" ]; then
    expected_count=$count
  elif [ "$count" -ne "$expected_count" ]; then
    echo "⚠️  Data inconsistency: $name has $count users, expected $expected_count"
  fi
done

echo "✅ Functional testing completed"
```

#### 3.3 Database Connection Validation
```bash
# Comprehensive database validation
#!/bin/bash
set -e

echo "Starting database validation..."

# Database schema and data validation
echo "🔍 Checking database schema and data..."

# Verify schema exists and has expected tables
TABLES_QUERY="
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = 'benchmark'
ORDER BY tablename;
"

echo "Database tables:"
podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "$TABLES_QUERY"

# Expected tables
EXPECTED_TABLES=("users" "posts" "comments")
for table in "${EXPECTED_TABLES[@]}"; do
  if ! podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "$TABLES_QUERY" | grep -q "$table"; then
    echo "❌ Missing expected table: $table"
    exit 1
  fi
done

# Data count validation
echo "Data counts:"
DATA_COUNTS=$(podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "
SELECT 'users' as table_name, COUNT(*) as count FROM benchmark.users
UNION ALL
SELECT 'posts', COUNT(*) FROM benchmark.posts
UNION ALL
SELECT 'comments', COUNT(*) FROM benchmark.comments;
")

echo "$DATA_COUNTS"

# Minimum expected counts (should have substantial test data)
MIN_USERS=1000
MIN_POSTS=5000
MIN_COMMENTS=10000

while read -r line; do
  if [[ $line =~ users ]]; then
    user_count=$(echo "$line" | awk '{print $2}')
    if [ "$user_count" -lt $MIN_USERS ]; then
      echo "⚠️  Low user count: $user_count (expected >= $MIN_USERS)"
    fi
  elif [[ $line =~ posts ]]; then
    post_count=$(echo "$line" | awk '{print $2}')
    if [ "$post_count" -lt $MIN_POSTS ]; then
      echo "⚠️  Low post count: $post_count (expected >= $MIN_POSTS)"
    fi
  elif [[ $line =~ comments ]]; then
    comment_count=$(echo "$line" | awk '{print $2}')
    if [ "$comment_count" -lt $MIN_COMMENTS ]; then
      echo "⚠️  Low comment count: $comment_count (expected >= $MIN_COMMENTS)"
    fi
  fi
done <<< "$DATA_COUNTS"

# Connection validation from each framework
echo "🔍 Testing database connections from frameworks..."

FRAMEWORKS=("fraiseql" "strawberry" "graphene" "fastapi-rest" "flask-rest")

for fw in "${FRAMEWORKS[@]}"; do
  echo "Testing database connection for $fw..."

  # Check container logs for database connection messages
  if podman logs "$fw" 2>&1 | grep -q -i "connected\|database.*ready\|postgres.*connected"; then
    echo "  ✅ $fw: Database connection detected in logs"
  else
    echo "  ⚠️  $fw: No clear database connection evidence in logs"
  fi

  # Check for database-related errors in logs
  if podman logs "$fw" 2>&1 | grep -q -i "error\|failed\|exception" | grep -i "database\|postgres\|connection"; then
    echo "  ❌ $fw: Database errors found in logs:"
    podman logs "$fw" 2>&1 | grep -i "error\|failed\|exception" | grep -i "database\|postgres\|connection" | head -3
  fi
done

# Connection pool validation (if applicable)
echo "🔍 Checking database connection pool status..."
podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "
SELECT
  count(*) as total_connections,
  count(*) filter (where state = 'active') as active_connections,
  count(*) filter (where state = 'idle') as idle_connections
FROM pg_stat_activity
WHERE datname = 'fraiseql_benchmark';
"

echo "✅ Database validation completed"
```

### Step 4: JMeter Integration Testing
**Estimated Time**: 30 minutes

#### 4.1 Test JMeter Connection
```bash
# JMeter integration testing with comprehensive validation
#!/bin/bash
set -e

cd tests/perf/jmeter

# Create results directory
mkdir -p results
RESULTS_DIR="$(pwd)/results"

echo "Starting JMeter integration tests..."

# Test individual framework connectivity first
FRAMEWORK_ENDPOINTS=(
  "fraiseql:http://localhost:4000/graphql"
  "strawberry:http://localhost:8001/graphql"
  "graphene:http://localhost:8002/graphql"
  "fastapi-rest:http://localhost:8003"
  "flask-rest:http://localhost:8004"
)

for endpoint in "${FRAMEWORK_ENDPOINTS[@]}"; do
  IFS=':' read -r name url <<< "$endpoint"
  echo "Testing JMeter connectivity to $name..."

  # Simple connectivity test
  jmeter -n \
    -JTARGET_URL="$url" \
    -JFRAMEWORK="$name" \
    -t datasets/connectivity_test.jmx \
    -l "$RESULTS_DIR/${name}_connectivity.jtl" \
    -j "$RESULTS_DIR/${name}_connectivity.log"

  # Check for successful responses
  if grep -q "200" "$RESULTS_DIR/${name}_connectivity.jtl"; then
    echo "  ✅ $name: JMeter connectivity successful"
  else
    echo "  ❌ $name: JMeter connectivity failed"
    cat "$RESULTS_DIR/${name}_connectivity.log" | tail -10
    exit 1
  fi
done

# Test GraphQL frameworks with comparative test plan
echo "Testing GraphQL frameworks with comparative test plan..."
jmeter -n \
  -JPROTOCOL=graphql \
  -JFRAMEWORKS=fraiseql,strawberry,graphene \
  -JTEST_DURATION=30 \
  -JUSERS_PER_FRAMEWORK=5 \
  -t comparative-test-plan.jmx \
  -l "$RESULTS_DIR/graphql_comparative.jtl" \
  -j "$RESULTS_DIR/graphql_comparative.log"

# Test REST frameworks with comparative test plan
echo "Testing REST frameworks with comparative test plan..."
jmeter -n \
  -JPROTOCOL=rest \
  -JFRAMEWORKS=fastapi-rest,flask-rest \
  -JTEST_DURATION=30 \
  -JUSERS_PER_FRAMEWORK=5 \
  -t comparative-test-plan.jmx \
  -l "$RESULTS_DIR/rest_comparative.jtl" \
  -j "$RESULTS_DIR/rest_comparative.log"

echo "✅ JMeter connectivity tests completed"
```

#### 4.2 Validate Test Results
```bash
# Comprehensive JMeter result validation
#!/bin/bash

RESULTS_DIR="tests/perf/jmeter/results"

echo "Validating JMeter test results..."

# Check test result files exist
for result_file in graphql_comparative.jtl rest_comparative.jtl; do
  if [ ! -f "$RESULTS_DIR/$result_file" ]; then
    echo "❌ Missing result file: $result_file"
    exit 1
  fi
done

# Analyze GraphQL results
echo "GraphQL Test Results:"
echo "===================="

# Success rate
GRAPHQL_SUCCESS=$(grep -c "true" "$RESULTS_DIR/graphql_comparative.jtl" || echo "0")
GRAPHQL_TOTAL=$(wc -l < "$RESULTS_DIR/graphql_comparative.jtl")
GRAPHQL_SUCCESS_RATE=$((GRAPHQL_SUCCESS * 100 / GRAPHQL_TOTAL))

echo "Success Rate: $GRAPHQL_SUCCESS_RATE% ($GRAPHQL_SUCCESS/$GRAPHQL_TOTAL)"

# Response time statistics
GRAPHQL_AVG_RESPONSE=$(awk -F',' '{sum+=$2} END {print int(sum/NR)}' "$RESULTS_DIR/graphql_comparative.jtl" 2>/dev/null || echo "N/A")
echo "Average Response Time: ${GRAPHQL_AVG_RESPONSE}ms"

# Error analysis
if grep -q "false" "$RESULTS_DIR/graphql_comparative.jtl"; then
  echo "Errors found in GraphQL tests:"
  grep "false" "$RESULTS_DIR/graphql_comparative.jtl" | head -5
fi

# Analyze REST results
echo ""
echo "REST Test Results:"
echo "=================="

REST_SUCCESS=$(grep -c "true" "$RESULTS_DIR/rest_comparative.jtl" || echo "0")
REST_TOTAL=$(wc -l < "$RESULTS_DIR/rest_comparative.jtl")
REST_SUCCESS_RATE=$((REST_SUCCESS * 100 / REST_TOTAL))

echo "Success Rate: $REST_SUCCESS_RATE% ($REST_SUCCESS/$REST_TOTAL)"

REST_AVG_RESPONSE=$(awk -F',' '{sum+=$2} END {print int(sum/NR)}' "$RESULTS_DIR/rest_comparative.jtl" 2>/dev/null || echo "N/A")
echo "Average Response Time: ${REST_AVG_RESPONSE}ms"

if grep -q "false" "$RESULTS_DIR/rest_comparative.jtl"; then
  echo "Errors found in REST tests:"
  grep "false" "$RESULTS_DIR/rest_comparative.jtl" | head -5
fi

# Generate HTML reports
echo ""
echo "Generating HTML reports..."
jmeter -g "$RESULTS_DIR/graphql_comparative.jtl" -o "$RESULTS_DIR/graphql_report"
jmeter -g "$RESULTS_DIR/rest_comparative.jtl" -o "$RESULTS_DIR/rest_report"

# Validation thresholds
if [ $GRAPHQL_SUCCESS_RATE -lt 95 ]; then
  echo "⚠️  GraphQL success rate below 95%: $GRAPHQL_SUCCESS_RATE%"
fi

if [ $REST_SUCCESS_RATE -lt 95 ]; then
  echo "⚠️  REST success rate below 95%: $REST_SUCCESS_RATE%"
fi

if [ "$GRAPHQL_AVG_RESPONSE" != "N/A" ] && [ $GRAPHQL_AVG_RESPONSE -gt 200 ]; then
  echo "⚠️  GraphQL average response time high: ${GRAPHQL_AVG_RESPONSE}ms"
fi

if [ "$REST_AVG_RESPONSE" != "N/A" ] && [ $REST_AVG_RESPONSE -gt 200 ]; then
  echo "⚠️  REST average response time high: ${REST_AVG_RESPONSE}ms"
fi

echo "✅ JMeter result validation completed"
```

### Step 5: Load Testing Validation
**Estimated Time**: 30 minutes

#### 5.1 Run Light Load Tests
```bash
# Light load testing with monitoring
#!/bin/bash
set -e

cd tests/perf/jmeter
RESULTS_DIR="$(pwd)/results"

echo "Starting light load tests..."

# Function to run load test with monitoring
run_load_test() {
  local protocol=$1
  local frameworks=$2
  local duration=$3
  local users=$4
  local test_name=$5

  echo "Running $protocol load test: $frameworks ($users users, ${duration}s)..."

  # Start background monitoring
  monitor_containers "$test_name" &
  MONITOR_PID=$!

  # Run JMeter test
  timeout $duration jmeter -n \
    -JPROTOCOL="$protocol" \
    -JFRAMEWORKS="$frameworks" \
    -JTEST_DURATION="$duration" \
    -JUSERS_PER_FRAMEWORK="$users" \
    -t comparative-test-plan.jmx \
    -l "$RESULTS_DIR/${test_name}.jtl" \
    -j "$RESULTS_DIR/${test_name}.log"

  # Stop monitoring
  kill $MONITOR_PID 2>/dev/null || true
  wait $MONITOR_PID 2>/dev/null || true

  # Quick result analysis
  local success_count=$(grep -c "true" "$RESULTS_DIR/${test_name}.jtl" 2>/dev/null || echo "0")
  local total_count=$(wc -l < "$RESULTS_DIR/${test_name}.jtl" 2>/dev/null || echo "0")

  if [ $total_count -gt 0 ]; then
    local success_rate=$((success_count * 100 / total_count))
    echo "  ✅ $test_name: $success_rate% success rate ($success_count/$total_count requests)"

    if [ $success_rate -lt 90 ]; then
      echo "  ⚠️  Low success rate for $test_name"
    fi
  else
    echo "  ❌ $test_name: No results generated"
  fi
}

# Background monitoring function
monitor_containers() {
  local test_name=$1
  local monitor_file="$RESULTS_DIR/${test_name}_monitoring.log"

  echo "Starting resource monitoring for $test_name..." > "$monitor_file"

  while true; do
    echo "$(date '+%H:%M:%S'): $(podman stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | grep -E '(fraiseql|strawberry|graphene|fastapi|flask)')" >> "$monitor_file"
    sleep 5
  done
}

# Run light load tests (30 seconds, 10 users per framework)
run_load_test "graphql" "fraiseql,strawberry,graphene" 30 10 "light_graphql_load"
run_load_test "rest" "fastapi-rest,flask-rest" 30 10 "light_rest_load"

# Run individual framework stress test (15 seconds, 20 users)
for fw in fraiseql strawberry graphene fastapi-rest flask-rest; do
  if [[ $fw =~ (fraiseql|strawberry|graphene) ]]; then
    protocol="graphql"
  else
    protocol="rest"
  fi

  run_load_test "$protocol" "$fw" 15 20 "${fw}_stress"
done

echo "✅ Light load tests completed"
```

#### 5.2 Monitor Resource Usage
```bash
# Comprehensive resource monitoring and analysis
#!/bin/bash

echo "Analyzing resource usage during load tests..."

# Current container status
echo "Container Status:"
podman ps --filter "label=benchmark.phase=1" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Resource usage summary
echo ""
echo "Resource Usage Summary:"
podman stats --no-stream --filter "label=benchmark.phase=1"

# Check for resource alerts
echo ""
echo "Resource Alerts:"

# Memory usage check (>80% of allocated)
podman stats --no-stream --filter "label=benchmark.phase=1" --format "{{.Name}}:{{.MemPerc}}" | while read line; do
  name=$(echo "$line" | cut -d: -f1)
  mem_perc=$(echo "$line" | cut -d: -f2 | sed 's/%//')

  if (( $(echo "$mem_perc > 80" | bc -l) )); then
    echo "⚠️  High memory usage: $name (${mem_perc}%)"
  fi
done

# CPU usage check (>70% of allocated)
podman stats --no-stream --filter "label=benchmark.phase=1" --format "{{.Name}}:{{.CPUPerc}}" | while read line; do
  name=$(echo "$line" | cut -d: -f1)
  cpu_perc=$(echo "$line" | cut -d: | sed 's/%//')

  if (( $(echo "$cpu_perc > 70" | bc -l) )); then
    echo "⚠️  High CPU usage: $name (${cpu_perc}%)"
  fi
done

# Container log analysis for errors during load
echo ""
echo "Log Analysis During Load:"

FRAMEWORKS=("fraiseql" "strawberry" "graphene" "fastapi-rest" "flask-rest")
for fw in "${FRAMEWORKS[@]}"; do
  # Check for errors in recent logs
  error_count=$(podman logs "$fw" 2>&1 | grep -c -i "error\|exception\|failed" || echo "0")

  if [ "$error_count" -gt 0 ]; then
    echo "⚠️  $fw: $error_count errors found in logs during load test"
    podman logs "$fw" 2>&1 | grep -i "error\|exception\|failed" | tail -3
  else
    echo "✅ $fw: No errors in logs during load test"
  fi
done

# Load test result summary
echo ""
echo "Load Test Performance Summary:"
RESULTS_DIR="tests/perf/jmeter/results"

for result_file in light_graphql_load.jtl light_rest_load.jtl; do
  if [ -f "$RESULTS_DIR/$result_file" ]; then
    avg_response=$(awk -F',' '{sum+=$2; count++} END {if(count>0) print int(sum/count); else print "N/A"}' "$RESULTS_DIR/$result_file")
    echo "$result_file: Average response time = ${avg_response}ms"
  fi
done

echo "✅ Resource monitoring completed"
```

### Step 6: Performance Data Collection Validation
**Estimated Time**: 15 minutes

#### 6.1 Test Metrics Collection
```bash
# Comprehensive metrics collection validation
#!/bin/bash
set -e

echo "Testing metrics collection and monitoring setup..."

# Test metrics endpoints for frameworks that support them
METRICS_FRAMEWORKS=("fraiseql:4000" "fastapi-rest:8003")

for fw in "${METRICS_FRAMEWORKS[@]}"; do
  IFS=':' read -r name port <<< "$fw"
  echo "Testing metrics endpoint for $name..."

  if curl -f -m 5 -s "http://localhost:$port/metrics" > /dev/null; then
    echo "  ✅ $name: Metrics endpoint accessible"

    # Check metrics content
    metrics_content=$(curl -s "http://localhost:$port/metrics")

    # Validate common metrics exist
    if echo "$metrics_content" | grep -q "http_requests_total\|response_time\|active_connections"; then
      echo "  ✅ $name: Standard metrics present"
    else
      echo "  ⚠️  $name: Some standard metrics missing"
    fi

    # Check for Prometheus format
    if echo "$metrics_content" | grep -q "^[a-zA-Z_][a-zA-Z0-9_]*{"; then
      echo "  ✅ $name: Prometheus format detected"
    else
      echo "  ⚠️  $name: Non-standard metrics format"
    fi
  else
    echo "  ❌ $name: Metrics endpoint not accessible"
  fi
done

# Start monitoring stack (Prometheus + Grafana)
echo "Starting monitoring infrastructure..."

# Create monitoring network
podman network create benchmark-monitoring 2>/dev/null || true

# Start Prometheus
podman run -d \
  --name prometheus \
  --network benchmark-monitoring \
  --memory=512m \
  --cpus=0.2 \
  -p 9090:9090 \
  -v "$(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
  prom/prometheus:latest

# Wait for Prometheus
sleep 10

# Validate Prometheus is running
if curl -f -s "http://localhost:9090/-/healthy" > /dev/null; then
  echo "✅ Prometheus: Health check passed"
else
  echo "❌ Prometheus: Health check failed"
fi

# Start Grafana
podman run -d \
  --name grafana \
  --network benchmark-monitoring \
  --memory=256m \
  --cpus=0.1 \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  grafana/grafana:latest

# Wait for Grafana
sleep 15

# Validate Grafana is running
if curl -f -s "http://localhost:3000/api/health" > /dev/null; then
  echo "✅ Grafana: Health check passed"
else
  echo "❌ Grafana: Health check failed"
fi

# Test Prometheus can scrape metrics
echo "Testing Prometheus metrics scraping..."
if curl -s "http://localhost:9090/api/v1/targets" | jq -e '.data.activeTargets[] | select(.health == "up")' > /dev/null; then
  echo "✅ Prometheus: Successfully scraping targets"
else
  echo "⚠️  Prometheus: Target scraping issues detected"
fi

echo "✅ Metrics collection setup completed"
```

#### 6.2 Validate Data Collection
```bash
# Comprehensive data collection and analysis validation
#!/bin/bash
set -e

echo "Validating performance data collection and analysis..."

# Run comparative analysis script
echo "Running comparative analysis..."
if python3 run_rest_graphql_comparison.py; then
  echo "✅ Comparative analysis script executed successfully"
else
  echo "❌ Comparative analysis script failed"
  exit 1
fi

# Validate analysis output files
ANALYSIS_FILES=(
  "tests/perf/results/rest_graphql_analysis.json"
  "tests/perf/results/graphql_analysis.json"
  "tests/perf/results/rest_analysis.json"
)

for file in "${ANALYSIS_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "✅ Analysis file exists: $file"

    # Validate JSON structure
    if jq -e '.summary' "$file" > /dev/null 2>&1; then
      echo "  ✅ Valid JSON structure"

      # Check for key metrics
      if jq -e '.summary.average_response_time and .summary.success_rate' "$file" > /dev/null 2>&1; then
        echo "  ✅ Key metrics present"
      else
        echo "  ⚠️  Some key metrics missing"
      fi
    else
      echo "  ❌ Invalid JSON structure"
    fi
  else
    echo "❌ Missing analysis file: $file"
  fi
done

# Validate JMeter result processing
echo "Validating JMeter result processing..."

JMETER_RESULTS_DIR="tests/perf/jmeter/results"
if [ -d "$JMETER_RESULTS_DIR" ]; then
  result_files=$(find "$JMETER_RESULTS_DIR" -name "*.jtl" | wc -l)
  echo "✅ Found $result_files JMeter result files"

  # Check result file sizes (should have data)
  find "$JMETER_RESULTS_DIR" -name "*.jtl" -size +100c | while read -r file; do
    echo "  ✅ $file has substantial data"
  done
else
  echo "❌ JMeter results directory missing"
fi

# Generate summary report
echo "Generating performance summary report..."

cat > "tests/perf/results/phase1_performance_summary.md" << EOF
# Phase 1 Performance Summary

## Test Execution
- Frameworks tested: 5 (FraiseQL, Strawberry, Graphene, FastAPI REST, Flask REST)
- Test duration: Light load (30s) + Individual stress tests (15s each)
- JMeter threads: 10-20 per framework

## Key Metrics

### Response Times (ms)
$(for file in "${ANALYSIS_FILES[@]}"; do
  if [ -f "$file" ]; then
    framework=$(basename "$file" | sed 's/_analysis.json//' | sed 's/rest_graphql/graphql_rest/')
    avg_time=$(jq -r '.summary.average_response_time // "N/A"' "$file")
    echo "- $framework: ${avg_time}ms"
  fi
done)

### Success Rates (%)
$(for file in "${ANALYSIS_FILES[@]}"; do
  if [ -f "$file" ]; then
    framework=$(basename "$file" | sed 's/_analysis.json//' | sed 's/rest_graphql/graphql_rest/')
    success_rate=$(jq -r '.summary.success_rate // "N/A"' "$file")
    echo "- $framework: ${success_rate}%"
  fi
done)

## Resource Usage
$(podman stats --no-stream --filter "label=benchmark.phase=1" --format "- {{.Name}}: CPU {{.CPUPerc}}, Memory {{.MemPerc}}")

## Recommendations for Phase 2
- $([ $(jq -r '.summary.average_response_time // 1000' tests/perf/results/graphql_analysis.json 2>/dev/null) -gt 200 ] && echo "GraphQL response times may need optimization" || echo "GraphQL performance acceptable")
- $([ $(jq -r '.summary.average_response_time // 1000' tests/perf/results/rest_analysis.json 2>/dev/null) -gt 200 ] && echo "REST response times may need optimization" || echo "REST performance acceptable")

Generated: $(date)
EOF

echo "✅ Performance data collection validation completed"
echo "📊 Summary report: tests/perf/results/phase1_performance_summary.md"
```

### Step 7: Cleanup and Documentation
**Estimated Time**: 15 minutes

#### 7.1 Stop All Containers
```bash
# Comprehensive cleanup with validation
#!/bin/bash

echo "Starting Phase 1 cleanup..."

# Function to safely stop and remove containers
cleanup_container() {
  local container_name=$1

  if podman ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
    echo "Stopping and removing $container_name..."

    # Stop with timeout
    podman stop "$container_name" --timeout 30 2>/dev/null || true

    # Force stop if still running
    if podman ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
      echo "Force stopping $container_name..."
      podman kill "$container_name" 2>/dev/null || true
      sleep 5
    fi

    # Remove container
    podman rm "$container_name" 2>/dev/null || true
    echo "✅ $container_name cleaned up"
  else
    echo "ℹ️  $container_name not found, skipping"
  fi
}

# Stop framework containers
FRAMEWORKS=("fraiseql" "strawberry" "graphene" "fastapi-rest" "flask-rest")
for fw in "${FRAMEWORKS[@]}"; do
  cleanup_container "$fw"
done

# Stop infrastructure containers
INFRASTRUCTURE=("prometheus" "grafana" "fraiseql-postgres")
for infra in "${INFRASTRUCTURE[@]}"; do
  cleanup_container "$infra"
done

# Clean up volumes (optional - comment out if you want to preserve data)
echo "Cleaning up volumes..."
podman volume rm fraiseql-postgres-data 2>/dev/null || true

# Clean up networks
echo "Cleaning up networks..."
podman network rm benchmark-monitoring 2>/dev/null || true

# Remove dangling images (optional)
echo "Cleaning up dangling images..."
podman image prune -f > /dev/null 2>&1 || true

# Final verification
echo ""
echo "Cleanup verification:"
RUNNING_CONTAINERS=$(podman ps -a --filter "label=benchmark.phase=1" | wc -l)
if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
  echo "✅ All benchmark containers removed"
else
  echo "⚠️  $RUNNING_CONTAINERS benchmark containers still exist:"
  podman ps -a --filter "label=benchmark.phase=1"
fi

echo "✅ Phase 1 cleanup completed"
```

#### 7.2 Document Findings
```bash
# Automated phase completion report generation
#!/bin/bash

echo "Generating Phase 1 completion report..."

# Gather test results
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="phase1_completion_report.md"

# Function to check test result
check_result() {
  local test_name=$1
  local check_command=$2

  if eval "$check_command" > /dev/null 2>&1; then
    echo "- [x] $test_name"
  else
    echo "- [ ] $test_name"
  fi
}

# Generate report
cat > "$REPORT_FILE" << EOF
# Phase 1: Local Podman Testing - Completion Report

**Generated:** $TIMESTAMP
**Test Environment:** $(hostname)

## Test Results Summary

### Framework Startup
$(check_result "FraiseQL: Started successfully" "podman logs fraiseql 2>/dev/null | grep -q 'started\|ready\|running'")
$(check_result "Strawberry: Started successfully" "podman logs strawberry 2>/dev/null | grep -q 'started\|ready\|running'")
$(check_result "Graphene: Started successfully" "podman logs graphene 2>/dev/null | grep -q 'started\|ready\|running'")
$(check_result "FastAPI REST: Started successfully" "podman logs fastapi-rest 2>/dev/null | grep -q 'started\|ready\|running'")
$(check_result "Flask REST: Started successfully" "podman logs flask-rest 2>/dev/null | grep -q 'started\|ready\|running'")

### Health Checks
$(check_result "All frameworks passed health checks" "[ -f tests/perf/jmeter/results/connectivity_test.jtl ] && grep -q '200' tests/perf/jmeter/results/connectivity_test.jtl")
$(check_result "Database connections working" "podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c 'SELECT 1' > /dev/null 2>&1")
$(check_result "API endpoints responding" "curl -f http://localhost:4000/health > /dev/null 2>&1 && curl -f http://localhost:8003/ping > /dev/null 2>&1")

### Functional Testing
$(check_result "GraphQL ping queries working" "curl -f -X POST http://localhost:4000/graphql -H 'Content-Type: application/json' -d '{\"query\": \"{ ping }\"}' | jq -e '.data.ping' > /dev/null 2>&1")
$(check_result "REST ping endpoints working" "curl -f http://localhost:8003/ping > /dev/null 2>&1")
$(check_result "User/post queries working" "curl -f -X POST http://localhost:4000/graphql -H 'Content-Type: application/json' -d '{\"query\": \"query { users(limit: 1) { id } }\"}' | jq -e '.data.users[0].id' > /dev/null 2>&1")
$(check_result "No authentication issues" "curl -f http://localhost:4000/health > /dev/null 2>&1")

### JMeter Integration
$(check_result "JMeter can connect to all frameworks" "[ -f tests/perf/jmeter/results/graphql_comparative.jtl ] && [ -f tests/perf/jmeter/results/rest_comparative.jtl ]")
$(check_result "Test plans execute successfully" "grep -q 'true' tests/perf/jmeter/results/graphql_comparative.jtl 2>/dev/null")
$(check_result "Results collection working" "find tests/perf/jmeter/results -name '*.jtl' -size +100c | grep -q jtl")

### Load Testing
$(check_result "Light load tests completed" "[ -f tests/perf/jmeter/results/light_graphql_load.jtl ] && [ -f tests/perf/jmeter/results/light_rest_load.jtl ]")
$(check_result "No container crashes" "podman ps --filter 'label=benchmark.phase=1' --format '{{.Names}}' | wc -l | grep -q '^5$'")
$(check_result "Resource usage within limits" "podman stats --no-stream --filter 'label=benchmark.phase=1' | awk 'NR>1 {if(\$4+0 > 80) exit 1}' && echo 'true' || echo 'false'")

### Performance Data
$(check_result "Metrics collection working" "curl -f http://localhost:4000/metrics > /dev/null 2>&1 || curl -f http://localhost:8003/metrics > /dev/null 2>&1")
$(check_result "Analysis scripts functioning" "[ -f tests/perf/results/rest_graphql_analysis.json ]")
$(check_result "Data visualization ready" "[ -d tests/perf/jmeter/results/graphql_report ] && [ -d tests/perf/jmeter/results/rest_report ]")

## Performance Metrics Summary

### Response Times (Average)
EOF

# Add performance metrics if available
if [ -f "tests/perf/results/rest_graphql_analysis.json" ]; then
  jq -r '
    .frameworks // {} | to_entries[] |
    select(.key | test("^(fraiseql|strawberry|graphene|fastapi-rest|flask-rest)$")) |
    "- \(.key): \(.value.average_response_time // "N/A")ms"
  ' tests/perf/results/rest_graphql_analysis.json >> "$REPORT_FILE" 2>/dev/null || echo "- Performance data parsing failed" >> "$REPORT_FILE"
else
  echo "- Performance analysis not available" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

### Resource Usage
$(podman stats --no-stream --filter "label=benchmark.phase=1" --format "- {{.Name}}: CPU {{.CPUPerc}}, Memory {{.MemPerc}}" 2>/dev/null || echo "- Resource data not available")

## Issues Found & Resolutions

### Issues:
$(if [ -f "tests/perf/jmeter/results/graphql_comparative.log" ]; then
  ERROR_COUNT=$(grep -c "ERROR\|FATAL" tests/perf/jmeter/results/graphql_comparative.log 2>/dev/null || echo "0")
  if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "1. $ERROR_COUNT errors found in GraphQL tests - Check logs for details"
  else
    echo "1. No significant issues detected"
  fi
else
  echo "1. Test logs not available for analysis"
fi)

### Blockers:
$(if podman ps --filter "label=benchmark.phase=1" --format "{{.Names}}" | grep -q .; then
  echo "1. Some containers still running - Complete cleanup before Phase 2"
elif [ ! -f "tests/perf/results/rest_graphql_analysis.json" ]; then
  echo "1. Analysis data missing - Rerun analysis before Phase 2"
else
  echo "1. No blocking issues identified"
fi)

## Phase 1 Sign-off

- [$(podman ps --filter "label=benchmark.phase=1" --format "{{.Names}}" | wc -l | grep -q '^0$' && echo "x" || echo " ")] All frameworks working in podman
- [$( [ -f "tests/perf/jmeter/results/graphql_comparative.jtl" ] && [ -f "tests/perf/jmeter/results/rest_comparative.jtl" ] && echo "x" || echo " ")] JMeter integration validated
- [$( [ -f "tests/perf/results/rest_graphql_analysis.json" ] && echo "x" || echo " ")] Performance data collection confirmed
- [$( [ ! -f "phase1_cleanup_required" ] && echo "x" || echo " ")] Ready for distributed testing (Phase 2)

**Signed:** Automated Report
**Date:** $TIMESTAMP

---
*This report was auto-generated. Manual review recommended.*
EOF

echo "✅ Phase 1 completion report generated: $REPORT_FILE"
echo "📋 Review the report and address any unchecked items before proceeding to Phase 2"
```

#### 7.2 Document Findings
```bash
# Create phase completion report
cat > phase1_completion_report.md << 'EOF'
# Phase 1: Local Podman Testing - Completion Report

## Test Results Summary

### Framework Startup
- [ ] FraiseQL: Started successfully
- [ ] Strawberry: Started successfully
- [ ] Graphene: Started successfully
- [ ] FastAPI REST: Started successfully
- [ ] Flask REST: Started successfully

### Health Checks
- [ ] All frameworks passed health checks
- [ ] Database connections working
- [ ] API endpoints responding

### Functional Testing
- [ ] GraphQL ping queries working
- [ ] REST ping endpoints working
- [ ] User/post queries working
- [ ] No authentication issues

### JMeter Integration
- [ ] JMeter can connect to all frameworks
- [ ] Test plans execute successfully
- [ ] Results collection working

### Load Testing
- [ ] Light load tests completed
- [ ] No container crashes
- [ ] Resource usage within limits

### Performance Data
- [ ] Metrics collection working
- [ ] Analysis scripts functioning
- [ ] Data visualization ready

## Issues Found & Resolutions

### Issues:
1. Issue description and resolution

### Blockers:
1. Any blocking issues for Phase 2

## Phase 1 Sign-off

- [ ] All frameworks working in podman
- [ ] JMeter integration validated
- [ ] Performance data collection confirmed
- [ ] Ready for distributed testing (Phase 2)

Signed: [Date]
EOF
```

## Phase Validation Checklist

### Pre-Phase Validation
- [ ] Podman installed and working
- [ ] All framework code ready
- [ ] Database schema and data prepared
- [ ] JMeter test plans configured
- [ ] Analysis scripts ready

### Post-Phase Validation
- [ ] All containers start successfully
- [ ] All frameworks respond to health checks
- [ ] JMeter can run tests against all frameworks
- [ ] Performance data collection works
- [ ] No resource conflicts or crashes
- [ ] Analysis reports generate correctly

## Success Metrics

### Quantitative
- All 5 frameworks start within 30 seconds
- Health checks pass for all frameworks
- JMeter tests complete without errors
- Response times < 100ms for simple queries
- No container restarts during testing

### Qualitative
- Clean container logs (no errors)
- Consistent performance across runs
- Proper resource utilization
- Clear performance differentiation between frameworks

## Risk Mitigation

### Identified Risks

1. **Port conflicts**: Multiple frameworks trying to use same ports
2. **Resource exhaustion**: Containers consuming too much CPU/memory
3. **Database connection issues**: Network connectivity or authentication problems
4. **JMeter configuration**: Test plans not matching framework APIs
5. **Container startup failures**: Framework-specific initialization issues
6. **Data consistency**: Different frameworks returning different results
7. **Metrics collection failures**: Monitoring endpoints not working
8. **Disk space exhaustion**: Test data and logs filling up storage

### Mitigation Strategies

1. **Port management**: Use distinct ports (4000, 8001, 8002, 8003, 8004) with validation
2. **Resource monitoring**: Set container memory/CPU limits, monitor usage in real-time
3. **Network testing**: Use host.containers.internal, validate connectivity before starting frameworks
4. **Incremental testing**: Test individual frameworks first, then concurrent execution
5. **Error handling**: Comprehensive logging and error detection in all scripts
6. **Data validation**: Cross-framework consistency checks and data integrity validation
7. **Monitoring setup**: Validate metrics endpoints and monitoring stack before load testing
8. **Cleanup procedures**: Automated cleanup with verification and manual override options

### Troubleshooting Guide

#### Common Issues and Solutions

**Issue: Container fails to start**
```bash
# Check container logs
podman logs <container_name>

# Check resource availability
free -h
df -h .

# Verify image exists
podman images | grep <framework>

# Try manual start with verbose logging
podman run -it --rm <image_name> /bin/bash
```

**Issue: Database connection failures**
```bash
# Test database connectivity
podman exec -it fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "SELECT 1;"

# Check database logs
podman logs fraiseql-postgres

# Verify environment variables in framework containers
podman exec <framework> env | grep DB_

# Test network connectivity
podman exec <framework> ping host.containers.internal
```

**Issue: JMeter connection errors**
```bash
# Test basic connectivity
curl -v http://localhost:<port>/health

# Check JMeter logs
cat tests/perf/jmeter/results/*.log | grep ERROR

# Validate test plan
jmeter -t comparative-test-plan.jmx -v

# Test with simple plan
jmeter -n -t datasets/connectivity_test.jmx
```

**Issue: High resource usage**
```bash
# Monitor resource usage
podman stats

# Check for memory leaks
podman logs <framework> | grep -i "memory\|leak\|gc"

# Adjust resource limits
podman update --memory=1g --cpus=0.5 <framework>

# Restart with lower limits
podman stop <framework>
podman rm <framework>
# Re-run startup with adjusted parameters
```

**Issue: Performance data collection fails**
```bash
# Test metrics endpoints
curl http://localhost:<port>/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq .

# Validate analysis script
python3 -c "import run_rest_graphql_comparison; print('Import OK')"

# Check result file permissions
ls -la tests/perf/results/
```

#### Emergency Procedures

**Complete Environment Reset**:
```bash
# Stop all containers
podman stop $(podman ps -q)

# Remove all containers and volumes
podman rm -f $(podman ps -aq)
podman volume rm $(podman volume ls -q)

# Clean up networks
podman network rm $(podman network ls -q)

# Remove images (optional)
podman rmi $(podman images -q)

# Restart podman service
sudo systemctl restart podman
```

**Selective Framework Restart**:
```bash
# Stop problematic framework
podman stop <framework>
podman rm <framework>

# Rebuild if needed
cd frameworks/<framework>
podman build -t <framework>-debug .

# Restart with debug logging
podman run -d --name <framework> \
  -e LOG_LEVEL=DEBUG \
  <other_env_vars> \
  <framework>-debug
```

**Data Reset**:
```bash
# Reset database
podman exec fraiseql-postgres psql -U benchmark -d fraiseql_benchmark -c "
  DROP SCHEMA benchmark CASCADE;
  CREATE SCHEMA benchmark;
"

# Reinitialize data
podman exec fraiseql-postgres /docker-entrypoint-initdb.d/init.sql

# Clear test results
rm -rf tests/perf/jmeter/results/*
rm -f tests/perf/results/*.json
```

## Phase 2 Preparation

### Artifacts Ready for Distributed Testing
- [ ] All container images built and tested
- [ ] JMeter test plans validated
- [ ] Database schema confirmed
- [ ] Analysis scripts working
- [ ] Performance baselines established

### Distributed Testing Considerations
- [ ] Container images can be transferred to test machines
- [ ] Network configuration for cross-machine communication
- [ ] JMeter distributed testing setup
- [ ] Result aggregation strategy
- [ ] Monitoring and observability for distributed setup

## Security Considerations

### Local Testing Security Measures

1. **Container Isolation**: All frameworks run in separate containers with resource limits
2. **Database Security**: Local PostgreSQL with benchmark credentials (not production)
3. **Network Security**: Containers communicate via defined networks, no external exposure except mapped ports
4. **Credential Management**: Test credentials clearly marked and isolated
5. **Log Security**: No sensitive data logged during testing
6. **Cleanup Security**: Automated removal of test data and credentials

### Security Validation Checklist

- [ ] No hardcoded production credentials in framework code
- [ ] Database credentials are test-only and clearly marked
- [ ] Container images don't contain sensitive data
- [ ] Logs don't expose authentication tokens or user data
- [ ] Network exposure limited to localhost only
- [ ] Test data is anonymized and appropriate for benchmarking

## Timeline

### Detailed Breakdown

- **Prerequisites Validation**: 15 minutes
- **Infrastructure Setup (PostgreSQL)**: 15 minutes
- **Framework Image Building**: 30 minutes
- **Individual Framework Testing**: 45 minutes
- **Concurrent Framework Testing**: 30 minutes
- **Health Checks & Functional Testing**: 45 minutes
- **Database Connection Validation**: 20 minutes
- **JMeter Integration Testing**: 40 minutes
- **Load Testing & Resource Monitoring**: 45 minutes
- **Performance Data Collection Setup**: 30 minutes
- **Data Collection Validation & Analysis**: 25 minutes
- **Cleanup & Documentation**: 20 minutes

### Total Estimated Time: ~6 hours

### Time Distribution
- **Setup & Building**: ~1 hour (20%)
- **Individual Testing**: ~1.5 hours (25%)
- **Integration Testing**: ~1.5 hours (25%)
- **Load Testing & Analysis**: ~1.5 hours (25%)
- **Cleanup & Documentation**: ~0.5 hours (5%)

### Parallel Execution Opportunities
- Framework image building can be parallelized
- Individual framework testing can run concurrently (different terminals)
- JMeter testing for GraphQL and REST can run simultaneously
- Resource monitoring can run in background during load tests

### Contingency Time
- Add 2 hours buffer for troubleshooting and unexpected issues
- Individual framework debugging: 30-60 minutes per framework if needed
- Database setup issues: 30 minutes
- JMeter configuration problems: 45 minutes

## Exit Criteria

Phase 1 is complete when ALL of the following conditions are met:

### Functional Requirements
- [ ] All 5 frameworks (FraiseQL, Strawberry, Graphene, FastAPI REST, Flask REST) start successfully in podman containers
- [ ] All frameworks pass health checks and respond to basic API calls within 100ms
- [ ] Database connections are established and functional for all frameworks
- [ ] JMeter can execute test plans against all frameworks with >95% success rate
- [ ] Basic GraphQL queries (ping, users, posts) work for GraphQL frameworks
- [ ] Basic REST endpoints (ping, users, posts) work for REST frameworks

### Performance Requirements
- [ ] Performance data collection (metrics endpoints) working for monitoring-enabled frameworks
- [ ] Light load tests (30 seconds, 10 users/framework) complete without container crashes
- [ ] Average response times < 200ms under light load
- [ ] Resource usage stays within allocated limits (no >80% memory, >70% CPU sustained)
- [ ] Analysis scripts generate valid performance reports

### Quality Requirements
- [ ] Cross-framework data consistency (same user/post counts within frameworks)
- [ ] No critical errors in container logs during testing
- [ ] Automated cleanup procedures work correctly
- [ ] Phase completion report generated with all test results documented

### Readiness Requirements
- [ ] All container images properly built and tagged for distribution
- [ ] JMeter test plans validated and working
- [ ] Database schema and test data confirmed
- [ ] Monitoring and analysis infrastructure functional
- [ ] No outstanding issues that would block Phase 2 distributed testing

### Sign-off Requirements
- [ ] Phase completion report reviewed and approved
- [ ] Test results meet or exceed success criteria
- [ ] All frameworks ready for horizontal scaling in Phase 2
- [ ] Performance baselines established for comparative analysis

**Phase 1 Status**: ☐ Ready for Phase 2 ☐ Needs Remediation

**Remediation Required**: [List any issues that need to be addressed before Phase 2]

**Approved By**: ________________________ Date: _______________