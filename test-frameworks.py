#!/usr/bin/env python3
"""Test GraphQL frameworks against FraiseQL benchmark."""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Optional

# Framework endpoints configuration
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
    },
    "express-rest": {
        "url": "http://localhost:8005",
        "graphql_endpoint": "/graphql",
        "headers": {"Content-Type": "application/json"}
    },
    "fastapi-rest": {
        "url": "http://localhost:8003",
        "graphql_endpoint": "/graphql",
        "headers": {"Content-Type": "application/json"}
    },
    "spring-boot": {
        "url": "http://localhost:8010",
        "graphql_endpoint": "/graphql",
        "headers": {"Content-Type": "application/json"}
    }
}

# Test queries
QUERIES = {
    "users_simple": """
        query {
            users(limit: 5) {
                id
                username
            }
        }
    """,
    "users_count": """
        query {
            users(limit: 10) {
                id
            }
        }
    """,
    "single_user": """
        query {
            user(id: 1) {
                id
                username
            }
        }
    """,
    "posts": """
        query {
            posts(limit: 5) {
                id
                title
            }
        }
    """,
    "ping": """
        query {
            ping
        }
    """
}

def test_framework(name: str, config: dict, query: str, query_name: str) -> Optional[dict]:
    """Test a single framework with a query."""
    url = f"{config['url']}{config['graphql_endpoint']}"

    try:
        start_time = time.time()
        response = requests.post(
            url,
            json={"query": query},
            headers=config["headers"],
            timeout=10
        )
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        if response.status_code == 200:
            data = response.json()
            has_errors = "errors" in data
            return {
                "framework": name,
                "query": query_name,
                "status": "✓ OK" if not has_errors else "⚠ ERRORS",
                "time_ms": f"{elapsed:.2f}",
                "response_size": len(response.content),
                "errors": data.get("errors", [])[0]["message"] if has_errors else None
            }
        else:
            return {
                "framework": name,
                "query": query_name,
                "status": f"✗ {response.status_code}",
                "time_ms": f"{elapsed:.2f}",
                "response_size": len(response.content),
                "errors": response.text[:100]
            }
    except Exception as e:
        return {
            "framework": name,
            "query": query_name,
            "status": "✗ FAILED",
            "time_ms": "N/A",
            "response_size": 0,
            "errors": str(e)[:100]
        }

def main():
    print("\n" + "="*80)
    print("🧪 FraiseQL Framework Test Suite")
    print("="*80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # Test each framework
    for framework_name, framework_config in FRAMEWORKS.items():
        print(f"\n📊 Testing {framework_name}...")

        # Test each query
        for query_name, query in QUERIES.items():
            result = test_framework(framework_name, framework_config, query, query_name)
            if result:
                results.append(result)
                status = result["status"]
                time_ms = result["time_ms"]
                print(f"   {status} {query_name}: {time_ms}ms")
                if result["errors"]:
                    print(f"      Error: {result['errors']}")

    # Print summary
    print("\n" + "="*80)
    print("📈 Test Summary")
    print("="*80)

    # Group by framework
    by_framework = {}
    for result in results:
        fw = result["framework"]
        if fw not in by_framework:
            by_framework[fw] = []
        by_framework[fw].append(result)

    # Print results table
    print(f"\n{'Framework':<20} {'Query':<20} {'Status':<12} {'Time (ms)':<12} {'Size':<10}")
    print("-" * 74)

    for framework in sorted(by_framework.keys()):
        for result in by_framework[framework]:
            print(f"{result['framework']:<20} {result['query']:<20} {result['status']:<12} {result['time_ms']:<12} {result['response_size']:<10}")

    # Calculate success rate
    total = len(results)
    successful = sum(1 for r in results if "OK" in r["status"] or "ERRORS" in r["status"])
    success_rate = (successful / total * 100) if total > 0 else 0

    print("\n" + "-" * 74)
    print(f"Success Rate: {successful}/{total} ({success_rate:.1f}%)")
    print(f"Average Response Time: {sum(float(r['time_ms']) for r in results if r['time_ms'] != 'N/A') / len([r for r in results if r['time_ms'] != 'N/A']):.2f}ms")
    print("="*80 + "\n")

    return 0 if success_rate == 100 else 1

if __name__ == "__main__":
    sys.exit(main())
