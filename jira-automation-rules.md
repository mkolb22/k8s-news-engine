# Jira Automation Rules for K8s News Engine DevOps

## Overview
This document provides comprehensive automation rules for the K8SNE Jira project to enable seamless CI/CD workflow integration, intelligent issue management, and automated DevOps processes.

## Prerequisites
- Jira Cloud Premium or higher (automation rules included)
- GitHub-Jira integration configured
- Custom fields created as per setup guide
- Webhook endpoints configured

---

## Rule 1: Auto-Create Issues from Failed Builds

### Purpose
Automatically create bug issues when CI/CD pipelines fail, ensuring no build failures go unnoticed.

### Configuration
**Navigate to**: Project Settings → Automation → Create Rule

**Rule Name**: Auto-Create Bug on Build Failure  
**Description**: Creates bug issues when GitHub Actions workflows fail

#### Trigger
```yaml
Type: Webhook
Webhook URL: Incoming from GitHub Actions  
Events: workflow_run (conclusion: failure)
```

#### Conditions
```yaml
Condition 1: Advanced Compare Condition
  First Value: {{webhookData.workflow_run.conclusion}}
  Condition: equals
  Second Value: failure

Condition 2: Advanced Compare Condition  
  First Value: {{webhookData.workflow_run.event}}
  Condition: equals
  Second Value: push

Condition 3: JQL Condition
  JQL: project = K8SNE AND summary ~ "Build failure: {{webhookData.workflow_run.name}}" AND resolution is EMPTY
  Condition: Issue count equals 0
```

#### Actions
```yaml
Action 1: Create Issue
  Project: K8SNE
  Issue Type: Bug
  Summary: Build failure: {{webhookData.workflow_run.name}} #{{webhookData.workflow_run.run_number}}
  Description: |
    **Automated Bug Report** 🚨
    
    GitHub Actions workflow failed and requires investigation.
    
    **Failure Details:**
    - Repository: {{webhookData.repository.full_name}}
    - Workflow: {{webhookData.workflow_run.name}}
    - Run Number: {{webhookData.workflow_run.run_number}}
    - Branch: {{webhookData.workflow_run.head_branch}}
    - Commit: {{webhookData.workflow_run.head_sha}}
    - Actor: {{webhookData.workflow_run.triggering_actor.login}}
    - Started: {{webhookData.workflow_run.created_at}}
    - Failed: {{webhookData.workflow_run.updated_at}}
    
    **Logs:** [View Failed Run]({{webhookData.workflow_run.html_url}})
    
    Please investigate and resolve this build failure immediately.
  Priority: High
  Components: CI/CD
  Labels: build-failure, automated
  Assignee: Component Lead for CI/CD
  Custom Fields:
    - GitHub Repository: {{webhookData.repository.full_name}}
    - Service Impact: All Services

Action 2: Send Notification
  Recipients: Project Lead, CI/CD Component Lead
  Subject: 🚨 Build Failure Alert - K8SNE
  Message: |
    Build failure detected in K8s News Engine.
    Issue created: {{createdIssue.key}}
    Workflow: {{webhookData.workflow_run.name}}
    Branch: {{webhookData.workflow_run.head_branch}}
    
    Please investigate immediately: [View Issue]({{createdIssue.url}})
```

---

## Rule 2: PR Status Integration

### Purpose
Automatically transition issues through the development workflow based on pull request events.

### Configuration
**Rule Name**: PR Status Sync  
**Description**: Updates issue status based on GitHub pull request events

#### Trigger
```yaml
Type: Webhook  
Events: pull_request (opened, closed, merged)
```

#### Conditions
```yaml
Condition 1: Smart Value Condition
  Smart Value: {{webhookData.pull_request}}
  Condition: is not empty

Condition 2: Advanced Compare Condition
  First Value: {{webhookData.action}}  
  Condition: is one of
  Second Value: opened, closed, synchronize
```

#### Actions

