# GitHub-Jira Integration Setup Guide

## Overview
This guide configures seamless integration between your GitHub repository (`mkolb22/k8s-news-engine`) and your Jira Cloud project (K8SNE) to enable automated issue tracking, status updates, and deployment coordination.

## 1. GitHub Secrets Configuration

### Required Repository Secrets
Navigate to GitHub → Settings → Secrets and Variables → Actions:

```bash
# Jira Integration Secrets
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-automation-email@company.com  
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=K8SNE

# Additional Integration Secrets  
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
TEAMS_WEBHOOK_URL=https://your-teams-webhook-url
```

### Jira API Token Creation
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Label: "K8SNE GitHub Integration"
4. Copy token and store securely in GitHub Secrets as `JIRA_API_TOKEN`

## 2. GitHub Workflow Enhancement

### Enhanced GitHub Actions Workflow
Update your `.github/workflows/ci-cd.yml`:

```yaml
name: K8SNE CI/CD with Jira Integration

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main, develop]

env:
  JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
  JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT_KEY }}

jobs:
  extract-jira-issues:
    runs-on: ubuntu-latest
    outputs:
      issues: ${{ steps.extract.outputs.issues }}
    steps:
      - name: Extract Jira Issue Keys
        id: extract
        run: |
          # Extract K8SNE-XXX from commit messages and PR title
          ISSUES=$(echo "${{ github.event.head_commit.message }} ${{ github.event.pull_request.title }}" | grep -oE 'K8SNE-[0-9]+' | sort -u | tr '\n' ',' | sed 's/,$//')
          echo "issues=$ISSUES" >> $GITHUB_OUTPUT
          echo "Found Jira issues: $ISSUES"

  build-and-test:
    runs-on: ubuntu-latest
    needs: extract-jira-issues
    steps:
      - uses: actions/checkout@v4
      
      - name: Update Jira Issue - Build Started
        if: needs.extract-jira-issues.outputs.issues != ''
        uses: atlassian/gajira-transition@master
        with:
          issue: ${{ needs.extract-jira-issues.outputs.issues }}
          transition: "In Progress"
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          JIRA_USER_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Run Tests
        run: |
          cd services/analytics-py
          pip install -r requirements.txt
          pip install pytest pytest-cov
          pytest --cov=. --cov-report=xml
          
      - name: Security Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload Trivy Results to Jira
        if: needs.extract-jira-issues.outputs.issues != '' && always()
        uses: atlassian/gajira-comment@master
        with:
          issue: ${{ needs.extract-jira-issues.outputs.issues }}
          comment: |
            **Security Scan Results** 🔒
            - Workflow: ${{ github.workflow }}
            - Commit: ${{ github.sha }}
            - Trivy Scan: ${{ job.status == 'success' && '✅ Passed' || '❌ Failed' }}
            - Details: [View in Actions](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          JIRA_USER_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}

      - name: Build Docker Images
        run: |
          docker build -t eqis-analytics:${{ github.sha }} ./services/analytics-py
          docker build -t publisher:${{ github.sha }} ./services/publisher

  deploy-staging:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    needs: [extract-jira-issues, build-and-test]
    steps:
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment"
          # Add your staging deployment commands here
          
      - name: Update Jira - Deployed to Staging
        if: needs.extract-jira-issues.outputs.issues != ''
        uses: atlassian/gajira-transition@master
        with:
          issue: ${{ needs.extract-jira-issues.outputs.issues }}
          transition: "Testing"
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          JIRA_USER_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          
      - name: Add Deployment Comment to Jira
        if: needs.extract-jira-issues.outputs.issues != ''
        uses: atlassian/gajira-comment@master
        with:
          issue: ${{ needs.extract-jira-issues.outputs.issues }}
          comment: |
            **Staging Deployment Complete** 🚀
            - Environment: Staging
            - Version: ${{ github.sha }}
            - Time: ${{ steps.date.outputs.date }}
            - Status: ${{ job.status == 'success' && '✅ Success' || '❌ Failed' }}
            - Staging URL: https://staging.k8s-news-engine.com
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          JIRA_USER_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}

  deploy-production:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    needs: [extract-jira-issues, build-and-test]
    steps:
      - name: Deploy to Production
        run: |
          echo "Deploying to production environment"
          # Add your production deployment commands here
          
      - name: Update Jira - Ready for Production
        if: needs.extract-jira-issues.outputs.issues != ''
        uses: atlassian/gajira-transition@master
        with:
          issue: ${{ needs.extract-jira-issues.outputs.issues }}
          transition: "Done"
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          JIRA_USER_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}

  failure-notification:
    if: failure()
    runs-on: ubuntu-latest  
    needs: [extract-jira-issues, build-and-test]
    steps:
      - name: Create Bug Issue on Failure
        if: needs.extract-jira-issues.outputs.issues != ''
        uses: atlassian/gajira-create@master
        with:
          project: K8SNE
          issuetype: Bug
          summary: "CI/CD Pipeline Failure - ${{ github.workflow }} #${{ github.run_number }}"
          description: |
            **Automated Bug Report** 🚨
            
            CI/CD pipeline failed during execution.
            
            **Details:**
            - Workflow: ${{ github.workflow }}
            - Run Number: ${{ github.run_number }}
            - Branch: ${{ github.ref }}
            - Commit: ${{ github.sha }}
            - Triggered by: ${{ github.actor }}
            
            **Related Issues:** ${{ needs.extract-jira-issues.outputs.issues }}
            
            **Action Required:**
            Please investigate the failure and resolve the issue.
            
            [View Failed Run](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          JIRA_USER_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
```

