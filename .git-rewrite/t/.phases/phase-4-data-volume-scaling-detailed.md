# FraiseQL Performance Assessment - Phase 4: Data Volume Scaling

## Phase Overview

**Goal**: Scale the benchmark database from ~100-500 records to production-realistic volumes (10K+ users, 100K+ posts, 500K+ comments) to properly stress database indexes, memory pressure, and query optimization differences between frameworks.

**Scope**: Implement large dataset generation, index optimization, and data seeding infrastructure for realistic performance testing.

**Context**: Small datasets fit entirely in PostgreSQL buffer cache, preventing proper evaluation of index performance, memory pressure, and query optimization. This phase creates production-scale data volumes.

**Success Criteria**:
- Large dataset contains 10K+ users, 100K+ posts, 500K+ comments
- Data generation is reproducible (same seed = same data)
- TV tables automatically synced after generation
- JMeter datasets generated from actual data
- Indexes used for common query patterns
- Database size > 200MB for large dataset

## Learning Objectives

As a junior engineer, by completing Phase 4 you will learn:

1. **Async/Await Patterns**: Python async programming, event loops, coroutines
2. **Database Connection Pooling**: Pool sizing, lifecycle management, monitoring
3. **asyncpg vs psycopg2**: Async driver capabilities, performance characteristics
4. **Framework Integration**: Adapting sync frameworks to async patterns
5. **Resource Management**: Connection lifecycle, pool tuning, resource limits
6. **Performance Optimization**: Statement caching, prepared statements, batch operations
7. **Production Patterns**: Graceful shutdown, health checks, metrics collection
8. **Debugging Async Code**: Event loop debugging, task management, error handling

## Prerequisites and Knowledge Requirements

### Required Knowledge
- Basic Python async/await syntax
- Database connection concepts
- Basic SQL query optimization
- HTTP request/response lifecycle
- Basic Docker container concepts

### Required Tools
- Python 3.8+ with asyncpg, psycopg packages
- PostgreSQL running (from Phase 1)
- curl for API testing
- Docker/Podman for container management

### Environment Setup
```bash
# Verify async capabilities
python3 -c "import asyncio; print('Async support OK')"

# Check asyncpg installation
python3 -c "import asyncpg; print('asyncpg version:', asyncpg.__version__)"

# Verify PostgreSQL async support
python3 -c "import asyncpg; print('PostgreSQL async ready')"
```

## Implementation Steps

### Step 1: Async Database Module Creation
**Estimated Time**: 1 hour

**Learning Objective**: Building reusable async database abstractions

**What you'll learn**:
- Async context managers and connection handling
- Database connection pool configuration
- Query execution patterns (fetch, fetchrow, execute)
- Error handling in async contexts

