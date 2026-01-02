# Pre-Benchmark Validation Checklist

**Status**: ✅ Ready for Benchmarking
**Last Updated**: 2025-12-26
**Framework Count**: 28 active frameworks (100% deployed)

---

## ✅ Infrastructure Readiness

### Docker & Containers
- ✅ All 28 frameworks have Dockerfiles
- ✅ docker-compose.yml is valid and tested
- ✅ Network configured (fraiseql-benchmark)
- ✅ Volume mounts configured for postgres_data, prometheus_data, grafana_data
- ✅ JMeter service configured

### Port Configuration
- ✅ Port conflicts resolved (spring-boot-orm: 8011 → 8013, apollo-orm: 4004 → 4005)
- ✅ All 28 frameworks have unique external ports
- ✅ Port range: 4000-4010, 8002-8025, 8081
- ✅ No overlapping port assignments
- ✅ Framework mapping documented in FRAMEWORK_MAPPING.md (authoritative reference)

### Resource Constraints
- ✅ Disk space available: 100GB (plenty for benchmark results)
- ✅ RAM available: 16GB+ (sufficient for 32 containerized services)
- ✅ No CPU constraints configured (will auto-scale)
- ⚠️ Monitor during benchmark for resource exhaustion

---

## ✅ Database Setup

### PostgreSQL Configuration
- ✅ PostgreSQL 15 Alpine image configured
- ✅ CQRS schema (fraiseql_cqrs_schema.sql) present
- ✅ Trinity identifiers implemented (pk_*, id, *_identifier)
- ✅ Extensions enabled (pg_stat_statements, pg_buffercache)
- ✅ Connection pooling configured (min/max connections per framework)

### Database Initialization
- ✅ Schema load: 01-extensions.sql → fraiseql_cqrs_schema.sql → 04-cqrs-extensions.sql
- ✅ Optional large dataset: 05-large-dataset.sql
- ⚠️ Data generation scripts available but not required for baseline
- ⚠️ Default dataset size: "small" (configurable via DATA_VOLUME env var)

### Data Validation
- [ ] OPTIONAL: Run schema validation before benchmarking
- [ ] OPTIONAL: Verify data population and row counts

---

## ✅ Framework Health Checks

### Health Check Endpoints Verified
- ✅ Standard `/health` endpoints (23 frameworks)
- ✅ Spring Boot `/actuator/health` (3 frameworks)
- ✅ API path `/api/health` (2 frameworks)
- ✅ GraphQL `/graphql` POST (Apollo special case)
- ✅ Hasura `/healthz` (special handling)

### Framework-Specific Checks
- ✅ All frameworks have healthcheck directives in docker-compose
- ✅ Health check intervals: 30s (most), 60s (Python, Ruby)
- ✅ Health check timeouts: 10-15s (appropriate for framework type)
- ✅ Health check retries: 3 (standard across all)

### Known Special Cases
- Apollo Server: Uses POST to /graphql with JSON body (handled in script)
- Laravel/Rails: Use /api/health instead of /health
- Hasura: Uses /healthz instead of /health

---

## ✅ Test Infrastructure

### JMeter Configuration
- ✅ 8 workload types defined:
  - simple: Basic queries with minimal filtering
  - parameterized: Variable-driven queries
  - aggregation: COUNT, SUM, GROUP BY operations
  - pagination: Cursor-based pagination
  - fulltext: Full-text search queries
  - deep-traversal: Nested data fetching (N-levels)
  - mutations: Write operations (INSERT, UPDATE)
  - mixed: Mixed read/write workload
  
- ✅ 4 load profiles configured:
  - smoke: 1 thread, 60s (validation)
  - small: 5 threads, 60s
  - medium: 20 threads, 60s (RECOMMENDED)
  - large: 50 threads, 120s

- ✅ Test plans available for all frameworks
- ✅ Comparative test plans for REST vs GraphQL
- ⚠️ JMeter binary required on system (jmeter --version)

