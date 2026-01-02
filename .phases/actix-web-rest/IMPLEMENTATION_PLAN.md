# Actix-web REST Framework Implementation Plan

## 📋 Overview

Implement a high-performance REST API in Rust using **Actix-web** framework to provide a compiled language baseline for performance benchmarking. This will enable direct comparison between interpreted languages (Python, Node.js) and compiled Rust.

---

## 🎯 Objectives

1. **Implement Actix-web REST API** matching the existing 5 REST endpoints
2. **Achieve sub-20ms latency** to establish compiled language baseline
3. **Support all existing workload patterns** (simple, parameterized, aggregation, etc.)
4. **Enable prometheus metrics collection** for performance monitoring
5. **Provide Docker deployment** matching other frameworks
6. **Document Rust async/ORM patterns** for reference implementation

---

## 📊 Scope

### What's Included

- ✅ Full REST API implementation (5 endpoints)
- ✅ PostgreSQL connection pooling (sqlx with pgx)
- ✅ N+1 query prevention (manual batch loading)
- ✅ Prometheus metrics (`/metrics` endpoint)
- ✅ Health checks (`/health` endpoint)
- ✅ Docker container with alpine base
- ✅ Dockerfile optimized for small size

### What's NOT Included

- ❌ ORM variant (initial release is raw SQL with sqlx)
- ❌ WebSocket/subscriptions
- ❌ GraphQL (that's async-graphql phase)
- ❌ Authentication/authorization

---

## 🏗️ Architecture

### Directory Structure

```
frameworks/actix-web-rest/
├── Cargo.toml                 # Rust dependencies
├── src/
│   ├── main.rs               # Application entry point
│   ├── models.rs             # Data models (User, Post, Comment)
│   ├── db.rs                 # Database initialization & pool
│   ├── handlers.rs           # HTTP endpoint handlers
│   ├── metrics.rs            # Prometheus metrics setup
│   └── error.rs              # Error handling utilities
├── Dockerfile                # Multi-stage build
└── .dockerignore
```

### Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Framework** | Actix-web | 4.x | High-performance, async-first |
| **Async Runtime** | Tokio | 1.x | Industry standard Rust async |
| **Database Driver** | sqlx | 0.7.x | Compile-time query verification |
| **Connection Pool** | deadpool-postgres | 0.14.x | Efficient connection pooling |
| **JSON** | serde_json | 1.x | Standard serialization |
| **Metrics** | prometheus | 0.13.x | Same as other frameworks |
| **Logging** | tracing/tracing-subscriber | 0.1.x | Structured logging |
| **Base Image** | rust:1.82-alpine | Latest | Small, production-ready |

### Data Models

```rust
// User model - matches database schema
pub struct User {
    pub id: String,
    pub username: String,
    pub first_name: String,
    pub last_name: String,
    pub bio: Option<String>,
}

// Post model with eager-loaded author
pub struct Post {
    pub id: String,
    pub title: String,
    pub content: Option<String>,
    pub author_id: String,
    pub author: User,  // eager loaded
    pub created_at: DateTime<Utc>,
}

// Comment model with eager-loaded relationships
pub struct Comment {
    pub id: String,
    pub content: String,
    pub post_id: String,
    pub author_id: String,
    pub author: User,  // eager loaded
    pub created_at: DateTime<Utc>,
}
```

---

## 📝 Implementation Phases

### Phase 1: Project Setup & Dependencies
**Objective**: Create Rust project structure with all dependencies

**Tasks**:
1. Initialize Cargo project
   ```bash
   cargo new frameworks/actix-web-rest
   ```

2. Add dependencies to `Cargo.toml`
   ```toml
   [dependencies]
   actix-web = "4.4"
   actix-rt = "2.9"
   tokio = { version = "1.35", features = ["full"] }
   serde = { version = "1.0", features = ["derive"] }
   serde_json = "1.0"
   sqlx = { version = "0.7", features = ["runtime-tokio-native-tls", "postgres", "json", "uuid"] }
   deadpool-postgres = "0.14"
   prometheus = "0.13"
   tracing = "0.1"
   tracing-subscriber = { version = "0.3", features = ["env-filter"] }
   chrono = { version = "0.4", features = ["serde"] }
   uuid = { version = "1.6", features = ["serde", "v4"] }
   thiserror = "1.0"

   [dev-dependencies]
   tokio-test = "0.4"
   ```

3. Set up `Cargo.toml` metadata
   - Project name: `actix-web-rest`
   - Edition: 2021
   - Authors, license, description

**Deliverables**:
- ✅ Working `cargo build` command
- ✅ All dependencies compile without errors
- ✅ Basic project structure created

**Verification**:
```bash
cd frameworks/actix-web-rest
cargo check   # Should succeed
cargo build   # Should compile
```

---

### Phase 2: Database Connection & Models
**Objective**: Set up PostgreSQL connection pooling and data models

**Tasks**:
1. Create `src/models.rs` with data structures
   - User struct with all fields
   - Post struct with eager-loaded author
   - Comment struct with eager-loaded relationships
   - Implement `Serialize` and `Deserialize` for all

2. Create `src/db.rs` with connection management
   - Initialize deadpool-postgres pool
   - Create connection acquisition function
   - Set pool size from environment (default: 20-100)
   - Implement connection health check

3. Create database initialization script
   - Connect to test PostgreSQL
   - Verify all required tables exist
   - Add indexes if missing
   - Log database schema version

**Code Example** (`src/models.rs`):
```rust
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub username: String,
    pub first_name: String,
    pub last_name: String,
    pub bio: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Post {
    pub id: String,
    pub title: String,
    pub content: Option<String>,
    pub author_id: String,
    pub author: User,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Comment {
    pub id: String,
    pub content: String,
    pub post_id: String,
    pub author_id: String,
    pub author: User,
    pub created_at: DateTime<Utc>,
}
```

**Deliverables**:
- ✅ All models defined and compile
- ✅ Connection pool can be created
- ✅ Pool connections to real PostgreSQL
- ✅ No serialization errors

**Verification**:
```bash
cargo build
# Manual test:
# 1. Start PostgreSQL container
# 2. Set DATABASE_URL env var
# 3. Test pool connects and acquires connection
```

---

### Phase 3: HTTP Handlers & Endpoints
**Objective**: Implement all 5 REST endpoints matching existing frameworks

**Tasks**:
1. Create `src/handlers.rs` with endpoint implementations

2. Implement 5 endpoints:

   **a) GET /health**
   ```rust
   pub async fn health() -> HttpResponse {
       HttpResponse::Ok().json(json!({"status": "ok"}))
   }
   ```

   **b) GET /users/{user_id}**
   - Query: `SELECT * FROM benchmark.tb_user WHERE id = $1`
   - Response: User JSON
   - Error handling: 404 if not found

   **c) GET /users?limit=10&offset=0&include=posts,comments**
   - Query: `SELECT * FROM benchmark.tb_user LIMIT $1 OFFSET $2`
   - Optional eager loading based on `include` parameter
   - Response: Array of User objects

   **d) GET /posts/{post_id}**
   - Query: `SELECT * FROM benchmark.tb_post WHERE id = $1`
   - Eager load author relationship
   - Optional: load comments if `include=comments`

   **e) GET /posts?limit=10&offset=0&include=comments**
   - Query: `SELECT * FROM benchmark.tb_post LIMIT $1 OFFSET $2`
   - Eager load authors for all posts
   - Optional: load all comments if `include=comments`

