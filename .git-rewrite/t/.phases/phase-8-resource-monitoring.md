# Phase 8: Continuous Resource Monitoring

## Objective

Implement real-time resource monitoring during benchmark execution, capturing CPU, memory, network I/O, disk I/O, database metrics, and container-level statistics for comprehensive performance correlation analysis.

## Context

**Current State:**
- System metrics collected only after test completion (`run_comparative_benchmarks.py:699-733`)
- No continuous sampling during load
- Missing database-level metrics (connections, query stats)
- No container resource limits/usage tracking
- Cannot correlate performance spikes with resource usage

**Target State:**
- Continuous sampling at 1-second intervals during tests
- Per-container resource tracking (CPU, memory, network)
- PostgreSQL performance metrics (pg_stat_statements, connections)
- Time-series data for visualization
- Automatic anomaly detection in resource usage

## Files to Create/Modify

| File | Purpose |
|------|---------|
| `monitoring/resource-collector.py` | Python-based continuous metrics collector |
| `monitoring/prometheus.yml` | Enhanced Prometheus config |
| `monitoring/grafana/dashboards/benchmark.json` | Benchmark-specific dashboard |
| `monitoring/docker-compose.monitoring.yml` | Monitoring stack |
| `tests/perf/scripts/collect-metrics.sh` | Wrapper for metric collection |
| `run_comparative_benchmarks.py` | Integrate continuous monitoring |

## Implementation Steps

### Step 1: Enhanced Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 1s       # High-frequency during benchmarks
  evaluation_interval: 1s
  external_labels:
    benchmark: 'fraiseql-perf'

scrape_configs:
  # Node exporter for system metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'node_(cpu|memory|disk|network).*'
        action: keep

  # cAdvisor for container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    metric_relabel_configs:
      - source_labels: [container_label_com_docker_compose_service]
        target_label: service

  # PostgreSQL exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Framework-specific metrics
  - job_name: 'fraiseql'
    static_configs:
      - targets: ['fraiseql:4000']
    metrics_path: /metrics

  - job_name: 'strawberry'
    static_configs:
      - targets: ['strawberry:8001']
    metrics_path: /metrics

  - job_name: 'graphene'
    static_configs:
      - targets: ['graphene:8002']
    metrics_path: /metrics

  - job_name: 'fastapi-rest'
    static_configs:
      - targets: ['fastapi-rest:8003']
    metrics_path: /metrics

  - job_name: 'flask-rest'
    static_configs:
      - targets: ['flask-rest:8004']
    metrics_path: /metrics

  - job_name: 'apollo-server'
    static_configs:
      - targets: ['apollo-server:4002']
    metrics_path: /metrics

  - job_name: 'go-gqlgen'
    static_configs:
      - targets: ['go-gqlgen:4003']
    metrics_path: /metrics

  - job_name: 'gin-rest'
    static_configs:
      - targets: ['gin-rest:8006']
    metrics_path: /metrics

# Recording rules for derived metrics
rule_files:
  - 'rules/*.yml'
```

```yaml
# monitoring/rules/benchmark.yml
groups:
  - name: benchmark_derived
    interval: 1s
    rules:
      # Request rate per framework
      - record: framework:request_rate:1m
        expr: sum by (job) (rate(http_requests_total[1m]))

      # P95 latency per framework
      - record: framework:latency_p95:1m
        expr: histogram_quantile(0.95, sum by (job, le) (rate(http_request_duration_seconds_bucket[1m])))

      # Container CPU usage percentage
      - record: container:cpu_usage_percent
        expr: sum by (service) (rate(container_cpu_usage_seconds_total{container!=""}[30s])) * 100

      # Container memory usage
      - record: container:memory_usage_bytes
        expr: sum by (service) (container_memory_usage_bytes{container!=""})

      # PostgreSQL connections per database
      - record: postgres:connections
        expr: pg_stat_activity_count
