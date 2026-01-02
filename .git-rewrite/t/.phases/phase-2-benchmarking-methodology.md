# Phase 2: Benchmarking Methodology Improvements

## Objective

Replace the current curl-based sequential testing with proper load testing methodology using JMeter, implementing warmup phases, statistically significant request volumes, and concurrent execution patterns.

## Context

**Current State:**
- `run_comparative_benchmarks.py` uses sequential curl commands (18 requests per framework)
- JMeter test plans exist but are not integrated into the benchmark runner
- No warmup phase before measurements
- No cold vs warm comparison
- Results are statistically insignificant

**Target State:**
- JMeter-driven concurrent load testing with configurable thread counts
- Proper warmup phases (2-3 minutes) before measurement
- Minimum 1000+ requests per scenario for statistical validity
- Cold start vs warm system comparison reports
- Percentile distributions (p50, p95, p99, p99.9) with confidence intervals

## Files to Modify

| File | Action | Purpose |
|------|--------|---------|
| `run_comparative_benchmarks.py` | Major refactor | Integrate JMeter execution |
| `tests/perf/jmeter/comparative-test-plan.jmx` | Enhance | Add warmup thread groups |
| `tests/perf/scripts/run-headless.sh` | Create | JMeter CLI execution wrapper |
| `tests/perf/scripts/warmup.sh` | Create | Framework warmup script |
| `tests/perf/scripts/analyze-results.py` | Create | Statistical analysis with confidence intervals |

## Implementation Steps

### Step 1: Create JMeter CLI Execution Wrapper

```bash
# tests/perf/scripts/run-headless.sh
#!/bin/bash
JMETER_HOME="${JMETER_HOME:-/opt/jmeter}"
TEST_PLAN="$1"
RESULTS_DIR="$2"
THREADS="${3:-100}"
LOOPS="${4:-1000}"
RAMP_UP="${5:-30}"

$JMETER_HOME/bin/jmeter -n \
  -t "$TEST_PLAN" \
  -l "$RESULTS_DIR/results.jtl" \
  -e -o "$RESULTS_DIR/html" \
  -Jthreads="$THREADS" \
  -Jloops="$LOOPS" \
  -Jrampup="$RAMP_UP" \
  -Jresults.dir="$RESULTS_DIR"
```

### Step 2: Implement Warmup Phase

Add to each JMeter test plan:
- SetupThreadGroup with 10 threads, 100 iterations
- 2-minute steady-state warmup before measurement
- Discard warmup results from final statistics

```xml
<!-- Warmup Thread Group Template -->
<SetupThreadGroup>
  <stringProp name="ThreadGroup.num_threads">10</stringProp>
  <stringProp name="LoopController.loops">100</stringProp>
  <stringProp name="ThreadGroup.ramp_time">10</stringProp>
</SetupThreadGroup>
```

### Step 3: Refactor Benchmark Runner

Replace curl-based testing in `run_comparative_benchmarks.py`:

```python
def run_framework_test(self, framework: str, timestamp: str) -> Optional[str]:
    """Run JMeter test for a specific framework"""

    # Select framework-specific test plan
    test_plan = f"tests/perf/jmeter/comparative-test-plan-{framework}.jmx"
    results_dir = f"{self.results_dir}/raw/{framework}_{timestamp}"

    # Configure test parameters
    jmeter_cmd = [
        "jmeter", "-n",
        "-t", test_plan,
        "-l", f"{results_dir}/results.jtl",
        "-e", "-o", f"{results_dir}/html",
        f"-Jthreads={self.config.threads}",
        f"-Jloops={self.config.loops}",
        f"-Jrampup={self.config.ramp_up}",
        f"-Jframework.port={self.port_map[framework]}"
    ]

    subprocess.run(jmeter_cmd, check=True, timeout=600)
    return f"{framework}_{timestamp}"
```

### Step 4: Implement Cold vs Warm Comparison

```python
def run_cold_warm_comparison(self, framework: str):
    """Run both cold start and warm benchmarks"""

    # Cold start test
    self.restart_framework(framework)
    time.sleep(5)  # Minimal stabilization
    cold_results = self.run_benchmark(framework, phase="cold")

    # Warmup phase
    self.run_warmup(framework, duration_seconds=120)

    # Warm test
    warm_results = self.run_benchmark(framework, phase="warm")

    return {
        "cold": cold_results,
        "warm": warm_results,
        "warmup_improvement": self.calculate_improvement(cold_results, warm_results)
    }
```

### Step 5: Statistical Analysis Enhancement

```python
# tests/perf/scripts/analyze-results.py
import numpy as np
from scipy import stats

def calculate_statistics(response_times: List[float]) -> Dict[str, float]:
    """Calculate comprehensive statistics with confidence intervals"""
    data = np.array(response_times)

    return {
        "count": len(data),
        "mean": np.mean(data),
        "std": np.std(data),
        "p50": np.percentile(data, 50),
        "p75": np.percentile(data, 75),
        "p90": np.percentile(data, 90),
        "p95": np.percentile(data, 95),
        "p99": np.percentile(data, 99),
        "p999": np.percentile(data, 99.9),
        "min": np.min(data),
        "max": np.max(data),
        "ci_95": stats.t.interval(0.95, len(data)-1, loc=np.mean(data), scale=stats.sem(data))
    }
```

## Verification Commands

```bash
# Verify JMeter is available
jmeter -v

# Run single framework test
python run_comparative_benchmarks.py --framework fraiseql --threads 100 --loops 1000

# Verify results contain sufficient data points
wc -l tests/perf/results/raw/fraiseql_*/results.jtl
# Expected: > 100,000 lines (header + 100 threads * 1000 loops)

# Verify percentile calculations
python -c "
import json
with open('tests/perf/results/comparative_analysis.json') as f:
    data = json.load(f)
    for fw, stats in data['statistics'].items():
        assert stats['total_requests'] >= 1000, f'{fw}: insufficient requests'
        assert 'p999' in stats, f'{fw}: missing p99.9'
"
```

## Acceptance Criteria

- [ ] JMeter executes with 100+ concurrent threads
- [ ] Each scenario runs 1000+ requests minimum
- [ ] Warmup phase (2 min) precedes measurement phase
- [ ] Cold vs warm results captured separately
- [ ] Statistical output includes p50, p95, p99, p99.9
- [ ] 95% confidence intervals calculated for mean response time
- [ ] Results are reproducible (variance < 10% between runs)

## DO NOT

- Use curl for load testing (only for health checks)
- Run fewer than 1000 requests per scenario
- Skip warmup phase
- Report results without confidence intervals
- Mix cold and warm results in same dataset

## Dependencies

- JMeter 5.6+ installed (or run via Docker)
- scipy for statistical analysis
- numpy for percentile calculations

## Estimated Complexity

**High** - Requires significant refactoring of benchmark runner and proper JMeter integration.
