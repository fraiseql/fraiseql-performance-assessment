# FraiseQL Performance Assessment - Improvement Roadmap

## Overview

This document provides a high-level roadmap for transforming the FraiseQL Performance Assessment project from a basic curl-based benchmark into a production-grade, multi-language, statistically rigorous performance testing platform.

## Current State Summary

| Aspect | Current | Target |
|--------|---------|--------|
| **Frameworks** | 5 Python | 9+ (Python, Node.js, Go) |
| **Test Method** | curl (18 requests) | JMeter (100K+ requests) |
| **Concurrency** | Sequential | 100+ concurrent threads |
| **Database** | psycopg2 sync | asyncpg/pgx pools |
| **Data Volume** | ~500 records | 100K+ records |
| **Monitoring** | Post-test only | Continuous 1s sampling |
| **CI/CD** | None | Full GitHub Actions |
| **Regression** | Manual | Automated thresholds |

## Phase Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PHASES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 2: Benchmarking Methodology                               │
│  ├── JMeter integration (replace curl)                          │
│  ├── Warmup phases (2-3 min)                                    │
│  ├── Statistical analysis (p50/p95/p99/p99.9)                   │
│  └── Cold vs warm comparison                                    │
│                                                                  │
│  Phase 3: Connection Pooling & Async                            │
│  ├── asyncpg for Python async frameworks                        │
│  ├── psycopg3 pool for Flask                                    │
│  ├── Pool tuning (10-100 connections)                           │
│  └── Statement caching                                          │
│                                                                  │
│  Phase 4: Data Volume Scaling                                   │
│  ├── 10K users, 100K posts, 500K comments                       │
│  ├── Reproducible seed (Faker + seed)                           │
│  ├── TV table sync automation                                   │
│  └── Index usage verification                                   │
│                                                                  │
│  Phase 5: Node.js Frameworks                                    │
│  ├── Apollo Server 4 (GraphQL)                                  │
│  ├── Express (REST)                                             │
│  ├── DataLoader integration                                     │
│  └── pg connection pool                                         │
│                                                                  │
│  Phase 6: Go Frameworks                                         │
│  ├── gqlgen (GraphQL)                                           │
│  ├── Gin (REST)                                                 │
│  ├── pgxpool (100+ connections)                                 │
│  └── graph-gophers/dataloader                                   │
│                                                                  │
│  Phase 7: Advanced Workloads                                    │
│  ├── Aggregation queries (COUNT, SUM, GROUP BY)                 │
│  ├── Pagination (offset vs cursor)                              │
│  ├── Full-text search (tsvector)                                │
│  ├── Deep traversal (3+ levels)                                 │
│  ├── Concurrent mutations                                       │
│  └── Mixed realistic traffic (weighted)                         │
│                                                                  │
│  Phase 8: Resource Monitoring                                   │
│  ├── Prometheus + Grafana stack                                 │
│  ├── cAdvisor (container metrics)                               │
│  ├── postgres_exporter                                          │
│  ├── 1-second continuous sampling                               │
│  └── Correlation analysis                                       │
│                                                                  │
│  Phase 9: CI/CD & Regression                                    │
│  ├── GitHub Actions workflows                                   │
│  ├── Baseline management                                        │
│  ├── Configurable thresholds                                    │
│  ├── PR performance comments                                    │
│  ├── Nightly comprehensive runs                                 │
│  └── Historical trend analysis                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Graph

```
Phase 2 (Methodology) ─────┬───────────────────────────────────────┐
                           │                                        │
Phase 3 (Async/Pool) ──────┼──► Phase 5 (Node.js) ─────────────────┤
                           │                                        │
Phase 4 (Data Scale) ──────┼──► Phase 6 (Go) ──────────────────────┤
                           │                                        │
                           └──► Phase 7 (Workloads) ────────────────┤
                                                                    │
Phase 8 (Monitoring) ──────────────────────────────────────────────┤
                                                                    │
                                                                    ▼
                                                    Phase 9 (CI/CD)
```

## Implementation Priority

### High Priority (Foundation)

| Phase | Description | Estimated Effort | Impact |
|-------|-------------|------------------|--------|
| **Phase 2** | Benchmarking Methodology | 3-5 days | Critical - everything depends on valid measurements |
| **Phase 3** | Connection Pooling | 3-4 days | High - unlocks true async performance |
| **Phase 4** | Data Scaling | 2-3 days | High - tests index/memory pressure |

### Medium Priority (Framework Expansion)

| Phase | Description | Estimated Effort | Impact |
|-------|-------------|------------------|--------|
| **Phase 5** | Node.js Frameworks | 4-5 days | Medium - adds language diversity |
| **Phase 6** | Go Frameworks | 4-5 days | Medium - shows compiled performance |
| **Phase 7** | Advanced Workloads | 3-4 days | Medium - realistic scenarios |

### Lower Priority (Infrastructure)

| Phase | Description | Estimated Effort | Impact |
|-------|-------------|------------------|--------|
| **Phase 8** | Resource Monitoring | 2-3 days | Medium - correlation analysis |
| **Phase 9** | CI/CD & Regression | 3-4 days | Medium - automation |

## Quick Start Guide

### Phase 2: Fix Benchmarking First

```bash
# Current (WRONG)
python run_comparative_benchmarks.py  # Only 18 curl requests!

# After Phase 2 (CORRECT)
python run_comparative_benchmarks.py \
  --framework fraiseql \
  --threads 100 \
  --loops 1000 \
  --warmup 120
```

### Phase 3: Enable Async