3. Implement error handling
   - Return proper HTTP status codes (400, 404, 500)
   - Include error messages in response
   - Log all errors

4. Create `src/error.rs` for custom error types
   ```rust
   #[derive(Debug, thiserror::Error)]
   pub enum ApiError {
       #[error("Database error: {0}")]
       DatabaseError(String),

       #[error("Not found")]
       NotFound,

       #[error("Bad request: {0}")]
       BadRequest(String),
   }

   impl ResponseError for ApiError {
       fn status_code(&self) -> StatusCode { /* ... */ }
       fn error_response(&self) -> HttpResponse { /* ... */ }
   }
   ```

**Code Example** (GET /users/{user_id}):
```rust
#[get("/users/{user_id}")]
pub async fn get_user(
    user_id: web::Path<String>,
    db: web::Data<Pool>,
) -> Result<HttpResponse, ApiError> {
    let client = db.get().await
        .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

    let user = client.query_one(
        "SELECT id, username, first_name, last_name, bio
         FROM benchmark.tb_user WHERE id = $1",
        &[&user_id.into_inner()]
    ).await
        .map_err(|_| ApiError::NotFound)?;

    let user = User {
        id: user.get("id"),
        username: user.get("username"),
        first_name: user.get("first_name"),
        last_name: user.get("last_name"),
        bio: user.get("bio"),
    };

    Ok(HttpResponse::Ok().json(user))
}
```

