# FraiseQL Performance Assessment - Phase 2: Benchmarking Methodology Improvements

## Phase Overview

**Goal**: Replace the current curl-based sequential testing with proper load testing methodology using JMeter, implementing warmup phases, statistically significant request volumes, and concurrent execution patterns.

**Scope**: Transform the benchmarking infrastructure from basic API testing to production-grade performance evaluation.

**Context**: The current `run_comparative_benchmarks.py` uses sequential curl commands with only 18 requests per framework, providing statistically insignificant results. This phase establishes proper benchmarking foundations with JMeter integration, warmup phases, concurrent execution, and statistical analysis.

**Success Criteria**:
- JMeter executes with 100+ concurrent threads across multiple frameworks
- Each scenario runs minimum 1000+ requests for statistical validity
- Warmup phase (2-3 minutes) precedes all measurement phases
- Cold start vs warm system performance captured separately
- Percentile distributions (p50/p95/p99/p99.9) calculated with confidence intervals
- Results reproducible with <10% variance between runs
- All frameworks tested concurrently rather than sequentially

## Learning Objectives

As a junior engineer, by completing Phase 2 you will learn:

1. **Containerization Fundamentals**: Podman/Docker container lifecycle, networking, resource limits
2. **Multi-Service Architecture**: Running multiple services concurrently with proper isolation
3. **Database Connectivity**: PostgreSQL connection patterns, health checks, connection pooling basics
4. **API Testing**: REST and GraphQL endpoint validation, health check implementation
5. **Load Testing Tools**: JMeter basics, test plan structure, result interpretation
6. **Infrastructure Automation**: Bash scripting for container management, error handling
7. **Debugging Distributed Systems**: Log analysis, network troubleshooting, resource monitoring
8. **Documentation Best Practices**: Comprehensive runbooks, troubleshooting guides

## Prerequisites and Knowledge Requirements

### Required Knowledge
- Basic Linux command line usage (ls, cd, chmod, grep, etc.)
- Basic SQL concepts (SELECT, tables, connections)
- Basic HTTP concepts (GET/POST, status codes, JSON)
- Basic programming concepts (variables, loops, conditionals)

### Required Tools
- Python 3.8+ with pandas, numpy, scipy
- JMeter 5.6+ with command-line interface
- curl for health checks
- Git for version control

### Environment Setup
```bash
# Verify JMeter installation
jmeter --version

# Verify Python packages
python3 -c "import pandas, numpy, scipy, argparse; print('All packages available')"

# Install required packages if missing
pip install pandas numpy scipy

# Check JMeter plugins
ls $JMETER_HOME/lib/ext/ | grep -E "(jpgc|jmeter-plugins)"
```

### Dependencies Check
```bash
# Create requirements-benchmark.txt
cat > requirements-benchmark.txt << 'EOF'
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.5.0
seaborn>=0.11.0
EOF

pip install -r requirements-benchmark.txt
```

## Implementation Steps

### Step 1: Infrastructure Setup
**Estimated Time**: 30 minutes

#### 1.1 Start PostgreSQL Database

**Learning Objective**: Understand containerized database setup and initialization

**What you'll learn**:
- Podman volume management for data persistence
- Container resource limits (memory, CPU)
- Database initialization scripts
- Health check verification

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

**Verification Steps**:
```bash
# Check container is running
podman ps | grep fraiseql-postgres

# Check logs for successful initialization
podman logs fraiseql-postgres | tail -20
```

**Common Issues**:
- **Port 5432 already in use**: `sudo netstat -tlnp | grep 5432` to find conflict
- **Volume creation fails**: Check disk space with `df -h`
- **Initialization timeout**: Database may need more time, check logs

#### 1.2 Verify Database Setup

**Learning Objective**: Database connectivity testing and schema validation

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
```

**Expected Output**:
```
 table_name | count
------------+--------
 users      | 1000
 posts      | 5000
 comments   | 10000
