# Implementation Plan: Full Test Suite Execution with Generated Databases

**Objective:** Execute the complete FraiseQL performance assessment test suite using the newly generated XXS, XS, and XXLarge databases with realistic AI-generated content.

**Current State:**
- ✅ XXS database: 100 users, 1K posts, 5K comments (2.3MB, with vLLM content)
- ✅ XS database: 500 users, 5K posts, 25K comments (10.9MB, with vLLM content)
- ✅ XXLarge database: 600 users, 6K posts, 30K comments (10.3MB, concatenated)
- ✅ Validation scripts created
- ✅ **PHASE 0 COMPLETED:** All databases successfully imported to PostgreSQL with schema transformation
- ⏳ Docker environment not yet initialized

**Phase 0 Completion Summary (Dec 22, 2025):**
- Identified critical schema mismatch: SQLite uses integer PKs (pk_user, fk_author) vs PostgreSQL uses UUID PKs (id, author_id)
- Created sqlite-to-postgres-import.py with full schema transformation:
  - Text UUID → PostgreSQL UUID type conversion
  - Column name mapping: pk_user → id lookup, fk_author → author_id lookup
  - Full name splitting: full_name → (first_name, last_name)
  - Timestamp format conversion: ISO 8601 → PostgreSQL TIMESTAMP
  - Build ID lookup tables to maintain referential integrity
- ✅ XXS: 100 users, 1K posts, 5K comments imported successfully
- ✅ XS: 500 users, 5K posts, 25K comments imported successfully
- ✅ XXLarge: 600 users, 6K posts, 30K comments imported successfully
- ✅ Referential integrity: 0 orphaned posts, 0 orphaned comments
- ✅ Data quality: vLLM-generated content verified in random samples
- ⚠️ Known Issue: user_follows and post_likes tables not created in PostgreSQL schema (exist in SQLite but not target) - silently skipped during import, doesn't block core data

**Timeline:** ~4-6 hours for complete suite execution (depending on profile selection)

---

## Phase 0: Database Import to PostgreSQL [COMPLETED ✅]

**Status:** COMPLETED on 2025-12-22
**Implementation:** `database/sqlite-to-postgres-import.py`
**Commit:** 7e8a7563 (feat: Add SQLite-to-PostgreSQL import script with schema transformation)

### Phase 0 Summary

Successfully identified and resolved critical schema mismatch between SQLite generation format and PostgreSQL target schema:

**Schema Transformation Handled:**
- SQLite integer primary keys (pk_user, pk_post, pk_comment) → PostgreSQL UUID primary keys
- SQLite foreign key names (fk_author, fk_post) → PostgreSQL foreign key name mapping (author_id, post_id)
- SQLite full_name (single string) → PostgreSQL first_name + last_name (split on space)
- SQLite timestamps (ISO 8601 text format) → PostgreSQL TIMESTAMP format
- Text-encoded UUIDs → PostgreSQL UUID type conversion using uuid.UUID()

**Import Results:**
- ✅ XXS: 100 users, 1K posts, 5K comments
- ✅ XS: 500 users, 5K posts, 25K comments
- ✅ XXLarge: 600 users, 6K posts, 30K comments
- ✅ Referential Integrity: 0 orphaned posts, 0 orphaned comments
- ✅ Data Quality: vLLM-generated content confirmed in samples

**Known Issue (Non-blocking):**
- user_follows and post_likes tables: Exist in SQLite but not in PostgreSQL schema
  - Currently skipped during import (no block to core data)
  - Validation tries to check these tables and fails, but import completes successfully
  - May need to either (a) create tables in PostgreSQL schema, or (b) update validation to skip missing tables

---

## Phase 1: Database Verification & Docker Preparation

### Step 1.1: Verify Imported Data
**Duration:** 5 minutes