**Deliverables**:
- ✅ All 5 endpoints defined and routed
- ✅ Request/response serialization working
- ✅ Error handling implemented
- ✅ Handlers compile without warnings

**Verification**:
```bash
cargo build
# Manual test with curl:
# curl http://localhost:8001/health
# curl http://localhost:8001/users/{some-id}
# curl "http://localhost:8001/users?limit=5"
```

---

### Phase 4: Prometheus Metrics
**Objective**: Add performance monitoring metrics matching other frameworks

**Tasks**:
1. Create `src/metrics.rs` with metric definitions
   ```rust
   use prometheus::{Counter, Histogram, Registry};

   pub struct Metrics {
       pub http_requests_total: Counter,
       pub http_request_duration_seconds: Histogram,
   }
   ```

2. Implement metrics collection
   - Track request count per endpoint
   - Track request latency per endpoint
   - Track error rates
   - Register metrics with Prometheus registry

3. Create `/metrics` endpoint
   - Expose Prometheus metrics in text format
   - Match format of other frameworks
   - Include all counters and histograms

4. Add middleware for automatic metric collection
   ```rust
   pub struct MetricsMiddleware {
       metrics: web::Data<Metrics>,
   }

   impl Transform<S, ServiceRequest> for MetricsMiddleware {
       // Track request timing
       // Increment counters
   }
   ```

**Deliverables**:
- ✅ Metrics collected for all endpoints
- ✅ `/metrics` endpoint returns valid Prometheus format
- ✅ Middleware automatically tracks requests
- ✅ Metrics match naming of other frameworks

**Verification**:
```bash
# Start server
# curl http://localhost:8001/metrics
# Should show:
# - actix_web_rest_requests_total
# - actix_web_rest_request_duration_seconds
# - actix_web_rest_errors_total
```

---

### Phase 5: Application Setup & Startup
**Objective**: Create main application with all components integrated

**Tasks**:
1. Create `src/main.rs`
   - Initialize tracing/logging
   - Create database pool from environment
   - Initialize metrics registry
   - Configure Actix application

2. Set up environment variables
   ```
   DATABASE_URL=postgres://benchmark:benchmark123@localhost:5434/fraiseql_benchmark
   DB_POOL_MIN=20
   DB_POOL_MAX=100
   RUST_LOG=actix_web=info,actix_web_rest=debug
   ```

3. Configure Actix app
   ```rust
   #[actix_web::main]
   async fn main() -> std::io::Result<()> {
       // Initialize logging
       tracing_subscriber::fmt().init();

       // Create database pool
       let db_pool = create_pool().await;
       let metrics = Metrics::new();

       // Start HTTP server
       HttpServer::new(move || {
           App::new()
               .app_data(web::Data::new(db_pool.clone()))
               .app_data(web::Data::new(metrics.clone()))
               .wrap(MetricsMiddleware::new())
               .service(health)
               .service(get_user)
               .service(list_users)
               .service(get_post)
               .service(list_posts)
               .route("/metrics", web::get().to(metrics_handler))
       })
       .bind("0.0.0.0:8001")?
       .run()
       .await
   }
   ```

4. Add startup logging
   - Log framework name and version
   - Log database connection pool size
   - Log listening port
   - Log Prometheus metrics endpoint

