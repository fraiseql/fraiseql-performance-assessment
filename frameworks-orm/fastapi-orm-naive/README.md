# FastAPI REST Naive ORM Implementation

## Purpose

This is an **intentionally naive implementation** that demonstrates **N+1 query problems** in FastAPI REST APIs with SQLAlchemy ORM. It shows what happens when you don't use eager loading.

Use this alongside the optimized version (`../fastapi-orm/`) to compare performance and understand the impact of proper ORM patterns.

## Key N+1 Patterns

### 1. **Lazy Loading in REST Endpoints**

Instead of using `selectinload()` for eager loading, each endpoint relies on lazy loading:

```python
# NAIVE: Always use lazy loading - no eager loading!
stmt = select(User).where(User.id == user_id)
result = await session.execute(stmt)
user = result.scalars().first()
# Relationships loaded lazily when accessed
```

### 2. **No Conditional Eager Loading**

The optimized version uses include parameters to conditionally load relationships:

```python
# OPTIMIZED (removed from naive version):
if include == "posts":
    stmt = stmt.options(selectinload(User.posts))
```

### 3. **Individual Relationship Access**

When you return ORM objects from FastAPI, accessing relationships triggers lazy loads:

```python
@app.get("/users/{user_id}")
async def get_user(user_id: str, session: AsyncSession):
    user = await session.get(User, user_id)  # Query 1
    return user  # Relationships not loaded yet

# When client accesses user.posts, it triggers Query 2, 3, 4... (N+1!)
```

## N+1 Problem Demonstration

### **GET /users (List Users)**
**Naive Version:**
```
Query: GET /users?include=posts

Database Queries:
1. SELECT * FROM tb_user LIMIT 10 (get users)
2. SELECT * FROM tb_post WHERE author_id = ? (per user - N queries)

Total: 1 + N queries
Example: 10 users = 11 queries
```

**Optimized Version:**
```
Database Queries:
1. SELECT * FROM tb_user LIMIT 10 (get users)
2. SELECT * FROM tb_post WHERE author_id IN (...) (1 batch query)

Total: 2 queries (regardless of user count)
```

### **GET /posts (List Posts with Authors)**
**Naive Version:**
```
Query: GET /posts?include=comments

Database Queries:
1. SELECT * FROM tb_post LIMIT 10 (get posts)
2. SELECT * FROM tb_user WHERE id = ? (per post - N queries)
3. SELECT * FROM tb_comment WHERE post_id = ? (per post - N queries)

Total: 1 + N + N queries
Example: 10 posts = 21 queries
```

**Optimized Version:**
```
Database Queries:
1. SELECT * FROM tb_post + JOIN tb_user (get posts with authors)
2. SELECT * FROM tb_comment WHERE post_id IN (...) (1 batch query)

Total: 2 queries
```

## Performance Impact

| Endpoint | Data Size | Naive Queries | Optimized Queries | Slowdown Factor |
|----------|-----------|---------------|-------------------|-----------------|
| GET /users | 10 users | 11 queries | 2 queries | ~5x slower |
| GET /users?include=posts | 10 users | 21 queries | 3 queries | ~7x slower |
| GET /posts | 10 posts | 21 queries | 2 queries | ~10x slower |
| GET /posts?include=comments | 10 posts | 31 queries | 3 queries | ~10x slower |

## Setup & Testing

### 1. Install Dependencies
```bash
cd frameworks-orm/fastapi-orm-naive
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
# Test that will show N+1 problem
curl "http://localhost:8000/users?include=posts"
# Watch the logs - you should see N+1 SELECT queries

curl "http://localhost:8000/posts?include=comments"
# Watch the logs - you should see 2N+1 SELECT queries

# Compare with optimized version
cd ../fastapi-orm
python main.py  # Runs on different port

# Same queries show only 2-3 queries total!
```

### 5. Compare with Optimized Version
```bash
# Run same requests against optimized version
curl "http://localhost:8000/users?include=posts"  # Optimized
curl "http://localhost:8000/posts?include=comments"  # Optimized

# Notice: Fixed number of queries regardless of data size
```

## What Makes This "Naive"

1. **No Eager Loading**: All `selectinload()` calls removed
2. **Lazy Loading Reliance**: Relationships loaded on-demand
3. **Include Parameter Ignored**: No conditional relationship loading
4. **Exponential Queries**: Query count grows with relationships

## Educational Value

This implementation teaches:
- Why REST APIs can have N+1 problems too
- How `selectinload()` prevents lazy loading issues
- Importance of relationship preloading in web APIs
- Performance impact of ORM lazy loading
- When to use eager vs lazy loading strategies

## Comparison with Optimized Version

| Aspect | Naive (This) | Optimized (fastapi-orm) |
|--------|--------------|--------------------------|
| **Queries** | 1+N+(N×M) | 2-3 (fixed) |
| **Performance** | Slow (seconds) | Fast (milliseconds) |
| **Code Complexity** | Simple | More complex (conditional loading) |
| **Scalability** | Poor | Excellent |
| **Use Case** | Learning anti-patterns | Production APIs |

## Lessons Learned

- Always eager load relationships in REST API responses
- Use `selectinload()` for one-to-many relationships
- Use `joinedload()` for many-to-one relationships
- Include parameters can optimize based on client needs
- Monitor query logs to catch N+1 problems early
- ORM lazy loading is convenient but dangerous for APIs

---

**Remember**: This implementation is intentionally bad! Never use these patterns in production. Compare it with the optimized version to understand why proper eager loading matters.</content>
<parameter name="filePath">frameworks-orm/fastapi-orm-naive/README.md