**Actions:**
1. Verify all data is correctly in PostgreSQL:
   ```bash
   # Check XXLarge dataset is current
   psql -U fraiseql -d fraiseql -c "
     SELECT
       (SELECT COUNT(*) FROM benchmark.tb_user) as users,
       (SELECT COUNT(*) FROM benchmark.tb_post) as posts,
       (SELECT COUNT(*) FROM benchmark.tb_comment) as comments;
   "
   # Expected: 600 | 6000 | 30000
   ```

2. Spot-check data integrity:
   ```bash
   # Verify UUID format is correct
   psql -U fraiseql -d fraiseql -c "
     SELECT id::text as id, email, first_name, last_name
     FROM benchmark.tb_user LIMIT 3;
   "

   # Verify foreign key references work
   psql -U fraiseql -d fraiseql -c "
     SELECT COUNT(*) FROM benchmark.tb_post
     WHERE NOT EXISTS (SELECT 1 FROM benchmark.tb_user u WHERE u.id = tb_post.author_id);
   "
   # Expected: 0 (no orphaned posts)
   ```

3. Verify timestamp conversion worked:
   ```bash
   psql -U fraiseql -d fraiseql -c "
     SELECT id, created_at, updated_at FROM benchmark.tb_user LIMIT 1;
   "
   # Should show TIMESTAMP format, not text
   ```

**Acceptance Criteria:**
- XXLarge dataset with 600 users, 6K posts, 30K comments is active
- All UUIDs are in correct PostgreSQL UUID format
- All timestamps are TIMESTAMP type (not text)
- Referential integrity is intact (0 orphaned records)
- Sample data can be retrieved and displayed correctly

---

### Step 1.2: Prepare Docker Compose Configuration
**Duration:** 5 minutes

**Actions:**
1. Create `.env.test` file with test-specific settings:
   ```env
   DATA_VOLUME=xxlarge  # Use XXLarge dataset for comprehensive testing
   COMPOSE_PROJECT_NAME=fraiseql-test-suite
   POSTGRES_PORT=5435
   ```

2. Verify docker-compose.yml includes:
   - PostgreSQL service (port 5435)
   - All 23 framework services with health checks
   - Network configuration for inter-service communication
   - Volume mounts for data persistence
   - Resource limits appropriate for test machine

3. Check for required Docker images:
   ```bash
   docker images | grep -E "postgres|fraiseql|strawberry|graphene|apollo"
   ```

**Acceptance Criteria:**
- docker-compose.yml is valid (runs `docker-compose config` without error)
- .env.test file exists with correct settings
- All framework images are available or can be built

---

### Step 1.3: Verify PostgreSQL & Framework Connectivity
**Duration:** 3 minutes

**Actions:**
1. Test PostgreSQL connection:
   ```bash
   psql -U fraiseql -d fraiseql -c "SELECT version();"
   ```

2. Test Docker can reach PostgreSQL:
   ```bash
   docker run --rm postgres:latest psql -h host.docker.internal -U fraiseql -d fraiseql -c "SELECT COUNT(*) FROM benchmark.tb_user;"
   ```

**Acceptance Criteria:**
- PostgreSQL responds with version information
- Docker container can connect to PostgreSQL
- Database is accessible from container network

---

## Phase 2: Docker Environment Setup

### Step 2.1: Prepare Docker Compose Configuration
**Duration:** 5-10 minutes

**Actions:**
1. Create `.env.test` file with test-specific settings:
   ```env
   DATA_VOLUME=xxlarge  # Use XXLarge dataset for comprehensive testing
   COMPOSE_PROJECT_NAME=fraiseql-test-suite
   POSTGRES_PORT=5434
   ```

2. Verify docker-compose.yml includes:
   - PostgreSQL service (port 5434)
   - All 23 framework services with health checks
   - Network configuration for inter-service communication
   - Volume mounts for data persistence
   - Resource limits appropriate for test machine

3. Check for required Docker images:
   ```bash
   docker images | grep -E "postgres|fraiseql|strawberry|graphene|apollo"
   ```

**Acceptance Criteria:**
- docker-compose.yml is valid (runs `docker-compose config`)
- .env.test file exists with correct settings
- All framework images are available or can be built

---

### Step 2.2: Start Docker Environment
**Duration:** 3-5 minutes (with pre-built images)

