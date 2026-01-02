# Phase 8: Quick Start Guide

## What is Phase 8?

Phase 8 adds **continuous resource monitoring** during benchmark runs to correlate performance metrics with resource usage.

**Why it matters**: You can run workloads, but you won't know *why* latency spikes. Phase 8 answers: Is it CPU? Memory? Database? I/O?

---

## Phase 8 at a Glance

### The Problem
```
Before Phase 8:
JMeter Report: "p99 latency = 200ms"
You: "Why? What happened?"
Answer: Unknown (no visibility)

After Phase 8:
JMeter Report: "p99 latency = 200ms"
Prometheus/Grafana: "CPU spiked to 95% at same time"
Postgres: "Connection pool at 28/30 connections"
Conclusion: CPU-bound, connection pool sizing issue
```

### The Solution (5 Sub-Phases)

| Sub-Phase | What | Duration | Impact |
|-----------|------|----------|--------|
| **8.1** | Deploy Prometheus, Grafana, exporters | 3-4h | Infrastructure foundation |
| **8.2** | Build resource collector script | 3-4h | Continuous metric sampling |
| **8.3** | Create Grafana dashboard | 2-3h | Real-time visualization |
| **8.4** | Integrate with benchmark runner | 2-3h | Automated collection |
| **8.5** | Build analysis script | 2-3h | Correlation reports |

**Total**: ~13-17 hours (2-3 days)

---

## Quick Reference: What Gets Measured

### System Metrics (via psutil)
- CPU usage (total, user, system, iowait)
- Memory (used, available, percent)
- Disk I/O rates (MB/s)
- Network I/O rates (MB/s)
- Load average (1m, 5m, 15m)

### Container Metrics (via cAdvisor + Prometheus)
- Per-framework CPU usage
- Per-framework memory usage
- Network in/out per container

### Database Metrics (via postgres-exporter)
- Active/idle connections
- Transaction commit/rollback rates
- Cache hit ratio (%)
- Deadlock count

### Sampling
- **Interval**: 1 second (critical for micro-benchmarks)
- **Duration**: Full test run (all 8 workloads)
- **Output**: CSV + JSON

---

## Key Files to Create

```
monitoring/
├── resource-collector.py          # Main collection script
├── analyze-metrics.py             # Post-test analysis
├── prometheus.yml                 # Prometheus config
├── rules/benchmark.yml            # Recording rules
├── docker-compose.monitoring.yml  # Monitoring stack
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── prometheus.yml
    │   └── dashboards/
    │       └── dashboard.yml
    └── dashboards/
        └── benchmark.json          # Dashboard definition
```

---

## Sub-Phase 8.1: Quick Verification

**Goal**: All monitoring services running and scraping metrics

**Checklist**:
```bash
# 1. Start monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# 2. Verify Prometheus is running
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Should output: 5 or more

# 3. Check if metrics are flowing
curl -s "http://localhost:9090/api/v1/query?query=up" | jq '.data.result | length'
# Should output: Same number as targets

# 4. Verify Grafana access
open http://localhost:3000
# Login: admin/admin
# Should see: Prometheus datasource, benchmark dashboard

# 5. Test postgres-exporter
curl -s http://localhost:9187/metrics | grep pg_stat | head -5
# Should see: PostgreSQL metrics
```

---

## Sub-Phase 8.2: Quick Test

**Goal**: Resource collector samples metrics at 1s intervals

**Test commands**:
```bash
# 1. Start collector for 30 seconds
python monitoring/resource-collector.py \
  --output-dir /tmp/test-metrics \
  --interval 1 \
  --duration 30

# 2. Verify output files created
ls -lah /tmp/test-metrics/

# 3. Check metric count (should be ~30 rows = 30 seconds)
wc -l /tmp/test-metrics/system_metrics_*.csv

# 4. Sample data
head -5 /tmp/test-metrics/system_metrics_*.csv
```

**Expected output**:
```
timestamp,cpu_percent,memory_used_gb,memory_percent,net_recv_mb_s,load_1m
1702796421.5,45.2,3.2,42.1,0.05,1.2
1702796422.5,42.1,3.2,42.1,0.08,1.1
...
```

---

## Sub-Phase 8.3: Dashboard Verification

**Goal**: Real-time metrics visible in Grafana

**Manual test**:
```bash
# 1. Open Grafana
open http://localhost:3000/d/fraiseql-benchmark

# 2. Expected panels (should show data):
#    - Request Rate by Framework
#    - P95 Latency
#    - Container CPU Usage
#    - Container Memory Usage
#    - PostgreSQL Connections
#    - System Load Average
```

**No data?** Check:
1. Prometheus scraping is working (see 8.1 verification)
2. Time range selector (top-right) includes now
3. Refresh (Ctrl+Shift+R) to reload

---

## Sub-Phase 8.4: Integration Test

**Goal**: Benchmark runner starts/stops monitoring automatically

**Simple test**:
```bash
# Run 1 framework with monitoring (should take ~10 minutes)
python run_comparative_benchmarks.py \
  --framework fraiseql \
  --with-monitoring \
  --threads 10 \
  --loops 10
```

**What happens**:
1. Monitoring stack starts (if not running)
2. Resource collector starts in background
3. JMeter workloads run (Phase 7 tests)
4. Metrics collected every 1 second during test
5. Resource collector stops
6. Results saved to: `tests/perf/results/fraiseql_*/resources/`

