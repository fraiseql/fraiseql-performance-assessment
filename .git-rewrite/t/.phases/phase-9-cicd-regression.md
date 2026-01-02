# Phase 9: CI/CD Integration & Regression Detection

## Objective

Implement automated CI/CD pipelines for performance testing, baseline management, regression detection with configurable thresholds, and historical trend analysis for long-term performance tracking.

## Context

**Current State:**
- No CI/CD integration
- No baseline storage or comparison
- No automated regression detection
- No historical trend analysis
- Manual benchmark execution only

**Target State:**
- GitHub Actions workflow for automated benchmarks
- Baseline storage with versioning
- Configurable regression thresholds per metric
- Automatic PR comments with performance delta
- Historical trend visualization
- Nightly benchmark runs

## Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/benchmark.yml` | Main benchmark workflow |
| `.github/workflows/nightly-benchmark.yml` | Scheduled nightly runs |
| `ci/baseline-thresholds.json` | Regression threshold configuration |
| `ci/compare-results.py` | Baseline comparison script |
| `ci/update-baseline.py` | Baseline management script |
| `ci/generate-trend-report.py` | Historical trend analysis |
| `tests/perf/results/baseline/` | Baseline storage directory |

## Implementation Steps

### Step 1: GitHub Actions Benchmark Workflow

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmark

on:
  pull_request:
    paths:
      - 'frameworks/**'
      - 'database/**'
      - 'tests/perf/**'
  workflow_dispatch:
    inputs:
      frameworks:
        description: 'Frameworks to benchmark (comma-separated, or "all")'
        required: false
        default: 'all'
      threads:
        description: 'Number of concurrent threads'
        required: false
        default: '50'
      duration:
        description: 'Test duration in seconds'
        required: false
        default: '120'

env:
  DOCKER_BUILDKIT: 1
  COMPOSE_DOCKER_CLI_BUILD: 1

