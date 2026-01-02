# C#/.NET Core REST & GraphQL Implementation Plan

## 📋 Overview

Implement comprehensive C#/.NET Core benchmarking frameworks to establish .NET managed runtime baseline, demonstrate Hot Chocolate GraphQL performance, and provide enterprise-standard patterns for comparison with Java and other languages.

---

## 🎯 Objectives

1. **Implement ASP.NET Core REST API** - Modern .NET REST patterns
2. **Implement Hot Chocolate GraphQL** - .NET's leading GraphQL framework
3. **Establish .NET performance baseline** - Show managed memory characteristics
4. **Demonstrate LINQ query compilation** - Different from SQL generation
5. **Compare with Java/Python/Go** - Language-specific performance
6. **Provide enterprise context** - .NET adoption in enterprises and Azure

---

## 📊 Scope

### What's Included

- ✅ ASP.NET Core 8.0 REST API (5 endpoints)
- ✅ Hot Chocolate GraphQL (7 query fields)
- ✅ Entity Framework Core ORM
- ✅ Connection pooling (default pooling)
- ✅ Prometheus metrics (App Metrics)
- ✅ Health checks and logging
- ✅ Docker container with multi-stage build
- ✅ GC monitoring and heap analysis

### What's NOT Included

- ❌ MAUI/Mobile development
- ❌ SignalR/WebSockets
- ❌ Entity Framework 6 (legacy)
- ❌ Minimal hosting model (using standard DI setup)

---

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Framework** | ASP.NET Core | 8.0 | Latest LTS |
| **Language** | C# | 12.0 | Latest features |
| **ORM** | Entity Framework Core | 8.0 | Official .NET ORM |
| **GraphQL** | Hot Chocolate | 13.x | Industry standard for .NET |
| **Metrics** | App Metrics + Prometheus | Latest | .NET standard |
| **Database Driver** | Npgsql | 8.x | PostgreSQL for .NET |
| **DI Container** | Built-in | 8.0 | ASP.NET Core native |
| **Base Image** | mcr.microsoft.com/dotnet | 8.0-alpine | Official Microsoft image |

### Project Structure

```
frameworks/csharp-dotnet/
├── FraiseQL.Benchmark.csproj     # Project file
├── Program.cs                     # ASP.NET Core startup
├── appsettings.json               # Configuration
├── Models/
│   ├── User.cs                    # EF Core entity
│   ├── Post.cs
│   └── Comment.cs
├── Data/
│   └── BenchmarkContext.cs        # DbContext
├── Repositories/
│   ├── IUserRepository.cs
│   ├── UserRepository.cs
│   ├── IPostRepository.cs
│   └── PostRepository.cs
├── Services/
│   ├── UserService.cs             # Business logic
│   ├── PostService.cs
│   └── CommentService.cs
├── Controllers/
│   ├── UsersController.cs         # REST endpoints
│   ├── PostsController.cs
│   └── HealthController.cs
├── GraphQL/
│   ├── UserType.cs                # Hot Chocolate types
│   ├── PostType.cs
│   ├── Query.cs                   # GraphQL queries
│   └── schema.graphql             # Schema definition (optional)
├── Middleware/
│   ├── MetricsMiddleware.cs
│   └── ErrorHandlingMiddleware.cs
├── Dockerfile                     # Multi-stage build
└── docker-entrypoint.sh
```

---

## 📝 Implementation Phases (9 phases, ~35 hours)

### Phase 1: Project Setup & NuGet Configuration
**Objective**: Create .NET project with all dependencies
**Duration**: 1-2 hours

**Tasks**:
1. Create ASP.NET Core project
   ```bash
   dotnet new webapi -n FraiseQL.Benchmark -f net8.0
   ```

2. Add NuGet packages
   ```bash
   dotnet add package Microsoft.EntityFrameworkCore
   dotnet add package Microsoft.EntityFrameworkCore.Npgsql
   dotnet add package HotChocolate.Types
   dotnet add package HotChocolate.Execution
   dotnet add package HotChocolate.AspNetCore
   dotnet add package App.Metrics
   dotnet add package App.Metrics.Reporting.Prometheus
   dotnet add package Npgsql
   ```

3. Restore dependencies
   ```bash
   dotnet restore
   ```

**Deliverables**:
- ✅ Project file created with all dependencies
- ✅ `dotnet build` succeeds
- ✅ All NuGet packages resolved