##### Action 1: PR Opened - Move to Code Review
```yaml
If/Else: If {{webhookData.action}} equals "opened"
Then:
  Action: Transition Issue
    Issue: Extract from PR title/body using regex K8SNE-\d+
    Transition: Code Review
    
  Action: Add Comment
    Issue: Same as above
    Comment: |
      **Pull Request Created** 📝
      
      - PR: [#{{webhookData.pull_request.number}}]({{webhookData.pull_request.html_url}})
      - Title: {{webhookData.pull_request.title}}
      - Author: {{webhookData.pull_request.user.login}}  
      - Branch: {{webhookData.pull_request.head.ref}} → {{webhookData.pull_request.base.ref}}
      - Files Changed: {{webhookData.pull_request.changed_files}}
      - Lines: +{{webhookData.pull_request.additions}} -{{webhookData.pull_request.deletions}}
      
      Status: Ready for code review
      
  Action: Update Field
    Field: PR Number
    Value: {{webhookData.pull_request.number}}
```

##### Action 2: PR Merged - Move to Testing  
```yaml
Else If: {{webhookData.action}} equals "closed" AND {{webhookData.pull_request.merged}} equals true
Then:
  Action: Transition Issue
    Transition: Testing
    
  Action: Add Comment
    Comment: |
      **Pull Request Merged** ✅
      
      - Merged by: {{webhookData.pull_request.merged_by.login}}
      - Merge commit: {{webhookData.pull_request.merge_commit_sha}}
      - Target branch: {{webhookData.pull_request.base.ref}}
      
      Status: Deployed to staging, ready for testing
      
  Action: Update Field  
    Field: Deployment Environment
    Value: Staging
```

##### Action 3: PR Closed Without Merge
```yaml
Else If: {{webhookData.action}} equals "closed" AND {{webhookData.pull_request.merged}} equals false  
Then:
  Action: Add Comment
    Comment: |
      **Pull Request Closed** ❌
      
      - Closed by: {{webhookData.pull_request.user.login}}
      - Status: Not merged
      - Reason: PR closed without merging
      
      Issue returned to previous status.
      
  Action: Transition Issue
    Transition: In Progress
```

---

## Rule 3: Deployment Status Automation

### Purpose  
Track deployment status and automatically update issues when deployments complete successfully or fail.

### Configuration
**Rule Name**: Deployment Status Tracker  
**Description**: Updates issues based on deployment webhook events from GitHub

#### Trigger
```yaml
Type: Webhook
Events: deployment_status
```

#### Conditions
```yaml
Condition 1: Smart Value Condition
  Smart Value: {{webhookData.deployment_status}}
  Condition: is not empty
  
Condition 2: Advanced Compare Condition
  First Value: {{webhookData.deployment_status.state}}
  Condition: is one of  
  Second Value: success, failure, error
```

#### Actions

##### Action 1: Successful Staging Deployment
```yaml
If: {{webhookData.deployment_status.state}} equals "success" AND {{webhookData.deployment.environment}} equals "staging"
Then:
  Action: Transition Issue
    Issue: Extract from deployment description K8SNE-\d+
    Transition: Testing
    
  Action: Add Comment
    Comment: |
      **Staging Deployment Successful** 🚀
      
      - Environment: {{webhookData.deployment.environment}}
      - Deployment ID: {{webhookData.deployment.id}}
      - SHA: {{webhookData.deployment.sha}}
      - Deployed at: {{webhookData.deployment_status.created_at}}
      - URL: {{webhookData.deployment_status.target_url}}
      
      Status: Ready for testing
      
  Action: Update Fields
    Deployment Environment: Staging
    Service Impact: [Based on components changed]
```

##### Action 2: Successful Production Deployment  
```yaml
Else If: {{webhookData.deployment_status.state}} equals "success" AND {{webhookData.deployment.environment}} equals "production"
Then:
  Action: Transition Issue  
    Transition: Done
    Resolution: Done
    
  Action: Add Comment
    Comment: |
      **Production Deployment Complete** 🎉
      
      - Environment: Production
      - Version: {{webhookData.deployment.ref}}
      - Deployment ID: {{webhookData.deployment.id}}
      - Deployed at: {{webhookData.deployment_status.created_at}}
      - Production URL: {{webhookData.deployment_status.target_url}}
      
      Issue resolved - feature available to users.
      
  Action: Update Fields
    Deployment Environment: Production
    Fix Version: [Extract from deployment ref]
```

