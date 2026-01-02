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

## Framework Endpoints

| Framework | Health Check | GraphQL/REST Endpoint |
|-----------|--------------|----------------------|
| FraiseQL | http://localhost:4000/health | http://localhost:4000/graphql |
| Strawberry | http://localhost:8011/health | http://localhost:8011/graphql |
| Graphene | http://localhost:8002/health | http://localhost:8002/graphql |
| FastAPI | http://localhost:8003/health | http://localhost:8003/api/v1 |
| Flask | http://localhost:8004/health | http://localhost:8004/api/v1 |
| Apollo | http://localhost:4001/graphql | http://localhost:4001/graphql |
| Express | http://localhost:8005/health | http://localhost:8005/api/v1 |
| gqlgen | http://localhost:4003/health | http://localhost:4003/query |
| gin-rest | http://localhost:8006/health | http://localhost:8006/api/v1 |

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
