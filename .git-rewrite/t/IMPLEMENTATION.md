# FraiseQL Performance Assessment - Implementation Guide

## Overview

This document provides a step-by-step implementation plan for building the complete FraiseQL performance assessment system. The repository currently contains only documentation; this guide will help build the actual application and testing infrastructure.

## 1. Project Structure Setup

### Create the Directory Structure

```bash
# Create main directories
mkdir -p app/{fraiseql-server,config,scripts}
mkdir -p tests/perf/{jmeter/{datasets,results/{html,raw,baseline}},monitoring,scripts}
mkdir -p ci
```

### Initial File Structure

```
fraiseql-performance-assessment/
├── app/
│   ├── fraiseql-server/
│   │   ├── main.py
│   │   ├── graphql/
│   │   │   ├── schema.py
│   │   │   ├── resolvers.py
│   │   └── config.py
│   ├── config/
│   │   ├── development.yaml
│   │   ├── benchmark.yaml
│   │   └── production.yaml
│   ├── scripts/
│   │   ├── start.sh
│   │   └── healthcheck.sh
│   ├── Dockerfile
│   ├── requirements.txt
│   └── Makefile
├── tests/
│   ├── perf/
│   │   ├── jmeter/
│   │   │   ├── fraiseql-test-plan.jmx
│   │   │   ├── datasets/
│   │   │   │   ├── simple_queries.csv
│   │   │   │   ├── parameterized_queries.csv
│   │   │   │   ├── complex_queries.csv
│   │   │   │   └── mixed_workload.csv
│   │   │   ├── user.properties
│   │   │   └── log4j2.xml
│   │   ├── monitoring/
│   │   │   ├── resource-collector.sh
│   │   │   ├── parse-metrics.py
│   │   │   └── system-monitor.py
│   │   ├── scripts/
│   │   │   ├── run-headless.sh
│   │   │   ├── warmup.sh
│   │   │   ├── compare-results.py
│   │   │   └── generate-report.py
│   │   └── results/
│   │       ├── html/
│   │       ├── raw/
│   │       └── baseline/
│   └── README.md
├── ci/
│   ├── perf-workflow.yaml
│   ├── artifact-upload.yaml
│   └── baseline-thresholds.json
├── Makefile
└── docker-compose.yml
```

## 2. FraiseQL Application Implementation

### 2.1 Core GraphQL Server

Create `app/fraiseql-server/main.py`:

```python
#!/usr/bin/env python3
"""
FraiseQL Performance Assessment Server
A GraphQL server optimized for benchmarking FraiseQL's unique features.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge

# Import GraphQL components
from .graphql.schema import schema
from .graphql.resolvers import get_resolvers
from .config import Config

# Metrics
REQUEST_COUNT = Counter('fraiseql_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('fraiseql_request_duration_seconds', 'Request latency', ['method', 'endpoint'])
GRAPHQL_PARSE_TIME = Histogram('fraiseql_graphql_parse_duration_seconds', 'GraphQL parsing time')
GRAPHQL_VALIDATE_TIME = Histogram('fraiseql_graphql_validate_duration_seconds', 'GraphQL validation time')
GRAPHQL_EXECUTE_TIME = Histogram('fraiseql_graphql_execute_duration_seconds', 'GraphQL execution time')
PLAN_CACHE_HITS = Counter('fraiseql_plan_cache_hits_total', 'Plan cache hits')
PLAN_CACHE_MISSES = Counter('fraiseql_plan_cache_misses_total', 'Plan cache misses')
SQL_QUERY_COUNT = Counter('fraiseql_sql_queries_total', 'SQL queries executed')

class GraphQLRequest(BaseModel):
    query: str
    variables: Optional[Dict[str, Any]] = None
    operationName: Optional[str] = None

class FraiseQLServer:
    def __init__(self, config: Config):
        self.config = config
        self.app = FastAPI(title="FraiseQL Performance Server")
        self.plan_cache = {}  # Simple in-memory cache for demo
        self.registered_operations = {}  # TurboRouter operations

        self.setup_routes()
        self.setup_metrics()

    def setup_routes(self):
        @self.app.post("/graphql")
        async def graphql_endpoint(request: Request, gql_request: GraphQLRequest):
            start_time = time.time()

            try:
                # Parse GraphQL
                parse_start = time.time()
                document = self.parse_graphql(gql_request.query)
                GRAPHQL_PARSE_TIME.observe(time.time() - parse_start)

                # Validate
                validate_start = time.time()
                self.validate_graphql(document)
                GRAPHQL_VALIDATE_TIME.observe(time.time() - validate_start)

                # Check plan cache
                cache_key = self.get_cache_key(gql_request)
                if cache_key in self.plan_cache:
                    PLAN_CACHE_HITS.inc()
                    execution_plan = self.plan_cache[cache_key]
                else:
                    PLAN_CACHE_MISSES.inc()
                    execution_plan = self.create_execution_plan(document)
                    if self.config.enable_plan_cache:
                        self.plan_cache[cache_key] = execution_plan

                # Execute
                execute_start = time.time()
                result = await self.execute_graphql(document, gql_request.variables, execution_plan)
                GRAPHQL_EXECUTE_TIME.observe(time.time() - execute_start)

                REQUEST_LATENCY.labels(method="POST", endpoint="/graphql").observe(time.time() - start_time)
                REQUEST_COUNT.labels(method="POST", endpoint="/graphql").inc()

                return JSONResponse(content=result)

            except Exception as e:
                REQUEST_COUNT.labels(method="POST", endpoint="/graphql").inc()
                return JSONResponse(
                    status_code=400,
                    content={"errors": [{"message": str(e)}]}
                )

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": time.time()}

        @self.app.get("/metrics")
        async def metrics():
            return Response(
                media_type="text/plain",
                content=prometheus_client.generate_latest()
            )

    def setup_metrics(self):
        # Additional setup if needed
        pass

    def parse_graphql(self, query: str):
        """Parse GraphQL query - simplified for demo"""
        # In real FraiseQL, this would use the actual GraphQL parser
        return {"query": query, "parsed": True}

    def validate_graphql(self, document):
        """Validate GraphQL document"""
        # Simplified validation
        pass

    def get_cache_key(self, request: GraphQLRequest) -> str:
        """Generate cache key for query plan"""
        return f"{request.query}:{json.dumps(request.variables or {}, sort_keys=True)}"

    def create_execution_plan(self, document):
        """Create execution plan - simplified"""
        return {"plan": "simplified_plan"}

    async def execute_graphql(self, document, variables, plan):
        """Execute GraphQL query"""
        # Simplified execution - in real FraiseQL this would:
        # 1. Use Rust projection pipeline
        # 2. Execute against database
        # 3. Handle cascade mutations
        # 4. Support Table Views vs Live Views

        SQL_QUERY_COUNT.inc()  # Track SQL queries

        # Simulate different workloads
        if "ping" in document.get("query", ""):
            return {"data": {"ping": "pong"}}
        elif "user" in document.get("query", ""):
            return {"data": {"user": {"id": variables.get("id", 1), "name": "Test User"}}}
        elif "mutation" in document.get("query", ""):
            return {"data": {"updateUser": {"id": 1, "name": "Updated User"}}}
        else:
            return {"data": {"complexQuery": {"result": "complex_result"}}}

def main():
    config = Config.from_env()
    server = FraiseQLServer(config)

    logging.basicConfig(level=config.log_level)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting FraiseQL server on {config.host}:{config.port}")

    uvicorn.run(
        server.app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower()
    )

if __name__ == "__main__":
    main()
```

### 2.2 GraphQL Schema

Create `app/fraiseql-server/graphql/schema.py`:

```python
"""
GraphQL Schema for FraiseQL Performance Testing
Includes workloads for benchmarking different FraiseQL features.
"""

import graphene
from .resolvers import resolve_ping, resolve_user, resolve_complex_query, resolve_mutation

class User(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    email = graphene.String()

class Query(graphene.ObjectType):
    # Simple workload - minimal overhead
    ping = graphene.String(description="Simple ping query for throughput testing")

    # Parameterized workload
    user = graphene.Field(User, id=graphene.ID(required=True),
                         description="Parameterized user query")

    # Complex workload - nested queries, fragments
    complex_query = graphene.Field(
        graphene.List(User),
        limit=graphene.Int(default_value=10),
        description="Complex query with filtering and aggregation"
    )

class UpdateUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        email = graphene.String()

    user = graphene.Field(User)

    async def mutate(self, info, id, name=None, email=None):
        return UpdateUser(user=await resolve_mutation(info, id, name, email))

class CascadeUpdateUser(graphene.Mutation):
    """FraiseQL-specific: Cascade mutation that updates and returns related data"""
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        email = graphene.String()

    user = graphene.Field(User)
    related_posts = graphene.List(lambda: Post)  # Cascade effect

    async def mutate(self, info, id, name=None, email=None):
        # FraiseQL eliminates the need for separate queries after mutation
        result = await resolve_cascade_mutation(info, id, name, email)
        return CascadeUpdateUser(
            user=result["user"],
            related_posts=result["related_posts"]
        )

class Post(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    author = graphene.Field(User)

class Mutation(graphene.ObjectType):
    update_user = UpdateUser.Field()
    cascade_update_user = CascadeUpdateUser.Field()  # FraiseQL-specific

schema = graphene.Schema(query=Query, mutation=Mutation)
```

### 2.3 Configuration

Create `app/fraiseql-server/config.py`:

```python
"""
Configuration for FraiseQL Performance Server
"""

import os
from typing import Optional
import yaml

class Config:
    def __init__(self):
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "4000"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.enable_plan_cache: bool = os.getenv("ENABLE_PLAN_CACHE", "true").lower() == "true"
        self.enable_turborouter: bool = os.getenv("ENABLE_TURBOROUTER", "false").lower() == "true"
        self.max_workers: int = int(os.getenv("MAX_WORKERS", "4"))
        self.query_timeout: float = float(os.getenv("QUERY_TIMEOUT", "30.0"))

    @classmethod
    def from_env(cls) -> "Config":
        return cls()

    @classmethod
    def from_file(cls, path: str) -> "Config":
        if not os.path.exists(path):
            return cls()

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config
```

### 2.4 Dockerfile

Create `app/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for performance monitoring
RUN apt-get update && apt-get install -y \
    procps \
    sysstat \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY fraiseql-server/ ./fraiseql-server/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

CMD ["python", "-m", "fraiseql-server.main"]
```

### 2.5 Requirements

Create `app/requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
graphene==3.3
pydantic==2.5.0
prometheus-client==0.19.0
pyyaml==6.0.1
aiohttp==3.9.1
```

## 3. Performance Testing Suite

### 3.1 JMeter Test Plan Structure