##### Action 3: Deployment Failure
```yaml
Else If: {{webhookData.deployment_status.state}} is one of "failure,error"  
Then:
  Action: Create Issue
    Issue Type: Bug
    Summary: Deployment failure - {{webhookData.deployment.environment}} ({{webhookData.deployment.ref}})
    Description: |
      **Automated Deployment Failure Report** 🔥
      
      Deployment to {{webhookData.deployment.environment}} has failed and requires immediate attention.
      
      **Failure Details:**
      - Environment: {{webhookData.deployment.environment}}
      - SHA: {{webhookData.deployment.sha}}
      - Deployment ID: {{webhookData.deployment.id}}  
      - Status: {{webhookData.deployment_status.state}}
      - Description: {{webhookData.deployment_status.description}}
      - Log URL: {{webhookData.deployment_status.log_url}}
      
      **Related Issues:** [Extract from commit messages]
      
      Please investigate and resolve immediately.
    Priority: Critical
    Labels: deployment-failure, automated
    Components: Infrastructure
    Assignee: DevOps Lead
    
  Action: Send Notification
    Recipients: DevOps Team, Project Lead
    Subject: 🔥 CRITICAL: Deployment Failure - {{webhookData.deployment.environment}}
```

---

## Rule 4: Automated Testing Integration

### Purpose
Coordinate automated testing workflows with Jira issue status based on test results from CI pipelines.

### Configuration  
**Rule Name**: Test Results Integration  
**Description**: Updates issues based on automated test results

#### Trigger
```yaml
Type: Webhook
Events: check_run (GitHub Actions test results)
```

#### Conditions
```yaml
Condition 1: Advanced Compare Condition
  First Value: {{webhookData.check_run.name}}
  Condition: contains
  Second Value: test

Condition 2: Advanced Compare Condition  
  First Value: {{webhookData.check_run.status}}
  Condition: equals
  Second Value: completed
```

#### Actions

##### Action 1: Tests Passed
```yaml
If: {{webhookData.check_run.conclusion}} equals "success"
Then:
  Action: Add Comment
    Issue: Extract from commit message K8SNE-\d+
    Comment: |
      **Automated Tests Passed** ✅
      
      - Test Suite: {{webhookData.check_run.name}}
      - Status: {{webhookData.check_run.conclusion}}
      - Duration: {{webhookData.check_run.completed_at - webhookData.check_run.started_at}}
      - Details: [View Results]({{webhookData.check_run.html_url}})
      
      All tests passing - ready for deployment.
```

##### Action 2: Tests Failed  
```yaml
Else If: {{webhookData.check_run.conclusion}} is one of "failure,cancelled,timed_out"
Then:
  Action: Transition Issue
    Transition: In Progress
    
  Action: Add Comment  
    Comment: |
      **Automated Tests Failed** ❌
      
      - Test Suite: {{webhookData.check_run.name}}
      - Status: {{webhookData.check_run.conclusion}}  
      - Started: {{webhookData.check_run.started_at}}
      - Completed: {{webhookData.check_run.completed_at}}
      - Details: [View Results]({{webhookData.check_run.html_url}})
      
      Tests failing - please review and fix issues before proceeding.
      
  Action: Update Priority
    Priority: High
    
  Action: Add Label
    Label: test-failure
```

---

## Rule 5: Sprint Automation

### Purpose
Automate sprint-related activities including issue assignment, sprint planning, and retrospective preparation.

### Configuration
**Rule Name**: Sprint Management Automation  
**Description**: Manages sprint lifecycle events and issue assignments

#### Trigger
```yaml
Type: Scheduled
Trigger: Daily at 9:00 AM (business days only)
```