```

### Step 2: Framework Container Testing
**Estimated Time**: 2 hours

#### 2.1 Build All Framework Images

**Learning Objective**: Multi-stage container builds and image management

**What you'll learn**:
- Container image building process
- Build optimization (caching, resource limits)
- Image tagging and organization
- Build failure debugging

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

**Learning Objective**: Individual service testing and debugging

**What you'll learn**:
- Container environment variables
- Port mapping and networking
- Container resource allocation
- Startup time optimization
- Log analysis for debugging

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
  if ! curl -f -m 10 -s "http://localhost:$port/health" > /dev/null; then
    echo "❌ Health check failed"
    podman logs "test-$framework"
    return 1
  fi

  # Framework-specific API tests
  case $framework in
    fraiseql|strawberry|graphene)
      # GraphQL ping test
      if ! curl -f -m 10 -s -X POST "http://localhost:$port/graphql" \
        -H "Content-Type: application/json" \
        -d '{"query": "{ ping }"}' | jq -e '.data.ping' > /dev/null; then
        echo "❌ GraphQL ping failed"
        return 1
      fi

      # GraphQL user query test
      if ! curl -f -m 10 -s -X POST "http://localhost:$port/graphql" \
        -H "Content-Type: application/json" \
        -d '{"query": "query { users(limit: 1) { id username } }"}' | jq -e '.data.users[0].id' > /dev/null; then
        echo "❌ GraphQL user query failed"
        return 1
      fi
      ;;
    fastapi-rest|flask-rest)
      # REST ping test
      if ! curl -f -m 10 -s "http://localhost:$port/ping" > /dev/null; then
        echo "❌ REST ping failed"
        return 1
      fi

      # REST user endpoint test
      if ! curl -f -m 10 -s "http://localhost:$port/users?limit=1" | jq -e '.[0].id' > /dev/null; then
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

### Step 3: Framework Validation
**Estimated Time**: 45 minutes

#### 3.1 Health Check All Frameworks

**Learning Objective**: Comprehensive system health validation

**What you'll learn**:
- Automated health checking
- Error handling in scripts
- JSON response parsing with jq
- Framework-specific health patterns

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

**Learning Objective**: End-to-end API testing and data consistency validation

**What you'll learn**:
- GraphQL vs REST API patterns
- Error handling in API responses
- Data consistency validation
- Cross-framework comparison

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

### Step 4: JMeter Integration Testing
**Estimated Time**: 30 minutes

#### 4.1 Test JMeter Connection

**Learning Objective**: Load testing tool integration and validation

**What you'll learn**:
- JMeter test plan execution
- Result file parsing
- Success rate calculation
- Error analysis

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

### Step 5: Load Testing Validation
**Estimated Time**: 30 minutes

#### 5.1 Run Light Load Tests

**Learning Objective**: Basic load testing and resource monitoring

**What you'll learn**:
- Load test execution patterns
- Resource usage monitoring
- Performance degradation detection
- Concurrent execution management

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

## Testing Strategy

### Unit Testing (Individual Components)
- **Container startup**: Verify each framework starts within timeout
- **Database connectivity**: Test connection from each container
- **API endpoints**: Validate health checks and basic functionality
- **JMeter integration**: Test tool can connect and execute plans

### Integration Testing (Multi-Component)
- **Concurrent execution**: All frameworks running simultaneously
- **Resource limits**: No container exceeds allocated resources
- **Network isolation**: Containers communicate correctly
- **Data consistency**: Same data returned across frameworks

### Performance Testing (Load Validation)
- **Baseline performance**: Simple queries < 100ms
- **Concurrent load**: 10-20 users per framework
- **Resource monitoring**: CPU/memory usage within limits
- **Stability testing**: 30-minute continuous operation

## Common Pitfalls and Solutions

### 1. Port Conflicts
**Problem**: Multiple containers trying to use same port
**Solution**: Use distinct ports (4000, 8001, 8002, 8003, 8004)
**Prevention**: Document port assignments clearly

### 2. Database Connection Issues
**Problem**: Frameworks can't connect to PostgreSQL
**Solution**:
```bash
# Check database is running
podman ps | grep postgres