**Expected output**:
```
✓ Monitoring stack started
✓ Resource collector running (PID: 12345)
✓ Running workloads: simple, parameterized, aggregation...
✓ Resource collector stopped
✓ Metrics saved:
  - system_metrics_20251216_140000.csv (600 rows)
  - postgres_metrics_20251216_140000.csv (600 rows)
  - all_metrics_20251216_140000.json (2.5 MB)
```

---

## Sub-Phase 8.5: Analysis Test

**Goal**: Post-test analysis identifies bottlenecks

**Run analysis**:
```bash
# Analyze collected metrics from Phase 8.4 test
python monitoring/analyze-metrics.py \
  --results-dir tests/perf/results/fraiseql_*/resources

# View correlation report
cat tests/perf/results/fraiseql_*/analysis/correlation.json | jq .
```

**Expected output**:
```json
{
  "test_run": "fraiseql_20251216_140000",
  "duration_seconds": 600,
  "bottleneck": "CPU-bound",
  "correlations": {
    "cpu_to_latency": 0.78,
    "memory_to_latency": 0.34,
    "connection_pool_to_latency": 0.89
  },
  "recommendations": [
    "Connection pool saturation during aggregation workload",
    "Consider increasing pool_size from 20 to 30"
  ]
}
```

---

## Troubleshooting

### Problem: "Prometheus targets unhealthy"
```bash
# Check which targets are failing
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'

# Common causes:
# - Framework not running on specified port
# - postgres-exporter not connected to database
# - cAdvisor permission issue

# Fix: Verify frameworks are running
docker-compose ps | grep -E "fraiseql|strawberry|graphene|postgres"
```

### Problem: "No metrics in Grafana"
```bash
# Verify Prometheus is scraping
curl -s "http://localhost:9090/api/v1/query?query=up" | jq '.data.result'

# If empty, Prometheus might not have data yet
# Try after running a test:
python run_comparative_benchmarks.py --framework fraiseql --threads 5 --loops 5

# Then check again
```

### Problem: "Resource collector hangs"
```bash
# Check if collector process is running
ps aux | grep resource-collector

# If hanging on Prometheus query, check:
curl -s http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total

# If no results, cAdvisor might not be scraping
docker-compose logs cadvisor | tail -20
```

### Problem: "Metrics files empty or incomplete"
```bash
# Check if collector completed gracefully
tail -20 /tmp/test-metrics/system_metrics_*.csv

# If aborted, rerun with explicit duration:
python monitoring/resource-collector.py \
  --duration 60 \
  --output-dir /tmp/test-metrics \
  --interval 1
```

---

## What's Different About FraiseQL?

### Key Insight
FraiseQL's **WhereType system auto-generates queries**, so Phase 8 measures:
- How fast WhereType compiles WHERE clauses (Rust pipeline)
- How efficiently the connection pool handles async requests
- Memory overhead of Pydantic validation
- N+1 detection via TV table joins

### What to Expect
- **Lower CPU usage** vs other frameworks (Rust pipeline efficient)
- **Higher connection utilization** (async requests pile up in pool)
- **Consistent memory** (TV tables pre-compute joins)
- **Fewer queries** (batching via TV tables)

### Sample Metrics
```
Simple Workload (ping):
  CPU: 5-10% (minimal)
  Memory: 50-60 MB
  Connections: 1-2
  Queries: 1 (cached)

Aggregation Workload:
  CPU: 25-35% (WHERE clause compilation)
  Memory: 150-200 MB
  Connections: 12-18 (active)
  Queries: 1-2 (GROUP BY in DB)

Deep Traversal Workload:
  CPU: 30-40% (multiple WHERE clauses)
  Memory: 250-300 MB
  Connections: 18-25 (near saturation)
  Queries: 3-5 (TV table joins)
```

---

## Next Steps

1. **Review Phase 8 sub-phases plan**: `.phases/phase-8-resource-monitoring-subphases.md`
2. **Review FraiseQL analysis**: `.phases/FRAISEQL_FRAMEWORK_ANALYSIS.md`
3. **Start Sub-Phase 8.1**: Deploy monitoring stack
4. **Verify each sub-phase** using quick tests above
5. **Run Phase 7 workloads** with monitoring enabled
6. **Analyze results** to identify FraiseQL bottlenecks

---

## Success Criteria

- [ ] All 5 monitoring services healthy (Prometheus, Grafana, cAdvisor, node-exporter, postgres-exporter)
- [ ] Resource collector samples at 1s with <50ms latency
- [ ] CSV output contains >600 rows per 10-minute test
- [ ] Grafana dashboard shows real-time metrics without lag
- [ ] Correlation analysis identifies true bottleneck (CPU/Memory/I/O/DB)
- [ ] Historical comparison available for regression detection

---

## Commands Cheat Sheet

```bash
# Start/stop monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
docker-compose -f monitoring/docker-compose.monitoring.yml down

# Quick health check
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Test resource collector
python monitoring/resource-collector.py --duration 30 --output-dir /tmp/test

# Run benchmark with monitoring
python run_comparative_benchmarks.py --framework fraiseql --with-monitoring

# Analyze metrics
python monitoring/analyze-metrics.py --results-dir tests/perf/results/fraiseql_*/resources

# View Grafana
open http://localhost:3000/d/fraiseql-benchmark

# View Prometheus
open http://localhost:9090/graph
```

