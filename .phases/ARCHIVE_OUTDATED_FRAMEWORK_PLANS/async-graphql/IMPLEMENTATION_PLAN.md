# async-graphql GraphQL Framework Implementation Plan

## 📋 Overview

Implement a high-performance GraphQL API in Rust using **async-graphql** framework to provide a compiled language baseline for GraphQL benchmarking. This complements the Actix-web REST implementation and enables direct comparison between REST vs GraphQL in a compiled language context.

---

## 🎯 Objectives

1. **Implement async-graphql GraphQL API** matching the existing 7 GraphQL endpoints
2. **Achieve sub-25ms latency** to establish compiled language GraphQL baseline
3. **Support all workload patterns** (simple, parameterized, aggregation, deep-traversal)
4. **Implement DataLoader pattern** for N+1 prevention in GraphQL context
5. **Provide Docker deployment** matching other frameworks
6. **Compare REST vs GraphQL** performance in compiled language

---

## 📊 Scope

### What's Included

- ✅ Full GraphQL schema (Query root with 7 fields)
- ✅ PostgreSQL connection pooling (deadpool-postgres)
- ✅ N+1 prevention via DataLoader pattern
- ✅ Batch loading for relationships
- ✅ Prometheus metrics (custom implementation)
- ✅ Health checks and server health endpoint
- ✅ Docker container with alpine base
- ✅ Integration with Actix-web as HTTP server

### What's NOT Included

- ❌ Mutations (focused on read performance)
- ❌ Subscriptions
- ❌ Custom directives
- ❌ Federation
- ❌ ORM variant (initial release uses raw SQL with sqlx)

---

## 🏗️ Architecture

### Directory Structure

```
frameworks/async-graphql/
├── Cargo.toml                 # Rust dependencies
├── src/
│   ├── main.rs               # Application entry point
│   ├── schema.rs             # GraphQL schema definition
│   ├── models.rs             # Data models (User, Post, Comment)
│   ├── resolvers.rs          # GraphQL field resolvers
│   ├── db.rs                 # Database initialization & pool
│   ├── dataloaders.rs        # N+1 prevention with DataLoader
│   ├── metrics.rs            # Prometheus metrics setup
│   └── error.rs              # Error handling utilities
├── Dockerfile                # Multi-stage build
└── .dockerignore
```

### Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Framework** | Actix-web | 4.x | HTTP server |
| **GraphQL** | async-graphql | 0.15.x | Modern Rust GraphQL |
| **Async Runtime** | Tokio | 1.x | Industry standard |
| **Database Driver** | sqlx | 0.7.x | Compile-time verification |
| **Connection Pool** | deadpool-postgres | 0.14.x | Efficient pooling |
| **DataLoader** | async-graphql built-in | 0.15.x | N+1 prevention |
| **JSON** | serde_json | 1.x | Serialization |
| **Metrics** | prometheus | 0.13.x | Monitoring |
| **Base Image** | rust:1.82-alpine | Latest | Small, production |

### GraphQL Schema

```graphql
type User {
  id: ID!
  username: String!
  firstName: String!
  lastName: String!
  bio: String
  posts: [Post!]!
  comments: [Comment!]!
}

type Post {
  id: ID!
  title: String!
  content: String
  author: User!
  comments: [Comment!]!
  createdAt: DateTime!
}

type Comment {
  id: ID!
  content: String!
  post: Post!
  author: User!
  createdAt: DateTime!
}

type Query {
  user(id: ID!): User
  users(limit: Int = 10, offset: Int = 0): [User!]!
  post(id: ID!): Post
  posts(limit: Int = 10, offset: Int = 0): [Post!]!
  postsByUser(userId: ID!, limit: Int = 10): [Post!]!
  commentsByPost(postId: ID!, limit: Int = 50): [Comment!]!
  postsWithComments(limit: Int = 10, offset: Int = 0): [Post!]!
}
```

---

## 📝 Implementation Phases

### Phase 1: Project Setup & Dependencies
**Objective**: Create Rust project with async-graphql dependencies