---

### Phase 2: EF Core Models & DbContext
**Objective**: Define database models using EF Core
**Duration**: 2-3 hours

**Tasks**:
1. Create User model
   ```csharp
   public class User
   {
       public string Id { get; set; }
       public string Username { get; set; }
       public string FirstName { get; set; }
       public string LastName { get; set; }
       public string Bio { get; set; }

       public ICollection<Post> Posts { get; set; } = new List<Post>();
       public ICollection<Comment> Comments { get; set; } = new List<Comment>();
   }
   ```

2. Create Post and Comment models with relationships
3. Create BenchmarkContext (DbContext)
   ```csharp
   public class BenchmarkContext : DbContext
   {
       public DbSet<User> Users { get; set; }
       public DbSet<Post> Posts { get; set; }
       public DbSet<Comment> Comments { get; set; }

       protected override void OnModelCreating(ModelBuilder modelBuilder)
       {
           modelBuilder.HasDefaultSchema("benchmark");
           // Configure relationships, indexes, etc.
       }
   }
   ```

4. Configure connection pooling

**Deliverables**:
- ✅ All models defined
- ✅ Relationships configured correctly
- ✅ DbContext compiles
- ✅ Migrations work

---

### Phase 3: Repository Pattern Implementation
**Objective**: Create repository layer for data access
**Duration**: 1-2 hours

**Tasks**:
1. Create repository interfaces
   ```csharp
   public interface IUserRepository
   {
       Task<User> GetByIdAsync(string id);
       Task<IEnumerable<User>> GetAllAsync(int page, int size);
   }
   ```

2. Implement repositories with LINQ queries
   ```csharp
   public class UserRepository : IUserRepository
   {
       private readonly BenchmarkContext _context;

       public async Task<User> GetByIdAsync(string id)
       {
           return await _context.Users
               .AsNoTracking()
               .FirstOrDefaultAsync(u => u.Id == id);
       }

       public async Task<IEnumerable<User>> GetAllAsync(int page, int size)
       {
           return await _context.Users
               .AsNoTracking()
               .Skip(page * size)
               .Take(size)
               .ToListAsync();
       }
   }
   ```

3. Implement PostRepository with eager loading

**Deliverables**:
- ✅ Repositories functional
- ✅ LINQ queries compile to SQL
- ✅ Eager loading prevents N+1

---

### Phase 4: REST Controllers
**Objective**: Implement 5 REST endpoints
**Duration**: 2-3 hours

**Tasks**:
1. Create UsersController
   ```csharp
   [ApiController]
   [Route("api/[controller]")]
   public class UsersController : ControllerBase
   {
       private readonly IUserRepository _repository;

       [HttpGet("{id}")]
       public async Task<ActionResult<UserDto>> GetUser(string id)
       {
           var user = await _repository.GetByIdAsync(id);
           if (user == null) return NotFound();
           return Ok(MapToDto(user));
       }

       [HttpGet]
       public async Task<ActionResult<IEnumerable<UserDto>>> ListUsers(
           [FromQuery] int page = 0,
           [FromQuery] int size = 10)
       {
           var users = await _repository.GetAllAsync(page, size);
           return Ok(users.Select(MapToDto));
       }
   }
   ```

2. Create PostsController with 2 endpoints
3. Add error handling middleware
4. Add response compression

**Deliverables**:
- ✅ 5 REST endpoints working
- ✅ Proper HTTP status codes
- ✅ JSON serialization working
- ✅ Error handling implemented

---

### Phase 5: Service Layer & Business Logic
**Objective**: Implement service layer
**Duration**: 1-2 hours

**Tasks**:
1. Create UserService
   ```csharp
   public class UserService
   {
       private readonly IUserRepository _repository;

       public async Task<UserDto> GetUserAsync(string id)
       {
           var user = await _repository.GetByIdAsync(id);
           return user != null ? MapToDto(user) : null;
       }
   }
   ```

2. Create PostService
3. Register services in DI container
4. Add logging

**Deliverables**:
- ✅ Services implemented
- ✅ DI registration working
- ✅ Logging functional

---

### Phase 6: Hot Chocolate GraphQL Implementation
**Objective**: Implement GraphQL with Hot Chocolate
**Duration**: 3-4 hours

