# Gin REST Naive ORM Implementation

## Purpose

This is an **intentionally naive implementation** that demonstrates **N+1 query problems** in Gin REST APIs with GORM. It shows what happens when you don't use Preload in REST endpoints.

Use this alongside optimized Gin implementations to compare performance and understand the impact of proper ORM patterns.

## Key N+1 Patterns

### 1. **Lazy Loading in REST Endpoints**

Instead of using Preload for eager loading, endpoints return entities that trigger lazy loads when relationships are accessed:

```go
// NAIVE: Load users without relationships - causes lazy loading!
var users []*models.User
if err := models.DB.Limit(limit).Find(&users).Error; err != nil {
    // Error handling
}
return users // Client accessing user.Posts triggers N+1 queries!
```

### 2. **No Relationship Preloading**

GORM models don't use Preload, causing lazy loading on access:

```go
// NAIVE: Relationships without Preload - causes lazy loading!
type User struct {
    Posts    []Post    `gorm:"foreignKey:AuthorID"`
    Comments []Comment `gorm:"foreignKey:AuthorID"`
}
```

### 3. **Separate Relationship Queries**

Instead of joining, relationships are queried separately:

```go
// GET /users/:userId/posts - NAIVE approach
var posts []*models.Post
if err := models.DB.Where("author_id = ?", userID).Limit(limit).Find(&posts).Error; err != nil {
    // Error handling
}
return posts // Separate query per user relationship access
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

**Optimized Version (with Preload):**
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
| GET /api/users | 10 users | 21 queries | 1 query | ~21x slower |
| GET /api/posts | 10 posts | 21 queries | 1 query | ~21x slower |
| GET /api/users/:id | 1 user | 3 queries | 1 query | ~3x slower |
| GET /api/posts/:id | 1 post | 3 queries | 1 query | ~3x slower |

## Setup & Testing

### 1. Install Dependencies
```bash
cd frameworks-orm/gin-orm-naive
go mod tidy
```

### 2. Enable Query Logging
GORM logging is enabled in the database configuration:
```go
Logger: logger.Default.LogMode(logger.Info) // Shows all queries!
```

### 3. Start Server
```bash
go run cmd/server/main.go
# Server runs on http://localhost:5000
```

### 4. Test N+1 Problem
```bash
# Test that will show N+1 problem
curl "http://localhost:5000/api/users?limit=5"
# Watch the console logs - you should see N+1 SELECT queries when accessing relationships

curl "http://localhost:5000/api/posts?limit=5"
# Watch the console logs - you should see additional queries for relationships

# Example of what you'll see in logs:
# SELECT * FROM tb_user LIMIT 5
# SELECT * FROM tb_post WHERE author_id = ?  -- N+1!
# SELECT * FROM tb_post WHERE author_id = ?  -- N+1!
# SELECT * FROM tb_post WHERE author_id = ?  -- N+1!
```

### 5. Compare with Optimized Version
Compare the query logs with an optimized Gin implementation that uses Preload.

## What Makes This "Naive"

1. **No Preload**: All GORM queries use default lazy loading
2. **Lazy Loading Reliance**: Relationships loaded on-demand
3. **Separate Queries**: Each relationship access triggers new query
4. **No Joins**: No relationship preloading in queries

## Educational Value

This implementation teaches:
- Why REST APIs can have N+1 problems too
- How GORM Preload prevents lazy loading issues
- Gin route handler performance implications
- Go ORM lazy vs eager loading trade-offs
- Real-world impact of REST API query optimization

## Comparison with Optimized Version

| Aspect | Naive (This) | Optimized (with Preload) |
|--------|--------------|--------------------------|
| **Queries** | 1+2N | 1 (fixed) |
| **Performance** | Slow (seconds) | Fast (milliseconds) |
| **Code Complexity** | Simple | More complex (Preload management) |
| **Scalability** | Poor | Excellent |
| **Use Case** | Learning anti-patterns | Production REST APIs |

## Lessons Learned

- Always use GORM Preload for REST API queries that return related data
- Set up Preload strategically based on API usage patterns
- Monitor GORM query logs for N+1 patterns
- Use JOINs or preloading for relationships in list endpoints
- Include relationships based on client access patterns

---

**Remember**: This implementation is intentionally bad! Never use these patterns in production. Compare it with Preload implementations to understand why eager loading matters.</content>
<parameter name="filePath">frameworks-orm/gin-orm-naive/README.md