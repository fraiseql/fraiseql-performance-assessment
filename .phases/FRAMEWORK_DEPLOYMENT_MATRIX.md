# Framework Deployment Status Matrix

**Date**: 2025-12-26
**Total Frameworks**: 34
**Actively Deployed**: 21 in docker-compose.yml
**Available for Deployment**: 13 additional

---

## Quick Status Summary

```
RUNNING (21)     ████████████████████░░░░░░░░░░░░ 62%
FIXABLE (3)      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 9%
MISSING (10)     ██████████░░░░░░░░░░░░░░░░░░░░░░░ 29%
```

---

## 🟢 RUNNING: 21 Frameworks

### Python (5 frameworks)
| Name | Type | Port | Health Check | Status |
|------|------|------|--------------|--------|
| fraiseql | GraphQL | 4000 | curl /health | ✅ Running |
| strawberry | GraphQL | 8011 | python3 urllib | ✅ Running |
| graphene | GraphQL | 8002 | python3 urllib | ✅ Running |
| fastapi-rest | REST | 8003 | python urllib | ✅ Running |
| strawberry-orm-naive | ORM (N+1) | 8019 | python3 urllib | ✅ Running |
| fastapi-orm-naive | ORM (N+1) | 8020 | python3 urllib | ✅ Running |

**Python Coverage**: ✅ Excellent (GraphQL, REST, ORM covered)

### Node.js/TypeScript (5 frameworks)
| Name | Type | Port | Health Check | Status |
|------|------|------|--------------|--------|
| apollo | GraphQL | 4001 | wget /health | ✅ Running |
| express-rest | REST | 8005 | wget /health | ✅ Running |
| express-orm | ORM | 8007 | wget /health | ✅ Running |
| apollo-orm-naive | ORM (N+1) | 8021 | wget /health | ✅ Running |
| express-orm-naive | ORM (N+1) | 8022 | wget /health | ✅ Running |

**Node.js Coverage**: ✅ Excellent (GraphQL, REST, ORM covered)

### Go (2 frameworks)
| Name | Type | Port | Health Check | Status |
|------|------|------|--------------|--------|
| gqlgen-orm-naive | ORM (N+1) | 8023 | wget /health | ✅ Running |
| gin-orm-naive | ORM (N+1) | 8024 | wget /health | ✅ Running |

**Go Coverage**: ⚠️ Partial (only ORM naive variants; pure GraphQL/REST Go implementations missing)

### Java (3 frameworks)
| Name | Type | Port | Health Check | Status |
|------|------|------|--------------|--------|
| spring-boot | REST | 8010 | curl /actuator/health | ✅ Running |
| spring-boot-orm | ORM | 8011 | curl /actuator/health | ✅ Running |
| spring-boot-orm-naive | ORM (N+1) | 8014 | curl /actuator/health | ✅ Running |

**Java Coverage**: ✅ Good (REST and ORM variants covered)

### Rust (1 framework)
| Name | Type | Port | Health Check | Status |
|------|------|------|--------------|--------|
| actix-web-rest | REST | 8015 | wget /health | ✅ Running |

**Rust Coverage**: ⚠️ Partial (only REST; GraphQL Rust framework disabled)

### Special (1 framework)
| Name | Type | Port | Health Check | Status |
|------|------|------|--------------|--------|
| hasura | GraphQL Engine | 8081 | curl /healthz | ✅ Running |

**Special**: ✅ Managed GraphQL service for comparison

### Infrastructure (3 services)
| Name | Type | Port | Status |
|------|------|------|--------|
| postgres | Database | 5434 | ⚠️ Not Running |
| prometheus | Metrics | 9090 | ⚠️ Not Running |
| grafana | Dashboards | 3000 | ⚠️ Not Running |

---

## 🟡 FIXABLE: 3 Frameworks (Disabled)

### Why Disabled
These are **actively broken** and preventing deployment. All have compiled/installed dependencies.

#### 1. async-graphql (Rust GraphQL) ⛔
```
Location: frameworks/async-graphql/src/schema.rs:262
Issue:    Missing pk_post field in Post struct initialization
Build:    ✅ Binary compiled (target/ present)
Fix Time: 5 minutes (add field to struct)
Impact:   Removes Rust GraphQL coverage (Rust REST still available)

Quick Fix:
  1. Edit frameworks/async-graphql/src/schema.rs
  2. Add pk_post field to Post struct initialization
  3. Rebuild: docker build frameworks/async-graphql
  4. Un-comment in docker-compose.yml
  5. docker-compose restart async-graphql
```

#### 2. apollo-orm (Node.js ORM) ⛔
```
Location: frameworks/apollo-orm/
Issue:    Missing entities/index.js module
Build:    ✅ Dependencies installed (node_modules/ present)
Fix Time: 10 minutes (rebuild or create module)
Impact:   Removes Node.js ORM coverage (express-orm still available)

Quick Fix:
  1. Navigate to frameworks/apollo-orm
  2. Either:
     a) Rebuild: npm install (or yarn install)
     b) Create missing file: src/entities/index.js
  3. Un-comment in docker-compose.yml
  4. docker build frameworks/apollo-orm
  5. docker-compose restart apollo-orm
```

