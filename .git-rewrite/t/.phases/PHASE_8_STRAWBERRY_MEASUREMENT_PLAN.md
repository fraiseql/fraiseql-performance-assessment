# Phase 8: Strawberry GraphQL Measurement Plan

## High-Priority Metrics

### 1. DataLoader Batch Size and Effectiveness

**Why it matters**: Proper DataLoader batching reduces N+1 queries by 5-50x. This is Strawberry's primary optimization lever.

**What to measure**:
- Batch function call count per request
- Average batch size (items batched per function call)
- Query reduction ratio (actual queries / queries without batching)

**How to measure**:
```python
# Via Prometheus custom metric in DataLoader wrapper:
dataloader_batch_size_histogram = Histogram(
    'strawberry_dataloader_batch_size',
    'Number of items in each DataLoader batch',
    buckets=[1, 5, 10, 25, 50, 100, 250],
    labelnames=['dataloader_name', 'workload']
)

# Log when batch_fn is called:
async def batch_fn(keys):
    dataloader_batch_size_histogram.observe(len(keys))
    return await db.query_in(keys)
```

**Expected behavior per workload**:

| Workload | DataLoaders Used | Batch Count | Avg Batch Size | Query Count |
|----------|-----------------|-------------|-----------------|------------|
| Simple | 0 | 0 | N/A | 1 |
| Parameterized | 0 | 0 | N/A | 1 |
| Aggregation | 0 | 0 | N/A | 1 |
| Deep Traversal | 2-3 | 3-4 | 10-50 | 3-5 |
| Mutations | 0 | 0 | N/A | 2-4 |
| Full-text Search | 1 | 1 | 10-100 | 1-2 |

