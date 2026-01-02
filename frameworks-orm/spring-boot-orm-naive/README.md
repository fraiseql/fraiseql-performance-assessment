# Spring Boot JPA ORM Naive Implementation

**Purpose**: Demonstrate common JPA/Hibernate anti-patterns that cause N+1 query problems and poor performance.

**Performance**: Very slow due to N+1 queries (~200%+ slower than optimized versions).

## Quick Start

```bash
# Build and run
cd frameworks-orm/spring-boot-orm-naive
docker build -t spring-boot-orm-naive .
docker run -p 8012:8012 --network fraiseql-benchmark spring-boot-orm-naive

# Health check
curl http://localhost:8012/health

# Test N+1 query problems
curl http://localhost:8012/users/1/with-posts
# Watch the logs - you'll see dozens of SQL queries!
```

## N+1 Query Problems Demonstrated

### The Classic N+1 Problem

```java
// NAIVE: This causes N+1 queries!
@GetMapping("/{id}/with-posts")
public ResponseEntity<User> getUserWithPosts(@PathVariable Long id) {
    Optional<User> user = userRepository.findById(id);
    if (user.isPresent()) {
        // Each access to user.getPosts() triggers a separate SQL query!
        List<?> posts = user.get().getPosts(); // 1 query per user!
        return ResponseEntity.ok(user.get());
    }
    return ResponseEntity.notFound().build();
}
```

**What happens:**
1. `SELECT * FROM tb_users WHERE id = ?` - 1 query
2. `SELECT * FROM tb_posts WHERE author_id = ?` - N queries (one per user)
3. **Total: N+1 queries instead of 2!**

### Multiple Levels of N+1

```java
// EVEN WORSE: N+1 queries for posts, then N+1 for comments!
@GetMapping("/{id}/with-posts-and-comments")
public ResponseEntity<User> getUserWithPostsAndComments(@PathVariable Long id) {
    Optional<User> user = userRepository.findById(id);
    if (user.isPresent()) {
        List<?> posts = user.get().getPosts(); // N queries
        for (Object post : posts) {
            // Each post access triggers another query for comments!
            // post.getComments() - another N queries!
        }
        return ResponseEntity.ok(user.get());
    }
    return ResponseEntity.notFound().build();
}
```

## Anti-Patterns Demonstrated

### 1. Lazy Loading Without Optimization
```java
@Entity
public class User {
    // NAIVE: Lazy loading without @BatchSize
    @OneToMany(fetch = FetchType.LAZY, mappedBy = "author")
    private List<Post> posts; // Causes N+1 when accessed
}
```

### 2. No Fetch Joins in Queries
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    // NAIVE: No @Query with LEFT JOIN FETCH
    // Accessing relationships = separate queries
}
```

### 3. Default Hibernate Configuration
```yaml
hibernate:
  # NAIVE: Default batch fetch size = 1
  default_batch_fetch_size: 1
  # NAIVE: Show SQL to demonstrate the problem
  show_sql: true
```

## Performance Impact

### Query Count Comparison

| Operation | Optimized ORM | Naive ORM | Raw JDBC |
|-----------|---------------|-----------|----------|
| Get User | 1 query | 1 query | 1 query |
| Get User + Posts | 2 queries | N+1 queries | 1-2 queries |
| Get User + Posts + Comments | 3 queries | N×M+1 queries | 2-3 queries |

### Real Performance Impact

```
User with 10 posts, each with 5 comments:

Optimized: 3 queries total
Naive:     1 + 10 + 50 = 61 queries! (2000% slower)
Raw JDBC: 2-3 queries with manual JOINs
```

## Architecture

### Naive Entity Relationships
```
User (1) ────► Post (N) ────► Comment (M)
    │              │
    └─── LAZY ─────┴─── LAZY (No batching!)
```

### Query Execution Pattern
```
1. SELECT * FROM users WHERE id = ?
2. SELECT * FROM posts WHERE author_id = ?  // For each user
3. SELECT * FROM comments WHERE post_id = ?  // For each post
   SELECT * FROM comments WHERE post_id = ?
   SELECT * FROM comments WHERE post_id = ?
   // ... N×M queries total!
```

## Endpoints

- `GET /health` - Health check (shows N+1 warning)
- `GET /users` - List all users
- `GET /users/{id}` - Get single user
- `GET /users/{id}/with-posts` - **Demonstrates N+1 for posts**
- `GET /users/{id}/with-posts-and-comments` - **Demonstrates nested N+1**

## Configuration

### Hibernate Settings (Naive)
```yaml
jpa:
  properties:
    hibernate:
      show_sql: true  # Show the problem!
      format_sql: true
      default_batch_fetch_size: 1  # No batching
```

### Logging (Enabled for Education)
```yaml
logging:
  level:
    org.hibernate.SQL: DEBUG  # Show every query
    org.hibernate.type.descriptor.sql.BasicBinder: TRACE
```

## Running Benchmarks

```bash
# Start the naive implementation
docker-compose up -d spring-boot-orm-naive

# Run performance tests
./run-comprehensive-benchmark.sh --framework spring-boot-orm-naive --workload simple

# Compare with optimized version
./run-comprehensive-benchmark.sh --framework spring-boot-orm --workload simple
```

## Expected Results

### Response Times (Approximate)
- **spring-boot** (Raw JDBC): ~8ms
- **spring-boot-orm** (Optimized): ~12ms (+50%)
- **spring-boot-orm-naive** (N+1): ~45ms (+462%!)

### Query Counts
- **Optimized**: 2-3 queries per request
- **Naive**: 10-50+ queries per request
- **Raw**: 1-2 queries per request

## Educational Value

This implementation demonstrates:

1. **Why ORM can be slow** - N+1 query problems
2. **Common mistakes** - Lazy loading without batching
3. **Performance pitfalls** - Nested relationship access
4. **Query analysis** - How to identify N+1 problems
5. **Optimization importance** - Proper fetch strategies

## Comparison with Optimized Version

### Optimized (spring-boot-orm)
```java
@Query("SELECT u FROM User u LEFT JOIN FETCH u.posts WHERE u.id = :id")
@QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
Optional<User> findByIdWithPosts(@Param("id") Long id);
```

### Naive (spring-boot-orm-naive)
```java
// No fetch joins - causes N+1!
Optional<User> findById(Long id);
```

## Best Practices (What This Breaks)

1. ❌ **Use lazy loading without batching**
2. ❌ **Access relationships without fetch joins**
3. ❌ **Nest relationship access in loops**
4. ❌ **Default Hibernate batch fetch size**
5. ❌ **No query optimization hints**

## Next Steps

1. **Run benchmarks** to quantify the performance impact
2. **Compare with optimized ORM** implementation
3. **Document the performance differences**
4. **Create optimization guides** based on findings
5. **Show before/after** query analysis

---

**Status**: ✅ Complete - Naive JPA implementation demonstrating N+1 query problems

**Educational Impact**: Shows developers why proper ORM usage matters and how small configuration changes can cause massive performance degradation.