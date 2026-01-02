# Phase 6: Go Framework Implementations

## Objective

Implement gqlgen (GraphQL) and Gin (REST) frameworks in Go, showcasing true concurrency without GIL limitations, compiled performance, and production-grade connection pooling with pgx.

## Context

**Current State:**
- Only interpreted languages (Python, planned Node.js)
- Cannot demonstrate compiled language performance advantages
- Go's goroutine model ideal for high-concurrency benchmarks
- gqlgen is the most performant Go GraphQL implementation

**Target State:**
- gqlgen with DataLoader pattern implementation
- Gin REST with pgxpool connection management
- Demonstrate Go's superior throughput under load
- Fair comparison showing language runtime differences

## Files to Create

| File | Purpose |
|------|---------|
| `frameworks/go-gqlgen/` | gqlgen GraphQL implementation |
| `frameworks/go-gqlgen/go.mod` | Go module definition |
| `frameworks/go-gqlgen/gqlgen.yml` | gqlgen configuration |
| `frameworks/go-gqlgen/graph/schema.graphqls` | GraphQL schema |
| `frameworks/go-gqlgen/graph/model/models.go` | Data models |
| `frameworks/go-gqlgen/graph/resolver.go` | Resolver implementation |
| `frameworks/go-gqlgen/graph/dataloader.go` | DataLoader implementation |
| `frameworks/go-gqlgen/internal/db/db.go` | Database pool |
| `frameworks/go-gqlgen/cmd/server/main.go` | Entry point |
| `frameworks/go-gqlgen/Dockerfile` | Container build |
| `frameworks/gin-rest/` | Gin REST implementation |
| `frameworks/gin-rest/go.mod` | Go module definition |
| `frameworks/gin-rest/internal/handlers/` | REST handlers |
| `frameworks/gin-rest/internal/db/db.go` | Database pool |
| `frameworks/gin-rest/cmd/server/main.go` | Entry point |
| `frameworks/gin-rest/Dockerfile` | Container build |

## Implementation Steps

### Step 1: Go Module Setup for gqlgen

```go
// frameworks/go-gqlgen/go.mod
module github.com/benchmark/go-gqlgen

go 1.22

require (
    github.com/99designs/gqlgen v0.17.43
    github.com/vektah/gqlparser/v2 v2.5.11
    github.com/jackc/pgx/v5 v5.5.3
    github.com/graph-gophers/dataloader/v7 v7.1.0
    github.com/prometheus/client_golang v1.18.0
)
```

```yaml
# frameworks/go-gqlgen/gqlgen.yml
schema:
  - graph/schema.graphqls

exec:
  filename: graph/generated.go
  package: graph

model:
  filename: graph/model/models_gen.go
  package: model

resolver:
  layout: follow-schema
  dir: graph
  package: graph
  filename_template: "{name}.resolvers.go"

autobind:
  - "github.com/benchmark/go-gqlgen/graph/model"

models:
  ID:
    model:
      - github.com/99designs/gqlgen/graphql.ID
  Int:
    model:
      - github.com/99designs/gqlgen/graphql.Int
```

### Step 2: GraphQL Schema

```graphql
# frameworks/go-gqlgen/graph/schema.graphqls
type User {
  id: ID!
  username: String!
  firstName: String
  lastName: String
  bio: String
  posts(limit: Int = 10): [Post!]!
  followerCount: Int!
}

type Post {
  id: ID!
  title: String!
  content: String
  author: User!
  comments(limit: Int = 10): [Comment!]!
}

type Comment {
  id: ID!
  content: String!
  author: User!
  post: Post!
}

type Query {
  ping: String!
  user(id: ID!): User
  users(limit: Int = 10): [User!]!
  post(id: ID!): Post
  posts(limit: Int = 10): [Post!]!
  comment(id: ID!): Comment
  comments(limit: Int = 10): [Comment!]!
}

type Mutation {
  updateUser(id: ID!, firstName: String, lastName: String, bio: String): User
}
```

### Step 3: Database Connection Pool (pgx)

