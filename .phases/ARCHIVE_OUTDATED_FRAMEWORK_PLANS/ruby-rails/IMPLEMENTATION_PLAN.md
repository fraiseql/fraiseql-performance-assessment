# Ruby on Rails REST & GraphQL Implementation Plan

## 📋 Overview

Implement Rails-based benchmarking to establish Ruby interpreter performance baseline, demonstrate ActiveRecord ORM characteristics, and provide comparison with modern async frameworks.

---

## 🎯 What Rails Demonstrates

- **Dynamic language interpreter overhead** (Ruby without JIT)
- **ActiveRecord ORM characteristics** (vs SQLAlchemy)
- **Thread-based concurrency** with global interpreter lock
- **"Convention over configuration"** framework overhead
- **Full-stack framework patterns** (Rails is comprehensive)

---

## 🏗️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | Rails | 7.1.x |
| **ORM** | ActiveRecord | 7.1.x |
| **GraphQL** | graphql-ruby | 2.2.x |
| **Server** | Puma | 6.x |
| **Database Driver** | pg | 1.5.x |
| **JSON API** | jsonapi-rails | Latest |
| **Metrics** | prometheus-client | Latest |
| **Base Image** | ruby:3.3-alpine | Latest |

---

## 📝 Implementation Phases (8 phases, ~35 hours)

### Phase 1: Rails Project Setup
**Duration**: 1-2 hours

```bash
rails new fraiseql-benchmark --api --database=postgresql
cd fraiseql-benchmark
bundle add graphql
bundle add prometheus-client
```

---

### Phase 2: ActiveRecord Models
**Duration**: 2-3 hours

Generate models with relationships:
```ruby
# User model
class User < ApplicationRecord
  has_many :posts, foreign_key: 'author_id'
  has_many :comments, foreign_key: 'author_id'
  validates :username, presence: true, uniqueness: true
end

# Post model with eager loading
class Post < ApplicationRecord
  belongs_to :author, class_name: 'User', foreign_key: 'author_id'
  has_many :comments
end
```

---

### Phase 3: REST Controllers
**Duration**: 2-3 hours

Create Rails controllers:
```ruby
class UsersController < ApplicationController
  def show
    @user = User.find(params[:id])
    render json: @user
  end

  def index
    @users = User.limit(params[:limit] || 10)
      .offset(params[:offset] || 0)
    render json: @users
  end
end
```

---

### Phase 4: GraphQL Schema
**Duration**: 2-3 hours

Define GraphQL types:
```ruby
module Types
  class UserType < Types::BaseObject
    field :id, ID, null: false
    field :username, String, null: false
    field :first_name, String, null: false
    field :posts, [Types::PostType], null: false
  end

  class QueryType < Types::BaseObject
    field :user, Types::UserType, null: true do
      argument :id, ID, required: true
    end
    def user(id:)
      User.find(id)
    end
  end
end
```

---

### Phase 5: Database Connection Pool
**Duration**: 1-2 hours

Configure connection pooling in database.yml:
```yaml
production:
  adapter: postgresql
  database: fraiseql_benchmark
  host: postgres
  pool: 20
  timeout: 10000
```

---

### Phase 6: Prometheus Metrics
**Duration**: 1-2 hours

Add metrics middleware:
```ruby
require 'prometheus/client'
require 'prometheus/client/push'

class MetricsMiddleware
  def initialize(app)
    @app = app
  end

  def call(env)
    status, headers, body = @app.call(env)
    # Track metrics
    [status, headers, body]
  end
end
```

---

### Phase 7: Puma Configuration
**Duration**: 1-2 hours

Configure Puma for performance:
```ruby
workers ENV.fetch("WEB_CONCURRENCY") { 4 }
threads 5, 25
```

---

### Phase 8: Docker & Integration
**Duration**: 1-2 hours

```dockerfile
FROM ruby:3.3-alpine
RUN apk add --no-cache postgresql-client postgresql-dev
WORKDIR /app
COPY Gemfile .
RUN bundle install
COPY . .
EXPOSE 8010
CMD ["bundle", "exec", "puma", "-b", "tcp://0.0.0.0:8010"]
```

Add to docker-compose.yml (port 8010)

---

## 🎯 Performance Targets

| Metric | Target |
|--------|--------|
| **P50 Latency** | 100-180ms |
| **P99 Latency** | 200-400ms |
| **Throughput** | 400-600 req/s |
| **Memory** | 300-500MB |

---

## 📊 Story

Rails demonstrates:
- Interpreter-level performance overhead
- ActiveRecord N+1 query impact
- Thread-based concurrency limitations
- Full-framework overhead vs microframeworks

---

## ✅ Checklist

- [ ] Rails project created
- [ ] Models with associations
- [ ] REST controllers functional
- [ ] GraphQL schema working
- [ ] Connection pooling configured
- [ ] Metrics functional
- [ ] Docker image builds
- [ ] Integration tests pass

---

**Version**: 1.0 | **Status**: Ready | **Hours**: 35
