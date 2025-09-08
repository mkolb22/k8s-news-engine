#!/usr/bin/env python3
"""
GitHub Integration Setup for Jira
Configures GitHub repository settings and webhooks for Jira integration
"""

import requests
import json
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init
from tabulate import tabulate
from github import Github

# Initialize colorama for cross-platform colored output
init()

# Load environment variables
load_dotenv('.env.kolbai')

class GitHubJiraIntegration:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_owner = os.getenv('GITHUB_OWNER', 'mkolb22')
        self.github_repo = os.getenv('GITHUB_REPO', 'k8s-news-engine')
        self.jira_base_url = os.getenv('JIRA_BASE_URL')
        self.project_key = os.getenv('PROJECT_KEY', 'K8SNE')
        
        if not all([self.github_token, self.jira_base_url]):
            raise ValueError("Missing required environment variables. Check .env file.")
        
        self.github = Github(self.github_token)
        self.repo = None
        
        print(f"{Fore.CYAN}🔗 Setting up GitHub-Jira Integration{Style.RESET_ALL}")
        print(f"Repository: {self.github_owner}/{self.github_repo}")
        print(f"Jira Project: {self.project_key}")
    
    def test_github_access(self):
        """Test GitHub API access and get repository info"""
        print(f"\n{Fore.YELLOW}Testing GitHub access...{Style.RESET_ALL}")
        
        try:
            # Get user info
            user = self.github.get_user()
            print(f"{Fore.GREEN}✅ Connected as: {user.login}{Style.RESET_ALL}")
            
            # Get repository
            self.repo = self.github.get_repo(f"{self.github_owner}/{self.github_repo}")
            
            repo_info = [
                ["Repository", self.repo.full_name],
                ["Description", self.repo.description or "N/A"],
                ["Private", "Yes" if self.repo.private else "No"],
                ["Default Branch", self.repo.default_branch],
                ["Has Issues", "Yes" if self.repo.has_issues else "No"],
                ["Has Actions", "Yes" if hasattr(self.repo, 'get_actions_permissions') else "Unknown"]
            ]
            
            print(f"\n{Fore.CYAN}📊 Repository Information:{Style.RESET_ALL}")
            print(tabulate(repo_info, headers=["Property", "Value"], tablefmt="grid"))
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ GitHub access failed: {str(e)}{Style.RESET_ALL}")
            return False
    
    def check_existing_webhooks(self):
        """Check for existing webhooks"""
        print(f"\n{Fore.YELLOW}Checking existing webhooks...{Style.RESET_ALL}")
        
        try:
            webhooks = self.repo.get_hooks()
            
            webhook_table = []
            jira_webhooks = []
            
            for webhook in webhooks:
                webhook_table.append([
                    webhook.id,
                    webhook.config.get('url', 'N/A'),
                    ', '.join(webhook.events),
                    "✅" if webhook.active else "❌"
                ])
                
                # Check if it's a Jira webhook
                if 'jira' in webhook.config.get('url', '').lower() or 'atlassian' in webhook.config.get('url', '').lower():
                    jira_webhooks.append(webhook)
            
            if webhook_table:
                print(f"{Fore.CYAN}🪝 Existing Webhooks:{Style.RESET_ALL}")
                print(tabulate(webhook_table, headers=["ID", "URL", "Events", "Active"], tablefmt="grid"))
                
                if jira_webhooks:
                    print(f"{Fore.GREEN}✅ Found {len(jira_webhooks)} existing Jira webhook(s){Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ No webhooks configured{Style.RESET_ALL}")
            
            return jira_webhooks
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error checking webhooks: {str(e)}{Style.RESET_ALL}")
            return []
    
    def setup_github_secrets(self):
        """Guide for setting up GitHub repository secrets"""
        print(f"\n{Fore.YELLOW}Setting up GitHub repository secrets...{Style.RESET_ALL}")
        
        required_secrets = [
            {
                "name": "JIRA_BASE_URL",
                "description": "Your Jira instance URL",
                "example": "https://your-domain.atlassian.net",
                "current": self.jira_base_url
            },
            {
                "name": "JIRA_API_TOKEN",
                "description": "Jira API token for authentication",
                "example": "ATATT3xFfGF0...",
                "current": "*** (from .env)"
            },
            {
                "name": "JIRA_USER_EMAIL", 
                "description": "Email address for Jira API authentication",
                "example": "user@domain.com",
                "current": os.getenv('JIRA_USER_EMAIL', 'Not set')
            },
            {
                "name": "KUBE_CONFIG_STAGING",
                "description": "Base64 encoded kubeconfig for staging environment",
                "example": "LS0tLS1CRUdJTi...",
                "current": "Not set"
            },
            {
                "name": "KUBE_CONFIG_PROD",
                "description": "Base64 encoded kubeconfig for production environment", 
                "example": "LS0tLS1CRUdJTi...",
                "current": "Not set"
            }
        ]
        
        secret_table = []
        for secret in required_secrets:
            secret_table.append([
                secret["name"],
                secret["description"],
                secret["current"]
            ])
        
        print(f"{Fore.CYAN}🔐 Required GitHub Repository Secrets:{Style.RESET_ALL}")
        print(tabulate(secret_table, headers=["Secret Name", "Description", "Current Value"], tablefmt="grid"))
        
        print(f"\n{Fore.CYAN}📋 Setup Instructions:{Style.RESET_ALL}")
        print(f"1. Go to https://github.com/{self.github_owner}/{self.github_repo}/settings/secrets/actions")
        print("2. Click 'New repository secret' for each required secret")
        print("3. Use the secret names and values from the table above")
        print("4. For Kubernetes configs, base64 encode your kubeconfig files:")
        print("   cat ~/.kube/config | base64 | tr -d '\\n'")
        
        return required_secrets
    
    def create_jira_webhook_config(self):
        """Create webhook configuration for Jira integration"""
        print(f"\n{Fore.YELLOW}Creating Jira webhook configuration...{Style.RESET_ALL}")
        
        # Standard Jira webhook URL (this may need to be adjusted based on your Jira setup)
        webhook_url = f"{self.jira_base_url}/rest/webhooks/1.0/webhook/jira"
        
        webhook_config = {
            "name": "Jira Integration Webhook",
            "active": True,
            "events": [
                "push",
                "pull_request",
                "pull_request_review",
                "workflow_run",
                "deployment_status",
                "security_advisory"
            ],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        print(f"{Fore.CYAN}🔧 Webhook Configuration:{Style.RESET_ALL}")
        config_table = [
            ["URL", webhook_config["config"]["url"]],
            ["Events", ", ".join(webhook_config["events"])],
            ["Content Type", webhook_config["config"]["content_type"]],
            ["Active", "Yes" if webhook_config["active"] else "No"]
        ]
        
        print(tabulate(config_table, headers=["Property", "Value"], tablefmt="grid"))
        
        return webhook_config
    
    def setup_branch_protection(self):
        """Set up branch protection rules"""
        print(f"\n{Fore.YELLOW}Setting up branch protection rules...{Style.RESET_ALL}")
        
        try:
            # Get the main branch
            main_branch = self.repo.get_branch(self.repo.default_branch)
            
            # Check current protection status
            try:
                protection = main_branch.get_protection()
                print(f"{Fore.GREEN}✅ Branch protection already exists for {main_branch.name}{Style.RESET_ALL}")
                
                protection_info = [
                    ["Required Status Checks", "Yes" if protection.required_status_checks else "No"],
                    ["Enforce Admins", "Yes" if protection.enforce_admins else "No"],
                    ["Required Reviews", str(protection.required_pull_request_reviews.required_approving_review_count) if protection.required_pull_request_reviews else "0"],
                    ["Dismiss Stale Reviews", "Yes" if protection.required_pull_request_reviews and protection.required_pull_request_reviews.dismiss_stale_reviews else "No"]
                ]
                
                print(f"\n{Fore.CYAN}🛡️ Current Protection Settings:{Style.RESET_ALL}")
                print(tabulate(protection_info, headers=["Setting", "Value"], tablefmt="grid"))
                
            except Exception:
                print(f"{Fore.YELLOW}⚠️ No branch protection configured for {main_branch.name}{Style.RESET_ALL}")
                print(f"\n{Fore.CYAN}📋 Recommended Protection Rules:{Style.RESET_ALL}")
                
                recommendations = [
                    ["Require PR reviews", "At least 1 approving review"],
                    ["Dismiss stale reviews", "When new commits are pushed"],
                    ["Require status checks", "All CI/CD workflows must pass"],
                    ["Require branches up to date", "Before merging"],
                    ["Include administrators", "Apply rules to admins too"],
                    ["Allow force pushes", "Disabled for security"]
                ]
                
                print(tabulate(recommendations, headers=["Setting", "Recommendation"], tablefmt="grid"))
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error checking branch protection: {str(e)}{Style.RESET_ALL}")
            return False
    
    def setup_github_actions_integration(self):
        """Configure GitHub Actions for Jira integration"""
        print(f"\n{Fore.YELLOW}Configuring GitHub Actions integration...{Style.RESET_ALL}")
        
        # Check if our Jira integration workflow exists
        try:
            workflows_path = ".github/workflows"
            jira_workflow = None
            
            try:
                contents = self.repo.get_contents(workflows_path)
                
                workflow_files = []
                for content in contents:
                    if content.name.endswith('.yml') or content.name.endswith('.yaml'):
                        workflow_files.append([content.name, content.size, content.html_url])
                        
                        if 'jira' in content.name.lower():
                            jira_workflow = content
                
                if workflow_files:
                    print(f"{Fore.CYAN}⚙️ Existing GitHub Actions Workflows:{Style.RESET_ALL}")
                    print(tabulate(workflow_files, headers=["File", "Size (bytes)", "URL"], tablefmt="grid"))
                
                if jira_workflow:
                    print(f"{Fore.GREEN}✅ Jira integration workflow found: {jira_workflow.name}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}⚠️ No Jira integration workflow found{Style.RESET_ALL}")
                    
            except Exception:
                print(f"{Fore.YELLOW}⚠️ No workflows directory found{Style.RESET_ALL}")
            
            # Provide integration recommendations
            print(f"\n{Fore.CYAN}🔧 GitHub Actions Integration Recommendations:{Style.RESET_ALL}")
            
            integration_steps = [
                "✅ Install Jira GitHub Actions from marketplace",
                "✅ Use atlassian/gajira-login@v3 for authentication", 
                "✅ Use atlassian/gajira-create@v3 for issue creation",
                "✅ Use atlassian/gajira-transition@v3 for status updates",
                "✅ Extract Jira issue keys from branch names or PR titles",
                "✅ Update issues on PR events (opened, merged, closed)",
                "✅ Create issues for deployment tracking and failures"
            ]
            
            for step in integration_steps:
                print(f"  {step}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error checking GitHub Actions: {str(e)}{Style.RESET_ALL}")
            return False
    
    def create_integration_summary(self):
        """Create integration setup summary"""
        print(f"\n{Fore.CYAN}📋 Integration Setup Summary{Style.RESET_ALL}")
        
        summary_data = {
            "repository": f"{self.github_owner}/{self.github_repo}",
            "jira_project": self.project_key,
            "jira_url": self.jira_base_url,
            "integration_type": "GitHub Actions + Webhooks",
            "setup_date": "2025-09-08",
            "features": [
                "Automatic issue transitions on PR events",
                "Build failure issue creation",
                "Deployment tracking",
                "Branch name to issue key linking",
                "Commit message issue updates",
                "Security vulnerability alerts"
            ],
            "required_actions": [
                "Configure GitHub repository secrets",
                "Set up Jira automation rules manually", 
                "Test webhook delivery",
                "Enable branch protection rules",
                "Train team on naming conventions"
            ]
        }
        
        # Save summary to file
        summary_file = "/Users/kolb/Documents/github/k8s-news-engine/scripts/jira-setup/integration_summary.json"
        
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            print(f"{Fore.GREEN}✅ Integration summary saved to: {summary_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving summary: {str(e)}{Style.RESET_ALL}")
        
        return summary_data
    
    def run_github_integration(self):
        """Run the complete GitHub integration setup"""
        try:
            # Test GitHub access
            if not self.test_github_access():
                return False
            
            # Check existing webhooks
            existing_webhooks = self.check_existing_webhooks()
            
            # Setup GitHub secrets (guidance)
            self.setup_github_secrets()
            
            # Create webhook configuration
            webhook_config = self.create_jira_webhook_config()
            
            # Setup branch protection
            self.setup_branch_protection()
            
            # Configure GitHub Actions integration
            self.setup_github_actions_integration()
            
            # Create summary
            summary = self.create_integration_summary()
            
            print(f"\n{Fore.GREEN}🎉 GitHub-Jira integration setup completed!{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}📋 Next Steps:{Style.RESET_ALL}")
            print("1. Configure GitHub repository secrets as shown above")
            print("2. Set up Jira automation rules using the generated templates")
            print("3. Test the integration with a sample PR workflow")
            print("4. Configure team training on branch naming conventions")
            print("5. Monitor integration health and adjust as needed")
            
            print(f"\n{Fore.CYAN}🔧 Branch Naming Convention:{Style.RESET_ALL}")
            print("feature/K8SNE-123-add-monitoring")
            print("bugfix/K8SNE-456-fix-security-issue") 
            print("hotfix/K8SNE-789-critical-patch")
            
            print(f"\n{Fore.CYAN}💬 Commit Message Convention:{Style.RESET_ALL}")
            print("K8SNE-123: Add Prometheus monitoring dashboard")
            print("K8SNE-456: Fix container security vulnerability")
            
            print(f"\n{Fore.YELLOW}⚠️  Manual Actions Required:{Style.RESET_ALL}")
            print("🔐 Set GitHub repository secrets")
            print("🤖 Configure Jira automation rules")
            print("🪝 Test webhook delivery")
            print("🛡️ Enable branch protection (optional)")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ GitHub integration setup failed: {str(e)}{Style.RESET_ALL}")
            return False

if __name__ == "__main__":
    try:
        integration = GitHubJiraIntegration()
        integration.run_github_integration()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Integration setup interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")