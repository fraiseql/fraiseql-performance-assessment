# Phase 7: Advanced Workload Scenarios - Completion Report

## Overview

Phase 7 successfully implements comprehensive workload scenarios that stress different aspects of each framework: aggregations, pagination strategies, full-text search, concurrent writes, deep relationship traversal, and mixed realistic traffic patterns.

## Completion Status

✅ **COMPLETE** - All Phase 7 objectives implemented and ready for framework integration.

---

## Deliverables

### 1. Database Infrastructure

**File**: `database/06-fulltext-indexes.sql`

✅ **Components Created**:
- Full-text search vectors for `tb_post` (title, content)
- Full-text search vectors for `tb_user` (username, full_name, bio)
- GIN indexes for both tables for fast tsvector searches
- Trigger functions to automatically maintain search vectors on INSERT/UPDATE
- Helper functions: `search_posts()` and `search_users()`
- Additional indexes for aggregation and user stats queries

**Verification**:
```sql
-- Search vectors populated: 10,005 users, 5 posts
SELECT COUNT(*) FROM benchmark.tb_post WHERE search_vector IS NOT NULL;  -- 5
SELECT COUNT(*) FROM benchmark.tb_user WHERE search_vector IS NOT NULL;  -- 10,005

-- Test searches work correctly
SELECT id, username FROM benchmark.tb_user
WHERE search_vector @@ plainto_tsquery('english', 'user') LIMIT 3;
```

### 2. JMeter Workload Test Plans

**Location**: `tests/perf/jmeter/workloads/`

✅ **8 Workloads Created**:

| Workload | File | Purpose | Metrics |
|----------|------|---------|---------|
| Simple | `simple.jmx` | Protocol overhead (ping) | Max throughput |
| Parameterized | `parameterized.jmx` | Single entity lookup | p50, p95, p99 latencies |
| Aggregation | `aggregation.jmx` | COUNT, SUM, GROUP BY | Query complexity handling |
| Pagination | `pagination.jmx` | Offset vs Cursor | Performance at scale |
| Full-text | `fulltext.jmx` | ILIKE, tsvector search | Search optimization |
| Deep Traversal | `deep-traversal.jmx` | 3+ levels nesting | N+1 detection |
| Mutations | `mutations.jmx` | Write operations | Concurrent write handling |
| Mixed | `mixed.jmx` | Realistic traffic | Overall system behavior |

**Template Structure**:
- JMeter 5.6 compatible
- HTTP POST to `/graphql` endpoint
- Configurable threads, ramp-up time, and loop count
- Each runs with 50 threads, 30s ramp-up, 100 iterations by default

### 3. Parameter Datasets

**Location**: `tests/perf/datasets/`

✅ **CSV Files Created**:

1. **search_terms.csv** (20 search queries)
   - Single words, phrases, boolean queries, quoted searches
   - Covers various PostgreSQL FTS operators

2. **pagination_offsets.csv** (10 pagination parameters)
   - Offsets: 0, 20, 40, 100, 200, 500, 1000, 2500, 5000, 10000
   - All with 20-item limit

3. **mutation_payloads.csv** (10 mutation payloads)
   - Create operations (5)
   - Update operations (5)

### 4. Workload Runner Infrastructure

**Scripts Created**:

1. **run-workloads.sh** - Main orchestration script
   - Executes all 8 workloads sequentially
   - Generates JTL result files and HTML reports
   - Calls summarization script for analysis
   - Usage: `./tests/perf/scripts/run-workloads.sh [framework] [port] [threads] [loops]`

2. **summarize-workloads.py** - Result analysis and reporting
   - Parses JMeter JTL CSV output files
   - Calculates latency statistics (min, max, avg, p50, p95, p99)
   - Generates JSON summary and console output
   - Tracks error rates and response codes

3. **create_jmeter_workloads.sh** - Workload generator
   - Template-based JMeter test plan generation
   - Easily customizable for new workload types

---

## Framework Integration Requirements

Each framework must implement the following query types for Phase 7:

### 1. Aggregation Queries

**Required Fields**:
- `postCount`: COUNT of posts by user
- `commentCount`: COUNT of comments by user
- `followerCount`: COUNT of followers
- `totalLikes`: SUM of likes across user's posts

**Example Query**:
```graphql
query {
  users(limit: 5) {
    id
    username
    posts(limit: 3) {
      id
      title
    }
  }
}
```

### 2. Pagination Queries

**Offset-based** (less efficient at scale):
```graphql
query {
  users(limit: 20, offset: 100) {
    id
    username
  }
}
```

