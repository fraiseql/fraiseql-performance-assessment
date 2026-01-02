# FraiseQL Performance Assessment - Phase 8: Continuous Resource Monitoring

## Phase Overview

**Goal**: Implement real-time resource monitoring during benchmark execution, capturing CPU, memory, network I/O, disk I/O, database metrics, and container-level statistics for comprehensive performance correlation analysis.

**Scope**: Set up Prometheus, Grafana, cAdvisor, and node-exporter for comprehensive monitoring during benchmarks.

**Success Criteria**:
- Prometheus scrapes all framework metrics endpoints
- cAdvisor provides container-level metrics
- postgres_exporter provides PostgreSQL metrics
- Resource collector samples at 1-second intervals
- Grafana dashboard visualizes all metrics
- Benchmark runner integrates resource collection

## Learning Objectives

As a junior engineer, by completing Phase 8 you will learn:

1. **Advanced Query Patterns**: Aggregations, window functions, complex JOINs
2. **Pagination Strategies**: Offset vs cursor-based pagination performance
3. **Full-Text Search**: PostgreSQL tsvector, GIN indexes, ranking algorithms
4. **N+1 Query Detection**: Query counting, DataLoader effectiveness measurement
5. **Concurrent Write Testing**: Transaction isolation, lock contention, write performance
6. **Mixed Workload Simulation**: Traffic pattern analysis, weighted distribution
7. **Performance Analysis**: Query plan optimization, index effectiveness, bottleneck identification

## Implementation Steps

### Step 1: Aggregation Workload
**Estimated Time**: 1 hour

```graphql
# GraphQL aggregation queries
query UserStats($userId: ID!) {
  user(id: $userId) {
    id
    postCount
    commentCount
    followerCount
    totalLikes
  }
}

query PopularPosts($limit: Int!) {
  popularPosts(limit: $limit) {
    id title likeCount commentCount author { username }
  }
}
```

```python
# FraiseQL aggregation resolver
def resolve_user_stats(self, info, user_id):
    db = info.context["db"]
    result = db.execute("""
        SELECT
            (SELECT COUNT(*) FROM benchmark.posts WHERE author_id = $1) as post_count,
            (SELECT COUNT(*) FROM benchmark.comments WHERE author_id = $1) as comment_count,
            (SELECT COUNT(*) FROM benchmark.user_follows WHERE following_id = $1) as follower_count,
            COALESCE(SUM(like_count), 0) as total_likes
        FROM (
            SELECT COUNT(*) as like_count
            FROM benchmark.post_likes pl
            JOIN benchmark.posts p ON pl.post_id = p.id
            WHERE p.author_id = $1
            GROUP BY p.id
        ) likes
    """, (user_id,))
    return UserStats(**result[0])
```

### Step 2: Pagination Workload
**Estimated Time**: 1 hour

```python
# Cursor-based pagination implementation
def resolve_posts_cursor(self, info, first, after=None):
    db = info.context["db"]
    if after:
        created_at, last_id = decode_cursor(after)
        return db.execute("""
            SELECT id, title, author_id, created_at
            FROM benchmark.posts
            WHERE status = 'published'
              AND (created_at, id) < ($1, $2)
            ORDER BY created_at DESC, id DESC
            LIMIT $3
        """, (created_at, last_id, first + 1))
    else:
        return db.execute("""
            SELECT id, title, author_id, created_at
            FROM benchmark.posts
            WHERE status = 'published'
            ORDER BY created_at DESC, id DESC
            LIMIT $1
        """, (first + 1,))
```

### Step 3: Full-Text Search Workload
**Estimated Time**: 45 minutes

```sql
-- Full-text search indexes
ALTER TABLE benchmark.posts ADD COLUMN search_vector tsvector;
UPDATE benchmark.posts SET search_vector = 
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(content, '')), 'B');
CREATE INDEX idx_posts_search ON benchmark.posts USING GIN (search_vector);
```

```python
# Full-text search implementation
def resolve_search_posts(self, info, query, limit=10):
    db = info.context["db"]
    return db.execute("""
        SELECT id, title, content,
               ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
        FROM benchmark.posts
        WHERE search_vector @@ plainto_tsquery('english', $1)
          AND status = 'published'
        ORDER BY rank DESC
        LIMIT $2
    """, (query, limit))
```

### Step 4: Deep Traversal Workload
**Estimated Time**: 45 minutes

```graphql
# Deep traversal query
query DeepUserTraversal($userId: ID!) {
  user(id: $userId) {
    posts(limit: 3) {
      comments(limit: 3) {
        author { username followerCount }
      }
    }
    followers(limit: 3) {
      posts(limit: 2) { likeCount }
    }
  }
}
```

### Step 5: Mutation Workload
**Estimated Time**: 45 minutes

```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id title author { postCount }
  }
}
```

### Step 6: Mixed Workload
**Estimated Time**: 30 minutes

```xml
<!-- JMeter mixed workload with weighted distribution -->
<ThreadGroup testname="Mixed Workload">
  <ThroughputController percentThroughput="40">
    <IncludeController includePath="simple.jmx"/>
  </ThroughputController>
  <ThroughputController percentThroughput="20">
    <IncludeController includePath="parameterized.jmx"/>
  </ThroughputController>
  <ThroughputController percentThroughput="15">
    <IncludeController includePath="search.jmx"/>
  </ThroughputController>
  <ThroughputController percentThroughput="25">
    <IncludeController includePath="mixed-reads.jmx"/>
  </ThroughputController>
</ThreadGroup>
```

## Best Practices Learned

### 1. Query Optimization
- Use EXPLAIN ANALYZE to understand query plans
- Create appropriate indexes for query patterns
- Avoid N+1 queries with DataLoader
- Optimize aggregation queries

### 2. Pagination Design
- Prefer cursor-based pagination for performance
- Implement proper cursor encoding/decoding
- Handle edge cases (empty results, invalid cursors)
- Consider memory implications of large result sets

### 3. Search Implementation
- Use database full-text search capabilities
- Implement proper ranking algorithms
- Handle search term preprocessing
- Consider search result highlighting

## Phase Sign-off

**Phase 7 Status**: ☐ Ready for Phase 8 ☐ Needs Remediation

**Workloads Implemented**:
- Simple queries, parameterized lookups, aggregations
- Pagination (offset + cursor), full-text search
- Deep traversal, mutations, mixed realistic traffic

**Performance Validations**:
- N+1 queries prevented with DataLoader
- Indexes used in query execution plans
- Cursor pagination performs better than offset</content>
<parameter name="filePath">.phases/phase-7-advanced-workloads-detailed.md