# Test connection manually
psql -h localhost -U benchmark -d fraiseql_benchmark

# Verify environment variables in container
podman exec <framework> env | grep DB_
```

### 3. Container Resource Exhaustion
**Problem**: Memory/CPU limits too low causing crashes
**Solution**: Monitor usage and adjust limits:
```bash
# Check current usage
podman stats

# Adjust limits
podman update --memory=2g --cpus=1 <container>
```

### 4. JMeter Configuration Errors
**Problem**: Test plans not matching framework APIs
**Solution**:
```bash
# Validate test plan
jmeter -t testplan.jmx -v

# Check JMeter logs
cat jmeter.log | grep ERROR
```

### 5. Timing Issues
**Problem**: Tests run before services are ready
**Solution**: Implement proper wait logic:
```bash
# Wait for health check
timeout 60 bash -c 'until curl -f http://localhost:4000/health; do sleep 2; done'
```

## Best Practices Learned

### 1. Infrastructure as Code
- Document all container configurations
- Use consistent naming conventions
- Version control configuration files
- Automate setup and teardown

### 2. Error Handling
- Always check return codes: `set -e`
- Use timeout commands for network operations
- Log errors with context
- Provide clear error messages

### 3. Resource Management
- Set appropriate resource limits
- Monitor usage during testing
- Clean up resources after tests
- Document resource requirements

### 4. Testing Strategy
- Test components individually first
- Then test integration scenarios
- Validate in staging before production
- Automate regression testing

### 5. Documentation
- Document every step with expected outputs
- Include troubleshooting sections
- Version control all scripts and configurations
- Maintain runbooks for common issues

## Verification Criteria

### Phase 1 Completion Checklist

**Infrastructure Setup**
- [ ] PostgreSQL container running with proper volumes
- [ ] Database initialized with schema and data
- [ ] All framework containers built successfully
- [ ] Resource limits set appropriately

**Individual Framework Testing**
- [ ] Each framework starts within 30 seconds
- [ ] Health endpoints respond correctly
- [ ] Basic API calls work (ping, simple queries)
- [ ] Database connections established
- [ ] Response times < 100ms for simple queries

**Concurrent Framework Testing**
- [ ] All 5 frameworks running simultaneously
- [ ] No port conflicts or resource issues
- [ ] Network communication working
- [ ] Stable for at least 30 minutes

**JMeter Integration**
- [ ] JMeter can connect to all frameworks
- [ ] Test plans execute without errors
- [ ] Results collected successfully
- [ ] Basic load testing works (10-20 users)

**Performance Validation**
- [ ] Light load tests complete successfully
- [ ] Resource usage within allocated limits
- [ ] No container crashes or restarts
- [ ] Performance data collection working

**Documentation and Cleanup**
- [ ] All scripts documented and working
- [ ] Troubleshooting guide created
- [ ] Cleanup procedures verified
- [ ] Phase completion report generated

## References and Resources

### Documentation
- [Podman User Guide](https://docs.podman.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [JMeter User Manual](https://jmeter.apache.org/usermanual/)
- [curl Documentation](https://curl.se/docs/)

### Tools
- [jq Manual](https://stedolan.github.io/jq/manual/)
- [Bash Scripting Guide](https://tldp.org/LDP/Bash-Beginners-Guide/html/)

### Best Practices
- [Twelve-Factor App](https://12factor.net/) for containerized applications
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/) for reliability
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## Phase Sign-off

**Phase 2 Status**: ☐ Ready for Phase 3 ☐ Needs Remediation

**Completed By**: ________________________ Date: _______________

**Reviewed By**: ________________________ Date: _______________

**Key Improvements Demonstrated**:
1. Statistical validity (1000+ requests per test)
2. Proper warmup phases implemented
3. Cold vs warm performance comparison
4. Concurrent multi-framework testing
5. Confidence intervals and percentiles calculated

**Issues Identified**:
1.
2.
3.

**Remediation Plan**:
1.
2.
3.</content>
<parameter name="filePath">.phases/phase-1-local-podman-testing-detailed.md