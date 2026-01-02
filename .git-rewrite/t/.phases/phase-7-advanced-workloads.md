# Phase 7: Advanced Workload Scenarios

## Objective

Implement comprehensive workload scenarios that stress different aspects of each framework: aggregations, pagination strategies, full-text search, concurrent writes, deep relationship traversal, and mixed realistic traffic patterns.

## Context

**Current State:**
- Only basic CRUD operations tested
- No aggregation queries
- No pagination comparison (offset vs cursor)
- No concurrent write stress testing
- No full-text search scenarios
- No mixed workload simulation

**Target State:**
- 8 distinct workload categories
- Parameterized JMeter test plans for each
- CSV datasets for realistic data distribution
- Weighted mixed workload simulating real traffic

## Workload Categories

| Category | Purpose | Key Metrics |
|----------|---------|-------------|
| Simple | Protocol overhead | Max throughput |
| Parameterized | Single entity lookup | p50, p95, p99 |
| Aggregation | COUNT, SUM, GROUP BY | Query complexity handling |
| Pagination | Offset vs Cursor | Performance at scale |
| Full-text | ILIKE, tsvector | Search optimization |
| Deep Traversal | 3+ levels nesting | N+1 detection |
| Mutations | Write operations | Concurrent write handling |
| Mixed | Realistic traffic | Overall system behavior |

## Files to Create

| File | Purpose |
|------|---------|
| `tests/perf/jmeter/workloads/simple.jmx` | Simple ping/pong tests |
| `tests/perf/jmeter/workloads/parameterized.jmx` | Entity lookups with IDs |
| `tests/perf/jmeter/workloads/aggregation.jmx` | COUNT, SUM queries |
| `tests/perf/jmeter/workloads/pagination.jmx` | Offset vs cursor comparison |
| `tests/perf/jmeter/workloads/fulltext.jmx` | Search queries |
| `tests/perf/jmeter/workloads/deep-traversal.jmx` | Nested relationships |
| `tests/perf/jmeter/workloads/mutations.jmx` | Write operations |
| `tests/perf/jmeter/workloads/mixed.jmx` | Combined realistic traffic |
| `tests/perf/datasets/search_terms.csv` | Search query terms |
| `tests/perf/datasets/pagination_offsets.csv` | Pagination parameters |
| `tests/perf/datasets/mutation_payloads.csv` | Update payloads |
| `database/05-fulltext-indexes.sql` | Full-text search setup |

## Implementation Steps

### Step 1: Simple Workload (Baseline)

```xml
<!-- tests/perf/jmeter/workloads/simple.jmx -->
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Simple Workload">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="FRAMEWORK_HOST" elementType="Argument">
            <stringProp name="Argument.name">FRAMEWORK_HOST</stringProp>
            <stringProp name="Argument.value">${__P(host,localhost)}</stringProp>
          </elementProp>
          <elementProp name="FRAMEWORK_PORT" elementType="Argument">
            <stringProp name="Argument.name">FRAMEWORK_PORT</stringProp>
            <stringProp name="Argument.value">${__P(port,4000)}</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Simple Queries">
        <stringProp name="ThreadGroup.num_threads">${__P(threads,100)}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">${__P(rampup,30)}</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">${__P(loops,1000)}</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <!-- GraphQL ping -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GraphQL Ping">
          <stringProp name="HTTPSampler.domain">${FRAMEWORK_HOST}</stringProp>
          <stringProp name="HTTPSampler.port">${FRAMEWORK_PORT}</stringProp>
          <stringProp name="HTTPSampler.path">/graphql</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <stringProp name="Argument.value">{"query": "{ ping }"}</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### Step 2: Aggregation Workload

```graphql
# GraphQL queries for aggregation workload

# Query 1: User statistics aggregation
query UserStats($userId: ID!) {
  user(id: $userId) {
    id
    username
    postCount        # COUNT(posts)
    commentCount     # COUNT(comments)
    followerCount    # COUNT(followers)
    totalLikes       # SUM(post_likes)
  }
}

# Query 2: Post popularity ranking
query PopularPosts($limit: Int!) {
  popularPosts(limit: $limit) {
    id
    title
    likeCount
    commentCount
    author {
      username
    }
  }
}