#### Conditions  
```yaml
Condition 1: JQL Condition
  JQL: project = K8SNE AND sprint in openSprints()
  Issue Count: greater than 0
```

#### Actions

##### Action 1: Daily Sprint Health Check
```yaml
Action: Advanced Field Update
  Script: |
    // Calculate sprint progress
    def totalIssues = issues.size()
    def completedIssues = issues.findAll { it.status.name == 'Done' }.size()  
    def inProgressIssues = issues.findAll { it.status.name == 'In Progress' }.size()
    def blockedIssues = issues.findAll { it.status.name == 'Blocked' }.size()
    
    def progressPercentage = totalIssues > 0 ? (completedIssues / totalIssues) * 100 : 0
    
    return [
      totalIssues: totalIssues,
      completed: completedIssues,  
      inProgress: inProgressIssues,
      blocked: blockedIssues,
      progress: progressPercentage
    ]

Action: Send Notification (if blocked issues > 0)
  Recipients: Scrum Master, Product Owner
  Subject: Daily Sprint Update - Blocked Issues Detected
  Message: |
    Sprint health check reveals {{blockedIssues}} blocked issues requiring attention.
    
    Sprint Progress: {{progressPercentage}}% complete
    - Total Issues: {{totalIssues}}
    - Completed: {{completedIssues}}  
    - In Progress: {{inProgressIssues}}
    - Blocked: {{blockedIssues}}
    
    Please review blocked issues and take action.
```

---

## Rule 6: SLA Monitoring & Escalation

### Purpose
Monitor issue response times and escalate overdue issues automatically.

### Configuration
**Rule Name**: SLA Escalation Management  
**Description**: Escalates issues that exceed defined SLA thresholds

#### Trigger
```yaml  
Type: Scheduled
Trigger: Every 2 hours (business hours only)
```

#### Conditions
```yaml
Condition 1: JQL Condition
  JQL: |
    project = K8SNE AND resolution is EMPTY AND (
      (priority = "Critical" AND created <= -4h) OR
      (priority = "High" AND created <= -8h) OR  
      (priority = "Medium" AND created <= -24h) OR
      (priority = "Low" AND created <= -72h)
    )
```

#### Actions

##### Action 1: Critical Issue Escalation
```yaml
If: Priority equals "Critical" AND created before "-4h"
Then:
  Action: Update Issue
    Priority: Highest
    Labels: Add "sla-breach"
    
  Action: Assign Issue
    Assignee: Project Lead
    
  Action: Add Comment
    Comment: |
      **SLA BREACH ALERT** 🚨
      
      Critical issue has exceeded 4-hour SLA threshold.
      - Created: {{issue.created}}
      - Current Age: {{now - issue.created}}
      - SLA Target: 4 hours
      
      Issue escalated to project lead for immediate attention.
      
  Action: Send Notification
    Recipients: Project Lead, DevOps Lead, Stakeholders
    Subject: 🚨 CRITICAL SLA BREACH - {{issue.key}}
    Priority: High
```

##### Action 2: General SLA Warning  
```yaml
Else:
  Action: Add Comment
    Comment: |
      **SLA Warning** ⚠️  
      
      This issue is approaching or has exceeded its SLA target:
      - Priority: {{issue.priority.name}}
      - Age: {{now - issue.created}}  
      - Target: {{issue.priority.name == "High" ? "8 hours" : issue.priority.name == "Medium" ? "24 hours" : "72 hours"}}
      
      Please prioritize resolution of this issue.
      
  Action: Update Labels
    Add Label: sla-warning
    
  Action: Send Notification  
    Recipients: Assignee, Component Lead
    Subject: SLA Warning - {{issue.key}} requires attention
```

---

## Rule 7: Release Management Automation

### Purpose
Automate release-related tasks including version creation, release notes, and deployment coordination.

### Configuration
**Rule Name**: Release Management  
**Description**: Coordinates release activities and communications

#### Trigger
```yaml
Type: Issue Event
Events: Issue Resolved (when Fix Version is set)
```

