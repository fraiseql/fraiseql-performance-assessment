# Monitoring Dashboard Quick Links

## Primary Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
  - Main Dashboard: http://localhost:3000/d/fraiseql-performance-benchmark

- **Prometheus**: http://localhost:9090
  - Targets: http://localhost:9090/targets
  - Rules: http://localhost:9090/rules
  - Graph: http://localhost:9090/graph

- **cAdvisor**: http://localhost:8080
  - Docker metrics: http://localhost:8080/docker/

## Framework Endpoints (28 Total Frameworks)

**See FRAMEWORK_MAPPING.md for the complete list of all 28 frameworks and their ports**

### Sample Framework Endpoints

| Framework | Port | Health Check | GraphQL/REST Endpoint |
|-----------|------|--------------|----------------------|
| fraiseql | 4000 | http://localhost:4000/health | http://localhost:4000/graphql |
| strawberry | 8011 | http://localhost:8011/health | http://localhost:8011/graphql |
| graphene | 8002 | http://localhost:8002/health | http://localhost:8002/graphql |
| fastapi-rest | 8003 | http://localhost:8003/health | http://localhost:8003/api/v1 |
| flask-rest | 8004 | http://localhost:8004/health | http://localhost:8004/api/v1 |
| apollo | 4001 | http://localhost:4001/graphql (POST) | http://localhost:4001/graphql |
| express-rest | 8005 | http://localhost:8005/health | http://localhost:8005/api/v1 |
| go-gqlgen | 4010 | http://localhost:4010/health | http://localhost:4010/query |
| gin-rest | 8006 | http://localhost:8006/health | http://localhost:8006/api/v1 |

### Special Health Check Cases
- **Apollo**: POST /graphql (not GET /health)
- **Spring Boot** (spring-boot, spring-boot-orm, spring-boot-orm-naive): /actuator/health
- **Laravel/Rails** (php-laravel, ruby-rails): /api/health
- **Hasura**: /healthz

## Useful Prometheus Queries

### Framework CPU Usage
```promql
rate(container_cpu_usage_seconds_total{name=~"fraiseql.*"}[1m]) * 100
```

### Framework Memory Usage
```promql
container_memory_usage_bytes{name=~"fraiseql.*"} / 1024 / 1024
```

### Database Connections
```promql
pg_stat_activity_count{state="active"}
```

### Request Rate (if frameworks expose metrics)
```promql
rate(http_requests_total[1m])
```

## Quick Commands

```bash
# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View framework logs
docker logs -f fraiseql-performance-assessment-fraiseql-1

# Restart monitoring stack
cd monitoring && docker-compose -f docker-compose.monitoring.yml restart

# Run verification script
./scripts/verify-frameworks.sh
```
