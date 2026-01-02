# Apollo Server Naive ORM Implementation

## Purpose

This is an **intentionally naive implementation** that demonstrates **N+1 query problems** in Apollo Server GraphQL with TypeORM. It shows what happens when you don't use DataLoaders or eager loading.

Use this alongside optimized Apollo implementations to compare performance and understand the impact of proper ORM patterns.

## Key N+1 Patterns

### 1. **Lazy Loading in GraphQL Resolvers**

Instead of using DataLoaders for batching, each field resolver makes a separate database query:

```typescript
@FieldResolver(() => [PostType])
async posts(@Root() user: UserType) {
    // NAIVE: Called once per user in result set (N+1 problem!)
    return await this.postRepository.find({
        where: { authorId: user.id }  // Individual query per user!
    });
}
```

### 2. **No Relationship Preloading**

TypeORM entities have `eager: false` which causes lazy loading on access:

```typescript
@OneToMany(() => Post, post => post.author, {
    eager: false  // This causes lazy loading!
})
posts: Post[];
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

**Optimized Version (with DataLoaders):**
```
Database Queries:
1. SELECT * FROM tb_user LIMIT 10 (get users)
2. SELECT * FROM tb_post WHERE author_id IN (...) (1 batch query)

Total: 2 queries
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
| Users + Posts | 10 users | 11 queries | 2 queries | ~5x slower |
| Posts + Author | 10 posts | 11 queries | 2 queries | ~5x slower |
| Posts + Comments | 10 posts | 11 queries | 2 queries | ~5x slower |
| Full nested query | 10 users, 2 posts each, 3 comments each | 71 queries | 4 queries | ~18x slower |

## Setup & Testing

### 1. Install Dependencies
```bash
cd frameworks-orm/apollo-orm-naive
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
# Server runs on http://localhost:4000/graphql
```

### 4. Test N+1 Problem
Open GraphQL playground at `http://localhost:4000/graphql` and run:

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

### 5. Compare with Optimized Version
Compare the query logs with an optimized Apollo implementation that uses DataLoaders.

## What Makes This "Naive"

1. **No DataLoaders**: Each field resolver hits the database individually
2. **Lazy Loading**: TypeORM relationships use `eager: false`
3. **Individual Queries**: No batching of similar requests
4. **Resolver Explosion**: Field resolvers called per entity in result

## Educational Value

This implementation teaches:
- Why GraphQL resolvers can cause N+1 problems
- How DataLoader pattern prevents N+1 queries
- TypeORM lazy vs eager loading trade-offs
- Apollo Server field resolver performance implications
- Real-world impact of GraphQL query optimization

## Comparison with Optimized Version

| Aspect | Naive (This) | Optimized (with DataLoaders) |
|--------|--------------|------------------------------|
| **Queries** | 1+N+(N×M) | 3-4 (fixed) |
| **Performance** | Slow (seconds) | Fast (milliseconds) |
| **Code Complexity** | Simple | More complex (DataLoaders) |
| **Scalability** | Poor | Excellent |
| **Use Case** | Learning anti-patterns | Production GraphQL APIs |

## Lessons Learned

- Always use DataLoaders for GraphQL field resolvers that access related data
- Set `eager: true` in TypeORM relationships when appropriate
- Monitor database query logs for N+1 patterns
- Use batch loading techniques for GraphQL APIs
- Field resolvers should be designed for batching, not individual queries

---

**Remember**: This implementation is intentionally bad! Never use these patterns in production. Compare it with DataLoader implementations to understand why batch loading matters.</content>
<parameter name="filePath">frameworks-orm/apollo-orm-naive/README.md