#### Conditions
```yaml
Condition 1: Field Value Changed
  Field: Fix Version
  Changed to: Any value

Condition 2: Issue Status  
  Current Status: Done
```

#### Actions

##### Action 1: Update Release Progress
```yaml
Action: Advanced Script
  Script: |
    // Calculate release progress
    def version = issue.fixVersions[0]
    def allIssuesInVersion = jqlSearch("project = K8SNE AND fixVersion = '${version.name}'")
    def resolvedIssuesInVersion = jqlSearch("project = K8SNE AND fixVersion = '${version.name}' AND resolution is not EMPTY")
    
    def progress = allIssuesInVersion.size() > 0 ? 
      (resolvedIssuesInVersion.size() / allIssuesInVersion.size()) * 100 : 0
      
    return [version: version.name, progress: progress, total: allIssuesInVersion.size(), resolved: resolvedIssuesInVersion.size()]
```

##### Action 2: Release Readiness Notification
```yaml
If: Release progress >= 100%
Then:
  Action: Send Notification
    Recipients: Release Manager, Product Owner, DevOps Lead
    Subject: 🎉 Release {{version.name}} Ready for Deployment
    Message: |
      All issues for release {{version.name}} have been resolved.
      
      **Release Summary:**
      - Total Issues: {{total}}
      - Resolved Issues: {{resolved}}  
      - Progress: 100%
      
      Release is ready for production deployment.
      
  Action: Create Issue
    Issue Type: Task
    Summary: Deploy release {{version.name}} to production
    Description: |
      **Production Deployment Task**
      
      All development work for {{version.name}} is complete.
      Please coordinate production deployment.
      
      **Included Issues:**
      [List of resolved issues in this version]
      
      **Deployment Checklist:**
      - [ ] Final security scan passed
      - [ ] Staging environment tested  
      - [ ] Database migrations prepared
      - [ ] Rollback plan confirmed
      - [ ] Monitoring alerts configured
      - [ ] Stakeholders notified
    Priority: High  
    Components: Infrastructure
    Assignee: DevOps Lead
    Fix Version: {{version.name}}
```

---

## Rule 8: Knowledge Management

### Purpose
Automatically organize and categorize issues for better knowledge management and searchability.

### Configuration
**Rule Name**: Knowledge Management  
**Description**: Categorizes and tags issues for better organization

#### Trigger
```yaml
Type: Issue Created, Issue Updated
```

#### Conditions
```yaml
Condition 1: Issue Type
  Is one of: Story, Bug, Task, Improvement
```

#### Actions

##### Action 1: Auto-labeling Based on Content  
```yaml
Action: Advanced Script for Auto-labeling
  Script: |
    def summary = issue.summary.toLowerCase()
    def description = issue.description?.toLowerCase() ?: ""
    def content = summary + " " + description
    
    def labels = []
    
    // Technology stack labels
    if (content.contains("kubernetes") || content.contains("k8s")) labels.add("kubernetes")
    if (content.contains("docker") || content.contains("container")) labels.add("containers") 
    if (content.contains("python") || content.contains("analytics")) labels.add("python")
    if (content.contains("database") || content.contains("postgresql")) labels.add("database")
    if (content.contains("security") || content.contains("rbac")) labels.add("security")
    if (content.contains("monitoring") || content.contains("prometheus")) labels.add("monitoring")
    if (content.contains("cicd") || content.contains("pipeline")) labels.add("cicd")
    
    // Complexity labels  
    if (content.contains("migration") || content.contains("refactor")) labels.add("high-complexity")
    if (content.contains("config") || content.contains("setup")) labels.add("configuration")
    if (content.contains("performance") || content.contains("optimization")) labels.add("performance")
    
    return labels

Action: Add Labels
  Labels: {{scriptResult}}
```