jobs:
  benchmark:
    name: Run Benchmarks
    runs-on: ubuntu-latest
    timeout-minutes: 60

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: fraiseql_benchmark
          POSTGRES_USER: benchmark
          POSTGRES_PASSWORD: benchmark123
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install scipy numpy pandas

      - name: Set up JMeter
        run: |
          wget -q https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz
          tar -xzf apache-jmeter-5.6.3.tgz
          echo "$PWD/apache-jmeter-5.6.3/bin" >> $GITHUB_PATH

      - name: Initialize database
        run: |
          PGPASSWORD=benchmark123 psql -h localhost -U benchmark -d fraiseql_benchmark -f database/02-schema.sql
          PGPASSWORD=benchmark123 psql -h localhost -U benchmark -d fraiseql_benchmark -f database/fraiseql_cqrs_schema.sql
          PGPASSWORD=benchmark123 psql -h localhost -U benchmark -d fraiseql_benchmark -f database/03-data.sql

      - name: Determine frameworks to test
        id: frameworks
        run: |
          if [ "${{ github.event.inputs.frameworks }}" = "all" ] || [ -z "${{ github.event.inputs.frameworks }}" ]; then
            echo "frameworks=fraiseql,strawberry,graphene,fastapi-rest,flask-rest" >> $GITHUB_OUTPUT
          else
            echo "frameworks=${{ github.event.inputs.frameworks }}" >> $GITHUB_OUTPUT
          fi

      - name: Build framework containers
        run: |
          IFS=',' read -ra FRAMEWORKS <<< "${{ steps.frameworks.outputs.frameworks }}"
          for framework in "${FRAMEWORKS[@]}"; do
            docker-compose build "$framework"
          done

      - name: Run benchmarks
        run: |
          python run_comparative_benchmarks.py \
            --framework ${{ steps.frameworks.outputs.frameworks }} \
            --threads ${{ github.event.inputs.threads || '50' }} \
            --duration ${{ github.event.inputs.duration || '120' }}

      - name: Compare with baseline
        id: compare
        run: |
          python ci/compare-results.py \
            --results tests/perf/results/comparative_analysis.json \
            --baseline tests/perf/results/baseline/baseline.json \
            --thresholds ci/baseline-thresholds.json \
            --output comparison_report.json

          # Check for regressions
          if [ -f regression_detected ]; then
            echo "regression=true" >> $GITHUB_OUTPUT
          else
            echo "regression=false" >> $GITHUB_OUTPUT
          fi

      - name: Generate summary report
        run: |
          python ci/generate-summary.py \
            --comparison comparison_report.json \
            --output benchmark_summary.md

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('benchmark_summary.md', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });

      - name: Upload results artifact
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results-${{ github.run_number }}
          path: |
            tests/perf/results/
            comparison_report.json
            benchmark_summary.md
          retention-days: 30

      - name: Fail on regression
        if: steps.compare.outputs.regression == 'true'
        run: |
          echo "Performance regression detected!"
          cat comparison_report.json | jq '.regressions'
          exit 1

  update-baseline:
    name: Update Baseline
    needs: benchmark
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download benchmark results
        uses: actions/download-artifact@v4
        with:
          name: benchmark-results-${{ github.run_number }}

      - name: Update baseline
        run: |
          python ci/update-baseline.py \
            --results tests/perf/results/comparative_analysis.json \
            --baseline tests/perf/results/baseline/baseline.json

      - name: Commit baseline update
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: update performance baseline [skip ci]"
          file_pattern: tests/perf/results/baseline/*.json
```

### Step 2: Nightly Benchmark Workflow

```yaml
# .github/workflows/nightly-benchmark.yml
name: Nightly Performance Benchmark

on:
  schedule:
    - cron: '0 2 * * *'  # Run at 2 AM UTC daily
  workflow_dispatch:

jobs:
  nightly-benchmark:
    name: Full Benchmark Suite
    runs-on: ubuntu-latest
    timeout-minutes: 180  # 3 hours for comprehensive testing

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up environment
        # ... (same as benchmark.yml)

      - name: Run comprehensive benchmarks
        run: |
          # Run all frameworks with high thread counts
          python run_comparative_benchmarks.py \
            --framework all \
            --threads 100 \
            --duration 300 \
            --warmup 120 \
            --workloads simple,parameterized,aggregation,pagination,fulltext,deep-traversal,mutations,mixed

      - name: Generate trend report
        run: |
          python ci/generate-trend-report.py \
            --results-dir tests/perf/results/history \
            --output trend_report.html

      - name: Upload to S3/GCS (optional)
        if: env.AWS_ACCESS_KEY_ID != ''
        run: |
          aws s3 cp tests/perf/results/history/ s3://benchmark-results/$(date +%Y-%m-%d)/ --recursive

      - name: Send notification on regression
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Nightly benchmark detected performance regression!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Nightly Benchmark Failed*\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Details>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Step 3: Baseline Thresholds Configuration

```json
// ci/baseline-thresholds.json
{
  "version": "1.0",
  "description": "Performance regression thresholds",

  "global": {
    "response_time_regression_percent": 15,
    "throughput_regression_percent": 10,
    "error_rate_max_percent": 1,
    "p99_max_ms": 500
  },

  "frameworks": {
    "fraiseql": {
      "simple_query": {
        "max_p95_ms": 10,
        "max_p99_ms": 20,
        "min_throughput_rps": 5000,
        "max_avg_ms": 5
      },
      "parameterized_query": {
        "max_p95_ms": 25,
        "max_p99_ms": 50,
        "min_throughput_rps": 2000,
        "max_avg_ms": 15
      },
      "complex_query": {
        "max_p95_ms": 100,
        "max_p99_ms": 200,
        "min_throughput_rps": 500,
        "max_avg_ms": 50
      },
      "aggregation": {
        "max_p95_ms": 150,
        "max_p99_ms": 300,
        "min_throughput_rps": 300
      },
      "deep_traversal": {
        "max_p95_ms": 200,
        "max_p99_ms": 400,
        "min_throughput_rps": 200,
        "max_query_count": 5
      },
      "mutation": {
        "max_p95_ms": 50,
        "max_p99_ms": 100,
        "min_throughput_rps": 1000
      }
    },

    "strawberry": {
      "simple_query": {
        "max_p95_ms": 15,
        "max_p99_ms": 30,
        "min_throughput_rps": 3000
      },
      "deep_traversal": {
        "max_p95_ms": 500,
        "max_p99_ms": 1000,
        "notes": "Expected N+1 behavior"
      }
    },

    "graphene": {
      "simple_query": {
        "max_p95_ms": 15,
        "max_p99_ms": 30,
        "min_throughput_rps": 3000
      }
    },

    "fastapi-rest": {
      "simple_query": {
        "max_p95_ms": 8,
        "max_p99_ms": 15,
        "min_throughput_rps": 6000
      }
    },

    "flask-rest": {
      "simple_query": {
        "max_p95_ms": 10,
        "max_p99_ms": 20,
        "min_throughput_rps": 4000
      }
    },

    "apollo-server": {
      "simple_query": {
        "max_p95_ms": 12,
        "max_p99_ms": 25,
        "min_throughput_rps": 4000
      }
    },

    "go-gqlgen": {
      "simple_query": {
        "max_p95_ms": 5,
        "max_p99_ms": 10,
        "min_throughput_rps": 10000,
        "notes": "Expected highest performance due to compiled Go"
      },
      "deep_traversal": {
        "max_p95_ms": 50,
        "max_p99_ms": 100,
        "min_throughput_rps": 2000
      }
    },

    "gin-rest": {
      "simple_query": {
        "max_p95_ms": 3,
        "max_p99_ms": 8,
        "min_throughput_rps": 15000,
        "notes": "Expected highest REST performance"
      }
    }
  },

  "workloads": {
    "mixed": {
      "max_p95_ms": 100,
      "max_p99_ms": 250,
      "min_throughput_rps": 1000,
      "max_error_rate_percent": 0.5
    }
  }
}
```

### Step 4: Baseline Comparison Script

```python
#!/usr/bin/env python3
"""
Compare benchmark results against baseline and detect regressions.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Regression:
    framework: str
    metric: str
    baseline_value: float
    current_value: float
    threshold_percent: float
    actual_delta_percent: float
    severity: str  # "warning", "error", "critical"


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def calculate_delta_percent(baseline: float, current: float) -> float:
    if baseline == 0:
        return 0 if current == 0 else float('inf')
    return ((current - baseline) / baseline) * 100


def compare_results(
    results: dict,
    baseline: dict,
    thresholds: dict
) -> Dict[str, any]:
    """Compare current results against baseline using thresholds"""

    regressions: List[Regression] = []
    improvements: List[dict] = []
    comparisons: Dict[str, dict] = {}

    global_thresholds = thresholds.get("global", {})
    framework_thresholds = thresholds.get("frameworks", {})

    current_stats = results.get("statistics", {})
    baseline_stats = baseline.get("statistics", {})

    for framework, current in current_stats.items():
        if framework not in baseline_stats:
            continue

        base = baseline_stats[framework]
        fw_thresholds = framework_thresholds.get(framework, {})

        comparison = {
            "framework": framework,
            "metrics": {},
            "regressions": [],
            "improvements": []
        }

        # Compare each metric
        metrics_to_compare = [
            ("avg_response_time", "max_avg_ms", "lower_is_better"),
            ("p95_response_time", "max_p95_ms", "lower_is_better"),
            ("p99_response_time", "max_p99_ms", "lower_is_better"),
            ("throughput_rps", "min_throughput_rps", "higher_is_better"),
            ("success_rate", None, "higher_is_better"),
        ]

        for metric, threshold_key, direction in metrics_to_compare:
            if metric not in current or metric not in base:
                continue

            current_val = current[metric]
            baseline_val = base[metric]
            delta_percent = calculate_delta_percent(baseline_val, current_val)

            comparison["metrics"][metric] = {
                "baseline": baseline_val,
                "current": current_val,
                "delta_percent": delta_percent
            }

            # Check regression based on direction
            regression_threshold = global_thresholds.get(
                "response_time_regression_percent" if "response_time" in metric
                else "throughput_regression_percent",
                15
            )

            is_regression = False
            if direction == "lower_is_better" and delta_percent > regression_threshold:
                is_regression = True
            elif direction == "higher_is_better" and delta_percent < -regression_threshold:
                is_regression = True

            if is_regression:
                severity = "warning"
                if abs(delta_percent) > regression_threshold * 2:
                    severity = "error"
                if abs(delta_percent) > regression_threshold * 3:
                    severity = "critical"

                reg = Regression(
                    framework=framework,
                    metric=metric,
                    baseline_value=baseline_val,
                    current_value=current_val,
                    threshold_percent=regression_threshold,
                    actual_delta_percent=delta_percent,
                    severity=severity
                )
                regressions.append(reg)
                comparison["regressions"].append({
                    "metric": metric,
                    "delta_percent": delta_percent,
                    "severity": severity
                })

            # Check for improvements
            elif (direction == "lower_is_better" and delta_percent < -10) or \
                 (direction == "higher_is_better" and delta_percent > 10):
                comparison["improvements"].append({
                    "metric": metric,
                    "delta_percent": delta_percent
                })
                improvements.append({
                    "framework": framework,
                    "metric": metric,
                    "delta_percent": delta_percent
                })

            # Check absolute thresholds
            if threshold_key and threshold_key in fw_thresholds.get("simple_query", {}):
                threshold_val = fw_thresholds["simple_query"][threshold_key]
                if direction == "lower_is_better" and current_val > threshold_val:
                    regressions.append(Regression(
                        framework=framework,
                        metric=f"{metric}_absolute",
                        baseline_value=threshold_val,
                        current_value=current_val,
                        threshold_percent=0,
                        actual_delta_percent=calculate_delta_percent(threshold_val, current_val),
                        severity="error"
                    ))
                elif direction == "higher_is_better" and current_val < threshold_val:
                    regressions.append(Regression(
                        framework=framework,
                        metric=f"{metric}_absolute",
                        baseline_value=threshold_val,
                        current_value=current_val,
                        threshold_percent=0,
                        actual_delta_percent=calculate_delta_percent(threshold_val, current_val),
                        severity="error"
                    ))

        comparisons[framework] = comparison

    return {
        "regressions": [
            {
                "framework": r.framework,
                "metric": r.metric,
                "baseline": r.baseline_value,
                "current": r.current_value,
                "threshold_percent": r.threshold_percent,
                "actual_delta_percent": r.actual_delta_percent,
                "severity": r.severity
            }
            for r in regressions
        ],
        "improvements": improvements,
        "comparisons": comparisons,
        "summary": {
            "total_regressions": len(regressions),
            "critical_regressions": len([r for r in regressions if r.severity == "critical"]),
            "error_regressions": len([r for r in regressions if r.severity == "error"]),
            "warning_regressions": len([r for r in regressions if r.severity == "warning"]),
            "total_improvements": len(improvements),
            "frameworks_compared": len(comparisons)
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Compare benchmark results against baseline")
    parser.add_argument("--results", "-r", required=True, help="Current results JSON file")
    parser.add_argument("--baseline", "-b", required=True, help="Baseline JSON file")
    parser.add_argument("--thresholds", "-t", required=True, help="Thresholds JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output comparison report JSON")

    args = parser.parse_args()

    results = load_json(args.results)
    baseline = load_json(args.baseline)
    thresholds = load_json(args.thresholds)

    comparison = compare_results(results, baseline, thresholds)

    with open(args.output, "w") as f:
        json.dump(comparison, f, indent=2)

    # Create regression flag file if any critical/error regressions
    if comparison["summary"]["critical_regressions"] > 0 or \
       comparison["summary"]["error_regressions"] > 0:
        with open("regression_detected", "w") as f:
            f.write("true")
        sys.exit(1)

    print(f"Comparison complete: {comparison['summary']['total_regressions']} regressions, "
          f"{comparison['summary']['total_improvements']} improvements")


if __name__ == "__main__":
    main()
```

### Step 5: Trend Report Generator

```python
#!/usr/bin/env python3
"""
Generate historical trend analysis report from benchmark history.
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List
import statistics


def load_history(results_dir: str) -> List[dict]:
    """Load all historical results"""
    history = []

    for filename in sorted(os.listdir(results_dir)):
        if filename.endswith(".json"):
            filepath = os.path.join(results_dir, filename)
            with open(filepath) as f:
                data = json.load(f)
                data["_filename"] = filename
                history.append(data)

    return history


def calculate_trends(history: List[dict]) -> Dict[str, dict]:
    """Calculate performance trends over time"""
    trends = {}

    for framework in ["fraiseql", "strawberry", "graphene", "fastapi-rest", "flask-rest",
                      "apollo-server", "go-gqlgen", "gin-rest"]:
        framework_data = []

        for run in history:
            stats = run.get("statistics", {}).get(framework, {})
            if stats:
                framework_data.append({
                    "timestamp": run.get("timestamp", ""),
                    "avg_response_time": stats.get("avg_response_time", 0),
                    "p95_response_time": stats.get("p95_response_time", 0),
                    "p99_response_time": stats.get("p99_response_time", 0),
                    "throughput_rps": stats.get("throughput_rps", 0),
                })

        if framework_data:
            avg_times = [d["avg_response_time"] for d in framework_data]
            p95_times = [d["p95_response_time"] for d in framework_data]
            throughputs = [d["throughput_rps"] for d in framework_data]

            trends[framework] = {
                "data_points": len(framework_data),
                "avg_response_time": {
                    "mean": statistics.mean(avg_times),
                    "stdev": statistics.stdev(avg_times) if len(avg_times) > 1 else 0,
                    "min": min(avg_times),
                    "max": max(avg_times),
                    "trend": "stable" if len(avg_times) < 3 else
                             "improving" if avg_times[-1] < avg_times[0] * 0.9 else
                             "degrading" if avg_times[-1] > avg_times[0] * 1.1 else "stable"
                },
                "p95_response_time": {
                    "mean": statistics.mean(p95_times),
                    "stdev": statistics.stdev(p95_times) if len(p95_times) > 1 else 0,
                    "trend": "stable" if len(p95_times) < 3 else
                             "improving" if p95_times[-1] < p95_times[0] * 0.9 else
                             "degrading" if p95_times[-1] > p95_times[0] * 1.1 else "stable"
                },
                "throughput_rps": {
                    "mean": statistics.mean(throughputs),
                    "stdev": statistics.stdev(throughputs) if len(throughputs) > 1 else 0,
                    "trend": "stable" if len(throughputs) < 3 else
                             "improving" if throughputs[-1] > throughputs[0] * 1.1 else
                             "degrading" if throughputs[-1] < throughputs[0] * 0.9 else "stable"
                },
                "history": framework_data
            }

    return trends


def generate_html_report(trends: Dict[str, dict], output_path: str):
    """Generate HTML trend report with charts"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>FraiseQL Benchmark Trends</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .chart-container { width: 800px; height: 400px; margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .trend-improving { color: green; }
        .trend-degrading { color: red; }
        .trend-stable { color: gray; }
    </style>
</head>
<body>
    <h1>FraiseQL Performance Benchmark Trends</h1>
    <p>Generated: """ + datetime.now().isoformat() + """</p>

    <h2>Summary Table</h2>
    <table>
        <tr>
            <th>Framework</th>
            <th>Avg Response Time (ms)</th>
            <th>P95 Response Time (ms)</th>
            <th>Throughput (RPS)</th>
            <th>Overall Trend</th>
        </tr>
"""

    for framework, data in sorted(trends.items()):
        avg_trend = data["avg_response_time"]["trend"]
        p95_trend = data["p95_response_time"]["trend"]
        throughput_trend = data["throughput_rps"]["trend"]

        # Determine overall trend
        trend_scores = {"improving": 1, "stable": 0, "degrading": -1}
        overall_score = (trend_scores[avg_trend] + trend_scores[p95_trend] + trend_scores[throughput_trend]) / 3
        overall_trend = "improving" if overall_score > 0.3 else "degrading" if overall_score < -0.3 else "stable"

        html += f"""
        <tr>
            <td>{framework}</td>
            <td>{data['avg_response_time']['mean']:.2f} (±{data['avg_response_time']['stdev']:.2f}) <span class="trend-{avg_trend}">[{avg_trend}]</span></td>
            <td>{data['p95_response_time']['mean']:.2f} (±{data['p95_response_time']['stdev']:.2f}) <span class="trend-{p95_trend}">[{p95_trend}]</span></td>
            <td>{data['throughput_rps']['mean']:.0f} (±{data['throughput_rps']['stdev']:.0f}) <span class="trend-{throughput_trend}">[{throughput_trend}]</span></td>
            <td class="trend-{overall_trend}">{overall_trend.upper()}</td>
        </tr>
"""

    html += """
    </table>

    <h2>Response Time Trends</h2>
    <div class="chart-container">
        <canvas id="responseTimeChart"></canvas>
    </div>

    <h2>Throughput Trends</h2>
    <div class="chart-container">
        <canvas id="throughputChart"></canvas>
    </div>

    <script>
        // Response Time Chart
        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        new Chart(responseTimeCtx, {
            type: 'line',
            data: {
                labels: """ + json.dumps([d.get("timestamp", "")[:10] for d in list(trends.values())[0].get("history", [])]) + """,
                datasets: [
"""

    colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#C9CBCF", "#7CFC00"]
    for i, (framework, data) in enumerate(sorted(trends.items())):
        html += f"""
                    {{
                        label: '{framework}',
                        data: {json.dumps([d['p95_response_time'] for d in data.get('history', [])])},
                        borderColor: '{colors[i % len(colors)]}',
                        fill: false
                    }},
"""

    html += """
                ]
            },
            options: {
                responsive: true,
                plugins: { title: { display: true, text: 'P95 Response Time (ms)' } },
                scales: { y: { beginAtZero: true } }
            }
        });

        // Throughput Chart
        const throughputCtx = document.getElementById('throughputChart').getContext('2d');
        new Chart(throughputCtx, {
            type: 'line',
            data: {
                labels: """ + json.dumps([d.get("timestamp", "")[:10] for d in list(trends.values())[0].get("history", [])]) + """,
                datasets: [
"""

    for i, (framework, data) in enumerate(sorted(trends.items())):
        html += f"""
                    {{
                        label: '{framework}',
                        data: {json.dumps([d['throughput_rps'] for d in data.get('history', [])])},
                        borderColor: '{colors[i % len(colors)]}',
                        fill: false
                    }},
"""

    html += """
                ]
            },
            options: {
                responsive: true,
                plugins: { title: { display: true, text: 'Throughput (Requests/Second)' } },
                scales: { y: { beginAtZero: true } }
            }
        });
    </script>
</body>
</html>
"""

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Trend report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate trend analysis report")
    parser.add_argument("--results-dir", "-r", required=True, help="Directory containing historical results")
    parser.add_argument("--output", "-o", required=True, help="Output HTML report path")

    args = parser.parse_args()

    history = load_history(args.results_dir)
    if not history:
        print("No historical data found")
        return

    trends = calculate_trends(history)
    generate_html_report(trends, args.output)


if __name__ == "__main__":
    main()
```

## Verification Commands

```bash
# Test comparison script locally
python ci/compare-results.py \
  --results tests/perf/results/comparative_analysis.json \
  --baseline tests/perf/results/baseline/baseline.json \
  --thresholds ci/baseline-thresholds.json \
  --output comparison_test.json

cat comparison_test.json | jq '.summary'

# Generate trend report from history
python ci/generate-trend-report.py \
  --results-dir tests/perf/results/history \
  --output tests/perf/results/trend_report.html

# Validate GitHub Actions workflow
act -l  # List available jobs
act push -n  # Dry run

# Test threshold configuration
python -c "
import json
with open('ci/baseline-thresholds.json') as f:
    t = json.load(f)
    print(f'Frameworks configured: {list(t[\"frameworks\"].keys())}')
    print(f'Global regression threshold: {t[\"global\"][\"response_time_regression_percent\"]}%')
"
```

## Acceptance Criteria

- [ ] GitHub Actions workflow runs on PR to framework/database paths
- [ ] Baseline comparison detects >15% response time regression
- [ ] PR comments include performance delta summary
- [ ] Nightly benchmarks run at 2 AM UTC
- [ ] Trend report shows historical performance over time
- [ ] Critical regressions fail the CI build
- [ ] Baseline auto-updates on main branch merges
- [ ] Artifacts retained for 30 days

## DO NOT

- Fail builds on warning-level regressions
- Update baseline without successful benchmark completion
- Skip PR comments for performance changes
- Run comprehensive benchmarks on every PR (too slow)
- Ignore variance when comparing results

## Estimated Complexity

**Medium** - Primarily configuration and scripting, but requires careful threshold tuning and CI/CD integration testing.
