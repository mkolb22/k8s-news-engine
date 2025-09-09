# Subagent Setup Guide for K8s News Engine

## Overview
This project has been configured with 5 specialized subagents to assist with development tasks. The subagents are properly configured and ready for use.

## Available Subagents

### 🚀 k8s-engineer
- **Purpose**: Kubernetes manifests and deployment specialist
- **Triggers**: kubernetes, k8s, deployment, manifest, pod, service, configmap
- **Use for**: Writing YAML manifests, debugging deployments, resource optimization

### 🔧 devops-engineer  
- **Purpose**: CI/CD pipeline and deployment automation specialist
- **Triggers**: ci/cd, pipeline, deployment, automation, monitoring, docker
- **Use for**: Build automation, deployment strategies, monitoring setup

### 🐳 docker-engineer
- **Purpose**: Container optimization and security specialist  
- **Triggers**: docker, dockerfile, container, image, alpine
- **Use for**: Dockerfile optimization, security hardening, multi-stage builds

### 🗄️ database-engineer
- **Purpose**: PostgreSQL database specialist
- **Triggers**: database, postgresql, sql, schema, migration
- **Use for**: Schema design, query optimization, migrations

### 🐍 python-analytics
- **Purpose**: Python analytics and ML specialist
- **Triggers**: python, analytics, ml, scikit-learn, nltk, pandas
- **Use for**: Data processing, ML algorithms, EQIS implementation

## How to Use Subagents

### Method 1: Direct Reference
```
@k8s-engineer help me create a deployment manifest for the publisher service
```

### Method 2: Keyword Triggers
```
I need to optimize this Dockerfile for better security
```
(This will automatically suggest the docker-engineer subagent)

### Method 3: File Context
When working with specific files, subagents are auto-suggested:
- `*.yaml` files → k8s-engineer
- `Dockerfile*` → docker-engineer  
- `*.py` files → python-analytics
- `*.sql` files → database-engineer

## Configuration Files

### Primary Configuration
- **`.claude/agents-config.yaml`**: Main agent definitions and triggers
- **`.claude/project-config.yaml`**: Project-specific settings and initialization
- **`.claude/agents.json`**: Alternative JSON format configuration

### Agent Definitions
All subagent definitions are stored in `.claude/agents/`:
- `k8s-engineer.agent`
- `devops-engineer.agent`
- `docker-engineer.agent`
- `database-engineer.agent`
- `python-analytics.agent`

## Verification

### Check Subagent Status
Run the initialization script to verify all subagents are properly configured:
```bash
./.claude/init.sh
```

### Expected Output
```
✅ Subagent initialization complete!

Available subagents:
  • k8s-engineer: Kubernetes manifests and deployment
  • devops-engineer: CI/CD and deployment automation
  • docker-engineer: Container optimization and security
  • database-engineer: PostgreSQL schema and queries
  • python-analytics: Analytics and ML development
```

## Troubleshooting

### Subagents Not Loading
1. **Check file permissions**:
   ```bash
   chmod 644 .claude/*.yaml .claude/*.json
   chmod 644 .claude/agents/*.agent
   ```

2. **Verify directory structure**:
   ```
   .claude/
   ├── agents/
   │   ├── k8s-engineer.agent
   │   ├── devops-engineer.agent
   │   ├── docker-engineer.agent
   │   ├── database-engineer.agent
   └── └── python-analytics.agent
   ├── agents-config.yaml
   ├── project-config.yaml
   └── agents.json
   ```

3. **Run initialization script**:
   ```bash
   ./.claude/init.sh
   ```

### Configuration Issues
- Ensure agent file paths in `agents-config.yaml` use correct `.agent` extension
- Verify all agent files have required fields: `name`, `description`, `instructions`
- Check YAML syntax is valid

## Auto-Initialization
The project is configured to auto-load subagents when Claude Code starts. The following files ensure proper initialization:

- `.claude/project-config.yaml` - Project settings and auto-load configuration
- `.claude/init.sh` - Verification and setup script
- `.claude/agents-config.yaml` - Agent definitions and triggers

## Best Practices

1. **Use specific triggers**: Mention relevant keywords to get the right subagent
2. **Be context-aware**: Work in relevant files to auto-trigger appropriate agents  
3. **Multi-agent tasks**: Complex tasks can use multiple subagents simultaneously
4. **Verify setup**: Run the init script after any configuration changes

---

**Status**: ✅ All subagents configured and verified working
**Last Updated**: September 9, 2025
**Version**: 1.0