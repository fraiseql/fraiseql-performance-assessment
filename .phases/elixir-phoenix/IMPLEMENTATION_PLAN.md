# Elixir Phoenix REST & GraphQL Implementation Plan

## 📋 Overview

Implement Elixir/Phoenix frameworks to demonstrate actor-based concurrency model, BEAM VM characteristics, and functional programming approach to API development - unique performance story not captured by other languages.

---

## 🎯 What Elixir Demonstrates

- **Actor-based concurrency** (lightweight processes, not threads)
- **BEAM VM characteristics** (garbage collection, distribution)
- **Functional programming patterns** (immutability, pattern matching)
- **Hot code reloading** capability
- **Fault tolerance** through supervision trees
- **Distributed-by-default** architecture

**Unique Value**: Elixir is orthogonal to everything else - different concurrency model, different runtime, different language paradigm.

---

## 🏗️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | Phoenix | 1.7.x |
| **Language** | Elixir | 1.16.x |
| **GraphQL** | Absinthe | 1.7.x |
| **ORM** | Ecto | 3.x |
| **Database Driver** | Postgrex | 0.18.x |
| **Metrics** | Prometheus exporter | Latest |
| **Base Image** | elixir:1.16-alpine | Latest |

---

## 📝 Implementation Phases (7 phases, ~25 hours)

### Phase 1: Phoenix Project Setup
**Duration**: 1-2 hours

```bash
mix phx.new fraiseql_benchmark --no-mailer --api
cd fraiseql_benchmark
mix deps.get
mix ecto.setup
```

Add dependencies:
```elixir
{:absinthe, "~> 1.7"},
{:absinthe_plug, "~> 1.5"},
{:prometheus_ex, "~> 3.0"}
```

---

### Phase 2: Ecto Schemas
**Duration**: 1-2 hours

Define schemas (Elixir's approach to models):
```elixir
defmodule FraiseqlBenchmark.Schema.User do
  use Ecto.Schema

  schema "tb_user" do
    field :username, :string
    field :first_name, :string
    field :last_name, :string
    field :bio, :string

    has_many :posts, FraiseqlBenchmark.Schema.Post, foreign_key: :author_id
    has_many :comments, FraiseqlBenchmark.Schema.Comment, foreign_key: :author_id

    timestamps()
  end
end
```

---

### Phase 3: Ecto Queries & Repositories
**Duration**: 1-2 hours

Define query functions:
```elixir
defmodule FraiseqlBenchmark.Repo.User do
  import Ecto.Query
  alias FraiseqlBenchmark.Schema.User

  def get_by_id(id) do
    Repo.get(User, id)
  end

  def list_users(page, size) do
    Repo.all(
      from u in User,
      limit: ^size,
      offset: ^(page * size)
    )
  end
end
```

---

### Phase 4: REST Endpoints
**Duration**: 2-3 hours

Create Phoenix controllers:
```elixir
defmodule FraiseqlBenchmarkWeb.UserController do
  use FraiseqlBenchmarkWeb, :controller

  def show(conn, %{"id" => id}) do
    user = Repo.User.get_by_id(id)
    render(conn, :show, user: user)
  end

  def index(conn, params) do
    page = String.to_integer(params["page"] || "0")
    size = String.to_integer(params["size"] || "10")
    users = Repo.User.list_users(page, size)
    render(conn, :index, users: users)
  end
end
```

---

### Phase 5: Absinthe GraphQL Schema
**Duration**: 2-3 hours

Define GraphQL schema:
```elixir
defmodule FraiseqlBenchmarkWeb.Schema do
  use Absinthe.Schema

  object :user do
    field :id, :id
    field :username, :string
    field :first_name, :string
    field :last_name, :string
    field :bio, :string
    field :posts, list_of(:post)
  end

  query do
    field :user, :user do
      arg :id, :id
      resolve fn _obj, %{id: id}, _info ->
        {:ok, Repo.User.get_by_id(id)}
      end
    end

    field :users, list_of(:user) do
      arg :first, :integer
      arg :after, :string
      resolve fn _obj, args, _info ->
        {:ok, Repo.User.list_users(0, args[:first] || 10)}
      end
    end
  end
end
```

---

### Phase 6: Prometheus Metrics
**Duration**: 1-2 hours

Add metrics collection:
```elixir
defmodule FraiseqlBenchmark.Metrics do
  require Prometheus.Registry

  def setup do
    Prometheus.Registry.register_collector(:prometheus_registry)
  end

  defmodule RequestCounter do
    use Prometheus.Metric

    def setup do
      Counter.declare([name: :request_total, help: "Total requests"])
    end
  end
end
```

---

### Phase 7: Docker & Integration
**Duration**: 1-2 hours

```dockerfile
FROM elixir:1.16-alpine

RUN apk add --no-cache postgresql-client

WORKDIR /app
COPY . .

RUN mix local.hex --force
RUN mix deps.get --only prod
RUN mix compile

EXPOSE 8011
CMD ["mix", "phx.server"]
```

Add to docker-compose.yml (port 8011)

---

## 🎯 Performance Targets

| Metric | Target | Why |
|--------|--------|-----|
| **P50 Latency** | 15-30ms | BEAM VM efficiency |
| **P99 Latency** | 40-80ms | Lightweight processes |
| **Throughput** | 3000-5000 req/s | Thousands of processes |
| **Memory** | 200-400MB | Process overhead |

---

## 📊 Unique Story

Elixir demonstrates:
- Actor model efficiency (million lightweight processes)
- BEAM VM characteristics (different GC than Java/Python)
- Functional programming impact on performance
- Fault tolerance without performance penalty
- Hot code reloading capability

---

## 🎓 Learning Value

Elixir is fundamentally different:
- **Concurrency**: Actors vs threads vs async/await
- **Memory**: Each process has own heap
- **Distribution**: Built-in distributed semantics
- **Fault Tolerance**: "Let it crash" philosophy

---

## ✅ Checklist

- [ ] Phoenix project created
- [ ] Ecto schemas defined
- [ ] REST endpoints working
- [ ] Absinthe GraphQL schema
- [ ] Query functions functional
- [ ] Metrics setup
- [ ] Docker image builds
- [ ] Integration tests pass

---

**Version**: 1.0 | **Status**: Ready | **Hours**: 25
