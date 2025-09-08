#!/usr/bin/env python3
"""
Jira Project Setup Script for K8s News Engine
Creates the Jira project, components, and custom fields
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

class JiraProjectSetup:
    def __init__(self):
        self.base_url = os.getenv('JIRA_BASE_URL')
        self.email = os.getenv('JIRA_USER_EMAIL') 
        self.api_token = os.getenv('JIRA_API_TOKEN')
        self.project_key = os.getenv('PROJECT_KEY', 'K8SNE')
        self.project_name = os.getenv('PROJECT_NAME', 'K8s News Engine')
        self.project_lead = os.getenv('PROJECT_LEAD_EMAIL')
        
        if not all([self.base_url, self.email, self.api_token, self.project_lead]):
            raise ValueError("Missing required environment variables. Check .env file.")
            
        self.auth = (self.email, self.api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        print(f"{Fore.CYAN}🚀 Jira Project Setup for {self.project_name}{Style.RESET_ALL}")
        print(f"Base URL: {self.base_url}")
        print(f"Project Key: {self.project_key}")
        
    def test_connection(self):
        """Test Jira API connection"""
        print(f"\n{Fore.YELLOW}Testing Jira connection...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/myself",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"{Fore.GREEN}✅ Connected as: {user_info.get('displayName')}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ Connection failed: {response.status_code} - {response.text}{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Connection error: {str(e)}{Style.RESET_ALL}")
            return False
    
    def get_project_template(self):
        """Get available project templates"""
        print(f"\n{Fore.YELLOW}Getting project templates...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/template",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                templates = response.json()
                for template in templates:
                    if 'software' in template.get('name', '').lower():
                        print(f"{Fore.GREEN}✅ Found software template: {template.get('name')}{Style.RESET_ALL}")
                        return template.get('projectTemplateKey')
                        
            print(f"{Fore.YELLOW}⚠️ Using default template{Style.RESET_ALL}")
            return "com.pyxis.greenhopper.jira:gh-scrum-template"
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error getting templates: {str(e)}{Style.RESET_ALL}")
            return "com.pyxis.greenhopper.jira:gh-scrum-template"
    
    def create_project(self):
        """Create the Jira project"""
        print(f"\n{Fore.YELLOW}Creating Jira project...{Style.RESET_ALL}")
        
        # Check if project already exists
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{self.project_key}",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                print(f"{Fore.YELLOW}⚠️ Project {self.project_key} already exists{Style.RESET_ALL}")
                return response.json()
                
        except:
            pass
        
        template_key = self.get_project_template()
        
        project_data = {
            "key": self.project_key,
            "name": self.project_name,
            "projectTypeKey": "software",
            "projectTemplateKey": template_key,
            "description": "DevOps Platform Modernization for K8s News Engine - A microservices-based news verification and truth analysis system",
            "leadAccountId": None,  # Will be set after getting user account ID
            "assigneeType": "PROJECT_LEAD",
            "avatarId": 10324  # Default project avatar
        }
        
        # Get current user account ID for project lead
        user_response = requests.get(
            f"{self.base_url}/rest/api/3/myself",
            auth=self.auth,
            headers=self.headers
        )
        
        if user_response.status_code == 200:
            project_data["leadAccountId"] = user_response.json().get("accountId")
        
        try:
            response = requests.post(
                f"{self.base_url}/rest/api/3/project",
                auth=self.auth,
                headers=self.headers,
                json=project_data
            )
            
            if response.status_code == 201:
                project = response.json()
                print(f"{Fore.GREEN}✅ Project created successfully!{Style.RESET_ALL}")
                print(f"   Project ID: {project.get('id')}")
                print(f"   Project URL: {project.get('self')}")
                return project
            else:
                print(f"{Fore.RED}❌ Failed to create project: {response.status_code}{Style.RESET_ALL}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error creating project: {str(e)}{Style.RESET_ALL}")
            return None
    
    def create_components(self, project_id):
        """Create project components"""
        print(f"\n{Fore.YELLOW}Creating project components...{Style.RESET_ALL}")
        
        components = [
            {
                "name": "Analytics Service",
                "description": "Python-based analytics service computing EQIS scores"
            },
            {
                "name": "Publisher Service", 
                "description": "Lighttpd-based content delivery service"
            },
            {
                "name": "Database",
                "description": "PostgreSQL database and schema management"
            },
            {
                "name": "Infrastructure",
                "description": "Kubernetes manifests and infrastructure as code"
            },
            {
                "name": "CI/CD",
                "description": "GitHub Actions workflows and deployment automation"
            },
            {
                "name": "Monitoring",
                "description": "Prometheus, Grafana, and observability stack"
            },
            {
                "name": "Security",
                "description": "Security scanning, RBAC, and compliance"
            }
        ]
        
        created_components = []
        
        for component in components:
            component_data = {
                "name": component["name"],
                "description": component["description"],
                "project": self.project_key,
                "assigneeType": "PROJECT_DEFAULT"
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/rest/api/3/component",
                    auth=self.auth,
                    headers=self.headers,
                    json=component_data
                )
                
                if response.status_code == 201:
                    comp = response.json()
                    created_components.append([comp["name"], comp["id"]])
                    print(f"{Fore.GREEN}  ✅ {comp['name']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}  ❌ Failed to create {component['name']}: {response.status_code}{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.RED}  ❌ Error creating {component['name']}: {str(e)}{Style.RESET_ALL}")
        
        if created_components:
            print(f"\n{Fore.CYAN}📋 Created Components:{Style.RESET_ALL}")
            print(tabulate(created_components, headers=["Component", "ID"], tablefmt="grid"))
        
        return created_components
    
    def create_custom_fields(self):
        """Create custom fields for GitHub integration"""
        print(f"\n{Fore.YELLOW}Creating custom fields...{Style.RESET_ALL}")
        
        custom_fields = [
            {
                "name": "GitHub PR Number",
                "description": "GitHub Pull Request number for tracking",
                "type": "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
                "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:textsearcher"
            },
            {
                "name": "GitHub Branch",
                "description": "GitHub branch name associated with the issue",
                "type": "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
                "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:textsearcher"
            },
            {
                "name": "Deployment Environment",
                "description": "Target deployment environment (staging/production)",
                "type": "com.atlassian.jira.plugin.system.customfieldtypes:select",
                "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:multiselectsearcher"
            },
            {
                "name": "Service Impact",
                "description": "Which services are impacted by this change",
                "type": "com.atlassian.jira.plugin.system.customfieldtypes:multiselect",
                "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:multiselectsearcher"
            }
        ]
        
        created_fields = []
        
        for field in custom_fields:
            field_data = {
                "name": field["name"],
                "description": field["description"],
                "type": field["type"],
                "searcherKey": field["searcherKey"]
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/rest/api/3/field",
                    auth=self.auth,
                    headers=self.headers,
                    json=field_data
                )
                
                if response.status_code == 201:
                    custom_field = response.json()
                    created_fields.append([custom_field["name"], custom_field["id"]])
                    print(f"{Fore.GREEN}  ✅ {custom_field['name']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}  ❌ Failed to create {field['name']}: {response.status_code}{Style.RESET_ALL}")
                    if response.status_code == 400:
                        print(f"     Response: {response.text}")
                    
            except Exception as e:
                print(f"{Fore.RED}  ❌ Error creating {field['name']}: {str(e)}{Style.RESET_ALL}")
        
        if created_fields:
            print(f"\n{Fore.CYAN}🔧 Created Custom Fields:{Style.RESET_ALL}")
            print(tabulate(created_fields, headers=["Field Name", "Field ID"], tablefmt="grid"))
        
        return created_fields
    
    def setup_project_permissions(self):
        """Set up project permissions"""
        print(f"\n{Fore.YELLOW}Setting up project permissions...{Style.RESET_ALL}")
        
        # Get default permission scheme
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/permissionscheme",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                schemes = response.json()
                if schemes.get('permissionSchemes'):
                    default_scheme = schemes['permissionSchemes'][0]
                    print(f"{Fore.GREEN}✅ Using permission scheme: {default_scheme.get('name')}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Could not configure permissions: {str(e)}{Style.RESET_ALL}")
    
    def run_setup(self):
        """Run the complete setup process"""
        try:
            # Test connection
            if not self.test_connection():
                return False
            
            # Create project
            project = self.create_project()
            if not project:
                return False
                
            project_id = project.get('id')
            
            # Create components
            self.create_components(project_id)
            
            # Create custom fields
            self.create_custom_fields()
            
            # Setup permissions
            self.setup_project_permissions()
            
            print(f"\n{Fore.GREEN}🎉 Jira project setup completed successfully!{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}📋 Next Steps:{Style.RESET_ALL}")
            print("1. Run script 2_create_epic_and_stories.py to create EPIC and user stories")
            print("2. Run script 3_setup_automation_rules.py to configure automation")
            print("3. Configure GitHub webhooks with script 4_github_integration.py")
            print(f"\n{Fore.CYAN}🔗 Project URL: {self.base_url}/projects/{self.project_key}{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Setup failed: {str(e)}{Style.RESET_ALL}")
            return False

if __name__ == "__main__":
    try:
        setup = JiraProjectSetup()
        setup.run_setup()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Setup interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")