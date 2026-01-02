# FraiseQL Comparative Benchmarking - Quick Start

## Overview

This expanded benchmarking suite enables **apples-to-apples performance comparison** between FraiseQL and leading GraphQL frameworks, measuring performance across multiple optimization levels:

- **FastAPI/Architecture**: No N+1 queries, no ORM, Rust serialization, GraphQL Cascade
- **PostgreSQL Extensions**: jsonb_ivm (incremental views), pg_tview (table views)
- **GraphQL Engine**: Query planning, caching, execution optimization

## Quick Start

### 1. Start the Comparative Environment

```bash
# Start all services (PostgreSQL + GraphQL frameworks)
docker-compose up -d

# Wait for services to be healthy (~30 seconds)
docker-compose ps
```

### 2. Run Comparative Benchmarks

```bash
# Run the full comparative suite
python run_comparative_benchmarks.py

# Or run JMeter directly
docker run --rm --network host \
  -v $(pwd):/tests \
  -v $(pwd)/tests/perf/results:/results \
  justb4/jmeter:5.6 \
  -n -t /tests/perf/jmeter/comparative-test-plan.jmx \
  -l /results/comparative.jtl \
  -e -o /results/html/comparative
```

### 3. View Results

```bash
# Open HTML dashboard
open tests/perf/results/html/comparative/index.html

# View analysis summary
cat tests/perf/results/comparative_analysis.json
```

## Framework Comparison Matrix

| Framework | Language | Architecture | Key Features Tested |
|-----------|----------|--------------|---------------------|
| **FraiseQL** | Python | FastAPI + Rust | No N+1, Cascade mutations, Query plan cache |
| **Strawberry** | Python | FastAPI | Modern Python GraphQL, Type-safe |
| **Graphene** | Python | FastAPI | Established Python GraphQL |
| **Apollo Server** | Node.js | Express | Industry standard (future) |
| **Hasura** | Haskell | Auto-generated | PostgreSQL auto-GraphQL (future) |

## Benchmarking Dimensions

### 1. Query Performance Levels

#### Level 1: Simple Queries (Protocol Overhead)
```graphql
query { ping }
```
- **FraiseQL Advantage**: FastAPI + optimized routing

#### Level 2: Parameterized Queries (Data Access)
```graphql
query GetUser($id: ID!) { user(id: $id) { id username posts { title } } }
```
- **FraiseQL Advantage**: Single JOIN query vs N+1, jsonb_ivm views

#### Level 3: Complex Queries (Graph Traversal)
```graphql
query GetUserWithRelations($id: ID!) {
  user(id: $id) {
    posts { comments { author { posts { title } } } }
  }
}
```
- **FraiseQL Advantage**: pg_tview optimizations, query plan caching

#### Level 4: Mutations (Data Modification)
```graphql
mutation UpdateUser($id: ID!, $input: UserInput!) {
  updateUser(id: $id, input: $input) {
    id name posts { title }  # Cascade: no separate query
  }
}
```
- **FraiseQL Advantage**: GraphQL Cascade (eliminates post-mutation queries)

### 2. Execution Modes

- **Cold Start**: Empty caches, measure startup performance
- **Warm System**: Populated caches, measure steady-state
- **Hot Path**: Pre-registered operations (FraiseQL TurboRouter)

## Expected Performance Insights

### FraiseQL Optimization Impact

| Optimization | Expected Improvement | Measurement |
|--------------|---------------------|-------------|
| **No N+1 Queries** | 5-10x faster | Complex queries with relations |
| **Rust Serialization** | 2-3x faster | JSON encoding/decoding |
| **GraphQL Cascade** | 3-5x faster | Mutations with follow-up queries |
| **Query Plan Cache** | 10x+ faster | Hot path execution |
| **jsonb_ivm Views** | 2-4x faster | Incremental view maintenance |

### Comparative Benchmarks

**Simple Queries**: FraiseQL should be 2-3x faster than Python frameworks
**Complex Queries**: FraiseQL should be 5-10x faster due to PostgreSQL optimizations
**Mutations**: FraiseQL should excel with cascade patterns

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐
│   JMeter Load   │────│  Frameworks      │
│   Generator     │    │  • FraiseQL:4000 │
└─────────────────┘    │  • Strawberry:8001│
                       │  • Graphene:8002  │
┌─────────────────┐    │  • Apollo:4001    │
│  PostgreSQL     │────│  • Hasura:8080    │
│  (Shared DB)    │    └──────────────────┘
│  • jsonb_ivm    │
│  • pg_tview     │
└─────────────────┘
```

## Key Features Implemented

✅ **Shared Database**: All frameworks use identical PostgreSQL schema
✅ **Identical Schemas**: Same GraphQL operations across frameworks
✅ **Concurrent Testing**: JMeter tests all frameworks simultaneously
✅ **Statistical Rigor**: P50, P95, P99 latency measurements
✅ **Automated Analysis**: Comparative reports and insights
✅ **Container Orchestration**: Docker Compose for reproducible environment

## Next Steps

### Immediate (Week 1)
- [x] Basic framework implementations
- [x] Shared database schema
- [x] JMeter comparative test plan
- [x] Analysis and reporting

### Short Term (Week 2-3)
- [ ] Add Apollo Server (Node.js)
- [ ] Add Hasura (auto-generated)
- [ ] Implement detailed metrics collection
- [ ] Add Grafana dashboards

### Medium Term (Month 2)
- [ ] Distributed load testing
- [ ] Advanced PostgreSQL optimizations
- [ ] Performance regression tracking
- [ ] CI/CD integration

## Running Individual Frameworks

```bash
# Test FraiseQL only
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ ping }"}'

# Test Strawberry
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ ping }"}'

# Test Graphene
curl -X POST http://localhost:8002/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ ping }"}'
```

## Troubleshooting

### Services Not Starting
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs fraiseql

# Restart services
docker-compose restart
```

### Database Connection Issues
```bash
# Connect to database
docker-compose exec postgres psql -U benchmark -d fraiseql_benchmark

# Check data
SELECT COUNT(*) FROM benchmark.users;
```

### JMeter Issues
```bash
# Run JMeter GUI for debugging
docker run --rm -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd):/tests \
  justb4/jmeter:5.6 \
  -t /tests/perf/jmeter/comparative-test-plan.jmx
```

## Performance Expectations

**Development Environment** (local machine):
- Simple queries: < 5ms average
- Complex queries: < 50ms average
- Throughput: 1000-5000 RPS depending on framework

**Production Environment** (optimized hardware):
- Simple queries: < 1ms average
- Complex queries: < 10ms average
- Throughput: 10000+ RPS for FraiseQL

This comparative benchmarking suite provides the foundation for demonstrating FraiseQL's performance advantages across multiple optimization dimensions.