# Query 3: Category statistics
query CategoryStats {
  categories {
    id
    name
    postCount
    avgLikesPerPost
  }
}

# Query 4: Time-based aggregation
query PostsByMonth($year: Int!) {
  postsByMonth(year: $year) {
    month
    postCount
    totalComments
    totalLikes
  }
}
```

**Required Schema Additions:**

```graphql
# Add to all framework schemas

type UserStats {
  postCount: Int!
  commentCount: Int!
  followerCount: Int!
  totalLikes: Int!
}

type PostPopularity {
  id: ID!
  title: String!
  likeCount: Int!
  commentCount: Int!
  author: User!
}

type CategoryStats {
  id: ID!
  name: String!
  postCount: Int!
  avgLikesPerPost: Float!
}

type MonthlyStats {
  month: Int!
  postCount: Int!
  totalComments: Int!
  totalLikes: Int!
}

extend type Query {
  userStats(userId: ID!): UserStats
  popularPosts(limit: Int = 10): [PostPopularity!]!
  categoryStats: [CategoryStats!]!
  postsByMonth(year: Int!): [MonthlyStats!]!
}
```

**Implementation Example (FraiseQL):**

```python
def resolve_user_stats(self, info, user_id):
    db = info.context["db"]
    result = db.execute("""
        SELECT
            (SELECT COUNT(*) FROM benchmark.posts WHERE author_id = $1) as post_count,
            (SELECT COUNT(*) FROM benchmark.comments WHERE author_id = $1) as comment_count,
            (SELECT COUNT(*) FROM benchmark.user_follows WHERE following_id = $1) as follower_count,
            (SELECT COALESCE(SUM(like_count), 0) FROM (
                SELECT COUNT(*) as like_count
                FROM benchmark.post_likes pl
                JOIN benchmark.posts p ON pl.post_id = p.id
                WHERE p.author_id = $1
                GROUP BY p.id
            ) likes) as total_likes
    """, (user_id,))
    return UserStats(**result[0])
```

### Step 3: Pagination Workload

```graphql
# Offset-based pagination
query PostsOffset($offset: Int!, $limit: Int!) {
  posts(offset: $offset, limit: $limit) {
    id
    title
    author { username }
  }
  totalPosts  # Required for offset pagination
}

