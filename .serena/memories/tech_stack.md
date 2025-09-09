# Tech Stack

## Languages
- **Python**: Analytics service, data processing, machine learning
- **Go**: RSS fetcher service (high-performance, low-footprint)
- **CGI/Shell**: Publisher service scripts

## Key Technologies

### Python Stack
- **SQLAlchemy 2.0.35**: Database ORM
- **psycopg2-binary 2.9.9**: PostgreSQL driver
- **pandas 2.2.2**: Data manipulation and analysis
- **numpy 2.1.1**: Numerical computing
- **scikit-learn 1.5.2**: Machine learning (TF-IDF analysis)
- **PyYAML 6.0.2**: Configuration management

### Go Stack
- **Go 1.21**: Core language
- **gofeed**: RSS feed parsing
- **goquery**: HTML parsing and content extraction
- **gocron**: Scheduled task management
- **logrus**: Structured logging
- **lib/pq**: PostgreSQL driver

### Infrastructure
- **PostgreSQL**: Primary database
- **Docker**: Multi-stage builds, Alpine-based images
- **Kubernetes**: Orchestration (CronJobs, Deployments, ConfigMaps)
- **Lighttpd**: Web server for publisher service

## Development Environment
- macOS (Darwin)
- Git version control
- Docker for local testing
- Kubernetes for deployment