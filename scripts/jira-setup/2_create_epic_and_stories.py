#!/usr/bin/env python3
"""
Create EPIC and User Stories for K8s News Engine DevOps Modernization
"""

import requests
import json
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init
from tabulate import tabulate
import time

# Initialize colorama for cross-platform colored output
init()

# Load environment variables
load_dotenv('.env.kolbai')

class JiraStoryCreator:
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
        
        self.components_map = {}
        self.epic_id = None
        self.epic_key = None
        
        print(f"{Fore.CYAN}📋 Creating EPIC and User Stories for {self.project_key}{Style.RESET_ALL}")
    
    def get_components(self):
        """Get project components for assignment"""
        print(f"\n{Fore.YELLOW}Getting project components...{Style.RESET_ALL}")
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{self.project_key}/components",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                components = response.json()
                for comp in components:
                    self.components_map[comp['name']] = comp['id']
                    print(f"{Fore.GREEN}  ✅ {comp['name']}: {comp['id']}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ Failed to get components: {response.status_code}{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error getting components: {str(e)}{Style.RESET_ALL}")
            return False
    
    def get_issue_types(self):
        """Get available issue types"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/{self.project_key}",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                project = response.json()
                issue_types = {}
                for issue_type in project.get('issueTypes', []):
                    issue_types[issue_type['name']] = issue_type['id']
                return issue_types
            return {}
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Could not get issue types: {str(e)}{Style.RESET_ALL}")
            return {}
    
    def create_epic(self):
        """Create the main DevOps Modernization EPIC"""
        print(f"\n{Fore.YELLOW}Creating EPIC: K8SNE-1 DevOps Platform Modernization...{Style.RESET_ALL}")
        
        issue_types = self.get_issue_types()
        epic_type_id = issue_types.get('Epic') or issue_types.get('epic') or '10000'
        
        # Use simple text description for better compatibility
        epic_description = "DevOps Platform Modernization for K8s News Engine\n\nObjective: Transform the K8s News Engine into a production-ready, enterprise-grade platform with comprehensive DevOps practices, automated CI/CD pipelines, and robust monitoring capabilities.\n\nSuccess Criteria:\n- Deployment frequency: >10 deployments per day\n- Lead time: <2 hours from commit to production\n- Mean Time to Recovery (MTTR): <30 minutes\n- System uptime: >99.95%\n- Security scan coverage: 100% of containers\n\nImplementation Phases:\n1. Phase 1: CI/CD Foundation (Weeks 1-4)\n2. Phase 2: Security & Secrets Management (Weeks 5-6)\n3. Phase 3: Monitoring & Observability (Weeks 7-10)"
        
        epic_data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": "DevOps Platform Modernization EPIC",
                "issuetype": {"id": epic_type_id},
                "priority": {"name": "High"},
                "labels": ["epic", "devops", "platform", "modernization", "infrastructure"],
                "components": [
                    {"id": self.components_map.get("Infrastructure", "")},
                    {"id": self.components_map.get("CI/CD", "")},
                    {"id": self.components_map.get("Monitoring", "")}
                ]
            }
        }
        
        # Epic Name custom field not available in this instance - skip it
        # The summary field will serve as the epic name
        
        try:
            response = requests.post(
                f"{self.base_url}/rest/api/3/issue",
                auth=self.auth,
                headers=self.headers,
                json=epic_data
            )
            
            if response.status_code == 201:
                epic = response.json()
                self.epic_id = epic['id']
                self.epic_key = epic['key']
                print(f"{Fore.GREEN}✅ EPIC created: {self.epic_key}{Style.RESET_ALL}")
                print(f"   Epic ID: {self.epic_id}")
                return self.epic_key
            else:
                print(f"{Fore.RED}❌ Failed to create EPIC: {response.status_code}{Style.RESET_ALL}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error creating EPIC: {str(e)}{Style.RESET_ALL}")
            return None
    
    def create_user_stories(self):
        """Create all user stories for the EPIC"""
        print(f"\n{Fore.YELLOW}Creating user stories...{Style.RESET_ALL}")
        
        issue_types = self.get_issue_types()
        story_type_id = issue_types.get('Story') or issue_types.get('story') or '10001'
        
        user_stories = [
            {
                "key": "K8SNE-2",
                "summary": "GitHub Actions CI/CD Pipeline Setup",
                "description": "As a DevOps Engineer I want automated CI/CD pipelines using GitHub Actions so that code changes are automatically built, tested, and deployed.\n\nAcceptance Criteria:\n- GitHub Actions workflow triggers on push to main/develop branches\n- Parallel builds for analytics-py and publisher services\n- Container images pushed to GitHub Container Registry\n- Staging deployment on develop branch\n- Production deployment on main branch\n- Integration with Jira for automatic issue tracking\n\nStatus: COMPLETED - GitHub Actions workflows are implemented and working.",
                "components": ["CI/CD", "Analytics Service", "Publisher Service"],
                "story_points": 8,
                "status": "Done",  # Already completed
                "priority": "High"
            },
            {
                "key": "K8SNE-3", 
                "summary": "Automated Testing Implementation",
                "description": "As a Developer I want comprehensive automated testing integrated into CI pipeline so that code quality is maintained and regressions are caught early.\n\nAcceptance Criteria:\n- Unit tests implemented for analytics service using pytest\n- Code coverage reporting with minimum 80% coverage\n- Integration tests for database operations\n- API tests for publisher service endpoints\n- Tests run automatically in CI pipeline\n- PR blocking on test failures\n\nTechnical Tasks:\n- Set up pytest test structure in services/analytics-py/tests/\n- Create unit tests for EQIS calculation functions\n- Configure coverage reporting\n- Update GitHub Actions workflow",
                "components": ["Analytics Service", "CI/CD"],
                "story_points": 13,
                "status": "To Do",
                "priority": "High"
            },
            {
                "key": "K8SNE-4",
                "summary": "Container Security Scanning with Trivy",
                "description": """