```python
# frameworks/common/async_db.py
"""
Shared async database module for all Python frameworks.
Provides connection pooling, query execution, and metrics.
"""

import asyncpg
import os
import time
import logging
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PoolMetrics:
    """Connection pool metrics for monitoring"""
    pool_size: int
    pool_free: int
    pool_used: int
    pool_waiting: int
    pool_max: int

class AsyncDatabase:
    """
    Production-ready async database pool with monitoring and metrics.
    
    Key features:
    - Connection pooling with configurable min/max
    - Statement caching for performance
    - Automatic reconnection on failures
    - Comprehensive metrics collection
    - Graceful shutdown handling
    """
    
    def __init__(
        self, 
        min_size: int = 10, 
        max_size: int = 50,
        statement_cache_size: int = 100,
        health_check_interval: int = 30
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.statement_cache_size = statement_cache_size
        self.health_check_interval = health_check_interval
        
        self.pool: Optional[asyncpg.Pool] = None
        self._pool_created_at: Optional[float] = None
        
        # Metrics tracking
        self._query_count = 0
        self._error_count = 0
        self._connection_acquire_time = 0.0
        self._connection_acquire_count = 0
    
    async def connect(self) -> None:
        """
        Initialize the connection pool.
        
        Connection string uses environment variables for flexibility:
        - DB_HOST: Database hostname
        - DB_PORT: Database port
        - DB_NAME: Database name
        - DB_USER: Database username
        - DB_PASSWORD: Database password
        """
        conn_str = (
            f"postgresql://{os.getenv('DB_USER', 'benchmark')}:"
            f"{os.getenv('DB_PASSWORD', 'benchmark123')}@"
            f"{os.getenv('DB_HOST', 'postgres')}:"
            f"{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'fraiseql_benchmark')}"
        )
        
        logger.info(f"Creating asyncpg pool: min={self.min_size}, max={self.max_size}")
        
        self.pool = await asyncpg.create_pool(
            conn_str,
            min_size=self.min_size,
            max_size=self.max_size,
            
            # Performance tuning
            statement_cache_size=self.statement_cache_size,
            max_cached_statement_lifetime=300,  # 5 minutes
            
            # Connection management
            command_timeout=30.0,
            connection_timeout=10.0,
            
            # Health and monitoring
            heartbeat_interval=30,
            
            # Event handlers for monitoring
            setup=self._on_connection_acquire,
            init=self._on_connection_create
        )
        
        self._pool_created_at = time.time()
        logger.info("Database pool created successfully")
    
    async def close(self) -> None:
        """Gracefully close the connection pool"""
        if self.pool:
            logger.info("Closing database pool...")
            await self.pool.close()
            self.pool = None
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def connection(self):
        """
        Context manager for getting a connection from the pool.
        
        Usage:
            async with db.connection() as conn:
                result = await conn.fetch("SELECT * FROM users")
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as conn:
            start_time = time.time()
            try:
                yield conn
            finally:
                # Track connection usage time
                duration = time.time() - start_time
                self._connection_acquire_time += duration
                self._connection_acquire_count += 1
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results as list of dicts.
        
        Args:
            query: SQL query string
            *args: Query parameters
        
        Returns:
            List of dictionaries representing rows
        """
        async with self.connection() as conn:
            try:
                self._query_count += 1
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                self._error_count += 1
                logger.error(f"Query failed: {query[:100]}... Error: {e}")
                raise
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Execute SELECT query and return single row as dict.
        
        Returns None if no rows found.
        """
        async with self.connection() as conn:
            try:
                self._query_count += 1
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                self._error_count += 1
                logger.error(f"Query failed: {query[:100]}... Error: {e}")
                raise
    
    async def execute(self, query: str, *args) -> str:
        """
        Execute non-SELECT query (INSERT, UPDATE, DELETE).
        
        Returns the command status string.
        """
        async with self.connection() as conn:
            try:
                self._query_count += 1
                return await conn.execute(query, *args)
            except Exception as e:
                self._error_count += 1
                logger.error(f"Execute failed: {query[:100]}... Error: {e}")
                raise
    
    async def get_pool_metrics(self) -> PoolMetrics:
        """Get current pool metrics for monitoring"""
        if not self.pool:
            raise RuntimeError("Pool not initialized")
        
        # Get pool statistics
        stats = self.pool.get_stats()
        
        return PoolMetrics(
            pool_size=stats['size'],
            pool_free=stats['free'],
            pool_used=stats['used'],
            pool_waiting=stats['waiting'],
            pool_max=self.max_size
        )
    
    def get_query_metrics(self) -> Dict[str, Union[int, float]]:
        """Get query execution metrics"""
        avg_acquire_time = (
            self._connection_acquire_time / self._connection_acquire_count
            if self._connection_acquire_count > 0 else 0.0
        )
        
        return {
            "total_queries": self._query_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / self._query_count if self._query_count > 0 else 0.0,
            "avg_connection_acquire_time": avg_acquire_time
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        if not self.pool:
            return {"status": "disconnected", "error": "Pool not initialized"}
        
        try:
            # Test basic connectivity
            start_time = time.time()
            result = await self.fetchrow("SELECT 1 as health_check")
            query_time = time.time() - start_time
            
            if result and result.get("health_check") == 1:
                metrics = await self.get_pool_metrics()
                query_metrics = self.get_query_metrics()
                
                return {
                    "status": "healthy",
                    "query_time_ms": query_time * 1000,
                    "pool_metrics": metrics,
                    "query_metrics": query_metrics
                }
            else:
                return {"status": "unhealthy", "error": "Health check query failed"}
                
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _on_connection_create(self, conn: asyncpg.Connection) -> None:
        """Called when a new connection is created"""
        logger.debug("New database connection created")
    
    async def _on_connection_acquire(self, conn: asyncpg.Connection) -> None:
        """Called when a connection is acquired from pool"""
        # Could set connection-specific settings here
        # await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads)
        pass

# Global instance for easy import
db = AsyncDatabase()
```

