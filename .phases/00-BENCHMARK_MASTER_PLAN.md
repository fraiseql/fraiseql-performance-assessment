# FraiseQL Performance Benchmark - Master Implementation Plan

**Status**: Active
**Last Updated**: 2025-12-26
**Purpose**: Complete guide for running comprehensive performance benchmarks across all frameworks

---

## 📋 Executive Summary

This master plan provides a complete, step-by-step guide for executing the FraiseQL performance benchmark suite. It covers:

- **Current Active Frameworks**: 21 enabled in docker-compose + 13 additional frameworks available
- **Total Frameworks Available**: 34 (including ORM variants and naive implementations)
- **Test Coverage**: 8 workload types × multiple load configurations
- **Infrastructure**: Docker-based with Prometheus/Grafana monitoring + PostgreSQL 15 CQRS schema
- **Output**: Comparative performance metrics, latency distributions, resource analysis, N+1 detection

### Current System Status
- ✅ **21 frameworks configured** in docker-compose (GraphQL, REST, ORM, Naive variants)
- ✅ **Database schema** CQRS pattern with Trinity identifiers (benchmark.tb_* tables)
- ✅ **8 JMeter workloads** fully defined and tested
- ✅ **Monitoring stack** ready (Prometheus/Grafana on ports 9090/3000)
- ✅ **Test infrastructure** complete (integration, QA, performance 3-layer system)
- ✅ **Build artifacts** present for 11 frameworks (Node.js, Rust, Java, PHP, Ruby)
- ⚠️ **3 frameworks disabled** (async-graphql, apollo-orm compilation issues; jmeter image unavailable)
- ℹ️ **13 frameworks not in docker-compose** (missing Dockerfiles or not yet configured)

---

## 🏗️ Phase Structure

### Phase 0: Pre-Benchmark Validation (15 mins)
**Objective**: Ensure all infrastructure is ready

**Steps**:
1. Verify Docker network exists
   ```bash
   docker network ls | grep fraiseql-benchmark
   ```
2. Check database connectivity and data
   ```bash
   PGPASSWORD=benchmark123 psql -h localhost -p 5434 -U benchmark -d fraiseql_benchmark \
     -c "SELECT COUNT(*) as users FROM benchmark.tb_user;"
   ```
3. Verify all containers can start
   ```bash
   docker-compose ps
   ```

**Acceptance Criteria**:
- Docker network is active
- Database has >1000 users (minimum test data)
- All 12 services show "Up" status

**Troubleshooting**:
- If network missing: `docker network create fraiseql-benchmark`
- If database empty: `uv run --with psycopg generate_posts.py`
- If containers failing: `docker-compose logs [service-name]`

---

### Phase 1: Infrastructure Startup (5-10 mins)
**Objective**: Start all services and verify health checks pass

**Steps**:
1. Start all services
   ```bash
   cd /home/lionel/code/fraiseql-performance-assessment
   docker-compose up -d
   ```

2. Wait for health checks (60-90 seconds)
   ```bash
   watch docker-compose ps
   ```

3. Verify all services healthy
   ```bash
   docker-compose ps | grep -c "healthy"  # Should show 12+
   ```

**Acceptance Criteria**:
- All 12 framework services show "healthy" status
- All services running without restarts
- No error logs in past 30 seconds

**Common Issues & Fixes**:
| Issue | Solution |
|-------|----------|
| Containers crashing | Check logs: `docker-compose logs [service]` |
| Network connectivity | Restart network: `docker network prune && docker-compose down && docker-compose up` |
| Database not responding | Increase shared_buffers in docker-compose.yml |
| Memory pressure | Reduce `DB_SHARED_BUFFERS` or close other apps |

---

### Phase 2: Benchmark Selection (2 mins)
**Objective**: Choose appropriate test profile

**Options**:

| Profile | Duration | Tests | Use Case |
|---------|----------|-------|----------|
| `--quick` | ~20 mins | 5 | Initial validation, CI/CD |
| `--medium` | ~1 hour | 45 | **RECOMMENDED** - Standard benchmarking |
| `--full` | 2+ hours | 160+ | Complete stress testing, research |

