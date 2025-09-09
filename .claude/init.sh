#!/bin/bash

# Claude Code Subagent Initialization Script
# This script ensures all subagents are properly configured and available

echo "🚀 Initializing Claude Code subagents for K8s News Engine..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"

# Verify .claude directory structure
echo "📁 Verifying .claude directory structure..."
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "❌ .claude directory not found at $CLAUDE_DIR"
    exit 1
fi

if [ ! -d "$CLAUDE_DIR/agents" ]; then
    echo "❌ agents directory not found"
    exit 1
fi

# Count available agents
AGENT_COUNT=$(find "$CLAUDE_DIR/agents" -name "*.agent" | wc -l)
echo "🤖 Found $AGENT_COUNT subagent definitions:"

# List all available agents
for agent_file in "$CLAUDE_DIR/agents"/*.agent; do
    if [ -f "$agent_file" ]; then
        agent_name=$(basename "$agent_file" .agent)
        echo "   ✓ $agent_name"
    fi
done

# Verify configuration files
echo "⚙️  Verifying configuration files..."

if [ -f "$CLAUDE_DIR/agents-config.yaml" ]; then
    echo "   ✓ agents-config.yaml found"
else
    echo "   ❌ agents-config.yaml missing"
fi

if [ -f "$CLAUDE_DIR/project-config.yaml" ]; then
    echo "   ✓ project-config.yaml found"
else
    echo "   ❌ project-config.yaml missing"
fi

if [ -f "$CLAUDE_DIR/agents.json" ]; then
    echo "   ✓ agents.json found"
else
    echo "   ❌ agents.json missing"
fi

# Validate agent file syntax
echo "🔍 Validating agent file syntax..."
for agent_file in "$CLAUDE_DIR/agents"/*.agent; do
    if [ -f "$agent_file" ]; then
        agent_name=$(basename "$agent_file" .agent)
        
        # Check if file has required fields
        if grep -q "^name:" "$agent_file" && grep -q "^description:" "$agent_file" && grep -q "^instructions:" "$agent_file"; then
            echo "   ✓ $agent_name syntax valid"
        else
            echo "   ❌ $agent_name missing required fields"
        fi
    fi
done

# Set proper permissions
echo "🔒 Setting proper file permissions..."
chmod 644 "$CLAUDE_DIR"/*.yaml "$CLAUDE_DIR"/*.json 2>/dev/null
chmod 644 "$CLAUDE_DIR/agents"/*.agent 2>/dev/null
chmod +x "$CLAUDE_DIR/init.sh" 2>/dev/null

echo "✅ Subagent initialization complete!"
echo ""
echo "Available subagents:"
echo "  • k8s-engineer: Kubernetes manifests and deployment"
echo "  • devops-engineer: CI/CD and deployment automation" 
echo "  • docker-engineer: Container optimization and security"
echo "  • database-engineer: PostgreSQL schema and queries"
echo "  • python-analytics: Analytics and ML development"
echo ""
echo "To use a subagent, use @subagent-name or mention relevant keywords in your requests."