**Deliverables**:
- ✅ Server starts without errors
- ✅ Logs show configuration on startup
- ✅ Server listens on port 8001
- ✅ All endpoints respond to requests

**Verification**:
```bash
cargo build --release
./target/release/actix-web-rest
# Should log:
# "Actix-web REST server starting..."
# "Database pool initialized (20-100 connections)"
# "Listening on http://0.0.0.0:8001"

# In another terminal:
curl http://localhost:8001/health  # Should return {"status": "ok"}
```

---

### Phase 6: Docker Container
**Objective**: Create optimized Docker image for benchmarking

**Tasks**:
1. Create `Dockerfile` with multi-stage build
   ```dockerfile
   # Stage 1: Builder
   FROM rust:1.82-alpine AS builder
   RUN apk add --no-cache musl-dev postgresql-dev

   WORKDIR /app
   COPY . .
   RUN cargo build --release

   # Stage 2: Runtime
   FROM alpine:3.19
   RUN apk add --no-cache libpq

   COPY --from=builder /app/target/release/actix-web-rest /app/
   EXPOSE 8001
   CMD ["/app/actix-web-rest"]
   ```

2. Create `.dockerignore`
   ```
   target/
   .git/
   .gitignore
   Cargo.lock
   ```

3. Build and test image
   - Build image: `docker build -t fraiseql-actix-web-rest .`
   - Test image runs: `docker run --rm fraiseql-actix-web-rest /app/actix-web-rest --help`
   - Verify image size < 100MB

**Deliverables**:
- ✅ Dockerfile compiles Rust binary
- ✅ Image runs and serves requests
- ✅ Image size reasonable (< 100MB)
- ✅ Container passes health checks

**Verification**:
```bash
# Build image
docker build -t fraiseql-actix-web-rest .

# Run locally with docker-compose (temporary)
docker run -d \
  --name actix-test \
  -e DATABASE_URL="postgres://benchmark:benchmark123@host.docker.internal:5434/fraiseql_benchmark" \
  -p 8001:8001 \
  fraiseql-actix-web-rest

# Test endpoints
curl http://localhost:8001/health
docker stop actix-test
```

---

### Phase 7: Docker Compose Integration
**Objective**: Integrate into main docker-compose.yml for benchmarking

**Tasks**:
1. Add Actix-web service to `docker-compose.yml`
   ```yaml
   actix-web:
     build: ./frameworks/actix-web-rest
     ports:
       - "8001:8001"
     depends_on:
       postgres:
         condition: service_healthy
     environment:
       - DATABASE_URL=postgres://benchmark:benchmark123@postgres:5432/fraiseql_benchmark
       - DB_POOL_MIN=20
       - DB_POOL_MAX=100
       - RUST_LOG=actix_web=info
     healthcheck:
       test: ["CMD", "wget", "-q", "--spider", "http://localhost:8001/health"]
       interval: 30s
       timeout: 15s
       retries: 3
     networks:
       - fraiseql-benchmark
   ```

2. Update framework list in `tests/perf/scripts/run-test.sh`
   ```bash
   declare -A PORTS=(
     # ... existing ...
     ["actix-web"]="8001"
   )
   ```

3. Test integration
   - Start full docker-compose stack
   - Verify Actix-web service starts
   - Verify health checks pass
   - Verify metrics endpoint works

**Deliverables**:
- ✅ Service defined in docker-compose.yml
- ✅ Service starts with full stack
- ✅ Health checks pass
- ✅ Framework accessible from test scripts

**Verification**:
```bash
docker-compose up -d
sleep 30
docker-compose ps  # Should show actix-web "Up"

curl http://localhost:8001/health
curl http://localhost:8001/metrics | head -20

# Run a test
./tests/perf/scripts/run-test.sh simple actix-web smoke
```

---

### Phase 8: Performance Testing & Optimization
**Objective**: Benchmark Actix-web and optimize for throughput

