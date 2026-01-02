# PHP Laravel REST & GraphQL Implementation Plan

## 📋 Overview

Implement Laravel-based benchmarking frameworks to establish PHP performance baseline, demonstrate synchronous I/O model characteristics, and provide historical reference for full-stack PHP applications.

---

## 🎯 Key Differences from Other Languages

**Synchronous I/O Model**: PHP's shared-nothing architecture and synchronous database queries create fundamentally different performance profile than async frameworks.

**Why It Matters**: Shows what happens without async/await patterns - important for developers evaluating framework choices.

---

## 🏗️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | Laravel | 11.x |
| **ORM** | Eloquent | 11.x |
| **GraphQL** | Lighthouse | 9.x |
| **Server** | Laravel Octane + Swoole | Latest |
| **Database** | PostgreSQL with PDO | 15 |
| **Cache** | Redis (optional) | Latest |
| **Metrics** | Prometheus PHP client | Latest |
| **Base Image** | php:8.3-fpm-alpine | Latest |

---

## 📝 Implementation Phases (8 phases, ~30 hours)

### Phase 1: Laravel Project Setup
**Duration**: 1-2 hours

Create Laravel project with composer:
```bash
composer create-project laravel/laravel fraiseql-benchmark
cd fraiseql-benchmark
composer require lighthouse-php/lighthouse
```

Add dependencies:
- laravel/octane (performance)
- swoole (async server)
- prometheus/client_php (metrics)

---

### Phase 2: Eloquent Models
**Duration**: 1-2 hours

Create models with relationships:
```php
class User extends Model {
    public $fillable = ['id', 'username', 'first_name', 'last_name', 'bio'];

    public function posts() {
        return $this->hasMany(Post::class, 'author_id');
    }

    public function comments() {
        return $this->hasMany(Comment::class, 'author_id');
    }
}
```

---

### Phase 3: REST Controllers
**Duration**: 2-3 hours

Create API controllers:
- UserController (GET /api/users/{id}, GET /api/users)
- PostController (GET /api/posts/{id}, GET /api/posts)
- HealthController

---

### Phase 4: Lighthouse GraphQL Schema
**Duration**: 2-3 hours

Define schema in config/lighthouse.php or graphql/schema.graphql:
```graphql
type User {
    id: ID!
    username: String!
    firstName: String!
    lastName: String!
    bio: String
    posts: [Post!]!
}

type Query {
    user(id: ID!): User
    users(first: Int, after: String): [User!]!
    post(id: ID!): Post
    posts(first: Int): [Post!]!
}
```

---

### Phase 5: Laravel Octane Configuration
**Duration**: 1-2 hours

Configure Octane for performance:
```bash
php artisan octane:install --server=swoole
```

This enables connection pooling and keeps app in memory.

---

### Phase 6: Prometheus Metrics
**Duration**: 2-3 hours

Add metrics collection:
```php
Route::get('/metrics', function() {
    $registry = new CollectorRegistry();
    $counter = $registry->getOrRegisterCounter('requests_total', ['method', 'path']);
    // ... collect metrics
    echo (new PrometheusExporter())->export($registry);
});
```

---

### Phase 7: Docker Configuration
**Duration**: 1-2 hours

```dockerfile
FROM php:8.3-fpm-alpine

RUN apk add --no-cache postgresql-dev
RUN docker-php-ext-install pdo pdo_pgsql

COPY . /app
WORKDIR /app

RUN composer install --no-dev

EXPOSE 8009
CMD ["php", "artisan", "octane:start", "--host=0.0.0.0", "--port=8009"]
```

---

### Phase 8: Integration & Testing
**Duration**: 1-2 hours

- Add to docker-compose.yml (port 8009)
- Update test scripts
- Run smoke tests

---

## 🎯 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **P50 Latency** | 80-120ms | Synchronous I/O |
| **P99 Latency** | 150-250ms | Connection pool wait time |
| **Throughput** | 500-800 req/s | Limited by sync model |
| **Memory** | 200-300MB | Per Octane worker |

---

## 📊 Unique Story

PHP demonstrates:
- Synchronous I/O performance ceiling
- How connection pools become bottleneck
- "Batteries included" framework overhead
- Database-bound application characteristics

---

## ✅ Checklist

- [ ] Laravel project created
- [ ] Eloquent models defined
- [ ] REST endpoints working
- [ ] GraphQL schema functional
- [ ] Octane configured
- [ ] Metrics endpoint working
- [ ] Docker image builds
- [ ] Integration tests pass

---

**Version**: 1.0 | **Status**: Ready | **Hours**: 30
