# Jira Cloud Project Setup Guide: K8s News Engine DevOps Modernization

## 1. Project Creation & Configuration

### Basic Project Setup
1. **Navigate to Projects** → Create Project
2. **Project Template**: Software Development (Scrum/Kanban Hybrid)
3. **Project Configuration**:
   - **Project Name**: K8s News Engine DevOps
   - **Project Key**: K8SNE
   - **Project Lead**: [Assign appropriate team lead]
   - **Default Assignee**: Project Lead

### Project Components Configuration
Navigate to Project Settings → Components and create:

```
Component Name          | Lead                    | Description
--------------------- | ----------------------- | ------------------------------------
Analytics Service     | Backend Development     | Python EQIS analytics service
Publisher Service     | Backend Development     | Lighttpd-based content delivery
Database             | Database Administrator   | PostgreSQL schema and operations
Infrastructure       | DevOps Engineer         | Kubernetes, networking, storage
CI/CD                | DevOps Engineer         | GitHub Actions, deployment automation
Monitoring           | SRE Team                | Observability, alerting, metrics
Security             | Security Engineer       | RBAC, secrets, scanning, compliance
```

### Custom Fields Configuration

Navigate to Settings → Issues → Custom Fields → Create Custom Field:

#### 1. GitHub Repository (Single line text)
- **Field Name**: GitHub Repository
- **Description**: Associated GitHub repository
- **Context**: All issue types for K8SNE project
- **Default Value**: mkolb22/k8s-news-engine

#### 2. PR Number (Number Field)
- **Field Name**: Pull Request Number  
- **Description**: Associated GitHub Pull Request number
- **Context**: All issue types for K8SNE project

#### 3. Deployment Environment (Single Select)
- **Field Name**: Deployment Environment
- **Description**: Target deployment environment
- **Options**: Development, Staging, Production
- **Context**: Story, Bug, Task

#### 4. Service Impact (Multi Select)
- **Field Name**: Service Impact
- **Description**: Which services are affected
- **Options**: Analytics, Publisher, Database, All Services
- **Context**: All issue types

#### 5. Technical Debt Priority (Single Select)
- **Field Name**: Tech Debt Priority
- **Description**: Priority level for technical debt items
- **Options**: Critical, High, Medium, Low
- **Context**: Story, Task, Improvement

## 2. Workflow Configuration

### Enhanced DevOps Workflow States
Navigate to Project Settings → Workflows → Edit Workflow:

#### Workflow States:
1. **Backlog** (Initial state)
2. **Ready for Development** 
3. **In Progress**
4. **Code Review** (PR created)
5. **Testing** (PR approved, deployed to staging)
6. **Ready for Production**
7. **Done** (Deployed to production)
8. **Blocked** (Can transition from any state)

#### Workflow Transitions with Conditions:

**Backlog → Ready for Development**
- Condition: Story points assigned AND acceptance criteria defined
- Validator: Required fields validation

**Ready for Development → In Progress** 
- Condition: Assignee must be set
- Post Function: Set "Started Date" field

**In Progress → Code Review**
- Condition: PR Number field must be populated
- Validator: GitHub repository field required
- Post Function: Add comment "PR created: [PR URL]"

**Code Review → Testing**
- Condition: PR approved (GitHub webhook trigger)
- Post Function: Update environment field to "Staging"

**Testing → Ready for Production**
- Condition: All tests passed AND QA approval
- Validator: Deployment environment validation

**Ready for Production → Done**
- Condition: Deployed to production
- Post Function: Set resolution date, update environment to "Production"

**Any State → Blocked**
- Condition: Always available
- Required Field: Reason for blocking

## 3. Screen Configuration

### Create Custom Screens
Navigate to Settings → Issues → Screens:

#### DevOps Story Screen
Include these fields:
- Summary, Description, Story Points
- Components, Fix Versions
- Assignee, Reporter, Priority
- GitHub Repository, PR Number
- Deployment Environment, Service Impact
- Acceptance Criteria (Description field)

#### Bug Screen  
Include these fields:
- Summary, Description, Priority
- Components, Affects Versions
- Environment (custom field), Service Impact
- Steps to Reproduce, Expected Results, Actual Results
- GitHub Repository, PR Number

#### Epic Screen
Include these fields:
- Summary, Description, Epic Name
- Components, Fix Versions  
- Epic Color, Start Date, Due Date
- Business Value, Success Metrics

