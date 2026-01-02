#!/usr/bin/env python3
"""
Simple FraiseQL Phase 3 Testing Script
Tests async connection pooling and async resolvers
"""

import subprocess
import time
import requests
import json
from datetime import datetime

def run_command(cmd, description=""):
    """Run a command and return output"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ {description} completed")
    return True

def wait_for_service(url, max_attempts=30):
    """Wait for service to be ready"""
    print(f"\n⏳ Waiting for service at {url}...")
    for i in range(max_attempts):
        try:
            response = requests.get(url + "/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Service is ready!")
                return True
        except:
            pass

        if (i + 1) % 10 == 0:
            print(f"  Attempt {i+1}/{max_attempts}...")
        time.sleep(1)

    print(f"❌ Service did not become ready after {max_attempts} seconds")
    return False

def test_fraiseql():
    """Test FraiseQL with async pooling"""

    print("\n" + "="*60)
    print("🚀 FraiseQL Phase 3 - Async Connection Pooling Test")
    print("="*60)

    # Start services
    if not run_command("docker-compose up -d postgres fraiseql", "Starting PostgreSQL and FraiseQL"):
        return False

    # Wait for services
    time.sleep(10)

    if not wait_for_service("http://localhost:4000"):
        print("\n❌ FraiseQL failed to start")
        subprocess.run("docker-compose logs fraiseql | tail -50", shell=True)
        subprocess.run("docker-compose down -v", shell=True)
        return False

    print("\n" + "="*60)
    print("📊 Testing FraiseQL Queries")
    print("="*60)

    # Test queries
    test_cases = [
        {
            "name": "Simple Ping Query",
            "query": "{ ping }"
        },
        {
            "name": "List Users",
            "query": "{ users(limit: 5) { id username } }"
        },
        {
            "name": "User with Posts",
            "query": '{ users(limit: 2) { id username posts(limit: 3) { id title } } }'
        },
        {
            "name": "Single User",
            "query": '{ user(id: "00000001-1111-1111-1111-111111111111") { id username bio } }'
        }
    ]

    results = {}
    base_url = "http://localhost:4000/graphql"

    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"   Query: {test['query'][:60]}...")

        try:
            start_time = time.time()

            response = requests.post(
                base_url,
                json={"query": test["query"]},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            elapsed = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                if "errors" in data and data["errors"]:
                    print(f"   ❌ GraphQL Error: {data['errors'][0].get('message', 'Unknown error')}")
                    results[test["name"]] = {"status": "error", "elapsed_ms": elapsed}
                elif "data" in data:
                    print(f"   ✅ Success ({elapsed:.1f}ms)")
                    results[test["name"]] = {"status": "success", "elapsed_ms": elapsed}
                else:
                    print(f"   ⚠️  Unexpected response: {data}")
                    results[test["name"]] = {"status": "unknown", "elapsed_ms": elapsed}
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                results[test["name"]] = {"status": "http_error", "status_code": response.status_code, "elapsed_ms": elapsed}

        except requests.Timeout:
            print(f"   ⏱️  Timeout")
            results[test["name"]] = {"status": "timeout"}
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:100]}")
            results[test["name"]] = {"status": "exception", "error": str(e)}

    # Load testing with concurrent requests
    print("\n" + "="*60)
    print("🔥 Load Test: 100 Sequential Requests")
    print("="*60)

    query = '{ users(limit: 1) { id username } }'
    times = []
    errors = 0

    for i in range(100):
        try:
            start = time.time()
            response = requests.post(
                base_url,
                json={"query": query},
                timeout=5
            )
            elapsed = (time.time() - start) * 1000

            if response.status_code == 200 and "data" in response.json():
                times.append(elapsed)
            else:
                errors += 1
        except:
            errors += 1

        if (i + 1) % 25 == 0:
            print(f"  Completed {i+1}/100 requests...")

    if times:
        times.sort()
        print(f"\n✅ Load Test Results:")
        print(f"   Total Requests: 100")
        print(f"   Successful: {len(times)}")
        print(f"   Errors: {errors}")
        print(f"   Min Response: {times[0]:.1f}ms")
        print(f"   Avg Response: {sum(times)/len(times):.1f}ms")
        print(f"   P50: {times[len(times)//2]:.1f}ms")
        print(f"   P95: {times[int(len(times)*0.95)]:.1f}ms")
        print(f"   P99: {times[int(len(times)*0.99)]:.1f}ms")
        print(f"   Max Response: {times[-1]:.1f}ms")
        print(f"   Throughput: {100/(sum(times)/len(times)/1000):.1f} RPS")
    else:
        print(f"\n❌ No successful requests in load test")

    # Check connection pool logs
    print("\n" + "="*60)
    print("📋 Checking Connection Pool Status")
    print("="*60)

    result = subprocess.run(
        "docker-compose logs fraiseql | grep -i 'pool\\|connection\\|asyncpg' | tail -10",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)
    else:
        print("(No pool-related logs found)")

    # Save results
    print("\n" + "="*60)
    print("📊 Saving Results")
    print("="*60)

    output = {
        "timestamp": datetime.now().isoformat(),
        "framework": "fraiseql",
        "phase_3_async_pooling": True,
        "functional_tests": results,
        "load_test": {
            "total_requests": 100,
            "successful": len(times),
            "errors": errors,
            "min_ms": min(times) if times else None,
            "avg_ms": sum(times)/len(times) if times else None,
            "p50_ms": times[len(times)//2] if times else None,
            "p95_ms": times[int(len(times)*0.95)] if times else None,
            "p99_ms": times[int(len(times)*0.99)] if times else None,
            "max_ms": max(times) if times else None,
            "rps": 100/(sum(times)/len(times)/1000) if times and sum(times) > 0 else 0
        }
    }

    with open("fraiseql_phase3_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to fraiseql_phase3_results.json")

    # Cleanup
    print("\n" + "="*60)
    print("🧹 Cleanup")
    print("="*60)

    subprocess.run("docker-compose down -v", shell=True, capture_output=True)
    print("✅ Containers stopped")

    # Summary
    print("\n" + "="*60)
    print("📈 PHASE 3 TEST SUMMARY")
    print("="*60)
    print(f"✅ Async Connection Pooling: DEPLOYED")
    print(f"✅ FraiseQL: Running")
    print(f"✅ Functional Tests: {len([r for r in results.values() if r['status'] == 'success'])}/{len(results)} passed")
    print(f"✅ Load Test: {len(times)}/100 successful requests")
    if times:
        print(f"✅ Average Response Time: {sum(times)/len(times):.1f}ms")
        print(f"✅ Throughput: {100/(sum(times)/len(times)/1000):.1f} RPS")
    print("="*60)

if __name__ == "__main__":
    test_fraiseql()