**Tasks**:
1. Run smoke tests
   ```bash
   ./tests/perf/scripts/run-test.sh simple actix-web smoke
   ./tests/perf/scripts/run-test.sh simple actix-web small
   ```

2. Compare latency vs other frameworks
   - Extract p50, p95, p99 latencies
   - Compare with gqlgen (~11ms), Go (~20ms), Python (~96ms)
   - Document results

3. Profile and optimize if needed
   - Use flamegraph for CPU profiling
   - Check for allocation hotspots
   - Optimize query patterns if visible

4. Document performance characteristics
   - Expected latency range
   - Throughput ceiling
   - Resource usage

**Deliverables**:
- ✅ Smoke test results documented
- ✅ Performance compared to other frameworks
- ✅ Any performance issues identified and resolved
- ✅ Baseline latency established

**Verification**:
```bash
# Run progressive tests
./tests/perf/scripts/run-test.sh simple actix-web smoke
./tests/perf/scripts/run-test.sh simple actix-web small
./tests/perf/scripts/run-test.sh simple actix-web medium

# Check results in:
# tests/perf/results/actix-web/simple/smoke/*/html/index.html
```

---

### Phase 9: Documentation & Code Quality
**Objective**: Document implementation and ensure code quality

**Tasks**:
1. Create `frameworks/actix-web-rest/README.md`
   - Architecture overview
   - Dependencies explanation
   - Running locally
   - Performance characteristics
   - Known limitations

2. Add inline code comments
   - Explain non-obvious patterns
   - Document async/await usage
   - Explain database query strategies

3. Run Rust linting
   ```bash
   cargo fmt      # Format code
   cargo clippy   # Check for common mistakes
   cargo check    # Verify compilation
   ```

4. Add project documentation
   - Update main README.md with Actix-web section
   - Add to framework comparison table
   - Update `.phases` documentation

**Deliverables**:
- ✅ README.md complete and accurate
- ✅ Code formatted and linted
- ✅ No clippy warnings
- ✅ Main documentation updated

**Verification**:
```bash
cd frameworks/actix-web-rest
cargo fmt --check  # Should succeed
cargo clippy       # Should have no warnings
ls -la README.md   # Should exist and have content
```

---

## 🔄 Development Workflow

### Environment Setup

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup default stable

# Start PostgreSQL (if not running)
docker run -d \
  --name postgres-bench \
  -e POSTGRES_DB=fraiseql_benchmark \
  -e POSTGRES_USER=benchmark \
  -e POSTGRES_PASSWORD=benchmark123 \
  -p 5434:5432 \
  postgres:15-alpine

# Initialize database (run once)
# ... (use existing initialization scripts)
```

### Build & Test Commands

```bash
# Check compilation
cargo check

# Build debug version (fast)
cargo build

# Build release (optimized)
cargo build --release

# Run tests (if added)
cargo test

# Format code
cargo fmt

# Lint code
cargo clippy

# View documentation
cargo doc --open
```

### Running Locally

```bash
# Set environment
export DATABASE_URL="postgres://benchmark:benchmark123@localhost:5434/fraiseql_benchmark"
export RUST_LOG=debug

# Run the application
cargo run --release

