# Scripts - Disaster Response System

## Overview

The **Scripts directory** contains utility scripts for development, deployment, testing, and maintenance. These scripts automate common tasks and streamline the development workflow.

## Purpose

- **Development automation** - Setup, build, run
- **Testing utilities** - Test runners, data generators
- **Deployment** - Docker builds, environment setup
- **Maintenance** - Backup, cleanup, database management
- **Data management** - Import, export, migration

## Current Status

**Phase 1: Initialization**
- ✅ Scripts directory structure created
- ⏳ Individual utility scripts (Phase 2+)

## Planned Scripts

### Development & Setup (Phase 2+)

#### `setup.sh` - Complete project setup
```bash
./scripts/setup.sh
# Installs dependencies for all modules
# Creates virtual environments
# Initializes database
```

#### `run_all.sh` - Start all services
```bash
./scripts/run_all.sh
# Starts backend
# Starts dashboard
# Starts mobile (Expo)
```

#### `install_deps.sh` - Install all dependencies
```bash
./scripts/install_deps.sh
# Installs Node modules for mobile, dashboard
# Creates Python venv and installs requirements
# Installs ML and CV dependencies
```

### Testing & Validation (Phase 3+)

#### `test_backend.sh` - Run backend tests
```bash
./scripts/test_backend.sh
# Runs pytest on backend
# Checks code coverage
# Validates API endpoints
```

#### `test_mobile.sh` - Run mobile tests
```bash
./scripts/test_mobile.sh
# Runs Jest on mobile app
# Validates components
# Checks for errors
```

#### `lint.sh` - Code quality checks
```bash
./scripts/lint.sh
# Runs ESLint on JS/React
# Runs Pylint on Python
# Checks code style
```

### Data Management (Phase 2+)

#### `backup_db.py` - Backup database
```bash
python scripts/backup_db.py
# Creates database backup
# Saves to backups/ directory
# Compresses backup file
```

#### `generate_test_data.py` - Create test data
```bash
python scripts/generate_test_data.py --count 100
# Generates dummy emergencies
# Generates test messages
# Populates database for testing
```

#### `export_data.py` - Export data
```bash
python scripts/export_data.py --format csv --output data.csv
# Exports emergencies to CSV/JSON
# Useful for analysis and reporting
```

### Docker & Deployment (Phase 8+)

#### `build_docker.sh` - Build Docker images
```bash
./scripts/build_docker.sh
# Builds Docker images for all services
# Tags with version
# Pushes to registry
```

#### `docker_compose_up.sh` - Start Docker containers
```bash
./scripts/docker_compose_up.sh
# Starts all services via docker-compose
# Creates networks and volumes
# Monitors service health
```

### CI/CD Pipeline (Phase 8+)

#### `ci_validate.sh` - Continuous integration
```bash
./scripts/ci_validate.sh
# Runs all tests
# Checks code quality
# Validates builds
# Reports coverage
```

## Project Structure

```
scripts/
├── setup.sh                # Complete project setup
├── run_all.sh             # Start all services
├── install_deps.sh        # Install dependencies
├── test_backend.sh        # Backend tests
├── test_mobile.sh         # Mobile tests
├── lint.sh                # Code quality checks
├── backup_db.py           # Database backup
├── generate_test_data.py  # Create test data
├── export_data.py         # Export data
├── build_docker.sh        # Build Docker images
├── docker_compose_up.sh   # Start containers
├── ci_validate.sh         # CI pipeline validation
├── requirements.txt       # Script dependencies
├── README.md             # This file
└── .gitignore
```

## Usage

### Running Scripts

```bash
# Make executable
chmod +x scripts/*.sh

# Run specific script
./scripts/setup.sh

# Run Python script
python scripts/backup_db.py
```

### From Project Root

```bash
cd disaster-response-system

# Setup
bash scripts/setup.sh

# Run all services
bash scripts/run_all.sh

# Test
bash scripts/test_backend.sh
bash scripts/lint.sh
```

## Development Workflow

### Initial Setup

```bash
# Clone repo
git clone <repo-url>
cd disaster-response-system

# Run setup script
bash scripts/setup.sh

# Start all services
bash scripts/run_all.sh
```

### Testing Before Commit

```bash
# Run linter
bash scripts/lint.sh

# Run tests
bash scripts/test_backend.sh
bash scripts/test_mobile.sh

# If all pass, commit
git commit -m "Feature: implement SOS form"
```

### Database Management

```bash
# Backup current database
python scripts/backup_db.py

# Generate test data
python scripts/generate_test_data.py --count 50

# Export for analysis
python scripts/export_data.py --table emergencies
```

## Environment Variables

Scripts use `.env` files in each module:

```env
# .env in project root
PYTHON_VERSION=3.10
NODE_VERSION=18
DB_PATH=./database/disaster_response.db
```

## Dependencies

Scripts require:
- Bash shell (Unix-like systems)
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (for deployment)

## Error Handling

All scripts include:
- Exit code checking
- Error messages
- Rollback on failure
- Log output

### Example Error Handling

```bash
#!/bin/bash
set -e  # Exit on error

echo "Running database backup..."
if ! python scripts/backup_db.py; then
    echo "ERROR: Backup failed!"
    exit 1
fi

echo "Backup completed successfully"
```

## Logging

Scripts generate logs in `logs/` directory:

```
logs/
├── setup.log           # Setup execution log
├── test_backend.log    # Backend test results
├── lint.log            # Linting results
└── backup.log          # Backup operation log
```

Access logs:

```bash
tail -f logs/setup.log
cat logs/test_backend.log
```

## Troubleshooting

### Script Permission Errors

```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

### Python Script Errors

```bash
# Check Python version
python --version

# Install script dependencies
pip install -r scripts/requirements.txt
```

### Bash Script Errors

```bash
# Run with error tracing
bash -x scripts/setup.sh

# Check for syntax errors
bash -n scripts/setup.sh
```

## Contributing New Scripts

When adding new scripts:

1. **Use consistent naming**: `verb_noun.sh` or `noun_action.py`
2. **Add documentation**: Header comment explaining purpose
3. **Include error handling**: Exit codes and error messages
4. **Add to this README**: Document in appropriate section
5. **Make executable**: `chmod +x script_name.sh`
6. **Test thoroughly**: Run before committing

### Script Template

```bash
#!/bin/bash
# Purpose: Brief description
# Usage: ./scripts/my_script.sh [options]
# Author: Your name
# Date: August 2026

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'  # No Color

# Functions
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Main script
if [[ $# -eq 0 ]]; then
    print_error "No arguments provided"
    exit 1
fi

# Script logic here

print_success "Script completed"
exit 0
```

## CI/CD Integration

Scripts are designed for CI/CD pipelines:

```yaml
# GitHub Actions example (.github/workflows/ci.yml)
- name: Run linter
  run: bash scripts/lint.sh

- name: Run tests
  run: bash scripts/test_backend.sh

- name: Build Docker images
  run: bash scripts/build_docker.sh
```

## Maintenance

### Regular Tasks

- Review and update scripts monthly
- Test scripts on new system configurations
- Archive old scripts with version numbers
- Update documentation as features change

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [Development Guide](../docs/development.md)

## Resources

- [Bash Scripting Guide](https://www.gnu.org/software/bash/manual/)
- [Python Script Best Practices](https://www.python.org/dev/peps/pep-0394/)
- [Docker Documentation](https://docs.docker.com/)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 2+ (Script Implementation)  
**Last Updated**: August 2026