Create `tests/perf/jmeter/fraiseql-test-plan.jmx`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.5">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="FraiseQL Performance Test Plan" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="GRAPHQL_ENDPOINT" elementType="Argument">
            <stringProp name="Argument.name">GRAPHQL_ENDPOINT</stringProp>
            <stringProp name="Argument.value">http://localhost:4000/graphql</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>

      <!-- Simple Query Thread Group -->
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Simple Query Load" enabled="true">
        <stringProp name="TestPlan.comments">Lightweight queries to measure raw throughput</stringProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControllerGui" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">1000</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">50</stringProp>
        <stringProp name="ThreadGroup.ramp_time">30</stringProp>
        <longProp name="ThreadGroup.start_time">1</longProp>
        <longProp name="ThreadGroup.end_time">1</longProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Simple Ping Query" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="Variables for Simple Query" enabled="true">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <boolProp name="HTTPArgument.always_encode">false</boolProp>
                <stringProp name="Argument.value">{"query": "{ ping }"}</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
                <boolProp name="HTTPArgument.use_equals">true</boolProp>
                <stringProp name="Argument.name"></stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
          <stringProp name="HTTPSampler.domain"></stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol"></stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">${GRAPHQL_ENDPOINT}</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
        <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="GraphQL Response Assertion" enabled="true">
          <collectionProp name="Asserion.test_strings">
            <stringProp name="51818">data</stringProp>
          </collectionProp>
          <stringProp name="Assertion.custom_message"></stringProp>
          <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
          <boolProp name="Assertion.assume_success">false</boolProp>
          <intProp name="Assertion.test_type">2</intProp>
        </ResponseAssertion>
        <hashTree/>
      </hashTree>

      <!-- Parameterized Query Thread Group -->
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Parameterized Query Load" enabled="true">
        <stringProp name="TestPlan.comments">CSV-driven parameterized queries</stringProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControllerGui" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">500</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">20</stringProp>
        <stringProp name="ThreadGroup.ramp_time">15</stringProp>
        <longProp name="ThreadGroup.start_time">1</longProp>
        <longProp name="ThreadGroup.end_time">1</longProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet" testname="User IDs" enabled="true">
          <stringProp name="filename">datasets/parameterized_queries.csv</stringProp>
          <stringProp name="fileEncoding"></stringProp>
          <stringProp name="variableNames">user_id</stringProp>
          <boolProp name="ignoreFirstLine">true</boolProp>
          <stringProp name="delimiter">,</stringProp>
          <boolProp name="quotedData">false</boolProp>
          <boolProp name="recycle">true</boolProp>
          <boolProp name="stopThread">false</boolProp>
          <stringProp name="shareMode">shareMode.all</stringProp>
        </CSVDataSet>
        <hashTree/>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Parameterized User Query" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="Variables for Parameterized Query" enabled="true">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <boolProp name="HTTPArgument.always_encode">false</boolProp>
                <stringProp name="Argument.value">{"query": "query GetUser($id: ID!) { user(id: $id) { id name email } }", "variables": {"id": "${user_id}"}}</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
                <boolProp name="HTTPArgument.use_equals">true</boolProp>
                <stringProp name="Argument.name"></stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
          <stringProp name="HTTPSampler.domain"></stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol"></stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">${GRAPHQL_ENDPOINT}</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>

      <!-- Results Configuration -->
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename">results/raw/results.jtl</stringProp>
      </ResultCollector>
      <hashTree/>

      <!-- HTML Report Generator -->
      <ResultCollector guiclass="ReportGenerator" testclass="ResultCollector" testname="HTML Report" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename">results/html/</stringProp>
      </ResultCollector>
      <hashTree/>

    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### 3.2 Dataset Files

Create `tests/perf/jmeter/datasets/simple_queries.csv`:
```
query_type
ping
```

Create `tests/perf/jmeter/datasets/parameterized_queries.csv`:
```
user_id
1
2
3
4
5
6
7
8
9
10
```

Create `tests/perf/jmeter/datasets/complex_queries.csv`:
```
limit,offset
10,0
20,10
50,0
100,50
```

Create `tests/perf/jmeter/datasets/mixed_workload.csv`:
```
query_type,weight
simple,0.4
parameterized,0.3
complex,0.2
mutation,0.1
```

### 3.3 Resource Monitoring

Create `tests/perf/monitoring/resource-collector.sh`:

```bash
#!/bin/bash
# Resource monitoring script for FraiseQL performance tests
# Collects system metrics during JMeter execution

set -e

OUTPUT_DIR="${1:-results/raw/system-metrics}"
DURATION="${2:-300}"  # 5 minutes default
INTERVAL="${3:-1}"    # 1 second intervals

mkdir -p "$OUTPUT_DIR"

echo "Starting resource monitoring for $DURATION seconds..."
echo "Output directory: $OUTPUT_DIR"
echo "Collection interval: $INTERVAL seconds"

# Function to collect metrics
collect_metrics() {
    local timestamp=$(date +%s)

    # CPU usage (all cores)
    echo "$(date +%s%3N),cpu,$(mpstat 1 1 | awk '/Average/ {print 100 - $12}')" >> "$OUTPUT_DIR/cpu.csv"

    # Memory usage
    echo "$(date +%s%3N),memory,$(free | awk 'NR==2{printf "%.2f", $3*100/$2 }')" >> "$OUTPUT_DIR/memory.csv"

    # Load average
    echo "$(date +%s%3N),loadavg,$(uptime | awk -F'load average:' '{ print $2 }' | tr -d ' ')" >> "$OUTPUT_DIR/loadavg.csv"

    # Network I/O (if applicable)
    if command -v sar >/dev/null 2>&1; then
        sar -n DEV 1 1 | grep -v "^$" | tail -1 | awk '{print strftime("%s%3N") "," $2 "," $5 "," $6}' >> "$OUTPUT_DIR/network.csv"
    fi

    # Disk I/O
    iostat -dx 1 1 | awk 'NR>3 {print strftime("%s%3N") "," $1 "," $4 "," $5 "," $6 "," $7}' >> "$OUTPUT_DIR/disk.csv"

    # Context switches
    vmstat 1 1 | awk 'NR==3 {print strftime("%s%3N") ",context_switches," $12}' >> "$OUTPUT_DIR/context_switches.csv"
}

# Initialize CSV headers
echo "timestamp,cpu_usage_percent" > "$OUTPUT_DIR/cpu.csv"
echo "timestamp,memory_usage_percent" > "$OUTPUT_DIR/memory.csv"
echo "timestamp,load_average" > "$OUTPUT_DIR/loadavg.csv"
echo "timestamp,interface,rx_packets,tx_packets" > "$OUTPUT_DIR/network.csv"
echo "timestamp,device,reads_per_sec,writes_per_sec" > "$OUTPUT_DIR/disk.csv"
echo "timestamp,context_switches" > "$OUTPUT_DIR/context_switches.csv"

# Collect metrics for specified duration
end_time=$(( $(date +%s) + DURATION ))

while [ $(date +%s) -lt $end_time ]; do
    collect_metrics
    sleep $INTERVAL
done

echo "Resource monitoring completed."
echo "Results saved to $OUTPUT_DIR/"
```