**What Gets Tested**:
- **21 Active Frameworks** (configured in docker-compose.yml):
  - **8 GraphQL**: fraiseql, strawberry, graphene, apollo, spring-boot, spring-boot-orm, gqlgen-orm-naive, hasura
  - **7 REST**: fastapi-rest, actix-web-rest, express-rest, spring-boot, spring-boot-orm, gin-orm-naive (alt Go)
  - **6 ORM/ORM-Naive**: strawberry-orm-naive, fastapi-orm-naive, apollo-orm-naive, express-orm-naive, gqlgen-orm-naive, gin-orm-naive
  - **Plus**: Hasura (managed GraphQL)
- **8 Workload Types**: simple, parameterized, aggregation, pagination, fulltext, deep-traversal, mutations, mixed
- **4 Load Levels**: smoke, small, medium, large
- **13 Additional Frameworks** available (not yet in docker-compose, can be added)

---

### Phase 3: Execute Benchmark (20 mins to 2+ hours)
**Objective**: Run comprehensive performance tests

**Basic Execution**:
```bash
cd /home/lionel/code/fraiseql-performance-assessment

# Quick baseline (recommended for first run)
./run-comprehensive-benchmark.sh --quick

# Medium tests (recommended for standard benchmarking)
./run-comprehensive-benchmark.sh --medium

# Full comprehensive tests
./run-comprehensive-benchmark.sh --full
```

**Advanced Options**:
```bash
# Test specific framework
./run-comprehensive-benchmark.sh --medium --framework strawberry

# Test specific workload
./run-comprehensive-benchmark.sh --medium --workload simple

# Test specific load configuration
./run-comprehensive-benchmark.sh --full --config large

# Combine options
./run-comprehensive-benchmark.sh --full --framework fraiseql --workload deep-traversal
```

**Monitoring During Execution**:

**Option 1: Terminal Monitoring**
```bash
# In separate terminal, watch progress
tail -f tests/perf/results/benchmark_*/benchmark.log

# Monitor system resources
top
```

**Option 2: Grafana Dashboards** (real-time metrics)
```bash
# Access at http://localhost:3000 (admin/admin)
# View dashboards:
# - Request rates per framework
# - Response time distributions
# - Error rates
# - Resource usage (CPU, memory, connections)
```

**What's Happening**:
1. Script initializes test suite
2. Starts JMeter processes for each test
3. Generates requests at configured thread counts
4. Collects `.jtl` files with raw results
5. Generates HTML reports
6. Stores results in timestamped directory

**Acceptance Criteria**:
- All tests complete without crashing
- Error rates <1% per framework
- All HTML reports generated
- No container restarts during benchmark

---

### Phase 4: Results Collection & Analysis (15-30 mins)
**Objective**: Collect and analyze benchmark results

**Results Location**:
```
tests/perf/results/
└── benchmark_YYYYMMDD_HHMMSS/
    ├── benchmark.log                  # Master log
    ├── ANALYSIS_GUIDE.md             # Analysis instructions
    └── [framework]/[workload]/[config]/YYYYMMDD_HHMMSS/
        ├── results.jtl               # Raw JMeter results
        ├── jmeter.log                # Execution log
        └── html/index.html           # Interactive report
```

**View Results**:

**Option 1: HTML Reports** (recommended)
```bash
# Find latest results
RESULT_DIR=$(ls -td tests/perf/results/benchmark_*/ | head -1)

# Open in browser
firefox $RESULT_DIR/[framework]/[workload]/[config]/*/html/index.html

# Or view master log
cat $RESULT_DIR/benchmark.log | tail -100
```

**Option 2: CSV Export** (for spreadsheet analysis)
```bash
cd $RESULT_DIR
python3 ../../scripts/analyze-results.py . > comparison.csv

# Import comparison.csv into Excel/Google Sheets for further analysis
```