**Red flags** (when something's wrong):
- Batch count = query count (DataLoader not batching)
- Avg batch size = 1 (batching disabled or N+1 occurring)
- Query count 10x higher than expected (missing DataLoader)

**Optimization tip**: If batch sizes <5, increase concurrent connections to force batching.

---

### 2. Memory Per Concurrent Request

**Why it matters**: Indicates object instantiation efficiency and whether memory leaks exist.

**What to measure**:
- Total process memory at request start vs end
- Per-request memory delta
- Memory growth rate over test duration

**How to measure**:
```python
# Via memory profiler in request context:
import psutil
import gc

process = psutil.Process()
memory_before = process.memory_info().rss

# Execute query
result = await execute_graphql(query)

gc.collect()  # Force GC
memory_after = process.memory_info().rss
memory_delta = (memory_after - memory_before) / 1024  # KB

memory_per_request_histogram.observe(memory_delta)
```

**Expected behavior**:
- Simple query: 200-500 KB per request
- Complex query: 1-5 MB per request
- Peak memory (all concurrent): 250-350 MB
- Memory growth rate: <50 MB per 1000 requests

**Red flags**:
- Memory growth >100 MB per 1000 requests (memory leak)
- Per-request memory >10 MB (too many objects created)
- Never recovers to baseline (GC not running)

**Optimization tip**: Profile with `memory_profiler` on 10 sample requests to identify allocation hotspots.

---

### 3. Query Count Reduction Via DataLoader

**Why it matters**: Direct indicator of N+1 prevention effectiveness.

**What to measure**:
- Actual query count per request
- Expected query count (theoretically optimal)
- Reduction ratio (actual / expected)

**How to measure**:
```python
# Via query counter at database level:
query_counter = Counter(
    'strawberry_database_queries_total',
    'Total database queries executed',
    labelnames=['workload', 'query_type']
)

# Increment in database execute:
async def execute(sql):
    query_counter.labels(
        workload=current_workload,
        query_type=infer_query_type(sql)
    ).inc()
    return await db.execute(sql)
```

**Expected reduction per workload**:

| Workload | Without DataLoader | With DataLoader | Reduction |
|----------|-------------------|-----------------|-----------|
| Deep Traversal (3 levels) | 20-30 queries | 3-5 queries | 85-90% |
| Full-text Search (results) | 1 + N per result | 1 + 1 | 90% |
| Nested Mutations | 5-10 | 3-4 | 50-70% |

**Red flags**:
- Reduction ratio <20% on deep traversal (DataLoader missing)
- Query count increasing linearly with result count (N+1 pattern)
- Same query repeated N times (batch function not used)

**Optimization tip**: Use query logging to identify which resolvers aren't batching.

---

### 4. GIL Contention Indicators

**Why it matters**: Under concurrent load, Python's GIL may limit throughput independent of database speed.

**What to measure**:
- CPU usage vs concurrent connections (should scale linearly up to ~4 cores)
- Context switch rate
- Time spent waiting for GIL

**How to measure**:
```python
# Via system metrics (from node-exporter):
cpu_percent = node_cpu_usage
context_switches = node_context_switches

# CPU should remain <80% per core on light workloads
# Context switches should be <10k/sec on normal load
# >100k/sec indicates GIL thrashing
```

**Expected behavior**:
- 1-2 concurrent connections: CPU scales linearly with load
- 4+ concurrent connections: CPU might plateau (GIL limit)
- Context switches: <5k/sec under normal load

**Red flags**:
- Throughput plateau at 100-150 req/sec (GIL bottleneck)
- CPU >90% while database connection pool has <50% usage
- Context switch spike >50k/sec

**Optimization tip**: Monitor for throughput plateau. If plateau occurs at <200 req/sec, GIL may be limiting.

---

## Expected Behavior Per Workload

### Workload-Specific Metric Expectations

```
SIMPLE (Ping)
├─ Queries: 1 (cached)
├─ Memory delta: 300 KB
├─ DataLoaders: 0
├─ p99 latency: <50ms
├─ p99 CPU: <5%
└─ Expected: Baseline for comparison

PARAMETERIZED (Indexed Lookup)
├─ Queries: 1
├─ Memory delta: 400 KB
├─ DataLoaders: 0
├─ p99 latency: <100ms
├─ p99 CPU: 10-15%
└─ Expected: Single index lookup, very consistent

AGGREGATION (GROUP BY, COUNT)
├─ Queries: 1
├─ Memory delta: 1-2 MB
├─ DataLoaders: 0
├─ p99 latency: <150ms
├─ p99 CPU: 15-20%
└─ Expected: Database does heavy lifting, Strawberry adds overhead

PAGINATION (Cursor-based)
├─ Queries: 1-2 (one for data, maybe one for cursor)
├─ Memory delta: 800 KB - 1 MB
├─ DataLoaders: 0
├─ p99 latency: <80ms
├─ p99 CPU: 12-18%
└─ Expected: Explicit limits reduce result set

FULL-TEXT SEARCH
├─ Queries: 1-2 (GIN index + result fetch)
├─ Memory delta: 2-3 MB
├─ DataLoaders: 1
├─ p99 latency: <150ms
├─ p99 CPU: 20-25%
└─ Expected: GIN index makes search fast

DEEP TRAVERSAL (3+ Levels)
├─ Queries: 3-5 (WITH DataLoader)
├─ Memory delta: 3-5 MB
├─ DataLoaders: 2-3
├─ p99 latency: <200ms
├─ p99 CPU: 25-30%
└─ Expected: DataLoader CRITICAL - without it, 20+ queries

MUTATIONS
├─ Queries: 2-4
├─ Memory delta: 1-2 MB
├─ DataLoaders: 0
├─ p99 latency: <200ms
├─ p99 CPU: 20-25%
└─ Expected: Transaction overhead visible

MIXED (Balanced)
├─ Queries: 1-5 (average 2)
├─ Memory delta: 1-2 MB (average)
├─ DataLoaders: Variable
├─ p99 latency: <150ms
├─ p99 CPU: 18-25%
└─ Expected: Average across workloads
```

---

## Red Flags and Failure Modes

### Critical Issues

🔴 **No DataLoaders Used (Query Count = Result Count)**
- Symptom: Query count for deep traversal = 20+
- Cause: DataLoaders not implemented in schema
- Impact: 10-50x latency increase
- Fix: Add DataLoader to resolvers

🔴 **Memory Leak (Continuous Growth)**
- Symptom: Memory grows >50 MB per 1000 requests, never drops
- Cause: Objects not garbage collected
- Impact: Server runs out of RAM after hours
- Fix: Check for circular references, use weak references

🔴 **GIL Contention Bottleneck**
- Symptom: Throughput plateaus at <150 req/sec, CPU >90%
- Cause: Python GIL limiting concurrent execution
- Impact: Cannot improve beyond 100-150 req/sec
- Fix: Consider async framework or Go/Node.js

### High Priority Issues

🟠 **Serialization Overhead (>20ms per request)**
- Symptom: Latency increases 2-3x on aggregation
- Cause: Large result sets require extensive JSON serialization
- Impact: Latency for heavy queries >300ms
- Fix: Limit fields returned, use pagination

🟠 **Connection Pool Saturation**
- Symptom: p99 latency spikes when concurrent >pool size
- Cause: Database connection pool exhausted
- Impact: p99 becomes highly variable
- Fix: Increase pool size or reduce concurrent load

🟠 **GC Pause Spike (p99 >300ms, p50 <50ms)**
- Symptom: Occasional latency spike 5-10x normal
- Cause: Python GC running during request
- Impact: Unreliable latency, poor user experience
- Fix: Tune GC thresholds, ensure pool size correct

### Medium Priority Issues

🟡 **Batch Sizes <5 (Inefficient Batching)**
- Symptom: DataLoader batching not batching
- Cause: Concurrent load insufficient to batch requests
- Impact: 2-3x more queries than optimal
- Fix: Increase concurrent load or implement request batching

🟡 **Memory Per Request >5 MB (High Allocation)**
- Symptom: Each request allocates >5 MB
- Cause: Creating all fields even if not requested
- Impact: Memory pressure, GC more frequent
- Fix: Use lazy field resolution

---

## Analysis Techniques

### Technique 1: DataLoader Effectiveness Analysis

```python
# Python code to analyze DataLoader effectiveness
import json
from prometheus_client import CollectorRegistry, generate_latest

# Query Prometheus for batch statistics
prometheus_query = """
histogram_quantile(0.99,
  strawberry_dataloader_batch_size
)
"""

# Analyze:
# If batch size > 10: Excellent batching
# If batch size 5-10: Good batching
# If batch size 1-5: Marginal batching
# If batch size = 1: No batching (N+1)

def analyze_dataloader_effectiveness(metrics):
    for dataloader, batches in metrics['dataloader_batches'].items():
        batch_sizes = [b['size'] for b in batches]
        avg_size = sum(batch_sizes) / len(batch_sizes)

        if avg_size < 1.5:
            print(f"ALERT: {dataloader} not batching (avg size {avg_size})")
        elif avg_size < 5:
            print(f"WARN: {dataloader} has inefficient batching (avg size {avg_size})")
        else:
            print(f"OK: {dataloader} batching effectively (avg size {avg_size})")
```

### Technique 2: Query Pattern Detection

```python
# Identify N+1 patterns
def detect_n_plus_one(query_log):
    """
    Detect N+1 by looking for repeated queries with different parameters
    """
    query_patterns = {}

    for query in query_log:
        # Extract pattern (remove parameter values)
        pattern = re.sub(r"'[^']*'", "?", query['sql'])

        if pattern not in query_patterns:
            query_patterns[pattern] = []
        query_patterns[pattern].append(query)

    # Report queries executed >10 times in single request
    for pattern, queries in query_patterns.items():
        if len(queries) > 10:
            print(f"ALERT: N+1 detected: {pattern} executed {len(queries)} times")
```

### Technique 3: Memory Leak Detection

```python
# Monitor memory over test duration
def detect_memory_leak(memory_samples):
    """
    Detect linear memory growth indicating leak
    """
    times = [s['time'] for s in memory_samples]
    memories = [s['memory_mb'] for s in memory_samples]

    # Linear regression: memory = a * time + b
    slope, intercept = polyfit(times, memories, 1)

    if slope > 50:  # MB per minute
        print(f"ALERT: Memory growing at {slope} MB/min (likely leak)")
    elif slope > 5:
        print(f"WARN: Memory growing at {slope} MB/min")
    else:
        print(f"OK: Memory stable")
```

### Technique 4: GIL Contention Detection

```python
# Detect GIL bottleneck
def detect_gil_contention(cpu_data, connection_data):
    """
    If CPU is high but connection pool utilization is low, GIL is limiting
    """
    avg_cpu = sum(cpu_data) / len(cpu_data)
    avg_pool_usage = sum(connection_data) / len(connection_data)

    if avg_cpu > 80 and avg_pool_usage < 50:
        print(f"ALERT: GIL contention likely (CPU {avg_cpu}%, Pool {avg_pool_usage}%)")
    elif avg_cpu > 90:
        print(f"WARN: High CPU usage ({avg_cpu}%)")
    else:
        print(f"OK: CPU and pool balanced")
```

---

## Optimization Recommendations (Ranked by Impact)

### Tier 1: Critical (5-10x impact)

1. **Add DataLoaders to deep traversal resolvers**
   - If missing, queries increase 5-50x
   - Implement for any resolver returning list
   - Expected impact: 10-20x latency improvement

2. **Enable connection pooling**
   - If not configured, add psycopg3 with asyncpg
   - Expected impact: 2-3x latency improvement

### Tier 2: High (2-5x impact)

3. **Increase concurrent connection limit**
   - If plateau at <200 req/sec, increase connections
   - Default 10, try 20-50 for benchmark
   - Expected impact: 2-3x throughput

4. **Tune Python garbage collection**
   - Increase GC intervals if pauses frequent
   - Expected impact: 10-30% latency reduction

5. **Use field selection pruning**
   - Don't resolve fields not requested
   - Expected impact: 20-30% memory reduction

### Tier 3: Medium (1.5-2x impact)

6. **Implement query result caching**
   - Cache aggregation query results
   - Expected impact: 2-3x latency for aggregation

7. **Use offset pagination for large sets**
   - Instead of cursor pagination complexity
   - Expected impact: 10-15% latency reduction

### Tier 4: Low (1-1.5x impact)

8. **Profile and optimize serialization**
   - Identify slowest field types
   - Expected impact: 5-10% latency reduction

---

## Conclusion

Strawberry's performance is heavily dependent on proper DataLoader implementation. The framework itself is fast, but DataLoader effectiveness determines whether deep queries are 3-5x slower (with batching) or 20x slower (without).

For Phase 8, the primary measurement should be:
1. Verify DataLoaders are used and batching effectively
2. Ensure memory per request is <5 MB
3. Monitor for GIL contention plateaus
4. Confirm query count matches expected values

With proper DataLoader configuration, Strawberry can sustain 200-300 req/sec on mixed workloads, which is respectable for a pure-Python GraphQL framework.
