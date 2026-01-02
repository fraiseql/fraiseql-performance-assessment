# Phase 8: Strawberry GraphQL Results Analysis Template

## Post-Test Analysis Checklist

### Immediate (Check first thing after test completes)

- [ ] Test completed without errors (check benchmark logs)
- [ ] All 8 workloads executed (verify result files exist)
- [ ] Prometheus has data (check Grafana for non-empty panels)
- [ ] Database stayed up (check connection count graph)
- [ ] Memory didn't crash (peak memory <500 MB)

### Within 1 Hour

- [ ] Extract metrics from Prometheus/CSV
- [ ] Calculate key metric values (DataLoader sizes, memory, query counts)
- [ ] Identify any anomalies or failures
- [ ] Compare against baseline expectations

---

## Metric Collection Checklist

For each workload, collect these metrics:

```
□ Throughput (req/sec)
  - Source: JMeter results
  - Expected: 200-400 req/sec (varies by workload)
  - How to extract: jmeter_results.csv → calculate requests / test duration

□ Latency Percentiles
  - Source: JMeter results
  - Expected p99: 150-250ms
  - How to extract: jmeter_results.csv → quantile calculations

□ Database Query Count
  - Source: Prometheus metric strawberry_database_queries_total
  - Expected: 1 (simple), 3-5 (deep traversal with DataLoader)
  - How to extract: SELECT SUM(increase(strawberry_database_queries_total[10m]))

□ DataLoader Batch Size
  - Source: Prometheus metric strawberry_dataloader_batch_size
  - Expected: >5 on deep traversal
  - How to extract: histogram_quantile(0.99, strawberry_dataloader_batch_size)

□ Memory Usage
  - Source: Prometheus node_memory_bytes or container_memory_bytes
  - Expected: Peak <350 MB, growth <50 MB per 1000 requests
  - How to extract: SELECT max(container_memory_bytes) by (workload)

□ CPU Usage
  - Source: Prometheus node_cpu_seconds_total
  - Expected: <80% per core during normal workloads
  - How to extract: 100 - (avg by(cpu) (irate(node_cpu_seconds_total{mode="idle"}[5m])))

□ Connection Pool Usage
  - Source: Prometheus strawberry_db_pool_active_connections
  - Expected: <20 active, <5 idle
  - How to extract: SELECT max(strawberry_db_pool_active_connections)

□ GC Pause Frequency
  - Source: Python GC statistics (via py-spy or memory_profiler)
  - Expected: <50ms pauses, <1 pause per second
  - How to extract: gc.get_stats() logged to CSV
```

---

## Analysis Questions to Answer

### Question 1: Are DataLoaders Working?

**Check these metrics**:
1. DataLoader batch size average (should be >5 for deep traversal)
2. Query count vs expected (should be 3-5 for deep traversal, not 20+)
3. Batch function call count (should be 2-4, not one per result)

**If DataLoaders are NOT working**:
- Query count will be 10x expected
- p99 latency will be 500ms+ on deep traversal
- Batch sizes will be 1-2
- Action: Review schema for missing DataLoader decorators

**If DataLoaders ARE working**:
- Query count will be 3-5
- p99 latency will be <200ms
- Batch sizes will be 10-50
- Action: Good! DataLoader strategy is sound

### Question 2: Is Memory Acceptable?

**Check these metrics**:
1. Peak memory (should be <350 MB)
2. Memory growth rate (should be <50 MB per 1000 requests)
3. Memory after GC (should drop to baseline)

**If memory is GROWING**:
- Slope > 50 MB per 1000 requests
- Memory never drops to baseline
- Action: Investigate for memory leaks (circular references, unclosed connections)

**If memory is STABLE**:
- Slope < 10 MB per 1000 requests
- Memory drops after GC
- Action: Good! Memory is well-managed

### Question 3: Is GIL Contention Limiting?

**Check these metrics**:
1. CPU vs concurrent connections (should scale linearly until 4+ cores)
2. Context switches (should be <5k/sec on normal load)
3. Throughput plateau (should plateau above 200 req/sec)

**If GIL IS contention-limiting**:
- Throughput plateaus at <150 req/sec
- CPU >90% while pool has <50% usage
- Context switches >50k/sec
- Action: This is expected for Python. Consider async/await optimization or other language

