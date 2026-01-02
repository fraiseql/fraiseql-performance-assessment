# Phase 8: Monitoring Infrastructure Fix Plan

## Current Status

### ✅ Completed
- Monitoring directory structure created
- `docker-compose.monitoring.yml` with all services defined
- Base `prometheus.yml` configuration file
- Main `docker-compose.yml` updated with Prometheus labels
- Monitoring stack containers running:
  - Prometheus (ready but unhealthy)
  - Node Exporter (running)
  - cAdvisor (healthy)
  - postgres-exporter (running)

### ❌ Issues to Fix

1. **Recording Rules Missing**
   - Directory `monitoring/prometheus/rules/` doesn't exist
   - Prometheus shows 0 rule groups loaded
   - Recording rules needed for metric aggregations

2. **Prometheus Healthcheck Failing**
   - Container shows "unhealthy" despite being "ready"
   - May need healthcheck configuration adjustment

3. **Scrape Targets Down**
   - Most targets showing "down" status
   - Expected (framework containers not running yet)
   - Will resolve once frameworks are deployed

4. **Grafana Not Configured**
   - No provisioning configuration
   - No datasource setup
   - No dashboards created

---

## Implementation Plan

### Step 1: Create Prometheus Recording Rules

**File:** `monitoring/prometheus/rules/benchmark.yml`

**Purpose:** Pre-aggregate metrics for efficient querying and dashboard performance

**Metric Categories:**

1. **System Metrics** (from node-exporter)
   - CPU usage by mode
   - Memory utilization
   - Disk I/O rates
   - Network throughput

2. **Container Metrics** (from cAdvisor)
   - Per-framework CPU usage
   - Per-framework memory usage
   - Container restart counts
   - Network traffic by container

3. **Database Metrics** (from postgres-exporter)
   - Connection pool utilization
   - Query performance (avg, p95, p99)
   - Cache hit ratios
   - Transaction rates
   - Lock waits

4. **Application Metrics** (from framework exporters)
   - HTTP request rates
   - Response time percentiles
   - Error rates
   - GraphQL query performance

5. **Derived Performance Metrics**
   - Requests per second per framework
   - Average response time trends
   - Error rate percentiles
   - Resource efficiency ratios

**Recording Rule Structure:**
```yaml
groups:
  - name: system_metrics
    interval: 30s
    rules:
      - record: node:cpu:usage_percent
      - record: node:memory:usage_percent
      # ... more rules

  - name: container_metrics
    interval: 30s
    rules:
      - record: container:cpu:usage_percent
      - record: container:memory:usage_bytes
      # ... more rules

  - name: database_metrics
    interval: 30s
    rules:
      - record: postgres:connections:active
      - record: postgres:cache:hit_ratio
      # ... more rules

  - name: application_metrics
    interval: 30s
    rules:
      - record: http:requests:rate_5m
      - record: http:response:p95_latency
      # ... more rules
```

**Implementation Steps:**
1. Create directory: `mkdir -p monitoring/prometheus/rules/`
2. Write `benchmark.yml` with all recording rules
3. Reload Prometheus configuration
4. Verify rules loaded: `curl http://localhost:9090/api/v1/rules`

---

### Step 2: Fix Prometheus Healthcheck

**Current Issue:** Container reports unhealthy despite API being ready

**Root Cause Analysis:**
- Healthcheck might be checking wrong endpoint
- Healthcheck timeout may be too short
- Initial delay might be insufficient

**Solution Options:**

**Option A: Update docker-compose healthcheck**
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/ready"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Option B: Use promtool for validation**
```yaml
healthcheck:
  test: ["CMD", "promtool", "check", "healthy", "--config.file=/etc/prometheus/prometheus.yml"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Recommended:** Option A (simpler, more reliable)

**Implementation Steps:**
1. Update `docker-compose.monitoring.yml` healthcheck section
2. Restart Prometheus container
3. Monitor: `docker ps` and `curl http://localhost:9090/-/healthy`
4. Verify: `docker inspect prometheus | jq '.[0].State.Health'`

---

### Step 3: Create Grafana Provisioning Configuration

**Purpose:** Auto-configure Grafana with datasources and dashboards on startup

#### 3.1 Datasource Provisioning

**File:** `monitoring/grafana/provisioning/datasources/prometheus.yml`

**Content:**
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: 15s
      queryTimeout: 60s
      httpMethod: POST
```

**Implementation:**
```bash
mkdir -p monitoring/grafana/provisioning/datasources
# Create prometheus.yml
```

#### 3.2 Dashboard Provisioning

**File:** `monitoring/grafana/provisioning/dashboards/default.yml`

**Content:**
```yaml
apiVersion: 1

providers:
  - name: 'FraiseQL Benchmarks'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

**Implementation:**
```bash
mkdir -p monitoring/grafana/provisioning/dashboards
# Create default.yml
```

#### 3.3 Update docker-compose.monitoring.yml

