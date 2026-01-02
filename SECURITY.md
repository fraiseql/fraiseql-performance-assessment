# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this repository, please **do not** open a public GitHub Issue. Instead:

1. **Email security details** to: `lionel.hamayon@evolution-digitale.fr`
2. **Include in your report**:
   - Description of the vulnerability
   - Steps to reproduce (if applicable)
   - Potential impact
   - Suggested fix (if you have one)

3. **We will**:
   - Acknowledge receipt within 48 hours
   - Provide a timeline for a fix
   - Keep you updated on progress
   - Credit you in the security advisory (if desired)

## Scope

This security policy applies to:
- Code in the main repository
- Docker containers and images
- CI/CD workflows
- Database schema and fixtures

## Out of Scope

The following are NOT in scope for security issues:

- **Test Infrastructure**: JMeter test plans, load testing scripts
- **Documentation**: README files, setup guides
- **Performance Benchmarks**: Test data generators, monitoring scripts
- **Development Tools**: Configuration files, helper scripts

These may contain temporary credentials, test data, or configurations intentionally designed for testing environments.

## Known Security Considerations

### 1. Test Database

The included PostgreSQL database comes with:
- **Default credentials**: Configured in `.env` files
- **Purpose**: Local development and testing only
- **Security**: Should NEVER be used in production
- **Recommendation**: Use environment-specific configurations with proper credential management

### 2. Docker Containers

Framework implementations in this repository:
- Include test/example implementations
- Use default credentials in container configurations
- Are designed for benchmarking, not production deployment
- Should be secured with proper secrets management in production

### 3. Load Testing Data

The dataset includes:
- Synthetic user data
- Example blog posts and comments
- No personally identifiable information (PII)
- Safe for public benchmarking

## Dependency Management

We maintain security through:

1. **Regular updates** - Dependencies are periodically updated
2. **Vulnerability scanning** - GitHub's dependabot monitors for issues
3. **Minimal dependencies** - Framework implementations keep dependencies minimal
4. **Lock files** - `Cargo.lock`, `package-lock.json`, `go.sum` are committed for reproducibility

## CI/CD Security

GitHub Actions workflows in `.github/workflows/`:
- Run on public repository
- Do not contain credentials (use GitHub Secrets)
- Generate public artifacts (test results, reports)
- Follow principle of least privilege

## Data Privacy

This repository:
- Contains **no real user data**
- Uses **synthetic datasets** for benchmarking
- Does **not collect** any personal information
- Is safe to fork and use publicly

## Best Practices for Users

If you're using this repository:

1. **Never use test credentials in production**
2. **Always rotate secrets** in your deployment environments
3. **Use environment-specific configurations** for different stages
4. **Enable authentication** for any public-facing monitoring dashboards
5. **Restrict network access** to your monitoring stack
6. **Keep dependencies updated** in your fork

## Security Advisories

We will publish security advisories for:
- Critical vulnerabilities affecting deployment security
- Issues requiring immediate action
- Framework-level security concerns

Check the Security tab on GitHub for published advisories.

## Questions?

For security-related questions or concerns, email: `lionel.hamayon@evolution-digitale.fr`

---

**Last Updated**: January 2025