**Actions:**
1. Start PostgreSQL first (isolated):
   ```bash
   docker-compose up -d postgres
   ```

2. Wait for PostgreSQL to be healthy:
   ```bash
   docker-compose exec postgres pg_isready -U fraiseql
   ```

3. Verify databases imported and ready:
   ```bash
   docker-compose exec postgres psql -U fraiseql -d fraiseql -c "SELECT COUNT(*) FROM benchmark.tb_user;"
   ```

4. Start all framework services:
   ```bash
   docker-compose up -d
   ```

5. Monitor startup progress:
   ```bash
   docker-compose ps --format "table {{.Service}}\t{{.Status}}"
   ```

**Acceptance Criteria:**
- PostgreSQL is healthy
- All 23 framework containers are running
- No container restart loops

---

## Phase 3: Framework Validation & Integration Testing

### Step 3.1: Smoke Tests (Quick Health Checks)
**Duration:** 2-3 minutes

**Actions:**
1. Run fast health checks on all frameworks:
   ```bash
   bash tests/integration/smoke-test.sh
   ```

2. This checks:
   - Container is running
   - Health endpoint responds (GET /health → 200)
   - Metrics endpoint responds (if applicable)
   - No obvious startup errors

3. Log results:
   ```bash
   > tests/integration/results/smoke-test-${TIMESTAMP}.log
   ```

**Acceptance Criteria:**
- 22/23 frameworks report healthy (async-graphql known broken)
- All health endpoints respond within 2 seconds
- No containers show high memory/CPU usage

---

### Step 3.2: Full Integration Tests
**Duration:** 3-5 minutes

**Actions:**
1. Run comprehensive integration test suite:
   ```bash
   python tests/integration/test_frameworks.py
   ```

2. This validates:
   - Health endpoint: GET /health → 200
   - GraphQL endpoints: Introspection query works
   - REST endpoints: GET /api/users?limit=10 works
   - Response schema: Responses contain expected fields
   - Data consistency: Can retrieve inserted data

3. Generate detailed results:
   ```bash
   > tests/integration/results/integration-test-${TIMESTAMP}.json
   > tests/integration/results/integration-test-${TIMESTAMP}.log
   ```

4. Check for failures:
   ```bash
   # Filter for failures
   cat tests/integration/results/integration-test-*.json | jq '.[] | select(.status == "FAIL")'
   ```

**Acceptance Criteria:**
- 22/23 frameworks pass all integration tests
- Response times < 500ms for standard queries
- All expected fields present in responses
- No timeout errors

---

## Phase 4: QA Validation (Multi-Dimensional Testing)

### Step 4.1: Schema Validation
**Duration:** 2 minutes

**Actions:**
1. Validate database schema against framework expectations:
   ```bash
   python tests/qa/schema_validator.py
   ```

2. Checks:
   - All required tables exist
   - All required columns exist with correct types
   - Foreign key constraints are in place
   - Indexes exist on join columns
   - View definitions are correct (if CQRS)

3. Output: `tests/qa/results/schema-validation-${TIMESTAMP}.json`

**Acceptance Criteria:**
- Zero schema violations
- All 23 frameworks agree on schema structure

---

### Step 4.2: Query Validation
**Duration:** 3-5 minutes

**Actions:**
1. Validate all standard queries work across frameworks:
   ```bash
   python tests/qa/query_validator.py
   ```

2. Uses `tests/qa/fixtures/test_queries.json` with queries like:
   - Simple list: GET /users
   - Filtered query: GET /users?role=admin
   - Paginated query: GET /users?limit=10&offset=20
   - Nested query (GraphQL): Posts with comments and authors
   - Aggregation: User post counts

3. Output: `tests/qa/results/query-validation-${TIMESTAMP}.json`

**Acceptance Criteria:**
- All test queries return 200 OK
- Response schemas match expected structure
- No N+1 queries detected
- Pagination works correctly

---

### Step 4.3: N+1 Query Detection
**Duration:** 2-3 minutes