**Tasks**:
1. Initialize Cargo project
   ```bash
   cargo new frameworks/async-graphql
   ```

2. Add dependencies to `Cargo.toml`
   ```toml
   [dependencies]
   actix-web = "4.4"
   async-graphql = "0.15"
   async-graphql-actix-web = "0.15"
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
   futures = "0.3"
   ```

3. Verify compilation
   ```bash
   cargo check
   ```

**Deliverables**:
- ✅ Working `cargo build` command
- ✅ All async-graphql dependencies available
- ✅ Basic project structure created

**Verification**:
```bash
cd frameworks/async-graphql
cargo check   # Should succeed
```

---

### Phase 2: Database Connection & Models
**Objective**: Set up PostgreSQL and data model structures

**Tasks**:
1. Create `src/models.rs` with data structures
   - User, Post, Comment structs
   - Implement async_graphql::Object derive
   - Define GraphQL field mappings
   - Implement resolvers for relationships

2. Create `src/db.rs` for connection management
   - Initialize deadpool-postgres pool
   - Implement connection acquisition
   - Set pool size from environment

3. Example model implementation:
   ```rust
   use async_graphql::*;

   #[Object]
   impl User {
       async fn id(&self) -> ID {
           ID::from(self.id.clone())
       }

       async fn username(&self) -> &str {
           &self.username
       }

       async fn first_name(&self) -> &str {
           &self.first_name
       }

       async fn last_name(&self) -> &str {
           &self.last_name
       }

       async fn bio(&self) -> Option<&str> {
           self.bio.as_deref()
       }

       async fn posts(
           &self,
           ctx: &Context<'_>,
       ) -> Result<Vec<Post>> {
           // Uses DataLoader to batch load posts
           let loader = ctx.data::<DataLoader<PostLoader>>()?;
           loader.load_one(self.id.clone()).await
       }
   }
   ```

**Deliverables**:
- ✅ All models defined and compile
- ✅ GraphQL Object derives work
- ✅ Connection pool functional
- ✅ Pool connects to PostgreSQL

**Verification**:
```bash
cargo build
```

---

### Phase 3: GraphQL Schema & Query Root
**Objective**: Define GraphQL schema and root query resolvers

**Tasks**:
1. Create `src/schema.rs` with root Query type
   ```rust
   pub struct Query;

   #[Object]
   impl Query {
       async fn user(
           &self,
           id: ID,
           ctx: &Context<'_>,
       ) -> Result<Option<User>> {
           // Query user by ID
       }

       async fn users(
           &self,
           limit: Option<i32>,
           offset: Option<i32>,
           ctx: &Context<'_>,
       ) -> Result<Vec<User>> {
           // Query multiple users with pagination
       }

       async fn post(
           &self,
           id: ID,
           ctx: &Context<'_>,
       ) -> Result<Option<Post>> {
           // Query post by ID
       }

       async fn posts(
           &self,
           limit: Option<i32>,
           offset: Option<i32>,
           ctx: &Context<'_>,
       ) -> Result<Vec<Post>> {
           // Query multiple posts
       }

       async fn posts_by_user(
           &self,
           user_id: ID,
           limit: Option<i32>,
           ctx: &Context<'_>,
       ) -> Result<Vec<Post>> {
           // Get posts for a user
       }

       async fn comments_by_post(
           &self,
           post_id: ID,
           limit: Option<i32>,
           ctx: &Context<'_>,
       ) -> Result<Vec<Comment>> {
           // Get comments for a post
       }

       async fn posts_with_comments(
           &self,
           limit: Option<i32>,
           offset: Option<i32>,
           ctx: &Context<'_>,
       ) -> Result<Vec<Post>> {
           // Get posts with comments eager-loaded
       }
   }
   ```

2. Implement each resolver
   - Query database directly
   - Return Result<Option<T>> or Result<Vec<T>>
   - Handle errors appropriately

3. Test schema compiles
   ```bash
   cargo build
   ```

**Deliverables**:
- ✅ All 7 Query fields defined
- ✅ Resolvers compile
- ✅ Schema can be introspected

