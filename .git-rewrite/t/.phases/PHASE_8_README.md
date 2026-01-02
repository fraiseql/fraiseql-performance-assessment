# Phase 8: Continuous Resource Monitoring - Documentation Index

## Overview

Phase 8 implements continuous resource monitoring during benchmark execution to correlate performance metrics with resource usage. **1,800+ lines of detailed documentation** covering all aspects from quick start to deep implementation details.

---

## Reading Guide

### For Quick Understanding (30 minutes)
1. **Start here**: `PHASE_8_QUICK_START.md`
   - What Phase 8 does and why
   - 5 sub-phases overview
   - Quick verification commands
   - Troubleshooting section

### For Implementation (Implementation phase)
1. **Read next**: `phase-8-resource-monitoring-subphases.md`
   - Detailed breakdown of each sub-phase
   - Implementation steps with code examples
   - Files to create/modify
   - Success criteria for each phase
   - Duration: 13-17 hours total

2. **Reference as needed**: `FRAISEQL_FRAMEWORK_ANALYSIS.md`
   - FraiseQL-specific insights
   - WhereType system explanation
   - Expected performance metrics
   - What Phase 8 should focus on for FraiseQL

### For Project Overview (Planning)
1. **Strategic view**: `PHASE_8_IMPLEMENTATION_OVERVIEW.md`
   - How Phase 8 fits with Phase 7 and Phase 9
   - Implementation roadmap (2 weeks)
   - Dependencies and prerequisites
   - Common pitfalls and solutions

---

## Documentation Files

### Primary Documents

| File | Lines | Purpose | Audience |
|------|-------|---------|----------|
| PHASE_8_QUICK_START.md | 384 | Entry point, commands, verification | Everyone |
| phase-8-resource-monitoring-subphases.md | 588 | Detailed implementation plan | Engineers implementing Phase 8 |
| FRAISEQL_FRAMEWORK_ANALYSIS.md | 468 | FraiseQL context and insights | Anyone supporting FraiseQL |
| PHASE_8_IMPLEMENTATION_OVERVIEW.md | 363 | Strategic overview and roadmap | Project leads and planners |

**Total**: 1,803 lines of documentation

### Reference Documents (Already Existing)

| File | Purpose |
|------|---------|
| phase-8-resource-monitoring.md | Original Phase 8 spec (26K) |
| phase-8-resource-monitoring-detailed.md | Detailed version (6.6K) |
| PHASE_7_COMPLETION.md | What Phase 7 delivered |

---

## Key Concepts Explained

### WhereType System (Important for FraiseQL)
FraiseQL's WhereType auto-generates:
- Filtering operators (equals, contains, in, startsWith, etc.)
- Aggregation queries (COUNT, SUM, GROUP BY)
- Pagination support (limit, offset, cursor-based)
- Full-text search operators
- Sorting and ordering

**Implication**: All Phase 7 workloads automatically work for FraiseQL. Phase 8 measures efficiency of execution.

### 5 Sub-Phases Overview

**Sub-Phase 8.1** (3-4 hours): Monitoring Stack
- Deploy Prometheus, Grafana, cAdvisor, node-exporter, postgres-exporter
- Files: prometheus.yml, docker-compose.monitoring.yml
- Verify: All services scraping metrics

**Sub-Phase 8.2** (3-4 hours): Resource Collector
- Python async script sampling at 1-second intervals
- Files: monitoring/resource-collector.py
- Output: CSV + JSON metrics files

**Sub-Phase 8.3** (2-3 hours): Grafana Dashboard
- 24 panels covering CPU, memory, I/O, database, network
- Files: benchmark.json, datasource configs
- Verify: Real-time visualization works

**Sub-Phase 8.4** (2-3 hours): Benchmark Integration
- Modify run_comparative_benchmarks.py
- Auto-start/stop monitoring with tests
- New CLI flag: --with-monitoring

**Sub-Phase 8.5** (2-3 hours): Analysis Script
- Post-test correlation analysis
- Files: monitoring/analyze-metrics.py
- Output: Bottleneck identification, recommendations

---

## What Gets Measured

### Metrics Collected