**Key Design Patterns**:
- **Context Manager**: Automatic connection cleanup
- **Metrics Collection**: Built-in monitoring capabilities
- **Error Handling**: Comprehensive error tracking and logging
- **Health Checks**: Production readiness verification
- **Configuration**: Environment-based connection strings

### Step 2: Refactor FraiseQL to Full Async
**Estimated Time**: 2 hours

**Learning Objective**: Converting GraphQL resolvers to async patterns

**What you'll learn**:
- GraphQL async resolver implementation
- Database query optimization in GraphQL context
- N+1 query problem solutions
- Context passing in GraphQL

```python
# frameworks/fraiseql/main.py - Complete async refactor

from frameworks.common.async_db import db
from strawberry.fastapi import GraphQLRouter
from strawberry import type as strawberry_type
import strawberry
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# GraphQL Types
@strawberry_type
class User:
    id: str
    username: str
    first_name: str | None
    last_name: str | None
    bio: str | None
    
    @strawberry.field
    async def posts(self, limit: int = 10) -> list["Post"]:
        """Resolve user's posts with proper JOIN to avoid N+1"""
        return await db.fetch(
            """
            SELECT p.id, p.title, p.content, p.created_at,
                   p.author_id  -- We know this is the current user
            FROM benchmark.posts p
            WHERE p.author_id = $1 AND p.status = 'published'
            ORDER BY p.created_at DESC
            LIMIT $2
            """,
            self.id, limit
        )

@strawberry_type  
class Post:
    id: str
    title: str
    content: str | None
    author_id: str
    
    @strawberry.field
    async def author(self) -> User:
        """Resolve post author"""
        result = await db.fetchrow(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
            self.author_id
        )
        if not result:
            raise ValueError(f"Author not found: {self.author_id}")
        return User(**result)

@strawberry.type
class Query:
    @strawberry.field
    async def ping(self) -> str:
        return "pong"
    
    @strawberry.field
    async def user(self, id: str) -> User | None:
        """Get single user by ID"""
        result = await db.fetchrow(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
            id
        )
        return User(**result) if result else None
    
    @strawberry.field
    async def users(self, limit: int = 10) -> list[User]:
        """Get multiple users"""
        results = await db.fetch(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users ORDER BY created_at DESC LIMIT $1",
            limit
        )
        return [User(**row) for row in results]
    
    @strawberry.field
    async def post(self, id: str) -> Post | None:
        """Get single post by ID"""
        result = await db.fetchrow(
            "SELECT id, title, content, author_id FROM benchmark.posts WHERE id = $1",
            id
        )
        return Post(**result) if result else None
    
    @strawberry.field
    async def posts(self, limit: int = 10) -> list[Post]:
        """Get multiple posts"""
        results = await db.fetch(
            "SELECT id, title, content, author_id FROM benchmark.posts WHERE status = 'published' ORDER BY created_at DESC LIMIT $1",
            limit
        )
        return [Post(**row) for row in results]

# FastAPI application setup
app = FastAPI(title="FraiseQL Async Benchmark")

@app.on_event("startup")
async def startup_event():
    """Initialize database pool on startup"""
    logger.info("Starting FraiseQL with async database pool")
    await db.connect()
    
    # Log pool configuration
    metrics = await db.get_pool_metrics()
    logger.info(f"Database pool initialized: size={metrics.pool_size}, max={metrics.pool_max}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of database pool"""
    logger.info("Shutting down FraiseQL")
    await db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = await db.health_check()
    if health["status"] == "healthy":
        return health
    else:
        return JSONResponse(status_code=503, content=health)

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    pool_metrics = await db.get_pool_metrics()
    query_metrics = db.get_query_metrics()
    
    metrics_output = f"""# HELP fraiseql_pool_size Current pool size
# TYPE fraiseql_pool_size gauge
fraiseql_pool_size {pool_metrics.pool_size}

# HELP fraiseql_pool_free Free connections in pool
# TYPE fraiseql_pool_free gauge
fraiseql_pool_free {pool_metrics.pool_free}

# HELP fraiseql_pool_used Used connections in pool
# TYPE fraiseql_pool_used gauge
fraiseql_pool_used {pool_metrics.pool_used}

# HELP fraiseql_queries_total Total queries executed
# TYPE fraiseql_queries_total counter
fraiseql_queries_total {query_metrics['total_queries']}

# HELP fraiseql_query_errors_total Total query errors
# TYPE fraiseql_query_errors_total counter
fraiseql_query_errors_total {query_metrics['total_errors']}
"""
    return Response(content=metrics_output, media_type="text/plain")

# Create GraphQL schema and router
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
```