**Actions:**
1. Detect inefficient query patterns using pg_stat_statements:
   ```bash
   python tests/qa/n1_detector.py
   ```

2. Monitors:
   - Query repetition patterns
   - Correlation between HTTP requests and DB queries
   - Identifies queries running per-row

3. Output: `tests/qa/results/n1-detection-${TIMESTAMP}.json`

**Acceptance Criteria:**
- Framework implementations don't have obvious N+1 patterns
- ORM frameworks use proper eager loading
- No more than 2-3 queries per HTTP request

---

### Step 4.4: Data Consistency Validation
**Duration:** 2-3 minutes

**Actions:**
1. Compare responses across frameworks to detect inconsistencies:
   ```bash
   python tests/qa/data_consistency_validator.py
   ```

2. Uses fraiseql as baseline and compares:
   - User counts match
   - Post counts match
   - Comment counts match
   - User relationships are consistent
   - Timestamps are consistent

3. Output: `tests/qa/results/data-consistency-${TIMESTAMP}.json`

**Acceptance Criteria:**
- All frameworks return identical data
- Zero data consistency violations
- Cross-framework variance < 0.01%

---

### Step 4.5: Performance Sanity Checks
**Duration:** 2-3 minutes

**Actions:**
1. Run performance sanity checks for obvious problems:
   ```bash
   python tests/qa/performance_validator.py
   ```

2. Checks:
   - Simple query completes in < 100ms
   - List query (10 items) completes in < 200ms
   - Nested query completes in < 500ms
   - No timeout errors
   - Memory usage stays below thresholds

3. Output: `tests/qa/results/performance-sanity-${TIMESTAMP}.json`

**Acceptance Criteria:**
- Zero framework timeouts
- All queries respond within sanity thresholds
- No frameworks crash during testing

---

### Step 4.6: Generate QA Summary Report
**Duration:** 1 minute

**Actions:**
1. Combine all QA validation results:
   ```bash
   python tests/qa/generate_qa_report.py
   ```

2. Generates:
   - `tests/qa/results/qa-summary-${TIMESTAMP}.md` (Markdown report)
   - `tests/qa/results/qa-summary-${TIMESTAMP}.json` (Machine-readable)
   - Overall pass/fail status per framework
   - Issues and recommendations

**Acceptance Criteria:**
- All validations passed
- Report is comprehensive and clear
- Issues are documented with remediation steps

---

## Phase 5: Performance Testing (JMeter Benchmark Suite)

### Step 5.1: Warmup Sequence
**Duration:** 2-3 minutes

**Actions:**
1. Prime database caches and connection pools:
   ```bash
   bash tests/perf/scripts/warmup.sh
   ```

2. Runs light load for 1 minute:
   - ~5 concurrent threads
   - Mix of read operations
   - Primes JIT compilation
   - Establishes connection pools

**Acceptance Criteria:**
- Warmup completes without errors
- All frameworks respond to warmup requests
- CPU/memory usage stabilizes

---

### Step 5.2: Run JMeter Workload Tests
**Duration:** 30-120 minutes (depending on load profile selected)

**Profile Selection (Choose one):**

**Option A: Smoke Test** (5 minutes)
- ~10 threads
- 50 loops per thread
- 5s ramp-up time
- **Use case:** Quick validation that benchmarks work
- **Best for:** CI/CD, quick iteration

**Option B: Small Load** (15 minutes)
- ~25 threads
- 100 loops per thread
- 15s ramp-up time
- **Use case:** Basic performance baseline
- **Best for:** Local development, quick comparisons

**Option C: Medium Load** (45 minutes)
- ~50 threads
- 500 loops per thread
- 30s ramp-up time
- **Use case:** Realistic load testing
- **Best for:** Standard benchmarking, publication-ready results

**Option D: Large Load** (120 minutes)
- ~100+ threads
- 1000+ loops per thread
- 60s ramp-up time
- **Use case:** Stress testing, scalability limits
- **Best for:** High-performance scenarios, extreme testing

