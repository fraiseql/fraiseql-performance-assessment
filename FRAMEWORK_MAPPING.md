# Framework Port & Health Check Mapping

Auto-generated mapping of all 32 deployed frameworks for benchmark script configuration.

## Python Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| fraiseql | 4000 | fraiseql | /health | GraphQL |
| strawberry | 8011 | strawberry | /health | GraphQL |
| graphene | 8002 | graphene | /health | GraphQL |
| fastapi-rest | 8003 | fastapi-rest | /health | REST |
| flask-rest | 8004 | flask-rest | /health | REST |
| strawberry-orm-naive | 8019 | strawberry-orm-naive | /health | GraphQL (Naive) |
| fastapi-orm-naive | 8020 | fastapi-orm-naive | /health | GraphQL (Naive) |

## Node.js Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| apollo | 4001 | apollo | /graphql (POST) | GraphQL |
| apollo-orm | 4005 | apollo-orm | /health | GraphQL (ORM) |
| express-rest | 8005 | express-rest | /health | REST |
| express-orm | 8007 | express-orm | /health | REST (ORM) |
| apollo-orm-naive | 8021 | apollo-orm-naive | /health | GraphQL (Naive) |
| express-orm-naive | 8022 | express-orm-naive | /health | REST (Naive) |

## Java Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| spring-boot | 8010 | spring-boot | /actuator/health | REST |
| spring-boot-orm | 8013 | spring-boot-orm | /actuator/health | REST (ORM) |
| spring-boot-orm-naive | 8014 | spring-boot-orm-naive | /actuator/health | REST (Naive) |

## Go Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| go-graphql-go | 8008 | go-graphql-go | /health | GraphQL |
| gin-rest | 8006 | gin-rest | /health | REST |
| go-gqlgen | 4010 | go-gqlgen | /health | GraphQL |
| go-gqlgen-alt | 4003 | go-gqlgen-alt | /health | GraphQL (Alt) |
| gqlgen-orm-naive | 8023 | gqlgen-orm-naive | /health | GraphQL (Naive) |
| gin-orm-naive | 8024 | gin-orm-naive | /health | REST (Naive) |

## Rust Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| async-graphql | 8016 | async-graphql | /health | GraphQL |
| actix-web-rest | 8015 | actix-web-rest | /health | REST |

## C#/.NET Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| csharp-dotnet | 8025 | csharp-dotnet | /health | REST |

## PHP Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| php-laravel | 8009 | php-laravel | /api/health | GraphQL |

## Ruby Frameworks

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| ruby-rails | 8012 | ruby-rails | /api/health | REST |

## Managed GraphQL

| Name | Port | Service | Health Endpoint | Type |
|------|------|---------|-----------------|------|
| hasura | 8081 | hasura | /healthz | GraphQL (Managed) |

## Health Check Endpoint Patterns

- **Standard**: `/health` (most frameworks) - GET request, returns 200 on healthy
- **Actuator**: `/actuator/health` (Java Spring Boot) - GET request, returns JSON
- **API Path**: `/api/health` (Laravel, Rails) - GET request
- **GraphQL**: `/graphql` (Apollo) - POST request with GraphQL query
- **Hasura**: `/healthz` - GET request

## Port Usage Summary

- Lowest: 4000 (fraiseql)
- Highest: 8081 (hasura)
- Total Unique Ports: 30 (some services expose multiple ports)
- Range: 4000-4010, 8002-8025, 8081

## Using This Mapping

For benchmark script configuration:
1. Generate framework arrays dynamically from docker-compose
2. Map service names to framework names
3. Apply health check logic based on framework type
4. Support optional filtering by language, type, or pattern
