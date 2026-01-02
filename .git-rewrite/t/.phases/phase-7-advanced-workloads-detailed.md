# FraiseQL Performance Assessment - Phase 7: Advanced Workload Scenarios

## Phase Overview

**Goal**: Implement comprehensive workload scenarios that stress different aspects of each framework: aggregations, pagination strategies, full-text search, concurrent writes, deep relationship traversal, and mixed realistic traffic patterns.

**Scope**: Create 8 distinct workload categories with JMeter test plans, parameterized datasets, and query optimization for each framework.

**Success Criteria**:
- 8 distinct workload JMeter test plans created
- Each framework implements all required query types
- Search indexes created and functional
- Cursor-based pagination implemented
- Query count tracking for N+1 detection
- Mixed workload properly weighted

## Learning Objectives

As a junior engineer, by completing Phase 7 you will learn:

1. **Go Concurrency**: Goroutines, channels, context management
2. **Compiled Performance**: Go compilation, binary optimization, startup time
3. **pgx Driver**: PostgreSQL driver for Go, connection pooling, prepared statements
4. **gqlgen Code Generation**: GraphQL schema to Go code generation
5. **Gin Web Framework**: HTTP routing, middleware, request handling
6. **Go Tooling**: go mod, go build, cross-compilation
7. **Performance Benchmarking**: Comparing compiled vs interpreted languages

## Implementation Steps

### Step 1: gqlgen Project Setup
**Estimated Time**: 1 hour

```go
// frameworks/go-gqlgen/go.mod
module github.com/benchmark/go-gqlgen

go 1.22

require (
    github.com/99designs/gqlgen v0.17.43
    github.com/jackc/pgx/v5 v5.5.3
    github.com/graph-gophers/dataloader/v7 v7.1.0
    github.com/prometheus/client_golang v1.18.0
)
```

### Step 2: Database Connection Pool (pgx)
**Estimated Time**: 45 minutes

```go
// frameworks/go-gqlgen/internal/db/db.go
package db

import (
    "context"
    "fmt"
    "os"
    
    "github.com/jackc/pgx/v5/pgxpool"
)

var Pool *pgxpool.Pool

func Init() error {
    connStr := fmt.Sprintf(
        "postgres://%s:%s@%s:%s/%s?pool_min_conns=10&pool_max_conns=100",
        getEnv("DB_USER", "benchmark"),
        getEnv("DB_PASSWORD", "benchmark123"),
        getEnv("DB_HOST", "postgres"),
        getEnv("DB_PORT", "5432"),
        getEnv("DB_NAME", "fraiseql_benchmark"),
    )
    
    config, err := pgxpool.ParseConfig(connStr)
    if err != nil {
        return fmt.Errorf("parse config: %w", err)
    }
    
    config.MinConns = 10
    config.MaxConns = 100
    
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    
    pool, err := pgxpool.NewWithConfig(ctx, config)
    if err != nil {
        return fmt.Errorf("create pool: %w", err)
    }
    
    Pool = pool
    return nil
}
```

### Step 3: DataLoader Implementation
**Estimated Time**: 1 hour

```go
// frameworks/go-gqlgen/graph/dataloader.go
package graph

import (
    "context"
    "time"
    
    "github.com/benchmark/go-gqlgen/internal/db"
    "github.com/graph-gophers/dataloader/v7"
)

type Loaders struct {
    UserLoader *dataloader.Loader[string, *model.User]
    PostsByAuthorLoader *dataloader.Loader[string, []*model.Post]
}

func NewLoaders() *Loaders {
    return &Loaders{
        UserLoader: dataloader.NewBatchedLoader(batchUsers, 
            dataloader.WithWait[string, *model.User](2*time.Millisecond)),
        PostsByAuthorLoader: dataloader.NewBatchedLoader(batchPostsByAuthor,
            dataloader.WithWait[string, []*model.Post](2*time.Millisecond)),
    }
}

func batchUsers(ctx context.Context, keys []string) []*dataloader.Result[*model.User] {
    results := make([]*dataloader.Result[*model.User], len(keys))
    
    rows, err := db.Pool.Query(ctx, `
        SELECT id, username, first_name, last_name, bio
        FROM benchmark.users WHERE id = ANY($1)
    `, keys)
    if err != nil {
        for i := range results {
            results[i] = &dataloader.Result[*model.User]{Error: err}
        }
        return results
    }
    defer rows.Close()
    
    userMap := make(map[string]*model.User)
    for rows.Next() {
        var u model.User
        rows.Scan(&u.ID, &u.Username, &u.FirstName, &u.LastName, &u.Bio)
        userMap[u.ID] = &u
    }
    
    for i, key := range keys {
        if user, ok := userMap[key]; ok {
            results[i] = &dataloader.Result[*model.User]{Data: user}
        } else {
            results[i] = &dataloader.Result[*model.User]{Data: nil}
        }
    }
    
    return results
}
```

### Step 4: GraphQL Resolvers
**Estimated Time**: 1.5 hours

```go
// frameworks/go-gqlgen/graph/resolver.go
func (r *queryResolver) User(ctx context.Context, id string) (*model.User, error) {
    loaders := GetLoaders(ctx)
    return loaders.UserLoader.Load(ctx, id)()
}

func (r *queryResolver) Users(ctx context.Context, limit *int) ([]*model.User, error) {
    lim := 10
    if limit != nil {
        lim = *limit
    }
    
    rows, err := db.Pool.Query(ctx, `
        SELECT id, username, first_name, last_name, bio
        FROM benchmark.users ORDER BY created_at DESC LIMIT $1
    `, lim)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    var users []*model.User
    for rows.Next() {
        var u model.User
        rows.Scan(&u.ID, &u.Username, &u.FirstName, &u.LastName, &u.Bio)
        users = append(users, &u)
    }
    
    return users, nil
}

func (r *userResolver) Posts(ctx context.Context, obj *model.User, limit *int) ([]*model.Post, error) {
    loaders := GetLoaders(ctx)
    posts, err := loaders.PostsByAuthorLoader.Load(ctx, obj.ID)()
    if err != nil {
        return nil, err
    }
    
    lim := 10
    if limit != nil {
        lim = *lim
    }
    if len(posts) > lim {
        posts = posts[:lim]
    }
    return posts, nil
}
```

## Best Practices Learned

### 1. Go Performance Patterns
- Use goroutines for concurrent operations
- Implement proper context cancellation
- Use connection pooling with pgx
- Monitor goroutine leaks

### 2. Compiled Language Advantages
- Fast startup times
- Efficient memory usage
- True concurrency without GIL
- Cross-platform compilation

## Phase Sign-off

**Phase 6 Status**: ☐ Ready for Phase 7 ☐ Needs Remediation

**Frameworks Implemented**:
- gqlgen (GraphQL) - Go code generation, DataLoader, pgxpool
- Gin (REST) - High-performance HTTP routing, middleware

**Performance Validations**:
- Throughput 5-10x higher than Python frameworks
- Binary size < 20MB
- Memory usage optimized</content>
<parameter name="filePath">.phases/phase-6-go-frameworks-detailed.md