**As a** Security Engineer  
**I want** automated vulnerability scanning of container images
**So that** security vulnerabilities are identified and blocked before deployment

### Acceptance Criteria
- [ ] Trivy security scanner integrated into CI pipeline
- [ ] Vulnerability scan runs on every container build
- [ ] Results uploaded to GitHub Security tab
- [ ] Pipeline fails on critical/high severity vulnerabilities
- [ ] Weekly security reports generated
- [ ] Whitelist mechanism for accepted vulnerabilities

### Technical Tasks
- [ ] Add Trivy action to GitHub workflow
- [ ] Configure SARIF output format
- [ ] Set up security policies and thresholds
- [ ] Create vulnerability report templates
- [ ] Implement exemption process for false positives
- [ ] Add security scanning to container registry

### Definition of Done
- [ ] Security scans run automatically
- [ ] Critical vulnerabilities block deployment
- [ ] Reports are accessible in GitHub Security
- [ ] Team has process for handling vulnerabilities
                """,
                "components": ["Security", "CI/CD"],
                "story_points": 8,
                "status": "To Do", 
                "priority": "High"
            },
            {
                "key": "K8SNE-5",
                "summary": "Multi-stage Docker Build Optimization",
                "description": """
**As a** DevOps Engineer
**I want** optimized multi-stage Docker builds  
**So that** container images are smaller, more secure, and build faster

### Acceptance Criteria
- [ ] Multi-stage Dockerfiles for both services
- [ ] Separate build and runtime stages
- [ ] Minimal base images (Alpine/distroless)
- [ ] Build caching implemented
- [ ] Image size reduced by >50%
- [ ] Build time reduced by >30%
- [ ] Non-root user in runtime containers

### Technical Tasks
- [ ] Refactor analytics-py Dockerfile with multi-stage build
- [ ] Refactor publisher Dockerfile with multi-stage build
- [ ] Implement Docker layer caching in GitHub Actions
- [ ] Add .dockerignore files to reduce context size
- [ ] Security hardening of container images
- [ ] Performance benchmarking of build times

### Definition of Done
- [ ] Container images are <100MB each
- [ ] Build times are under 5 minutes
- [ ] Images run as non-root user
- [ ] Layer caching reduces rebuild times
                """,
                "components": ["Analytics Service", "Publisher Service", "CI/CD"],
                "story_points": 5,
                "status": "To Do",
                "priority": "Medium"
            },
            {
                "key": "K8SNE-6",
                "summary": "Code Quality Automation with SonarQube", 
                "description": """
