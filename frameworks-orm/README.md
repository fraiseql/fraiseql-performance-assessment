# Traditional ORM Implementations - Performance Comparison Suite

**Purpose**: Compare raw SQL vs traditional ORM approaches across all frameworks
**Status**: Initial implementations ready (Strawberry + FastAPI)
**Next Phase**: Complete other frameworks and run benchmarks

---

## Quick Start

### Strawberry GraphQL + SQLAlchemy ORM

```bash
cd strawberry-orm
pip install -r requirements.txt
python main.py
# GraphQL endpoint: http://localhost:8000/graphql
```

### FastAPI REST + SQLAlchemy ORM

```bash
cd fastapi-orm
pip install -r requirements.txt
python main.py
# API endpoint: http://localhost:8003
# REST endpoints: /users, /posts, /users/{id}/posts
```

---

## What's Included

### Python Frameworks (Complete)

✅ **strawberry-orm/** - Strawberry GraphQL + SQLAlchemy ORM
  - Full ORM relationships
  - DataLoader for N+1 prevention
  - Eager loading with `selectinload()`
  - Production-ready code

✅ **fastapi-orm/** - FastAPI REST + SQLAlchemy ORM
  - Relationship-based routes
  - Include parameters for lazy/eager loading
  - Proper error handling
  - Type-safe Pydantic models

### Node.js Frameworks (Template Ready)

🔨 **apollo-orm/** - Apollo Server + TypeORM (structure ready)
🔨 **express-orm/** - Express REST + TypeORM (structure ready)

### Go Frameworks (Template Ready)

🔨 **gqlgen-orm/** - gqlgen + GORM (structure ready)
🔨 **gin-orm/** - Gin + GORM (structure ready)

---

## Key Features

### 1. Proper ORM Relationships

**Before** (Raw SQL - Manual Relationships):
```python
# Get user
user = await db.fetch("SELECT * FROM users WHERE id = $1", user_id)
# Get posts
posts = await db.fetch("SELECT * FROM posts WHERE author_id = $1", user_id)
# Get comments
comments = await db.fetch("SELECT * FROM comments WHERE post_id IN ($1...)", post_ids)
# Manually assemble objects
```

**After** (ORM - Automatic Relationships):
```python
# Get user with all relationships
user = await session.execute(
    select(User)
    .options(selectinload(User.posts).selectinload(Post.comments))
).scalars().first()
# Relationships automatically loaded
```

### 2. Type Safety

```python
# ORM Models are typed
class Post(Base):
    author: Relationship[User]  # Type-safe reference
    comments: Relationship[list[Comment]]

# Type-safe queries
posts: list[Post] = await session.execute(
    select(Post)
).scalars().all()
```

### 3. N+1 Query Prevention

**Automatic Detection**:
```python
# With ORM and eager loading
users = await session.execute(
    select(User).options(selectinload(User.posts))
)  # 2 queries total, no N+1

# Without ORM (easy to miss)
users = await db.fetch("SELECT * FROM users")  # 1 query
for user in users:
    posts = await db.fetch("SELECT * FROM posts WHERE author_id = $1", user['id'])
    # N queries! N+1 problem
```

---

## Performance Characteristics

### Expected Overhead vs Raw SQL

| Scenario | Raw SQL | ORM | Impact |
|----------|---------|-----|--------|
| **Simple query** | 5ms | 8ms | +60% |
| **Query + JOIN** | 10ms | 13ms | +30% |
| **Batch load** | 15ms | 16ms | +7% |
| **N+1 query** | 50ms | 15ms* | -70%* |

*With eager loading enabled

### When ORM Wins

1. **Prevents N+1 queries**: ORM detects relationship loads
2. **Complex relationships**: Automatic JOIN construction
3. **Maintenance**: Easier than manual relationship handling
4. **Type safety**: Compile-time relationship checking

### When Raw SQL Wins

1. **Analytics queries**: Complex CTEs, window functions
2. **Bulk operations**: INSERT/UPDATE millions
3. **Custom filtering**: Domain-specific logic
4. **Proven fast**: Already optimized SQL

---

## Architecture

### Database Schema (Used by All Implementations)

```
benchmark schema (PostgreSQL)
├── tb_users (User model)
│   ├── id (PK)
│   ├── username
│   ├── first_name, last_name
│   └── bio
├── tb_posts (Post model)
│   ├── id (PK)
│   ├── title, content
│   ├── author_id (FK → tb_users)
│   └── created_at
└── tb_comments (Comment model)
    ├── id (PK)
    ├── content
    ├── post_id (FK → tb_posts)
    ├── author_id (FK → tb_users)
    └── created_at
```

### ORM Model Structure

**Python (SQLAlchemy)**:
```
User.posts → list[Post]
Post.author → User
Post.comments → list[Comment]
Comment.author → User
Comment.post → Post
```

**Node.js (TypeORM)**:
```
User.posts → OneToMany(Post)
Post.author → ManyToOne(User)
Post.comments → OneToMany(Comment)
Comment.author → ManyToOne(User)
Comment.post → ManyToOne(Post)
```

**Go (GORM)**:
```
User.Posts → []Post
Post.Author → User
Post.Comments → []Comment
Comment.Author → User
Comment.Post → Post
```

---

## Running Benchmarks

### 1. Start Database

```bash
cd /path/to/fraiseql-performance-assessment
docker-compose up postgres
```

### 2. Run Raw SQL Implementation (Baseline)

```bash
cd frameworks/strawberry
python main.py &  # Runs on port 8000

# In another terminal
./tests/perf/scripts/run-test.sh --framework strawberry --workload simple
```

### 3. Run ORM Implementation (Comparison)

```bash
cd frameworks-orm/strawberry-orm
python main.py &  # Runs on port 8000

# Run same test
./tests/perf/scripts/run-test.sh --framework strawberry-orm --workload simple
```

### 4. Compare Results

```bash
python ./compare_orm_vs_sql.py \
  --raw-sql-file tests/perf/results/strawberry_only.jtl \
  --orm-file tests/perf/results/strawberry_orm.jtl
```

---

## Implementation Status

### ✅ Complete

- [x] Strawberry GraphQL + SQLAlchemy ORM
- [x] FastAPI REST + SQLAlchemy ORM
- [x] Documentation and guides
- [x] Requirements files
- [x] Architecture design

### 🔨 In Progress

- [ ] Apollo Server + TypeORM implementation
- [ ] Express REST + TypeORM implementation
- [ ] gqlgen + GORM implementation
- [ ] Gin REST + GORM implementation

### 📋 Planned

- [ ] Run comparative benchmarks
- [ ] Document performance differences
- [ ] Create optimization guides
- [ ] Performance tuning recommendations

---

## Comparing Implementations

### Query Patterns

**Raw SQL Pattern** (existing):
```python
# Direct SQL
users = await db.fetch("SELECT * FROM users WHERE id = ANY($1)", user_ids)
user_map = {user["id"]: user for user in users}
return [user_map.get(key) for key in user_ids]
```

**ORM Pattern** (new):
```python
# ORM with relationships
users = await session.execute(
    select(User).where(User.id.in_(user_ids))
)
return users.scalars().all()
```

### Relationship Loading

**Raw SQL** (Manual):
```python
# Must manually load relationships
posts = await db.fetch("SELECT * FROM posts WHERE author_id = $1", user.id)
user["posts"] = posts
```

**ORM** (Automatic):
```python
# Relationships automatically available
user = await session.execute(
    select(User).options(selectinload(User.posts))
).scalars().first()
# user.posts is automatically populated
```

---

## Best Practices

### 1. Use Eager Loading

```python
# ✅ Good: Load relationships eagerly
stmt = select(User).options(selectinload(User.posts))

# ❌ Bad: Lazy loading (causes N+1)
user = await session.get(User, user_id)
posts = user.posts  # Queries database!
```

### 2. Batch Loading

```python
# ✅ Good: Load many users with posts
users = await session.execute(
    select(User)
    .where(User.id.in_(user_ids))
    .options(selectinload(User.posts))
).scalars().all()

# ❌ Bad: Loop and load (N+1)
for user_id in user_ids:
    user = await session.get(User, user_id)
    posts = user.posts  # N queries!
```

### 3. Limit Relationships

```python
# ✅ Good: Only load what you need
stmt = select(User).options(selectinload(User.posts.filter(...)))

# ❌ Bad: Load all relationships
stmt = select(User).options(
    selectinload(User.posts),
    selectinload(User.comments),
    selectinload(User.followers),
    # ... 10 more relationships
)
```

---

## Troubleshooting

### N+1 Query Detection

**Symptom**: Slow response with many queries

**Check**:
```python
# Enable SQLAlchemy logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Now see all queries executed
```

**Solution**:
```python
# Add eager loading
.options(selectinload(Model.relationships))
```

### Connection Pool Exhaustion

**Symptom**: "QueuePool limit exceeded"

**Solution**:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,      # Increase from 10
    max_overflow=50,   # Allow overflow
)
```

### Slow Queries

**Symptom**: ORM queries slower than expected

**Check**:
1. Is it using eager loading?
2. Are there indexes on foreign keys?
3. Are you loading too many relationships?

**Solution**:
```python
# Add indexes
class Post(Base):
    __table_args__ = (
        Index("idx_post_author_id", "author_id"),
    )

# Or use raw SQL for complex queries
```

---

## Next Steps

1. **Complete other frameworks**:
   - Apollo + TypeORM
   - Gin + GORM
   - etc.

2. **Run benchmarks**:
   - Compare latency (raw SQL vs ORM)
   - Count queries executed
   - Memory usage

3. **Document findings**:
   - When to use each approach
   - Performance tuning tips
   - Best practices guide

4. **Create migration guide**:
   - How to switch from SQL to ORM
   - Common pitfalls
   - Optimization checklist

---

## References

- **SQLAlchemy 2.0 Docs**: https://docs.sqlalchemy.org/
- **TypeORM Docs**: https://typeorm.io/
- **GORM Docs**: https://gorm.io/
- **N+1 Query Problem**: https://en.wikipedia.org/wiki/N%2B1_query_problem

---

## Questions?

See `ORM_IMPLEMENTATIONS_GUIDE.md` for detailed implementation patterns and performance analysis.

---

**Status**: Ready for benchmarking
**Implementations**: 2 complete (Python), 4 in progress (Node.js/Go)
**Documentation**: Complete

Generated: December 18, 2025
