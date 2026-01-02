# Phase 8: Continuous Resource Monitoring - Sub-Phases Plan

## Overview

Phase 8 implements continuous resource monitoring during benchmark execution. Unlike Phase 7 which focused on workload diversity (aggregations, pagination, search, mutations), Phase 8 captures **what's happening at the system level** while these workloads run.

**Key insight for FraiseQL**: The rich `WhereType` system means FraiseQL frameworks don't need explicit aggregation/pagination/search implementations—these are auto-generated from database schema. This frees us to focus purely on **resource behavior** rather than query-specific optimizations.

---

## Current State Assessment

### Phase 7 Deliverables (Ready)
- ✅ 8 JMeter workload test plans (simple, parameterized, aggregation, pagination, fulltext, deep-traversal, mutations, mixed)
- ✅ Database infrastructure (search vectors, indexes, 10K users, 5 posts)
- ✅ Parameter datasets (search terms, pagination offsets, mutation payloads)
- ✅ Workload runner scripts (run-workloads.sh, summarize-workloads.py)

### Phase 8 Gap Analysis
- ❌ No continuous metrics collection during tests (only post-test snapshots)
- ❌ Prometheus/Grafana stack not configured for benchmarking
- ❌ No cAdvisor (container metrics) integration
- ❌ No postgres_exporter for database metrics
- ❌ No correlation between performance spikes and resource usage
- ❌ Resource collection happens sporadically, not at 1-second intervals

---

## Sub-Phases Breakdown

### Sub-Phase 8.1: Monitoring Stack Setup (Prometheus, Grafana, Exporters)

**Objective**: Deploy monitoring infrastructure that continuously scrapes metrics from all framework endpoints and system sources.

**Duration**: 3-4 hours

**Key Components**:

1. **Prometheus Configuration**
   - Scrape interval: 1 second (critical for micro-benchmarks)
   - Recording rules for derived metrics (request rates, percentiles, resource usage)
   - Retention: 7 days
   - Targets: frameworks, cAdvisor, node-exporter, postgres-exporter

2. **cAdvisor** (Container Metrics)
   - Per-container CPU usage
   - Memory consumption and limits
   - Network I/O (bytes sent/received)
   - Block I/O (disk read/write)
   - Live metrics endpoint for scraping

3. **node-exporter** (System Metrics)
   - CPU usage, user/system/iowait breakdown
   - Memory (total, used, available, swap)
   - Disk I/O rates
   - Network I/O rates
   - Load average

4. **postgres-exporter** (Database Metrics)
   - Active/idle/waiting connections
   - Transaction commit/rollback rates
   - Cache hit ratio
   - Temporary file creation
   - Deadlock counts
   - Per-database statistics

**Files to Create/Modify**:
- `monitoring/prometheus.yml` - Prometheus config
- `monitoring/rules/benchmark.yml` - Recording rules
- `monitoring/docker-compose.monitoring.yml` - Monitoring stack
- `docker-compose.yml` - Update to include monitoring services

**Deliverables**:
- [ ] Prometheus running and scraping from all targets
- [ ] cAdvisor collecting container metrics
- [ ] postgres-exporter providing database metrics
- [ ] node-exporter providing system metrics
- [ ] Verification commands working (curl prometheus API)

---

### Sub-Phase 8.2: Resource Collector Script (Python Async Collection)

**Objective**: Build a Python script that continuously samples system, container, and database metrics at 1-second intervals during benchmark execution.

**Duration**: 3-4 hours

**Key Features**:

1. **System Metrics (via psutil)**
   - CPU percentage and breakdown (user, system, iowait)
   - Memory (total, used, percent, available, swap)
   - Disk I/O rates (MB/s)
   - Network I/O rates (MB/s)
   - Load average (1m, 5m, 15m)
   - Sampling interval: 1 second

2. **Container Metrics (via Prometheus API)**
   - Query cAdvisor metrics from Prometheus
   - Per-framework container CPU/memory usage
   - Aggregate across all running containers

3. **Database Metrics (via Prometheus API)**
   - Query postgres-exporter for connection counts
   - Transaction rates
   - Cache hit ratio
   - Lock/deadlock statistics

4. **Async Architecture**
   - Non-blocking I/O for all metric queries
   - Concurrent collection of system/container/postgres metrics
   - Signal handling (graceful shutdown on SIGINT/SIGTERM)

