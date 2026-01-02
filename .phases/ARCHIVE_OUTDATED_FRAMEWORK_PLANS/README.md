# Archive: Outdated Framework Implementation Plans

This directory contains implementation plans for frameworks that are either:
1. **Not currently enabled** in docker-compose.yml (no active development)
2. **Superseded by newer implementations** (e.g., better alternatives exist)
3. **Lower priority** (less commonly used in production)

## Archived Frameworks

- **actix-web-rest/** - Rust REST (lower priority than async-graphql)
- **async-graphql/** - Rust GraphQL (has compilation issues, lower priority)
- **java-spring-boot/** - Java frameworks (extensive plans, not currently prioritized)
- **csharp-dotnet/** - C#/.NET (never enabled, business case unclear)
- **elixir-phoenix/** - Elixir (never enabled, niche use case)
- **php-laravel/** - PHP (never enabled, not preferred for benchmarking)
- **ruby-rails/** - Ruby (never enabled, operational overhead high)

## Why These Were Archived

1. **Focus on active frameworks**: Current 12 enabled frameworks provide sufficient coverage
   - Python (strawberry, graphene, fastapi, spring-boot)
   - Node.js (apollo, express)
   - Rust (fraiseql)
   - Go (gqlgen)
   - Java (spring-boot)

2. **Resource constraints**: Maintaining 20+ framework implementations is operationally expensive
   - CI/CD complexity increases
   - Docker build times increase
   - Test matrix becomes unwieldy
   - Code review burden increases

3. **Business priorities**: Focus on languages with highest production usage:
   - Python (ML/data science backends)
   - Node.js (web startups)
   - Go (cloud/distributed systems)
   - Rust (systems/performance-critical)
   - Java (enterprise)

## If Needed in Future

To re-activate a framework:
1. Review the archived IMPLEMENTATION_PLAN.md
2. Check if dependencies/base images are still available
3. Test building the Docker image
4. Add service entry to docker-compose.yml
5. Run smoke tests to verify functionality

## File Organization

```
ARCHIVE_OUTDATED_FRAMEWORK_PLANS/
├── README.md (this file)
├── actix-web-rest/
│   └── IMPLEMENTATION_PLAN.md
├── async-graphql/
│   └── IMPLEMENTATION_PLAN.md
├── java-spring-boot/
│   └── IMPLEMENTATION_PLAN.md
├── csharp-dotnet/
│   └── IMPLEMENTATION_PLAN.md
├── elixir-phoenix/
│   └── IMPLEMENTATION_PLAN.md
├── php-laravel/
│   └── IMPLEMENTATION_PLAN.md
└── ruby-rails/
    └── IMPLEMENTATION_PLAN.md
```

---

**Note**: These plans remain available for reference and future use. The master benchmark plan (`.phases/00-BENCHMARK_MASTER_PLAN.md`) focuses on the currently active framework set.