```python
# Current (BLOCKING)
conn = psycopg2.connect(...)  # Single sync connection

# After Phase 3 (ASYNC POOL)
pool = await asyncpg.create_pool(min_size=20, max_size=100)
result = await pool.fetch(query)
```

### Phase 4: Scale Data

```bash
# Current
make seed-small   # ~500 records

# After Phase 4
make seed-large   # 10K users, 100K posts, 500K comments
```

## Framework Comparison Matrix (Target)

| Framework | Language | Type | Expected RPS | N+1 Prevention |
|-----------|----------|------|--------------|----------------|
| **FraiseQL** | Python | GraphQL+CQRS | 500+ | TV Tables |
| **Strawberry** | Python | GraphQL | 200+ | DataLoader |
| **Graphene** | Python | GraphQL | 200+ | DataLoader |
| **FastAPI REST** | Python | REST | 400+ | Include params |
| **Flask REST** | Python | REST | 100+ | Multiple calls |
| **Apollo Server** | Node.js | GraphQL | 400+ | DataLoader |
| **Express** | Node.js | REST | 600+ | Include params |
| **gqlgen** | Go | GraphQL | 5000+ | DataLoader |
| **Gin** | Go | REST | 8000+ | Include params |

## Key Metrics to Track

### Response Time
- **p50** (median) - typical user experience
- **p95** - most users experience
- **p99** - worst case for most users
- **p99.9** - extreme tail latency

### Throughput
- **RPS** (requests per second) - system capacity
- **Concurrent connections** - scalability
- **Error rate** - reliability under load

### Resource Usage
- **CPU %** - per container
- **Memory MB** - per container
- **DB connections** - pool utilization
- **Query count** - N+1 detection

## Regression Thresholds

| Severity | Threshold | Action |
|----------|-----------|--------|
| **Warning** | >15% degradation | Log, continue CI |
| **Error** | >30% degradation | Fail CI, require review |
| **Critical** | >50% degradation | Block merge |

## File Structure After Implementation

```
fraiseql-performance-assessment/
├── .github/workflows/
│   ├── benchmark.yml           # PR benchmarks
│   └── nightly-benchmark.yml   # Comprehensive nightly
├── .phases/
│   ├── README.md               # This file
│   ├── phase-1-local-podman-testing.md
│   ├── phase-2-benchmarking-methodology.md
│   ├── phase-3-connection-pooling-async.md
│   ├── phase-4-data-volume-scaling.md
│   ├── phase-5-nodejs-frameworks.md
│   ├── phase-6-go-frameworks.md
│   ├── phase-7-advanced-workloads.md
│   ├── phase-8-resource-monitoring.md
│   └── phase-9-cicd-regression.md
├── ci/
│   ├── baseline-thresholds.json
│   ├── compare-results.py
│   ├── update-baseline.py
│   └── generate-trend-report.py
├── database/
│   ├── 01-extensions.sql
│   ├── 02-schema.sql
│   ├── 03-data.sql
│   ├── 04-large-dataset.sql    # NEW
│   ├── 05-fulltext-indexes.sql # NEW
│   ├── fraiseql_cqrs_schema.sql
│   └── seed-generator.py       # NEW
├── frameworks/
│   ├── common/
│   │   └── async_db.py         # NEW - shared async pool
│   ├── fraiseql/               # REFACTORED - asyncpg
│   ├── strawberry/             # REFACTORED - asyncpg
│   ├── graphene/               # REFACTORED - asyncpg
│   ├── fastapi-rest/           # REFACTORED - asyncpg
│   ├── flask-rest/             # REFACTORED - psycopg3 pool
│   ├── apollo-server/          # NEW
│   ├── express-rest/           # NEW
│   ├── go-gqlgen/              # NEW
│   └── gin-rest/               # NEW
├── monitoring/
│   ├── prometheus.yml          # ENHANCED
│   ├── rules/benchmark.yml     # NEW
│   ├── docker-compose.monitoring.yml # NEW
│   ├── resource-collector.py   # NEW
│   └── grafana/
│       └── dashboards/
│           └── benchmark.json  # NEW
├── tests/perf/
│   ├── jmeter/
│   │   ├── workloads/          # NEW - per-workload plans
│   │   └── datasets/           # NEW - parameterized data
│   ├── scripts/
│   │   ├── run-headless.sh     # NEW
│   │   ├── warmup.sh           # NEW
│   │   ├── run-workloads.sh    # NEW
│   │   └── analyze-results.py  # NEW
│   └── results/
│       ├── baseline/           # NEW
│       ├── history/            # NEW
│       └── resources/          # NEW
├── run_comparative_benchmarks.py # REFACTORED - JMeter integration
└── docker-compose.yml          # ENHANCED - all frameworks
```

## Success Metrics

After completing all phases, the project should achieve:

1. **Statistical Validity**: 100K+ requests per benchmark run
2. **Framework Coverage**: 9+ frameworks across 3 languages
3. **Workload Diversity**: 8 distinct workload types
4. **Regression Detection**: <15% variance tolerance
5. **Automation**: Full CI/CD with PR comments
6. **Reproducibility**: Same seed = same results (±5%)
7. **Documentation**: Each framework's N+1 behavior quantified

## Getting Started

1. **Read Phase 2** - Understand the methodology changes needed
2. **Run existing benchmarks** - Establish current baseline
3. **Implement Phase 2** - This is the foundation for everything else
4. **Proceed sequentially** - Each phase builds on previous work

---

*Last updated: December 2024*
*Version: 1.0*