**As a** Development Team Lead
**I want** automated code quality analysis
**So that** code maintainability and technical debt are managed

### Acceptance Criteria
- [ ] SonarQube analysis integrated in CI pipeline
- [ ] Code quality gates enforce standards
- [ ] Technical debt tracking and reporting
- [ ] Security hotspots identification
- [ ] Code coverage integration
- [ ] Quality metrics visible in PRs
- [ ] Historical trend reporting

### Technical Tasks
- [ ] Set up SonarQube Cloud instance
- [ ] Configure sonar-project.properties
- [ ] Add SonarQube analysis to GitHub Actions
- [ ] Define quality gates and rules
- [ ] Integrate with PR decoration
- [ ] Set up team notifications

### Definition of Done
- [ ] Code quality analysis runs on every PR
- [ ] Quality gates prevent merge of poor code
- [ ] Technical debt is tracked and reported
- [ ] Team has access to quality metrics
                """,
                "components": ["CI/CD", "Analytics Service", "Publisher Service"],
                "story_points": 8,
                "status": "To Do",
                "priority": "Medium"
            },
            {
                "key": "K8SNE-7",
                "summary": "Kubernetes Secrets Migration",
                "description": """
**As a** Security Engineer
**I want** all sensitive data managed through Kubernetes secrets
**So that** credentials are not exposed in configuration files

### Acceptance Criteria
- [ ] Database credentials moved to Kubernetes secrets
- [ ] Sealed Secrets or External Secrets Operator implemented
- [ ] No hardcoded credentials in any manifests
- [ ] Secret rotation procedure documented
- [ ] RBAC controls access to secrets
- [ ] Audit logging for secret access

### Technical Tasks
- [ ] Create Kubernetes secret manifests for database
- [ ] Update deployment manifests to use secret refs
- [ ] Install and configure Sealed Secrets controller
- [ ] Migrate API keys and tokens to secrets
- [ ] Implement secret rotation automation
- [ ] Document secret management procedures

### Definition of Done
- [ ] All credentials are stored in secrets
- [ ] Deployments successfully use secret references
- [ ] Secret rotation works automatically
- [ ] Documentation is complete
                """,
                "components": ["Security", "Database", "Infrastructure"],
                "story_points": 8,
                "status": "To Do",
                "priority": "High"
            },
            {
                "key": "K8SNE-8",
                "summary": "RBAC Implementation for Services",
                "description": """
**As a** Kubernetes Administrator  
**I want** proper RBAC policies for all services
**So that** services have minimal required permissions

### Acceptance Criteria
- [ ] ServiceAccounts created for each service
- [ ] Roles defined with minimal permissions
- [ ] RoleBindings configured correctly
- [ ] Network policies restrict pod communication
- [ ] Pod security policies implemented
- [ ] RBAC testing and validation

### Technical Tasks
- [ ] Create ServiceAccount for analytics service
- [ ] Create ServiceAccount for publisher service  
- [ ] Define Role for database access permissions
- [ ] Create RoleBindings for service accounts
- [ ] Implement NetworkPolicy resources
- [ ] Add PodSecurityPolicy or Pod Security Standards

### Definition of Done
- [ ] Services run with dedicated ServiceAccounts
- [ ] Permissions are minimal and functional
- [ ] Network traffic is properly restricted
- [ ] Security policies are enforced
                """,
                "components": ["Security", "Infrastructure"],
                "story_points": 5,
                "status": "To Do",
                "priority": "High"
            },
            {
                "key": "K8SNE-9",
                "summary": "Network Policies Configuration",
                "description": """
**As a** Security Engineer
**I want** network segmentation through Kubernetes network policies
**So that** inter-pod communication is controlled and secure

### Acceptance Criteria  
- [ ] Default deny-all network policy implemented
- [ ] Analytics service can access database only
- [ ] Publisher service has controlled ingress access
- [ ] Database access is restricted to authorized pods
- [ ] Monitoring tools have necessary access
- [ ] Network policy testing validates rules