## 4. Permission Scheme

### DevOps Project Permissions
Navigate to Settings → System → Permission Schemes:

#### Key Permission Groups:
- **K8SNE Developers**: Create, edit, transition issues; add comments
- **K8SNE DevOps**: All developer permissions + admin project, manage versions
- **K8SNE Stakeholders**: View issues, add comments, create issues
- **K8SNE Administrators**: Full project permissions

#### Critical Permission Settings:
```
Permission                    | K8SNE Developers | K8SNE DevOps | K8SNE Stakeholders | K8SNE Admin
----------------------------- | ---------------- | ------------ | ------------------ | -----------
Browse Projects               | ✓                | ✓            | ✓                  | ✓
Create Issues                 | ✓                | ✓            | ✓                  | ✓
Edit Issues                   | ✓                | ✓            | Own issues only    | ✓
Transition Issues             | ✓                | ✓            | ✗                  | ✓
Delete Issues                 | ✗                | ✓            | ✗                  | ✓
Administer Projects           | ✗                | ✓            | ✗                  | ✓
Manage Versions               | ✗                | ✓            | ✗                  | ✓
```

## 5. Version Management

### Release Version Naming Convention
Navigate to Project Settings → Versions:

Create versions following semantic versioning:
- **v1.1.0 - Infrastructure Foundation** (Current Sprint)
- **v1.2.0 - CI/CD Implementation** 
- **v1.3.0 - Security Hardening**
- **v1.4.0 - Monitoring & Observability**
- **v2.0.0 - Production Readiness**

## 6. Agile Boards Configuration

### Scrum Board Setup
1. **Navigate to** Project → Boards → Create Board → Create Scrum Board
2. **Board Name**: K8SNE DevOps Scrum
3. **Columns Configuration**:
   - Backlog
   - Ready for Dev
   - In Progress  
   - Code Review
   - Testing
   - Done

### Kanban Board Setup  
1. **Create Kanban Board**: K8SNE DevOps Kanban
2. **Column Configuration**:
   - Backlog (Backlog, Ready for Development)
   - Development (In Progress)
   - Review (Code Review) 
   - Testing (Testing, Ready for Production)
   - Done (Done)

### Board Filters
**Scrum Board Filter**:
```jql
project = K8SNE AND (fixVersion in openVersions() OR fixVersion is EMPTY) AND resolution is EMPTY
```

**Kanban Board Filter**:
```jql
project = K8SNE AND resolution is EMPTY ORDER BY priority DESC, created ASC
```

### Quick Filters
Create these quick filters for easy board navigation:
- **My Issues**: `assignee = currentUser()`
- **Critical/Blocker**: `priority in (Highest, High)`
- **This Sprint**: `sprint in openSprints()`
- **Analytics Service**: `component = "Analytics Service"`
- **Publisher Service**: `component = "Publisher Service"`
- **Infrastructure**: `component = Infrastructure`

## 7. Notification Scheme

### DevOps Notification Events
Navigate to Settings → System → Notification Schemes:

#### Key Notification Rules:
- **Issue Created**: Assignee, Project Lead, Component Lead
- **Issue Updated**: Assignee, Reporter, Watchers
- **Issue Resolved**: Reporter, Watchers, QA Team
- **Issue Transitioned**: Assignee, Reporter, Component Lead
- **Version Released**: All Project Users

#### Integration-Specific Notifications:
- **PR Created** (via automation): Component Lead, Code Reviewers
- **Deployment Failed** (via webhook): DevOps Team, Assignee
- **Production Incident**: All Stakeholders, On-call Engineer

## Next Steps

After completing this basic configuration:
1. **Test workflow transitions** with sample issues
2. **Configure GitHub integration** (see GitHub Integration Guide)
3. **Set up automation rules** (see Automation Rules Guide)  
4. **Import initial EPIC and User Stories** (see User Stories Guide)
5. **Configure team access** and train users on new workflow
6. **Set up reporting dashboards** for sprint planning and metrics

## Maintenance Tasks

### Weekly:
- Review and update component assignments
- Clean up resolved issues older than 30 days
- Update version progress and release notes

### Monthly:  
- Review permission scheme effectiveness
- Analyze workflow bottlenecks via reports
- Update custom field options based on team feedback
- Review and optimize JQL filters for performance