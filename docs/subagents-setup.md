# Claude Code Subagents Setup Documentation

## Problem
The Claude Code console was not detecting any subagents for the K8s News Engine project when running the `/agents` command.

## Root Cause
Claude Code requires agent configurations in a specific format (.agent files) in the `.claude/agents/` directory. The project had markdown files (.md) with agent descriptions but not the proper .agent configuration files that Claude Code expects.

## Solution Implemented

### 1. Backed Up Original Files
Created a timestamped backup of the original agents directory:
```bash
cp -r .claude/agents archive/agents-backup-$(date +%Y%m%d-%H%M%S)
```

### 2. Created Agent Configuration Files
Created properly formatted `.agent` files for each specialist role:

#### Created Agents:
1. **k8s-engineer.agent** - Kubernetes deployment and manifest specialist
2. **python-analytics.agent** - Python developer for EQIS algorithm implementation
3. **docker-engineer.agent** - Docker containerization expert
4. **database-engineer.agent** - PostgreSQL schema and optimization specialist
5. **devops-engineer.agent** - CI/CD pipeline and deployment automation specialist

### 3. Agent File Format
Each `.agent` file follows this structure:
```yaml
name: agent-identifier
description: Brief description of the agent's specialty
proactive: true
instructions: |
  Detailed instructions including:
  - Agent's expertise areas
  - Project-specific context
  - Key responsibilities
  - Best practices to follow
  - Tools and technologies used
```

### 4. Created agents.json Configuration
Also created a `agents.json` file in `.claude/` directory with:
- Agent definitions with IDs, names, and descriptions
- Tool permissions for each agent
- Trigger keywords for automatic agent selection
- Global settings for agent behavior

## How to Verify
Run the `/agents` command in Claude Code console to see the list of available subagents.

## Usage
These agents can now be invoked for specialized tasks:
- Use `k8s-engineer` for Kubernetes manifest work
- Use `python-analytics` for EQIS algorithm changes
- Use `docker-engineer` for Dockerfile optimization
- Use `database-engineer` for schema changes
- Use `devops-engineer` for CI/CD pipeline setup

## File Structure
```
.claude/
├── agents.json                 # Main agent configuration
├── agents-config.yaml          # Original YAML config (preserved)
└── agents/
    ├── k8s-engineer.agent      # K8s specialist
    ├── python-analytics.agent  # Analytics developer
    ├── docker-engineer.agent   # Docker specialist
    ├── database-engineer.agent # Database engineer
    ├── devops-engineer.agent   # DevOps specialist
    └── *.md                    # Original markdown files (preserved)
```

## Benefits
- Specialized agents for different aspects of the project
- Automatic agent selection based on task context
- Better code quality through domain-specific expertise
- Consistent application of best practices