**Verification**:
```bash
cargo build
# Later: schema introspection query works
```

---

### Phase 4: DataLoader for N+1 Prevention
**Objective**: Implement batch loading pattern for relationships

**Tasks**:
1. Create `src/dataloaders.rs`
   - Implement PostLoader for batch loading posts by author
   - Implement CommentLoader for batch loading comments
   - Implement UserLoader for batch loading users by ID

2. Example DataLoader implementation:
   ```rust
   use async_graphql::dataloader::*;
   use std::collections::HashMap;

   pub struct PostLoader {
       pool: deadpool_postgres::Pool,
   }

   #[async_trait::async_trait]
   impl Loader<String> for PostLoader {
       type Value = Vec<Post>;
       type Error = String;

       async fn load(
           &self,
           keys: Vec<String>,
       ) -> Result<HashMap<String, Self::Value>, Self::Error> {
           // Batch load posts for multiple user IDs
           let client = self.pool.get().await
               .map_err(|e| e.to_string())?;

           let placeholders = (1..=keys.len())
               .map(|i| format!("${}", i))
               .collect::<Vec<_>>()
               .join(",");

           let query = format!(
               "SELECT * FROM benchmark.tb_post WHERE author_id IN ({})",
               placeholders
           );

           let rows = client.query(&query, /* params */).await
               .map_err(|e| e.to_string())?;

           let mut map = HashMap::new();
           for row in rows {
               let post = Post::from_row(&row);
               map.entry(post.author_id.clone())
                   .or_insert_with(Vec::new)
                   .push(post);
           }

           Ok(map)
       }
   }
   ```

3. Register DataLoaders in schema context
   ```rust
   let schema = Schema::build(Query, EmptyMutation, EmptySubscription)
       .data(DataLoader::new(PostLoader { pool: pool.clone() }, Default::default()))
       .data(DataLoader::new(CommentLoader { pool: pool.clone() }, Default::default()))
       .data(DataLoader::new(UserLoader { pool: pool.clone() }, Default::default()))
       .finish();
   ```

4. Update resolvers to use DataLoaders
   - User.posts -> uses PostLoader
   - Post.comments -> uses CommentLoader
   - Comment.author -> uses UserLoader

**Deliverables**:
- ✅ All DataLoaders implemented
- ✅ Batch loading reduces query count
- ✅ No N+1 queries for relationships

**Verification**:
```bash
# Log SQL queries to verify batch loading
# One query per batch, not per item
```

---

### Phase 5: Metrics & Monitoring
**Objective**: Add Prometheus metrics collection

**Tasks**:
1. Create `src/metrics.rs`
   - Track GraphQL queries total
   - Track query latency histogram
   - Track field resolution latency

2. Implement GraphQL middleware for metrics
   ```rust
   pub struct MetricsExtension {
       metrics: Arc<Metrics>,
   }

   #[async_trait::async_trait]
   impl Extension for MetricsExtension {
       async fn execute_start(&mut self, info: &ExtensionInfo) {
           // Record start time
       }

       async fn execute_end(&mut self, info: &ExtensionInfo) {
           // Record end time
           // Update latency histogram
       }
   }
   ```

3. Create `/metrics` endpoint
   - Expose Prometheus metrics in text format
   - Include: query count, latency histogram, field resolution times

**Deliverables**:
- ✅ Metrics collected for GraphQL operations
- ✅ `/metrics` endpoint functional
- ✅ Naming matches other frameworks

**Verification**:
```bash
curl http://localhost:8002/metrics | grep async_graphql
```

---

### Phase 6: HTTP Server & GraphQL Endpoint
**Objective**: Set up Actix-web server with GraphQL endpoint

**Tasks**:
1. Create `src/main.rs`
   - Initialize logging
   - Create database pool
   - Build async-graphql Schema
   - Set up Actix-web server

2. Define GraphQL endpoint
   ```rust
   #[post("/graphql")]
   async fn graphql_endpoint(
       schema: web::Data<Schema>,
       req: GraphQLRequest,
   ) -> GraphQLResponse {
       schema.execute(req.into_inner()).await.into()
   }
   ```