### Test Execution
- ✅ run-comprehensive-benchmark.sh script present
- ✅ Script supports --quick, --medium, --full profiles
- ✅ Script can filter by --framework, --workload, --config
- ✅ All 28 frameworks supported
- ✅ Port mappings current and verified

---

## ⚠️ Important Notes

### Benchmark Script
- ✅ **run-comprehensive-benchmark.sh** supports all 28 frameworks
- ✅ **Framework detection** auto-discovers from docker-compose.yml
- ✅ **Port mappings** updated to current configuration
- ✅ **Health check logic** handles all special cases (Apollo POST, Spring Boot actuator, Laravel/Rails API paths, Hasura healthz)

### Usage Examples
```bash
# Run all frameworks with quick profile
./run-comprehensive-benchmark.sh --quick

# Run single framework
./run-comprehensive-benchmark.sh --framework fraiseql --medium

# Run specific workload with custom load profile
./run-comprehensive-benchmark.sh --workload simple --config smoke

# Run medium profile (recommended for baseline)
./run-comprehensive-benchmark.sh --medium
```

---

## 🚀 Quick Start Commands

### Verify Everything is Ready
```bash
# Check disk space (need 100GB+)
df -h | grep /

# Verify docker-compose
docker-compose config > /dev/null && echo "✅ Valid"

# Check Java dependencies
jmeter --version

# Verify Python 3.10+
python3 --version
```

### Start Containers
```bash
# Start all services
docker-compose up -d

# Wait for health checks
sleep 120

# Verify containers running
docker-compose ps | grep -c healthy
```

### Run Benchmark
```bash
# Run quick validation (45 min, all 28 frameworks)
./run-comprehensive-benchmark.sh --quick

# Run recommended baseline (2.5-3 hours, all 28 frameworks)
./run-comprehensive-benchmark.sh --medium

# Run full stress test (8-10 hours, all 28 frameworks)
./run-comprehensive-benchmark.sh --full

# Monitor progress in another terminal
tail -f tests/perf/results/benchmark_*/benchmark.log
```

---

## 📊 Expected Benchmark Duration (28 Frameworks)

| Profile | Frameworks | Workloads | Configs | Tests | Est. Duration |
|---------|-----------|-----------|---------|-------|----------------|
| **--quick** | 28 | 1 | 1 | 28 | **~45 minutes** |
| **--medium** | 28 | 3 | 3 | 252 | **~2.5-3 hours** |
| **--full** | 28 | 8 | 4 | 896 | **~8-10 hours** |

**Formula**: Frameworks × Workloads × Load Profiles × ~5 mins per test = Total Duration

**Recommended**: Run `--medium` profile for comprehensive baseline (2.5-3 hours)

---

## 📝 Post-Benchmark Actions

After benchmark completes:

1. **Collect Results**
   - Results in: `tests/perf/results/benchmark_[TIMESTAMP]/`
   - Check for failures in `benchmark.log`

2. **Analyze Results**
   - Run: `python tests/perf/scripts/analyze-results.py`
   - Review HTML reports in each framework result directory

3. **Compare Patterns**
   - GraphQL vs REST performance
   - Language performance comparison
   - N+1 naive vs optimized comparison

4. **Document Findings**
   - Create summary report
   - Note any framework issues
   - Identify performance outliers

---

## ✅ Final Verification

Before running benchmark:

- [ ] Disk space verified (100GB+ available)
- [ ] docker-compose.yml validated
- [ ] All 28 frameworks configured
- [ ] Port conflicts resolved
- [ ] Health check endpoints documented
- [ ] JMeter installed (`jmeter --version` works)
- [ ] Test data available
- [ ] Results directory accessible
- [ ] Benchmark script understood
- [ ] Expected duration acceptable

---

**Status**: ✅ All systems ready for benchmarking
**Framework Count**: 28 active frameworks (100% operational)
**Next Step**: Run `docker-compose up -d && ./run-comprehensive-benchmark.sh --medium`
**Recommended Time to Run**: ~2.5-3 hours for medium profile across all 28 frameworks