**Critical Changes**:
- All resolvers now `async def`
- Database calls use `await`
- Context managers for connection handling
- Metrics endpoints for monitoring

### Step 3: Refactor Strawberry to Async
**Estimated Time**: 1.5 hours

**Learning Objective**: Strawberry GraphQL async integration

**What you'll learn**:
- Strawberry async field resolvers
- DataLoader integration patterns
- Batch query optimization

```python
# frameworks/strawberry/main.py - Async refactor

from frameworks.common.async_db import db
from strawberry.fastapi import GraphQLRouter
import strawberry
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@strawberry.type
class User:
    id: str
    username: str
    first_name: str | None
    last_name: str | None
    bio: str | None
    
    @strawberry.field
    async def posts(self, limit: int = 10) -> list["Post"]:
        """Async resolver for user posts"""
        results = await db.fetch(
            """
            SELECT id, title, content, author_id, created_at
            FROM benchmark.posts
            WHERE author_id = $1 AND status = 'published'
            ORDER BY created_at DESC
            LIMIT $2
            """,
            self.id, limit
        )
        return [Post(**row) for row in results]

@strawberry.type
class Post:
    id: str
    title: str
    content: str | None
    author_id: str
    
    @strawberry.field
    async def author(self) -> User:
        """Async resolver for post author"""
        result = await db.fetchrow(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
            self.author_id
        )
        if not result:
            raise ValueError(f"Author not found: {self.author_id}")
        return User(**result)

@strawberry.type
class Query:
    @strawberry.field
    async def ping(self) -> str:
        return "pong"
    
    @strawberry.field
    async def user(self, id: str) -> User | None:
        result = await db.fetchrow(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
            id
        )
        return User(**result) if result else None
    
    @strawberry.field
    async def users(self, limit: int = 10) -> list[User]:
        results = await db.fetch(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users ORDER BY created_at DESC LIMIT $1",
            limit
        )
        return [User(**result) for result in results]

# FastAPI setup (same pattern as FraiseQL)
app = FastAPI(title="Strawberry Async Benchmark")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Strawberry with async database pool")
    await db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db.close()

@app.get("/health")
async def health_check():
    health = await db.health_check()
    if health["status"] == "healthy":
        return health
    return JSONResponse(status_code=503, content=health)

# GraphQL setup
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

### Step 4: Refactor FastAPI REST to Async
**Estimated Time**: 1.5 hours

**Learning Objective**: FastAPI async endpoint implementation

**What you'll learn**:
- FastAPI async route handlers
- Async database integration
- Request context management

```python
# frameworks/fastapi-rest/main.py - Async refactor

from frameworks.common.async_db import db
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="FastAPI Async REST Benchmark")

@app.on_event("startup")
async def startup_event():
    """Initialize async database pool"""
    logger.info("Starting FastAPI REST with async database pool")
    await db.connect()
    
    # Configure pool for REST API patterns
    # REST APIs often have more varied queries, so smaller statement cache
    db.statement_cache_size = 50

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    await db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = await db.health_check()
    if health["status"] == "healthy":
        return health
    return JSONResponse(status_code=503, content=health)

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

