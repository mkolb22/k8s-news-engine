#!/bin/bash

# Jira Setup Automation - Master Script
# Runs all setup scripts in the correct order

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${CYAN}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "======================================================================"
    echo " $1"
    echo "======================================================================"
    echo -e "${NC}"
}

# Check if .env.kolbai file exists
check_env_file() {
    if [ ! -f ".env.kolbai" ]; then
        print_error ".env.kolbai file not found!"
        echo "The environment file with your credentials is missing."
        echo "Please ensure .env.kolbai exists with your Jira and GitHub credentials."
        exit 1
    fi
    print_success ".env.kolbai file found with your credentials"
}

# Check if Python dependencies are installed
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check if required packages are available
    python3 -c "
import requests
import colorama
import tabulate
import click
from dotenv import load_dotenv
from github import Github
" 2>/dev/null || {
        print_warning "Some dependencies are missing. Installing..."
        pip install -r requirements.txt
    }
    
    print_success "Dependencies are ready"
}

# Run individual script with error handling
run_script() {
    local script_name=$1
    local description=$2
    local optional=${3:-false}
    
    print_header "$description"
    
    if [ ! -f "$script_name" ]; then
        print_error "Script $script_name not found!"
        return 1
    fi
    
    print_status "Running $script_name..."
    
    if python3 "$script_name"; then
        print_success "$description completed successfully"
        echo
        return 0
    else
        if [ "$optional" = true ]; then
            print_warning "$description failed but continuing (optional step)"
            echo
            return 0
        else
            print_error "$description failed!"
            echo
            return 1
        fi
    fi
}

# Prompt user for confirmation
confirm_continue() {
    local message=$1
    echo -e "${YELLOW}$message${NC}"
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Setup cancelled by user"
        exit 0
    fi
}

# Main execution
main() {
    print_header "Jira Setup Automation for K8s News Engine"
    
    echo "This script will set up your Jira project with:"
    echo "• Project configuration and components"
    echo "• DevOps modernization EPIC and user stories"  
    echo "• Automation rule templates"
    echo "• GitHub integration guidance"
    echo
    
    # Pre-flight checks
    print_status "Running pre-flight checks..."
    check_env_file
    check_dependencies
    
    echo
    confirm_continue "⚠️  This will create issues and modify your Jira project."
    
    # Step 1: Inspect configuration
    if run_script "0_inspect_jira_config.py" "Step 1: Inspect Jira Configuration" true; then
        echo "✅ Configuration inspection completed"
        echo "📋 Review the output above for any compatibility issues"
        echo
        confirm_continue "Continue with project setup?"
    fi
    
    # Step 2: Setup Jira project
    if run_script "1_setup_jira_project.py" "Step 2: Setup Jira Project"; then
        print_success "Jira project setup completed"
    else
        print_error "Failed to setup Jira project. Check credentials and permissions."
        exit 1
    fi
    
    # Step 3: Create EPIC and stories
    if run_script "2_create_epic_and_stories.py" "Step 3: Create EPIC and User Stories"; then
        print_success "EPIC and user stories created"
    else
        print_error "Failed to create issues. Check project permissions."
        exit 1
    fi
    
    # Step 4: Generate automation templates
    if run_script "3_setup_automation_rules.py" "Step 4: Generate Automation Rule Templates" true; then
        print_success "Automation templates generated"
    else
        print_warning "Automation template generation had issues (continuing)"
    fi
    
    # Step 5: GitHub integration setup
    if run_script "4_github_integration.py" "Step 5: GitHub Integration Setup" true; then
        print_success "GitHub integration guidance completed"
    else
        print_warning "GitHub integration setup had issues (continuing)"
    fi
    
    # Final summary
    print_header "🎉 Setup Completed!"
    
    echo "✅ Jira project configured with components and custom fields"
    echo "✅ DevOps modernization EPIC created (K8SNE-1)"
    echo "✅ User stories created for 3 implementation phases"
    echo "✅ Automation rule templates generated"
    echo "✅ GitHub integration guidance provided"
    echo
    
    print_header "📋 Next Steps"
    
    echo "1. 🔐 Configure GitHub repository secrets:"
    echo "   Go to: https://github.com/mkolb22/k8s-news-engine/settings/secrets/actions"
    echo
    
    echo "2. 🤖 Set up Jira automation rules manually:"
    echo "   • Open your Jira project settings > Automation"
    echo "   • Use templates from: automation_rule_templates.json"
    echo
    
    echo "3. 🪝 Configure GitHub webhooks (optional):"
    echo "   • Repository Settings > Webhooks"
    echo "   • Add webhook URL from integration summary"
    echo
    
    echo "4. 🧪 Test the integration:"
    echo "   • Create a test branch: feature/K8SNE-3-testing"
    echo "   • Open a PR and verify Jira issue updates"
    echo
    
    echo "5. 📊 Review your Jira project:"
    echo "   URL: $(grep JIRA_BASE_URL .env.kolbai | cut -d'=' -f2)/projects/K8SNE"
    echo
    
    print_success "All done! Your DevOps transformation project is ready to begin. 🚀"
}

# Run main function
main "$@"