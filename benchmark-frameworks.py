#!/usr/bin/env python3
"""Benchmark GraphQL frameworks for FraiseQL assessment."""

import requests
import json
import time
import sys
from statistics import mean, median, stdev
from datetime import datetime

# Frameworks to benchmark (only working GraphQL ones)
FRAMEWORKS = {
    "apollo": {
        "url": "http://localhost:4002",
        "graphql_endpoint": "/graphql",
        "headers": {"Content-Type": "application/json", "apollo-require-preflight": "true"}
    },
    "strawberry": {
        "url": "http://localhost:8011",
        "graphql_endpoint": "/graphql",
        "headers": {"Content-Type": "application/json"}
    }
}

# Benchmark queries with varying complexity
QUERIES = {
    "ping": {
        "query": "{ ping }",
        "complexity": "trivial",
        "description": "Basic connectivity test"
    },
    "users_10": {
        "query": """
        {
            users(limit: 10) {
                id
                username
            }
        }
        """,
        "complexity": "simple",
        "description": "Fetch 10 users with 2 fields"
    },
    "users_100": {
        "query": """
        {
            users(limit: 100) {
                id
                username
            }
        }
        """,
        "complexity": "medium",
        "description": "Fetch 100 users with 2 fields"
    }
}

def benchmark_framework(name: str, config: dict, query: str, num_requests: int = 50) -> dict:
    """Benchmark a single GraphQL query on a framework."""
    url = f"{config['url']}{config['graphql_endpoint']}"
    times = []
    errors = 0

    print(f"  Running {num_requests} requests...", end="", flush=True)

    for i in range(num_requests):
        try:
            start = time.time()
            response = requests.post(
                url,
                json={"query": query},
                headers=config["headers"],
                timeout=10
            )
            elapsed = (time.time() - start) * 1000  # Convert to ms

            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    times.append(elapsed)
                else:
                    errors += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1

        if (i + 1) % 10 == 0:
            print(f".", end="", flush=True)

    print(" Done!")

    if not times:
        return {
            "framework": name,
            "requests": num_requests,
            "successful": 0,
            "errors": errors,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "p95": None,
            "p99": None,
            "throughput": 0
        }

    times.sort()
    successful = len(times)
    p95_idx = int(len(times) * 0.95)
    p99_idx = int(len(times) * 0.99)

    return {
        "framework": name,
        "requests": num_requests,
        "successful": successful,
        "errors": errors,
        "min": f"{min(times):.2f}",
        "max": f"{max(times):.2f}",
        "mean": f"{mean(times):.2f}",
        "median": f"{median(times):.2f}",
        "p95": f"{times[p95_idx]:.2f}" if p95_idx < len(times) else "N/A",
        "p99": f"{times[p99_idx]:.2f}" if p99_idx < len(times) else "N/A",
        "throughput": f"{successful / (sum(times) / 1000):.2f}"  # requests per second
    }

def main():
    print("\n" + "="*100)
    print("📊 FraiseQL Framework Performance Benchmark")
    print("="*100)
    print(f"Benchmark started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # Benchmark each query on each framework
    for query_name, query_info in QUERIES.items():
        print(f"\n🔍 Query: {query_name} ({query_info['complexity']})")
        print(f"   Description: {query_info['description']}")
        print(f"   Running benchmark with 50 requests per framework...\n")

        results[query_name] = {}

        for framework_name, framework_config in FRAMEWORKS.items():
            print(f"   Framework: {framework_name}")
            result = benchmark_framework(
                framework_name,
                framework_config,
                query_info["query"],
                num_requests=50
            )
            results[query_name][framework_name] = result

    # Print summary tables
    print("\n" + "="*100)
    print("📈 Benchmark Results Summary")
    print("="*100)

    for query_name in QUERIES:
        print(f"\n{'Query:':<15} {query_name}")
        print(f"{'Complexity:':<15} {QUERIES[query_name]['complexity']}")
        print("-" * 100)
        print(f"{'Framework':<15} {'Requests':<12} {'Success':<10} {'Min (ms)':<12} {'Max (ms)':<12} {'Mean (ms)':<12} {'Median (ms)':<12} {'P95 (ms)':<12} {'Throughput':<15}")
        print("-" * 100)

        for framework_name, result in results[query_name].items():
            print(f"{result['framework']:<15} {result['requests']:<12} {result['successful']:<10} {str(result['min']):<12} {str(result['max']):<12} {str(result['mean']):<12} {str(result['median']):<12} {str(result['p95']):<12} {result['throughput']:<15}")

    print("\n" + "="*100)
    print("✅ Benchmark completed!")
    print("="*100 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