3. Define GraphQL Playground (development)
   ```rust
   #[get("/graphql")]
   async fn graphql_playground() -> impl Responder {
       HttpResponse::Ok()
           .content_type("text/html; charset=utf-8")
           .body(playground_source(GraphQLPlaygroundConfig::new("/graphql")))
   }
   ```

4. Server configuration
   ```rust
   #[actix_web::main]
   async fn main() -> std::io::Result<()> {
       // Initialize logging
       tracing_subscriber::fmt().init();

       // Create database pool
       let pool = create_pool().await;

       // Build GraphQL schema
       let schema = Schema::build(Query, EmptyMutation, EmptySubscription)
           .data(pool.clone())
           .data(DataLoader::new(PostLoader { pool: pool.clone() }, Default::default()))
           .finish();

       // Start HTTP server
       HttpServer::new(move || {
           App::new()
               .app_data(web::Data::new(schema.clone()))
               .service(graphql_endpoint)
               .service(graphql_playground)
               .route("/health", web::get().to(health_handler))
               .route("/metrics", web::get().to(metrics_handler))
       })
       .bind("0.0.0.0:8002")?
       .run()
       .await
   }
   ```

**Deliverables**:
- ✅ Server starts on port 8002
- ✅ `/graphql` endpoint accepts GraphQL queries
- ✅ `/graphql` GET returns Playground
- ✅ Health checks functional

**Verification**:
```bash
cargo run --release

# In another terminal:
# Test health
curl http://localhost:8002/health

# Test GraphQL query (using playground or curl)
curl -X POST http://localhost:8002/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users(limit: 1) { id username } }"}'
```

---

### Phase 7: Error Handling & Edge Cases
**Objective**: Implement robust error handling

**Tasks**:
1. Create `src/error.rs`
   - Define custom error types
   - Implement async_graphql::Error conversion
   - Handle database errors gracefully

2. Handle common errors:
   - Resource not found (404)
   - Invalid input (400)
   - Database connection errors (500)
   - Query timeout (408)

3. Test error cases
   - Invalid IDs
   - Malformed queries
   - Database disconnections

**Deliverables**:
- ✅ All errors return proper HTTP status codes
- ✅ GraphQL errors include useful messages
- ✅ No unhandled panics

**Verification**:
```bash
# Test with invalid ID
curl -X POST http://localhost:8002/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user(id: \"invalid\") { id } }"}'
```

---

### Phase 8: Docker Container
**Objective**: Create optimized Docker image

**Tasks**:
1. Create multi-stage Dockerfile
   ```dockerfile
   FROM rust:1.82-alpine AS builder
   RUN apk add --no-cache musl-dev postgresql-dev
   WORKDIR /app
   COPY . .
   RUN cargo build --release

   FROM alpine:3.19
   RUN apk add --no-cache libpq
   COPY --from=builder /app/target/release/async-graphql /app/
   EXPOSE 8002
   CMD ["/app/async-graphql"]
   ```

2. Build and test
   - Image size < 100MB
   - Runs without errors
   - Serves requests correctly

**Deliverables**:
- ✅ Docker image builds
- ✅ Image runs correctly
- ✅ Reasonable image size

**Verification**:
```bash
docker build -t fraiseql-async-graphql .
docker run -d --name graphql-test fraiseql-async-graphql
curl http://localhost:8002/health
docker stop graphql-test
```

---

### Phase 9: Docker Compose Integration
**Objective**: Integrate into main benchmarking suite

**Tasks**:
1. Add to docker-compose.yml
   ```yaml
   async-graphql:
     build: ./frameworks/async-graphql
     ports:
       - "8002:8002"
     depends_on:
       postgres:
         condition: service_healthy
     environment:
       - DATABASE_URL=postgres://benchmark:benchmark123@postgres:5432/fraiseql_benchmark
       - DB_POOL_MIN=20
       - DB_POOL_MAX=100
       - RUST_LOG=actix_web=info
     healthcheck:
       test: ["CMD", "wget", "-q", "--spider", "http://localhost:8002/health"]
       interval: 30s
       timeout: 15s
       retries: 3
     networks:
       - fraiseql-benchmark
   ```

