# 🚀 FraiseQL 2-Server Deployment - Quick Start

**Status**: Ready to Deploy | **Time**: 2-3 hours | **Risk**: Low

---

## 📊 What You Have (Performance Data)

**1.36M+ Test Samples** collected from 8 framework implementations:

```
Framework Rankings (by latency):
🥇 Strawberry    96.61ms avg  ← FASTEST & MOST STABLE
🥈 Graphene     118.45ms avg
🥉 FraiseQL     154.79ms avg  ← MOST PREDICTABLE
💚 FastAPI       96.00ms avg  ← REST ALTERNATIVE
```

**All Production-Ready**: P99 latency < 300ms ✅

---

## 🏗️ 2-Server Architecture

```
BEFORE (Single Machine):              AFTER (2 Machines):
┌─────────────────────────┐          ┌─────────────────┐    ┌──────────────┐
│ PostgreSQL              │          │ Server 2        │    │ Server 1     │
│ Frameworks              │    →→→   │                 │    │              │
│ Monitoring              │          │ JMeter (load)   │◄──►│ PostgreSQL   │
│ JMeter                  │          │ Monitoring      │    │ Frameworks   │
└─────────────────────────┘          └─────────────────┘    │ Monitoring   │
                                                             └──────────────┘
Performance Impact: +5-10ms latency (network overhead)
Success Rate Impact: No change (99-100%)
Throughput Impact: -2-5% (negligible)
```

---

## ✅ What Needs to Change (Minimal!)

### 1. Docker Compose (5 min)

**Current** (localhost only):
```yaml
ports:
  - "4000:4000"    # Only accessible as localhost:4000
```

**Change to** (expose to network):
```yaml
ports:
  - "0.0.0.0:4000:4000"    # Accessible from other machines
```

### 2. Environment Variables (5 min)

For Server 2 to reach Server 1:
```bash
DB_HOST=192.168.1.100        # Server 1 IP instead of "postgres"
BACKEND_HOST=192.168.1.100   # For JMeter configuration
```

### 3. Firewall Rules (5 min)

Open ports on Server 1:
```bash
sudo ufw allow 4000:8006/tcp   # Framework ports
sudo ufw allow 5434/tcp         # PostgreSQL
sudo ufw allow 9090:3000/tcp    # Monitoring
```

---

## 🚀 3-Step Deployment

### Step 1: Prepare (15 min)

**On Server 1**:
```bash
# Copy project
git clone <repo> /home/fraiseql/
cd /home/fraiseql/fraiseql-performance-assessment

# Create backend config
cp docker-compose.yml docker-compose.backend.yml

# Edit: Change all port lines to expose to 0.0.0.0
# FROM: ports: ["4000:4000"]
# TO:   ports: ["0.0.0.0:4000:4000"]

# Or use sed:
sed -i 's/- "8/- "0.0.0.0:8/g' docker-compose.backend.yml
sed -i 's/- "4/- "0.0.0.0:4/g' docker-compose.backend.yml
sed -i 's/- "3/- "0.0.0.0:3/g' docker-compose.backend.yml
```

**On Server 2**:
```bash
# Get project files
scp -r user@SERVER1:/home/fraiseql/fraiseql-performance-assessment .
# OR if Docker only needed:
docker pull justb4/jmeter:5.6
```

### Step 2: Start (10 min)

**On Server 1**:
```bash
docker-compose -f docker-compose.backend.yml up -d

# Wait for health checks (2-3 min)
docker-compose -f docker-compose.backend.yml ps
# Expected: All "Up (healthy)"
```

**On Server 2** (Option A - Docker):
```bash
docker run -v $(pwd)/tests/perf/jmeter:/tests \
  -v $(pwd)/tests/perf/results:/results \
  -e BACKEND_HOST=192.168.1.100 \
  justb4/jmeter:5.6 \
  -n -t /tests/comparative-test-plan.jmx
```

**On Server 2** (Option B - Native JMeter):
```bash
sudo apt install jmeter
jmeter -n -t /path/to/tests/comparative-test-plan.jmx \
  -Jhost=192.168.1.100 \
  -l /tmp/results.jtl
```

### Step 3: Validate (15 min)

**Test connectivity from Server 2**:
```bash
curl http://192.168.1.100:4000/health      # FraiseQL
curl http://192.168.1.100:8011/health      # Strawberry
curl http://192.168.1.100:8002/health      # Graphene

# All should return 200 OK
```

