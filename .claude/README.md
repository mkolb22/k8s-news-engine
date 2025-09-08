# Claude Subagents for K8s News Engine

This directory contains specialized AI subagents to assist with various aspects of the K8s News Engine project.

## Available Subagents

### Kubernetes Specialists
- **k8s-engineer** - Kubernetes deployment and manifest specialist
- **k8s-devops-engineer** - Kubernetes DevOps and CI/CD pipeline specialist  
- **k8s-admin** - Kubernetes cluster administration specialist

### DevOps Specialists
- **devops-engineer** - General DevOps and infrastructure automation
- **devops-docker-engineer** - Docker containerization and optimization
- **devops-ai-mcp-engineer** - AI/ML operations and MCP integration

### Development Specialists
- **frontend-developer** - Frontend web development specialist
- **software-team-lead** - Software project management and architecture

### Administration Specialists
- **atlassian-cloud-administrator** - Atlassian Cloud suite administration
- **jira-cloud-administrator** - Jira Cloud configuration and workflow

## Usage

To invoke a specific subagent for a task, use:
```
@<agent-name> <your request>
```

For example:
```
@k8s-engineer help me optimize the PostgreSQL deployment manifest
@devops-docker-engineer create a multi-stage Dockerfile for the RSS fetcher
```

## Configuration

The `agents-config.yaml` file contains:
- Agent descriptions and capabilities
- Trigger keywords for automatic agent suggestion
- Project-specific preferences
- File pattern associations

## Auto-Invocation

Certain agents are automatically suggested based on:
- File types being edited (*.yaml → k8s-engineer)
- Keywords in your requests
- Current context and task type

## Adding New Agents

To add a new agent:
1. Place the agent definition file in `.claude/agents/`
2. Update `agents-config.yaml` with the agent metadata
3. Define triggers and capabilities

## Project-Specific Agents

For this K8s News Engine project, the primary agents are:
- k8s-engineer (for Kubernetes manifests)
- k8s-devops-engineer (for deployment automation)
- devops-docker-engineer (for containerization)