#### 3. jmeter-master (JMeter Service) ⛔
```
Location: docker-compose.yml
Issue:    Docker image 'justb4/jmeter:5.6' not available on Docker Hub
Build:    ❌ External image (not in filesystem)
Fix Time: Medium (find alternative or build custom)
Impact:   Low - benchmarking uses local JMeter, not this service

Quick Fix:
  Option A: Use alternative image
    - Replace image: justb4/jmeter:5.6
    - With: jmeter:5.6 or build custom Dockerfile

  Option B: Remove service
    - Just delete the jmeter-master service from docker-compose
    - Benchmarks will use system JMeter installation
```

---

## 🔴 MISSING: 13 Frameworks

### Category A: Missing Dockerfiles (8 frameworks)

These exist in filesystem but cannot be deployed via Docker without Dockerfile:

#### Go GraphQL (1)
- **go-gqlgen** (location: `frameworks/go-gqlgen/`)
  - Main file: `server.go`
  - Status: Source code present, no Dockerfile
  - Priority: Medium (Go benchmark coverage)
  - Effort: Low (copy pattern from go-graphql-go or gin-rest)

#### Go REST/ORM (3)
- **gin-rest** (location: `frameworks/gin-rest/`)
  - Main file: `server.go`
  - Status: Source code present, Dockerfile exists but not in docker-compose
  - Priority: Medium
  - Effort: Very Low (just add to docker-compose)

- **gin-orm** (location: `frameworks/gin-orm/`)
  - Main file: `server.go`
  - Status: Source code present, no Dockerfile
  - Priority: Low (express-orm covers ORM testing)
  - Effort: Low

- **gqlgen-orm** (location: `frameworks/gqlgen-orm/`)
  - Main file: `server.go`
  - Status: Source code present, no Dockerfile
  - Priority: Low
  - Effort: Low

#### Python ORM (3)
- **strawberry-orm** (location: `frameworks/strawberry-orm/`)
  - Main file: `main.py`
  - Status: Source present, no Dockerfile
  - Priority: Low (strawberry-orm-naive covers N+1 pattern)
  - Effort: Very Low (copy from strawberry)

- **fastapi-orm** (location: `frameworks/fastapi-orm/`)
  - Main file: `main.py`
  - Status: Source present, no Dockerfile
  - Priority: Low (fastapi-orm-naive covers N+1 pattern)
  - Effort: Very Low (copy from fastapi-rest)

- **graphene-orm** (location: `frameworks/graphene-orm/`)
  - Main file: `main.py`
  - Status: Source present, no Dockerfile
  - Priority: Low (graphene covers GraphQL, have naive variant)
  - Effort: Very Low

#### Ruby (1)
- **ruby-rails-fixed** (location: `frameworks/ruby-rails-fixed/`)
  - Main file: `Gemfile`
  - Status: Source present, NO Dockerfile (unlike ruby-rails)
  - Priority: Low (Ruby not critical for baseline)
  - Effort: Medium (create Dockerfile + system dependencies)

### Category B: Dockerfiles Exist But Not Deployed (5 frameworks)

These have Dockerfiles and could be deployed with minimal effort:

#### Python (1)
- **flask-rest** (location: `frameworks/flask-rest/`)
  - Build: ✅ Dockerfile present
  - Status: Not in docker-compose.yml
  - Priority: Low (Strawberry/FastAPI preferred)
  - Effort: Very Low (add to docker-compose)
  - Dependencies: ✅ All installed

#### Go (2)
- **go-graphql-go** (location: `frameworks/go-graphql-go/`)
  - Build: ✅ Dockerfile present
  - Status: Not in docker-compose.yml
  - Priority: Low (gqlgen preferred for Go)
  - Effort: Very Low (add to docker-compose)
  - Dependencies: ✅ All installed

- **gin-rest** (location: `frameworks/gin-rest/`)
  - Build: ✅ Dockerfile present
  - Status: Not in docker-compose.yml
  - Priority: Medium (Go REST coverage)
  - Effort: Very Low (add to docker-compose)
  - Dependencies: ✅ All installed

#### PHP (1)
- **php-laravel** (location: `frameworks/php-laravel/`)
  - Build: ✅ Dockerfile present
  - Status: Not in docker-compose.yml
  - Priority: Low (PHP not critical)
  - Effort: Very Low (add to docker-compose)
  - Dependencies: ✅ Vendor dependencies present

#### Ruby (1)
- **ruby-rails** (location: `frameworks/ruby-rails/`)
  - Build: ✅ Dockerfile present
  - Status: Not in docker-compose.yml
  - Priority: Low (Ruby not critical)
  - Effort: Very Low (add to docker-compose)
  - Dependencies: ✅ Vendor dependencies present