```

### Step 2: Monitoring Docker Compose Stack

```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=7d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - benchmark-net

  grafana:
    image: grafana/grafana:10.2.0
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/var/lib/grafana/dashboards/benchmark.json
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - benchmark-net

  node-exporter:
    image: prom/node-exporter:v1.7.0
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"
    networks:
      - benchmark-net

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"
    privileged: true
    networks:
      - benchmark-net

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    environment:
      DATA_SOURCE_NAME: "postgresql://benchmark:benchmark123@postgres:5432/fraiseql_benchmark?sslmode=disable"
    ports:
      - "9187:9187"
    depends_on:
      - postgres
    networks:
      - benchmark-net

volumes:
  prometheus_data:
  grafana_data:

networks:
  benchmark-net:
    external: true
```

### Step 3: Resource Collector Script

```python
#!/usr/bin/env python3
"""
Continuous resource monitoring during benchmark execution.
Collects metrics at 1-second intervals and exports to CSV/JSON.
"""

import asyncio
import csv
import json
import os
import signal
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    cpu_user: float
    cpu_system: float
    cpu_iowait: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    memory_available_gb: float
    swap_used_gb: float
    disk_read_mb_s: float
    disk_write_mb_s: float
    net_recv_mb_s: float
    net_sent_mb_s: float
    load_1m: float
    load_5m: float
    load_15m: float


@dataclass
class ContainerMetrics:
    timestamp: float
    container_name: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    memory_percent: float
    net_rx_mb: float
    net_tx_mb: float
    block_read_mb: float
    block_write_mb: float


@dataclass
class PostgresMetrics:
    timestamp: float
    active_connections: int
    idle_connections: int
    waiting_connections: int
    total_connections: int
    max_connections: int
    db_size_mb: float
    xact_commit: int
    xact_rollback: int
    blks_read: int
    blks_hit: int
    cache_hit_ratio: float
    temp_files: int
    deadlocks: int