**Implementation Strategy**:
```python
# ResourceCollector class structure
class ResourceCollector:
    def __init__(self, output_dir, prometheus_url, interval, frameworks):
        # Initialize dataclass lists for metrics
        self.system_metrics: List[SystemMetrics] = []
        self.container_metrics: Dict[str, List[ContainerMetrics]] = {}
        self.postgres_metrics: List[PostgresMetrics] = []

    async def start(self):
        # Main loop: collect all metrics concurrently every second
        while self.running:
            await asyncio.gather(
                self._collect_system_metrics(),
                self._collect_container_metrics(),
                self._collect_postgres_metrics(),
                return_exceptions=True
            )
            await asyncio.sleep(interval)

    def _save_results(self):
        # Save to CSV and combined JSON for analysis
```

**Files to Create**:
- `monitoring/resource-collector.py` - Main collector script
- `monitoring/__init__.py` - Make monitoring a package

**Dependencies**:
- `psutil>=5.9.0` - System metrics
- `aiohttp>=3.9.0` - Async HTTP for Prometheus API

**Output Format**:
- `system_metrics_TIMESTAMP.csv` - Rows: [timestamp, cpu_%, mem_%, disk_io_rate, net_io_rate, load_avg, ...]
- `postgres_metrics_TIMESTAMP.csv` - Rows: [timestamp, connections, cache_hit, xact_rate, ...]
- `container_metrics_TIMESTAMP.csv` - Rows: [timestamp, container_name, cpu_%, mem_mb, ...]
- `all_metrics_TIMESTAMP.json` - Combined for analysis

**Deliverables**:
- [ ] Script runs continuously and samples at 1s intervals
- [ ] Handles Prometheus API queries correctly
- [ ] Graceful shutdown with complete data saved
- [ ] CSV output verified with multiple workloads
- [ ] No data loss on interruption (buffered writes)

---

### Sub-Phase 8.3: Grafana Dashboard (Real-time Visualization)

**Objective**: Create dashboard for real-time visualization of all metrics during benchmark runs.

**Duration**: 2-3 hours

**Dashboard Panels** (24 panels total):

**Row 1: Request Rate & Latency** (Framework Comparison)
1. Request rate (req/sec) by framework
2. P50 latency by framework
3. P95 latency by framework
4. P99 latency by framework

**Row 2: Container Resources** (CPU & Memory)
5. CPU usage (%) by container
6. Memory usage (MB) by container
7. CPU time breakdown (user/system/iowait)
8. Memory trend (shows pressure building)

**Row 3: Disk & Network I/O**
9. Disk read rate (MB/s)
10. Disk write rate (MB/s)
11. Network receive rate (MB/s)
12. Network send rate (MB/s)

**Row 4: Database Connections** (PostgreSQL)
13. Active connections
14. Idle connections
15. Total connections / max limit
16. Connection utilization (%)

**Row 5: Database Performance**
17. Cache hit ratio (%)
18. Transaction rate (commits/sec)
19. Blocks read/hit rate
20. Queries per second (if available)

**Row 6: System Load & Health**
21. Load average (1m, 5m, 15m)
22. Error rate (%)
23. Workload type indicator (shows which phase running)
24. Test duration timer

**Dashboard Features**:
- Auto-refresh every 5 seconds
- Time range selector (last 1 hour, 10 minutes, custom)
- Variable dropdown for framework selection
- Annotations for workload phase changes
- Threshold alerts (CPU >80%, mem >85%, connections >90%)

**Files to Create**:
- `monitoring/grafana/provisioning/datasources/prometheus.yml` - Datasource config
- `monitoring/grafana/provisioning/dashboards/dashboard.yml` - Dashboard provisioning
- `monitoring/grafana/dashboards/benchmark.json` - Dashboard definition

**Deliverables**:
- [ ] Dashboard loads in Grafana
- [ ] All panels populate with real data
- [ ] Time series queries return correct metrics
- [ ] Dashboard is responsive and performant
- [ ] Annotations appear during tests

---

### Sub-Phase 8.4: Integration with Benchmark Runner

**Objective**: Modify `run_comparative_benchmarks.py` to start/stop resource collection and coordinate with workloads.

**Duration**: 2-3 hours

**Integration Points**:

1. **Startup Phase**
   - Start monitoring stack (docker-compose up)
   - Verify all exporters are healthy
   - Start Prometheus scraping
   - Wait for metrics to stabilize (30s)

2. **Pre-Test Phase**
   - Create output directory for this test run
   - Start resource collector in background
   - Record start timestamp

3. **Workload Phase**
   - Resource collector runs continuously
   - JMeter workloads execute (run-workloads.sh)
   - Metrics stream into Prometheus

4. **Post-Test Phase**
   - JMeter workloads complete
   - Stop resource collector (graceful shutdown)
   - Save final metrics
   - Wait for Prometheus to flush

5. **Analysis Phase**
   - Correlate JMeter results with resource metrics
   - Identify bottlenecks (CPU, memory, I/O, DB)
   - Generate correlation report

