# 🚀 Phase 8 Quick Start

**Status**: ✅ Complete and Operational

---

## Start Monitoring (30 seconds)

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

## Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **cAdvisor** | http://localhost:8080 | - |

## View Performance Dashboard

1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Click **Dashboards** → **FraiseQL Performance Benchmark**
4. Set time range to "Last 15 minutes" with 5s refresh

## Quick Health Check

```bash
# All containers running?
docker ps | grep -E "prometheus|grafana|cadvisor|node-exporter|postgres-exporter"

# All targets healthy?
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Should return: 12

# Grafana healthy?
curl -s http://localhost:3000/api/health | jq '.database'
# Should return: "ok"
```

## Common Queries

```bash
# CPU usage per framework
curl -s "http://localhost:9090/api/v1/query?query=rate(container_cpu_usage_seconds_total{name=~\"fraiseql.*\"}[1m])*100" | jq .

# Database cache hit ratio
curl -s "http://localhost:9090/api/v1/query?query=pg_stat_database_blks_hit/(pg_stat_database_blks_hit+pg_stat_database_blks_read)*100" | jq .

# Request rate
curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total[1m])" | jq .
```

## Troubleshooting

**Dashboard not loading?**
```bash
# Restart Grafana
docker-compose -f monitoring/docker-compose.monitoring.yml restart grafana
```

**No metrics?**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload
```

**High CPU usage?**
```bash
# Reduce scrape interval (edit monitoring/prometheus.yml)
scrape_interval: 5s  # Instead of 1s
```

## Files Reference

```
monitoring/
├── docker-compose.monitoring.yml    # Start/stop monitoring
├── prometheus.yml                   # Scrape configuration
├── prometheus/rules/benchmark.yml   # 40+ recording rules
├── grafana/provisioning/
│   ├── datasources/prometheus.yml   # Auto-configured datasource
│   └── dashboards/
│       ├── default.yml              # Provisioning config
│       └── fraiseql-performance.json # Main dashboard
└── README.md                        # Full documentation
```

## Next: Run Benchmarks

With monitoring running, start frameworks and run benchmarks:

```bash
# Start all frameworks
docker-compose up -d

# Run a single workload
cd tests/perf
./scripts/run-workload.sh simple fraiseql 10m

# Watch metrics in Grafana during execution
# Open: http://localhost:3000
```

---

**For detailed docs**: See `monitoring/README.md`  
**For Phase 8 completion details**: See `.phases/PHASE_8_FINAL_COMPLETION.md`
