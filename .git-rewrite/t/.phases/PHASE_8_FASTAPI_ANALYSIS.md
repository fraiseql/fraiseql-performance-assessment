# Phase 8: FastAPI REST Framework Analysis

## Architecture Overview

**FastAPI** is a modern, high-performance REST API framework built on Python's async capabilities. Unlike GraphQL frameworks, FastAPI serves multiple endpoints, each returning specific data structures. This prevents overfetching but can introduce N+1 query problems through endpoint composition.

### Key Components

1. **ASGI Server**: Async request handling
   - Starlette-based async routing
   - Connection pooling via asyncpg
   - Concurrent request handling

2. **Endpoint-Based Architecture**: Multiple routes for different operations
   - `/users` → fetch all users
   - `/users/{id}` → fetch specific user
   - `/users/{id}/posts` → fetch user's posts
   - Explicit N+1 potential (need `include` pattern)

3. **Type Validation**: Pydantic models
   - Automatic request/response validation
   - Type hints for automatic serialization
   - Overhead: 2-5ms per request

4. **Connection Pooling**: AsyncPG support
   - Async database driver
   - Connection reuse across requests
   - Configurable pool size

### Performance Design Choices

- **Async-first architecture**: Leverages Python async/await
- **Simplicity of REST**: No GraphQL parsing overhead
- **Explicit routing**: No query complexity analysis needed
- **Separation of concerns**: Each endpoint serves specific purpose

---

## Performance Characteristics

### Expected Throughput

**Sustained Load**:
- Simple endpoint: 400-600 req/sec
- Single object fetch: 350-500 req/sec
- List with pagination: 300-400 req/sec
- Multiple endpoints (N+1 pattern): 100-200 req/sec
- Overall mixed: 300-400 req/sec

### Expected Latency

| Workload | p50 | p99 | p99.9 |
|----------|-----|-----|-------|
| Simple | 5-15ms | 30-80ms | 100-200ms |
| Parameterized | 10-20ms | 50-100ms | 150-300ms |
| Aggregation | 20-40ms | 80-150ms | 200-400ms |
| Pagination | 15-30ms | 60-120ms | 150-300ms |
| Full-text Search | 25-50ms | 100-200ms | 250-500ms |
| Deep Traversal (3 requests) | 50-150ms | 200-400ms | 500-1000ms |
| Mutations | 30-60ms | 100-200ms | 250-500ms |

### Memory Per Concurrent Connection

**Baseline**: ~3-5 MB per active connection
- Python process overhead: 50-60 MB
- Per-request allocation: +0.5-1 MB
- Peak memory: 150-250 MB

### HTTP Request/Response Patterns

- **Simple query**: Single request → single response
- **Aggregation**: Single endpoint returns aggregated data
- **Deep traversal**: 3-5 requests (one per level)
- **Payload size**: Larger than GraphQL (all fields returned)

---

## Bottleneck Analysis

### 1. N+1 Through Multiple Endpoints

**The Problem**: Unlike GraphQL where one query can fetch multiple levels, REST requires multiple requests.

**Pattern (Deep Traversal)**:
```
Request 1: GET /users → List of users (10 users)
Request 2-11: GET /users/{id}/posts → 10 requests (one per user!)
Request 12-111: GET /posts/{id}/comments → 100 requests
Total: 111 HTTP requests for one logical query
```

**vs GraphQL**:
```
Request 1: Single GraphQL query with nested fields
Total: 1 HTTP request
```

**Impact**:
- Network round-trip overhead: 50-100ms per request
- Total latency: 111 * (5ms + 50ms overhead) = 6+ seconds
- With "include" optimization: 3-4 requests, 200-400ms

### 2. Request Routing Overhead

**The Issue**: Each request must be routed to correct handler.

**Pattern**:
- Request → Route matching → Handler lookup → Execution

**Impact**:
- Route matching: 0.1-0.5ms per request
- Cumulative with N+1: Significant (visible at 100+ req/sec)

### 3. Serialization Per Endpoint

**The Issue**: Each endpoint serializes response to JSON.

**Pattern**:
- Result object → Pydantic model → JSON serialization

**Impact**:
- 2-5ms per response
- Cumulative on N+1: 5-10ms overhead per extra request

### 4. Connection Pool Contention (Unlike GraphQL)

**The Issue**: Multiple sequential requests use same connection pool.

**Pattern**:
- Request 1 uses connection A
- Request 2 (while 1 in progress) uses connection B
- If pool size < concurrent requests × request depth: Queue

**Impact**:
- Pool saturation on deep requests
- p99 spikes when pool exhausted
- Mitigation: Increase pool size (trade: memory)

---

## Workload Suitability Analysis

### 1. Simple (Ping)
- **Suitability**: ⭐⭐⭐⭐⭐ (Perfect)
- **Why**: Single endpoint, no joins
- **Expected latency**: 10-20ms

### 2. Parameterized
- **Suitability**: ⭐⭐⭐⭐⭐ (Perfect)
- **Why**: Direct index lookup, single request
- **Expected latency**: 15-40ms

