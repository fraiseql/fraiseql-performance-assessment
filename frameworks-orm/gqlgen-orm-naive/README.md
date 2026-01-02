# gqlgen GraphQL Naive ORM Implementation

## Purpose

This is an **intentionally naive implementation** that demonstrates **N+1 query problems** in gqlgen GraphQL with GORM. It shows what happens when you don't use Preload or DataLoaders.

Use this alongside the optimized gqlgen implementations to compare performance and understand the impact of proper ORM patterns.

## Key N+1 Patterns

### 1. **Lazy Loading in GraphQL Resolvers**

Instead of using Preload for eager loading, each field resolver makes a separate database query:

```go
// NAIVE: Called once per user in result set (N+1 problem!)
func (r *userResolver) Posts(ctx context.Context, obj *model.User) ([]*model.Post, error) {
    var posts []*model.Post
    if err := model.DB.Where("author_id = ?", obj.ID).Find(&posts).Error; err != nil {
        return nil, err
    }
    return posts, nil
}
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

### 3. **Field Resolver Explosion**

When querying users with posts and comments:

```graphql
{
  users {
    id
    posts {
      title
      comments {
        content
        author {
          username
        }
      }
    }
  }
}
```

**Naive Implementation:**
- `users` query: 1 query (get users)
- `posts` resolver: N queries (one per user)
- `comments` resolver: N×M queries (one per post)
- `author` resolver: N×M queries (one per comment)

**Total: 1 + N + (N×M) + (N×M) queries!**

## N+1 Problem Demonstration

### **Query: Get Users with Posts**
```graphql
{
  users(limit: 10) {
    id
    username
    posts {
      title
    }
  }
}
```

**Naive Version:**
```
Database Queries:
1. SELECT * FROM tb_user LIMIT 10 (get users)
2. SELECT * FROM tb_post WHERE author_id = ? (per user - 10 queries)

Total: 11 queries
Example: 10 users = 11 queries
```

**Optimized Version (with Preload):**
```
Database Queries:
1. SELECT * FROM tb_user u LEFT JOIN tb_post p ON u.id = p.author_id LIMIT 10

Total: 1 query
```

### **Query: Get Posts with Authors and Comments**
```graphql
{
  posts(limit: 10) {
    id
    title
    author {
      username
    }
    comments {
      content
    }
  }
}
```

**Naive Version:**
```
Database Queries:
1. SELECT * FROM tb_post LIMIT 10 (get posts)
2. SELECT * FROM tb_user WHERE id = ? (per post - 10 queries)
3. SELECT * FROM tb_comment WHERE post_id = ? (per post - 10 queries)

Total: 21 queries
Example: 10 posts = 21 queries
```

## Performance Impact

| Query Type | Data Size | Naive Queries | Optimized Queries | Slowdown Factor |
|------------|-----------|---------------|-------------------|-----------------|
| Users + Posts | 10 users | 11 queries | 1 query | ~11x slower |
| Posts + Author | 10 posts | 11 queries | 1 query | ~11x slower |
| Posts + Comments | 10 posts | 11 queries | 1 query | ~11x slower |
| Full nested query | 10 users, 2 posts each, 3 comments each | 71 queries | 3 queries | ~24x slower |

## Setup & Testing

### 1. Install Dependencies
```bash
cd frameworks-orm/gqlgen-orm-naive
go mod tidy
```

### 2. Generate GraphQL Code
```bash
go run github.com/99designs/gqlgen generate
```

### 3. Enable Query Logging
GORM logging is enabled in the database configuration:
```go
Logger: logger.Default.LogMode(logger.Info) // Shows all queries!
```

### 4. Start Server
```bash
go run cmd/server/main.go
# Server runs on http://localhost:8080
```

### 5. Test N+1 Problem
Open GraphQL playground at `http://localhost:8080` and run:

```graphql
# Test that will show N+1 problem
{
  users(limit: 5) {
    id
    username
    posts {
      title
      comments {
        content
        author {
          username
        }
      }
    }
  }
}

# Watch the console logs - you should see many individual SELECT queries
```

### 6. Compare with Optimized Version
Compare the query logs with an optimized gqlgen implementation that uses Preload.

## What Makes This "Naive"

1. **No Preload**: All GORM queries use default lazy loading
2. **Lazy Loading Reliance**: Relationships loaded on-demand
3. **Individual Queries**: Each field resolver hits database separately
4. **No Batch Loading**: No optimization for multiple similar queries

## Educational Value

This implementation teaches:
- Why GraphQL field resolvers can cause N+1 problems
- How GORM Preload prevents lazy loading issues
- gqlgen field resolver performance implications
- Go ORM lazy vs eager loading trade-offs
- Real-world impact of GraphQL query optimization

## Comparison with Optimized Version

| Aspect | Naive (This) | Optimized (with Preload) |
|--------|--------------|--------------------------|
| **Queries** | 1+N+(N×M) | 1-3 (fixed) |
| **Performance** | Slow (seconds) | Fast (milliseconds) |
| **Code Complexity** | Simple | More complex (Preload management) |
| **Scalability** | Poor | Excellent |
| **Use Case** | Learning anti-patterns | Production GraphQL APIs |

## Lessons Learned

- Always use GORM Preload for GraphQL field resolvers that access related data
- Set up Preload strategically based on query patterns
- Monitor GORM query logs for N+1 patterns
- Use batch loading techniques for GraphQL APIs
- Field resolvers should be designed for performance

---

**Remember**: This implementation is intentionally bad! Never use these patterns in production. Compare it with Preload implementations to understand why eager loading matters.</content>
<parameter name="filePath">frameworks-orm/gqlgen-orm-naive/README.md