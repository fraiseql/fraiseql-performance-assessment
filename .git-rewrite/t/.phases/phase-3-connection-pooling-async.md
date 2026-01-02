# Phase 3: Connection Pooling & Async Database Access

## Objective

Upgrade all framework implementations to use production-grade async connection pooling, ensuring each framework operates at its maximum potential rather than being bottlenecked by synchronous single-connection database access.

## Context

**Current State:**
- All Python frameworks use synchronous `psycopg2` with single connection
- No connection pooling configured
- FastAPI (async framework) blocked by sync database calls
- FraiseQL's async potential unrealized

**Target State:**
- Python frameworks use `asyncpg` with connection pools
- FraiseQL demonstrates true async CQRS performance
- Connection pool sizes tuned per framework
- Comparison between sync vs async variants

## Files to Modify

| File | Action | Purpose |
|------|--------|---------|
| `frameworks/fraiseql/main.py` | Major refactor | asyncpg + pool |
| `frameworks/strawberry/main.py` | Major refactor | asyncpg + pool |
| `frameworks/graphene/main.py` | Major refactor | asyncpg + pool |
| `frameworks/fastapi-rest/main.py` | Major refactor | asyncpg + pool |
| `frameworks/flask-rest/main.py` | Enhance | psycopg pool (sync) |
| `frameworks/*/requirements.txt` | Update | Add asyncpg dependency |
| `docker-compose.yml` | Update | Add PgBouncer service (optional) |

## Implementation Steps

### Step 1: Create Async Database Module

```python
# frameworks/common/async_db.py
import asyncpg
from typing import List, Dict, Any, Optional
import os

class AsyncDatabase:
    """Shared async database pool for Python frameworks"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, min_size: int = 10, max_size: int = 50):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "fraiseql_benchmark"),
            user=os.getenv("DB_USER", "benchmark"),
            password=os.getenv("DB_PASSWORD", "benchmark123"),
            min_size=min_size,
            max_size=max_size,
            command_timeout=30,
            # Performance tuning
            statement_cache_size=100,
            max_cached_statement_lifetime=300,
        )

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and return single row"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def execute(self, query: str, *args) -> str:
        """Execute query without returning results"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
```

### Step 2: Refactor FraiseQL to Full Async

```python
# frameworks/fraiseql/main.py - Key changes
from frameworks.common.async_db import AsyncDatabase

class FraiseQLApp:
    def __init__(self):
        self.app = FastAPI(title="FraiseQL Async Benchmark")
        self.db = AsyncDatabase()

    async def startup(self):
        await self.db.connect(min_size=20, max_size=100)

    async def shutdown(self):
        await self.db.close()

# GraphQL resolvers become async
class Query(ObjectType):
    @staticmethod
    async def resolve_user(root, info, id):
        db = info.context["db"]
        result = await db.fetchrow(
            """
            SELECT u.id, u.username, u.first_name, u.last_name, u.bio,
                   COALESCE(json_agg(json_build_object('id', p.id, 'title', p.title))
                            FILTER (WHERE p.id IS NOT NULL), '[]') as posts
            FROM benchmark.users u
            LEFT JOIN benchmark.posts p ON u.id = p.author_id AND p.status = 'published'
            WHERE u.id = $1
            GROUP BY u.id
            """,
            id,
        )
        if not result:
            return None
        return User(**result)
```

### Step 3: Refactor Strawberry to Async

```python
# frameworks/strawberry/main.py - Key changes
import strawberry
from strawberry.fastapi import GraphQLRouter
from frameworks.common.async_db import AsyncDatabase

@strawberry.type
class User:
    id: str
    username: str
    first_name: str | None
    last_name: str | None
    bio: str | None

    @strawberry.field
    async def posts(self, info, limit: int = 10) -> list["Post"]:
        db = info.context["db"]
        rows = await db.fetch(
            "SELECT id, title, content FROM benchmark.posts WHERE author_id = $1 LIMIT $2",
            self.id, limit
        )
        return [Post(**row) for row in rows]

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, info, id: str) -> User | None:
        db = info.context["db"]
        row = await db.fetchrow(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
            id
        )
        return User(**row) if row else None
```

### Step 4: Refactor FastAPI REST to Async

