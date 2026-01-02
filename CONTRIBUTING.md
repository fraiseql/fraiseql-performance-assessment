# Contributing to FraiseQL Performance Assessment

Thank you for your interest in contributing! This document outlines guidelines for contributing to this multi-framework benchmarking suite.

## Code of Conduct

Be respectful and constructive in all interactions. We're committed to maintaining an inclusive and welcoming community.

## How to Contribute

### Reporting Issues

1. **Check existing issues** - Search to see if your issue has already been reported
2. **Provide clear details**:
   - Framework(s) affected
   - Steps to reproduce
   - Expected vs actual behavior
   - System details (OS, hardware profile)
3. **Include relevant logs** - Performance test results, error messages, system metrics

### Adding a New Framework

If you'd like to add a new framework implementation:

1. **Create a new directory** under `frameworks/` following the pattern: `frameworks/{language}-{framework}`
2. **Implement the benchmark endpoints**:
   - GraphQL `/graphql` endpoint
   - REST `/api` endpoints (where applicable)
   - Health check `/health` endpoint
3. **Add Docker support**:
   - Create `Dockerfile` with proper database connection configuration
   - Ensure it can connect to PostgreSQL at `postgres:5432`
4. **Document the implementation**:
   - Create `README.md` in the framework directory
   - Include setup instructions and any framework-specific configuration
5. **Update configurations**:
   - Add entry to `docker-compose.yml`
   - Add port mapping to `.env` files
   - Update `FRAMEWORK_MAPPING.md`

### Improving Performance Tests

To enhance the JMeter test suite:

1. **Modify test plans** in `tests/perf/jmeter/fraiseql-test-plan.jmx`
2. **Add new workload scenarios** by creating sampler groups in JMeter
3. **Update datasets** in `tests/perf/jmeter/datasets/`
4. **Document changes** in `tests/perf/README.md`

### Improving Monitoring

To enhance the monitoring stack:

1. **Add Prometheus metrics** - Modify exporters in `monitoring/prometheus/`
2. **Create Grafana dashboards** - JSON dashboard files in `monitoring/grafana/dashboards/`
3. **Add recording rules** - Update `monitoring/prometheus/recording-rules.yml`
4. **Document changes** in `monitoring/README.md`

### Documentation Updates

Documentation lives in several places:

- **Main README**: `README.md` - High-level overview
- **Start here guide**: `START_HERE.md` - Quick start for first-time users
- **Framework mapping**: `FRAMEWORK_MAPPING.md` - Framework inventory
- **Performance testing**: `tests/perf/README.md` - Detailed test instructions
- **Monitoring**: `monitoring/README.md` - Monitoring stack documentation
- **Pre-benchmark checklist**: `PRE_BENCHMARK_CHECKLIST.md` - Deployment verification

## Development Workflow

### Local Development

```bash
# Clone the repository
git clone <repo-url>
cd fraiseql-performance-assessment

# Create a feature branch
git checkout -b feature/add-new-framework

# Make your changes and test locally
make perf-smoke

# Commit with descriptive messages (see below)
git commit -m "feat(frameworks): Add rust-tokio GraphQL implementation"

# Push to your fork and create a pull request
```

### Commit Message Guidelines

Follow conventional commits format:

- `feat(scope): description` - New feature
- `fix(scope): description` - Bug fix
- `refactor(scope): description` - Code refactoring
- `docs(scope): description` - Documentation updates
- `test(scope): description` - Test additions/modifications
- `chore(scope): description` - Build, dependencies, etc.

Examples:
```
feat(frameworks): Add golang-echo REST API implementation
fix(jmeter): Correct concurrent user ramp-up calculation
docs(readme): Add multi-framework deployment guide
test(perf): Add mixed workload scenario
```

### Testing Your Changes

Before submitting a PR:

1. **Run smoke tests** to verify basic functionality:
   ```bash
   make perf-smoke
   ```

2. **Check framework health** - Verify new implementations pass health checks:
   ```bash
   curl http://localhost:XXXX/health
   ```

3. **Validate against dataset** - If modifying data layer:
   ```bash
   ./tests/integration/validate-schema.sh
   ./tests/integration/validate-queries.sh
   ```

4. **Review performance baselines** - If modifying test plan:
   - Compare new results against `tests/perf/results/baseline/`
   - Document any expected performance changes

## Pull Request Process

1. **Create a feature branch** from `main`
2. **Make focused changes** - One feature or fix per PR
3. **Update documentation** - If your changes affect usage
4. **Test thoroughly** - Include test output in PR description
5. **Write a clear description**:
   - What problem does this solve?
   - How have you tested it?
   - Any breaking changes?
   - Performance impact (if applicable)?

### PR Title Format

```
[TYPE] Brief description (framework/component affected)

Examples:
[FEAT] Add Java Quarkus GraphQL framework
[FIX] Correct N+1 query detection in naive implementations
[DOCS] Update monitoring setup guide
```

## Style Guidelines

### Code Style

- **Python**: Follow PEP 8, use `ruff` for linting
- **JavaScript/Node.js**: Use standardized formatting
- **Go**: Follow Go conventions, use `gofmt`
- **Java**: Follow Google Java Style Guide
- **Rust**: Use `rustfmt` for formatting

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep paragraphs short
- Use markdown formatting consistently
- Add section headers for organization

## Hardware & Environment Considerations

Since this project benchmarks across different hardware profiles:

- **Document your test environment** in PR description
- **Include hardware specs** if adding framework-specific configurations
- **Test on modest hardware** when possible - this suite should work on t3.large cloud instances
- **Note performance characteristics** specific to your implementation

## Performance Baseline Maintenance

When adding features that might affect performance:

1. Establish new baseline with `make perf-warm`
2. Document expected performance impact
3. Update baseline thresholds in `ci/baseline-thresholds.json` if needed
4. Include before/after metrics in PR

## Questions?

- Open a GitHub Discussion for general questions
- Create an Issue for bugs or feature requests
- Check `START_HERE.md` and `PRE_BENCHMARK_CHECKLIST.md` for common questions

Thank you for contributing! 🚀