@app.get("/users")
async def get_users(limit: int = 10):
    """Get users with optional includes"""
    users = await db.fetch(
        "SELECT id, username, first_name, last_name, bio FROM benchmark.users ORDER BY created_at DESC LIMIT $1",
        limit
    )
    return users

@app.get("/users/{user_id}")
async def get_user(user_id: str, include: str = ""):
    """Get single user with optional relationships"""
    user = await db.fetchrow(
        "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
        user_id
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = dict(user)
    
    # Handle includes for relationships
    includes = include.split(",") if include else []
    
    if "posts" in includes:
        posts = await db.fetch(
            """
            SELECT id, title, content, created_at
            FROM benchmark.posts
            WHERE author_id = $1 AND status = 'published'
            ORDER BY created_at DESC
            LIMIT 10
            """,
            user_id
        )
        result["posts"] = posts
    
    if "followers" in includes:
        followers = await db.fetch(
            """
            SELECT u.id, u.username
            FROM benchmark.users u
            JOIN benchmark.user_follows f ON u.id = f.follower_id
            WHERE f.following_id = $1
            LIMIT 10
            """,
            user_id
        )
        result["followers"] = followers
    
    return result

@app.get("/posts")
async def get_posts(limit: int = 10, include: str = ""):
    """Get posts with optional author includes"""
    posts = await db.fetch(
        """
        SELECT p.id, p.title, p.content, p.created_at, p.author_id
        FROM benchmark.posts p
        WHERE p.status = 'published'
        ORDER BY p.created_at DESC
        LIMIT $1
        """,
        limit
    )
    
    # Handle author includes (batch load to avoid N+1)
    if "author" in include.split(","):
        author_ids = list(set(post["author_id"] for post in posts))
        authors = await db.fetch(
            "SELECT id, username, first_name, last_name FROM benchmark.users WHERE id = ANY($1)",
            author_ids
        )
        
        # Create lookup map
        author_map = {author["id"]: author for author in authors}
        
        # Attach authors to posts
        for post in posts:
            post["author"] = author_map.get(post["author_id"])
    
    return posts

@app.get("/posts/{post_id}")
async def get_post(post_id: str, include: str = ""):
    """Get single post with optional includes"""
    post = await db.fetchrow(
        "SELECT id, title, content, created_at, author_id FROM benchmark.posts WHERE id = $1",
        post_id
    )
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    result = dict(post)
    
    includes = include.split(",") if include else []
    
    if "author" in includes:
        author = await db.fetchrow(
            "SELECT id, username, first_name, last_name FROM benchmark.users WHERE id = $1",
            post["author_id"]
        )
        result["author"] = author
    
    if "comments" in includes:
        comments = await db.fetch(
            """
            SELECT c.id, c.content, c.created_at,
                   u.id as author_id, u.username as author_username
            FROM benchmark.comments c
            JOIN benchmark.users u ON c.author_id = u.id
            WHERE c.post_id = $1 AND c.is_approved = true
            ORDER BY c.created_at DESC
            LIMIT 20
            """,
            post_id
        )
        result["comments"] = comments
    
    return result
```

### Step 5: Enhance Flask REST with Sync Pool
**Estimated Time**: 1 hour

**Learning Objective**: Sync pool implementation for non-async frameworks

**What you'll learn**:
- psycopg3 connection pooling
- Thread-local connection management
- Sync/async boundary patterns

```python
# frameworks/flask-rest/main.py - Pool enhancement

from psycopg_pool import ConnectionPool
from flask import Flask, jsonify, request, g
import os
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database connection pool (psycopg3)
pool = ConnectionPool(
    conninfo=f"host={os.getenv('DB_HOST', 'postgres')} "
             f"port={os.getenv('DB_PORT', '5432')} "
             f"dbname={os.getenv('DB_NAME', 'fraiseql_benchmark')} "
             f"user={os.getenv('DB_USER', 'benchmark')} "
             f"password={os.getenv('DB_PASSWORD', 'benchmark123')}",
    min_size=10,
    max_size=50,
    timeout=30.0,
    open=True  # Open pool immediately
)

@app.before_request
def before_request():
    """Get connection from pool for this request"""
    g.db_conn = pool.getconn()

@app.after_request
def after_request(response):
    """Return connection to pool after request"""
    if hasattr(g, 'db_conn'):
        pool.putconn(g.db_conn)
    return response

@app.teardown_appcontext
def teardown_appcontext(exception):
    """Ensure connection cleanup on app context teardown"""
    if hasattr(g, 'db_conn'):
        pool.putconn(g.db_conn)

def get_db():
    """Get database connection for current request"""
    return g.db_conn

@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify({"status": "healthy", "framework": "flask-rest"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route("/ping")
def ping():
    return jsonify({"message": "pong"})

@app.route("/users")
def get_users():
    limit = request.args.get('limit', 10, type=int)
    
    conn = get_db()
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        users = cur.fetchall()
    
    return jsonify(users)

@app.route("/users/<user_id>")
def get_user(user_id):
    include = request.args.get('include', '')
    
    conn = get_db()
    with conn.cursor(row_factory=dict_row) as cur:
        # Get user
        cur.execute(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = %s",
            (user_id,)
        )
        user = cur.fetchone()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        result = dict(user)
        
        # Handle includes
        includes = include.split(',') if include else []
        
        if 'posts' in includes:
            cur.execute(
                """SELECT id, title, content, created_at FROM benchmark.posts 
                   WHERE author_id = %s AND status = 'published' 
                   ORDER BY created_at DESC LIMIT 10""",
                (user_id,)
            )
            result['posts'] = cur.fetchall()
        
        if 'followers' in includes:
            cur.execute(
                """SELECT u.id, u.username FROM benchmark.users u
                   JOIN benchmark.user_follows f ON u.id = f.follower_id
                   WHERE f.following_id = %s LIMIT 10""",
                (user_id,)
            )
            result['followers'] = cur.fetchall()
    
    return jsonify(result)

@app.route("/posts")
def get_posts():
    limit = request.args.get('limit', 10, type=int)
    include = request.args.get('include', '')
    
    conn = get_db()
    with conn.cursor(row_factory=dict_row) as cur:
        # Get posts
        cur.execute(
            """SELECT id, title, content, created_at, author_id FROM benchmark.posts 
               WHERE status = 'published' ORDER BY created_at DESC LIMIT %s""",
            (limit,)
        )
        posts = cur.fetchall()
        
        # Handle author includes (batch to avoid N+1)
        if 'author' in include.split(','):
            author_ids = [post['author_id'] for post in posts]
            if author_ids:
                cur.execute(
                    "SELECT id, username, first_name, last_name FROM benchmark.users WHERE id = ANY(%s)",
                    (author_ids,)
                )
                authors = cur.fetchall()
                author_map = {author['id']: author for author in authors}
                
                for post in posts:
                    post['author'] = author_map.get(post['author_id'])
    
    return jsonify(posts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004)
```

### Step 6: Connection Pool Configuration Matrix
**Estimated Time**: 30 minutes

**Learning Objective**: Pool tuning based on framework characteristics

**What you'll learn**:
- Pool sizing strategies
- Framework-specific optimization
- Resource allocation trade-offs

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

## Testing Strategy

### Unit Testing
- **Connection pool**: Pool creation, connection acquisition/release
- **Query execution**: All CRUD operations with proper error handling
- **Metrics collection**: Pool and query metrics accuracy
- **Health checks**: Proper health status reporting

### Integration Testing
- **Framework startup**: Pool initialization during app startup
- **Concurrent requests**: Multiple simultaneous database operations
- **Connection limits**: Behavior under high load (connection exhaustion)
- **Graceful shutdown**: Pool cleanup on application termination

### Performance Testing
- **Throughput comparison**: Before/after async implementation
- **Connection utilization**: Pool usage under load
- **Query performance**: Statement caching effectiveness
- **Resource usage**: Memory and CPU impact of async operations

## Common Pitfalls and Solutions

### 1. Event Loop Blocking
**Problem**: Sync database calls block the async event loop
**Solution**: Always use async database operations in async frameworks
**Prevention**: Code review checks for sync database calls

### 2. Connection Pool Exhaustion
**Problem**: Too many concurrent requests exhaust connection pool
**Solution**:
```python
# Monitor pool usage
metrics = await db.get_pool_metrics()
if metrics.pool_used / metrics.pool_max > 0.8:
    logger.warning("Pool usage > 80%")
```

### 3. Statement Cache Invalidation
**Problem**: Changing query patterns cause cache misses
**Solution**: Monitor cache hit rates and adjust cache size accordingly

### 4. Connection Leaks
**Problem**: Connections not returned to pool
**Solution**: Always use context managers or ensure proper cleanup

### 5. Pool Configuration Issues
**Problem**: Pool too small or too large for workload
**Solution**: Monitor and adjust based on actual usage patterns

## Best Practices Learned

### 1. Async Database Patterns
- Always use async database drivers in async frameworks
- Implement proper connection pooling
- Use context managers for connection lifecycle
- Monitor connection usage and pool health

### 2. Performance Optimization
- Enable statement caching for repeated queries
- Use prepared statements for complex queries
- Batch operations when possible
- Monitor query performance and optimize slow queries

### 3. Resource Management
- Configure appropriate pool sizes based on workload
- Implement graceful shutdown procedures
- Monitor resource usage and adjust accordingly
- Use health checks for production readiness

### 4. Error Handling
- Implement comprehensive error handling for database operations
- Log errors with sufficient context for debugging
- Implement retry logic for transient failures
- Provide meaningful error messages to clients

### 5. Monitoring and Observability
- Implement metrics collection for pool usage
- Track query performance and error rates
- Use health checks for service discovery
- Monitor resource utilization

## Verification Criteria

### Phase 3 Completion Checklist

**Async Implementation**
- [ ] FraiseQL uses asyncpg with connection pool (min 20, max 100)
- [ ] Strawberry uses asyncpg with connection pool (min 10, max 50)
- [ ] Graphene uses asyncpg with connection pool (min 10, max 50)
- [ ] FastAPI REST uses asyncpg with connection pool (min 20, max 100)
- [ ] Flask REST uses psycopg3 sync pool (min 10, max 50)

**Pool Configuration**
- [ ] Pool sizes configured per framework characteristics
- [ ] Statement caching enabled and sized appropriately
- [ ] Connection timeouts and health checks configured
- [ ] Graceful pool shutdown implemented

**Performance Validation**
- [ ] No "connection exhausted" errors under 100 concurrent users
- [ ] 5-10x throughput improvement for async frameworks
- [ ] Pool utilization monitored and optimized
- [ ] Query performance improved with statement caching

**Monitoring and Health**
- [ ] Pool metrics exposed via /metrics endpoints
- [ ] Health checks return pool status information
- [ ] Query count and error tracking implemented
- [ ] Connection acquire time monitoring

**Code Quality**
- [ ] All database operations properly awaited
- [ ] Context managers used for connection lifecycle
- [ ] Error handling implemented for all database calls
- [ ] Logging added for debugging and monitoring

## References and Resources

### asyncpg Documentation
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)
- [Connection Pools](https://magicstack.github.io/asyncpg/current/usage.html#connection-pools)
- [Performance Tips](https://magicstack.github.io/asyncpg/current/usage.html#performance-tips)

### PostgreSQL Connection Pooling
- [pgBouncer Documentation](https://www.pgbouncer.org/)
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html)

### Python Async Patterns
- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Async](https://fastapi.tiangolo.com/async/)
- [GraphQL Async](https://strawberry.rocks/docs/guides/async)

## Phase Sign-off

**Phase 3 Status**: ☐ Ready for Phase 4 ☐ Needs Remediation

**Completed By**: ________________________ Date: _______________

**Reviewed By**: ________________________ Date: _______________

**Performance Improvements Demonstrated**:
1. Async framework throughput increased 5-10x
2. Connection pool utilization optimized
3. No connection exhaustion under load
4. Proper resource management implemented

**Issues Identified**:
1.
2.
3.

**Remediation Plan**:
1.
2.
3.</content>
<parameter name="filePath">.phases/phase-3-connection-pooling-async-detailed.md