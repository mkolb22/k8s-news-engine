# Publisher Service Container Requirements

## Base Image Requirement

**MANDATORY**: This service MUST use Alpine Linux as its base image.

### Rationale
1. **Security**: Alpine Linux provides a minimal attack surface with its musl libc and busybox utilities
2. **Size**: Alpine images are significantly smaller (5MB base) compared to other distributions
3. **Performance**: Smaller images mean faster pulls, deploys, and cold starts
4. **Package Management**: APK package manager is fast and provides all required dependencies
5. **Compatibility**: All Python and web server dependencies are well-supported on Alpine

### Current Configuration
- **Base Image**: `alpine:3.20`
- **Alpine Version**: 3.20 LTS (Long Term Support)
- **Support Period**: Until April 2026
- **Architecture**: Multi-arch (amd64, arm64, armv7)

### Dependencies Available on Alpine
All required dependencies are available via Alpine's APK package manager:
- `lighttpd` - Web server
- `python3` - Python runtime
- `py3-psycopg2` - PostgreSQL adapter
- `py3-numpy`, `py3-scipy`, `py3-scikit-learn` - ML libraries
- `py3-nltk` - Natural language processing

### Version Policy
- Use Alpine LTS versions for production stability
- Current: `alpine:3.20`
- Upgrade path: Only upgrade to newer LTS versions after testing
- Never use `alpine:latest` to avoid unexpected breaking changes

### Security Considerations
- Alpine uses musl libc instead of glibc (smaller, more secure)
- Runs as non-root user (UID 1000)
- No unnecessary packages or tools included
- Regular security updates via `apk upgrade`

## DO NOT CHANGE
The base image requirement is architectural and should not be changed without:
1. Security review
2. Performance testing
3. Dependency compatibility verification
4. Team consensus