### 3. Aggregation
- **Suitability**: ⭐⭐⭐⭐ (Very Good)
- **Why**: Single aggregation endpoint, no joins needed
- **Expected latency**: 30-80ms
- **Note**: Requires aggregation endpoint in API design

### 4. Pagination
- **Suitability**: ⭐⭐⭐⭐⭐ (Perfect)
- **Why**: REST pagination is standard
- **Expected latency**: 20-60ms

### 5. Full-text Search
- **Suitability**: ⭐⭐⭐⭐ (Very Good)
- **Why**: PostgreSQL FTS, simple result return
- **Expected latency**: 40-120ms

### 6. Deep Traversal
- **Suitability**: ⭐ (Poor - without include pattern)
- **Why**: Requires 3-5 sequential requests
- **Without optimization**: 6+ seconds (6000+ requests) - NOT representative of real usage
- **With include pattern**: 200-400ms (3-4 requests) - Realistic performance
- **CRITICAL REQUIREMENT**: The `include` query parameter pattern MUST be implemented for Phase 8 testing.
  - Without it: Deep traversal will require 20+ sequential HTTP requests (~6+ seconds latency)
  - This breakdown of the benchmark would not represent real-world API design
  - Phase 8 testing assumes proper API resource composition via include parameters

### 7. Mutations
- **Suitability**: ⭐⭐⭐⭐ (Very Good)
- **Why**: RESTful mutation endpoints, clear error handling
- **Expected latency**: 40-120ms

### 8. Mixed
- **Suitability**: ⭐⭐⭐⭐ (Very Good)
- **Why**: Balanced endpoint mix
- **Expected latency**: 40-100ms

---

## Baseline Expectations

### Key Metrics

**Throughput**:
- Peak: 400-600 req/sec (simple endpoints)
- Average (mixed): 300-400 req/sec
- Deep traversal (with include): 100-200 req/sec (3-5 requests)

**Latency**:
- p50: 20-40ms
- p99: 100-150ms
- p99.9: 250-500ms

**Memory**:
- Baseline: 60-80 MB
- Peak: 150-250 MB
- Growth: Stable (no object instantiation)

**HTTP Requests**:
- Simple: 1
- Deep traversal: 3-5 (with include)
- Deep traversal: 20+ (without include)

### Success Criteria

✅ **Performing well**:
- p99 latency <150ms
- Memory stable
- HTTP request count matches expected
- No connection pool saturation

⚠️ **Performance issues**:
- p99 latency >250ms
- Deep traversal takes >1 second
- Connection pool errors
- Serialization overhead >10%

---

## Comparison with Other Frameworks

### FastAPI vs Flask
| Aspect | FastAPI | Flask |
|--------|---------|-------|
| Async | Native | Limited |
| Throughput | 300-400 req/sec | 200-300 req/sec |
| Latency | 100-150ms p99 | 150-200ms p99 |
| Type validation | Automatic | Manual |
| Startup time | <1s | <1s |

### FastAPI vs FraiseQL
| Aspect | FastAPI | FraiseQL |
|--------|---------|----------|
| Protocol | REST | GraphQL |
| Deep traversal | 3-5 requests | 1 request |
| Throughput | 300-400 req/sec | 500-800 req/sec |
| Latency p99 | 100-150ms | <100ms |
| Query complexity | N+1 risk | Auto-prevented |

### FastAPI vs Apollo Server (Node.js)
| Aspect | FastAPI | Apollo |
|--------|---------|--------|
| Throughput | 300-400 req/sec | 200-400 req/sec |
| Latency | Consistent | Variable (GC) |
| Async model | AsyncIO | Event loop |
| Memory | Stable | Fragmented |

---

## Phase 8 Measurement Focus

### High Priority
1. **HTTP request count per workload** - N+1 indicator
2. **Endpoint latency breakdown** - Route overhead + DB overhead
3. **Connection pool saturation** - Queue depth during deep traversal
4. **Serialization overhead** - Pydantic model time

### Medium Priority
5. **Memory per concurrent request** - Should be <1 MB
6. **Payload size comparison** - vs GraphQL
7. **Route matching latency** - Per request overhead

### Analysis Techniques

```python
# Measure endpoint routing
1. Log route matching time
2. Measure handler execution time
3. Subtract from total latency
4. Endpoint overhead = (latency - DB time - serialization)
```

---

## Conclusion

FastAPI excels at REST API performance but struggles with deep data traversal requiring multiple requests. The framework is fast (300-400 req/sec) and simple, making it ideal for traditional REST APIs where N+1 is not an issue (e.g., mobile backends).

For Phase 8, focus on:
- Verifying HTTP request counts for each workload
- Ensuring connection pool doesn't saturate
- Measuring endpoint routing overhead
- Detecting N+1 in deep traversal without include pattern

FastAPI is most suitable for REST-centric applications where multiple requests per logical operation are acceptable or unavoidable.