### Technical Tasks
- [ ] Create default deny NetworkPolicy
- [ ] Define analytics-to-database communication policy
- [ ] Configure publisher ingress network policy
- [ ] Set up monitoring namespace access policies
- [ ] Implement egress controls for external services
- [ ] Test network connectivity after policy application

### Definition of Done
- [ ] All inter-pod communication is controlled
- [ ] Services can only access required resources
- [ ] External traffic is properly filtered
- [ ] Policies are tested and validated
                """,
                "components": ["Security", "Infrastructure"],
                "story_points": 5,
                "status": "To Do", 
                "priority": "Medium"
            },
            {
                "key": "K8SNE-11",
                "summary": "Prometheus + Grafana Monitoring Stack",
                "description": """
**As a** Site Reliability Engineer
**I want** comprehensive monitoring with Prometheus and Grafana
**So that** system health and performance are observable

### Acceptance Criteria
- [ ] Prometheus deployed with persistent storage
- [ ] Grafana deployed with dashboards for all services
- [ ] ServiceMonitor configurations for metrics collection
- [ ] Node exporter for infrastructure metrics
- [ ] Application metrics exposed by services
- [ ] Custom dashboards for business metrics
- [ ] AlertManager configured for notifications

### Technical Tasks
- [ ] Deploy Prometheus operator or helm chart
- [ ] Configure Grafana with persistent storage
- [ ] Create ServiceMonitor for analytics service
- [ ] Create ServiceMonitor for publisher service
- [ ] Set up PostgreSQL metrics exporter
- [ ] Build custom Grafana dashboards
- [ ] Configure AlertManager rules

### Definition of Done
- [ ] All services are monitored
- [ ] Dashboards show relevant metrics
- [ ] Alerts fire for critical conditions
- [ ] Historical data is preserved
                """,
                "components": ["Monitoring", "Infrastructure"],
                "story_points": 13,
                "status": "To Do",
                "priority": "High"
            },
            {
                "key": "K8SNE-12",
                "summary": "Distributed Tracing with Jaeger",
                "description": """
**As a** Developer
**I want** distributed tracing across all services
**So that** request flows and performance bottlenecks are visible

### Acceptance Criteria
- [ ] Jaeger deployed in Kubernetes cluster
- [ ] Analytics service instrumented with tracing
- [ ] Publisher service instrumented with tracing
- [ ] Database operations traced
- [ ] Custom spans for business logic
- [ ] Trace correlation across service boundaries
- [ ] Performance analysis capabilities

### Technical Tasks
- [ ] Deploy Jaeger operator
- [ ] Add OpenTelemetry instrumentation to analytics service
- [ ] Add tracing to publisher service
- [ ] Instrument database queries
- [ ] Configure trace sampling rates
- [ ] Set up trace retention policies
- [ ] Create tracing documentation

### Definition of Done
- [ ] End-to-end traces are visible
- [ ] Performance bottlenecks can be identified
- [ ] Traces correlate across services
- [ ] Team can effectively use tracing data
                """,
                "components": ["Monitoring", "Analytics Service", "Publisher Service"],
                "story_points": 8,
                "status": "To Do",
                "priority": "Medium"
            },
            {
                "key": "K8SNE-13",
                "summary": "Comprehensive Alerting Rules Configuration",
                "description": """
**As a** Operations Team
**I want** intelligent alerting for all critical conditions
**So that** issues are detected and resolved quickly

### Acceptance Criteria
- [ ] Critical system alerts (CPU, memory, disk)
- [ ] Application-specific alerts (EQIS processing failures)
- [ ] Database health and performance alerts
- [ ] CI/CD pipeline failure alerts
- [ ] Security incident alerts
- [ ] SLA-based alerting rules
- [ ] Alert routing and escalation

### Technical Tasks
- [ ] Define alerting rule groups in Prometheus
- [ ] Configure AlertManager for notification routing
- [ ] Set up Slack/Teams integration
- [ ] Create runbooks for common alerts
- [ ] Implement alert severity levels
- [ ] Configure alert silencing and inhibition
- [ ] Test alert delivery and escalation

