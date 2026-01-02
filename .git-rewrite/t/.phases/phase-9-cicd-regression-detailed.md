# FraiseQL Performance Assessment - Phase 9: CI/CD Integration & Regression Detection

## Phase Overview

**Goal**: Implement automated CI/CD pipelines for performance testing, baseline management, regression detection with configurable thresholds, and historical trend analysis for long-term performance tracking.

**Scope**: Set up GitHub Actions workflows, baseline management, regression detection, and trend reporting.

**Success Criteria**:
- GitHub Actions workflow runs on PR to framework/database paths
- Baseline comparison detects >15% response time regression
- PR comments include performance delta summary
- Nightly benchmarks run at 2 AM UTC
- Trend report shows historical performance over time

## Learning Objectives

As a junior engineer, by completing Phase 9 you will learn:

1. **Metrics Collection**: Prometheus exposition format, metric types, labels
2. **Container Monitoring**: cAdvisor integration, Docker stats API
3. **Database Monitoring**: PostgreSQL exporter, query statistics, connection pooling metrics
4. **Time-Series Data**: Grafana dashboards, query optimization, alerting
5. **System Monitoring**: Node exporter, kernel metrics, hardware utilization
6. **Async Data Collection**: Python aiohttp for concurrent metric gathering
7. **Real-time Analysis**: Performance correlation, bottleneck identification, anomaly detection

## Implementation Steps

### Step 1: Prometheus Configuration
**Estimated Time**: 45 minutes

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 1s
  evaluation_interval: 1s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  - job_name: 'fraiseql'
    static_configs:
      - targets: ['fraiseql:4000']
    metrics_path: /metrics
```

### Step 2: Resource Collector Implementation
**Estimated Time**: 1.5 hours

```python
# monitoring/resource-collector.py
import asyncio
import aiohttp
import psutil
import csv
import json
from datetime import datetime

class ResourceCollector:
    def __init__(self, prometheus_url="http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.system_metrics = []
        
    async def collect_system_metrics(self):
        """Collect system-level metrics"""
        current_time = time.time()
        
        # CPU, memory, disk, network metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_io_counters()
        net = psutil.net_io_counters()
        
        metrics = {
            "timestamp": current_time,
            "cpu_percent": cpu_percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_percent": memory.percent,
            "disk_read_mb_s": disk.read_bytes / (1024**2) if disk else 0,
            "disk_write_mb_s": disk.write_bytes / (1024**2) if disk else 0,
            "net_recv_mb_s": net.bytes_recv / (1024**2) if net else 0,
            "net_sent_mb_s": net.bytes_sent / (1024**2) if net else 0
        }
        
        self.system_metrics.append(metrics)
    
    async def collect_prometheus_metrics(self):
        """Collect metrics from Prometheus"""
        async with aiohttp.ClientSession() as session:
            # Query container CPU usage
            query = 'rate(container_cpu_usage_seconds_total[30s]) * 100'
            async with session.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Process container metrics...
    
    async def start_collection(self, duration_seconds=300):
        """Run collection for specified duration"""
        print(f"Starting resource collection for {duration_seconds}s")
        
        tasks = []
        for _ in range(duration_seconds):
            tasks.append(self.collect_system_metrics())
            tasks.append(self.collect_prometheus_metrics())
            await asyncio.sleep(1)
        
        await asyncio.gather(*tasks)
        self.save_results()
    
    def save_results(self):
        """Save collected metrics to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save system metrics
        with open(f"system_metrics_{timestamp}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.system_metrics[0].keys())
            writer.writeheader()
            writer.writerows(self.system_metrics)
```

### Step 3: Grafana Dashboard
**Estimated Time**: 1 hour

```json
{
  "dashboard": {
    "title": "FraiseQL Benchmark Dashboard",
    "panels": [
      {
        "title": "Request Rate by Framework",
        "type": "timeseries",
        "targets": [{
          "expr": "sum by (job) (rate(http_requests_total[1m]))",
          "legendFormat": "{{job}}"
        }]
      },
      {
        "title": "Container CPU Usage",
        "type": "timeseries", 
        "targets": [{
          "expr": "rate(container_cpu_usage_seconds_total{name=~\"fraiseql|strawberry|graphene\"}[1m]) * 100",
          "legendFormat": "{{name}}"
        }]
      },
      {
        "title": "PostgreSQL Connections",
        "type": "timeseries",
        "targets": [
          {"expr": "pg_stat_activity_count{state='active'}", "legendFormat": "Active"},
          {"expr": "pg_stat_activity_count{state='idle'}", "legendFormat": "Idle"}
        ]
      }
    ]
  }
}
```

## Best Practices Learned

### 1. Monitoring Architecture
- Use pull-based metrics collection (Prometheus scraping)
- Implement proper metric naming and labeling
- Use appropriate metric types (counter, gauge, histogram)
- Design dashboards for operational visibility

### 2. Resource Correlation
- Collect metrics at matching intervals
- Use time-series databases for efficient storage
- Implement alerting on resource thresholds
- Correlate application metrics with system resources

## Phase Sign-off

**Phase 8 Status**: ☐ Ready for Phase 9 ☐ Needs Remediation

**Monitoring Stack**:
- Prometheus configured with 1s scrape interval
- cAdvisor for container metrics
- node-exporter for system metrics
- postgres-exporter for database metrics

**Dashboards Created**:
- Real-time performance visualization
- Resource usage correlation
- Anomaly detection capabilities</content>
<parameter name="filePath">.phases/phase-8-resource-monitoring-detailed.md