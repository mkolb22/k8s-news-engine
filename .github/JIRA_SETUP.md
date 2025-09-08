# Jira Integration Setup for K8s News Engine

## Required Jira Project Configuration

### 1. Jira Project Setup
- **Project Key**: `K8SNE` (K8s News Engine)
- **Project Type**: Software Development
- **Issue Types**: Epic, Story, Task, Bug, Sub-task

### 2. GitHub Secrets Configuration
Add these secrets to your GitHub repository settings:

```
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@domain.com  
JIRA_API_TOKEN=your-api-token
KUBE_CONFIG_STAGING=base64-encoded-staging-kubeconfig
KUBE_CONFIG_PROD=base64-encoded-production-kubeconfig
```

### 3. Jira Components
Create these components in your Jira project:
- Analytics Service
- Publisher Service  
- Database
- Infrastructure
- CI/CD
- Monitoring

### 4. Jira Workflow States
Ensure these workflow states exist:
- To Do
- In Progress
- In Review
- Testing
- Done

## EPIC: K8SNE-1 DevOps Platform Modernization

### Epic Summary
Transform K8s News Engine into production-ready platform with enterprise DevOps practices

### User Stories Breakdown

#### Phase 1: CI/CD Foundation (4 weeks)
- **K8SNE-2**: GitHub Actions CI/CD Pipeline Setup
  - Story Points: 8
  - Components: CI/CD, Analytics Service, Publisher Service
  - Acceptance Criteria:
    - [ ] Automated builds on push to main/develop
    - [ ] Container images pushed to GitHub Container Registry
    - [ ] Parallel builds for both services
    - [ ] Integration with Jira for issue tracking

- **K8SNE-3**: Automated Testing Implementation  
  - Story Points: 13
  - Components: Analytics Service, CI/CD
  - Acceptance Criteria:
    - [ ] Unit tests with pytest for analytics service
    - [ ] Code coverage reporting (>80%)
    - [ ] Lint checks with flake8
    - [ ] Tests run automatically in CI pipeline

- **K8SNE-4**: Container Security Scanning
  - Story Points: 5
  - Components: CI/CD, Infrastructure
  - Acceptance Criteria:
    - [ ] Trivy vulnerability scanning integrated
    - [ ] Results uploaded to GitHub Security tab
    - [ ] Pipeline fails on critical vulnerabilities
    - [ ] Weekly security report generation

#### Phase 2: Security & Secrets (2 weeks)
- **K8SNE-7**: Kubernetes Secrets Migration
  - Story Points: 8
  - Components: Infrastructure, Database
  - Acceptance Criteria:
    - [ ] Database credentials moved to K8s secrets
    - [ ] Sealed Secrets or External Secrets Operator implemented
    - [ ] No hardcoded credentials in manifests
    - [ ] Secret rotation procedure documented

#### Phase 3: Monitoring (4 weeks)  
- **K8SNE-11**: Prometheus + Grafana Deployment
  - Story Points: 13
  - Components: Monitoring, Infrastructure
  - Acceptance Criteria:
    - [ ] Prometheus deployed with persistent storage
    - [ ] Grafana dashboards for all services
    - [ ] ServiceMonitor configurations created
    - [ ] Basic alerting rules implemented

### Success Metrics
- Deployment frequency: >10/day
- Lead time: <2 hours
- MTTR: <30 minutes  
- Uptime: >99.95%
- Security scan coverage: 100%

## Automation Features

### Branch Naming Convention
Use Jira issue keys in branch names for automatic linking:
- `feature/K8SNE-2-github-actions-setup`
- `bugfix/K8SNE-15-monitoring-alerts`
- `hotfix/K8SNE-23-security-patch`

### Commit Message Convention  
Include Jira keys in commit messages:
- `K8SNE-2: Add GitHub Actions workflow for CI/CD`
- `K8SNE-3: Implement pytest tests for analytics service`

### Automated Workflows
1. **PR Creation**: Auto-transitions Jira issue to "In Review"
2. **PR Merge**: Auto-transitions to "Done"  
3. **Production Deploy**: Creates deployment tracking issue
4. **Pipeline Failure**: Creates bug issue with failure details

## Getting Started
1. Create Jira project with key `K8SNE`
2. Configure GitHub secrets
3. Push changes to trigger first pipeline
4. Monitor Jira for automatic issue creation and updates