**If GIL is NOT limiting**:
- Throughput reaches 300+ req/sec
- CPU and pool usage balanced
- Context switches <5k/sec
- Action: Good! Python performance is acceptable

### Question 4: Are Query Counts Expected?

**Compare against table**:

| Workload | Expected Queries | Actual Queries | Status |
|----------|------------------|----------------|--------|
| Simple | 1 | ? | |
| Parameterized | 1 | ? | |
| Aggregation | 1 | ? | |
| Pagination | 1-2 | ? | |
| Full-text Search | 1-2 | ? | |
| Deep Traversal | 3-5 | ? | |
| Mutations | 2-4 | ? | |
| Mixed | 1-3 avg | ? | |

**If ACTUAL >> EXPECTED**:
- Indicates N+1 problem (missing DataLoader or not batching)
- Action: Investigate query patterns in logs

**If ACTUAL ≈ EXPECTED**:
- Good! Query patterns are optimal
- Action: Proceed to other metrics

### Question 5: Latency Distribution - What Changed?

**Check**:
1. p50 latency (should be 30-80ms)
2. p99 latency (should be 150-250ms)
3. p99.9 latency (should be <500ms)
4. Ratio of p99/p50 (should be <5x)

**If ratio > 10x**:
- Indicates outlier queries (full table scans, no indexes)
- OR GC pauses (if p99.9 spike)
- Action: Profile slow queries

**If ratio < 5x**:
- Good! Distribution is tight and predictable
- Action: Proceed

---

## Optimization Recommendations (Ranked by Impact)

### Immediate (If Problems Found)

**Priority 1: Missing DataLoaders** (Impact: 10-50x)
- Symptom: Query count = result count on deep traversal
- Action: Add @dataloader decorator to list resolvers
- Expected improvement: Query count 20+ → 3-5

**Priority 2: Memory Leak** (Impact: Critical)
- Symptom: Memory growth >100 MB per 1000 requests
- Action: Profile with memory_profiler, identify circular references
- Expected improvement: Memory stable instead of growing

**Priority 3: GIL Bottleneck** (Impact: Architectural)
- Symptom: Throughput <150 req/sec even with small workloads
- Action: This is Python GIL - expected. Document as architectural limit
- No improvement possible within Python

### High Priority (If Metrics Below Target)

**Priority 4: Connection Pool Size** (Impact: 2-3x)
- If p99 spikes when concurrent > pool size
- Action: Increase pool from 10 to 20-30
- Expected improvement: p99 becomes consistent

**Priority 5: GC Tuning** (Impact: 10-30%)
- If GC pauses >100ms
- Action: Adjust gc.set_threshold() thresholds higher
- Expected improvement: p99 reduces by 10-30%

**Priority 6: Query Result Caching** (Impact: 2-3x on aggregation)
- If aggregation queries slow
- Action: Add @cache(ttl=60s) to aggregation resolvers
- Expected improvement: Aggregation latency 150ms → 50ms

### Medium Priority (For Fine-Tuning)

**Priority 7: Field Selection Optimization** (Impact: 20% memory)
- If memory per request >5 MB
- Action: Use lazy field resolution for optional fields
- Expected improvement: Memory per request 20% reduction

**Priority 8: Pagination Defaults** (Impact: 15% latency)
- If large result sets slow
- Action: Lower default page size from 100 to 25-50
- Expected improvement: Latency 15% improvement, memory 20% improvement

---

## Baseline Comparison

Compare current results against established baseline:

```
BASELINE (Strawberry v0.240+, Python 3.11)
Workload        | Throughput | p99 Latency | Memory Peak | Queries
                | (req/sec)  | (ms)        | (MB)        | (count)
-----------     | ---------- | ----------- | ----------- | --------
Simple          | 350-400    | 50-100      | 100         | 1
Parameterized   | 300-350    | 100-150     | 120         | 1
Aggregation     | 200-250    | 150-200     | 180         | 1
Pagination      | 250-300    | 80-120      | 140         | 1-2
Full-text Search| 200-250    | 100-150     | 200         | 1-2
Deep Traversal  | 100-200    | 200-350     | 250         | 3-5
Mutations       | 150-200    | 180-250     | 200         | 2-4
Mixed           | 200-300    | 150-200     | 200         | 1-3

PERFORMANCE TIERS (vs Baseline)
✅ EXCELLENT: 90-110% of baseline
⚠️  OK:       70-90% of baseline
🔴 POOR:     <70% of baseline
```