**Actions:**
1. For each workload type, run across all frameworks:
   ```bash
   for workload in simple parameterized aggregation pagination fulltext deep-traversal mutations mixed; do
     bash tests/perf/scripts/run-test.sh $workload smoke  # or small/medium/large
   done
   ```

2. Or run all workloads for a specific framework:
   ```bash
   bash tests/perf/scripts/run-test.sh all fraiseql smoke
   ```

3. Or run everything (comprehensive suite):
   ```bash
   bash tests/perf/scripts/run-all-tests.sh medium  # 2-3 hours
   ```

4. Workloads tested:
   - **simple.jmx**: Ping query throughput (baseline)
   - **parameterized.jmx**: Query with variable parameters
   - **aggregation.jmx**: Complex aggregation queries
   - **pagination.jmx**: Paginated list queries
   - **fulltext.jmx**: Full-text search
   - **deep-traversal.jmx**: Nested GraphQL traversal
   - **mutations.jmx**: Write operations
   - **mixed.jmx**: Mixed read/write workload

5. Results stored in:
   ```bash
   tests/perf/results/${FRAMEWORK}/${WORKLOAD}-${PROFILE}.jtl
   tests/perf/results/${FRAMEWORK}/${WORKLOAD}-${PROFILE}.html
   ```

**Acceptance Criteria:**
- All frameworks complete without errors
- < 0.1% error rate on requests
- Response times stable throughout test
- JMeter reports generated for all workloads

---

### Step 5.3: Generate Performance Reports
**Duration:** 5-10 minutes

**Actions:**
1. Analyze all JMeter results:
   ```bash
   python tests/perf/scripts/analyze-results.py
   ```

2. Generates:
   - Statistical summaries (mean, median, p95, p99)
   - Confidence intervals (95%)
   - Framework comparisons
   - Workload-specific analysis

3. Outputs:
   - `tests/perf/results/summary-${TIMESTAMP}.json` (All metrics)
   - `tests/perf/results/summary-${TIMESTAMP}.md` (Markdown report)
   - `tests/perf/results/summary-${TIMESTAMP}.csv` (Spreadsheet-friendly)

**Acceptance Criteria:**
- All frameworks have results
- Statistical analysis is complete
- Reports are accurate and useful

---

## Phase 6: Results Collection & Analysis

### Step 6.1: Aggregate All Results
**Duration:** 5 minutes

**Actions:**
1. Collect results from all test phases:
   ```bash
   python tests/aggregate_results.py
   ```

2. Creates comprehensive results package:
   ```
   results/${TIMESTAMP}/
   ├── integration/
   │   ├── smoke-test.json
   │   ├── integration-test.json
   │   └── test.log
   ├── qa/
   │   ├── schema-validation.json
   │   ├── query-validation.json
   │   ├── n1-detection.json
   │   ├── data-consistency.json
   │   ├── performance-sanity.json
   │   └── qa-summary.md
   ├── perf/
   │   ├── simple-smoke.html
   │   ├── aggregation-medium.html
   │   ├── deep-traversal-large.html
   │   └── summary.json
   └── manifest.json
   ```

**Acceptance Criteria:**
- All test results are collected
- Results are timestamped and indexed
- Manifest provides overview

---

### Step 6.2: Generate Executive Summary
**Duration:** 5-10 minutes

**Actions:**
1. Create high-level executive summary:
   ```bash
   python tests/generate_executive_summary.py results/${TIMESTAMP}
   ```

2. Includes:
   - Test date and dataset sizes used (XXS/XS/XXLarge)
   - Overall pass/fail by framework
   - Top 3 fastest frameworks
   - Top 3 slowest frameworks
   - Notable issues or anomalies
   - Recommendations

3. Outputs:
   - `results/${TIMESTAMP}/EXECUTIVE_SUMMARY.md`
   - `results/${TIMESTAMP}/EXECUTIVE_SUMMARY.json`

**Acceptance Criteria:**
- Summary is accurate and insightful
- Clearly highlights strengths and weaknesses
- Actionable recommendations provided

---

