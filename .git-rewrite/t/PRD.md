# 📄 **PRD — FraiseQL Application + JMeter Performance Testing Monorepo (Enhanced Edition)**

## **1. Project Overview**

This monorepo will host:

1. **FraiseQL Application**
   A runnable FraiseQL service exposing query execution endpoints, configurable for development, benchmarking, and CI environments.

2. **JMeter Performance Testing Suite**
   A full-featured benchmarking system designed to evaluate FraiseQL across multiple workloads, concurrency levels, and latency distributions.

The goal is to provide **repeatable, automated, and rigorous performance measurement**, enabling tuning, regression detection, and comparative analysis across versions and environments.

---

# **2. Goals & Success Criteria**

## **2.1 Primary Goals**

* Provide a FraiseQL server suitable for performance testing.
* Enable realistic, parameterized, multi-scenario benchmarking using JMeter.
* Provide meaningful, versioned performance metrics including:

  * throughput (QPS/RPS)
  * average latency
  * **tail latency** (p95, p99, p99.9)
  * error rates
  * resource consumption under load
* Automate performance validation using CLI-based testing.
* Store test artifacts for historical comparison.

## **2.2 Success Criteria**

| Criterion                      | Target                                      |
| ------------------------------ | ------------------------------------------- |
| Reproducible environment       | One command to start FraiseQL               |
| Reproducible performance tests | `make perf` executes full suite             |
| Rigorous instrumentation       | Tail latency + resource monitoring          |
| Clear separation               | `app/` vs `tests/perf/`                     |
| Historical comparisons         | Results stored & comparable                 |
| CI integration                 | Optional nightly or manual performance runs |

---

# **3. Non-Goals**

* Real business logic within FraiseQL queries (synthetic workloads only).
* Distributed load testing across multiple generator nodes.
* Real-world dataset generation (optional future work).
* Long-term monitoring (Grafana/Prometheus optional).

---

# **4. Architecture Overview**

## **4.1 Monorepo Structure**

```
/monorepo-root
│
├── app/
│   ├── fraiseql-server/
│   ├── config/
│   ├── scripts/
│   ├── Dockerfile
│   └── Makefile
│
├── tests/
│   ├── perf/
│   │   ├── jmeter/
│   │   │   ├── fraiseql-test-plan.jmx
│   │   │   ├── datasets/
│   │   │   ├── user.properties
│   │   │   └── log4j2.xml
│   │   ├── monitoring/
│   │   │   ├── resource-collector.sh
│   │   │   └── parse-metrics.py
│   │   ├── scripts/
│   │   │   ├── run-headless.sh
│   │   │   ├── warmup.sh
│   │   │   └── compare-results.py
│   │   └── results/
│   │       ├── html/
│   │       ├── raw/
│   │       └── baseline/
│   └── README.md
│
├── ci/
│   ├── perf-workflow.yaml
│   ├── artifact-upload.yaml
│   └── baseline-thresholds.json
│
└── Makefile
```

---

# **5. FraiseQL Application Requirements**

## **5.1 Functional Requirements**

The FraiseQL application **must include**:

### Endpoints:

* `POST /query` — JSON payload
* `GET /query?sql=...` — simplified interface for benchmark tests
* `/health` — simple liveness probe
* `/metrics` (optional but encouraged)
  Prometheus style counters:

  * query_count
  * query_duration_seconds
  * cache_hit/miss
  * request_failures_total

### Configurations:

* Bind address
* Port
* Query timeout
* Log verbosity
* Max threads / worker pool size

### Optional Enhancements:

* Log spans with correlation IDs for distributed tracing
* Query plan caching (test impact)

---

## **5.2 Non-Functional Requirements**

The FraiseQL server must:

* Run reproducibly in a Docker container.
* Support stable performance for **≥ 2,000 concurrent requests**.
* Produce structured logs (JSON).
* Document hardware dependencies for valid benchmarking.
* Support warm and cold start behaviors.

---

# **6. Performance Testing Requirements**

## **6.1 Workload Profiles**

To assess FraiseQL properly, four distinct workloads *must* be included:

### 1️⃣ **Simple Query Workload**

* Lightweight read (e.g., `SELECT 1`)
* Purpose: protocol overhead & maximum throughput

### 2️⃣ **Parameterized Query Workload**

Example:

```
SELECT * FROM products WHERE id = ${product_id}
```

* Simulates typical user-facing queries
* Data-driven via JMeter CSV datasets

### 3️⃣ **Complex Query Workload**

* Queries with filters, multiple fields, or aggregations
* Purpose: stress FraiseQL internals