**Tasks**:
1. Define GraphQL types
   ```csharp
   public class UserType
   {
       public string Id { get; set; }
       public string Username { get; set; }
       public string FirstName { get; set; }
       public string LastName { get; set; }
       public string Bio { get; set; }

       [GraphQLType(typeof(ListType<PostType>))]
       public IEnumerable<Post> Posts { get; set; }
   }
   ```

2. Create Query type with resolvers
   ```csharp
   public class Query
   {
       public async Task<User> GetUserAsync(
           [Service] IUserRepository repository,
           string id)
       {
           return await repository.GetByIdAsync(id);
       }

       public async Task<IEnumerable<User>> GetUsersAsync(
           [Service] IUserRepository repository,
           int first = 10)
       {
           return await repository.GetAllAsync(0, first);
       }
   }
   ```

3. Register GraphQL services in Program.cs
   ```csharp
   services
       .AddGraphQLServer()
       .AddQueryType<Query>()
       .AddType<UserType>()
       .AddType<PostType>()
       .AddType<CommentType>();
   ```

4. Map GraphQL endpoint

**Deliverables**:
- ✅ GraphQL schema defined
- ✅ 7 queries working
- ✅ Relationships resolve correctly
- ✅ GraphQL endpoint responding

---

### Phase 7: Prometheus Metrics & Monitoring
**Objective**: Add App Metrics with Prometheus
**Duration**: 2-3 hours

**Tasks**:
1. Configure App Metrics in Program.cs
   ```csharp
   services
       .AddMetrics()
       .AddInMemoryMetrics();

   var metricsRoot = app.ApplicationServices.GetRequiredService<IMetricsRoot>();

   app.UseMetricsEndpoint("/metrics", new PrometheusMetricsTextOutputFormatter());
   ```

2. Add custom metrics for endpoints
3. Add health checks endpoint
4. Configure /health endpoint

**Deliverables**:
- ✅ /health returns status
- ✅ /metrics returns Prometheus format
- ✅ Custom metrics collected
- ✅ Metrics accessible

---

### Phase 8: Application Configuration & Startup
**Objective**: Configure ASP.NET Core application
**Duration**: 1-2 hours

**Tasks**:
1. Create appsettings.json
   ```json
   {
     "ConnectionStrings": {
       "DefaultConnection": "Host=localhost;Port=5434;Database=fraiseql_benchmark;Username=benchmark;Password=benchmark123"
     },
     "Logging": {
       "LogLevel": {
         "Default": "Information"
       }
     }
   }
   ```

2. Configure Program.cs startup
3. Set up middleware pipeline
4. Add CORS and compression

**Deliverables**:
- ✅ Application starts on port 8008
- ✅ Database connection working
- ✅ All endpoints responsive
- ✅ Metrics accessible

---

### Phase 9: Docker & Integration
**Objective**: Create Docker image and integrate into suite
**Duration**: 2-3 hours

**Tasks**:
1. Create Dockerfile
   ```dockerfile
   # Build stage
   FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS builder
   WORKDIR /app
   COPY . .
   RUN dotnet publish -c Release -o out

   # Runtime stage
   FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine
   WORKDIR /app
   COPY --from=builder /app/out .
   EXPOSE 8008
   ENTRYPOINT ["dotnet", "FraiseQL.Benchmark.dll"]
   ```

2. Add to docker-compose.yml
3. Update test scripts
4. Test integration

**Deliverables**:
- ✅ Docker image builds
- ✅ Service in docker-compose.yml
- ✅ Starts with stack
- ✅ Health checks pass

---

## 🎯 Performance Targets

| Metric | Target |
|--------|--------|
| **P50 Latency** | 15-20ms |
| **P99 Latency** | 40-60ms |
| **Throughput** | 2500-3500 req/s |
| **Memory** | 300-500MB |
| **Startup Time** | 2-3 seconds |
| **Image Size** | < 300MB |

---

## ✅ Implementation Checklist

- [ ] Phase 1: Project setup
- [ ] Phase 2: EF Core models
- [ ] Phase 3: Repositories
- [ ] Phase 4: REST controllers
- [ ] Phase 5: Service layer
- [ ] Phase 6: Hot Chocolate GraphQL
- [ ] Phase 7: Metrics
- [ ] Phase 8: Configuration
- [ ] Phase 9: Docker & integration

---

**Version**: 1.0 | **Status**: Ready for Implementation | **Estimated Hours**: 35