### Step 6.3: Framework Comparison Report
**Duration:** 10 minutes

**Actions:**
1. Generate detailed framework comparison:
   ```bash
   python tests/generate_comparison_report.py results/${TIMESTAMP}
   ```

2. Creates comparison tables:
   - **Integration Test Performance:** Response times by framework
   - **Query Efficiency:** Queries per HTTP request
   - **Throughput Comparison:** Requests per second (by workload)
   - **Latency Comparison:** p50/p95/p99 response times
   - **Scalability:** Performance at different thread counts
   - **Language/Framework Grouping:** Grouped analysis

3. Outputs:
   - `results/${TIMESTAMP}/FRAMEWORK_COMPARISON.md`
   - `results/${TIMESTAMP}/FRAMEWORK_COMPARISON.xlsx` (spreadsheet)

**Acceptance Criteria:**
- Comparisons are fair (same test conditions)
- Data is presented clearly
- Comparative insights are valuable

---

### Step 6.4: Dataset Size Impact Analysis
**Duration:** 10 minutes (if testing multiple sizes)

**Actions:**
1. If tests were run against XXS, XS, and XXLarge datasets:
   ```bash
   python tests/analyze_dataset_scaling.py results/${TIMESTAMP}
   ```

2. Analyzes:
   - How performance degrades with data volume
   - Which queries are most affected by size
   - Scalability characteristics per framework
   - Volume-related issues (memory, timeouts)

3. Outputs:
   - `results/${TIMESTAMP}/SCALING_ANALYSIS.md`
   - `results/${TIMESTAMP}/SCALING_ANALYSIS.json`

**Acceptance Criteria:**
- Clear scaling patterns identified
- Recommendations for data sizing provided
- Insights into bottlenecks at scale

---

## Phase 7: Reporting & Documentation

### Step 7.1: Create Detailed Benchmark Report
**Duration:** 15-30 minutes

**Actions:**
1. Generate comprehensive benchmark report:
   ```bash
   python tests/generate_final_report.py results/${TIMESTAMP}
   ```

2. Report includes:
   - Executive summary
   - Methodology (test setup, dataset, workloads)
   - Framework descriptions and links
   - Integration test results with timing
   - QA validation findings
   - Performance benchmark results (all 8 workloads)
   - Framework comparisons and rankings
   - Dataset scaling analysis
   - Conclusions and recommendations

3. Outputs:
   - `results/${TIMESTAMP}/BENCHMARK_REPORT.md` (Primary)
   - `results/${TIMESTAMP}/BENCHMARK_REPORT.html` (Web-friendly)
   - `results/${TIMESTAMP}/BENCHMARK_REPORT.pdf` (Printable)

**Acceptance Criteria:**
- Report is comprehensive and professional
- All data is accurate and sourced
- Conclusions are supported by data
- Readable to non-technical audience

---

### Step 7.2: Commit Results to Git
**Duration:** 5 minutes

**Actions:**
1. Commit benchmark results:
   ```bash
   git add results/${TIMESTAMP}/
   git commit -m "perf: add benchmark results for ${TIMESTAMP}

   Test Configuration:
   - Dataset: XXS, XS, XXLarge (with vLLM content)
   - Frameworks: 23 implementations
   - Test Profile: [smoke/small/medium/large]
   - Duration: [X minutes]

   Results:
   - Integration tests: [X/23 passed]
   - QA validations: [All passed/issues noted]
   - Performance: [Summary of findings]

   See BENCHMARK_REPORT.md for full analysis"
   ```

2. Push to remote (optional):
   ```bash
   git push origin main
   ```

**Acceptance Criteria:**
- Results are committed with descriptive message
- All result files are tracked
- Commit references test configuration

---

### Step 7.3: Archive Results
**Duration:** 2 minutes

**Actions:**
1. Create archive for long-term storage:
   ```bash
   tar -czf results/${TIMESTAMP}-archive.tar.gz results/${TIMESTAMP}/
   ```