```go
// frameworks/go-gqlgen/internal/db/db.go
package db

import (
    "context"
    "fmt"
    "os"
    "time"

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

    // Connection pool settings
    config.MinConns = 10
    config.MaxConns = 100
    config.MaxConnLifetime = 30 * time.Minute
    config.MaxConnIdleTime = 5 * time.Minute
    config.HealthCheckPeriod = 1 * time.Minute

    // Create pool
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    pool, err := pgxpool.NewWithConfig(ctx, config)
    if err != nil {
        return fmt.Errorf("create pool: %w", err)
    }

    Pool = pool
    return nil
}

func Close() {
    if Pool != nil {
        Pool.Close()
    }
}

func getEnv(key, defaultVal string) string {
    if val := os.Getenv(key); val != "" {
        return val
    }
    return defaultVal
}
```

### Step 4: DataLoader Implementation

```go
// frameworks/go-gqlgen/graph/dataloader.go
package graph

import (
    "context"
    "time"

    "github.com/benchmark/go-gqlgen/graph/model"
    "github.com/benchmark/go-gqlgen/internal/db"
    "github.com/graph-gophers/dataloader/v7"
)

type Loaders struct {
    UserLoader          *dataloader.Loader[string, *model.User]
    PostsByAuthorLoader *dataloader.Loader[string, []*model.Post]
    CommentsByPostLoader *dataloader.Loader[string, []*model.Comment]
    FollowerCountLoader *dataloader.Loader[string, int]
}

func NewLoaders() *Loaders {
    return &Loaders{
        UserLoader: dataloader.NewBatchedLoader(
            batchUsers,
            dataloader.WithWait[string, *model.User](2*time.Millisecond),
            dataloader.WithBatchCapacity[string, *model.User](100),
        ),
        PostsByAuthorLoader: dataloader.NewBatchedLoader(
            batchPostsByAuthor,
            dataloader.WithWait[string, []*model.Post](2*time.Millisecond),
            dataloader.WithBatchCapacity[string, []*model.Post](100),
        ),
        CommentsByPostLoader: dataloader.NewBatchedLoader(
            batchCommentsByPost,
            dataloader.WithWait[string, []*model.Comment](2*time.Millisecond),
            dataloader.WithBatchCapacity[string, []*model.Comment](100),
        ),
        FollowerCountLoader: dataloader.NewBatchedLoader(
            batchFollowerCounts,
            dataloader.WithWait[string, int](2*time.Millisecond),
            dataloader.WithBatchCapacity[string, int](100),
        ),
    }
}

func batchUsers(ctx context.Context, keys []string) []*dataloader.Result[*model.User] {
    results := make([]*dataloader.Result[*model.User], len(keys))

    rows, err := db.Pool.Query(ctx, `
        SELECT id, username, first_name, last_name, bio
        FROM benchmark.users
        WHERE id = ANY($1)
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
        var firstName, lastName, bio *string
        if err := rows.Scan(&u.ID, &u.Username, &firstName, &lastName, &bio); err != nil {
            continue
        }
        if firstName != nil {
            u.FirstName = firstName
        }
        if lastName != nil {
            u.LastName = lastName
        }
        if bio != nil {
            u.Bio = bio
        }
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

func batchPostsByAuthor(ctx context.Context, authorIDs []string) []*dataloader.Result[[]*model.Post] {
    results := make([]*dataloader.Result[[]*model.Post], len(authorIDs))

    rows, err := db.Pool.Query(ctx, `
        SELECT id, author_id, title, content
        FROM benchmark.posts
        WHERE author_id = ANY($1) AND status = 'published'
        ORDER BY created_at DESC
    `, authorIDs)
    if err != nil {
        for i := range results {
            results[i] = &dataloader.Result[[]*model.Post]{Error: err}
        }
        return results
    }
    defer rows.Close()

    postMap := make(map[string][]*model.Post)
    for rows.Next() {
        var p model.Post
        var authorID string
        var content *string
        if err := rows.Scan(&p.ID, &authorID, &p.Title, &content); err != nil {
            continue
        }
        if content != nil {
            p.Content = content
        }
        postMap[authorID] = append(postMap[authorID], &p)
    }

    for i, authorID := range authorIDs {
        posts := postMap[authorID]
        if posts == nil {
            posts = []*model.Post{}
        }
        results[i] = &dataloader.Result[[]*model.Post]{Data: posts}
    }

    return results
}

