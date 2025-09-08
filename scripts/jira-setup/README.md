# Jira Setup Automation Scripts

This directory contains Python scripts to automate the setup of your Jira project for the K8s News Engine DevOps modernization initiative. The scripts are designed to work with **default Jira configurations** and provide templates for manual setup where API limitations exist.

## 🚀 Quick Start

### Prerequisites
1. **Jira Cloud account** with project administration permissions
2. **GitHub repository** with Actions enabled
3. **Python 3.8+** installed on your system

### Setup Environment
```bash
# 1. Install dependencies
cd scripts/jira-setup
pip install -r requirements.txt

# 2. Environment file is already configured
# (Using .env.kolbai with your actual credentials)

# 3. Verify your credentials are correct
cat .env.kolbai
```

### Environment Variables (Pre-configured)
Your `.env.kolbai` file contains:
```bash
# Jira Configuration
JIRA_BASE_URL=https://kolbai.atlassian.net
JIRA_USER_EMAIL=alexander.kolb@att.net
JIRA_API_TOKEN=ATATT3xFfGF0VCUkWnrnIMOOdfBBntoCvVmU-... (configured)

# GitHub Configuration  
GITHUB_TOKEN=github_pat_11AHZOIKI0PH2zlUAwOg1m_... (configured)
GITHUB_OWNER=mkolb22
GITHUB_REPO=k8s-news-engine

# Project Configuration
PROJECT_KEY=K8SNE
PROJECT_NAME=K8s News Engine
PROJECT_LEAD_EMAIL=alexander.kolb@att.net
```

## 📋 Script Execution Order

### Step 1: Inspect Jira Configuration
```bash
python 0_inspect_jira_config.py
```
**What it does:**
- Tests Jira API connection
- Inspects existing configuration (issue types, workflows, custom fields)
- Generates compatibility report
- Provides recommendations for setup

### Step 2: Create Jira Project
```bash
python 1_setup_jira_project.py
```
**What it does:**
- Creates K8SNE project with software development template
- Sets up components (Analytics Service, Publisher Service, Database, etc.)
- Creates custom fields for GitHub integration
- Configures project permissions

### Step 3: Create EPIC and User Stories
```bash
python 2_create_epic_and_stories.py
```
**What it does:**
- Creates K8SNE-1 DevOps Platform Modernization EPIC
- Creates 11 user stories across 3 phases:
  - Phase 1: CI/CD Foundation (K8SNE-2 through K8SNE-6)
  - Phase 2: Security & Secrets Management (K8SNE-7 through K8SNE-9)
  - Phase 3: Monitoring & Observability (K8SNE-11 through K8SNE-13)
- Marks K8SNE-2 as completed (GitHub Actions already implemented)
- Links stories to EPIC and assigns components

### Step 4: Generate Automation Rule Templates
```bash
python 3_setup_automation_rules.py
```
**What it does:**
- Inspects your Jira configuration for compatibility
- Generates automation rule templates for:
  - GitHub PR integration
  - Build failure handling
  - Deployment tracking
  - SLA monitoring
  - Sprint health monitoring
  - Security alerts
- Saves templates to `automation_rule_templates.json`
- Provides manual configuration instructions

### Step 5: Configure GitHub Integration
```bash
python 4_github_integration.py
```
**What it does:**
- Tests GitHub API access and repository permissions
- Checks existing webhooks
- Provides GitHub secrets configuration guide
- Sets up branch protection recommendations
- Configures GitHub Actions integration
- Creates integration summary report

## 🎯 Default Jira Compatibility

These scripts are designed to work with **standard Jira Cloud configurations**:

✅ **Compatible with:**
- Default issue types (Epic, Story, Task, Bug)
- Standard workflows and transitions
- Default priorities (High, Medium, Low, Critical)
- Standard status categories (To Do, In Progress, Done)
- Basic project permissions

✅ **No custom configuration required:**
- Uses webhook triggers (no complex custom fields)
- Leverages standard Jira automation features
- Works with default project templates
- Compatible with free Jira Cloud tier

⚠️ **Manual setup required for:**
- Automation rules (generated as templates)
- GitHub webhooks configuration
- Repository secrets setup
- Branch protection rules

## 📊 Generated Outputs

| File | Description |
|------|-------------|
| `jira_config_report.json` | Inspection results and recommendations |
| `automation_rule_templates.json` | Templates for manual automation rule setup |
| `integration_summary.json` | Complete integration setup summary |

## 🔧 Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Ensure all variables in `.env.kolbai` are set correctly
- Check that `.env.kolbai` file is in the same directory as scripts

**"Connection failed: 401"**
- Verify Jira API token is correct and not expired
- Ensure email address matches Jira account
- Check that API token has required permissions

**"Repository not found"**
- Verify GitHub token has repository access
- Check GITHUB_OWNER and GITHUB_REPO values
- Ensure repository exists and is accessible

**"Project already exists"**
- Script will detect existing project and skip creation
- Components and custom fields will be added if missing
- No data will be lost or overwritten

### API Rate Limits
- Scripts include rate limiting delays
- Jira Cloud: 10 requests per second
- GitHub: 5000 requests per hour (authenticated)

### Permissions Required

**Jira:**
- Project Administrator role
- Browse Projects permission
- Create Issues permission
- Administer Project automation (for manual rule setup)

**GitHub:**
- Repository Admin access (for webhooks and secrets)
- Actions: Read (to check workflows)
- Contents: Read (to check repository structure)

## 🎨 Customization

### Adding Custom Issue Types
Edit `2_create_epic_and_stories.py` to include additional issue types:
```python
# Add after existing user stories
{
    "key": "K8SNE-14",
    "summary": "Your Custom Story",
    "description": "Custom story description",
    "components": ["Your Component"],
    "story_points": 5,
    "status": "To Do",
    "priority": "Medium"
}
```

### Modifying Automation Rules
Edit `3_setup_automation_rules.py` to add custom rules:
```python
def setup_custom_rule(self):
    """Your custom automation rule"""
    rule_config = {
        "name": "Custom Rule Name",
        "description": "Custom rule description",
        "trigger": {"type": "webhook"},
        "actions": [{"type": "action_add_comment"}]
    }
    return self.create_automation_rule(rule_config)
```

### Custom Components
Edit `1_setup_jira_project.py` to add project components:
```python
components = [
    # Existing components...
    {
        "name": "Your Service",
        "description": "Description of your service"
    }
]
```

## 📚 Additional Resources

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Jira Automation Documentation](https://support.atlassian.com/jira-cloud-administration/docs/automation/)
- [GitHub Actions Marketplace - Jira](https://github.com/marketplace?category=&query=jira&type=actions)

## 🆘 Support

If you encounter issues:

1. **Check logs** - Each script provides detailed colored output
2. **Review configuration** - Run inspection script to verify setup
3. **Test connections** - Verify API tokens and permissions
4. **Manual fallback** - Use generated templates for manual setup

For project-specific questions, refer to the main project documentation in `/docs/`.

## 🔄 Updates and Maintenance

- **Scripts are version-controlled** with the main project
- **Templates adapt** to your Jira configuration automatically  
- **Safe to re-run** - Scripts detect existing configuration
- **Incremental setup** - Run individual scripts as needed