2. Calculate checksums:
   ```bash
   sha256sum results/${TIMESTAMP}-archive.tar.gz > results/${TIMESTAMP}-archive.sha256
   ```

3. Storage options:
   - Keep locally for 30 days (recent results)
   - Archive to S3/cloud storage for long-term
   - Version control via git (smaller results) or git-lfs (large results)

**Acceptance Criteria:**
- Archive is created and verified
- Checksums are documented
- Storage location is recorded

---

## Phase 8: Cleanup & Documentation

### Step 8.1: Generate Test Metadata
**Duration:** 5 minutes

**Actions:**
1. Create test metadata file:
   ```bash
   cat > results/${TIMESTAMP}/TEST_METADATA.json << 'EOF'
   {
     "timestamp": "2025-12-22T14:30:00Z",
     "test_configuration": {
       "databases": ["xxs", "xs", "xxlarge"],
       "frameworks": 23,
       "load_profile": "medium",
       "duration_minutes": 45
     },
     "environment": {
       "postgres_version": "14.5",
       "docker_version": "24.0",
       "machine_cores": 8,
       "machine_memory_gb": 32
     },
     "results": {
       "integration_tests_passed": 22,
       "qa_validations_passed": true,
       "perf_tests_completed": true,
       "errors": []
     }
   }
   EOF
   ```

**Acceptance Criteria:**
- Metadata is accurate and complete
- Can be used for automated result tracking
- Supports result filtering and comparison

---

### Step 8.2: Update Test Documentation
**Duration:** 10 minutes

**Actions:**
1. Update `tests/README.md` with:
   - Date and results summary
   - Link to full benchmark report
   - Dataset information (sizes, counts)
   - Performance highlights

2. Update main `README.md` with:
   - Latest benchmark results
   - Dataset generation status
   - Test suite readiness

3. Create results index:
   ```bash
   cat > results/INDEX.md << 'EOF'
   # FraiseQL Benchmark Results Index

   | Date | Profile | Frameworks | Dataset | Status |
   |------|---------|-----------|---------|--------|
   | 2025-12-22 | medium | 23/23 | XXS/XS/XXLarge | ✅ |
   EOF
   ```

**Acceptance Criteria:**
- Documentation is up-to-date
- Links are accurate
- Results are easily discoverable

---

### Step 8.3: Cleanup & Optimization
**Duration:** 5 minutes

**Actions:**
1. Clean up temporary files:
   ```bash
   # Remove large log files (keep summaries)
   find tests -name "*.log" -mtime +7 -delete

   # Remove intermediate JMeter files
   rm -rf tests/perf/jmeter/.bak tests/perf/jmeter/*.tmp
   ```

2. Optimize result storage:
   ```bash
   # Compress old results
   gzip results/*/perf/workload-*.jtl  # Keep raw data, compress XML

   # Create symlink to latest
   ln -sf results/$(ls -t results | head -1) results/latest
   ```

3. Docker cleanup (optional):
   ```bash
   # Keep containers running for 30 minutes for analysis
   # Then: docker-compose down
   # Remove volumes: docker volume prune
   ```

**Acceptance Criteria:**
- Temporary files are cleaned
- Results are optimized for storage
- Environment is ready for next run

---

## Execution Workflow Decisions

### Decision 1: Dataset Selection
**Options:**
- A) XXS only (5 min test, quick validation)
- B) XS only (15 min test, standard reference)
- C) XXS → XS → XXLarge (progressive testing, scaling analysis)
- D) All in parallel (3 separate runs)

**Recommendation:** Option C for comprehensive scaling insights

---

### Decision 2: Load Profile Selection
**Options:**
- A) Smoke (5 min, quick check)
- B) Small (15 min, light load)
- C) Medium (45 min, standard benchmarking)
- D) Large (120 min, stress testing)

**Recommendation:** Option C for balanced insights (realistic load, reasonable time)

---

### Decision 3: Framework Coverage
**Options:**
- A) Quick validation (GraphQL only: 7 frameworks)
- B) Standard suite (all 23 frameworks)
- C) Extended suite (23 frameworks + naive variants)

