#!/usr/bin/env python3
"""
Comparative Benchmarking Analysis Script
Runs performance tests across multiple GraphQL frameworks and generates analysis reports.
"""

import os
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not available - RAM monitoring disabled")


class BenchmarkConfig:
    """Configuration for benchmark testing"""

    def __init__(
        self,
        threads: int = 50,
        loops: int = 1000,
        ramp_up: int = 30,
        warmup_duration: int = 120,
        measurement_duration: int = 300,
    ):
        self.threads = threads
        self.loops = loops
        self.ramp_up = ramp_up
        self.warmup_duration = warmup_duration
        self.measurement_duration = measurement_duration


class ComparativeBenchmarkAnalyzer:
    def __init__(
        self,
        results_dir: str = "tests/perf/results",
        enable_tv_tables: bool = True,
        enable_resource_monitoring: bool = True,
        config: Optional[BenchmarkConfig] = None,
    ):
        self.results_dir = results_dir
        self.enable_tv_tables = enable_tv_tables
        self.enable_resource_monitoring = enable_resource_monitoring
        self.config = config or BenchmarkConfig()
        self.frameworks = [
            "fraiseql",
            "strawberry",
            "graphene",
            "fastapi-rest",
            "flask-rest",
        ]
        self.metrics = {}
        self.resource_metrics = []

    def run_warmup(self, framework: str, duration_seconds: int = 120):
        """Run warmup phase for a framework"""
        print(f"🔥 Warming up {framework} for {duration_seconds} seconds...")

        port_map = {
            "fraiseql": 4000,
            "strawberry": 8001,
            "graphene": 8002,
            "fastapi-rest": 8003,
            "flask-rest": 8004,
        }

        port = port_map.get(framework, 4000)

        # Use warmup script
        warmup_script = "tests/perf/scripts/warmup.sh"
        if os.path.exists(warmup_script):
            result = subprocess.run(
                [warmup_script, framework, str(port), str(duration_seconds), "10"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"✅ Warmup completed for {framework}")
                return True
            else:
                print(f"⚠️  Warmup script failed: {result.stderr}")
        else:
            print(f"⚠️  Warmup script not found: {warmup_script}")

        # Fallback: simple curl-based warmup
        print("🔄 Using fallback warmup method...")
        warmup_queries = [
            '{"query": "{ ping }"}',
            '{"query": "{ users(limit: 5) { id username } }"}',
            '{"query": "{ posts(limit: 3) { id title } }"}',
        ]

        for i in range(20):  # 20 warmup requests
            query = warmup_queries[i % len(warmup_queries)]
            try:
                subprocess.run(
                    [
                        "curl",
                        "-s",
                        "-X",
                        "POST",
                        f"http://localhost:{port}/graphql",
                        "-H",
                        "Content-Type: application/json",
                        "-d",
                        query,
                    ],
                    timeout=5,
                    capture_output=True,
                )
            except:
                pass  # Ignore warmup failures

        print(f"✅ Fallback warmup completed for {framework}")
        return True

    def restart_framework(self, framework: str):
        """Restart a framework container for cold start testing"""
        print(f"🔄 Restarting {framework} for cold start...")

        try:
            # Stop the framework
            subprocess.run(
                ["docker-compose", "stop", framework], capture_output=True, timeout=30
            )

            # Start it again
            subprocess.run(
                ["docker-compose", "up", "-d", framework],
                capture_output=True,
                timeout=30,
            )

            # Wait for health check
            self.wait_for_service_ready(framework)

        except Exception as e:
            print(f"⚠️  Error restarting {framework}: {e}")

    def run_cold_warm_comparison(self, framework: str, timestamp: str):
        """Run both cold start and warm benchmarks for comparison"""
        print(f"🧊🔥 Running cold vs warm comparison for {framework}")

        results = {}

        # Cold start test
        print(f"\n🧊 Cold start test for {framework}")
        self.restart_framework(framework)
        time.sleep(5)  # Minimal stabilization

        cold_result = self.run_framework_test(framework, timestamp, phase="cold")
        if cold_result:
            results["cold"] = self.collect_framework_results(cold_result, framework)

        # Warmup phase
        print(f"\n🔥 Warmup phase for {framework}")
        self.run_warmup(framework, duration_seconds=self.config.warmup_duration)

        # Warm test
        print(f"\n🔥 Warm test for {framework}")
        warm_result = self.run_framework_test(framework, timestamp, phase="warm")
        if warm_result:
            results["warm"] = self.collect_framework_results(warm_result, framework)

        # Calculate improvement metrics
        if "cold" in results and "warm" in results:
            cold_avg = results["cold"].get("avg_response_time", 0)
            warm_avg = results["warm"].get("avg_response_time", 0)

            if cold_avg > 0:
                improvement = ((cold_avg - warm_avg) / cold_avg) * 100
                results["warmup_improvement"] = {
                    "percentage": improvement,
                    "cold_avg_ms": cold_avg,
                    "warm_avg_ms": warm_avg,
                    "improvement_ms": cold_avg - warm_avg,
                }
                print(
                    f"   Warmup improvement: {improvement:.1f}% ({cold_avg:.1f}ms → {warm_avg:.1f}ms)"
                )
        return results

    def run_comparative_benchmarks(self):
        """Run JMeter-based comparative benchmarking with cold/warm analysis"""
        print("🚀 Starting JMeter-based Comparative Benchmarking Suite")
        print("=" * 60)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        all_results = {}

        # Test each framework with cold/warm comparison
        for framework in self.frameworks:
            print(f"\n{'=' * 60}")
            print(f"🧪 Testing {framework.upper()}")
            print("=" * 60)

            try:
                # Start services for this framework
                self.start_services_for_framework(framework)

                # Run cold vs warm comparison
                comparison_results = self.run_cold_warm_comparison(framework, timestamp)

                if comparison_results:
                    framework_results = comparison_results

                    # Add resource metrics if enabled
                    if self.enable_resource_monitoring:
                        framework_results["system_metrics"] = self.get_system_metrics()
                        framework_results["postgres_metrics"] = (
                            self.get_postgres_metrics()
                        )

                    all_results[framework] = framework_results
                else:
                    print(f"⚠️  No results obtained for {framework}")

            except Exception as e:
                print(f"❌ Error testing {framework}: {e}")
                all_results[framework] = {"error": str(e)}

            # Stop services
            self.stop_services()

        # Store all results
        self.metrics = all_results

        # Generate comparative analysis
        self.generate_analysis_report()

        print("\n✅ JMeter-based comparative benchmarking completed!")
        print(f"📊 Results available in: {self.results_dir}/comparative_analysis.json")

    def start_services_for_framework(self, framework: str):
        """Start only the services needed for a specific framework"""
        print(f"📦 Starting services for {framework}...")

        # Start PostgreSQL (always needed)
        subprocess.run(["docker-compose", "up", "-d", "postgres"], check=True)

        # Wait for PostgreSQL to be ready
        print("⏳ Waiting for PostgreSQL...")
        time.sleep(15)

        # Setup TV tables for FraiseQL if enabled
        if framework == "fraiseql" and self.enable_tv_tables:
            print("🔧 Setting up FraiseQL TV tables (CQRS pattern)...")
            self.setup_fraiseql_tv_tables()

        # Start the specific framework
        if framework in ["strawberry", "graphene", "fastapi-rest", "flask-rest"]:
            subprocess.run(["docker-compose", "up", "-d", framework], check=True)
            print(f"⏳ Waiting for {framework} to be ready...")
            time.sleep(15)  # Increased wait time
            self.wait_for_service_ready(framework)
        elif framework == "fraiseql":
            subprocess.run(["docker-compose", "up", "-d", "fraiseql"], check=True)
            print("⏳ Waiting for FraiseQL to be ready...")
            time.sleep(15)  # Increased wait time
            self.wait_for_service_ready(framework)

    def setup_fraiseql_tv_tables(self):
        """Setup FraiseQL TV tables for CQRS benchmarking"""
        try:
            # Check if TV tables exist and have data
            result = subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "benchmark",
                    "-d",
                    "fraiseql_benchmark",
                    "-c",
                    "SELECT COUNT(*) FROM benchmark.tv_user;",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and "0" not in result.stdout.strip():
                print("✅ FraiseQL TV tables already populated")
                return

            print("🔄 Populating FraiseQL TV tables with test data...")

            # Sync all existing data to TV tables
            subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "benchmark",
                    "-d",
                    "fraiseql_benchmark",
                    "-c",
                    "SELECT benchmark.fn_sync_tv_user(id) FROM benchmark.tb_user;",
                ],
                check=True,
                timeout=30,
            )

            subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "benchmark",
                    "-d",
                    "fraiseql_benchmark",
                    "-c",
                    "SELECT benchmark.fn_sync_tv_post(id) FROM benchmark.tb_post;",
                ],
                check=True,
                timeout=30,
            )

            subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "benchmark",
                    "-d",
                    "fraiseql_benchmark",
                    "-c",
                    "SELECT benchmark.fn_sync_tv_comment(id) FROM benchmark.tb_comment;",
                ],
                check=True,
                timeout=30,
            )

            print("✅ FraiseQL TV tables populated successfully")

        except Exception as e:
            print(f"⚠️  Failed to setup FraiseQL TV tables: {e}")
            print("   Continuing with standard benchmarking...")

    def wait_for_service_ready(self, framework: str):
        """Wait for a service to be ready by checking health endpoint"""
        port_map = {
            "fraiseql": 4000,
            "strawberry": 8001,
            "graphene": 8002,
            "fastapi-rest": 8003,
            "flask-rest": 8004,
        }

        port = port_map.get(framework, 4000)
        health_url = f"http://localhost:{port}/health"

        # Try up to 30 seconds
        for i in range(30):
            try:
                result = subprocess.run(
                    ["curl", "-s", health_url],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and "healthy" in result.stdout.lower():
                    print(f"✅ {framework} is ready!")
                    return
            except:
                pass
            time.sleep(1)

        print(f"⚠️  {framework} health check timed out, proceeding anyway...")

    def _validate_test_plan_exists(self, test_plan_path: str) -> bool:
        """Validate that test plan exists and is readable"""
        if not os.path.exists(test_plan_path):
            return False

        if not os.access(test_plan_path, os.R_OK):
            print(f"⚠️  Test plan not readable: {test_plan_path}")
            return False

        # Check file size (should be substantial)
        if os.path.getsize(test_plan_path) < 1000:  # Less than 1KB is suspicious
            print(f"⚠️  Test plan suspiciously small: {test_plan_path}")
            return False

        return True

    def _validate_test_plan_compatibility(
        self, test_plan_path: str, framework_type: str
    ) -> bool:
        """Validate that test plan is compatible with framework type"""
        try:
            with open(test_plan_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for framework-type specific indicators
            if framework_type == "graphql":
                # Should contain GraphQL-related elements
                graphql_indicators = ["graphql", "GraphQL", "query {", "mutation {"]
                has_graphql = any(
                    indicator in content for indicator in graphql_indicators
                )
                if not has_graphql:
                    return False

            elif framework_type == "rest":
                # Should contain REST-related elements and not GraphQL
                rest_indicators = [
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "/users",
                    "/posts",
                    "/comments",
                ]
                graphql_indicators = ["query {", "mutation {", "graphql"]

                has_rest = any(indicator in content for indicator in rest_indicators)
                has_graphql = any(
                    indicator in content for indicator in graphql_indicators
                )

                if not has_rest or has_graphql:
                    return False

            return True

        except Exception as e:
            print(f"⚠️  Error validating test plan {test_plan_path}: {e}")
            return False

    def run_framework_test(
        self, framework: str, timestamp: str, phase: str = "measurement"
    ) -> Optional[str]:
        """Run JMeter-based load test for a specific framework"""
        print(f"🧪 Running JMeter test for {framework} ({phase} phase)...")

        # Determine port for the framework
        port_map = {
            "fraiseql": 4000,
            "strawberry": 8001,
            "graphene": 8002,
            "fastapi-rest": 8003,
            "flask-rest": 8004,
        }

        port = port_map.get(framework, 4000)

        # Select appropriate JMeter test plan with framework-specific validation
        test_plan_map = {
            "fraiseql": "tests/perf/jmeter/comparative-test-plan-fraiseql.jmx",
            "strawberry": "tests/perf/jmeter/comparative-test-plan-strawberry.jmx",
            "graphene": "tests/perf/jmeter/comparative-test-plan-graphene.jmx",
            "fastapi-rest": "tests/perf/jmeter/comparative-test-plan-fastapi.jmx",
            "flask-rest": "tests/perf/jmeter/comparative-test-plan-flask.jmx",
        }

        # Determine framework type for fallback logic
        framework_type = (
            "rest" if framework in ["fastapi-rest", "flask-rest"] else "graphql"
        )

        # Try framework-specific plan first
        test_plan = test_plan_map.get(framework)

        # Validate test plan exists and is appropriate for framework type
        if test_plan and os.path.exists(test_plan):
            # Validate test plan compatibility
            if self._validate_test_plan_compatibility(test_plan, framework_type):
                print(f"✅ Using framework-specific test plan: {test_plan}")
            else:
                print(
                    f"⚠️  Test plan {test_plan} not compatible with {framework_type}, using generic"
                )
                test_plan = None
        else:
            test_plan = None

        # Fallback to generic plan based on framework type
        if not test_plan:
            generic_plan = (
                f"tests/perf/jmeter/comparative-test-plan-{framework_type}.jmx"
            )
            if os.path.exists(generic_plan):
                test_plan = generic_plan
                print(f"✅ Using generic {framework_type} test plan: {test_plan}")
            else:
                # Final fallback to basic plan
                basic_plan = "tests/perf/jmeter/comparative-test-plan.jmx"
                if os.path.exists(basic_plan):
                    test_plan = basic_plan
                    print(f"⚠️  Using basic fallback test plan: {test_plan}")
                else:
                    print(
                        f"❌ No suitable test plan found for {framework} ({framework_type})"
                    )
                    return None

        # Final validation
        if not self._validate_test_plan_exists(test_plan):
            print(f"❌ Test plan validation failed: {test_plan}")
            return None

        # Configure test parameters based on phase
        if phase == "warmup":
            threads = 10
            loops = 100  # Shorter warmup
            ramp_up = 10
            duration = None
        else:  # measurement phase
            threads = self.config.threads
            loops = self.config.loops
            ramp_up = self.config.ramp_up
            duration = None

        # Create results directory
        results_dir = f"{self.results_dir}/raw/{framework}_{timestamp}_{phase}"
        os.makedirs(results_dir, exist_ok=True)

        # Convert paths to absolute paths
        abs_test_plan = os.path.abspath(test_plan)
        abs_results_jtl = os.path.abspath(f"{results_dir}/results.jtl")
        abs_results_html = os.path.abspath(f"{results_dir}/html")

        # Get the project root directory for JMeter working directory
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Run JMeter test
        jmeter_cmd = [
            "jmeter",
            "-n",
            "-t",
            abs_test_plan,
            "-l",
            abs_results_jtl,
            "-e",
            "-o",
            abs_results_html,
            f"-Jthreads={threads}",
            f"-Jloops={loops}",
            f"-Jrampup={ramp_up}",
            f"-Jframework_port={port}",
        ]

        if duration:
            jmeter_cmd.extend([f"-Jduration={duration}"])

        # Retry logic for JMeter test execution
        max_retries = 2
        retry_delay = 5

        for attempt in range(max_retries + 1):
            try:
                print(
                    f"🚀 JMeter test attempt {attempt + 1}/{max_retries + 1} for {framework}"
                )

                result = subprocess.run(
                    jmeter_cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minute timeout
                    cwd=project_root,  # Run from project root for relative paths in JMeter
                )

                if result.returncode == 0:
                    break  # Success, exit retry loop
                else:
                    print(
                        f"⚠️  JMeter test attempt {attempt + 1} failed (exit code: {result.returncode})"
                    )
                    if result.stderr:
                        print(f"Error output: {result.stderr[-500:]}")  # Last 500 chars

                    if attempt < max_retries:
                        print(f"⏳ Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"❌ JMeter test failed after {max_retries + 1} attempts")
                        return None

            except subprocess.TimeoutExpired:
                print(f"⏰ JMeter test timed out on attempt {attempt + 1}")
                if attempt < max_retries:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"❌ JMeter test timed out after {max_retries + 1} attempts")
                    return None
            except Exception as e:
                print(f"💥 Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue  # Continue to next attempt
                else:
                    print(
                        f"❌ JMeter test failed with unexpected error after {max_retries + 1} attempts"
                    )
                    return None

        # Verify results file was created and has data (outside retry loop)
        jtl_file = f"{results_dir}/results.jtl"
        if not os.path.exists(jtl_file):
            print(f"❌ JMeter results file not created: {jtl_file}")
            return None

        # Count successful requests
        success_count = 0
        total_count = 0
        try:
            with open(jtl_file, "r") as f:
                for line in f:
                    if line.strip():
                        total_count += 1
                        parts = line.split(",")
                        if len(parts) > 7 and parts[7].lower() == "true":
                            success_count += 1
        except Exception as e:
            print(f"⚠️  Error reading results file: {e}")

        success_rate = success_count / total_count * 100 if total_count > 0 else 0

        print(
            f"✅ {framework} {phase} test completed: {success_count}/{total_count} requests ({success_rate:.1f}% success)"
        )

        return f"{framework}_{timestamp}_{phase}"

    def collect_framework_results(
        self, result_id: str, framework: str
    ) -> Dict[str, Any]:
        """Collect results for a specific framework from JMeter JTL file"""
        print(f"📊 Collecting results for {framework}...")

        jtl_file = f"{self.results_dir}/raw/{result_id}/results.jtl"
        if not os.path.exists(jtl_file):
            print(f"Warning: JTL file {jtl_file} not found")
            return {}

        # Use the statistical analysis script if available
        analysis_script = "tests/perf/scripts/analyze-results.py"
        if os.path.exists(analysis_script):
            try:
                result = subprocess.run(
                    [
                        "python3",
                        analysis_script,
                        jtl_file,
                        "--output",
                        "/tmp/analysis.json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and os.path.exists("/tmp/analysis.json"):
                    with open("/tmp/analysis.json", "r") as f:
                        analysis = json.load(f)
                    return analysis.get("summary", {}).get("response_time_stats", {})
            except Exception as e:
                print(
                    f"⚠️  Statistical analysis failed: {e}, falling back to basic analysis"
                )

        # Fallback: basic JTL parsing
        response_times = []
        success_count = 0
        total_count = 0

        try:
            with open(jtl_file, "r") as f:
                for line in f:
                    if line.strip() and not line.startswith("timeStamp"):
                        parts = line.strip().split(",")
                        if len(parts) >= 8:
                            try:
                                elapsed = int(parts[1])  # Response time
                                success = parts[7].lower() == "true"

                                response_times.append(elapsed)
                                total_count += 1
                                if success:
                                    success_count += 1
                            except (ValueError, IndexError):
                                continue

        except Exception as e:
            print(f"Error parsing JTL file: {e}")
            return {}

        if not response_times:
            return {}

        # Basic statistics
        stats = {
            "avg_response_time": sum(response_times) / len(response_times),
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)]
            if response_times
            else 0,
            "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)]
            if response_times
            else 0,
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "success_rate": success_count / total_count * 100 if total_count > 0 else 0,
            "total_requests": total_count,
            "successful_requests": success_count,
            "throughput_rps": len(response_times)
            / max(1, (max(response_times) / 1000)),  # Rough estimate
        }

        return stats

    def stop_services(self):
        """Stop all running services"""
        print("🛑 Stopping services...")
        subprocess.run(["docker-compose", "down"], check=True)
        time.sleep(5)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Collect system resource metrics (RAM, disk, CPU)"""
        metrics = {}

        if HAS_PSUTIL:
            try:
                # RAM usage
                ram = psutil.virtual_memory()
                metrics["ram_total_gb"] = round(ram.total / (1024**3), 2)
                metrics["ram_used_gb"] = round(ram.used / (1024**3), 2)
                metrics["ram_percent"] = ram.percent

                # Disk usage (for PostgreSQL data)
                disk = psutil.disk_usage("/")
                metrics["disk_total_gb"] = round(disk.total / (1024**3), 2)
                metrics["disk_used_gb"] = round(disk.used / (1024**3), 2)
                metrics["disk_percent"] = disk.percent

                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                metrics["cpu_percent"] = cpu_percent

                # Load average
                load_avg = psutil.getloadavg()
                metrics["load_avg_1m"] = load_avg[0]
                metrics["load_avg_5m"] = load_avg[1]
                metrics["load_avg_15m"] = load_avg[2]

            except Exception as e:
                print(f"Warning: Failed to collect system metrics: {e}")
                metrics["error"] = str(e)
        else:
            metrics["error"] = "psutil not available"

        return metrics

    def get_postgres_metrics(self) -> Dict[str, Any]:
        """Collect PostgreSQL-specific metrics (table sizes, etc.)"""
        metrics = {}

        try:
            # Get database size
            result = subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "benchmark",
                    "-d",
                    "fraiseql_benchmark",
                    "-c",
                    "SELECT pg_size_pretty(pg_database_size(current_database())) as size;",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse the output to extract size
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "MB" in line or "GB" in line:
                        metrics["db_size"] = line.strip()
                        break

            # Get table sizes
            result = subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "benchmark",
                    "-d",
                    "fraiseql_benchmark",
                    "-c",
                    "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                metrics["table_sizes"] = result.stdout.strip()

        except Exception as e:
            print(f"Warning: Failed to collect PostgreSQL metrics: {e}")
            metrics["error"] = str(e)

        return metrics

    def collect_results(self, jtl_file: str):
        """Parse JMeter JTL results and organize by framework (legacy method)"""
        print("📊 Collecting and parsing results...")

        # Read JTL file (simplified parsing)
        results = {}
        try:
            with open(f"{self.results_dir}/raw/{jtl_file}", "r") as f:
                lines = f.readlines()

            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split(",")
                    if len(parts) >= 10:
                        label = parts[0]
                        response_time = int(parts[1])
                        success = parts[7] == "true"

                        # Extract framework from label
                        framework = "unknown"
                        for fw in self.frameworks:
                            if fw in label.lower():
                                framework = fw
                                break

                        if framework not in results:
                            results[framework] = []

                        results[framework].append(
                            {
                                "response_time": response_time,
                                "success": success,
                                "timestamp": parts[2],
                            }
                        )

        except FileNotFoundError:
            print(f"Warning: JTL file {jtl_file} not found")
            return

        self.metrics = results

    def generate_analysis_report(self):
        """Generate comprehensive comparative analysis"""
        print("📈 Generating analysis report...")

        if not self.metrics:
            print("No metrics data available")
            return

        # Flatten metrics: use warm results as primary (or fall back to cold if no warm)
        stats = {}
        for framework, framework_data in self.metrics.items():
            if isinstance(framework_data, dict) and "warm" in framework_data:
                # Extract warm test results
                stats[framework] = framework_data["warm"]
            elif isinstance(framework_data, dict) and "cold" in framework_data:
                # Fall back to cold if no warm
                stats[framework] = framework_data["cold"]
            elif isinstance(framework_data, dict) and "avg_response_time" in framework_data:
                # Already flat structure
                stats[framework] = framework_data
            else:
                print(f"⚠️  Skipping {framework}: unexpected data structure")

        # Generate comparison table
        self.generate_comparison_table(stats)

        # Generate performance insights
        self.generate_performance_insights(stats)

        # Save comprehensive analysis
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "tv_tables_enabled": self.enable_tv_tables,
                "resource_monitoring_enabled": self.enable_resource_monitoring,
                "frameworks_tested": self.frameworks,
            },
            "statistics": stats,
            "raw_metrics": self.metrics,
        }

        with open(f"{self.results_dir}/comparative_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        # Generate resource usage report
        if self.enable_resource_monitoring:
            self.generate_resource_report(stats)

    def generate_comparison_table(self, stats: Dict[str, Any]):
        """Generate comparison table"""
        print("\n" + "=" * 80)
        print("FRAMEWORK COMPARISON RESULTS")
        print("=" * 80)

        print(
            f"{'Framework':<15} {'Avg (ms)':<10} {'P95 (ms)':<10} {'P99 (ms)':<10} {'Success %':<10}"
        )
        print("-" * 80)

        for framework, data in stats.items():
            if isinstance(data, dict) and 'avg_response_time' in data:
                print(
                    f"{framework:<15} {data['avg_response_time']:<10.1f} {data.get('p95_response_time', 0):<10.1f} {data.get('p99_response_time', 0):<10.1f} {data.get('success_rate', 0):<10.1f}"
                )
            else:
                print(f"{framework:<15} {'ERROR':<10} {'—':<10} {'—':<10} {'0.0':<10}")

        print("=" * 80)

        # Performance ratios (FraiseQL as baseline)
        fraiseql_data = stats.get("fraiseql", {})
        if isinstance(fraiseql_data, dict) and 'avg_response_time' in fraiseql_data and fraiseql_data['avg_response_time'] > 0:
            baseline = fraiseql_data["avg_response_time"]
            print("\nPERFORMANCE RATIOS (FraiseQL = 1.0)")
            print("-" * 50)

            for framework, data in stats.items():
                if isinstance(data, dict) and 'avg_response_time' in data and data['avg_response_time'] > 0:
                    ratio = data["avg_response_time"] / baseline
                    status = "🚀 Faster" if ratio < 1 else "🐌 Slower"
                    print(f"{framework:<15} {ratio:<8.2f}x {status}")
                else:
                    print(f"{framework:<15} {'N/A':<8} {'(test failed)'}")

    def generate_performance_insights(self, stats: Dict[str, Any]):
        """Generate performance insights and recommendations"""
        print("\n" + "=" * 80)
        print("PERFORMANCE INSIGHTS & RECOMMENDATIONS")
        print("=" * 80)

        if not stats:
            print("Insufficient data for insights")
            return

        # Find best performers (filter out failed tests)
        valid_stats = {fw: data for fw, data in stats.items()
                      if isinstance(data, dict) and 'avg_response_time' in data and data['avg_response_time'] > 0}

        if not valid_stats:
            print("⚠️  No successful test results available")
            return

        sorted_by_avg = sorted(valid_stats.items(), key=lambda x: x[1]["avg_response_time"])
        fastest = sorted_by_avg[0][0]
        slowest = sorted_by_avg[-1][0]

        print(f"🏆 Fastest Framework: {fastest}")
        print(f"🐌 Slowest Framework: {slowest}")

        # FraiseQL-specific insights
        fraiseql_stats = stats.get("fraiseql")
        if fraiseql_stats and isinstance(fraiseql_stats, dict) and 'avg_response_time' in fraiseql_stats:
            print("\n🔍 FraiseQL Analysis:")
            print(f"Average Response Time: {fraiseql_stats['avg_response_time']:.2f}ms")
            print(f"P95 Response Time: {fraiseql_stats.get('p95_response_time', 0):.2f}ms")
            print(f"Success Rate: {fraiseql_stats.get('success_rate', 0):.1f}%")

            # Compare with others
            for framework, data in stats.items():
                if framework != "fraiseql" and isinstance(data, dict) and 'avg_response_time' in data and data.get('avg_response_time', 0) > 0:
                    speedup = data["avg_response_time"] / fraiseql_stats["avg_response_time"]
                    if speedup > 1:
                        print(f"{framework} is {speedup:.1f}x slower than FraiseQL")
                    else:
                        print(f"{framework} is {1 / speedup:.1f}x faster than FraiseQL")
        # Optimization recommendations
        print("\n💡 Optimization Recommendations:")
        print("• Focus on N+1 query elimination (major impact)")
        print("• Implement query plan caching")
        print("• Optimize database connection pooling")
        print("• Consider Rust-based JSON serialization")
        print("• Evaluate cascade mutation patterns")

    def generate_resource_report(self, stats: Dict[str, Any]):
        """Generate resource usage analysis report"""
        print("\n" + "=" * 80)
        print("RESOURCE USAGE ANALYSIS")
        print("=" * 80)

        # Collect resource metrics from all frameworks
        resource_summary = {}

        for framework, framework_stats in stats.items():
            if "system_metrics" in framework_stats:
                sys_metrics = framework_stats["system_metrics"]
                resource_summary[framework] = {
                    "ram_used_gb": sys_metrics.get("ram_used_gb", 0),
                    "ram_percent": sys_metrics.get("ram_percent", 0),
                    "cpu_percent": sys_metrics.get("cpu_percent", 0),
                    "disk_used_gb": sys_metrics.get("disk_used_gb", 0),
                }

        if resource_summary:
            print("\n🖥️  SYSTEM RESOURCE USAGE BY FRAMEWORK:")
            print(
                f"{'Framework':<15} {'RAM (GB)':<10} {'RAM %':<8} {'CPU %':<8} {'Disk (GB)':<10}"
            )
            print("-" * 80)

            for framework, metrics in resource_summary.items():
                print(
                    f"{framework:<15} {metrics['ram_used_gb']:<10.1f} {metrics['ram_percent']:<8.1f} {metrics['cpu_percent']:<8.1f} {metrics['disk_used_gb']:<10.1f}"
                )

            # Find most/least resource intensive
            if resource_summary:
                by_ram = sorted(
                    resource_summary.items(), key=lambda x: x[1]["ram_used_gb"]
                )
                by_cpu = sorted(
                    resource_summary.items(), key=lambda x: x[1]["cpu_percent"]
                )

                print(
                    f"\n🏆 Most Memory Efficient: {by_ram[0][0]} ({by_ram[0][1]['ram_used_gb']:.1f} GB)"
                )
                print(
                    f"🏆 Highest CPU Usage: {by_cpu[-1][0]} ({by_cpu[-1][1]['cpu_percent']:.1f}%)"
                )
        else:
            print("\n⚠️  No resource metrics collected")

        # PostgreSQL metrics
        print("\n🐘 POSTGRESQL DATABASE METRICS:")
        for framework, framework_stats in stats.items():
            if "postgres_metrics" in framework_stats:
                pg_metrics = framework_stats["postgres_metrics"]
                if "db_size" in pg_metrics:
                    print(f"{framework}: Database size = {pg_metrics['db_size']}")
                if "table_sizes" in pg_metrics and pg_metrics["table_sizes"].strip():
                    print(f"{framework} table sizes:")
                    # Parse and display top tables
                    lines = pg_metrics["table_sizes"].split("\n")
                    for line in lines[:5]:  # Show top 5 tables
                        if line.strip() and not line.startswith(" schemaname "):
                            parts = line.split("|")
                            if len(parts) >= 3:
                                table = parts[1].strip()
                                size = parts[2].strip()
                                print(f"  {table}: {size}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="FraiseQL Comparative Benchmarking Suite"
    )
    parser.add_argument(
        "--no-tv-tables",
        action="store_true",
        help="Disable FraiseQL TV tables (use standard normalized schema)",
    )
    parser.add_argument(
        "--no-resource-monitoring",
        action="store_true",
        help="Disable RAM/disk usage monitoring",
    )
    parser.add_argument(
        "--framework",
        action="append",
        help="Test only specific framework (fraiseql, strawberry, graphene, fastapi-rest, flask-rest)",
    )

    args = parser.parse_args()

    # Configure analyzer
    enable_tv = not args.no_tv_tables
    enable_resources = not args.no_resource_monitoring

    analyzer = ComparativeBenchmarkAnalyzer(
        enable_tv_tables=enable_tv, enable_resource_monitoring=enable_resources
    )

    # Filter to specific frameworks if requested
    if args.framework:
        # Validate all requested frameworks
        invalid_frameworks = [
            fw for fw in args.framework if fw not in analyzer.frameworks
        ]
        if invalid_frameworks:
            print(
                f"Error: Invalid frameworks {invalid_frameworks}. Available: {analyzer.frameworks}"
            )
            return
        analyzer.frameworks = args.framework

    print("🚀 FraiseQL Comparative Benchmarking Suite")
    print(f"   TV Tables: {'✅ Enabled' if enable_tv else '❌ Disabled'}")
    print(
        f"   Resource Monitoring: {'✅ Enabled' if enable_resources else '❌ Disabled'}"
    )
    print(f"   Frameworks: {analyzer.frameworks}")
    print("=" * 60)

    analyzer.run_comparative_benchmarks()


if __name__ == "__main__":
    main()