**Code Structure**:
```python
class ComparativeBenchmarkAnalyzer:
    async def run_with_monitoring(self, framework):
        # 1. Start monitoring stack
        self.start_monitoring_stack()

        # 2. Start resource collector
        collector = ResourceCollector(
            output_dir=f"tests/perf/results/{framework}/resources",
            interval_seconds=1.0
        )
        collector_task = asyncio.create_task(collector.start())

        try:
            # 3. Run workloads
            await self.run_workloads(framework)
        finally:
            # 4. Stop collector
            collector.stop()
            await collector_task

        # 5. Analyze and correlate
        self.correlate_metrics(framework)
```

**CLI Integration**:
```bash
# New option: --with-monitoring
python run_comparative_benchmarks.py \
  --framework fraiseql \
  --with-monitoring \
  --threads 50 \
  --loops 100
```

**Files to Modify**:
- `run_comparative_benchmarks.py` - Add monitoring integration
- `tests/perf/scripts/run-workloads.sh` - Coordinate with collector

**Deliverables**:
- [ ] Monitoring stack starts before benchmarks
- [ ] Resource collector captures full duration of tests
- [ ] No data loss between workload phases
- [ ] Results organized by framework and timestamp
- [ ] Metrics available immediately after test completes

---

### Sub-Phase 8.5: Metrics Analysis & Correlation (Python Analysis Script)

**Objective**: Post-process collected metrics to identify performance patterns and bottlenecks.

**Duration**: 2-3 hours

**Analysis Components**:

1. **Resource Utilization Report**
   - Peak CPU usage by workload type
   - Peak memory usage by workload type
   - Average load during test
   - I/O saturation detection

2. **Correlation Analysis**
   - Which resource correlates with latency spikes?
   - When did CPU usage spike relative to JMeter response times?
   - Database connection pool saturation timing
   - Memory pressure effects on performance

3. **Anomaly Detection**
   - Identify outliers in metrics
   - Flag unexpected resource usage patterns
   - Compare against historical baselines

4. **Bottleneck Identification**
   - CPU-bound vs I/O-bound vs DB-bound
   - Lock contention indicators
   - Swap/OOM risk assessment

**Output Format**:
```json
{
  "test_run": "fraiseql_20251216_140000",
  "duration_seconds": 600,
  "workload_phases": [
    {
      "workload": "simple",
      "duration": 60,
      "cpu_peak": 45.2,
      "cpu_avg": 32.1,
      "memory_peak_mb": 512,
      "memory_avg_mb": 380,
      "bottleneck": "CPU-bound"
    }
  ],
  "correlations": {
    "cpu_to_latency": 0.78,
    "memory_to_latency": 0.34,
    "connection_pool_to_latency": 0.89
  },
  "anomalies": [
    {
      "timestamp": 120,
      "metric": "memory",
      "value": 892,
      "expected_range": [300, 600],
      "severity": "warning"
    }
  ]
}
```

**Files to Create**:
- `monitoring/analyze-metrics.py` - Main analysis script
- `tests/perf/scripts/correlate-results.sh` - Wrapper script

**Deliverables**:
- [ ] Metrics loaded from CSV files
- [ ] Correlation statistics calculated
- [ ] Bottleneck analysis performed
- [ ] JSON report generated
- [ ] HTML visualization available

---

## FraiseQL-Specific Considerations

**Why this matters for FraiseQL**:

FraiseQL's rich `WhereType` system auto-generates:
- Aggregation queries (COUNT, SUM, GROUP BY)
- Pagination support (limit, offset)
- Full-text search operators
- Deep relationship traversal

This means **all Phase 7 workloads just work**—frameworks don't need explicit resolvers. Phase 8 measures how efficiently FraiseQL executes these auto-generated queries at scale.

**Key Metrics to Watch**:

1. **Connection Pool Efficiency**
   - FraiseQL's async pool (20-100 connections)
   - Monitoring: active/idle ratios
   - Expected: <10% idle during load

2. **Query Generation Performance**
   - Time to generate WHERE clauses from WhereType
   - Complexity analysis (depth of nesting)
   - Expected: <1ms per query

3. **Caching Behavior**
   - Query plan caching effectiveness
   - WHERE clause compilation caching
   - Expected: >80% hit ratio

4. **N+1 Prevention**
   - TV table joins vs individual queries
   - Batch operation efficiency
   - Expected: <1 query per field resolution

---

## Execution Order

**Day 1 - Infrastructure**
1. Sub-Phase 8.1: Monitoring stack setup (3-4 hours)
2. Verification: All exporters healthy, metrics flowing