func batchCommentsByPost(ctx context.Context, postIDs []string) []*dataloader.Result[[]*model.Comment] {
    results := make([]*dataloader.Result[[]*model.Comment], len(postIDs))

    rows, err := db.Pool.Query(ctx, `
        SELECT id, post_id, author_id, content
        FROM benchmark.comments
        WHERE post_id = ANY($1) AND is_approved = true
        ORDER BY created_at DESC
    `, postIDs)
    if err != nil {
        for i := range results {
            results[i] = &dataloader.Result[[]*model.Comment]{Error: err}
        }
        return results
    }
    defer rows.Close()

    commentMap := make(map[string][]*model.Comment)
    for rows.Next() {
        var c model.Comment
        var postID, authorID string
        if err := rows.Scan(&c.ID, &postID, &authorID, &c.Content); err != nil {
            continue
        }
        c.AuthorID = authorID
        commentMap[postID] = append(commentMap[postID], &c)
    }

    for i, postID := range postIDs {
        comments := commentMap[postID]
        if comments == nil {
            comments = []*model.Comment{}
        }
        results[i] = &dataloader.Result[[]*model.Comment]{Data: comments}
    }

    return results
}

func batchFollowerCounts(ctx context.Context, userIDs []string) []*dataloader.Result[int] {
    results := make([]*dataloader.Result[int], len(userIDs))

    rows, err := db.Pool.Query(ctx, `
        SELECT following_id, COUNT(*)::int
        FROM benchmark.user_follows
        WHERE following_id = ANY($1)
        GROUP BY following_id
    `, userIDs)
    if err != nil {
        for i := range results {
            results[i] = &dataloader.Result[int]{Error: err}
        }
        return results
    }
    defer rows.Close()

    countMap := make(map[string]int)
    for rows.Next() {
        var userID string
        var count int
        if err := rows.Scan(&userID, &count); err != nil {
            continue
        }
        countMap[userID] = count
    }

    for i, userID := range userIDs {
        results[i] = &dataloader.Result[int]{Data: countMap[userID]}
    }

    return results
}

// Context key for dataloaders
type loadersKey struct{}

func WithLoaders(ctx context.Context, loaders *Loaders) context.Context {
    return context.WithValue(ctx, loadersKey{}, loaders)
}

func GetLoaders(ctx context.Context) *Loaders {
    return ctx.Value(loadersKey{}).(*Loaders)
}
```

### Step 5: Resolver Implementation

```go
// frameworks/go-gqlgen/graph/resolver.go
package graph

import (
    "context"

    "github.com/benchmark/go-gqlgen/graph/model"
    "github.com/benchmark/go-gqlgen/internal/db"
)

type Resolver struct{}