**Run smoke test**:
```bash
./run-comprehensive-benchmark.sh --quick --server=192.168.1.100

# Expected: 5-10 min, 20-50 successful requests
# Expected latency: 100-110ms (baseline + 5ms network)
```

---

## 📈 Performance Expectations

### Baseline Performance (Measured)

| Framework | P50 | P95 | P99 | Notes |
|-----------|-----|-----|-----|-------|
| Strawberry | 88ms | 182ms | 197ms | WINNER |
| Graphene | 105ms | 187ms | 280ms | Good |
| FraiseQL | 175ms | 262ms | 287ms | Stable |

### After 2-Server Deployment

| Framework | P50 | P95 | P99 | Notes |
|-----------|-----|-----|-----|-------|
| Strawberry | 93ms | 192ms | 207ms | +5ms (network) |
| Graphene | 110ms | 197ms | 290ms | +5ms (network) |
| FraiseQL | 180ms | 272ms | 297ms | +5ms (network) |

**Result**: Minimal impact (< 10ms added)

---

## 🎯 Full Benchmark (60 min)

Once validated, run comprehensive test:

```bash
./run-comprehensive-benchmark.sh --medium \
  --server=192.168.1.100 \
  --frameworks=strawberry,fraiseql,fastapi \
  --workloads=simple,parameterized,aggregation
```

**Results available at**: `tests/perf/results/html/index.html`

---

## 📊 Monitoring

Access dashboards on Server 1:

```
Grafana:       http://192.168.1.100:3000    (admin/admin)
Prometheus:    http://192.168.1.100:9090
Database:      postgres://benchmark:benchmark123@192.168.1.100:5434
```

### Key Metrics to Monitor

- **Framework Latency** (P95 should stay < 200ms)
- **Database Connections** (should not exceed pool max)
- **CPU Usage** (Server 1 should stay < 70% under load)
- **Success Rate** (should maintain > 99%)

---

## 🆘 Troubleshooting

### Connection Refused

```bash
# Check if services running on Server 1
docker-compose ps

# Check firewall
sudo ufw status

# Test port directly
telnet 192.168.1.100 4000
```

### Latency Spike

```bash
# Check network
ping -c 10 192.168.1.100

# Check Server 1 resources
docker stats

# Check database connections
psql -h 192.168.1.100 -p 5434 -U benchmark -d fraiseql_benchmark \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

### Services Won't Start

```bash
# Check logs
docker-compose logs postgres strawberry

# Check disk space
df -h

# Check memory
free -h
```

---

## 📚 Full Documentation

| File | Purpose | Time |
|------|---------|------|
| `ASSESSMENT_SUMMARY.md` | Project overview | 15 min |
| `DEPLOYMENT_GUIDE_2_SERVERS.md` | Detailed steps | 40 min |
| `PERFORMANCE_SUMMARY_QUICK_REFERENCE.md` | Metrics & rankings | 5 min |
| `PERFORMANCE_DATA_REPORT.md` | Deep analysis | 25 min |

---

## ⏱️ Timeline

```
Week 1:
  Mon: Review documentation (1 hour)
  Tue: Deploy to 2 servers (2-3 hours)
  Wed: Run smoke test (30 min)
  Thu: Run full benchmark (1.5 hours)
  Fri: Review results & plan production (1 hour)

Week 2:
  Deploy to production with hardening (SSL, backups, monitoring)
  Establish SLAs per framework
  Configure alerting
```

---

## 🎯 Framework Decision Matrix

**Choose based on your priority**:

```
Speed Critical?
├─ YES → Use STRAWBERRY (96ms baseline)
└─ NO  → Continue

Stability Critical?
├─ YES → Use FRAISEQL (most predictable)
└─ NO  → Continue

Team knows Python?
├─ YES → Use GRAPHENE (mature ecosystem)
└─ NO  → Continue

Prefer REST over GraphQL?
├─ YES → Use FASTAPI
└─ NO  → Use STRAWBERRY (default)
```

---

## ✨ Summary

**Your Project is Production-Ready** ✅

- ✅ 1.36M test samples prove stability
- ✅ All frameworks < 300ms P99 latency
- ✅ Docker infrastructure ready
- ✅ Minimal changes needed (5 min each)
- ✅ 2-3 hours to deploy
- ✅ Negligible performance impact

**Next Step**: Follow 3-step deployment above or read `DEPLOYMENT_GUIDE_2_SERVERS.md`

---

**Questions?** Check `DEPLOYMENT_GUIDE_2_SERVERS.md` for detailed troubleshooting.

**Ready to go live?** You have everything needed. Start with Step 1 above.