# Cursor-based pagination
query PostsCursor($first: Int!, $after: String) {
  postsConnection(first: $first, after: $after) {
    edges {
      node {
        id
        title
        author { username }
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**Dataset for pagination testing:**

```csv
# tests/perf/datasets/pagination_offsets.csv
offset,limit,page
0,20,1
20,20,2
100,20,6
500,20,26
1000,20,51
5000,20,251
10000,20,501
50000,20,2501
```

**Pagination Implementation:**

```python
# Offset-based (inefficient at scale)
def resolve_posts_offset(self, info, offset, limit):
    db = info.context["db"]
    return db.execute("""
        SELECT id, title, author_id
        FROM benchmark.posts
        WHERE status = 'published'
        ORDER BY created_at DESC
        OFFSET $1 LIMIT $2
    """, (offset, limit))

# Cursor-based (efficient at scale)
def resolve_posts_cursor(self, info, first, after=None):
    db = info.context["db"]
    if after:
        # Decode cursor (created_at, id)
        created_at, last_id = decode_cursor(after)
        return db.execute("""
            SELECT id, title, author_id, created_at
            FROM benchmark.posts
            WHERE status = 'published'
              AND (created_at, id) < ($1, $2)
            ORDER BY created_at DESC, id DESC
            LIMIT $3
        """, (created_at, last_id, first + 1))  # +1 to check hasNextPage
    else:
        return db.execute("""
            SELECT id, title, author_id, created_at
            FROM benchmark.posts
            WHERE status = 'published'
            ORDER BY created_at DESC, id DESC
            LIMIT $1
        """, (first + 1,))
```

### Step 4: Full-Text Search Workload

```sql
-- database/05-fulltext-indexes.sql
-- Add full-text search capabilities

-- Create search vectors
ALTER TABLE benchmark.posts ADD COLUMN IF NOT EXISTS search_vector tsvector;
ALTER TABLE benchmark.users ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Populate search vectors
UPDATE benchmark.posts SET search_vector =
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(content, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(excerpt, '')), 'C');

UPDATE benchmark.users SET search_vector =
    setweight(to_tsvector('english', COALESCE(username, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(first_name || ' ' || last_name, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(bio, '')), 'C');

-- Create GIN indexes
CREATE INDEX idx_posts_search ON benchmark.posts USING GIN (search_vector);
CREATE INDEX idx_users_search ON benchmark.users USING GIN (search_vector);

-- Triggers to maintain search vectors
CREATE OR REPLACE FUNCTION benchmark.update_post_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.excerpt, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_posts_search_vector
    BEFORE INSERT OR UPDATE ON benchmark.posts
    FOR EACH ROW EXECUTE FUNCTION benchmark.update_post_search_vector();
```

```csv
# tests/perf/datasets/search_terms.csv
term,type
programming,single_word
machine learning,phrase
python OR javascript,boolean
"exact phrase",quoted
user*,prefix
database performance,multi_word
api development,common
consectetur adipiscing,lorem_ipsum
```

**Search Implementation:**

```python
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

def resolve_search_users(self, info, query, limit=10):
    db = info.context["db"]
    return db.execute("""
        SELECT id, username, first_name, last_name, bio,
               ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
        FROM benchmark.users
        WHERE search_vector @@ plainto_tsquery('english', $1)
        ORDER BY rank DESC
        LIMIT $2
    """, (query, limit))
```

### Step 5: Deep Traversal Workload

```graphql
# Level 3 traversal - demonstrates N+1 problem
query DeepUserTraversal($userId: ID!) {
  user(id: $userId) {
    id
    username
    posts(limit: 5) {
      id
      title
      comments(limit: 3) {
        id
        content
        author {
          id
          username
          followerCount
        }
      }
    }
    followers(limit: 5) {
      id
      username
      posts(limit: 3) {
        id
        title
        likeCount
      }
    }
  }
}

# Level 4 traversal - extreme case
query ExtremeTraversal($userId: ID!) {
  user(id: $userId) {
    posts(limit: 3) {
      comments(limit: 3) {
        author {
          posts(limit: 2) {
            comments(limit: 2) {
              author {
                username
              }
            }
          }
        }
      }
    }
  }
}
```

**Query Count Tracking:**

```python
# Add to each framework for N+1 detection
import threading

_query_count = threading.local()

def reset_query_count():
    _query_count.value = 0

def increment_query_count():
    if not hasattr(_query_count, 'value'):
        _query_count.value = 0
    _query_count.value += 1

def get_query_count():
    return getattr(_query_count, 'value', 0)

# Wrap database execute
original_execute = db.execute
def tracked_execute(query, params=None):
    increment_query_count()
    return original_execute(query, params)
db.execute = tracked_execute

# Include in response for analysis
@app.post("/graphql")
async def graphql_endpoint(request: Request):
    reset_query_count()
    result = schema.execute(...)
    return JSONResponse({
        "data": result.data,
        "extensions": {
            "queryCount": get_query_count()
        }
    })
```

### Step 6: Mutation Workload

```graphql
# Create mutation
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title
    author {
      id
      postCount  # Verify count updated
    }
  }
}

# Update mutation with optimistic response
mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
  updatePost(id: $id, input: $input) {
    id
    title
    content
    updatedAt
  }
}

# Delete mutation
mutation DeletePost($id: ID!) {
  deletePost(id: $id) {
    success
    deletedId
  }
}

# Batch mutation
mutation BatchUpdatePosts($updates: [PostUpdate!]!) {
  batchUpdatePosts(updates: $updates) {
    updated
    failed
    errors
  }
}
```

```csv
# tests/perf/datasets/mutation_payloads.csv
operation,title,content
create,New Post Title ${__counter()},Content for post ${__counter()} with random data ${__Random(1000,9999)}
update,Updated Title ${__time()},Updated content at ${__time(HH:mm:ss)}
create,Performance Test Post,Testing concurrent write performance
```

### Step 7: Mixed Workload (Realistic Traffic)

```xml
<!-- tests/perf/jmeter/workloads/mixed.jmx -->
<!-- Weighted distribution simulating real traffic -->

<ThreadGroup testname="Mixed Workload">
  <!-- 60% Read operations -->
  <ThroughputController percentThroughput="60">
    <IncludeController includePath="simple.jmx"/>
    <IncludeController includePath="parameterized.jmx"/>
  </ThroughputController>

  <!-- 20% Search operations -->
  <ThroughputController percentThroughput="20">
    <IncludeController includePath="fulltext.jmx"/>
  </ThroughputController>

  <!-- 10% Complex reads -->
  <ThroughputController percentThroughput="10">
    <IncludeController includePath="deep-traversal.jmx"/>
    <IncludeController includePath="aggregation.jmx"/>
  </ThroughputController>

  <!-- 10% Write operations -->
  <ThroughputController percentThroughput="10">
    <IncludeController includePath="mutations.jmx"/>
  </ThroughputController>
</ThreadGroup>
```

**Traffic Distribution:**

| Operation Type | Percentage | Scenarios |
|---------------|------------|-----------|
| Simple reads | 40% | Ping, single entity |
| Parameterized reads | 20% | User by ID, Post by ID |
| Search | 15% | Full-text search |
| List with pagination | 10% | Posts list, Users list |
| Deep traversal | 5% | Nested relationships |
| Aggregations | 5% | Stats, rankings |
| Mutations | 5% | Create, update, delete |

### Step 8: JMeter Test Runner Script

```bash
#!/bin/bash
# tests/perf/scripts/run-workloads.sh

WORKLOADS_DIR="tests/perf/jmeter/workloads"
RESULTS_DIR="tests/perf/results"
FRAMEWORK="${1:-fraiseql}"
PORT="${2:-4000}"
THREADS="${3:-100}"
DURATION="${4:-300}"  # 5 minutes

timestamp=$(date +%Y%m%d_%H%M%S)
results_path="${RESULTS_DIR}/${FRAMEWORK}_${timestamp}"
mkdir -p "$results_path"

echo "Running workloads for $FRAMEWORK on port $PORT"
echo "Threads: $THREADS, Duration: ${DURATION}s"

# Run each workload
for workload in simple parameterized aggregation pagination fulltext deep-traversal mutations mixed; do
    echo "Running $workload workload..."

    jmeter -n \
        -t "${WORKLOADS_DIR}/${workload}.jmx" \
        -l "${results_path}/${workload}.jtl" \
        -e -o "${results_path}/${workload}_report" \
        -Jhost=localhost \
        -Jport=$PORT \
        -Jthreads=$THREADS \
        -Jduration=$DURATION \
        -Jframework=$FRAMEWORK

    echo "Completed $workload"
done

# Generate summary
python tests/perf/scripts/summarize-workloads.py "$results_path"
```

## Verification Commands

```bash
# Run specific workload
./tests/perf/scripts/run-workloads.sh fraiseql 4000 50 60

# Run aggregation test only
jmeter -n -t tests/perf/jmeter/workloads/aggregation.jmx \
  -Jhost=localhost -Jport=4000 -Jthreads=50 -Jloops=100

# Verify deep traversal query count
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user(id: \"00000001-1111-1111-1111-111111111111\") { posts { comments { author { username } } } } }"}' \
  | jq '.extensions.queryCount'
# FraiseQL should show 1-3 queries, others may show 50+

# Test pagination performance at scale
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ posts(offset: 50000, limit: 20) { id title } }"}'
# Should be slow with offset, fast with cursor

# Test full-text search
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ searchPosts(query: \"database performance\", limit: 10) { id title rank } }"}'
```

## Acceptance Criteria

- [ ] 8 distinct workload JMeter test plans created
- [ ] Each framework implements all required query types
- [ ] Search indexes created and functional
- [ ] Cursor-based pagination implemented
- [ ] Query count tracking for N+1 detection
- [ ] Mixed workload properly weighted
- [ ] CSV datasets for parameterized testing
- [ ] Summary report generated after workload runs

## DO NOT

- Skip warmup before measurement runs
- Use identical queries without parameterization
- Ignore query count in results
- Test pagination only at small offsets
- Skip concurrent write testing

## Estimated Complexity

**High** - Requires schema additions across all frameworks, new database indexes, and complex JMeter test plan construction.
