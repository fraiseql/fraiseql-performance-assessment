# Strawberry GraphQL Naive ORM Implementation

## Purpose

This is an **intentionally naive implementation** that demonstrates **N+1 query problems** in GraphQL with SQLAlchemy ORM. It shows what happens when you don't use DataLoaders or eager loading.

Use this alongside the optimized version (`../strawberry-orm/`) to compare performance and understand the impact of proper ORM patterns.

## Key N+1 Patterns

### 1. **Lazy Loading in GraphQL Resolvers**

Instead of using DataLoaders for batching, each field resolver makes a separate database query:

```python
@strawberry.field
async def author(self) -> Optional["UserGQL"]:
    # NAIVE: Direct database query for each comment/post (N+1 problem!)
    async with async_session_maker() as session:
        user = await session.get(User, self.author_id)  # 1 query per resolver call
```

### 2. **No Relationship Preloading**

Relationships are loaded on-demand, causing exponential queries:

```python
@strawberry.field
async def posts(self) -> list[PostGQL]:
    # NAIVE: Query executed for every user in result set
    async with async_session_maker() as session:
        stmt = select(Post).where(Post.author_id == self.id)  # N+1 queries
```

## N+1 Problem Demonstration

When querying for users with their posts and comments:

**Naive Version (This Implementation):**
```
Query: { users { id username posts { title comments { content } } } }

Database Queries:
1. SELECT * FROM tb_user (get users)
2. SELECT * FROM tb_post WHERE author_id = ? (per user - N queries)
3. SELECT * FROM tb_comment WHERE post_id = ? (per post - N×M queries)

Total: 1 + N + (N × M) queries
Example: 100 users × 5 posts × 10 comments = 5,101 queries!
```

**Optimized Version (With DataLoaders):**
```
Database Queries:
1. SELECT * FROM tb_user (get users)
2. SELECT * FROM tb_post WHERE author_id IN (...) (1 batch query)
3. SELECT * FROM tb_comment WHERE post_id IN (...) (1 batch query)

Total: 3 queries (regardless of data size)
```

## Performance Impact

| Data Size | Naive Queries | Optimized Queries | Slowdown Factor |
|-----------|---------------|-------------------|-----------------|
| 10 users, 2 posts each | ~25 queries | 3 queries | ~8x slower |
| 100 users, 5 posts each | ~505 queries | 3 queries | ~168x slower |
| 1000 users, 10 posts each | ~10,005 queries | 3 queries | ~3,335x slower |

## Setup & Testing

### 1. Install Dependencies
```bash
cd frameworks-orm/strawberry-orm-naive
pip install -r requirements.txt
```

### 2. Enable Query Logging
```bash
# In main.py, ensure SQLAlchemy logging is enabled:
engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True shows all queries
```

### 3. Start Server
```bash
python main.py
# Server runs on http://localhost:8000
```

### 4. Test N+1 Problem
```bash
# Query that will show N+1 problem
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ users(limit: 5) { id username posts { title comments { content author { username } } } } }"
  }'

# Watch the logs - you should see many individual SELECT queries
```

### 5. Compare with Optimized Version
```bash
# Run same query against optimized version
cd ../strawberry-orm
python main.py  # Runs on different port or stop naive first

# Notice: Only 3 queries instead of dozens!
```

## What Makes This "Naive"

1. **No DataLoaders**: Each field resolver hits the database individually
2. **Lazy Loading**: Relationships loaded on-demand, not preloaded
3. **Individual Queries**: No batching of similar requests
4. **Exponential Growth**: Query count grows with data relationships

## Educational Value

This implementation teaches:
- Why N+1 queries are problematic
- How GraphQL resolvers can cause performance issues
- The importance of DataLoader pattern
- ORM lazy loading vs eager loading trade-offs
- Real-world impact of database query optimization

## Comparison with Optimized Version

| Aspect | Naive (This) | Optimized (strawberry-orm) |
|--------|--------------|---------------------------|
| **Queries** | 1+N+(N×M) | 3 (fixed) |
| **Performance** | Slow (seconds) | Fast (milliseconds) |
| **Code Complexity** | Simple | More complex (DataLoaders) |
| **Scalability** | Poor | Excellent |
| **Use Case** | Learning anti-patterns | Production applications |

## Lessons Learned

- Always use DataLoaders in GraphQL for relationship fields
- Batch similar database queries to prevent N+1 problems
- Monitor query logs to identify performance issues
- ORM lazy loading is convenient but dangerous at scale
- Preloading relationships is critical for good performance

---

**Remember**: This implementation is intentionally bad! Never use these patterns in production. Compare it with the optimized version to understand why proper patterns matter.</content>
<parameter name="filePath">frameworks-orm/strawberry-orm-naive/README.md