#!/usr/bin/env python3
"""
REST vs GraphQL Comparative Analysis Script
Analyzes performance differences between REST and GraphQL approaches.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns


class RESTGraphQLComparativeAnalyzer:
    def __init__(self, results_dir: str = "tests/perf/results"):
        self.results_dir = results_dir
        self.frameworks = {
            # GraphQL Frameworks
            "fraiseql": {
                "type": "graphql",
                "language": "python",
                "category": "optimized",
            },
            "strawberry": {
                "type": "graphql",
                "language": "python",
                "category": "modern",
            },
            "graphene": {
                "type": "graphql",
                "language": "python",
                "category": "established",
            },
            # REST Frameworks
            "fastapi-rest": {
                "type": "rest",
                "language": "python",
                "category": "aggregated",
            },
            "flask-rest": {
                "type": "rest",
                "language": "python",
                "category": "traditional",
            },
        }

    def run_comparative_analysis(self):
        """Run comprehensive REST vs GraphQL analysis"""
        print("🔍 Starting REST vs GraphQL Comparative Analysis")
        print("=" * 60)

        # Analyze both protocols
        protocols = ["graphql", "rest"]
        all_results = {}

        for protocol in protocols:
            print(f"\n📊 Analyzing {protocol.upper()} protocol...")
            results = self.analyze_protocol(protocol)
            all_results[protocol] = results

        # Generate comparative insights
        self.generate_protocol_comparison(all_results)

        # Generate performance landscape
        self.generate_performance_landscape(all_results)

        # Generate insights
        insights = self.generate_insights(all_results)

        # Save comprehensive analysis
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "protocols": all_results,
            "insights": self.generate_insights(all_results),
        }

        with open(f"{self.results_dir}/rest_graphql_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        print("\n✅ Comparative analysis completed!")
        print(f"📈 Results saved to: {self.results_dir}/rest_graphql_analysis.json")

    def analyze_protocol(self, protocol: str) -> Dict[str, Any]:
        """Analyze performance for a specific protocol"""
        results_file = f"rest_graphql_comparison_{protocol}.jtl"
        results_path = f"{self.results_dir}/raw/{results_file}"

        if not os.path.exists(results_path):
            print(f"Warning: Results file {results_file} not found")
            return {}

        # Parse JMeter results (simplified)
        framework_stats = {}

        try:
            with open(results_path, "r") as f:
                lines = f.readlines()

            current_data = {}
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split(",")
                    if len(parts) >= 10:
                        label = parts[0]
                        response_time = int(parts[1])
                        success = parts[7] == "true"

                        # Extract framework from label
                        framework = "unknown"
                        for fw in self.frameworks.keys():
                            if fw in label.lower():
                                framework = fw
                                break

                        if framework not in current_data:
                            current_data[framework] = []

                        if success:
                            current_data[framework].append(response_time)

            # Calculate statistics
            for framework, times in current_data.items():
                if times:
                    framework_stats[framework] = {
                        "avg_response_time": sum(times) / len(times),
                        "p95_response_time": sorted(times)[int(len(times) * 0.95)],
                        "p99_response_time": sorted(times)[int(len(times) * 0.99)],
                        "min_response_time": min(times),
                        "max_response_time": max(times),
                        "total_requests": len(current_data.get(framework, [])),
                        "successful_requests": len(times),
                        "success_rate": len(times)
                        / len(current_data.get(framework, []))
                        * 100,
                    }

        except FileNotFoundError:
            pass

        return framework_stats

    def generate_protocol_comparison(self, all_results: Dict[str, Any]):
        """Generate detailed protocol comparison"""
        print("\n" + "=" * 80)
        print("REST VS GRAPHQL PROTOCOL COMPARISON")
        print("=" * 80)

        graphql_results = all_results.get("graphql", {})
        rest_results = all_results.get("rest", {})

        # Compare simple operations
        print("\n🔹 SIMPLE OPERATIONS (Ping/Low Overhead)")
        self.compare_operation_type(graphql_results, rest_results, "Simple")

        # Compare complex operations
        print("\n🔹 COMPLEX OPERATIONS (With Relationships)")
        self.compare_operation_type(graphql_results, rest_results, "Complex")

        # Protocol efficiency analysis
        print("\n📈 PROTOCOL EFFICIENCY ANALYSIS")
        self.analyze_protocol_efficiency(graphql_results, rest_results)

    def compare_operation_type(self, graphql: Dict, rest: Dict, operation_type: str):
        """Compare performance for a specific operation type"""
        print(f"\n{operation_type} Operations Performance:")

        # Get GraphQL frameworks
        graphql_fws = {
            k: v
            for k, v in graphql.items()
            if k in self.frameworks and self.frameworks[k]["type"] == "graphql"
        }
        rest_fws = {
            k: v
            for k, v in rest.items()
            if k in self.frameworks and self.frameworks[k]["type"] == "rest"
        }

        if graphql_fws and rest_fws:
            # Find best performers
            best_graphql = min(
                graphql_fws.items(), key=lambda x: x[1]["avg_response_time"]
            )
            best_rest = min(rest_fws.items(), key=lambda x: x[1]["avg_response_time"])

            print(
                f"Best GraphQL: {best_graphql[0]} ({best_graphql[1]['avg_response_time']:.1f}ms)"
            )
            print(
                f"Best REST: {best_rest[0]} ({best_rest[1]['avg_response_time']:.1f}ms)"
            )

            # Calculate efficiency ratio
            if best_rest[1]["avg_response_time"] > 0:
                efficiency_ratio = (
                    best_graphql[1]["avg_response_time"]
                    / best_rest[1]["avg_response_time"]
                )
                if efficiency_ratio < 1:
                    print(f"GraphQL is {1 / efficiency_ratio:.2f}x faster than REST")
                else:
                    print(f"REST is {efficiency_ratio:.2f}x faster than GraphQL")
        else:
            print("Insufficient data for comparison")

    def analyze_protocol_efficiency(self, graphql: Dict, rest: Dict):
        """Analyze overall protocol efficiency"""
        print("\n🎯 Key Efficiency Insights:")

        # Calculate averages by protocol
        graphql_times = [
            v["avg_response_time"] for v in graphql.values() if "avg_response_time" in v
        ]
        rest_times = [
            v["avg_response_time"] for v in rest.values() if "avg_response_time" in v
        ]

        if graphql_times and rest_times:
            avg_graphql = sum(graphql_times) / len(graphql_times)
            avg_rest = sum(rest_times) / len(rest_times)

            print(".1f")
            print(".1f")

            if avg_rest > 0:
                ratio = avg_graphql / avg_rest
                if ratio < 1:
                    print(f"GraphQL is {1 / ratio:.2f}x faster than REST on average")
                else:
                    print(f"REST is {ratio:.2f}x faster than GraphQL on average")
        # N+1 Query Analysis
        flask_rest = rest.get("flask-rest", {})
        fastapi_rest = rest.get("fastapi-rest", {})
        fraiseql = graphql.get("fraiseql", {})

        if flask_rest and fraiseql:
            flask_time = flask_rest.get("avg_response_time", 0)
            fraiseql_time = fraiseql.get("avg_response_time", 0)

            if flask_time > 0 and fraiseql_time > 0:
                n_plus_1_impact = flask_time / fraiseql_time
                print(
                    f"N+1 Query Impact: Flask REST is {n_plus_1_impact:.1f}x slower than FraiseQL"
                )
        # Over-fetching analysis
        if fastapi_rest and fraiseql:
            fastapi_time = fastapi_rest.get("avg_response_time", 0)
            fraiseql_time = fraiseql.get("avg_response_time", 0)

            if fastapi_time > 0 and fraiseql_time > 0:
                overfetch_impact = fastapi_time / fraiseql_time
                print(
                    f"Over-fetching Impact: FastAPI REST is {overfetch_impact:.1f}x slower than FraiseQL"
                )

    def generate_performance_landscape(self, all_results: Dict[str, Any]):
        """Generate comprehensive performance landscape"""
        print("\n" + "=" * 80)
        print("PERFORMANCE LANDSCAPE ANALYSIS")
        print("=" * 80)

        # Create performance ranking
        all_frameworks = []
        for protocol, results in all_results.items():
            for framework, stats in results.items():
                if "avg_response_time" in stats:
                    all_frameworks.append(
                        {
                            "framework": framework,
                            "protocol": protocol,
                            "response_time": stats["avg_response_time"],
                            "p95_time": stats.get("p95_response_time", 0),
                            "success_rate": stats.get("success_rate", 0),
                            "language": self.frameworks.get(framework, {}).get(
                                "language", "unknown"
                            ),
                            "category": self.frameworks.get(framework, {}).get(
                                "category", "unknown"
                            ),
                        }
                    )

        # Sort by performance
        sorted_frameworks = sorted(all_frameworks, key=lambda x: x["response_time"])

        print("\n🏆 OVERALL PERFORMANCE RANKING")
        print("<20")
        print("-" * 80)

        for i, fw in enumerate(sorted_frameworks, 1):
            print("<20")

        # Language comparison
        print("\n🐍 LANGUAGE PERFORMANCE COMPARISON")
        python_fws = [f for f in all_frameworks if f["language"] == "python"]
        if python_fws:
            python_avg = sum(f["response_time"] for f in python_fws) / len(python_fws)
            print(".1f")

        # Protocol comparison
        print("\n📡 PROTOCOL PERFORMANCE COMPARISON")
        graphql_fws = [f for f in all_frameworks if f["protocol"] == "graphql"]
        rest_fws = [f for f in all_frameworks if f["protocol"] == "rest"]

        if graphql_fws and rest_fws:
            graphql_avg = sum(f["response_time"] for f in graphql_fws) / len(
                graphql_fws
            )
            rest_avg = sum(f["response_time"] for f in rest_fws) / len(rest_fws)

            print(".1f")
            print(".1f")

            if rest_avg > 0:
                protocol_ratio = graphql_avg / rest_avg
                if protocol_ratio < 1:
                    print(
                        f"GraphQL is {1 / protocol_ratio:.2f}x faster than REST overall"
                    )
                else:
                    print(f"REST is {protocol_ratio:.2f}x faster than GraphQL overall")

    def generate_insights(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate key insights from the analysis"""
        insights = {
            "protocol_efficiency": {},
            "framework_performance": {},
            "optimization_opportunities": [],
            "fraiseql_positioning": {},
        }

        # Protocol efficiency insights
        graphql_results = all_results.get("graphql", {})
        rest_results = all_results.get("rest", {})

        if graphql_results and rest_results:
            # Calculate efficiency gains
            fraiseql = graphql_results.get("fraiseql", {})
            flask_rest = rest_results.get("flask-rest", {})
            fastapi_rest = rest_results.get("fastapi-rest", {})

            if fraiseql and flask_rest:
                n_plus_1_gain = flask_rest.get("avg_response_time", 0) / fraiseql.get(
                    "avg_response_time", 1
                )
                insights["protocol_efficiency"]["n_plus_1_elimination"] = (
                    f"{n_plus_1_gain:.1f}x faster"
                )

            if fraiseql and fastapi_rest:
                overfetch_gain = fastapi_rest.get(
                    "avg_response_time", 0
                ) / fraiseql.get("avg_response_time", 1)
                insights["protocol_efficiency"]["exact_fetching"] = (
                    f"{overfetch_gain:.1f}x faster"
                )

        # FraiseQL positioning
        all_times = []
        for protocol_results in all_results.values():
            for fw_stats in protocol_results.values():
                if "avg_response_time" in fw_stats:
                    all_times.append((fw_stats["avg_response_time"], fw_stats))

        if all_times:
            sorted_times = sorted(all_times, key=lambda x: x[0])
            fraiseql_time = None
            for time_val, stats in sorted_times:
                if "fraiseql" in str(stats):
                    fraiseql_time = time_val
                    break

            if fraiseql_time:
                faster_count = sum(1 for t, _ in sorted_times if t > fraiseql_time)
                insights["fraiseql_positioning"]["rank"] = (
                    f"{faster_count + 1} out of {len(sorted_times)} frameworks"
                )

        return insights


def main():
    analyzer = RESTGraphQLComparativeAnalyzer()
    analyzer.run_comparative_analysis()


if __name__ == "__main__":
    main()
