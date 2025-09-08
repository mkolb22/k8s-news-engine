#!/usr/bin/env python3
"""
Setup Jira Automation Rules for GitHub Integration
"""

import requests
import json
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init
from tabulate import tabulate

# Initialize colorama for cross-platform colored output
init()

# Load environment variables
load_dotenv('.env.kolbai')

class JiraAutomationSetup:
    def __init__(self):
        self.base_url = os.getenv('JIRA_BASE_URL')
        self.email = os.getenv('JIRA_USER_EMAIL') 
        self.api_token = os.getenv('JIRA_API_TOKEN')
        self.project_key = os.getenv('PROJECT_KEY', 'K8SNE')
        
        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Missing required environment variables. Check .env file.")
            
        self.auth = (self.email, self.api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Will be populated by inspection
        self.issue_types = {}
        self.custom_fields = {}
        self.project_id = None
        
        print(f"{Fore.CYAN}🤖 Setting up Jira Automation Rules for {self.project_key}{Style.RESET_ALL}")
    
    def inspect_jira_config(self):
        """Inspect current Jira configuration to adapt automation rules"""
        print(f"\n{Fore.YELLOW}Inspecting Jira configuration for compatibility...{Style.RESET_ALL}")
        
        try:
            # Get project info
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{self.project_key}",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                project = response.json()
                self.project_id = project.get('id')
                
                # Get issue types
                for issue_type in project.get('issueTypes', []):
                    self.issue_types[issue_type['name'].lower()] = issue_type['id']
                
                print(f"{Fore.GREEN}✅ Found project: {project.get('name')}{Style.RESET_ALL}")
                print(f"   Available issue types: {list(self.issue_types.keys())}")
            
            # Get custom fields (look for common ones)
            field_response = requests.get(
                f"{self.base_url}/rest/api/3/field",
                auth=self.auth,
                headers=self.headers
            )
            
            if field_response.status_code == 200:
                fields = field_response.json()
                
                # Look for common custom fields
                field_mapping = {
                    'Epic Link': 'epic_link',
                    'Story Points': 'story_points',
                    'Sprint': 'sprint'
                }
                
                for field in fields:
                    field_name = field.get('name', '')
                    if field_name in field_mapping:
                        self.custom_fields[field_mapping[field_name]] = field.get('id')
                
                print(f"{Fore.GREEN}✅ Detected custom fields: {list(self.custom_fields.keys())}{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Could not fully inspect config: {str(e)}{Style.RESET_ALL}")
            print(f"   Will use default configurations")
            return False
    
    def get_project_id(self):
        """Get project ID for automation rules"""
        return self.project_id
    
    def create_automation_rule(self, rule_config):
        """Create a single automation rule using standard Jira automation API"""
        print(f"{Fore.CYAN}📝 Note: This creates automation rule templates that need manual configuration{Style.RESET_ALL}")
        print(f"   Rule: {rule_config.get('name', 'Unnamed Rule')}")
        
        # Since automation rule creation via API requires specific permissions and setup,
        # we'll create templates that can be manually configured in Jira
        return self.create_rule_template(rule_config)
    
    def create_rule_template(self, rule_config):
        """Create a template for manual rule configuration"""
        template = {
            "name": rule_config.get("name"),
            "description": rule_config.get("description"),
            "template_type": "jira_automation",
            "configuration_steps": [
                f"1. Go to Project Settings > Automation in {self.project_key}",
                "2. Click 'Create rule'",
                f"3. Set name: {rule_config.get('name')}",
                f"4. Set description: {rule_config.get('description')}",
                "5. Configure trigger, conditions, and actions as specified below"
            ],
            "trigger": rule_config.get("trigger"),
            "conditions": rule_config.get("conditions", []),
            "actions": rule_config.get("actions", [])
        }
        
        return template
    
    def setup_pr_integration_rule(self):
        """Rule to handle GitHub PR events"""
        print(f"\n{Fore.YELLOW}Creating PR Integration Rule...{Style.RESET_ALL}")
        
        rule_config = {
            "name": "GitHub PR Integration",
            "description": "Automatically update Jira issues when GitHub PRs are created, updated, or merged",
            "trigger": {
                "type": "webhook",
                "webhook": {
                    "name": "GitHub PR Events",
                    "url": f"{self.base_url}/secure/webhooks/github"
                }
            },
            "conditions": [
                {
                    "type": "condition_compare_text",
                    "configuration": {
                        "value": "{{webhookData.action}}",
                        "comparator": "EQUALS",
                        "expected": "opened"
                    }
                }
            ],
            "actions": [
                {
                    "type": "action_transition_issue",
                    "configuration": {
                        "transition": "In Review"
                    }
                },
                {
                    "type": "action_add_comment",
                    "configuration": {
                        "comment": "🔍 **Pull Request Created**\\n\\n**PR:** {{webhookData.pull_request.html_url}}\\n**Branch:** {{webhookData.pull_request.head.ref}}\\n**Author:** {{webhookData.pull_request.user.login}}\\n\\nThis issue is now in review."
                    }
                }
            ],
            "scope": {
                "type": "project",
                "projectId": self.get_project_id()
            }
        }
        
        rule = self.create_automation_rule(rule_config)
        if rule:
            print(f"{Fore.GREEN}  ✅ PR Integration Rule created{Style.RESET_ALL}")
            return rule
        return None
    
    def setup_build_failure_rule(self):
        """Rule to create bugs from GitHub Actions failures"""
        print(f"\n{Fore.YELLOW}Creating Build Failure Rule...{Style.RESET_ALL}")
        
        rule_config = {
            "name": "GitHub Actions Build Failure",
            "description": "Automatically create bug issues when GitHub Actions builds fail",
            "trigger": {
                "type": "webhook",
                "webhook": {
                    "name": "GitHub Actions Status",
                    "url": f"{self.base_url}/secure/webhooks/github-actions"
                }
            },
            "conditions": [
                {
                    "type": "condition_compare_text",
                    "configuration": {
                        "value": "{{webhookData.state}}",
                        "comparator": "EQUALS", 
                        "expected": "failure"
                    }
                }
            ],
            "actions": [
                {
                    "type": "action_create_issue",
                    "configuration": {
                        "issueType": "Bug",
                        "summary": "CI/CD Pipeline Failure - {{webhookData.name}} #{{webhookData.run_number}}",
                        "description": "🚨 **Build Failure Alert**\\n\\n**Workflow:** {{webhookData.name}}\\n**Run:** {{webhookData.run_number}}\\n**Branch:** {{webhookData.head_branch}}\\n**Commit:** {{webhookData.head_sha}}\\n**URL:** {{webhookData.html_url}}\\n\\n**Action Required:**\\n- Review build logs\\n- Fix failing tests or build issues\\n- Re-run pipeline after fix",
                        "priority": "High",
                        "labels": ["ci-cd", "pipeline-failure", "automated"]
                    }
                }
            ],
            "scope": {
                "type": "project",
                "projectId": self.get_project_id()
            }
        }
        
        rule = self.create_automation_rule(rule_config)
        if rule:
            print(f"{Fore.GREEN}  ✅ Build Failure Rule created{Style.RESET_ALL}")
            return rule
        return None
    
    def setup_deployment_tracking_rule(self):
        """Rule to track deployments"""
        print(f"\n{Fore.YELLOW}Creating Deployment Tracking Rule...{Style.RESET_ALL}")
        
        rule_config = {
            "name": "Deployment Status Tracking", 
            "description": "Track deployment status and create deployment issues",
            "trigger": {
                "type": "webhook",
                "webhook": {
                    "name": "GitHub Deployment Status",
                    "url": f"{self.base_url}/secure/webhooks/github-deployment"
                }
            },
            "conditions": [
                {
                    "type": "condition_compare_text",
                    "configuration": {
                        "value": "{{webhookData.deployment_status.state}}",
                        "comparator": "EQUALS",
                        "expected": "success"
                    }
                }
            ],
            "actions": [
                {
                    "type": "action_create_issue",
                    "configuration": {
                        "issueType": "Task",
                        "summary": "Production Deployment - {{webhookData.deployment.sha}}",
                        "description": "🚀 **Deployment Successful**\\n\\n**Environment:** {{webhookData.deployment.environment}}\\n**Commit:** {{webhookData.deployment.sha}}\\n**URL:** {{webhookData.deployment_status.target_url}}\\n\\n**Post-Deployment Checklist:**\\n- [ ] Health checks passing\\n- [ ] Metrics baseline established\\n- [ ] No error alerts triggered\\n- [ ] User acceptance testing completed",
                        "components": ["Infrastructure"],
                        "labels": ["deployment", "automated"]
                    }
                }
            ],
            "scope": {
                "type": "project",
                "projectId": self.get_project_id()
            }
        }
        
        rule = self.create_automation_rule(rule_config)
        if rule:
            print(f"{Fore.GREEN}  ✅ Deployment Tracking Rule created{Style.RESET_ALL}")
            return rule
        return None
    
    def setup_sla_monitoring_rule(self):
        """Rule to monitor SLA and escalate overdue issues"""
        print(f"\n{Fore.YELLOW}Creating SLA Monitoring Rule...{Style.RESET_ALL}")
        
        rule_config = {
            "name": "SLA Monitoring and Escalation",
            "description": "Monitor issue SLA and escalate overdue items",
            "trigger": {
                "type": "scheduled",
                "schedule": {
                    "type": "daily",
                    "hour": 9,
                    "minute": 0
                }
            },
            "conditions": [
                {
                    "type": "condition_jql",
                    "configuration": {
                        "jql": f"project = {self.project_key} AND status != Done AND created < -3d AND priority in (High, Critical)"
                    }
                }
            ],
            "actions": [
                {
                    "type": "action_add_comment",
                    "configuration": {
                        "comment": "⚠️ **SLA Alert**: This high priority issue has been open for more than 3 days. Please review and update status or escalate as needed."
                    }
                },
                {
                    "type": "action_add_label",
                    "configuration": {
                        "labels": ["sla-breach", "needs-attention"]
                    }
                }
            ],
            "scope": {
                "type": "project",
                "projectId": self.get_project_id()
            }
        }
        
        rule = self.create_automation_rule(rule_config)
        if rule:
            print(f"{Fore.GREEN}  ✅ SLA Monitoring Rule created{Style.RESET_ALL}")
            return rule
        return None
    
    def setup_sprint_health_rule(self):
        """Rule to monitor sprint health"""
        print(f"\n{Fore.YELLOW}Creating Sprint Health Monitoring Rule...{Style.RESET_ALL}")
        
        rule_config = {
            "name": "Sprint Health Monitor",
            "description": "Monitor sprint progress and alert on blocked items",
            "trigger": {
                "type": "scheduled", 
                "schedule": {
                    "type": "weekly",
                    "dayOfWeek": "MONDAY",
                    "hour": 10,
                    "minute": 0
                }
            },
            "conditions": [
                {
                    "type": "condition_jql",
                    "configuration": {
                        "jql": f"project = {self.project_key} AND sprint in openSprints() AND status = Blocked"
                    }
                }
            ],
            "actions": [
                {
                    "type": "action_create_issue",
                    "configuration": {
                        "issueType": "Task",
                        "summary": "Sprint Health Alert - Blocked Items Review",
                        "description": "📊 **Sprint Health Alert**\\n\\nThere are blocked items in the current sprint that need attention:\\n\\n{{#issues}}\\n- {{key}}: {{summary}} ({{status}})\\n{{/issues}}\\n\\n**Action Required:**\\n- Review blocked items\\n- Identify and remove blockers\\n- Update sprint scope if necessary",
                        "priority": "Medium",
                        "labels": ["sprint-health", "automated", "review-needed"]
                    }
                }
            ],
            "scope": {
                "type": "project", 
                "projectId": self.get_project_id()
            }
        }
        
        rule = self.create_automation_rule(rule_config)
        if rule:
            print(f"{Fore.GREEN}  ✅ Sprint Health Monitor Rule created{Style.RESET_ALL}")
            return rule
        return None
    
    def setup_security_alert_rule(self):
        """Rule to handle security vulnerability alerts"""
        print(f"\n{Fore.YELLOW}Creating Security Alert Rule...{Style.RESET_ALL}")
        
        rule_config = {
            "name": "Security Vulnerability Alert",
            "description": "Create high priority issues for security vulnerabilities",
            "trigger": {
                "type": "webhook",
                "webhook": {
                    "name": "GitHub Security Alert",
                    "url": f"{self.base_url}/secure/webhooks/github-security"
                }
            },
            "conditions": [
                {
                    "type": "condition_compare_text",
                    "configuration": {
                        "value": "{{webhookData.alert.severity}}",
                        "comparator": "IN",
                        "expected": "critical,high"
                    }
                }
            ],
            "actions": [
                {
                    "type": "action_create_issue",
                    "configuration": {
                        "issueType": "Bug",
                        "summary": "🚨 Security Alert: {{webhookData.alert.title}}",
                        "description": "🔒 **Security Vulnerability Detected**\\n\\n**Severity:** {{webhookData.alert.severity}}\\n**Package:** {{webhookData.alert.package}}\\n**Vulnerability:** {{webhookData.alert.title}}\\n**Description:** {{webhookData.alert.description}}\\n\\n**Action Required:**\\n- Review vulnerability details\\n- Update affected dependencies\\n- Test security fix\\n- Deploy patch immediately",
                        "priority": "Critical",
                        "components": ["Security"],
                        "labels": ["security", "vulnerability", "urgent"]
                    }
                }
            ],
            "scope": {
                "type": "project",
                "projectId": self.get_project_id()
            }
        }
        
        rule = self.create_automation_rule(rule_config)
        if rule:
            print(f"{Fore.GREEN}  ✅ Security Alert Rule created{Style.RESET_ALL}")
            return rule
        return None
    
    def create_webhook_endpoints(self):
        """Create webhook endpoints configuration"""
        print(f"\n{Fore.YELLOW}Creating webhook endpoint configurations...{Style.RESET_ALL}")
        
        webhook_configs = [
            {
                "name": "GitHub PR Events",
                "url": f"{self.base_url}/rest/webhooks/1.0/webhook/jira",
                "events": ["pull_request.opened", "pull_request.closed", "pull_request.synchronize"],
                "description": "Handle GitHub Pull Request events"
            },
            {
                "name": "GitHub Actions Status",
                "url": f"{self.base_url}/rest/webhooks/1.0/webhook/jira",
                "events": ["workflow_run.completed"],
                "description": "Handle GitHub Actions workflow completion events"
            },
            {
                "name": "GitHub Deployment Status",
                "url": f"{self.base_url}/rest/webhooks/1.0/webhook/jira", 
                "events": ["deployment_status"],
                "description": "Handle GitHub deployment status events"
            },
            {
                "name": "GitHub Security Alert",
                "url": f"{self.base_url}/rest/webhooks/1.0/webhook/jira",
                "events": ["security_advisory.published"],
                "description": "Handle GitHub security advisory events"
            }
        ]
        
        webhook_table = []
        for webhook in webhook_configs:
            webhook_table.append([
                webhook["name"],
                ", ".join(webhook["events"]),
                webhook["url"]
            ])
        
        print(f"{Fore.CYAN}🔗 Webhook Endpoints to Configure:{Style.RESET_ALL}")
        print(tabulate(webhook_table, headers=["Name", "Events", "URL"], tablefmt="grid"))
        
        return webhook_configs
    
    def save_automation_templates(self, templates):
        """Save automation rule templates to JSON file"""
        output_file = "/Users/kolb/Documents/github/k8s-news-engine/scripts/jira-setup/automation_rule_templates.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(templates, f, indent=2)
            
            print(f"{Fore.GREEN}✅ Automation templates saved to: {output_file}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving templates: {str(e)}{Style.RESET_ALL}")
            return False
    
    def run_automation_setup(self):
        """Run the complete automation setup"""
        try:
            print(f"\n{Fore.CYAN}🎯 Setting up automation rules for DevOps workflow integration{Style.RESET_ALL}")
            
            # First inspect the Jira configuration
            self.inspect_jira_config()
            
            created_templates = []
            all_templates = {}
            
            # Create automation rule templates
            rules_to_create = [
                ("PR Integration", self.setup_pr_integration_rule),
                ("Build Failure Handling", self.setup_build_failure_rule),
                ("Deployment Tracking", self.setup_deployment_tracking_rule),
                ("SLA Monitoring", self.setup_sla_monitoring_rule),
                ("Sprint Health", self.setup_sprint_health_rule),
                ("Security Alerts", self.setup_security_alert_rule)
            ]
            
            for rule_name, rule_function in rules_to_create:
                try:
                    template = rule_function()
                    if template:
                        created_templates.append([rule_name, "✅ Template Created", "Manual Setup Required"])
                        all_templates[rule_name.lower().replace(' ', '_')] = template
                    else:
                        created_templates.append([rule_name, "❌ Failed", "N/A"])
                except Exception as e:
                    created_templates.append([rule_name, f"❌ Error: {str(e)[:50]}", "N/A"])
            
            # Save templates to file
            self.save_automation_templates(all_templates)
            
            # Create webhook configurations
            webhook_configs = self.create_webhook_endpoints()
            
            print(f"\n{Fore.CYAN}📋 Automation Rule Templates Summary:{Style.RESET_ALL}")
            print(tabulate(created_templates, headers=["Rule Name", "Status", "Next Steps"], tablefmt="grid"))
            
            print(f"\n{Fore.GREEN}🎉 Automation template generation completed!{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}📋 Implementation Steps:{Style.RESET_ALL}")
            print("1. Review automation_rule_templates.json for detailed configurations")
            print("2. Go to your Jira project > Project Settings > Automation")
            print("3. Create each rule manually using the provided templates")
            print("4. Configure GitHub webhooks using script 4_github_integration.py")
            print("5. Test automation rules with sample GitHub events")
            
            print(f"\n{Fore.CYAN}🔧 Default Jira Configuration Compatibility:{Style.RESET_ALL}")
            print("✅ Uses standard issue types (Epic, Story, Task, Bug)")
            print("✅ Compatible with default workflows and transitions")
            print("✅ Leverages standard priorities and statuses")
            print("✅ Uses webhook triggers (no custom field dependencies)")
            print("✅ Templates include manual configuration steps")
            
            print(f"\n{Fore.YELLOW}⚠️  Manual Configuration Required:{Style.RESET_ALL}")
            print("1. Jira automation rules require manual setup in the UI")
            print("2. Webhook URLs need to be configured in GitHub settings") 
            print("3. Test webhook delivery before enabling automation")
            print("4. Adjust rule conditions based on your specific workflow")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Automation setup failed: {str(e)}{Style.RESET_ALL}")
            return False

if __name__ == "__main__":
    try:
        automation = JiraAutomationSetup()
        automation.run_automation_setup()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Automation setup interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")