**How to use**:
1. Calculate your results vs baseline
2. If <70% of baseline on any workload, investigate
3. If 90-110%, performance is excellent
4. Track over time to detect regressions

---

## Historical Tracking

### How to Compare Future Runs

**Store results in JSON**:
```json
{
  "test_run": {
    "date": "2025-01-15",
    "duration_seconds": 600,
    "strawberry_version": "0.240",
    "python_version": "3.11.8",
    "workloads": {
      "simple": {
        "throughput_req_sec": 375,
        "latency_p99_ms": 75,
        "memory_peak_mb": 105,
        "queries_total": 1000,
        "status": "EXCELLENT"
      },
      ...
    },
    "notes": "DataLoader optimization merged"
  }
}
```

**Comparison table**:
```
Run #1 (baseline)    | Run #2 (optimized) | Change | Status
Simple: 375 req/sec  | 385 req/sec        | +2.7%  | ✅
Aggregation: 200     | 210                | +5%    | ✅
Deep Traversal: 150  | 165                | +10%   | ✅ (DataLoader improved)
```

**Regression detection**:
- If throughput drops >10%, investigate
- If latency p99 increases >20%, investigate
- If memory growth resumes, check for leaks

---

## Summary Report Template

Use this to write up results:

```
# Strawberry Phase 8 Results - [DATE]

## Executive Summary
- Overall performance: [EXCELLENT/GOOD/NEEDS WORK]
- Comparison to baseline: [X% of baseline]
- Key findings: [3-5 bullet points]

## Metrics Summary
[Insert table from baseline comparison section]

## Detailed Analysis

### DataLoader Effectiveness
- Batch size avg: [X]
- Query count reduction: [X%]
- Status: [WORKING / NOT WORKING]

### Memory Efficiency
- Peak memory: [X MB]
- Growth rate: [X MB per 1000 req]
- Status: [STABLE / LEAKING / HIGH]

### GIL Contention
- Throughput plateau: [X req/sec]
- CPU at plateau: [X%]
- Status: [NOT LIMITING / LIMITING / UNKNOWN]

### Latency Distribution
- p50: [X ms]
- p99: [X ms]
- p99.9: [X ms]
- Consistency: [TIGHT / VARIABLE / POOR]

## Recommendations
1. [Highest impact optimization]
2. [Next highest impact]
3. [Nice to have]

## Next Steps
- [ ] Implement priority 1 recommendation
- [ ] Re-run benchmark
- [ ] Compare results
```

---

## Troubleshooting

### "Query count is 10x expected"
- Check: Are DataLoaders defined in schema?
- Fix: Add @dataloader decorator to list fields
- Verify: Re-run and check query count drops

### "Memory keeps growing"
- Check: GC logs for any obvious leaks
- Fix: Profile with memory_profiler on single request
- Verify: Memory drops after profile fix

### "p99 latency varies wildly (p99/p50 > 10x)"
- Check: Are there GC pauses? (Look for sudden latency spikes)
- Fix: Tune gc.set_threshold() or increase pool size
- Verify: p99 becomes more consistent

### "Throughput plateaus low (<150 req/sec)"
- Check: Is this Python GIL contention? (CPU high, pool <50% used)
- Fix: This is expected for Python. Document limit
- Verify: Performance still acceptable for use case

### "No data in Prometheus panels"
- Check: Is Prometheus scraping the strawberry metrics endpoint?
- Fix: Verify strawberry_exporter is running and registered
- Verify: Manual curl of metrics endpoint works

---

## Conclusion

Strawberry results analysis focuses on three key areas:

1. **DataLoader effectiveness** - The primary performance lever
2. **Memory efficiency** - Indicator of object management
3. **GIL contention** - Python architectural limit

With proper DataLoader configuration, Strawberry can achieve 200-300 req/sec sustained, which is excellent for a pure-Python GraphQL framework. Use this template to systematically verify and optimize performance.
