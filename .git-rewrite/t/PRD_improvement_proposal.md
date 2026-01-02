Below is a **clear, structured comparison** of what my corrected PRD changes relative to your previous PRD — focused specifically on aligning with **FraiseQL being a GraphQL system**, adding FraiseQL-specific features, and removing REST assumptions.

---

# 🔥 **Summary of Key Improvements**

My revised PRD introduces **5 major categories of changes**:

1. **Corrected API model: from REST-like to proper GraphQL**
2. **Added FraiseQL-specific capabilities** (Cascade mutations, Table Views, Rust pipeline, Query Plan Cache, TurboRouter)
3. **Rebuilt workload definitions for GraphQL, not REST**
4. **Added new GraphQL-specific benchmarking dimensions**
5. **Corrected instrumentation and regression criteria to reflect GraphQL execution behavior**

Below is a detailed breakdown.

---

# 1️⃣ **Corrected the API model — previous PRD treated FraiseQL like REST**

### **Your previous PRD included endpoints like:**

```
POST /query
GET /query?sql=...
```

These are not GraphQL-conformant and do not reflect how FraiseQL actually operates.

### **Changes made:**

| Before                                   | After (Correct)                                        |
| ---------------------------------------- | ------------------------------------------------------ |
| REST-like `/query` endpoint              | Standard `POST /graphql`                               |
| Optional GET queries                     | Removed (GraphQL uses POST bodies)                     |
| Mixed semantics between SQL/REST/GraphQL | Pure GraphQL document semantics                        |
| "response must contain valid JSON"       | Updated to "response must match GraphQL response spec" |

This ensures the PRD now reflects how a real GraphQL server behaves.

---

# 2️⃣ **Added FraiseQL-specific capabilities missing from the previous PRD**

Your PRD behaved like a **generic benchmarking suite**.

Mine includes engine features **unique to FraiseQL**, which must be benchmarked distinctly:

### Newly added FraiseQL-specific benchmark dimensions:

| Feature                                 | Why it matters                                                            | Added to PRD? |
| --------------------------------------- | ------------------------------------------------------------------------- | ------------- |
| **Cascade mutations**                   | FraiseQL eliminates post-mutation queries unlike any other GraphQL engine | ✅ Added       |
| **Table Views vs Live Views**           | FraiseQL has dual execution engines (CQRS pattern)                        | ✅ Added       |
| **Rust projection pipeline**            | FraiseQL does field pruning + shaping in Rust, not Python                 | ✅ Added       |
| **Query plan caching**                  | FraiseQL bypasses GraphQL parsing/validation on hot paths                 | ✅ Added       |
| **Registered operations / TurboRouter** | Enables "hot GraphQL" execution with near-zero overhead                   | ✅ Added       |

None of these were explicitly represented in your original PRD.

Now they are first-class benchmarks.

---

# 3️⃣ **Rebuilt performance workloads around GraphQL semantics**

Your original workloads were correct conceptually but implicitly REST-like or SQL-like.

### I replaced them with **GraphQL-native performance workloads**:

| Before                         | After (Correct GraphQL Workload)                              |
| ------------------------------ | ------------------------------------------------------------- |
| "simple query workload"        | Minimal GraphQL query: `{ ping }`                             |
| Parameterized SQL-like queries | GraphQL parameterized queries with variables                  |
| "randomized mixed query"       | Mixed selection sets & fragment-heavy queries                 |
| Missing deep-nesting tests     | Added nested GraphQL query workload (resolver-heavy baseline) |
| No mutation focus              | Added: mutation baseline, mutation+readback, cascade mutation |

The new workloads reflect **how GraphQL servers are evaluated in real benchmarks**, e.g. Apollo vs HotChocolate vs Yoga.

---

# 4️⃣ **Added GraphQL execution lifecycle metrics missing before**

The previous PRD used generic HTTP benchmarking metrics.

GraphQL introduces extra processing steps:

* parsing
* validation
* planning
* resolving
* serialization
* selection-set pruning

### New metrics added include:

| Metric                      | Reason                                              |
| --------------------------- | --------------------------------------------------- |
| GraphQL parse duration      | FraiseQL eliminates this when plan cache is enabled |
| GraphQL validation duration | Same as above                                       |
| Plan cache hit/miss         | Critical for distinguishing cold/warm/hot behavior  |
| Projection time (Rust)      | A unique FraiseQL strength                          |
| SQL query count (always 1)  | Confirms no accidental N+1 regressions              |

These did not appear in your earlier PRD but are essential for GraphQL benchmarking.

---

# 5️⃣ **Restructured the benchmark to include cold, warm, and hot GraphQL modes**

Your previous PRD had warm vs cold testing, but not the **GraphQL-specific execution modes**:

| Mode | Meaning                                | Newly added?                             |
| ---- | -------------------------------------- | ---------------------------------------- |
| Cold | parse + validate + plan                | (was present, now corrected for GraphQL) |
| Warm | plan cache active                      | ✅ yes                                    |
| Hot  | pre-registered operation (TurboRouter) | ✅ yes                                    |

This is completely unique to FraiseQL and had been missing.

---

# 6️⃣ **Revised CI regression rules to reflect GraphQL behaviors**

Previous thresholds were generic.

New ones include:

* Fail if **SQL queries > 1** (signals resolver regression)
* Fail if **plan cache performance drops**
* Fail if **Cascade mutation becomes slower than mutation+refetch**
* Warn if **Rust pipeline time increases**
* Different p95/p99 expectations for cold vs warm vs hot execution paths

This aligns CI with FraiseQL's actual performance promises.

---

# 7️⃣ **Corrected documentation language to match GraphQL terminology**

Changes include:

* replacing "queries" with "GraphQL operations"
* replacing "responses must contain JSON" with "responses must follow GraphQL response spec `{ data, errors }`"
* describing benchmarks in terms of *selection sets*, *fragments*, *fields*, *variables*, *non-nullability*, etc.

This ensures technical accuracy for readers familiar with GraphQL.

---

# 🧠 **Why these corrections matter**

They ensure:

* The PRD evaluates **FraiseQL as a GraphQL server**, not as a REST or SQL API.
* The benchmark highlights **FraiseQL’s real competitive advantages**.
* The structure aligns with what engineers expect in **GraphQL performance research**.
* CI can detect regressions that would affect users of FraiseQL.

---

# 📝 **If you want, I can also produce:**

### ✔ A redlined version showing exact diff between the two PRDs

### ✔ A polished final PRD ready for publication or GitHub

### ✔ A repo skeleton matching the new PRD

### ✔ JMeter `.jmx` templates ready to use

Just tell me which format you prefer.