# In another terminal, test endpoints:
curl http://localhost:8001/health
curl http://localhost:8001/users/$(uuidgen)
curl http://localhost:8001/metrics
```

---

## 📋 Acceptance Criteria

Each phase must meet these criteria before proceeding:

### Phase 1 ✅
- [ ] `cargo check` succeeds
- [ ] `cargo build` completes without errors
- [ ] All dependencies resolve

### Phase 2 ✅
- [ ] Models compile without errors
- [ ] Connection pool can be created
- [ ] Pool connects to real PostgreSQL
- [ ] No serialization errors

### Phase 3 ✅
- [ ] All 5 endpoints defined
- [ ] Endpoints return correct HTTP status codes
- [ ] JSON serialization works
- [ ] Error handling doesn't crash server

### Phase 4 ✅
- [ ] Metrics endpoint returns valid Prometheus format
- [ ] Request metrics are recorded
- [ ] Latency histogram has correct buckets
- [ ] Metric names match conventions

### Phase 5 ✅
- [ ] Application starts without errors
- [ ] Startup logging is informative
- [ ] All endpoints respond within 100ms
- [ ] Server gracefully handles shutdown

### Phase 6 ✅
- [ ] Docker image builds successfully
- [ ] Image runs and serves requests
- [ ] Image size < 100MB
- [ ] Container exits cleanly on SIGTERM

### Phase 7 ✅
- [ ] docker-compose up starts service
- [ ] Health checks pass
- [ ] Service accessible on correct port
- [ ] Test script recognizes framework

### Phase 8 ✅
- [ ] Smoke tests complete successfully
- [ ] Latency < 50ms (p50)
- [ ] Performance documented
- [ ] No obvious optimization opportunities

### Phase 9 ✅
- [ ] README.md is complete
- [ ] Code is formatted (cargo fmt)
- [ ] No clippy warnings
- [ ] Documentation updated

---

## 🎯 Success Metrics

After implementation, Actix-web should:

| Metric | Target | Actual |
|--------|--------|--------|
| **P50 Latency** | < 15ms | ? |
| **P99 Latency** | < 50ms | ? |
| **Throughput** | > 5000 req/s | ? |
| **Docker Image Size** | < 100MB | ? |
| **Startup Time** | < 5 seconds | ? |
| **Memory Usage** | < 100MB | ? |
| **Code Lines** | 400-600 | ? |
| **Build Time** | < 3 minutes | ? |

---

## 🚀 Next Steps

After Actix-web implementation:

1. **Implement async-graphql** (see separate phase plan)
2. **Comparative analysis** - Actix-web (REST) vs async-graphql (GraphQL)
3. **Optional: Axum framework** - Modern alternative to Actix
4. **Update benchmarking suite** - Include Rust frameworks in all comparisons

---

## 📚 References

### Actix-web Documentation
- Official Guide: https://actix.rs/
- API Docs: https://docs.rs/actix-web/
- GitHub: https://github.com/actix/actix-web

### Rust Async/PostgreSQL
- sqlx Guide: https://github.com/launchbadge/sqlx
- Tokio Guide: https://tokio.rs/
- PostgreSQL Driver: https://docs.rs/tokio-postgres/

### Performance Optimization
- Flamegraph: https://www.brendangregg.com/flamegraph.html
- Criterion.rs: https://bheisler.github.io/criterion.rs/book/

---

## 📝 Notes

### Important Implementation Details

1. **Connection Pooling**: deadpool-postgres handles connection lifetime automatically
2. **Error Handling**: Custom ApiError type implements actix-web ResponseError trait
3. **Serialization**: serde + serde_json handles all JSON conversion automatically
4. **Metrics**: Prometheus library handles metric collection and formatting
5. **Logging**: tracing is flexible and supports structured logging

### Known Challenges

1. **Rust Learning Curve**: First Rust project will take longer to understand patterns
2. **Compilation Time**: Debug builds are slow; use `cargo check` during development
3. **Async Debugging**: Async stack traces can be harder to read; use `RUST_BACKTRACE=1`
4. **SQL Compilation**: sqlx checks queries at compile time (requires offline mode if no DB)

### Performance Expectations

Based on Go (gqlgen ~11ms) and Rust's performance characteristics:
- Expected P50 latency: **8-15ms**
- Expected P99 latency: **30-50ms**
- Expected throughput: **5000-10000 req/s** per thread
- Should be 2-3x faster than Go baseline

---

## ✅ Implementation Checklist

- [ ] Phase 1: Project setup & dependencies
- [ ] Phase 2: Database & models
- [ ] Phase 3: HTTP handlers & endpoints
- [ ] Phase 4: Prometheus metrics
- [ ] Phase 5: Application setup & startup
- [ ] Phase 6: Docker container
- [ ] Phase 7: Docker Compose integration
- [ ] Phase 8: Performance testing & optimization
- [ ] Phase 9: Documentation & code quality

---

**Document Version**: 1.0
**Last Updated**: 2025-12-18
**Status**: Ready for implementation