**Key Metrics to Review**:

| Metric | Meaning | Target |
|--------|---------|--------|
| **Throughput (RPS)** | Requests per second | Higher is better |
| **Avg Latency** | Average response time | <30ms for GraphQL |
| **P95 Latency** | 95th percentile (worst 5%) | <50ms for GraphQL |
| **P99 Latency** | 99th percentile (worst 1%) | <100ms for GraphQL |
| **P99.9 Latency** | 99.9th percentile (worst 0.1%) | <200ms for GraphQL |
| **Error %** | % of failed requests | <1% |

**Framework Comparison Template**:
```
Framework Rankings (by throughput - simple workload):
1. [Framework A]: XXX RPS (avg: Xms)
2. [Framework B]: XXX RPS (avg: Xms)
3. [Framework C]: XXX RPS (avg: Xms)
...

Framework Rankings (by p99 latency - deep-traversal):
1. [Framework A]: Xms p99
2. [Framework B]: Xms p99
3. [Framework C]: Xms p99
...
```

---

### Phase 5: Interpretation & Reporting (30 mins to 2 hours)
**Objective**: Generate insights and findings

**Analysis Questions to Answer**:

1. **Performance Hierarchy**
   - Which frameworks are fastest overall?
   - Which are optimized for throughput vs latency?
   - How do GraphQL vs REST compare?

2. **Language Comparison**
   - How do Rust implementations compare to Python/Node.js/Go/Java?
   - What's the speed multiplier (e.g., "Rust is 2.5x faster than Python")?

3. **Workload Sensitivity**
   - Which workloads stress different frameworks differently?
   - Which frameworks degrade gracefully under load?
   - Where do naive ORM implementations fail?

4. **Resource Efficiency**
   - CPU usage per framework
   - Memory usage and stability
   - Connection pool efficiency

5. **Scalability**
   - How does performance change from smoke → small → medium → large?
   - Linear degradation or cliff effects?
   - Which frameworks maintain consistency?

**Create Performance Report**:

**Template**:
```markdown
# FraiseQL Performance Benchmark Report
**Date**: [Date]
**Test Profile**: [quick/medium/full]
**Duration**: [Total time]

## Executive Summary
[1-2 paragraphs summarizing key findings]

## Framework Rankings

### Overall Throughput (requests/sec)
[Ranked list with metrics]

### Latency (p99)
[Ranked list with metrics]

## Detailed Analysis

### GraphQL Frameworks
- [Framework]: [Key findings]
- [Framework]: [Key findings]

### REST Frameworks
- [Framework]: [Key findings]

### Language Comparison
- Rust: [Summary]
- Python: [Summary]
- Node.js: [Summary]
- Go: [Summary]
- Java: [Summary]

## Workload Analysis
[For each workload type: which frameworks excel, which struggle]

## Resource Usage
[CPU, memory, connection analysis]

## Naive ORM Impact
[N+1 query effect on performance]

## Conclusions & Recommendations
[Strategic insights for framework selection]
```

---

## 🔴 Disabled/Broken Frameworks & Missing Deployments

### Explicitly Disabled in docker-compose.yml (3)
These frameworks are in the codebase but commented out:

1. **async-graphql** (Rust)
   - Issue: Compilation error - missing `pk_post` field in Post struct (line 262 of schema.rs)
   - Location: `frameworks/async-graphql/src/schema.rs:262`
   - Build artifact: `target/` directory present (compiled binary available)
   - Fix Effort: Low (add missing field to Post struct initialization)
   - Impact: Removes Rust GraphQL coverage (actix-web-rest still available for Rust REST)

2. **apollo-orm** (Node.js/TypeScript)
   - Issue: Missing critical module file `entities/index.js`
   - Location: `frameworks/apollo-orm`
   - Build artifact: `node_modules/` present (dependencies installed)
   - Fix Effort: Low (create missing module or rebuild)
   - Impact: Removes Node.js ORM coverage (express-orm still available)