2. Update test scripts
   - Add to framework list
   - Add port mapping (8002)

3. Test integration
   - docker-compose up works
   - Service starts and becomes healthy
   - Tests can connect and query

**Deliverables**:
- ✅ Service in docker-compose.yml
- ✅ Service starts with stack
- ✅ Health checks pass
- ✅ Accessible from tests

**Verification**:
```bash
docker-compose up -d
sleep 30
docker-compose ps | grep async-graphql
# Should show "Up (healthy)"

curl http://localhost:8002/health
```

---

### Phase 10: Benchmark Testing & Analysis
**Objective**: Run benchmarks and establish performance baseline

**Tasks**:
1. Create JMeter test plan for GraphQL
   - Use same workloads as other frameworks
   - Issue GraphQL queries (not REST)
   - Track latency and throughput

2. Run smoke tests
   ```bash
   ./tests/perf/scripts/run-test.sh simple async-graphql smoke
   ./tests/perf/scripts/run-test.sh simple async-graphql small
   ```

3. Compare performance
   - Latency: async-graphql vs Strawberry (GraphQL)
   - Latency: async-graphql vs Actix-web (REST)
   - Expected: async-graphql faster than Strawberry (2-3x)

4. Document results
   - Expected latency range
   - Throughput characteristics
   - GraphQL vs REST comparison

**Deliverables**:
- ✅ Smoke test results
- ✅ Performance compared to other frameworks
- ✅ GraphQL vs REST analysis
- ✅ Baseline established

**Verification**:
```bash
# Run test
./tests/perf/scripts/run-test.sh simple async-graphql smoke

# Check results
ls tests/perf/results/async-graphql/simple/smoke/*/html/index.html
# Open in browser to see metrics
```

---

### Phase 11: Documentation & Code Quality
**Objective**: Document and finalize implementation

**Tasks**:
1. Create `frameworks/async-graphql/README.md`
   - Architecture overview
   - DataLoader explanation
   - GraphQL schema documentation
   - Performance characteristics
   - Known limitations

2. Add code documentation
   - Explain async-graphql patterns
   - Document DataLoader usage
   - Explain resolver implementation

3. Run Rust quality checks
   ```bash
   cargo fmt      # Format
   cargo clippy   # Lint
   cargo check    # Verify
   ```

4. Update main documentation
   - Add async-graphql to README
   - Update framework comparison table
   - Add to Rust frameworks section

**Deliverables**:
- ✅ README.md complete
- ✅ Code well-formatted
- ✅ No clippy warnings
- ✅ Documentation updated

**Verification**:
```bash
cd frameworks/async-graphql
cargo fmt --check
cargo clippy
ls README.md
```

---

## 🔄 Development Workflow

### Quick Start

```bash
# Setup environment
export DATABASE_URL="postgres://benchmark:benchmark123@localhost:5434/fraiseql_benchmark"
export RUST_LOG=debug

# Build
cargo build --release

# Run locally
cargo run --release

# In another terminal:
# Test query
curl -X POST http://localhost:8002/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ users(limit: 5) { id username firstName } }"
  }'

# Visit GraphQL Playground
# http://localhost:8002/graphql
```

### Development Commands

```bash
cargo check          # Quick compilation check
cargo build          # Debug build
cargo build --release # Optimized build
cargo fmt            # Format code
cargo clippy         # Lint check
cargo test           # Run tests
cargo doc --open     # View documentation
```

---

## 📋 Acceptance Criteria

### Per Phase

#### Phase 1 ✅
- [ ] `cargo check` succeeds
- [ ] All dependencies resolve

#### Phase 2 ✅
- [ ] Models compile
- [ ] Connection pool works
- [ ] Connects to PostgreSQL

#### Phase 3 ✅
- [ ] All Query fields defined
- [ ] Schema compiles
- [ ] Introspection works