### 4️⃣ **Randomized Mixed Query Workload**

* Weighted distribution defined in CSV
* Most realistic scenario

---

## **6.2 JMeter Test Plan Requirements**

### Thread Groups

| Group      | Purpose         | VU Range      |
| ---------- | --------------- | ------------- |
| Smoke      | sanity check    | 1–5           |
| Baseline   | steady-state    | 50–200        |
| High Load  | peak throughput | 500–2000      |
| Spike Test | resilience      | 1000+ instant |

### Ramp-up Strategies

* linear
* stepped
* constant arrival rate (if plugin available)

### Assertions

* error rate < 1%
* 99th percentile latency < defined threshold
* response must contain valid JSON

### Outputs

* `.jtl` raw results
* static HTML report
* summarized `summary.json`
* baseline comparison output

---

# **7. System Resource Monitoring Requirements**

Performance results must *correlate* with server-side metrics.

## **7.1 Metrics Collected During Test**

* CPU (system, user)
* Memory usage
* Load average
* Network throughput
* Disk I/O (if applicable)
* Context switches
* GC or memory allocator events

Tools allowed:

* `pidstat`
* `dstat`
* `top/htop`
* `sar`
* Optional: Prometheus node exporter

Resource logs must be stored in:

```
tests/perf/results/raw/system-metrics/
```

---

# **8. Cold Start vs Warm System Testing**

## **8.1 Cold Start Benchmark**

Procedure:

1. Restart FraiseQL
2. Immediately run simple + medium workloads
3. Capture “cold-cache performance”

Required metrics:

* startup latency
* first-minute query variability
* JIT warmup effects (if applicable)

## **8.2 Warm System Benchmark**

Procedure:

1. Run warmup script (`warmup.sh`) for 2–3 minutes
2. Run the full performance suite

Warm tests reveal:

* peak throughput
* steady-state tail latency
* cache effectiveness

---

# **9. Regression Analysis & Thresholds**

Performance regressions must be automatically detectable.

## **9.1 Baseline Storage**

Baseline results stored in:

```
tests/perf/results/baseline/
```

Includes:

* p50, p95, p99, p99.9 latency
* max QPS
* error rate
* resource curves

## **9.2 Automated Thresholds**

Example thresholds:

```json
{
  "simple_query": {
    "max_p95_ms": 12,
    "max_p99_ms": 20,
    "min_throughput_rps": 8000
  },
  "medium_query": {
    "max_p95_ms": 40,
    "max_p99_ms": 90,
    "min_throughput_rps": 3000
  }
}
```

If thresholds are exceeded → CI marks build as degraded.

---

# **10. CI Integration**

Optional but recommended CI workflow:

### Actions:

1. Build FraiseQL
2. Start server container
3. Run JMeter in CLI mode
4. Upload HTML report as artifact
5. Compare results with baseline
6. Fail CI if major performance regression detected

### Frequencies:

* Manual trigger
* Nightly scheduled tests
* Before releases

This ensures long-term performance stability.

---

# **11. Deliverables**

## **Required**

* FraiseQL app + Dockerfile
* JMeter test plan (.jmx)
* Data-driven workloads
* Scripts for warm, cold, smoke, baseline, and full perf tests
* System metrics collectors
* Result parser for summary extraction
* Baseline comparison script

## **Optional**

* Grafana dashboards
* Synthetic dataset generator
* Trend analyzer

---

# **12. Risks & Mitigations**

| Risk                                      | Impact            | Mitigation                           |
| ----------------------------------------- | ----------------- | ------------------------------------ |
| Load generator machine becomes bottleneck | invalid results   | run on Arch Linux machine            |
| FraiseQL instability at high concurrency  | unreliable tests  | isolate environment, capture logs    |
| OS-level interference                     | distorted latency | set CPU governor to performance mode |
| CI variability                            | noisy results     | dedicate runner hardware             |

---

# **13. Timeline**

| Phase                       | Duration |
| --------------------------- | -------- |
| Monorepo setup              | 1 day    |
| FraiseQL containerization   | 1–2 days |
| JMeter test design          | 2–3 days |
| Resource monitoring tooling | 1 day    |
| Automation scripts          | 1 day    |
| CI integration              | 1–2 days |
| Documentation               | 1 day    |

---

# ✅ **Improved PRD Complete**

This revised PRD now includes:

✔ tail-latency goals
✔ warm/cold system analysis
✔ workload modeling
✔ resource monitoring requirements
✔ regression analysis + thresholds
✔ CI automation
✔ expanded architecture
✔ rigorous, research-level methodology

This is now a **top-tier, production-quality performance testing specification**.