**Day 2 - Collection**
3. Sub-Phase 8.2: Resource collector script (3-4 hours)
4. Testing: Manual sampling during small workload

**Day 3 - Visualization & Integration**
5. Sub-Phase 8.3: Grafana dashboard (2-3 hours)
6. Sub-Phase 8.4: Benchmark runner integration (2-3 hours)

**Day 4 - Analysis**
7. Sub-Phase 8.5: Metrics analysis script (2-3 hours)
8. Testing: Full benchmark run with all components

---

## Success Criteria

- [ ] Prometheus scrapes all targets every second (errors < 1%)
- [ ] Resource collector samples at 1s intervals with <50ms latency
- [ ] CSV files contain >95% of expected metric points
- [ ] Grafana displays real-time metrics without lag
- [ ] Correlation analysis identifies true bottlenecks
- [ ] Full benchmark run (all 8 workloads) completes with complete metrics
- [ ] Analysis report generated automatically post-test
- [ ] Historical comparison available for regression detection

---

## Dependencies & Prerequisites

**Software**:
- Docker & Docker Compose 2.0+
- Python 3.11+
- JMeter 5.6+ (from Phase 7)

**Python Packages** (to add to requirements.txt):
```txt
psutil>=5.9.0          # System metrics
aiohttp>=3.9.0         # Async HTTP
prometheus-client>=0.19.0
```

**Docker Images**:
- `prom/prometheus:v2.48.0`
- `grafana/grafana:10.2.0`
- `prom/node-exporter:v1.7.0`
- `gcr.io/cadvisor/cadvisor:v0.47.0`
- `prometheuscommunity/postgres-exporter:v0.15.0`

**Disk Space**:
- Prometheus storage: ~500 MB for 7-day retention
- Grafana data: ~100 MB
- CSV output: ~50 MB per benchmark run
- Total: ~2 GB recommended

---

## Known Limitations & Workarounds

### Limitation 1: Prometheus Scrape Intervals
- **Issue**: 1s scrape interval generates high cardinality
- **Workaround**: Use recording rules to aggregate, keep raw metrics for 1 hour only
- **Cost**: ~500 MB disk per day

### Limitation 2: Container Metrics Accuracy
- **Issue**: cAdvisor samples at 1s but may skip some intervals under load
- **Workaround**: Take psutil as source of truth for system metrics, cAdvisor for container breakdown
- **Accuracy**: ~95% for container metrics

### Limitation 3: Network I/O Attribution
- **Issue**: Can't attribute network I/O to specific containers
- **Workaround**: Use tcpdump for detailed analysis only when needed
- **Cost**: Run only on demand (not continuous)

---

## Testing Strategy

**Phase 8.1 Testing**:
```bash
# Verify monitoring stack health
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Should show: 5+ targets

curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result | length'
# Should show: all targets returning 1 (healthy)
```

**Phase 8.2 Testing**:
```bash
# Start collector and run for 30 seconds
python monitoring/resource-collector.py \
  --output-dir /tmp/test-metrics \
  --interval 1 \
  --duration 30

# Verify CSV has 30 rows (1 per second)
wc -l /tmp/test-metrics/system_metrics_*.csv
```

**Phase 8.3 Testing**:
```bash
# Access Grafana
open http://localhost:3000/d/fraiseql-benchmark
# Should show panels with historical data
```

**Phase 8.4 Testing**:
```bash
# Run single framework with monitoring
python run_comparative_benchmarks.py \
  --framework fraiseql \
  --with-monitoring \
  --threads 10 \
  --loops 5  # Small test for quick verification
```

**Phase 8.5 Testing**:
```bash
# Analyze collected metrics
python monitoring/analyze-metrics.py \
  --results-dir tests/perf/results/fraiseql_*/resources

# Check correlation report
cat tests/perf/results/fraiseql_*/analysis/correlation.json
```

---

## Rollback & Recovery

If monitoring causes issues:

```bash
# Stop monitoring stack without affecting benchmarks
docker-compose -f monitoring/docker-compose.monitoring.yml down

# Data recovery: Metrics already saved to CSV
# Re-run analysis on saved data
python monitoring/analyze-metrics.py --results-dir <existing_dir>
```

---

## Next Steps After Phase 8

After Phase 8 completion, Phase 9 (CI/CD & Regression) will:
- Use Phase 8 metrics to establish performance baselines
- Detect regressions based on resource utilization patterns
- Correlate code changes with performance degradation
- Generate automated reports on performance trends

---

## References

- Prometheus documentation: https://prometheus.io/docs/
- Grafana dashboard design: https://grafana.com/docs/grafana/latest/dashboards/
- cAdvisor metrics: https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md
- postgres-exporter metrics: https://github.com/prometheus-community/postgres_exporter