### Definition of Done
- [ ] Critical alerts fire within 5 minutes
- [ ] Alerts include actionable information
- [ ] Escalation procedures work correctly
- [ ] False positive rate is <5%
                """,
                "components": ["Monitoring", "Infrastructure"],
                "story_points": 8,
                "status": "To Do",
                "priority": "High"
            }
        ]
        
        created_stories = []
        
        for story in user_stories:
            # Map status to Jira status
            status_map = {
                "To Do": "10001",
                "Done": "10002",
                "In Progress": "10003"
            }
            
            story_data = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": story["summary"],
                    "issuetype": {"id": story_type_id},
                    "priority": {"name": story["priority"]},
                    "labels": ["user-story", "devops"],
                    "components": [{"id": self.components_map.get(comp, "")} 
                                 for comp in story["components"] 
                                 if self.components_map.get(comp)]
                }
            }
            
            # Skip Epic Link field for now - can be linked manually in Jira UI
            # Different Jira instances have different Epic Link field IDs
            
            # Skip Story Points field as it's not available in this instance
            # Story points can be added manually in Jira UI
            
            try:
                response = requests.post(
                    f"{self.base_url}/rest/api/3/issue",
                    auth=self.auth,
                    headers=self.headers,
                    json=story_data
                )
                
                if response.status_code == 201:
                    issue = response.json()
                    story_key = issue['key']
                    created_stories.append([story_key, story["summary"][:50] + "...", story["status"]])
                    print(f"{Fore.GREEN}  ✅ {story_key}: {story['summary']}{Style.RESET_ALL}")
                    
                    # If story is marked as Done, transition it
                    if story["status"] == "Done":
                        self.transition_issue(story_key, "Done")
                    
                    time.sleep(0.5)  # Rate limiting
                    
                else:
                    print(f"{Fore.RED}  ❌ Failed to create {story['summary']}: {response.status_code}{Style.RESET_ALL}")
                    print(f"     Response: {response.text}")
                    
            except Exception as e:
                print(f"{Fore.RED}  ❌ Error creating {story['summary']}: {str(e)}{Style.RESET_ALL}")
        
        if created_stories:
            print(f"\n{Fore.CYAN}📋 Created User Stories:{Style.RESET_ALL}")
            print(tabulate(created_stories, headers=["Story Key", "Summary", "Status"], tablefmt="grid"))
        
        return created_stories
    
    def transition_issue(self, issue_key, target_status):
        """Transition issue to target status"""
        try:
            # Get available transitions
            response = requests.get(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                transitions = response.json().get('transitions', [])
                
                for transition in transitions:
                    if transition['to']['name'].lower() == target_status.lower():
                        # Execute transition
                        transition_data = {
                            "transition": {"id": transition['id']}
                        }
                        
                        trans_response = requests.post(
                            f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                            auth=self.auth,
                            headers=self.headers,
                            json=transition_data
                        )
                        
                        if trans_response.status_code == 204:
                            print(f"{Fore.GREEN}    ✅ Transitioned {issue_key} to {target_status}{Style.RESET_ALL}")
                        break
                        
        except Exception as e:
            print(f"{Fore.YELLOW}    ⚠️ Could not transition {issue_key}: {str(e)}{Style.RESET_ALL}")
    
    def run_creation(self):
        """Run the complete story creation process"""
        try:
            # Get components
            if not self.get_components():
                return False
                
            # Create EPIC
            epic_key = self.create_epic()
            if not epic_key:
                return False
            
            # Create user stories
            created_stories = self.create_user_stories()
            
            print(f"\n{Fore.GREEN}🎉 EPIC and User Stories created successfully!{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}📊 Summary:{Style.RESET_ALL}")
            print(f"   EPIC: {epic_key}")
            print(f"   User Stories: {len(created_stories)}")
            print(f"\n{Fore.CYAN}📋 Next Steps:{Style.RESET_ALL}")
            print("1. Review and refine stories in Jira backlog")
            print("2. Run script 3_setup_automation_rules.py for automation")
            print("3. Configure GitHub integration with script 4_github_integration.py")
            print(f"\n{Fore.CYAN}🔗 Project URL: {self.base_url}/projects/{self.project_key}{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Story creation failed: {str(e)}{Style.RESET_ALL}")
            return False

if __name__ == "__main__":
    try:
        creator = JiraStoryCreator()
        creator.run_creation()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Story creation interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")