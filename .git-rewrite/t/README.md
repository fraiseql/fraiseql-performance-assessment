# 📘 **FraiseQL Monorepo**

### *FraiseQL Application + JMeter Performance Testing Suite*

This monorepo contains:

* **A FraiseQL server application** (`app/`)
* **A complete JMeter-based performance benchmarking suite** (`tests/perf/`)
* **Scripts, automation tools, monitoring utilities, and CI workflows** for reproducible and rigorous performance testing

The goal of this repository is to provide a **self-contained environment for validating FraiseQL performance**, ensuring stability, scalability, and throughput across releases.

---

# 🗂 Repository Structure

```
/monorepo-root
│
├── app/                       # FraiseQL application
│   ├── fraiseql-server/
│   ├── config/
│   ├── scripts/
│   ├── Dockerfile
│   └── Makefile
│
├── tests/
│   ├── perf/                  # Performance testing suite
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
├── ci/                        # CI performance workflows
│   ├── perf-workflow.yaml
│   ├── artifact-upload.yaml
│   └── baseline-thresholds.json
│
└── Makefile                   # root commands
```

---

# 🚀 Getting Started

## **Prerequisites**

* Docker + Docker Compose
* JMeter (for manual runs):

  ```
  pacman -S jmeter      # Arch Linux
  apt install jmeter    # Debian/Ubuntu
  ```
* GNU Make
* Bash
* Optional: Python 3 for utility scripts

---

# 🟩 1. Running FraiseQL Locally

### Start a local FraiseQL instance:

```
make dev
```

or manually:

```
cd app/
docker build -t fraiseql-app .
docker run -p 4000:4000 fraiseql-app
```

Check health:

```
curl http://localhost:4000/health
```

---

# 🟥 2. Running Performance Tests

All performance tests are located under `tests/perf/`.

You can run the entire suite using:

```
make perf
```

This will:

1. Ensure FraiseQL is running
2. Run warmup sequence
3. Execute JMeter test plan headless
4. Collect raw `.jtl` data
5. Generate HTML performance report
6. Store results under `tests/perf/results`

### Result directories:

```
tests/perf/results/
│
├── html/        # interactive JMeter HTML dashboards
├── raw/         # raw results (.jtl), logs, system metrics
└── baseline/    # stored reference results for regression detection
```

---

# 📊 3. Resource Monitoring (Phase 8)

### Real-Time Performance Monitoring

Phase 8 provides continuous resource monitoring during benchmark execution with Prometheus, Grafana, and exporters.

#### Quick Start

```bash
# Start monitoring stack
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

#### What's Monitored

- **System Metrics**: CPU usage, memory, disk I/O, network throughput, load average
- **Container Metrics**: Per-framework resource usage (CPU, memory, network)
- **Database Metrics**: Connections, transaction rates, cache hit ratio, query latency
- **Application Metrics**: Request rates, response time percentiles (p50, p95, p99)

#### Features

- **1-second sampling interval** for micro-benchmark precision
- **40+ recording rules** for fast dashboard queries
- **15-panel dashboard** with framework comparison
- **30-day retention** for historical analysis
- **Auto-provisioned** datasources and dashboards

See `monitoring/README.md` for detailed documentation.

---

# 📊 4. Performance Test Types

The suite includes eight workload scenarios:

### **1. Simple Query Load**

Very lightweight queries (e.g., `SELECT 1`) to measure raw throughput.

### **2. Parameterized Query Load**

CSV-driven template queries simulating common use cases:

```
SELECT * FROM items WHERE id = ${id}
```

### **3. Complex / Heavy Queries**

Stress FraiseQL pipeline, caching, planner, and execution engine.

### **4. Mixed Workload**

Weighted distribution of simple ↔ medium ↔ heavy queries, simulating real-world usage.

---

# 🧪 5. Cold & Warm Performance Testing

### **Cold Start Test**

Evaluates performance immediately after server startup.

Run:

```
make perf-cold
```

### **Warm System Test**

Warms caches & runtime for 2 minutes, then executes full suite.

Run:

```
make perf-warm
```

---

# 📈 6. Interpreting Results

### Access the HTML dashboard:

```
tests/perf/results/html/index.html
```

You will find:

* Requests/sec graphs
* Response time distributions
* Latency percentiles (p50, p95, p99, p99.9)
* Failure breakdowns
* Thread & throughput curves

### Example key metrics:

| Metric               | Meaning                          |
| -------------------- | -------------------------------- |
| **p95 latency**      | typical worst-case in production |
| **p99 latency**      | upper tail—critical for UX & SLA |
| **p99.9 latency**    | rare but important outliers      |
| **Throughput (RPS)** | peak sustainable capacity        |
| **Error %**          | stability indicator              |

---

# 📉 7. Regression Detection

The repository includes automated regression testing logic.

### Compare results with baseline:

```
make perf-compare
```

Thresholds are defined in:

```
ci/baseline-thresholds.json
```

If performance drops below acceptable thresholds, CI will fail with a performance regression indicator.

---

# 🧩 8. Legacy Resource Monitoring (Pre-Phase 8)

During tests, resource collectors capture:

* CPU usage
* Memory usage
* Load average
* Network I/O
* Disk I/O
* Context switches

Run manually:

```
tests/perf/monitoring/resource-collector.sh
```

Outputs stored in:

```
tests/perf/results/raw/system-metrics/
```

These are correlated with JMeter results to identify bottlenecks such as:

* scheduler stalls
* memory pressure
* cache starvation
* garbage collection
* kernel contention

---

# 🛠 9. Root-Level Makefile Commands

| Command              | Description                  |
| -------------------- | ---------------------------- |
| `make dev`           | Start FraiseQL locally       |
| `make build`         | Build the FraiseQL container |
| `make perf`          | Full warm performance suite  |
| `make perf-cold`     | Cold start benchmark         |
| `make perf-warm`     | Warm baseline benchmark      |
| `make perf-smoke`    | Quick 10-second test         |
| `make perf-compare`  | Compare results to baseline  |
| `make clean-results` | Remove old test results      |

---

# 🔄 10. CI Integration

CI workflows (GitHub/GitLab) include:

* On-demand performance tests
* Nightly scheduled benchmarks
* Artifact upload (HTML report + raw logs)
* Baseline comparison
* Regression alerts

Workflow files located in `/ci/`.

---

# 🧱 11. Roadmap

### Completed:

* ✅ **Phase 8: Resource Monitoring** - Prometheus/Grafana dashboards with real-time metrics
* ✅ 8 Framework implementations (Python, Node.js, Go)
* ✅ 8 Workload scenarios (simple → complex → mixed)
* ✅ Realistic database content (10K+ users, blog posts)

### Planned enhancements:

* Phase 9: Execute all benchmarks and analyze results
* Distributed load generation (multiple clients)
* Configurable dataset generator
* Automated anomaly detection
* Query-plan explainability tools

---

# 📬 Support & Contributions

Contributions are welcome!
Please see `CONTRIBUTING.md` (coming soon).

Questions or issues?
Open a GitHub Issue in this monorepo or reach out to the maintainers.

---

# 🎉 **You're ready to benchmark FraiseQL!**

This README provides everything needed to:

* Run the FraiseQL app
* Execute performance benchmarks
* Interpret output
* Validate scalability
* Detect regressions
* Improve FraiseQL over time