Add volume mounts for Grafana:
```yaml
grafana:
  image: grafana/grafana:latest
  container_name: grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
    - GF_USERS_ALLOW_SIGN_UP=false
  volumes:
    - grafana-data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning
  networks:
    - fraiseql-benchmark
  restart: unless-stopped
```

---

### Step 4: Create Grafana Dashboard JSON

**File:** `monitoring/grafana/provisioning/dashboards/fraiseql-performance.json`

**Dashboard Specification:**

#### Panel Layout (15 panels total)

**Row 1: Overview (4 panels)**
1. **Total Request Rate** - Single stat with sparkline
   - Metric: `sum(rate(http_requests_total[5m]))`
   - Unit: req/s

2. **Average Response Time** - Gauge
   - Metric: `avg(http_response_duration_seconds)`
   - Unit: seconds
   - Thresholds: green <100ms, yellow <500ms, red >500ms

3. **Error Rate** - Single stat
   - Metric: `sum(rate(http_requests_total{status=~"5.."}[5m]))`
   - Unit: errors/s
   - Thresholds: green <0.1, yellow <1, red >1

4. **Active Connections** - Gauge
   - Metric: `sum(pg_stat_activity_count)`
   - Unit: connections

**Row 2: Framework Comparison (3 panels)**
5. **Requests/sec by Framework** - Time series graph
   - Metric: `rate(http_requests_total[5m]) by (framework)`
   - Legend: framework name
   - Stack: false

6. **Response Time by Framework** - Time series graph
   - Metric: `histogram_quantile(0.95, rate(http_response_duration_seconds_bucket[5m])) by (framework)`
   - Legend: framework name
   - Unit: seconds

7. **Framework Resource Efficiency** - Bar gauge
   - Metric: `rate(http_requests_total[5m]) / container_memory_usage_bytes by (framework)`
   - Unit: req/MB
   - Horizontal orientation

**Row 3: Database Performance (3 panels)**
8. **Database Query Performance** - Time series
   - Metrics:
     - `rate(pg_stat_statements_calls[5m])`
     - `rate(pg_stat_statements_total_time[5m])`
   - Dual Y-axis

9. **Connection Pool Status** - Stacked area chart
   - Metrics:
     - `pg_stat_activity_count by (state)`
   - States: active, idle, idle in transaction

10. **Cache Hit Ratio** - Gauge
    - Metric: `rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))`
    - Unit: percent
    - Thresholds: red <90%, yellow <95%, green >=95%

**Row 4: System Resources (3 panels)**
11. **CPU Usage** - Time series
    - Metric: `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
    - Unit: percent
    - Fill: 1

12. **Memory Usage** - Time series
    - Metric: `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100`
    - Unit: percent
    - Fill: 1

13. **Disk I/O** - Time series
    - Metrics:
      - `rate(node_disk_read_bytes_total[5m])`
      - `rate(node_disk_written_bytes_total[5m])`
    - Unit: bytes/s
    - Dual Y-axis (read positive, write negative)

**Row 5: Container & Network (2 panels)**
14. **Container CPU by Framework** - Stacked area
    - Metric: `rate(container_cpu_usage_seconds_total{container_label_framework!=""}[5m]) by (container_label_framework)`
    - Unit: CPU cores
    - Stack: true

15. **Network Traffic** - Time series
    - Metrics:
      - `rate(container_network_receive_bytes_total[5m])`
      - `rate(container_network_transmit_bytes_total[5m])`
    - Unit: bytes/s

**Dashboard Settings:**
```json
{
  "title": "FraiseQL Performance Assessment",
  "timezone": "browser",
  "refresh": "10s",
  "time": {
    "from": "now-15m",
    "to": "now"
  },
  "templating": {
    "list": [
      {
        "name": "framework",
        "type": "query",
        "query": "label_values(http_requests_total, framework)",
        "multi": true,
        "includeAll": true
      }
    ]
  }
}
```

---

### Step 5: Verification and Testing

#### 5.1 Verify Prometheus

**Recording Rules:**
```bash
# Check rules loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | length'
# Expected: >0 (should show number of rule groups)

# Check specific rule
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[0]'
```

**Healthcheck:**
```bash
# Check container health
docker ps --filter name=prometheus --format "{{.Status}}"
# Expected: "Up X minutes (healthy)"

# Check ready endpoint
curl -sf http://localhost:9090/-/ready && echo "READY"

# Check healthy endpoint
curl -sf http://localhost:9090/-/healthy && echo "HEALTHY"
```

**Scrape Targets:**
```bash
# Check target status
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Expected targets to be UP:
# - prometheus (self)
# - node-exporter
# - cadvisor
# - postgres-exporter
```

#### 5.2 Verify Grafana

**Access:**
```bash
# Check Grafana is running
curl -s http://localhost:3000/api/health | jq

# Login and check datasources
curl -s -u admin:admin http://localhost:3000/api/datasources | jq
# Expected: Prometheus datasource configured

