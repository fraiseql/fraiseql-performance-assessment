# Phase 8.1 Monitoring Stack - Agent Handoff

## Current Status

**Monitoring Stack Deployment**: 80% Complete ✅

### What's Working
- ✅ Prometheus deployed and scraping (3/11 active targets):
  - `prometheus` (self-monitoring)
  - `node-exporter` (system metrics)
  - `cadvisor` (container metrics)
- ✅ Grafana deployed and initializing (port 3000)
- ✅ cAdvisor collecting container metrics
- ✅ Configuration files validated and fixed

### Known Issue: postgres-exporter DNS Resolution
**Problem**: postgres-exporter cannot connect to PostgreSQL

```
Error: dial tcp: lookup host.docker.internal on 127.0.0.11:53: no such host
```

**Root Cause**: Docker bridge network cannot resolve `host.docker.internal` for external connections.

**Current Connection String**:
```yaml
DATA_SOURCE_NAME: "postgresql://benchmark:benchmark@host.docker.internal:5434/fraiseql_benchmark?sslmode=disable"
```

**PostgreSQL Actual Location**: Running on host machine at port 5434.

## Immediate Task: Fix postgres-exporter

Choose and implement ONE of these approaches:

### Option A: Use Actual Host IP (Recommended for Development)
1. Get host IP: `hostname -I` or `ip addr` (usually something like 192.168.x.x)
2. Update connection string in `monitoring/docker-compose.monitoring.yml` line 94:
   ```yaml
   DATA_SOURCE_NAME: "postgresql://benchmark:benchmark@192.168.x.x:5434/fraiseql_benchmark?sslmode=disable"
   ```
3. Restart postgres-exporter: `docker-compose -f monitoring/docker-compose.monitoring.yml restart postgres-exporter`
4. Verify with: `docker logs postgres-exporter | grep -i "connection\|error" | tail -5`

### Option B: Add PostgreSQL to Monitoring Network
1. Modify main `docker-compose.yml` to add postgres service to `fraiseql-benchmark` network
2. Update connection string in monitoring compose:
   ```yaml
   DATA_SOURCE_NAME: "postgresql://benchmark:benchmark@postgres:5434/fraiseql_benchmark?sslmode=disable"
   ```
3. Requires coordination with existing postgres container

### Option C: Run postgres-exporter Outside Docker
1. Install postgres-exporter on host machine
2. Point directly to localhost:5434
3. Add host port 9187 to Prometheus scrape config

## Verification Commands

After fixing postgres-exporter, verify success:

```bash
# Check postgres-exporter is healthy
docker-compose -f monitoring/docker-compose.monitoring.yml logs postgres-exporter | tail -5

# Query Prometheus for postgres-exporter metrics
curl -s http://localhost:9090/api/v1/query?query=pg_stat_activity_count | jq '.data.result'

# Should show active PostgreSQL metrics
```

## Next Steps After postgres-exporter is Fixed

1. **Verify all 5 scrape targets are healthy**:
   ```bash
   curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
   # Should show: 5
   ```

2. **Proceed to Sub-Phase 8.2: Resource Collector Script**
   - Create Python script for 1-second metric sampling
   - Query Prometheus API for container and database metrics
   - Output CSV files with all metrics

## Key Files

- **Monitoring compose**: `/monitoring/docker-compose.monitoring.yml` (line 94 needs update)
- **Prometheus config**: `/monitoring/prometheus.yml` (already validated)
- **Phase 8 plan**: `/.phases/phase-8-resource-monitoring-subphases.md` (section 8.2 is next)

## Framework-Specific Targets

These targets are currently "DOWN" (expected - they don't exist until framework deployment):
- fraiseql (port 4000)
- strawberry (port 8000)
- graphene (port 8000)
- apollo-server (port 4000)
- fastapi (port 8000)
- flask (port 8000)
- gqlgen (port 8000)
- gin-rest (port 8000)

These will automatically become available once frameworks are deployed during benchmark execution.

## Success Criteria for Sub-Phase 8.1 Completion

- [ ] postgres-exporter connected to PostgreSQL
- [ ] Prometheus shows 5+ healthy scrape targets (use Prometheus UI at http://localhost:9090)
- [ ] Grafana loads at http://localhost:3000 (login: admin/admin)
- [ ] All 5 exporters collecting metrics continuously
- [ ] No errors in container logs

Once these criteria are met, proceed to Sub-Phase 8.2 (Resource Collector Script).