```python
# frameworks/fastapi-rest/main.py - Key changes
from frameworks.common.async_db import AsyncDatabase

db = AsyncDatabase()

@app.on_event("startup")
async def startup():
    await db.connect(min_size=20, max_size=100)

@app.on_event("shutdown")
async def shutdown():
    await db.close()

@app.get("/users/{user_id}")
async def get_user(user_id: str, include: str = ""):
    user = await db.fetchrow(
        "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
        user_id
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = dict(user)

    if "posts" in include:
        posts = await db.fetch(
            "SELECT id, title, content FROM benchmark.posts WHERE author_id = $1",
            user_id
        )
        result["posts"] = posts

    return result
```

### Step 5: Enhance Flask REST with Sync Pool

Flask remains synchronous but benefits from connection pooling:

```python
# frameworks/flask-rest/main.py - Key changes
from psycopg_pool import ConnectionPool  # psycopg3 pool

pool = ConnectionPool(
    conninfo=f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}",
    min_size=10,
    max_size=50,
    open=True,
)

def get_db():
    return pool.getconn()

def release_db(conn):
    pool.putconn(conn)

@app.route("/users/<user_id>")
def get_user(user_id):
    conn = get_db()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM benchmark.users WHERE id = %s", (user_id,))
            user = cur.fetchone()
        return jsonify(user) if user else ({"error": "not found"}, 404)
    finally:
        release_db(conn)
```

### Step 6: Add PgBouncer Service (Optional)

```yaml
# docker-compose.yml addition
pgbouncer:
  image: edoburu/pgbouncer:1.21.0
  environment:
    DATABASE_URL: postgres://benchmark:benchmark123@postgres:5432/fraiseql_benchmark
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 1000
    DEFAULT_POOL_SIZE: 50
  ports:
    - "6432:5432"
  depends_on:
    - postgres
```

### Step 7: Connection Pool Configuration Matrix

```yaml
# config/pool_settings.yaml
frameworks:
  fraiseql:
    min_connections: 20
    max_connections: 100
    statement_cache_size: 200
    rationale: "High read throughput, TV table queries benefit from prepared statements"

  strawberry:
    min_connections: 10
    max_connections: 50
    statement_cache_size: 100
    rationale: "N+1 pattern means more varied queries, smaller cache"

  graphene:
    min_connections: 10
    max_connections: 50
    statement_cache_size: 100
    rationale: "Similar to Strawberry patterns"

  fastapi-rest:
    min_connections: 20
    max_connections: 100
    statement_cache_size: 50
    rationale: "Include pattern reduces query variation"

  flask-rest:
    min_connections: 10
    max_connections: 50
    statement_cache_size: 0
    rationale: "Sync pool, varied endpoint queries"
```

## Verification Commands

```bash
# Test async connection pool is working
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user(id: \"11111111-1111-1111-1111-111111111111\") { id username posts { id } } }"}'

# Verify pool statistics (add metrics endpoint)
curl http://localhost:4000/metrics | grep pool

# Expected metrics:
# fraiseql_pool_size 50
# fraiseql_pool_free 45
# fraiseql_pool_used 5

# Load test to verify pool handles concurrency
ab -n 1000 -c 100 -p query.json -T application/json http://localhost:4000/graphql
```

## Acceptance Criteria

- [ ] All async-capable frameworks (FraiseQL, Strawberry, FastAPI) use asyncpg
- [ ] Connection pools configured with min 10, max 50+ connections
- [ ] Flask uses psycopg3 sync pool (not psycopg2)
- [ ] Pool metrics exposed via /metrics endpoint
- [ ] No "connection exhausted" errors under 100 concurrent users
- [ ] Statement caching enabled for repeated queries
- [ ] Graceful pool shutdown on container stop

## DO NOT

- Use psycopg2 for async frameworks (blocks event loop)
- Create new connections per request (defeats pooling)
- Set pool max_size below expected concurrent users
- Forget to close pools on shutdown (connection leaks)
- Mix sync and async database calls in same framework

## Dependencies

```txt
# requirements.txt additions
asyncpg>=0.29.0
psycopg[binary,pool]>=3.1.0  # psycopg3 with pool support
```

## Performance Expectations

| Framework | Current (sync, no pool) | Target (async + pool) | Expected Improvement |
|-----------|------------------------|----------------------|---------------------|
| FraiseQL | ~50 RPS | ~500+ RPS | 10x |
| Strawberry | ~30 RPS | ~200+ RPS | 6x |
| FastAPI REST | ~40 RPS | ~400+ RPS | 10x |
| Flask REST | ~30 RPS | ~100+ RPS | 3x (sync limited) |

## Estimated Complexity

**High** - Requires refactoring all database access patterns from sync to async, plus careful pool configuration tuning.