**Recommendation:** Option B (all 23, includes both GraphQL and REST)

---

### Decision 4: Test Phases to Execute
**Options:**
- A) Core only (Phases 1-2, 5: database + JMeter)
- B) Full validation (Phases 1-6: database + integration + QA + JMeter)
- C) Comprehensive (Phases 1-8: everything including reporting)

**Recommendation:** Option B for balanced insights (10-15 minutes, includes QA)

---

## Expected Outcomes

### Performance Benchmarks
- **Throughput:** Requests/second by framework and workload
- **Latency:** p50, p95, p99 response times
- **Scaling:** Performance degradation as load increases
- **Query efficiency:** Queries per HTTP request
- **Consistency:** Data integrity across frameworks

### Quality Assurance Results
- **23/23 frameworks** pass basic integration tests
- **Schema validation:** 100% compliant
- **Query validation:** All standard queries work
- **N+1 detection:** No obvious anti-patterns
- **Data consistency:** Perfect match across frameworks
- **Performance sanity:** All within expected thresholds

### Deliverables
1. Comprehensive benchmark report (Markdown + HTML)
2. Framework comparison spreadsheet (CSV/XLSX)
3. Dataset scaling analysis
4. Executive summary for stakeholders
5. Detailed test logs and raw data
6. Reusable test configuration for future runs

---

## Estimated Timeline (Remaining Phases with Medium Load)

**Phase 0 Status:** ✅ COMPLETED (22 Dec 2025) - ~1 hour total

**Remaining Phases Timeline:**

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1.1: Data Verification | 5 min | - |
| 1.2: Docker Config | 5 min | 1.1 |
| 1.3: Connectivity Test | 3 min | 1.2 |
| 2.1: Docker Config | 5 min | 1.3 |
| 2.2: Docker Startup | 5 min | 2.1 |
| 3.1: Smoke Tests | 3 min | 2.2 |
| 3.2: Integration Tests | 5 min | 3.1 |
| 4.1-4.6: QA Validation | 15 min | 3.2 |
| 5.1: Warmup | 3 min | 4.6 |
| 5.2: JMeter Medium | 45 min | 5.1 |
| 5.3: Performance Report | 10 min | 5.2 |
| 6-7: Results & Reporting | 30 min | 5.3 |
| 8: Cleanup & Archive | 10 min | 6-7 |
| **Remaining Total** | **~2.5 hours** | - |
| **Grand Total (0-8)** | **~3.5 hours** | - |

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| PostgreSQL schema mismatch | High | Verify schema matches framework expectations |
| Data import corruption | High | Validate row counts and referential integrity |
| Framework startup failures | Medium | Use smoke tests to catch early |
| Memory exhaustion | Medium | Monitor resource usage, reduce load if needed |
| JMeter timeout errors | Medium | Increase timeouts, reduce concurrency |
| Disk space for results | Low | Archive and compress old results |

---

## Success Criteria

**Phase 0 (Import) - COMPLETED ✅**
- ✅ XXS database successfully imported to PostgreSQL (100u / 1Kp / 5Kc)
- ✅ XS database successfully imported to PostgreSQL (500u / 5Kp / 25Kc)
- ✅ XXLarge database successfully imported to PostgreSQL (600u / 6Kp / 30Kc)
- ✅ All data transformed correctly (UUID conversion, name splitting, timestamp conversion)
- ✅ Referential integrity intact (0 orphaned posts/comments)
- ✅ Import script created and committed to git

**Phases 1-8 (Remaining Phases)**
- ⏳ Phase 1: Database verification and Docker preparation
- ⏳ 22/23 frameworks pass integration tests (async-graphql excepted)
- ⏳ All QA validations pass (schema, queries, N+1, consistency, performance)
- ⏳ JMeter completes all workloads with < 0.1% error rate
- ⏳ Performance results generated for all 8 workloads
- ⏳ Comprehensive benchmark report is accurate and insightful
- ⏳ Results are committed to git with metadata
- ⏳ Execution time for remaining phases matches estimates (±20%)