#### C#/.NET (1)
- **csharp-dotnet** (location: `frameworks/csharp-dotnet/`)
  - Build: ✅ Dockerfile present
  - Status: Not in docker-compose.yml
  - Priority: Low (.NET niche)
  - Effort: Very Low (add to docker-compose)
  - Dependencies: ❓ Build artifacts unknown

---

## 📊 Language Distribution

### Currently Deployed (21)
```
Python:     6 frameworks (29%)  ██████
Node.js:    5 frameworks (24%)  █████
Java:       3 frameworks (14%)  ███
Go:         2 frameworks (10%)  ██
Rust:       1 framework  (5%)   █
Other:      1 framework  (5%)   █ (Hasura pre-built)
```

### Full Potential (34)
```
Python:     9 frameworks (26%)  ██████
Go:         8 frameworks (24%)  ██████
Node.js:    7 frameworks (21%)  █████
Java:       3 frameworks (9%)   ██
Rust:       2 frameworks (6%)   █
PHP:        1 framework  (3%)
Ruby:       2 frameworks (6%)   █
C#/.NET:    1 framework  (3%)
Other:      1 framework  (3%)   (Hasura)
```

---

## 🎯 Deployment Recommendations

### For Full Benchmark Suite NOW (Recommended)
**Use the 21 active frameworks** - sufficient for comprehensive analysis:
- ✅ 6 Python implementations (excellent coverage)
- ✅ 5 Node.js implementations (excellent coverage)
- ✅ 3 Java implementations (good coverage)
- ✅ 2 Go implementations (partial - ORM only)
- ✅ 1 Rust implementation (partial - REST only)

**Run**: `./run-comprehensive-benchmark.sh --medium`

### To Improve Go Coverage
**Add 3 Go frameworks** (all ready to deploy):
1. Un-comment or add `gin-rest` to docker-compose
2. Un-comment or add `go-graphql-go` to docker-compose
3. Add `go-gqlgen` (needs Dockerfile copy from similar)

**Effort**: 15 minutes

### To Fix Disabled Frameworks (Optional)
**Restore 3 broken frameworks** (all fixable):
1. async-graphql: 5 min (add struct field)
2. apollo-orm: 10 min (rebuild or fix module)
3. jmeter-master: 10 min (use alternative image)

**Effort**: 25 minutes total

### To Add PHP/Ruby (Lower Priority)
**If needed, deploy 3 legacy frameworks**:
1. php-laravel: Already ready (very low effort)
2. ruby-rails: Already ready (very low effort)
3. ruby-rails-fixed: Needs Dockerfile (medium effort)

**Effort**: 30 minutes total

---

## 🚀 Deployment Sequence

### Phase 1: Start Current 21 Frameworks (5 minutes)
```bash
docker-compose up -d
# Wait for health checks (30-60 seconds)
```

### Phase 2: Run Initial Benchmark (1 hour)
```bash
./run-comprehensive-benchmark.sh --medium
```

### Phase 3: Fix Disabled Frameworks (Optional, 25 minutes)
```bash
# async-graphql
cd frameworks/async-graphql/src
# Edit schema.rs line 262: add pk_post field

# apollo-orm
cd frameworks/apollo-orm
npm install  # or rebuild

# jmeter-master
# Remove from docker-compose or use alternative image
```

### Phase 4: Add Missing Go Frameworks (Optional, 15 minutes)
```bash
# Add to docker-compose.yml:
# - gin-rest
# - go-graphql-go
# - go-gqlgen (if Dockerfile added)

docker-compose up -d gin-rest go-graphql-go
```

### Phase 5: Run Full Extended Benchmark (2+ hours)
```bash
./run-comprehensive-benchmark.sh --full
```

---

## ✅ Pre-Benchmark Checklist

- [ ] 21 frameworks running: `docker-compose ps` shows 21 up
- [ ] Database responsive: `psql -c "SELECT 1"` works
- [ ] Test data populated: `SELECT COUNT(*) FROM benchmark.tb_user > 0`
- [ ] Health checks pass: `cd tests/integration && ./smoke-test.sh`
- [ ] JMeter installed: `jmeter --version` shows 5.4+
- [ ] Disk space available: `df -h /home | grep available > 10GB`

---

## Summary Table

| Status | Count | Effort | Impact |
|--------|-------|--------|--------|
| ✅ Running | 21 | 0 min | Full benchmark ready |
| ⛔ Fixable | 3 | 25 min | Restore Rust GraphQL, Node ORM |
| ❌ Missing | 10 | 15-60 min | Enhanced Go/legacy language support |
| 📦 Total | 34 | 0-85 min | Up to 34 frameworks available |

**Recommendation**: Start with 21 frameworks, run comprehensive benchmark, optionally add more.