### 3.4 Automation Scripts

Create `tests/perf/scripts/run-headless.sh`:

```bash
#!/bin/bash
# Run JMeter performance tests in headless mode

set -e

JMETER_HOME="${JMETER_HOME:-/opt/jmeter}"
TEST_PLAN="${1:-jmeter/fraiseql-test-plan.jmx}"
RESULTS_DIR="${2:-results}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Ensure JMeter is available
if ! command -v jmeter >/dev/null 2>&1 && [ ! -f "$JMETER_HOME/bin/jmeter" ]; then
    echo "ERROR: JMeter not found. Please install JMeter or set JMETER_HOME."
    exit 1
fi

JMETER_CMD="${JMETER_HOME}/bin/jmeter"
if ! command -v jmeter >/dev/null 2>&1; then
    JMETER_CMD="$JMETER_HOME/bin/jmeter"
fi

# Create results directory
mkdir -p "$RESULTS_DIR/raw" "$RESULTS_DIR/html"

echo "Starting JMeter performance tests..."
echo "Test Plan: $TEST_PLAN"
echo "Results: $RESULTS_DIR"
echo "Timestamp: $TIMESTAMP"

# Start resource monitoring in background
echo "Starting resource monitoring..."
./monitoring/resource-collector.sh "$RESULTS_DIR/raw/system-metrics" 300 1 &
MONITOR_PID=$!

# Run JMeter test
"$JMETER_CMD" \
    -n \
    -t "$TEST_PLAN" \
    -l "$RESULTS_DIR/raw/results_$TIMESTAMP.jtl" \
    -e \
    -o "$RESULTS_DIR/html/report_$TIMESTAMP" \
    -j "$RESULTS_DIR/raw/jmeter_$TIMESTAMP.log"

# Stop resource monitoring
kill $MONITOR_PID 2>/dev/null || true

echo "Performance tests completed."
echo "Raw results: $RESULTS_DIR/raw/results_$TIMESTAMP.jtl"
echo "HTML report: $RESULTS_DIR/html/report_$TIMESTAMP/index.html"
echo "System metrics: $RESULTS_DIR/raw/system-metrics/"
```

Create `tests/perf/scripts/warmup.sh`:

