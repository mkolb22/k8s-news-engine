# Service Documentation Standard

## Overview

Each microservice in the K8s News Engine must maintain comprehensive documentation in its service directory as `README.md`. This ensures consistency, maintainability, and knowledge transfer.

## Required Documentation Sections

### 1. Service Header
```markdown
# [Service Name]

## Overview
Brief description of the service purpose and role in the system.
```

### 2. Architecture
```markdown
## Architecture
- **Language**: Primary programming language and version
- **Database**: Database technology and connection details
- **Deployment**: Deployment method (Kubernetes, Docker, etc.)
- **Processing**: Processing model (batch, real-time, event-driven)
- **Container**: Current container image name and version
```

### 3. Core Functionality
```markdown
## Core Functionality
Detailed description of what the service does, including:
- Primary business logic
- Data processing workflows
- Integration points
- Key algorithms or methods
```

### 4. Database Schema
```markdown
## Database Schema
### Input Tables
- Table descriptions and key columns

### Output Tables  
- Table descriptions and modifications made
- Any new columns added
- Indexes created
```

### 5. Configuration
```markdown
## Configuration
### Environment Variables
- Variable name, purpose, and default values

### Processing Logic
- Key configuration parameters
- Performance tuning options
```

### 6. Deployment
```markdown
## Deployment
### Kubernetes Resources
- Resource definitions
- Service configurations
- Health check implementations

### Development Commands
```bash
# Build commands
# Deploy commands  
# Monitoring commands
```

### 7. Monitoring & Troubleshooting
```markdown
## Monitoring
### Log Messages
- Key log messages and their meanings

### Metrics
- Important metrics to track

## Troubleshooting
### Common Issues
- Frequent problems and solutions

### Debug Queries
- Useful SQL queries or debug commands
```

### 8. Change Log
```markdown
## Change Log

### vX.Y.Z (YYYY-MM-DD)
**[Change Type]: [Brief Description]**

#### Changes Made
- ✅ **[Feature Name]**: Description of change
- 🔧 **[Fix Name]**: Description of fix
- 📈 **[Enhancement]**: Description of improvement

#### Technical Details  
- **Function/Method**: Code location and purpose
- **Container**: Container version information
- **Database**: Schema changes
- **Validation**: Testing and verification performed

#### Migration Notes
- Any breaking changes
- Upgrade instructions
- Database migration scripts

### Previous Versions
- Brief description of earlier versions
```

## Documentation Standards

### 1. Change Documentation
**Every code change must be documented** in the service README:
- Add entry to Change Log section
- Update relevant functional sections
- Include validation results
- Document any breaking changes

### 2. Version Management
- Use semantic versioning (major.minor.patch)
- Container versions must match documentation
- Document upgrade path for breaking changes

### 3. Technical Details
- Include function names and file locations for major changes
- Provide example code snippets for complex functionality
- Document performance characteristics and limitations

### 4. Validation Requirements
- Document testing methodology
- Include validation results and metrics
- Provide example queries or API calls

## Implementation Checklist

When creating or updating service documentation:

- [ ] **Header Section**: Service name and overview complete
- [ ] **Architecture**: Technology stack documented
- [ ] **Functionality**: Core features explained
- [ ] **Database**: Schema changes documented
- [ ] **Configuration**: Environment variables listed
- [ ] **Deployment**: Commands and resources documented
- [ ] **Monitoring**: Logs and metrics explained
- [ ] **Troubleshooting**: Common issues addressed
- [ ] **Change Log**: Latest changes documented with version
- [ ] **Code Review**: Documentation reviewed alongside code

## Example Services

### Completed Documentation
- ✅ **quality-service**: Comprehensive documentation with NER feature changelog
  
### Pending Documentation
- 🔄 **rss-fetcher**: Needs documentation standardization
- 🔄 **publisher**: Needs documentation standardization  
- 🔄 **analytics-py**: Needs documentation standardization
- 🔄 **claim-extractor**: Needs documentation standardization

## Maintenance

- Review documentation quarterly for accuracy
- Update change logs with every release
- Validate example commands and queries
- Keep troubleshooting section current with known issues

## Benefits

1. **Knowledge Transfer**: New developers can quickly understand services
2. **Change Tracking**: Full history of modifications and reasoning
3. **Troubleshooting**: Documented solutions to common problems  
4. **Integration**: Clear API and database contracts
5. **Compliance**: Auditable change history for production systems