## 3. Branch Naming Conventions

### Standardized Branch Naming
Implement these branch naming conventions to enable automatic Jira linking:

```bash
# Feature branches
feature/K8SNE-3-automated-testing
feature/K8SNE-4-container-security

# Bug fix branches  
bugfix/K8SNE-25-analytics-memory-leak
hotfix/K8SNE-26-critical-api-error

# Release branches
release/v1.2.0-K8SNE-sprint-2

# Examples of commit messages that trigger Jira integration:
git commit -m "K8SNE-3: Add pytest configuration for analytics service"
git commit -m "K8SNE-4: Integrate Trivy security scanning into CI pipeline"
git commit -m "Fix database connection issue - resolves K8SNE-25"
```

## 4. Webhook Configuration

### Jira Webhook Setup
1. **Navigate to**: Jira Settings → System → Webhooks
2. **Create Webhook** with these settings:

```json
{
  "name": "GitHub Integration Webhook",
  "url": "https://api.github.com/repos/mkolb22/k8s-news-engine/dispatches",
  "events": [
    "jira:issue_updated",
    "jira:issue_deleted", 
    "comment_created",
    "worklog_updated"
  ],
  "jqlFilter": "project = K8SNE",
  "headers": {
    "Authorization": "token YOUR_GITHUB_PAT",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
  }
}
```

### GitHub Webhook for Jira
Configure repository webhook:
1. **GitHub Settings** → Webhooks → Add Webhook
2. **Payload URL**: `https://your-domain.atlassian.net/rest/api/2/issue/webhook`
3. **Content Type**: application/json
4. **Events**: Push, Pull Request, Issues, Deployment Status

## 5. Pull Request Integration

### Smart Commit Messages
Configure automatic PR to Jira issue linking:

```bash
# PR Titles that auto-link to Jira
"K8SNE-3: Implement automated testing framework"
"K8SNE-4: Add Trivy security scanning to CI"

# PR Descriptions with Jira integration
## Changes Made
- Added pytest configuration
- Implemented unit tests for EQIS algorithm
- Set up coverage reporting

## Jira Issues
- Resolves K8SNE-3
- Related to K8SNE-1

## Testing
- [x] Unit tests pass
- [x] Coverage above 80%
- [x] Integration tests pass

## Checklist
- [x] Code reviewed
- [x] Tests added/updated  
- [x] Documentation updated
- [x] Jira issue linked
```

## 6. Jira Automation Rules

### Create Automation Rules in Jira
Navigate to Project Settings → Automation → Create Rule:

### Rule 1: PR Created Transition
```yaml
Trigger: Webhook received
Webhook URL: GitHub webhook URL
Conditions: 
  - Webhook data contains "pull_request"
  - Issue exists in project K8SNE
Actions:
  - Transition issue to "Code Review"
  - Add comment: "Pull request created: {{webhookData.pull_request.html_url}}"
  - Set field "PR Number": {{webhookData.pull_request.number}}
```

### Rule 2: PR Merged Transition  
```yaml
Trigger: Webhook received
Conditions:
  - Webhook data contains "pull_request" 
  - Pull request state is "closed"
  - Pull request merged is true
Actions:
  - Transition issue to "Testing"
  - Add comment: "Pull request merged successfully"
  - Update field "Deployment Environment": "Staging"
```