```bash
#!/bin/bash
# Warmup script for FraiseQL performance testing
# Prepares caches and runtime for warm system benchmarks

set -e

GRAPHQL_ENDPOINT="${GRAPHQL_ENDPOINT:-http://localhost:4000/graphql}"
WARMUP_DURATION="${1:-120}"  # 2 minutes default
CONCURRENT_USERS="${2:-10}"

echo "Starting FraiseQL warmup for $WARMUP_DURATION seconds..."
echo "Endpoint: $GRAPHQL_ENDPOINT"
echo "Concurrent users: $CONCURRENT_USERS"

# Simple ping queries for warmup
PING_QUERY='{"query": "{ ping }"}'

# Parameterized queries for cache warmup
USER_QUERY='{"query": "query GetUser($id: ID!) { user(id: $id) { id name } }", "variables": {"id": "1"}}'

# Complex query for deeper warmup
COMPLEX_QUERY='{"query": "{ complexQuery(limit: 5) { id name } }"}'

warmup_with_query() {
    local query="$1"
    local duration="$2"
    local concurrency="$3"

    echo "Warming up with query for $duration seconds..."

    local end_time=$(( $(date +%s) + duration ))

    for i in $(seq 1 $concurrency); do
        (
            while [ $(date +%s) -lt $end_time ]; do
                curl -s -X POST \
                    -H "Content-Type: application/json" \
                    -d "$query" \
                    "$GRAPHQL_ENDPOINT" >/dev/null
            done
        ) &
    done

    wait
}

# Phase 1: Simple queries (30% of warmup time)
warmup_with_query "$PING_QUERY" $((WARMUP_DURATION * 30 / 100)) $CONCURRENT_USERS

# Phase 2: Parameterized queries (40% of warmup time)
warmup_with_query "$USER_QUERY" $((WARMUP_DURATION * 40 / 100)) $CONCURRENT_USERS

# Phase 3: Complex queries (30% of warmup time)
warmup_with_query "$COMPLEX_QUERY" $((WARMUP_DURATION * 30 / 100)) $CONCURRENT_USERS

echo "Warmup completed. FraiseQL caches should now be hot."
```

## 4. Build System

### 4.1 Root Makefile

Create `Makefile`:

```makefile
.PHONY: help dev build perf perf-cold perf-warm perf-smoke perf-compare clean clean-results

# Default target
help:
	@echo "FraiseQL Performance Assessment"
	@echo ""
	@echo "Development:"
	@echo "  dev          Start FraiseQL server locally"
	@echo "  build        Build FraiseQL Docker container"
	@echo ""
	@echo "Performance Testing:"
	@echo "  perf         Full warm performance suite"
	@echo "  perf-cold    Cold start benchmark"
	@echo "  perf-warm    Warm system benchmark"
	@echo "  perf-smoke   Quick 10-second smoke test"
	@echo "  perf-compare Compare results with baseline"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Remove all build artifacts"
	@echo "  clean-results Remove test results"

# Development
dev: build
	cd app && docker-compose up --build

build:
	cd app && docker build -t fraiseql-app .

# Performance testing
perf: build
	@echo "Running full warm performance suite..."
	./tests/perf/scripts/warmup.sh 120 20
	./tests/perf/scripts/run-headless.sh jmeter/fraiseql-test-plan.jmx tests/perf/results

perf-cold: build
	@echo "Running cold start benchmark..."
	./tests/perf/scripts/run-headless.sh jmeter/fraiseql-test-plan.jmx tests/perf/results

perf-warm: build
	@echo "Running warm system benchmark..."
	./tests/perf/scripts/warmup.sh 120 20
	./tests/perf/scripts/run-headless.sh jmeter/fraiseql-test-plan.jmx tests/perf/results

perf-smoke: build
	@echo "Running smoke test..."
	timeout 10 ./tests/perf/scripts/run-headless.sh jmeter/fraiseql-smoke-test.jmx tests/perf/results

perf-compare:
	@echo "Comparing results with baseline..."
	python3 tests/perf/scripts/compare-results.py

# Maintenance
clean:
	cd app && docker-compose down -v --remove-orphans
	docker rmi fraiseql-app 2>/dev/null || true

clean-results:
	rm -rf tests/perf/results/raw/* tests/perf/results/html/*
```

### 4.2 App Makefile

Create `app/Makefile`:

```makefile
.PHONY: build run test clean

IMAGE_NAME := fraiseql-app
CONTAINER_NAME := fraiseql-server

build:
	docker build -t $(IMAGE_NAME) .

run: build
	docker run --rm -p 4000:4000 --name $(CONTAINER_NAME) $(IMAGE_NAME)

test:
	docker run --rm $(IMAGE_NAME) python -m pytest

logs:
	docker logs $(CONTAINER_NAME)

shell:
	docker run --rm -it $(IMAGE_NAME) /bin/bash

clean:
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
```

## 5. CI/CD Integration

### 5.1 GitHub Actions Workflow