class ResourceCollector:
    def __init__(
        self,
        output_dir: str,
        prometheus_url: str = "http://localhost:9090",
        interval_seconds: float = 1.0,
        frameworks: List[str] = None
    ):
        self.output_dir = output_dir
        self.prometheus_url = prometheus_url
        self.interval = interval_seconds
        self.frameworks = frameworks or []
        self.running = False

        self.system_metrics: List[SystemMetrics] = []
        self.container_metrics: Dict[str, List[ContainerMetrics]] = {}
        self.postgres_metrics: List[PostgresMetrics] = []

        self._prev_disk_io = None
        self._prev_net_io = None
        self._prev_time = None

        os.makedirs(output_dir, exist_ok=True)

    async def start(self):
        """Start continuous metric collection"""
        self.running = True
        print(f"Starting resource collection (interval: {self.interval}s)")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while self.running:
                start_time = time.time()

                # Collect all metrics concurrently
                await asyncio.gather(
                    self._collect_system_metrics(),
                    self._collect_container_metrics(),
                    self._collect_postgres_metrics(),
                    return_exceptions=True
                )

                # Wait for next interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)
                await asyncio.sleep(sleep_time)

        finally:
            self._save_results()

    def stop(self):
        """Stop metric collection"""
        self.running = False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nReceived shutdown signal, saving results...")
        self.stop()

    async def _collect_system_metrics(self):
        """Collect system-level metrics using psutil"""
        if not HAS_PSUTIL:
            return

        current_time = time.time()

        # CPU metrics
        cpu_times = psutil.cpu_times_percent(interval=None)
        cpu_percent = psutil.cpu_percent(interval=None)

        # Memory metrics
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk I/O (calculate rate)
        disk_io = psutil.disk_io_counters()
        disk_read_rate = 0.0
        disk_write_rate = 0.0
        if self._prev_disk_io and self._prev_time:
            dt = current_time - self._prev_time
            if dt > 0:
                disk_read_rate = (disk_io.read_bytes - self._prev_disk_io.read_bytes) / dt / 1024 / 1024
                disk_write_rate = (disk_io.write_bytes - self._prev_disk_io.write_bytes) / dt / 1024 / 1024
        self._prev_disk_io = disk_io

        # Network I/O (calculate rate)
        net_io = psutil.net_io_counters()
        net_recv_rate = 0.0
        net_sent_rate = 0.0
        if self._prev_net_io and self._prev_time:
            dt = current_time - self._prev_time
            if dt > 0:
                net_recv_rate = (net_io.bytes_recv - self._prev_net_io.bytes_recv) / dt / 1024 / 1024
                net_sent_rate = (net_io.bytes_sent - self._prev_net_io.bytes_sent) / dt / 1024 / 1024
        self._prev_net_io = net_io
        self._prev_time = current_time

        # Load average
        load = psutil.getloadavg()

        metrics = SystemMetrics(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            cpu_user=cpu_times.user,
            cpu_system=cpu_times.system,
            cpu_iowait=getattr(cpu_times, 'iowait', 0),
            memory_total_gb=mem.total / (1024**3),
            memory_used_gb=mem.used / (1024**3),
            memory_percent=mem.percent,
            memory_available_gb=mem.available / (1024**3),
            swap_used_gb=swap.used / (1024**3),
            disk_read_mb_s=disk_read_rate,
            disk_write_mb_s=disk_write_rate,
            net_recv_mb_s=net_recv_rate,
            net_sent_mb_s=net_sent_rate,
            load_1m=load[0],
            load_5m=load[1],
            load_15m=load[2],
        )

        self.system_metrics.append(metrics)

    async def _collect_container_metrics(self):
        """Collect container metrics via Docker API or Prometheus"""
        try:
            async with aiohttp.ClientSession() as session:
                # Query Prometheus for container metrics
                query = 'container_cpu_usage_seconds_total{container!=""}'
                async with session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": query}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Process container metrics from Prometheus
                        # ... (implementation details)
        except Exception as e:
            pass  # Prometheus may not be available

    async def _collect_postgres_metrics(self):
        """Collect PostgreSQL metrics via Prometheus postgres_exporter"""
        current_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                queries = {
                    "active_connections": "pg_stat_activity_count{state='active'}",
                    "idle_connections": "pg_stat_activity_count{state='idle'}",
                    "total_connections": "sum(pg_stat_activity_count)",
                    "xact_commit": "pg_stat_database_xact_commit{datname='fraiseql_benchmark'}",
                    "xact_rollback": "pg_stat_database_xact_rollback{datname='fraiseql_benchmark'}",
                    "blks_read": "pg_stat_database_blks_read{datname='fraiseql_benchmark'}",
                    "blks_hit": "pg_stat_database_blks_hit{datname='fraiseql_benchmark'}",
                }

                results = {}
                for metric_name, query in queries.items():
                    async with session.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={"query": query}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data["data"]["result"]:
                                results[metric_name] = float(data["data"]["result"][0]["value"][1])

                if results:
                    blks_read = results.get("blks_read", 0)
                    blks_hit = results.get("blks_hit", 0)
                    cache_hit_ratio = blks_hit / (blks_read + blks_hit) if (blks_read + blks_hit) > 0 else 0

                    metrics = PostgresMetrics(
                        timestamp=current_time,
                        active_connections=int(results.get("active_connections", 0)),
                        idle_connections=int(results.get("idle_connections", 0)),
                        waiting_connections=0,
                        total_connections=int(results.get("total_connections", 0)),
                        max_connections=100,  # Default, could query pg_settings
                        db_size_mb=0,
                        xact_commit=int(results.get("xact_commit", 0)),
                        xact_rollback=int(results.get("xact_rollback", 0)),
                        blks_read=int(blks_read),
                        blks_hit=int(blks_hit),
                        cache_hit_ratio=cache_hit_ratio,
                        temp_files=0,
                        deadlocks=0,
                    )
                    self.postgres_metrics.append(metrics)

        except Exception as e:
            pass  # Prometheus may not be available

    def _save_results(self):
        """Save collected metrics to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save system metrics
        if self.system_metrics:
            csv_path = os.path.join(self.output_dir, f"system_metrics_{timestamp}.csv")
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.system_metrics[0]).keys())
                writer.writeheader()
                for m in self.system_metrics:
                    writer.writerow(asdict(m))
            print(f"Saved {len(self.system_metrics)} system metric samples to {csv_path}")

        # Save postgres metrics
        if self.postgres_metrics:
            csv_path = os.path.join(self.output_dir, f"postgres_metrics_{timestamp}.csv")
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.postgres_metrics[0]).keys())
                writer.writeheader()
                for m in self.postgres_metrics:
                    writer.writerow(asdict(m))
            print(f"Saved {len(self.postgres_metrics)} postgres metric samples to {csv_path}")

        # Save combined JSON
        json_path = os.path.join(self.output_dir, f"all_metrics_{timestamp}.json")
        with open(json_path, "w") as f:
            json.dump({
                "system": [asdict(m) for m in self.system_metrics],
                "postgres": [asdict(m) for m in self.postgres_metrics],
                "containers": {k: [asdict(m) for m in v] for k, v in self.container_metrics.items()},
            }, f, indent=2)
        print(f"Saved combined metrics to {json_path}")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Resource Collector")
    parser.add_argument("--output-dir", "-o", default="tests/perf/results/resources",
                        help="Output directory for metrics")
    parser.add_argument("--interval", "-i", type=float, default=1.0,
                        help="Collection interval in seconds")
    parser.add_argument("--prometheus-url", "-p", default="http://localhost:9090",
                        help="Prometheus server URL")
    parser.add_argument("--duration", "-d", type=int, default=0,
                        help="Collection duration in seconds (0 = until interrupted)")

    args = parser.parse_args()

    collector = ResourceCollector(
        output_dir=args.output_dir,
        prometheus_url=args.prometheus_url,
        interval_seconds=args.interval,
    )

    if args.duration > 0:
        # Run for specified duration
        async def timed_run():
            task = asyncio.create_task(collector.start())
            await asyncio.sleep(args.duration)
            collector.stop()
            await task

        await timed_run()
    else:
        # Run until interrupted
        await collector.start()


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Grafana Dashboard

```json
// monitoring/grafana/dashboards/benchmark.json
{
  "dashboard": {
    "title": "FraiseQL Benchmark Dashboard",
    "uid": "fraiseql-benchmark",
    "panels": [
      {
        "title": "Request Rate by Framework",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "sum by (job) (rate(http_requests_total[1m]))",
            "legendFormat": "{{job}}"
          }
        ]
      },
      {
        "title": "P95 Latency by Framework",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum by (job, le) (rate(http_request_duration_seconds_bucket[1m])))",
            "legendFormat": "{{job}}"
          }
        ]
      },
      {
        "title": "Container CPU Usage",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "sum by (name) (rate(container_cpu_usage_seconds_total{name=~\".*fraiseql.*|.*strawberry.*|.*graphene.*|.*fastapi.*|.*flask.*|.*apollo.*|.*gqlgen.*|.*gin.*\"}[1m])) * 100",
            "legendFormat": "{{name}}"
          }
        ]
      },
      {
        "title": "Container Memory Usage",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "container_memory_usage_bytes{name=~\".*fraiseql.*|.*strawberry.*|.*graphene.*|.*fastapi.*|.*flask.*|.*apollo.*|.*gqlgen.*|.*gin.*\"} / 1024 / 1024",
            "legendFormat": "{{name}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "decmbytes"
          }
        }
      },
      {
        "title": "PostgreSQL Connections",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "pg_stat_activity_count{state='active'}",
            "legendFormat": "Active"
          },
          {
            "expr": "pg_stat_activity_count{state='idle'}",
            "legendFormat": "Idle"
          }
        ]
      },
      {
        "title": "PostgreSQL Cache Hit Ratio",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 16},
        "targets": [
          {
            "expr": "pg_stat_database_blks_hit{datname='fraiseql_benchmark'} / (pg_stat_database_blks_hit{datname='fraiseql_benchmark'} + pg_stat_database_blks_read{datname='fraiseql_benchmark'})"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 0.9, "color": "yellow"},
                {"value": 0.99, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "title": "System Load Average",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 16},
        "targets": [
          {
            "expr": "node_load1",
            "legendFormat": "1 min"
          },
          {
            "expr": "node_load5",
            "legendFormat": "5 min"
          },
          {
            "expr": "node_load15",
            "legendFormat": "15 min"
          }
        ]
      }
    ]
  }
}
```

### Step 5: Integration with Benchmark Runner

```python
# Add to run_comparative_benchmarks.py

class ComparativeBenchmarkAnalyzer:
    def __init__(self, ...):
        # ... existing init
        self.resource_collector = None

    async def run_with_monitoring(self):
        """Run benchmarks with continuous resource monitoring"""
        # Start resource collector in background
        from monitoring.resource_collector import ResourceCollector

        collector = ResourceCollector(
            output_dir=f"{self.results_dir}/resources",
            interval_seconds=1.0
        )

        # Run collector in background task
        collector_task = asyncio.create_task(collector.start())

        try:
            # Run benchmarks
            await self.run_comparative_benchmarks_async()
        finally:
            # Stop collector and save results
            collector.stop()
            await collector_task

    def start_monitoring_stack(self):
        """Start Prometheus, Grafana, exporters"""
        subprocess.run([
            "docker-compose",
            "-f", "monitoring/docker-compose.monitoring.yml",
            "up", "-d"
        ], check=True)
        print("Monitoring stack started")
        print("  Prometheus: http://localhost:9090")
        print("  Grafana:    http://localhost:3000 (admin/admin)")

    def stop_monitoring_stack(self):
        """Stop monitoring stack"""
        subprocess.run([
            "docker-compose",
            "-f", "monitoring/docker-compose.monitoring.yml",
            "down"
        ], check=True)
```

## Verification Commands

```bash
# Start monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Verify Prometheus is scraping
curl -s "http://localhost:9090/api/v1/targets" | jq '.data.activeTargets | length'
# Should show number of configured targets

# Verify postgres_exporter
curl -s "http://localhost:9187/metrics" | grep pg_stat

# Start resource collection during test
python monitoring/resource-collector.py \
  --output-dir tests/perf/results/resources \
  --interval 1 \
  --duration 300 &

# Run benchmark
python run_comparative_benchmarks.py --framework fraiseql

# Check collected metrics
ls -la tests/perf/results/resources/
cat tests/perf/results/resources/system_metrics_*.csv | head

# View in Grafana
open http://localhost:3000/d/fraiseql-benchmark
```

## Acceptance Criteria

- [ ] Prometheus scrapes all framework metrics endpoints
- [ ] cAdvisor provides container-level metrics
- [ ] postgres_exporter provides PostgreSQL metrics
- [ ] Resource collector samples at 1-second intervals
- [ ] CSV output includes timestamp, CPU, memory, disk I/O, network I/O
- [ ] Grafana dashboard visualizes all metrics
- [ ] Benchmark runner integrates resource collection
- [ ] Time-series data allows correlation with response time spikes

## DO NOT

- Sample slower than 1 second during benchmarks
- Ignore container resource limits
- Skip PostgreSQL connection pool metrics
- Collect metrics only before/after tests (not during)
- Use polling for metrics (prefer push/scrape model)

## Dependencies

```txt
# Python requirements
aiohttp>=3.9.0
psutil>=5.9.0

# Docker images
prom/prometheus:v2.48.0
grafana/grafana:10.2.0
prom/node-exporter:v1.7.0
gcr.io/cadvisor/cadvisor:v0.47.0
prometheuscommunity/postgres-exporter:v0.15.0
```

## Estimated Complexity

**Medium-High** - Requires Docker Compose orchestration, Prometheus configuration, and async Python for continuous collection.