// Query resolvers
func (r *queryResolver) Ping(ctx context.Context) (string, error) {
    return "pong", nil
}

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
        FROM benchmark.users
        ORDER BY created_at DESC
        LIMIT $1
    `, lim)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var users []*model.User
    for rows.Next() {
        var u model.User
        var firstName, lastName, bio *string
        if err := rows.Scan(&u.ID, &u.Username, &firstName, &lastName, &bio); err != nil {
            continue
        }
        u.FirstName = firstName
        u.LastName = lastName
        u.Bio = bio
        users = append(users, &u)
    }

    return users, nil
}

func (r *queryResolver) Post(ctx context.Context, id string) (*model.Post, error) {
    row := db.Pool.QueryRow(ctx, `
        SELECT id, author_id, title, content
        FROM benchmark.posts
        WHERE id = $1
    `, id)

    var p model.Post
    var content *string
    if err := row.Scan(&p.ID, &p.AuthorID, &p.Title, &content); err != nil {
        return nil, nil
    }
    p.Content = content
    return &p, nil
}

func (r *queryResolver) Posts(ctx context.Context, limit *int) ([]*model.Post, error) {
    lim := 10
    if limit != nil {
        lim = *limit
    }

    rows, err := db.Pool.Query(ctx, `
        SELECT id, author_id, title, content
        FROM benchmark.posts
        WHERE status = 'published'
        ORDER BY created_at DESC
        LIMIT $1
    `, lim)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var posts []*model.Post
    for rows.Next() {
        var p model.Post
        var content *string
        if err := rows.Scan(&p.ID, &p.AuthorID, &p.Title, &content); err != nil {
            continue
        }
        p.Content = content
        posts = append(posts, &p)
    }

    return posts, nil
}

// User field resolvers
func (r *userResolver) Posts(ctx context.Context, obj *model.User, limit *int) ([]*model.Post, error) {
    loaders := GetLoaders(ctx)
    posts, err := loaders.PostsByAuthorLoader.Load(ctx, obj.ID)()
    if err != nil {
        return nil, err
    }

    lim := 10
    if limit != nil {
        lim = *limit
    }
    if len(posts) > lim {
        posts = posts[:lim]
    }
    return posts, nil
}

func (r *userResolver) FollowerCount(ctx context.Context, obj *model.User) (int, error) {
    loaders := GetLoaders(ctx)
    return loaders.FollowerCountLoader.Load(ctx, obj.ID)()
}

// Post field resolvers
func (r *postResolver) Author(ctx context.Context, obj *model.Post) (*model.User, error) {
    loaders := GetLoaders(ctx)
    return loaders.UserLoader.Load(ctx, obj.AuthorID)()
}

func (r *postResolver) Comments(ctx context.Context, obj *model.Post, limit *int) ([]*model.Comment, error) {
    loaders := GetLoaders(ctx)
    comments, err := loaders.CommentsByPostLoader.Load(ctx, obj.ID)()
    if err != nil {
        return nil, err
    }

    lim := 10
    if limit != nil {
        lim = *limit
    }
    if len(comments) > lim {
        comments = comments[:lim]
    }
    return comments, nil
}

// Comment field resolvers
func (r *commentResolver) Author(ctx context.Context, obj *model.Comment) (*model.User, error) {
    loaders := GetLoaders(ctx)
    return loaders.UserLoader.Load(ctx, obj.AuthorID)()
}

// Mutation resolvers
func (r *mutationResolver) UpdateUser(ctx context.Context, id string, firstName *string, lastName *string, bio *string) (*model.User, error) {
    // Build dynamic update query
    query := "UPDATE benchmark.users SET updated_at = NOW()"
    args := []interface{}{}
    argIdx := 1

    if firstName != nil {
        query += fmt.Sprintf(", first_name = $%d", argIdx)
        args = append(args, *firstName)
        argIdx++
    }
    if lastName != nil {
        query += fmt.Sprintf(", last_name = $%d", argIdx)
        args = append(args, *lastName)
        argIdx++
    }
    if bio != nil {
        query += fmt.Sprintf(", bio = $%d", argIdx)
        args = append(args, *bio)
        argIdx++
    }

    query += fmt.Sprintf(" WHERE id = $%d", argIdx)
    args = append(args, id)

    _, err := db.Pool.Exec(ctx, query, args...)
    if err != nil {
        return nil, err
    }

    // Return updated user via dataloader
    loaders := GetLoaders(ctx)
    loaders.UserLoader.Clear(ctx, id)  // Clear cache
    return loaders.UserLoader.Load(ctx, id)()
}

type queryResolver struct{ *Resolver }
type mutationResolver struct{ *Resolver }
type userResolver struct{ *Resolver }
type postResolver struct{ *Resolver }
type commentResolver struct{ *Resolver }
```

### Step 6: Main Entry Point