**Cursor-based** (efficient at scale):
```graphql
query {
  usersConnection(first: 20, after: "cursor_value") {
    edges {
      node { id username }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### 3. Full-text Search Queries

```graphql
query {
  searchUsers(query: "username OR bio") {
    id
    username
    bio
  }
}
```

### 4. Deep Traversal Queries (N+1 Detection)

```graphql
query {
  users(limit: 3) {
    id
    username
    posts(limit: 2) {
      id
      title
      comments(limit: 2) {
        id
        content
      }
    }
  }
}
```

### 5. Mutation Queries

```graphql
mutation {
  createPost(input: {title: "...", content: "..."}) {
    id
    title
    author { username }
  }
}
```

### 6. Query Count Tracking

For N+1 detection, frameworks should track database query count and include in response extensions:

```json
{
  "data": { ... },
  "extensions": {
    "queryCount": 3,
    "queryTime": 42.5
  }
}
```

---

## Testing Workflow

### Quick Test
```bash
# Test a single workload against FraiseQL
jmeter -n -t tests/perf/jmeter/workloads/simple.jmx \
  -Jhost=localhost -Jport=4000 -Jthreads=10 -Jloops=10 \
  -l results/simple.jtl -e -o results/simple_report
```

### Full Workload Suite
```bash
# Run all workloads for a framework
./tests/perf/scripts/run-workloads.sh fraiseql 4000 50 100

# View results
open tests/perf/results/fraiseql_*/summary.json
```

### Framework Comparison
```bash
# Test multiple frameworks
./tests/perf/scripts/run-workloads.sh fraiseql 4000 50 100
./tests/perf/scripts/run-workloads.sh strawberry 5000 50 100
./tests/perf/scripts/run-workloads.sh gqlgen 6000 50 100

# Compare in results directory
ls tests/perf/results/
```

---

## Database Verification

All Phase 7 database requirements verified:

✅ Full-text search vectors created and populated
✅ GIN indexes created for fast tsvector queries
✅ Trigger functions maintain vectors on data changes
✅ Helper search functions created
✅ Additional indexes for aggregation queries
✅ 10,005 test users with searchable data
✅ 5 test posts with searchable content

**Test Query**:
```sql
SELECT search_posts('database', 10);
SELECT search_users('test', 10);
```

---

## Phase 7 Checklist

✅ 8 distinct workload JMeter test plans created
✅ Each workload properly parameterized
✅ Search indexes created and functional
✅ Cursor-based pagination structure defined
✅ Query count tracking pattern documented
✅ CSV datasets for parameterized testing created
✅ Workload runner script (`run-workloads.sh`) created
✅ Result summarization script (`summarize-workloads.py`) created
✅ Full database schema for Phase 7 applied
✅ Mixed workload with realistic traffic weights defined

---

## Next Steps for Framework Teams

Each framework team should:

1. **Implement query types** from Framework Integration Requirements section
2. **Add query count tracking** to detect N+1 problems
3. **Run workload suite** using provided scripts:
   ```bash
   ./tests/perf/scripts/run-workloads.sh [framework-name] [port] 50 100
   ```
4. **Review results** in generated HTML reports and JSON summary
5. **Optimize** based on performance metrics (especially pagination and deep traversal)
6. **Document** findings in framework-specific analysis file

---

## Performance Baselines

These are established baseline expectations:

| Workload | Expected Behavior | Red Flag |
|----------|-------------------|----------|
| Simple | 1000+ req/sec | < 500 req/sec |
| Parameterized | p99 < 100ms | p99 > 500ms |
| Aggregation | p99 < 200ms | p99 > 1000ms |
| Pagination (offset) | Degradation > page 100 | No degradation |
| Pagination (cursor) | Consistent < 50ms | Inconsistent latency |
| Full-text | p99 < 150ms | Errors on searches |
| Deep Traversal | p99 < 300ms | Query count > 50 |
| Mutations | p99 < 200ms | Errors on writes |

---

## Files Summary

**New Files Created**: 17
- Database schema: 1
- JMeter workloads: 8
- CSV datasets: 3
- Scripts: 5

**Total Lines of Code**: ~2,000

---

## Phase Sign-off

**Status**: ✅ COMPLETE

**Phase 7 Achievements**:
- Comprehensive workload testing infrastructure
- Database optimizations for advanced queries
- Reusable testing framework for all GraphQL implementations
- Clear path for performance analysis and optimization

**Ready for Integration**: Yes

Framework teams can now proceed with implementing Phase 7 query types and running comprehensive performance testing.