**System Metrics** (psutil):
```
CPU: usage, user, system, iowait
Memory: total, used, available, percent
I/O: disk read/write rates (MB/s)
Network: bytes sent/received rates (MB/s)
Load: 1-minute, 5-minute, 15-minute average
```

**Container Metrics** (cAdvisor + Prometheus):
```
Per-framework CPU usage (%)
Per-framework memory usage (MB)
Network in/out per container
Block I/O (disk read/write)
```

**Database Metrics** (postgres-exporter):
```
Active/idle/waiting connections
Transaction commit/rollback rates
Cache hit ratio (%)
Temporary files created
Deadlock count
```

**Sampling**: Every 1 second, duration: full test run (~10 minutes)

---

## FraiseQL Performance Profile

Based on WhereType system analysis:

| Workload | CPU | Memory | Connections | Queries | Expected p99 |
|----------|-----|--------|-------------|---------|--------------|
| Simple | 1-5% | 50MB | 1-2 | 1 | < 10ms |
| Parameterized | 10-20% | 100MB | 5-10 | 1-2 | < 100ms |
| Aggregation | 20-30% | 150MB | 10-15 | 1 | < 200ms |
| Pagination | 15-25% | 100MB | 8-12 | 1-2 | < 100ms |
| Full-text | 25-35% | 200MB | 12-18 | 1 | < 150ms |
| Deep Traversal | 30-40% | 250MB | 15-20 | 3-5 | < 300ms |
| Mutations | 20-30% | 150MB | 10-15 | 2-4 | < 200ms |

---

## Implementation Timeline

### Week 1: Infrastructure & Collection
- **Day 1** (3-4h): Sub-Phase 8.1 - Monitoring stack
- **Day 2** (3-4h): Sub-Phase 8.2 - Resource collector
- **Day 3** (2-3h): Sub-Phase 8.3 - Grafana dashboard

### Week 2: Integration & Analysis
- **Day 4** (2-3h): Sub-Phase 8.4 - Benchmark runner integration
- **Day 5** (2-3h): Sub-Phase 8.5 - Analysis script
- **Days 6-7**: Full system testing and optimization

**Total**: 13-17 hours implementation + testing

---

## Quick Commands

```bash
# Verify Prometheus scraping
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Test resource collector
python monitoring/resource-collector.py --duration 30 --output-dir /tmp/test

# Run benchmark with monitoring
python run_comparative_benchmarks.py --framework fraiseql --with-monitoring

# View Grafana dashboard
open http://localhost:3000/d/fraiseql-benchmark

# Analyze metrics
python monitoring/analyze-metrics.py --results-dir tests/perf/results/fraiseql_*/resources
```

---

## Success Criteria

- [ ] All 5 monitoring services healthy
- [ ] Resource collector samples at 1s intervals
- [ ] Grafana dashboard shows real-time metrics
- [ ] Benchmark runner auto-manages monitoring
- [ ] Post-test analysis identifies bottlenecks
- [ ] Full benchmark run completes with complete metrics

---

## How to Use This Documentation

### If implementing Phase 8:
1. Read `PHASE_8_QUICK_START.md` (30 min)
2. Read relevant sub-phase in `phase-8-resource-monitoring-subphases.md` before implementing
3. Reference `FRAISEQL_FRAMEWORK_ANALYSIS.md` for FraiseQL-specific guidance
4. Use verification commands from quick start after each sub-phase

### If managing the project:
1. Read `PHASE_8_IMPLEMENTATION_OVERVIEW.md` for strategic view
2. Use "Implementation Timeline" section for scheduling
3. Reference "Common Pitfalls" for risk mitigation
4. Use "Success Criteria" for completion verification

### If supporting FraiseQL specifically:
1. Read `FRAISEQL_FRAMEWORK_ANALYSIS.md` first
2. Understand WhereType system and performance expectations
3. Focus on metrics in "Key Metrics to Watch for FraiseQL" section
4. Use performance profile table for baseline expectations

---

## Integration with Other Phases

**Phase 7 (Advanced Workloads)** → **Phase 8 (Resource Monitoring)**
- Phase 7 defines: What to measure (8 workload types)
- Phase 8 adds: How well and why (resource visibility)