##### Action 2: Component Assignment Intelligence
```yaml
Action: Set Component Based on Content
  Logic: |
    If summary/description contains "analytics" OR "eqis" OR "python" → Analytics Service
    If summary/description contains "publisher" OR "lighttpd" OR "cgi" → Publisher Service  
    If summary/description contains "database" OR "postgresql" OR "schema" → Database
    If summary/description contains "kubernetes" OR "deployment" OR "infrastructure" → Infrastructure
    If summary/description contains "pipeline" OR "github" OR "actions" → CI/CD
    If summary/description contains "prometheus" OR "grafana" OR "monitoring" → Monitoring
    If summary/description contains "security" OR "rbac" OR "secrets" → Security
```

---

## Rule 9: Developer Productivity Metrics

### Purpose  
Collect metrics on development velocity, code quality, and team productivity.

### Configuration
**Rule Name**: Productivity Metrics Collection  
**Description**: Gathers metrics for team performance analysis

#### Trigger
```yaml
Type: Issue Event
Events: Issue Resolved, Issue Reopened, Issue Transitioned
```

#### Actions

##### Action 1: Cycle Time Calculation
```yaml
Action: Advanced Script - Cycle Time Tracking
  Script: |
    def createdTime = issue.created
    def resolvedTime = issue.resolutionDate ?: new Date()
    def cycleTime = resolvedTime.time - createdTime.time
    def cycleTimeHours = cycleTime / (1000 * 60 * 60)
    
    // Track by component and issue type for analysis
    def metrics = [
      issueKey: issue.key,
      issueType: issue.issueType.name,
      component: issue.components[0]?.name ?: "Unassigned",
      cycleTimeHours: cycleTimeHours,
      storyPoints: issue.customfield_10016 ?: 0, // Story Points field
      resolved: issue.resolutionDate != null
    ]
    
    return metrics

Action: Store Metrics (Custom Implementation)
  // This would integrate with external analytics system
  // or create dashboard-specific custom fields
```

---

## Testing & Validation

### Automation Rule Testing Checklist

#### Rule 1: Build Failure Detection
- [ ] Trigger test build failure in GitHub Actions
- [ ] Verify bug issue is created automatically  
- [ ] Confirm notification sent to correct recipients
- [ ] Check issue contains accurate failure details

#### Rule 2: PR Integration
- [ ] Create PR with K8SNE issue key in title
- [ ] Verify issue transitions to "Code Review"
- [ ] Merge PR and confirm transition to "Testing"  
- [ ] Check PR number is populated in custom field

#### Rule 3: Deployment Tracking
- [ ] Deploy to staging environment
- [ ] Verify issue updates with deployment info
- [ ] Deploy to production and confirm issue resolution
- [ ] Test deployment failure scenario

#### Rule 4: SLA Monitoring
- [ ] Create critical issue and wait 4+ hours
- [ ] Confirm escalation triggers automatically
- [ ] Verify stakeholder notifications sent
- [ ] Check SLA labels applied correctly

### Performance Considerations

#### Rule Optimization Guidelines
- Limit JQL queries to specific time ranges where possible
- Use smart values efficiently to reduce API calls
- Implement conditions to prevent unnecessary rule executions
- Monitor rule execution frequency and performance

#### Monitoring Rule Performance
```jql
# Query to monitor automation rule execution
project = K8SNE AND labels in (automated, build-failure, deployment-failure) 
AND created >= -7d ORDER BY created DESC
```

## Maintenance & Updates

### Monthly Rule Review Tasks
1. **Analyze rule execution statistics** - identify frequently triggered rules
2. **Review false positive rates** - optimize conditions to reduce noise
3. **Update notification recipients** - ensure correct team members receive alerts
4. **Performance optimization** - review and improve slow-running rules
5. **User feedback incorporation** - adjust rules based on team feedback

### Rule Documentation Standards  
- Maintain clear rule descriptions and purposes
- Document all webhook integrations and dependencies
- Keep testing procedures up to date
- Version control rule changes and rollback procedures

This comprehensive automation rule set provides intelligent workflow management for your K8s News Engine DevOps project, ensuring seamless integration between development activities and project tracking in Jira.