#!/usr/bin/env python3
"""
Inspect Default Jira Configuration
This script examines your Jira instance to understand the default configuration
before creating custom automation rules and workflows.
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

class JiraConfigInspector:
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
        
        print(f"{Fore.CYAN}🔍 Inspecting Jira Configuration{Style.RESET_ALL}")
        print(f"Base URL: {self.base_url}")
        print(f"Target Project: {self.project_key}")
    
    def test_connection(self):
        """Test Jira API connection and get user info"""
        print(f"\n{Fore.YELLOW}Testing Jira connection...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/myself",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"{Fore.GREEN}✅ Connected successfully{Style.RESET_ALL}")
                
                user_table = [
                    ["Display Name", user_info.get('displayName', 'N/A')],
                    ["Email", user_info.get('emailAddress', 'N/A')],
                    ["Account ID", user_info.get('accountId', 'N/A')],
                    ["Account Type", user_info.get('accountType', 'N/A')],
                    ["Active", user_info.get('active', 'N/A')]
                ]
                
                print(f"\n{Fore.CYAN}👤 User Information:{Style.RESET_ALL}")
                print(tabulate(user_table, headers=["Property", "Value"], tablefmt="grid"))
                return True
            else:
                print(f"{Fore.RED}❌ Connection failed: {response.status_code} - {response.text}{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Connection error: {str(e)}{Style.RESET_ALL}")
            return False
    
    def inspect_issue_types(self):
        """Inspect available issue types"""
        print(f"\n{Fore.YELLOW}Inspecting available issue types...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/issuetype",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                issue_types = response.json()
                
                issue_type_table = []
                for issue_type in issue_types:
                    issue_type_table.append([
                        issue_type.get('name', 'N/A'),
                        issue_type.get('id', 'N/A'),
                        issue_type.get('description', 'N/A')[:50] + "..." if len(issue_type.get('description', '')) > 50 else issue_type.get('description', 'N/A'),
                        "✅" if not issue_type.get('subtask', False) else "📋 Sub-task"
                    ])
                
                print(f"{Fore.CYAN}📝 Available Issue Types:{Style.RESET_ALL}")
                print(tabulate(issue_type_table, headers=["Name", "ID", "Description", "Type"], tablefmt="grid"))
                
                return {it['name']: it['id'] for it in issue_types}
            else:
                print(f"{Fore.RED}❌ Failed to get issue types: {response.status_code}{Style.RESET_ALL}")
                return {}
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error getting issue types: {str(e)}{Style.RESET_ALL}")
            return {}
    
    def inspect_project_config(self):
        """Inspect project configuration if it exists"""
        print(f"\n{Fore.YELLOW}Inspecting project configuration...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{self.project_key}",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                project = response.json()
                
                project_table = [
                    ["Project Key", project.get('key', 'N/A')],
                    ["Project Name", project.get('name', 'N/A')],
                    ["Project ID", project.get('id', 'N/A')],
                    ["Project Type", project.get('projectTypeKey', 'N/A')],
                    ["Lead", project.get('lead', {}).get('displayName', 'N/A')],
                    ["Description", (project.get('description', 'N/A')[:50] + "...") if len(project.get('description', '')) > 50 else project.get('description', 'N/A')]
                ]
                
                print(f"{Fore.GREEN}✅ Project exists: {project.get('key')}{Style.RESET_ALL}")
                print(f"\n{Fore.CYAN}📊 Project Configuration:{Style.RESET_ALL}")
                print(tabulate(project_table, headers=["Property", "Value"], tablefmt="grid"))
                
                # Get project components if they exist
                self.inspect_project_components()
                
                # Get project issue types
                self.inspect_project_issue_types()
                
                return project
            else:
                print(f"{Fore.YELLOW}⚠️ Project {self.project_key} does not exist yet{Style.RESET_ALL}")
                return None
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error inspecting project: {str(e)}{Style.RESET_ALL}")
            return None
    
    def inspect_project_components(self):
        """Inspect project components"""
        print(f"\n{Fore.YELLOW}Inspecting project components...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{self.project_key}/components",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                components = response.json()
                
                if components:
                    component_table = []
                    for component in components:
                        component_table.append([
                            component.get('name', 'N/A'),
                            component.get('id', 'N/A'),
                            component.get('description', 'N/A')[:50] + "..." if len(component.get('description', '')) > 50 else component.get('description', 'N/A')
                        ])
                    
                    print(f"{Fore.CYAN}🧩 Project Components:{Style.RESET_ALL}")
                    print(tabulate(component_table, headers=["Name", "ID", "Description"], tablefmt="grid"))
                else:
                    print(f"{Fore.YELLOW}⚠️ No components configured{Style.RESET_ALL}")
                
                return components
            else:
                print(f"{Fore.YELLOW}⚠️ Could not get components: {response.status_code}{Style.RESET_ALL}")
                return []
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error getting components: {str(e)}{Style.RESET_ALL}")
            return []
    
    def inspect_project_issue_types(self):
        """Inspect project-specific issue types"""
        print(f"\n{Fore.YELLOW}Inspecting project issue types and workflows...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{self.project_key}",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                project = response.json()
                issue_types = project.get('issueTypes', [])
                
                if issue_types:
                    issue_type_table = []
                    for issue_type in issue_types:
                        issue_type_table.append([
                            issue_type.get('name', 'N/A'),
                            issue_type.get('id', 'N/A'),
                            "✅" if not issue_type.get('subtask', False) else "📋 Sub-task"
                        ])
                    
                    print(f"{Fore.CYAN}📝 Project Issue Types:{Style.RESET_ALL}")
                    print(tabulate(issue_type_table, headers=["Name", "ID", "Type"], tablefmt="grid"))
                
                return issue_types
            else:
                return []
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error getting project issue types: {str(e)}{Style.RESET_ALL}")
            return []
    
    def inspect_workflows(self):
        """Inspect available workflows"""
        print(f"\n{Fore.YELLOW}Inspecting available workflows...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/workflow/search",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                workflows = result.get('values', [])
                
                if workflows:
                    workflow_table = []
                    for workflow in workflows[:10]:  # Limit to first 10 workflows
                        workflow_table.append([
                            workflow.get('id', {}).get('name', 'N/A'),
                            workflow.get('id', {}).get('entityId', 'N/A'),
                            workflow.get('description', 'N/A')[:50] + "..." if len(workflow.get('description', '')) > 50 else workflow.get('description', 'N/A')
                        ])
                    
                    print(f"{Fore.CYAN}⚙️ Available Workflows (first 10):{Style.RESET_ALL}")
                    print(tabulate(workflow_table, headers=["Name", "ID", "Description"], tablefmt="grid"))
                else:
                    print(f"{Fore.YELLOW}⚠️ No workflows found{Style.RESET_ALL}")
                
                return workflows
            else:
                print(f"{Fore.YELLOW}⚠️ Could not get workflows: {response.status_code}{Style.RESET_ALL}")
                return []
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error getting workflows: {str(e)}{Style.RESET_ALL}")
            return []
    
    def inspect_custom_fields(self):
        """Inspect available custom fields"""
        print(f"\n{Fore.YELLOW}Inspecting custom fields...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/field",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                fields = response.json()
                
                # Filter for custom fields (they usually start with 'customfield_')
                custom_fields = [f for f in fields if f.get('id', '').startswith('customfield_')]
                system_fields = [f for f in fields if not f.get('id', '').startswith('customfield_')]
                
                if custom_fields:
                    custom_field_table = []
                    for field in custom_fields[:10]:  # Show first 10 custom fields
                        custom_field_table.append([
                            field.get('name', 'N/A'),
                            field.get('id', 'N/A'),
                            field.get('schema', {}).get('type', 'N/A')
                        ])
                    
                    print(f"{Fore.CYAN}🔧 Custom Fields (first 10):{Style.RESET_ALL}")
                    print(tabulate(custom_field_table, headers=["Name", "ID", "Type"], tablefmt="grid"))
                else:
                    print(f"{Fore.YELLOW}⚠️ No custom fields found{Style.RESET_ALL}")
                
                # Show some important system fields
                important_fields = ['Epic Link', 'Story Points', 'Sprint']
                important_field_table = []
                
                for field in system_fields:
                    if field.get('name') in important_fields:
                        important_field_table.append([
                            field.get('name', 'N/A'),
                            field.get('id', 'N/A'),
                            field.get('schema', {}).get('type', 'N/A')
                        ])
                
                if important_field_table:
                    print(f"\n{Fore.CYAN}⭐ Important System Fields:{Style.RESET_ALL}")
                    print(tabulate(important_field_table, headers=["Name", "ID", "Type"], tablefmt="grid"))
                
                return {'custom': custom_fields, 'system': system_fields}
            else:
                print(f"{Fore.YELLOW}⚠️ Could not get fields: {response.status_code}{Style.RESET_ALL}")
                return {'custom': [], 'system': []}
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error getting fields: {str(e)}{Style.RESET_ALL}")
            return {'custom': [], 'system': []}
    
    def inspect_priorities_and_statuses(self):
        """Inspect available priorities and statuses"""
        print(f"\n{Fore.YELLOW}Inspecting priorities and statuses...{Style.RESET_ALL}")
        
        # Get priorities
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/priority",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                priorities = response.json()
                
                priority_table = []
                for priority in priorities:
                    priority_table.append([
                        priority.get('name', 'N/A'),
                        priority.get('id', 'N/A'),
                        priority.get('description', 'N/A')[:30] + "..." if len(priority.get('description', '')) > 30 else priority.get('description', 'N/A')
                    ])
                
                print(f"{Fore.CYAN}🎯 Available Priorities:{Style.RESET_ALL}")
                print(tabulate(priority_table, headers=["Name", "ID", "Description"], tablefmt="grid"))
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error getting priorities: {str(e)}{Style.RESET_ALL}")
        
        # Get statuses
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/status",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                statuses = response.json()
                
                status_table = []
                for status in statuses[:15]:  # Show first 15 statuses
                    status_table.append([
                        status.get('name', 'N/A'),
                        status.get('id', 'N/A'),
                        status.get('statusCategory', {}).get('name', 'N/A')
                    ])
                
                print(f"\n{Fore.CYAN}📊 Available Statuses (first 15):{Style.RESET_ALL}")
                print(tabulate(status_table, headers=["Name", "ID", "Category"], tablefmt="grid"))
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error getting statuses: {str(e)}{Style.RESET_ALL}")
    
    def generate_recommendations(self):
        """Generate recommendations based on inspection"""
        print(f"\n{Fore.CYAN}💡 Configuration Recommendations:{Style.RESET_ALL}")
        
        recommendations = [
            "✅ Use standard issue types (Epic, Story, Task, Bug) for DevOps workflow",
            "✅ Create components for each service (Analytics, Publisher, Database, etc.)",
            "✅ Use existing priority levels (High, Medium, Low) for story prioritization", 
            "✅ Leverage default workflow states with custom automation rules",
            "✅ Add GitHub-specific custom fields (PR Number, Branch Name)",
            "✅ Configure automation rules using webhook triggers",
            "✅ Use labels for automated categorization (ci-cd, deployment, security)",
            "✅ Set up scheduled rules for SLA monitoring and sprint health"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
        
        print(f"\n{Fore.YELLOW}⚠️  Configuration Notes:{Style.RESET_ALL}")
        notes = [
            "📝 Custom field IDs vary between Jira instances (will auto-detect)",
            "📝 Automation rules require Jira Cloud Premium or higher",
            "📝 Webhook URLs must be accessible from GitHub",
            "📝 Epic Link field may have different ID in your instance"
        ]
        
        for note in notes:
            print(f"  {note}")
    
    def save_config_report(self):
        """Save configuration report to file"""
        print(f"\n{Fore.YELLOW}Saving configuration report...{Style.RESET_ALL}")
        
        config_data = {
            "jira_base_url": self.base_url,
            "project_key": self.project_key,
            "inspection_timestamp": "2025-09-08",
            "recommendations": [
                "Use detected issue types and workflows",
                "Create automation rules compatible with default setup",
                "Configure GitHub webhooks with detected field IDs"
            ]
        }
        
        report_path = "/Users/kolb/Documents/github/k8s-news-engine/scripts/jira-setup/jira_config_report.json"
        
        try:
            with open(report_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"{Fore.GREEN}✅ Configuration report saved to: {report_path}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving report: {str(e)}{Style.RESET_ALL}")
    
    def run_inspection(self):
        """Run the complete inspection process"""
        try:
            # Test connection
            if not self.test_connection():
                return False
            
            # Inspect various configurations
            self.inspect_issue_types()
            self.inspect_project_config()
            self.inspect_workflows()
            self.inspect_custom_fields()
            self.inspect_priorities_and_statuses()
            
            # Generate recommendations
            self.generate_recommendations()
            
            # Save report
            self.save_config_report()
            
            print(f"\n{Fore.GREEN}🎉 Configuration inspection completed!{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}📋 Next Steps:{Style.RESET_ALL}")
            print("1. Review the configuration findings above")
            print("2. Run 1_setup_jira_project.py if project doesn't exist")
            print("3. Run 2_create_epic_and_stories.py to create issues")
            print("4. Run 3_setup_automation_rules.py with detected configuration")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Inspection failed: {str(e)}{Style.RESET_ALL}")
            return False

if __name__ == "__main__":
    try:
        inspector = JiraConfigInspector()
        inspector.run_inspection()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Inspection interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")