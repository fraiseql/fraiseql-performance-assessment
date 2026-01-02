# FraiseQL Performance Benchmark - Phase Documentation

**Last Updated**: 2025-12-26
**Current Status**: ✅ Ready for Benchmarking

---

## 🎯 Quick Start

### For Running Performance Benchmarks
**→ Read**: [`00-BENCHMARK_MASTER_PLAN.md`](./00-BENCHMARK_MASTER_PLAN.md)

Complete 5-phase guide for executing comprehensive performance tests across all 28 active frameworks.

### For Navigation & Overview
**→ Read**: [`INDEX.md`](./INDEX.md)

Complete reference guide with quick links to all documentation.

### For Archived Framework Plans
**→ Browse**: [`ARCHIVE_OUTDATED_FRAMEWORK_PLANS/`](./ARCHIVE_OUTDATED_FRAMEWORK_PLANS/)

Legacy implementation plans for frameworks not currently enabled (kept for reference).

---

## 📋 What's in This Directory

```
.phases/
├── README.md (you are here)
├── INDEX.md                          ← Complete reference & navigation
├── 00-BENCHMARK_MASTER_PLAN.md      ← MAIN PLAN - START HERE
│
├── qa-framework-verification/        ← Latest QA validation results
│   ├── phase-plan.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── VERIFICATION_RESULTS.md
│   ├── FINAL_QA_SUMMARY.md
│   └── [other QA documents]
│
└── ARCHIVE_OUTDATED_FRAMEWORK_PLANS/ ← Old framework plans (reference)
    ├── README.md
    ├── actix-web-rest/
    ├── async-graphql/
    ├── java-spring-boot/
    └── [other archived plans]
```

---

## 🚀 Quick Commands

### Run Performance Benchmark
```bash
cd /home/lionel/code/fraiseql-performance-assessment

# Start services
docker-compose up -d

# Run benchmark (choose one)
./run-comprehensive-benchmark.sh --quick      # ~45 mins
./run-comprehensive-benchmark.sh --medium     # ~2.5-3 hours (RECOMMENDED)
./run-comprehensive-benchmark.sh --full       # ~8-10 hours
```

### View Results
```bash
# Find latest results directory
RESULT_DIR=$(ls -td tests/perf/results/benchmark_*/ | head -1)

# Open HTML report
firefox $RESULT_DIR/*/html/index.html

# Or export to CSV
cd $RESULT_DIR && python3 ../../scripts/analyze-results.py . > comparison.csv
```

---

## 📊 Framework Status

### ✅ Active (28 Frameworks)

**Python (7)**: fraiseql, strawberry, graphene, fastapi-rest, flask-rest, strawberry-orm-naive, fastapi-orm-naive

**Node.js (6)**: apollo, apollo-orm, express-rest, express-orm, apollo-orm-naive, express-orm-naive

**Java (3)**: spring-boot, spring-boot-orm, spring-boot-orm-naive

**Go (6)**: go-graphql-go, gin-rest, go-gqlgen, go-gqlgen-alt, gqlgen-orm-naive, gin-orm-naive

**Rust (2)**: async-graphql, actix-web-rest

**C#/.NET (1)**: csharp-dotnet

**PHP (1)**: php-laravel

**Ruby (1)**: ruby-rails

**Managed (1)**: hasura

All 28 frameworks are deployed, healthy, and operational.

---

## 📚 Documentation Overview

### Current Phase (Phase 0 - Benchmarking)
**Status**: ✅ Active & Ready
**Document**: `00-BENCHMARK_MASTER_PLAN.md`
**Duration**: 20 mins - 2+ hours

5-phase execution plan:
1. **Phase 0**: Pre-Benchmark Validation (15 mins)
2. **Phase 1**: Infrastructure Startup (5-10 mins)
3. **Phase 2**: Benchmark Selection (2 mins)
4. **Phase 3**: Execute Benchmark (20 mins - 2+ hours)
5. **Phase 4**: Results Collection (15-30 mins)
6. **Phase 5**: Interpretation & Reporting (30 mins - 2 hours)

### Completed Phase (QA Verification)
**Status**: ✅ Completed
**Document**: `qa-framework-verification/phase-plan.md`
**Results**: All 28 frameworks validated and working

Key findings:
- Framework configuration correct
- Database schema (benchmark.tb_*) properly set up
- Connection pools optimized
- Naive ORM impact documented
- 8 languages represented
- All health check endpoints verified

### Archived Frameworks (Reference Only)
**Status**: 📦 Archived (not currently active)
**Location**: `ARCHIVE_OUTDATED_FRAMEWORK_PLANS/`
**Contains**: 7 framework implementation plans

These were archived due to:
- Lower business priority
- Better alternatives exist (e.g., gqlgen over go-graphql-go)
- Resource constraints (20+ frameworks too many)
- Not currently in docker-compose.yml

To re-activate: review archived plan → add to docker-compose.yml → run smoke tests

---

## 🎓 If You're New Here

### Step 1: Understand the Project
- Read the main `README.md` in project root
- Check `BENCHMARK_QUICK_START.md` for quick overview