# Check dashboards
curl -s -u admin:admin http://localhost:3000/api/search | jq
# Expected: FraiseQL Performance dashboard present
```

**Manual Verification:**
1. Open browser: http://localhost:3000
2. Login: admin/admin
3. Navigate to dashboard
4. Verify all 15 panels load
5. Check that data appears (may be limited if frameworks not running)

#### 5.3 Verify Metrics Flow

**Test Metric Collection:**
```bash
# Check if metrics are being collected
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result[] | {job: .metric.job, value: .value[1]}'

# Check node-exporter metrics
curl -s http://localhost:9090/api/v1/query?query=node_cpu_seconds_total | jq '.data.result | length'

# Check cadvisor metrics
curl -s http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total | jq '.data.result | length'

# Check postgres metrics
curl -s http://localhost:9090/api/v1/query?query=pg_up | jq
```

---

### Step 6: Documentation Updates

#### 6.1 Create Monitoring README

**File:** `monitoring/README.md`

**Content:**
```markdown
# FraiseQL Performance Assessment - Monitoring Stack

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Node Exporter**: System metrics
- **cAdvisor**: Container metrics
- **postgres-exporter**: PostgreSQL metrics

## Quick Start

### Start Monitoring Stack
```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Access UIs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### Stop Monitoring Stack
```bash
docker-compose -f docker-compose.monitoring.yml down
```

## Dashboards

### FraiseQL Performance Assessment
- **URL**: http://localhost:3000/d/fraiseql-perf
- **Panels**: 15 panels covering:
  - Request rates and response times
  - Framework comparisons
  - Database performance
  - System resources
  - Container metrics

## Recording Rules

Location: `prometheus/rules/benchmark.yml`

Pre-aggregated metrics for:
- System performance
- Container resource usage
- Database statistics
- Application metrics

## Troubleshooting

### Prometheus unhealthy
```bash
# Check logs
docker logs prometheus

# Verify config
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Reload config
curl -X POST http://localhost:9090/-/reload
```

### Grafana datasource issues
```bash
# Check Grafana logs
docker logs grafana

# Test Prometheus connection from Grafana container
docker exec grafana curl http://prometheus:9090/-/healthy
```

### Missing metrics
```bash
# Check scrape targets
curl http://localhost:9090/api/v1/targets

# Check specific exporter
curl http://localhost:9100/metrics  # node-exporter
curl http://localhost:8080/metrics  # cadvisor
curl http://localhost:9187/metrics  # postgres-exporter
```
```

#### 6.2 Update Main README

Add monitoring section to `/home/lionel/code/fraiseql-performance-assessment/README.md`:

```markdown
## Monitoring

The project includes a comprehensive monitoring stack:

- **Prometheus**: Metrics collection (http://localhost:9090)
- **Grafana**: Dashboards (http://localhost:3000, admin/admin)
- **Exporters**: node-exporter, cAdvisor, postgres-exporter

### Start Monitoring

```bash
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

See `monitoring/README.md` for detailed documentation.
```

---

## Execution Order

1. **Create Recording Rules** (Step 1)
   - Highest priority
   - Required for Prometheus to be fully functional
   - Affects dashboard performance

2. **Fix Healthcheck** (Step 2)
   - Important for production readiness
   - Ensures proper container orchestration

3. **Grafana Provisioning** (Step 3)
   - Enables automated setup
   - Required before dashboard creation

4. **Create Dashboard** (Step 4)
   - Largest task
   - Can be done incrementally (create basic structure, then add panels)

5. **Verification** (Step 5)
   - Ensures everything works
   - Identifies any remaining issues

6. **Documentation** (Step 6)
   - Helps future users
   - Documents the setup

---

## Success Criteria

✅ All monitoring containers healthy
✅ Prometheus loads recording rules (count > 0)
✅ Prometheus healthcheck passes
✅ Grafana accessible with auto-configured datasource
✅ Dashboard loads with all 15 panels
✅ Metrics visible in Prometheus UI
✅ Documentation complete and accurate

---

## Estimated Effort

- Recording Rules: 30-45 minutes
- Healthcheck Fix: 10-15 minutes
- Grafana Provisioning: 15-20 minutes
- Dashboard Creation: 60-90 minutes (largest task)
- Verification: 20-30 minutes
- Documentation: 20-30 minutes

**Total: 2.5-3.5 hours**

---

## Notes

- Dashboard panel queries should use recording rules where possible for performance
- Some metrics won't have data until framework containers are running - this is expected
- Grafana provisioning allows for easy dashboard version control
- Recording rules can be tuned based on actual query patterns
- Consider adding alerting rules in future phase

---

## Next Phase Dependencies

Before Phase 9 (actual performance testing):
1. All monitoring must be operational
2. Dashboards must be validated with sample data
3. Recording rules must be optimized for query patterns

The monitoring stack will be critical for:
- Real-time performance observation
- Framework comparison
- Bottleneck identification
- Report generation