#### Phase 4 ✅
- [ ] DataLoaders batch correctly
- [ ] No N+1 queries
- [ ] Relationships resolve

#### Phase 5 ✅
- [ ] Metrics endpoint works
- [ ] Prometheus format valid
- [ ] Metrics named consistently

#### Phase 6 ✅
- [ ] Server starts
- [ ] GraphQL endpoint responds
- [ ] Playground accessible

#### Phase 7 ✅
- [ ] docker-compose up works
- [ ] Service healthy
- [ ] Tests can query

#### Phase 8 ✅
- [ ] Docker image builds
- [ ] Image < 100MB
- [ ] Container runs

#### Phase 9 ✅
- [ ] Service in docker-compose
- [ ] Health checks pass
- [ ] Accessible on port 8002

#### Phase 10 ✅
- [ ] Smoke tests pass
- [ ] Latency < 50ms p50
- [ ] Results documented

#### Phase 11 ✅
- [ ] README complete
- [ ] Code formatted
- [ ] No clippy warnings
- [ ] Documentation updated

---

## 🎯 Performance Targets

| Metric | Target | vs Strawberry |
|--------|--------|---------------|
| **P50 Latency** | < 20ms | 5x faster |
| **P99 Latency** | < 60ms | 3x faster |
| **Throughput** | > 3000 req/s | 5x faster |
| **Latency Consistency** | Low stddev | Better than interpreted |

---

## 🚀 Integration Points

### REST vs GraphQL Comparison

After both Actix-web and async-graphql are implemented:

1. **Performance Comparison**
   - Same query patterns in both REST and GraphQL
   - Measure overhead of GraphQL vs REST
   - Measure compiled (Rust) vs interpreted (Python)

2. **Updated README**
   - Rust frameworks section
   - Performance envelope table
   - Language comparison analysis

3. **Test Suite Updates**
   - Include Rust frameworks in all comparisons
   - Create Rust-specific workloads if needed

---

## 📚 References

### async-graphql Resources
- Official Repo: https://github.com/async-graphql/async-graphql
- Book: https://async-graphql.rs/
- Examples: https://github.com/async-graphql/async-graphql/tree/master/examples

### DataLoader Pattern
- Original DataLoader (JavaScript): https://github.com/graphql/dataloader
- Batch Loading: https://en.wikipedia.org/wiki/Batch_processing

### Performance References
- Flamegraph: https://www.brendangregg.com/flamegraph.html
- Profiling: https://docs.rust-embedded.org/book/c-tips/index.html

---

## 📝 Notes

### Implementation Challenges

1. **Lifetime Management**: Rust's borrow checker requires careful design
2. **Error Handling**: Converting sqlx errors to GraphQL errors
3. **Async Debugging**: Difficult stack traces in async code
4. **Query Optimization**: sqlx requires compile-time verification

### Performance Expectations

Based on async-graphql benchmarks and Rust performance:
- Expected P50: **12-20ms** (3-5x faster than Strawberry)
- Expected P99: **40-60ms** (2-3x faster than Strawberry)
- Expected throughput: **3000-5000 req/s** per thread
- Lower GC impact than Python

### Known Limitations

1. **No mutations** (v1 focused on read performance)
2. **No subscriptions** (WebSocket support not included)
3. **Compile time**: Rust compilation slower than Python
4. **Learning curve**: async-graphql patterns can be challenging

---

## ✅ Implementation Checklist

- [ ] Phase 1: Project setup & dependencies
- [ ] Phase 2: Database & models
- [ ] Phase 3: GraphQL schema & queries
- [ ] Phase 4: DataLoader for N+1 prevention
- [ ] Phase 5: Metrics & monitoring
- [ ] Phase 6: HTTP server & GraphQL endpoint
- [ ] Phase 7: Error handling & edge cases
- [ ] Phase 8: Docker container
- [ ] Phase 9: Docker Compose integration
- [ ] Phase 10: Benchmark testing & analysis
- [ ] Phase 11: Documentation & code quality

---

**Document Version**: 1.0
**Last Updated**: 2025-12-18
**Status**: Ready for implementation