### Rule 3: Deployment Success Notification
```yaml
Trigger: Webhook received  
Conditions:
  - Webhook data contains "deployment_status"
  - Deployment state is "success"
Actions:
  - Transition issue to "Done" 
  - Add comment: "Deployment successful to {{webhookData.deployment.environment}}"
  - Set Resolution: "Done"
  - Set Environment: {{webhookData.deployment.environment}}
```

### Rule 4: Failed Build Notification
```yaml
Trigger: Webhook received
Conditions:
  - Webhook data contains "workflow_run"
  - Workflow conclusion is "failure"  
Actions:
  - Create linked issue (Bug type)
  - Set summary: "Build failure: {{webhookData.workflow_run.name}}"
  - Assign to: Component lead
  - Set priority: High
  - Add label: "build-failure"
```

## 7. Dashboard Configuration

### GitHub Integration Dashboard
Create a Jira dashboard with these gadgets:

#### Gadget 1: Issues by Status
```jql
project = K8SNE AND "GitHub Repository" is not EMPTY
```

#### Gadget 2: Recent Deployments  
```jql
project = K8SNE AND "Deployment Environment" in (Staging, Production) AND resolved >= -7d
```

#### Gadget 3: Failed Builds
```jql
project = K8SNE AND labels = "build-failure" AND resolution is EMPTY
```

#### Gadget 4: PR Review Backlog
```jql
project = K8SNE AND status = "Code Review" AND "PR Number" is not EMPTY
```

## 8. Slack Integration (Optional)

### Slack Notifications Setup
Add to your GitHub workflow:

```yaml
- name: Notify Slack on Deployment
  if: success() && needs.extract-jira-issues.outputs.issues != ''
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    custom_payload: |
      {
        text: "K8SNE Deployment Complete",
        attachments: [{
          color: '${{ job.status }}' === 'success' ? 'good' : 'danger',
          fields: [{
            title: 'Environment',
            value: '${{ github.ref == "refs/heads/main" && "Staging" || "Production" }}',
            short: true
          }, {
            title: 'Jira Issues',
            value: '${{ needs.extract-jira-issues.outputs.issues }}',
            short: true
          }, {
            title: 'Commit',
            value: '<${{ github.server_url }}/${{ github.repository }}/commit/${{ github.sha }}|${{ github.sha }}>',
            short: true
          }]
        }]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## 9. Testing the Integration

### Validation Steps
1. **Create test branch**: `feature/K8SNE-99-integration-test`
2. **Make small change** and commit with: `"K8SNE-99: Test GitHub-Jira integration"`
3. **Create pull request** with title: `"K8SNE-99: Integration test"`
4. **Verify automatic transitions** in Jira issue
5. **Merge PR** and verify final status update
6. **Check Jira comments** for automation updates

### Troubleshooting Common Issues

#### Authentication Issues
- Verify Jira API token is valid and not expired
- Check GitHub repository secrets are correctly configured
- Ensure Jira user has proper permissions for automation

#### Webhook Failures  
- Verify webhook URLs are accessible
- Check webhook payload format matches expected schema
- Review webhook delivery history in both GitHub and Jira

#### Missing Issue Transitions
- Verify workflow transitions are configured correctly
- Check automation rule conditions and actions
- Ensure issue key format matches regex patterns

#### Integration Testing Checklist
- [ ] GitHub Actions can authenticate with Jira
- [ ] Issue keys are extracted from commit messages
- [ ] Issues transition properly through workflow states
- [ ] Comments are added automatically with build/deployment info
- [ ] Failed builds create bug issues automatically  
- [ ] Dashboard shows GitHub integration data correctly
- [ ] Slack notifications work (if configured)

## 10. Maintenance & Monitoring

### Regular Maintenance Tasks

#### Weekly:
- Review webhook delivery logs for failures
- Check for orphaned branches with unlinked issues  
- Validate automation rule execution statistics

#### Monthly:
- Rotate Jira API tokens for security
- Review and optimize automation rule performance
- Update integration documentation with new features

#### Monitoring Metrics:
- Webhook success rate (target: >98%)
- Average issue transition time (target: <4 hours)
- Failed build notification accuracy (target: 100%)
- Developer adoption rate (target: >90% issues linked)

This integration setup provides a robust connection between your GitHub repository and Jira project, enabling automated workflow management and comprehensive DevOps visibility.