### Step 2: Review Benchmark Plan
- Read `00-BENCHMARK_MASTER_PLAN.md` completely
- Understand phases 0-5

### Step 3: Check System Status
- Run `docker-compose ps`
- Verify database has >1000 rows
- Ensure all frameworks are healthy

### Step 4: Run First Benchmark
- Execute `./run-comprehensive-benchmark.sh --quick`
- Review results in HTML reports
- Understand metrics

### Step 5: Run Standard Benchmark
- Execute `./run-comprehensive-benchmark.sh --medium`
- Analyze results
- Create performance report

---

## 📖 Document Guide

### Master Benchmark Plan
**File**: `00-BENCHMARK_MASTER_PLAN.md`
- Complete execution guide for performance benchmarks
- 5-phase structure with detailed steps
- Troubleshooting and interpretation
- Success criteria and expected results
- **Start here if you want to run benchmarks**

### Navigation Index
**File**: `INDEX.md`
- Complete reference guide
- Quick links to all docs
- Status of all phases
- Framework inventory
- Getting started checklist
- **Start here if you want to understand the whole project**

### QA Verification
**Directory**: `qa-framework-verification/`
- Latest validation results
- Framework verification checklist
- Critical findings
- Implementation completeness
- **Reference if debugging framework issues**

### Archived Plans
**Directory**: `ARCHIVE_OUTDATED_FRAMEWORK_PLANS/`
- 7 framework implementation plans
- Why they were archived
- How to re-activate if needed
- **Reference only - for historical context**

---

## 🔄 Phase Flow

```
Completed: QA Framework Verification ✅
    ↓
Current: Phase 0 - Performance Benchmark (Active)
    ├─ Phase 0: Pre-validation
    ├─ Phase 1: Infrastructure startup
    ├─ Phase 2: Benchmark selection
    ├─ Phase 3: Execute tests
    ├─ Phase 4: Collect results
    └─ Phase 5: Analysis & reporting
    ↓
Future: Framework optimization (if needed)
```

---

## 🛠️ Common Tasks

### "I want to run a quick test"
```bash
cd /home/lionel/code/fraiseql-performance-assessment
docker-compose up -d
./run-comprehensive-benchmark.sh --quick
# Results in ~20 minutes
```

### "I want to understand the current status"
→ Read `INDEX.md` section: "Current Phase Status"

### "I want to see framework details"
→ Read `INDEX.md` section: "Framework Status Summary"

### "I want to run a specific framework test"
```bash
./run-comprehensive-benchmark.sh --medium --framework strawberry
```

### "I need to understand a disabled framework"
→ Check `ARCHIVE_OUTDATED_FRAMEWORK_PLANS/[framework]/IMPLEMENTATION_PLAN.md`

### "I want to fix a broken framework"
→ See `00-BENCHMARK_MASTER_PLAN.md` section: "Disabled/Broken Frameworks"

---

## 📊 Success Metrics

A successful benchmark run has:
- ✅ All 28 frameworks complete without crashing
- ✅ Error rates <1%
- ✅ HTML reports for all test combinations
- ✅ Results properly archived with timestamp
- ✅ No container restarts during execution
- ✅ Metrics comparable between frameworks
- ✅ 8 languages represented in results
- ✅ All workload types (8) and load profiles (4) complete

---

## 🔗 Related Documentation

In project root:
- `BENCHMARK_QUICK_START.md` - Quick start guide
- `FRAMEWORK_EXPECTATIONS.md` - Framework config details
- `SCHEMA_FIX_PLAN.md` - Database schema info
- `FRAMEWORKS_INVENTORY.md` - Complete framework list

In test directory:
- `tests/perf/` - Performance test infrastructure
- `tests/perf/scripts/` - Test execution scripts
- `tests/perf/jmeter/` - JMeter test plans

In monitoring directory:
- `monitoring/README.md` - Monitoring stack setup
- `monitoring/prometheus.yml` - Prometheus config
- `monitoring/grafana/` - Grafana dashboards

---

## 📝 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-26 | 2.0 | Reorganized for benchmarking focus, created master plan, archived outdated frameworks |
| 2025-12-18 | 1.0 | Original framework implementation phase plans |

---

## 🎯 Next Steps

**If running benchmarks**:
1. Read `00-BENCHMARK_MASTER_PLAN.md`
2. Follow Phase 0-5
3. View and analyze results

**If understanding the project**:
1. Read `INDEX.md`
2. Review framework status
3. Check QA validation results

**If doing development work**:
1. Check `ARCHIVE_OUTDATED_FRAMEWORK_PLANS/` for reference
2. Review existing framework in `frameworks/[name]/`
3. Follow similar patterns

---

## 📞 Quick Help

| Question | Answer |
|----------|--------|
| Where do I start? | Read `00-BENCHMARK_MASTER_PLAN.md` |
| How do I see everything? | Read `INDEX.md` |
| What's the status? | Check section "Framework Status" above |
| How do I run a test? | See "Common Tasks" → "quick test" |
| What frameworks are disabled? | See section "Framework Status" above |
| How do I view results? | See "Common Tasks" → "view results" |

---

**Document Version**: 2.0
**Last Updated**: 2025-12-26
**Status**: ✅ Ready for benchmarking