```go
// frameworks/go-gqlgen/cmd/server/main.go
package main

import (
    "log"
    "net/http"
    "os"

    "github.com/99designs/gqlgen/graphql/handler"
    "github.com/99designs/gqlgen/graphql/playground"
    "github.com/prometheus/client_golang/prometheus/promhttp"

    "github.com/benchmark/go-gqlgen/graph"
    "github.com/benchmark/go-gqlgen/internal/db"
)

func main() {
    // Initialize database pool
    if err := db.Init(); err != nil {
        log.Fatalf("Failed to initialize database: %v", err)
    }
    defer db.Close()

    // Create GraphQL server
    srv := handler.NewDefaultServer(graph.NewExecutableSchema(graph.Config{
        Resolvers: &graph.Resolver{},
    }))

    // Middleware to inject dataloaders per request
    http.Handle("/graphql", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        loaders := graph.NewLoaders()
        ctx := graph.WithLoaders(r.Context(), loaders)
        srv.ServeHTTP(w, r.WithContext(ctx))
    }))

    // Playground
    http.Handle("/", playground.Handler("GraphQL", "/graphql"))

    // Health check
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        if err := db.Pool.Ping(r.Context()); err != nil {
            w.WriteHeader(http.StatusServiceUnavailable)
            w.Write([]byte(`{"status":"unhealthy"}`))
            return
        }
        w.Header().Set("Content-Type", "application/json")
        w.Write([]byte(`{"status":"healthy","framework":"go-gqlgen"}`))
    })

    // Prometheus metrics
    http.Handle("/metrics", promhttp.Handler())

    port := os.Getenv("PORT")
    if port == "" {
        port = "4003"
    }

    log.Printf("🚀 gqlgen server ready at http://localhost:%s", port)
    log.Fatal(http.ListenAndServe(":"+port, nil))
}
```

### Step 7: Gin REST Implementation

```go
// frameworks/gin-rest/cmd/server/main.go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "strconv"
    "strings"

    "github.com/gin-gonic/gin"
    "github.com/prometheus/client_golang/prometheus/promhttp"

    "github.com/benchmark/gin-rest/internal/db"
)

func main() {
    if err := db.Init(); err != nil {
        log.Fatalf("Failed to initialize database: %v", err)
    }
    defer db.Close()

    r := gin.Default()

    // Health check
    r.GET("/health", func(c *gin.Context) {
        if err := db.Pool.Ping(c.Request.Context()); err != nil {
            c.JSON(http.StatusServiceUnavailable, gin.H{"status": "unhealthy"})
            return
        }
        c.JSON(http.StatusOK, gin.H{"status": "healthy", "framework": "gin-rest"})
    })

    // Metrics
    r.GET("/metrics", gin.WrapH(promhttp.Handler()))

    // Ping
    r.GET("/ping", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{"message": "pong"})
    })

    // Users
    r.GET("/users", getUsers)
    r.GET("/users/:id", getUser)
    r.PUT("/users/:id", updateUser)

    // Posts
    r.GET("/posts", getPosts)
    r.GET("/posts/:id", getPost)

    port := os.Getenv("PORT")
    if port == "" {
        port = "8006"
    }

    log.Printf("🚀 Gin REST server ready at http://localhost:%s", port)
    r.Run(":" + port)
}

func getUsers(c *gin.Context) {
    limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))

    rows, err := db.Pool.Query(c.Request.Context(), `
        SELECT id, username, first_name, last_name, bio
        FROM benchmark.users
        ORDER BY created_at DESC
        LIMIT $1
    `, limit)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    defer rows.Close()

    var users []map[string]interface{}
    for rows.Next() {
        var id, username string
        var firstName, lastName, bio *string
        rows.Scan(&id, &username, &firstName, &lastName, &bio)
        users = append(users, map[string]interface{}{
            "id": id, "username": username,
            "first_name": firstName, "last_name": lastName, "bio": bio,
        })
    }

    c.JSON(http.StatusOK, users)
}

func getUser(c *gin.Context) {
    id := c.Param("id")
    include := strings.Split(c.Query("include"), ",")

    ctx := c.Request.Context()

    row := db.Pool.QueryRow(ctx, `
        SELECT id, username, first_name, last_name, bio
        FROM benchmark.users WHERE id = $1
    `, id)

    var user struct {
        ID        string  `json:"id"`
        Username  string  `json:"username"`
        FirstName *string `json:"first_name"`
        LastName  *string `json:"last_name"`
        Bio       *string `json:"bio"`
    }
    if err := row.Scan(&user.ID, &user.Username, &user.FirstName, &user.LastName, &user.Bio); err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
        return
    }

    result := gin.H{
        "id": user.ID, "username": user.Username,
        "first_name": user.FirstName, "last_name": user.LastName, "bio": user.Bio,
    }

    for _, inc := range include {
        switch inc {
        case "posts":
            result["posts"] = getPosts ByAuthor(ctx, id)
        case "followers":
            result["followers"] = getFollowers(ctx, id)
        case "following":
            result["following"] = getFollowing(ctx, id)
        }
    }

    c.JSON(http.StatusOK, result)
}

func getPostsByAuthor(ctx context.Context, authorID string) []map[string]interface{} {
    rows, _ := db.Pool.Query(ctx, `
        SELECT id, title, content FROM benchmark.posts
        WHERE author_id = $1 AND status = 'published'
        ORDER BY created_at DESC LIMIT 10
    `, authorID)
    defer rows.Close()

    var posts []map[string]interface{}
    for rows.Next() {
        var id, title string
        var content *string
        rows.Scan(&id, &title, &content)
        posts = append(posts, map[string]interface{}{"id": id, "title": title, "content": content})
    }
    return posts
}

// Additional handlers follow similar pattern...
```