3. **jmeter-master** (JMeter Load Generator)
   - Issue: Docker image `justb4/jmeter:5.6` not available on Docker Hub
   - Location: docker-compose.yml service definition
   - Build artifact: N/A (external service)
   - Fix Effort: Medium (use alternative image or build custom)
   - Impact: Optional (benchmarking uses run-comprehensive-benchmark.sh, not this service)

### Not Included in docker-compose.yml (13 total)
Frameworks in filesystem but with no docker-compose configuration:

#### Missing Dockerfiles (8 frameworks)
These frameworks exist but lack Dockerfile for Docker deployment:

1. **go-gqlgen** (Go GraphQL) - No Dockerfile
2. **ruby-rails-fixed** (Ruby on Rails variant) - No Dockerfile
3. **strawberry-orm** (Python ORM) - No Dockerfile
4. **fastapi-orm** (Python REST ORM) - No Dockerfile
5. **gin-orm** (Go REST ORM) - No Dockerfile
6. **gqlgen-orm** (Go GraphQL ORM) - No Dockerfile
7. **graphene-orm** (Python GraphQL ORM) - No Dockerfile
8. **flask-rest** (Python REST) - Dockerfile exists but not in docker-compose

#### Not Yet Configured (5 frameworks)
These have Dockerfiles but are not yet added to docker-compose.yml:

1. **csharp-dotnet** (C#/.NET) - Build artifacts not present
2. **php-laravel** (PHP) - Vendor dependencies present, ready for deployment
3. **ruby-rails** (Ruby) - Vendor dependencies present, ready for deployment
4. **go-graphql-go** (Go GraphQL) - Alternative Go GraphQL implementation
5. **gin-rest** (Go REST) - Alternative Go REST implementation

#### Special Cases
1. **hasura** (GraphQL as a Service) - Uses pre-built image (v2.36.0), not a build from Dockerfile

### Framework Status Matrix

| Framework | Type | Language | Docker | Dockerfile | Build Ready | Issue |
|-----------|------|----------|--------|-----------|-------------|-------|
| async-graphql | GraphQL | Rust | ❌ Disabled | ✅ | ✅ Yes | Compilation error in schema.rs |
| apollo-orm | ORM | Node.js | ❌ Disabled | ✅ | ✅ Yes | Missing entities/index.js |
| jmeter-master | Tool | Java | ❌ Disabled | ❌ | ❌ | Image unavailable |
| go-gqlgen | GraphQL | Go | ❌ Missing | ❌ | ❌ | No Dockerfile |
| strawberry-orm | ORM | Python | ❌ Missing | ❌ | ❌ | No Dockerfile |
| fastapi-orm | ORM | Python | ❌ Missing | ❌ | ❌ | No Dockerfile |
| gin-orm | ORM | Go | ❌ Missing | ❌ | ❌ | No Dockerfile |
| gqlgen-orm | ORM | Go | ❌ Missing | ❌ | ❌ | No Dockerfile |
| graphene-orm | ORM | Python | ❌ Missing | ❌ | ❌ | No Dockerfile |
| flask-rest | REST | Python | ❌ Missing | ✅ | ❌ | Not in docker-compose |
| csharp-dotnet | Misc | C#/.NET | ❌ Missing | ✅ | ❓ | Not configured |
| php-laravel | REST | PHP | ❌ Missing | ✅ | ✅ Yes | Not configured |
| ruby-rails | REST | Ruby | ❌ Missing | ✅ | ✅ Yes | Not configured |
| go-graphql-go | GraphQL | Go | ❌ Missing | ✅ | ❌ | Not configured |
| gin-rest | REST | Go | ❌ Missing | ✅ | ❌ | Not configured |

---

## 📊 Expected Benchmark Results

### Baseline Performance (from recent runs)

**Smoke Test** (single thread, minimal data):
```
Graphene (Python):   ~6ms avg
Strawberry (Python): ~11ms avg
gqlgen (Go):         ~11ms avg
FraiseQL (Rust):     ~13ms avg
Apollo (Node.js):    ~14ms avg
```

**Under Load** (medium config - 20 threads, 60 sec):
- Throughput: 200-500 RPS per framework
- P95 Latency: 20-40ms
- P99 Latency: 40-80ms
- Error Rate: <1%

### Typical Patterns
- **Rust**: Lowest latency, highest throughput
- **Go**: Good latency, solid throughput
- **Python**: Higher latency, good consistency
- **Node.js**: Moderate latency, variable
- **Java**: Warmup effects, stable when warmed

---

## 🛠️ Troubleshooting

### Benchmark Execution Issues

**Problem: "Could not connect to framework at port XXXX"**
```bash
# Check if container is running
docker-compose ps [service-name]

# Restart if needed
docker-compose restart [service-name]

# Check logs
docker-compose logs [service-name] | tail -50
```

**Problem: "Error rate >1%"**
```bash
# Check framework logs for errors
docker-compose logs [service-name] | grep -i "error\|exception"

# Check database connectivity
docker-compose exec [service-name] sh -c "psql -h postgres -d fraiseql_benchmark -c 'SELECT 1'"

# Check for slow queries
PGPASSWORD=benchmark123 psql -h localhost -p 5434 -U benchmark -d fraiseql_benchmark \
  -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Problem: "Out of memory or high CPU during benchmark"**
```bash
# Monitor resource usage
watch -n 1 'docker stats'

# Reduce load during testing
./run-comprehensive-benchmark.sh --quick  # Instead of --full

# Reduce database size
# Edit .env: DATA_VOLUME=small
docker-compose down
docker volume rm fraiseql-performance-assessment_postgres_data
docker-compose up -d
```

**Problem: "Timeout waiting for containers to be healthy"**
```bash
# Increase health check timeout in docker-compose.yml
# Change 'retries: 3' to 'retries: 5' for slow systems

# Or manually verify via HTTP
for port in 4000 8011 8002 4001 8003 8015 8005 8007; do
  echo "Port $port:"; curl -s http://localhost:$port/health | head -c 100
done
```

---

## 📝 Command Reference

### Quick Start
```bash
cd /home/lionel/code/fraiseql-performance-assessment

# Validate infrastructure
docker-compose ps

# Generate test data if needed
uv run --with psycopg generate_posts.py

# Start services
docker-compose up -d

# Run benchmark (pick one)
./run-comprehensive-benchmark.sh --quick      # 20 mins
./run-comprehensive-benchmark.sh --medium     # 1 hour (RECOMMENDED)
./run-comprehensive-benchmark.sh --full       # 2+ hours
```

### View Results
```bash
# Find latest results
RESULT_DIR=$(ls -td tests/perf/results/benchmark_*/ | head -1)

# View in browser
firefox $RESULT_DIR/[framework]/[workload]/[config]/*/html/index.html

# Export CSV
cd $RESULT_DIR && python3 ../../scripts/analyze-results.py . > comparison.csv
```

### Stop & Cleanup
```bash
# Stop all services (keep data)
docker-compose down

# Clean old results
rm -rf tests/perf/results/benchmark_YYYYMMDD_*

# Full cleanup (delete database)
docker-compose down -v
```

---

## 📚 Additional Resources

- **Quick Start Guide**: `BENCHMARK_QUICK_START.md`
- **Framework Documentation**: `frameworks/*/README.md`
- **Database Schema**: `database/fraiseql_cqrs_schema.sql`
- **Monitoring Setup**: `monitoring/README.md`
- **Test Configuration**: `tests/perf/configs/`

---

## ✅ Success Criteria

A successful benchmark run meets all of:
1. ✅ All 12 frameworks complete without crashing
2. ✅ Error rates <1% across all tests
3. ✅ HTML reports generated for all tests
4. ✅ Results properly archived with timestamp
5. ✅ No container restarts during execution
6. ✅ Metrics analyzable and comparable

---

**Next Step**: Follow Phase 0-5 above to execute your first benchmark!
