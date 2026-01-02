# 📘 **FraiseQL Performance Assessment - Multi-Framework Benchmark Suite**

### *28-Framework GraphQL & REST Performance Benchmarking Infrastructure*

> ⚠️ **Status**: This is a **work-in-progress benchmarking suite**. Phase 8 (monitoring) is complete, but **Phase 9 (full benchmark execution and analysis) has not yet been completed**. Framework integrations are implemented but have not been run to full completion across all 28 implementations.

This repository contains:

* **28 Framework Implementations** across 8 languages (Python, Node.js, Java, Go, Rust, C#/.NET, PHP, Ruby + Hasura)
  - Individual Dockerfiles and implementations ready for deployment
  - Some frameworks may require minor configuration adjustments
* **A complete JMeter-based performance benchmarking suite** (`tests/perf/`)
  - Validated infrastructure and test plans
  - Ready for execution but full multi-framework runs are pending
* **PostgreSQL 15 CQRS database** with comprehensive test data
* **Prometheus + Grafana monitoring stack** (Phase 8 - Complete)
* **Automated test infrastructure** (integration tests, QA validators, performance benchmarks)

The goal of this repository is to provide a **comprehensive benchmarking environment for comparative performance testing** across multiple frameworks, languages, and architectural patterns. While the infrastructure is ready, **full production benchmark results across all 28 frameworks are pending completion in Phase 9**.

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

# ⚠️ 5. Naive Implementations (Included for Smoke/Small Tests)

Naive implementations are educational demonstrations of **N+1 query problems** and improper ORM usage. They intentionally showcase anti-patterns and are **automatically included for smoke and small payload tests** to provide comprehensive benchmarking across all implementations.

### **Available Naive Implementations**

- `strawberry-naive` (port 8012) - Strawberry with lazy loading, no eager fetching
- `fastapi-naive` (port 8013) - FastAPI with N+1 query patterns

### **When Naive Implementations Are Included**

Naive implementations are included by default for:
- **smoke** - Quick validation tests with minimal load
- **small** - Small payload tests for baseline benchmarking

Naive implementations are excluded by default for larger payloads (**medium**, **large**) to prevent excessive database strain from N+1 queries on large datasets.

### **Testing Naive Implementations**

**For smoke/small payloads** (automatic inclusion):
```bash
./tests/perf/scripts/run-test.sh simple strawberry-naive smoke   # ✅ Included automatically
./tests/perf/scripts/run-test.sh simple fastapi-naive small      # ✅ Included automatically
```

**For larger payloads** (opt-in with `--include-naive`):
```bash
# Force inclusion for medium/large tests (not recommended due to N+1 strain)
./tests/perf/scripts/run-test.sh simple strawberry-naive medium --include-naive
```

### **Framework Lists**

**Standard Frameworks** (always available):
- fraiseql, strawberry, graphene, fastapi, flask, apollo, express, gqlgen, gin

**Naive Implementations** (automatic for smoke/small, opt-in for larger):
- strawberry-naive, fastapi-naive

---

# 🧪 6. Cold & Warm Performance Testing

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

# 📈 7. Interpreting Results

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

# 📉 8. Regression Detection

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

# 🧩 9. Legacy Resource Monitoring (Pre-Phase 8)

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

# 🛠 10. Root-Level Makefile Commands

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

# 🔄 11. CI Integration

CI workflows (GitHub/GitLab) include:

* On-demand performance tests
* Nightly scheduled benchmarks
* Artifact upload (HTML report + raw logs)
* Baseline comparison
* Regression alerts

Workflow files located in `/ci/`.

---

# 🧱 12. Development Status & Roadmap

### ✅ Completed Phases:

* **Phase 1-7**: Framework implementations and infrastructure setup
  - ✅ 28 framework implementations (individual Dockerfiles, endpoints, configurations)
  - ✅ PostgreSQL 15 CQRS database schema
  - ✅ Realistic test data (10K+ users, blog posts, comments)
  - ✅ 8 workload scenarios (simple → parameterized → complex → mixed)
  - ✅ JMeter test plan infrastructure

* **Phase 8: Resource Monitoring** ✅ Complete
  - ✅ Prometheus + Grafana monitoring stack
  - ✅ 40+ recording rules and metrics
  - ✅ 15-panel framework comparison dashboard
  - ✅ Auto-provisioned datasources and dashboards

### 🔄 In Progress / Pending:

* **Phase 9: Full Benchmark Execution & Analysis** ⏳ Pending
  - Execute complete benchmark suite across all 28 frameworks
  - Collect and analyze performance results
  - Generate comparative reports
  - Identify optimization opportunities

### 📋 Known Limitations:

* Full end-to-end benchmark execution across all 28 frameworks has **not been completed**
* Some frameworks may require minor configuration adjustments
* Individual framework health checks successful, but integrated multi-framework benchmarks pending
* Performance baseline data not yet collected

### 🚀 Future Enhancements:

* Distributed load generation (multiple clients)
* Configurable dataset generator
* Automated anomaly detection
* Query-plan explainability tools
* Performance regression detection CI/CD integration

---

# 📬 13. Support & Contributions

Contributions are welcome! This project is in active development and benefits from community testing and feedback.

Please see `CONTRIBUTING.md` for:
* How to report issues
* Framework addition guidelines
* Testing and validation procedures
* Development workflow

**This is a great project to contribute to if you:**
- Want to help complete Phase 9 (benchmark execution)
- Have expertise in specific frameworks
- Can help validate and optimize implementations
- Want to contribute monitoring or analysis improvements

Questions or issues?
Open a GitHub Issue in this repository or reach out to the maintainers.

---

# ⚙️ **Getting Started with This Work-In-Progress**

This repository provides a comprehensive benchmarking infrastructure ready for:

* **Framework Integration Testing** - Validate your framework works with the test suite
* **Individual Framework Benchmarking** - Test a single framework's performance
* **Infrastructure Development** - Improve monitoring, testing, or deployment
* **Phase 9 Completion** - Help execute and analyze full benchmark suite

**Not yet ready for:**
* ❌ Production performance comparisons (Phase 9 pending)
* ❌ Baseline performance metrics (not yet collected)
* ❌ Complete multi-framework benchmarks (infrastructure ready, execution pending)

**To get started:**
1. Read `START_HERE.md` for quick setup
2. Test a single framework to ensure your environment works
3. Review `CONTRIBUTING.md` to see how you can help complete Phase 9
4. Check `.phases/` documentation for development context