**Phase 8 (Resource Monitoring)** → **Phase 9 (CI/CD & Regression)**
- Phase 8 provides: Baseline metrics and patterns
- Phase 9 uses: Regression detection thresholds

---

## File Structure After Phase 8

```
monitoring/
├── resource-collector.py
├── analyze-metrics.py
├── prometheus.yml
├── rules/
│   └── benchmark.yml
├── docker-compose.monitoring.yml
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── prometheus.yml
    │   └── dashboards/
    │       └── dashboard.yml
    └── dashboards/
        └── benchmark.json

tests/perf/results/
└── [framework]_[timestamp]_[cold|warm]/
    ├── summary.json (from Phase 7)
    └── resources/
        ├── system_metrics_TIMESTAMP.csv
        ├── postgres_metrics_TIMESTAMP.csv
        ├── container_metrics_TIMESTAMP.csv
        ├── all_metrics_TIMESTAMP.json
        └── analysis/
            └── correlation.json
```

---

## Dependencies

**Python packages** (to add):
```
psutil>=5.9.0
aiohttp>=3.9.0
prometheus-client>=0.19.0
```

**Docker images** (to download):
```
prom/prometheus:v2.48.0
grafana/grafana:10.2.0
prom/node-exporter:v1.7.0
gcr.io/cadvisor/cadvisor:v0.47.0
prometheuscommunity/postgres-exporter:v0.15.0
```

**Disk space**: ~2 GB total (Prometheus + Grafana + CSV output)

---

## Troubleshooting Matrix

| Issue | Document | Section |
|-------|-----------|---------|
| Prometheus not scraping | QUICK_START | Troubleshooting |
| Resource collector hangs | QUICK_START | Troubleshooting |
| No data in Grafana | QUICK_START | Troubleshooting |
| postgres-exporter fails | IMPLEMENTATION_OVERVIEW | Common Pitfalls |
| cAdvisor missing containers | IMPLEMENTATION_OVERVIEW | Common Pitfalls |

---

## References & Links

**Within This Project**:
- PHASE_7_COMPLETION.md - What Phase 7 delivered
- phase-8-resource-monitoring.md - Original specification
- run_comparative_benchmarks.py - Benchmark runner to integrate

**External Resources**:
- Prometheus docs: https://prometheus.io/docs/
- Grafana docs: https://grafana.com/docs/
- cAdvisor metrics: https://github.com/google/cadvisor
- postgres-exporter: https://github.com/prometheus-community/postgres_exporter

---

## Questions & Answers

**Q: Do I need to read all 4 documents?**
A: No. Start with QUICK_START (30 min). Then read the sub-phases document for whichever phase you're implementing. Use others as reference.

**Q: How long will Phase 8 take?**
A: 13-17 hours implementation + testing = about 2-3 days if focused.

**Q: Why WhereType matters for Phase 8?**
A: FraiseQL's WhereType auto-generates all queries Phase 7 tests. Phase 8 measures how efficiently it does so.

**Q: Can I skip any sub-phases?**
A: Not really. Sub-phases are sequential and interdependent. However, you can test each independently.

**Q: What if Phase 8 reveals performance issues?**
A: That's the point! Phase 8 helps identify whether issues are CPU-bound, I/O-bound, memory-bound, or database-bound. Phase 9 uses these insights for regression detection.

---

## Document Metadata

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| PHASE_8_QUICK_START.md | 1.0 | 2025-12-16 | Complete |
| phase-8-resource-monitoring-subphases.md | 1.0 | 2025-12-16 | Complete |
| FRAISEQL_FRAMEWORK_ANALYSIS.md | 1.0 | 2025-12-16 | Complete |
| PHASE_8_IMPLEMENTATION_OVERVIEW.md | 1.0 | 2025-12-16 | Complete |
| PHASE_8_README.md | 1.0 | 2025-12-16 | Complete |

---

## Getting Started

1. **Right now**: Read PHASE_8_QUICK_START.md (30 minutes)
2. **Before implementing**: Read phase-8-resource-monitoring-subphases.md for your assigned sub-phase
3. **During implementation**: Reference FRAISEQL_FRAMEWORK_ANALYSIS.md for FraiseQL insights
4. **For questions**: Check PHASE_8_IMPLEMENTATION_OVERVIEW.md or specific sub-phase document