Create `ci/perf-workflow.yaml`:

```yaml
name: Performance Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run nightly performance tests
    - cron: '0 2 * * *'
  workflow_dispatch:
    inputs:
      test_type:
        description: 'Test type to run'
        required: true
        default: 'full'
        type: choice
        options:
          - smoke
          - cold
          - warm
          - full

jobs:
  performance-test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build FraiseQL container
      run: make build

    - name: Start FraiseQL server
      run: |
        docker run -d --name fraiseql -p 4000:4000 fraiseql-app
        timeout 60 bash -c 'until curl -f http://localhost:4000/health; do sleep 1; done'

    - name: Install JMeter
      run: |
        wget https://downloads.apache.org/jmeter/binaries/apache-jmeter-5.6.2.tgz
        tar -xzf apache-jmeter-5.6.2.tgz
        echo "JMETER_HOME=$PWD/apache-jmeter-5.6.2" >> $GITHUB_ENV
        echo "$PWD/apache-jmeter-5.6.2/bin" >> $GITHUB_PATH

    - name: Run performance tests
      run: |
        case "${{ github.event.inputs.test_type || 'full' }}" in
          smoke)
            make perf-smoke
            ;;
          cold)
            make perf-cold
            ;;
          warm)
            make perf-warm
            ;;
          full)
            make perf
            ;;
        esac

    - name: Compare with baseline
      run: make perf-compare

    - name: Upload HTML report
      uses: actions/upload-artifact@v4
      with:
        name: performance-report
        path: tests/perf/results/html/
        retention-days: 30

    - name: Upload raw results
      uses: actions/upload-artifact@v4
      with:
        name: raw-results
        path: tests/perf/results/raw/
        retention-days: 7

    - name: Performance regression check
      run: |
        if [ -f tests/perf/results/regression-report.json ]; then
          if jq -e '.regression_detected == true' tests/perf/results/regression-report.json > /dev/null; then
            echo "🚨 Performance regression detected!"
            exit 1
          else
            echo "✅ No performance regression detected"
          fi
        fi
```

### 5.2 Baseline Thresholds

Create `ci/baseline-thresholds.json`:

```json
{
  "simple_query": {
    "max_p95_ms": 12,
    "max_p99_ms": 20,
    "min_throughput_rps": 8000,
    "max_error_rate_percent": 0.1
  },
  "parameterized_query": {
    "max_p95_ms": 25,
    "max_p99_ms": 45,
    "min_throughput_rps": 4000,
    "max_error_rate_percent": 0.1
  },
  "complex_query": {
    "max_p95_ms": 80,
    "max_p99_ms": 150,
    "min_throughput_rps": 1200,
    "max_error_rate_percent": 0.5
  },
  "mixed_workload": {
    "max_p95_ms": 50,
    "max_p99_ms": 100,
    "min_throughput_rps": 2500,
    "max_error_rate_percent": 0.2
  },
  "system_metrics": {
    "max_cpu_percent": 85,
    "max_memory_percent": 90,
    "max_load_average": 8
  },
  "fraiseql_specific": {
    "max_sql_queries_per_request": 1,
    "min_plan_cache_hit_ratio": 0.8,
    "max_graphql_parse_ms": 5,
    "max_projection_time_ms": 10
  }
}
```

## 6. Docker Compose for Development

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  fraiseql:
    build: ./app
    ports:
      - "4000:4000"
    environment:
      - LOG_LEVEL=DEBUG
      - ENABLE_PLAN_CACHE=true
      - ENABLE_TURBOROUTER=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  # Optional: Add a database for more realistic testing
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: fraiseql_test
      POSTGRES_USER: fraiseql
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fraiseql"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

## 7. Next Steps

This implementation document provides the foundation for a complete FraiseQL performance assessment system. The next steps would be:

1. **Implement the GraphQL resolvers** with actual database integration
2. **Add FraiseQL-specific features** like cascade mutations and Rust projection pipeline
3. **Implement result comparison and regression detection**
4. **Add more comprehensive workload profiles**
5. **Set up monitoring dashboards** (Prometheus/Grafana)
6. **Add distributed load testing** capabilities

The structure provided here gives you a production-ready foundation that can be extended with FraiseQL's unique capabilities.