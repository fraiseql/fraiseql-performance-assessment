# Express REST Naive ORM Implementation

## Purpose

This is an **intentionally naive implementation** that demonstrates **N+1 query problems** in Express REST APIs with TypeORM. It shows what happens when you don't use eager loading in REST endpoints.

Use this alongside optimized Express implementations to compare performance and understand the impact of proper ORM patterns.

## Key N+1 Patterns

### 1. **Lazy Loading in REST Endpoints**

Instead of using eager loading, endpoints return entities that trigger lazy loads when relationships are accessed:

```typescript
// NAIVE: Load users without relationships - causes lazy loading!
const users = await userRepository.find({
    take: limit
    // NO relations loaded - relationships accessed lazily
});

return users; // Client accessing user.posts triggers N+1 queries!
```

### 2. **No Relationship Preloading**

TypeORM entities have `eager: false` which causes lazy loading on access:

```typescript
@OneToMany(() => Post, post => post.author, {
    eager: false  // This causes lazy loading!
})
posts: Post[];
```

### 3. **Separate Relationship Queries**

Instead of joining, relationships are queried separately:

```typescript
// GET /users/:id/posts - NAIVE approach
const posts = await postRepository.find({
    where: { authorId: id }  // Separate query per user relationship access
});
```

## N+1 Problem Demonstration

### **GET /api/users (List Users)**
**Naive Version:**
```
Query: GET /api/users

Database Queries:
1. SELECT * FROM tb_user LIMIT 10 (get users)
2. SELECT * FROM tb_post WHERE author_id = ? (when accessing user.posts - N queries)
3. SELECT * FROM tb_comment WHERE author_id = ? (when accessing user.comments - N queries)

Total: 1 + 2N queries per user access
Example: 10 users = 21 queries
```

**Optimized Version (with eager loading):**
```
Database Queries:
1. SELECT u.*, p.*, c.* FROM tb_user u
   LEFT JOIN tb_post p ON u.id = p.author_id
   LEFT JOIN tb_comment c ON u.id = c.author_id
   LIMIT 10 (1 query with joins)

Total: 1 query
```

### **GET /api/posts (List Posts with Authors)**
**Naive Version:**
```
Query: GET /api/posts

Database Queries:
1. SELECT * FROM tb_post LIMIT 10 (get posts)
2. SELECT * FROM tb_user WHERE id = ? (when accessing post.author - N queries)
3. SELECT * FROM tb_comment WHERE post_id = ? (when accessing post.comments - N queries)

Total: 1 + 2N queries
Example: 10 posts = 21 queries
```

## Performance Impact

| Endpoint | Data Size | Naive Queries | Optimized Queries | Slowdown Factor |
|----------|-----------|---------------|-------------------|-----------------|
| GET /users | 10 users | 21 queries | 1 query | ~21x slower |
| GET /posts | 10 posts | 21 queries | 1 query | ~21x slower |
| GET /users/:id | 1 user | 3 queries | 1 query | ~3x slower |
| GET /posts/:id | 1 post | 3 queries | 1 query | ~3x slower |

## Setup & Testing

### 1. Install Dependencies
```bash
cd frameworks-orm/express-orm-naive
npm install
```

### 2. Enable Query Logging
TypeORM logging is enabled in the connection configuration:
```typescript
logging: true  // Shows all queries in console
```

### 3. Start Server
```bash
npm run dev
# Server runs on http://localhost:3000
```

### 4. Test N+1 Problem
```bash
# Test that will show N+1 problem
curl "http://localhost:3000/api/users?limit=5"
# Watch the console logs - you should see N+1 SELECT queries when accessing relationships

curl "http://localhost:3000/api/posts?limit=5"
# Watch the console logs - you should see additional queries for relationships

# Example of what you'll see in logs:
# SELECT * FROM tb_user LIMIT 5
# SELECT * FROM tb_post WHERE author_id = ?  -- N+1!
# SELECT * FROM tb_post WHERE author_id = ?  -- N+1!
# SELECT * FROM tb_post WHERE author_id = ?  -- N+1!
```

### 5. Compare with Optimized Version
Compare the query logs with an optimized Express implementation that uses eager loading.

## What Makes This "Naive"

1. **No Eager Loading**: All repository queries use default lazy loading
2. **Lazy Loading Reliance**: Relationships loaded on-demand
3. **Separate Queries**: Each relationship access triggers new query
4. **No Joins**: No relationship preloading in queries

## Educational Value

This implementation teaches:
- Why REST APIs can have N+1 problems too
- How eager loading prevents lazy loading issues
- TypeORM lazy vs eager loading trade-offs
- REST API performance implications of ORM patterns
- When to use `.relations()` in TypeORM queries

## Comparison with Optimized Version

| Aspect | Naive (This) | Optimized (with eager loading) |
|--------|--------------|-------------------------------|
| **Queries** | 1+2N | 1 (fixed) |
| **Performance** | Slow (seconds) | Fast (milliseconds) |
| **Code Complexity** | Simple | More complex (relations management) |
| **Scalability** | Poor | Excellent |
| **Use Case** | Learning anti-patterns | Production REST APIs |

## Lessons Learned

- Always use `.relations()` or eager loading in REST API queries
- Set `eager: true` in TypeORM relationships when appropriate
- Monitor database query logs for N+1 patterns
- Use JOINs or preloading for relationships in list endpoints
- Include relationships strategically based on API usage patterns

---

**Remember**: This implementation is intentionally bad! Never use these patterns in production. Compare it with eager loading implementations to understand why relationship preloading matters.</content>
<parameter name="filePath">frameworks-orm/express-orm-naive/README.md