### Step 8: Dockerfiles

```dockerfile
# frameworks/go-gqlgen/Dockerfile
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /server ./cmd/server

FROM alpine:3.19
RUN apk --no-cache add ca-certificates
COPY --from=builder /server /server

EXPOSE 4003
CMD ["/server"]
```

```dockerfile
# frameworks/gin-rest/Dockerfile
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /server ./cmd/server

FROM alpine:3.19
RUN apk --no-cache add ca-certificates
COPY --from=builder /server /server

EXPOSE 8006
CMD ["/server"]
```

### Step 9: Docker Compose Updates

```yaml
# docker-compose.yml additions
go-gqlgen:
  build: ./frameworks/go-gqlgen
  ports:
    - "4003:4003"
  environment:
    - DB_HOST=postgres
    - DB_PORT=5432
    - DB_NAME=fraiseql_benchmark
    - DB_USER=benchmark
    - DB_PASSWORD=benchmark123
    - PORT=4003
  depends_on:
    - postgres
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:4003/health"]
    interval: 10s
    timeout: 5s
    retries: 5

gin-rest:
  build: ./frameworks/gin-rest
  ports:
    - "8006:8006"
  environment:
    - DB_HOST=postgres
    - DB_PORT=5432
    - DB_NAME=fraiseql_benchmark
    - DB_USER=benchmark
    - DB_PASSWORD=benchmark123
    - PORT=8006
  depends_on:
    - postgres
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:8006/health"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Verification Commands

```bash
# Build Go services
docker-compose build go-gqlgen gin-rest
docker-compose up -d go-gqlgen gin-rest

# Test gqlgen
curl -X POST http://localhost:4003/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user(id: \"00000001-1111-1111-1111-111111111111\") { id username posts { title } followerCount } }"}'

# Test Gin REST
curl "http://localhost:8006/users/00000001-1111-1111-1111-111111111111?include=posts,followers"

# Check health
curl http://localhost:4003/health
curl http://localhost:8006/health

# Benchmark throughput (expect significantly higher than Python)
ab -n 10000 -c 100 -p query.json -T application/json http://localhost:4003/graphql
```

## Acceptance Criteria

- [ ] gqlgen starts and responds to GraphQL queries
- [ ] Gin REST starts and responds to REST endpoints
- [ ] DataLoader batches related entity lookups
- [ ] pgxpool configured (min 10, max 100 connections)
- [ ] Compiled binaries < 20MB each
- [ ] Health and metrics endpoints functional
- [ ] Throughput significantly higher than Python equivalents (3-10x expected)

## DO NOT

- Use database/sql (use pgx directly for performance)
- Create goroutines per request without pooling
- Skip DataLoader implementation
- Use reflection-heavy JSON marshaling (use code generation)
- Ignore context cancellation

## Performance Expectations

| Framework | Expected RPS (100 concurrent) | vs Python |
|-----------|------------------------------|-----------|
| gqlgen | 5,000-10,000 | 5-10x faster |
| Gin REST | 8,000-15,000 | 5-10x faster |

Go's advantages:
- No GIL - true parallelism
- Compiled native code
- Efficient memory management
- Goroutine-based concurrency

## Estimated Complexity

**High** - Requires Go expertise, gqlgen code generation, and understanding of DataLoader batching patterns.
