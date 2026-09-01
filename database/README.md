# Database - Disaster Response System

## Overview

The **Database module** manages persistent storage for the system. It contains:

- **Database schema** - Tables for emergencies, messages, users, etc.
- **Migrations** - Version control for schema changes
- **Backup procedures** - Data protection and recovery
- **Indexing strategies** - Performance optimization

## Architecture

### Core Components (Phase 2+)

- **Schema Definition** - Tables and relationships
- **Migrations** - Alembic or manual migration scripts
- **Backup System** - Automated backups and recovery
- **Performance** - Indexes, query optimization
- **Data Integrity** - Constraints and validations

### Current Status

**Phase 1: Initialization**
- ✅ Module directory structure created
- ⏳ Schema design (Phase 2)
- ⏳ Migration scripts (Phase 2)
- ⏳ Backup procedures (Phase 8)
- ⏳ Performance tuning (Phase 8)

## Technology Stack

- **Database Engine**: SQLite (Phase 1-2), PostgreSQL (Phase 8+)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Language**: Python
- **Data Format**: SQL

## Project Structure

```
database/
├── data/                # Database files
│   ├── disaster_response.db
│   ├── backups/
│   └── exports/
├── migrations/          # Alembic migration scripts (Phase 2)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py
│       └── ...
├── scripts/             # Database utilities
│   ├── init_db.py      # Initialize database
│   ├── backup.py       # Backup procedures
│   ├── restore.py      # Restore from backup
│   └── export_csv.py   # Data export
├── schema.sql          # SQL schema definition (Phase 2)
├── README.md           # This file
└── .gitignore
```

## Planned Development

### Phase 2: Database Design & Implementation
1. Design schema for emergencies, messages, users
2. Define relationships and constraints
3. Create initial schema.sql
4. Set up SQLAlchemy models
5. Implement database initialization script
6. Test database operations

### Phase 8: Advanced Features
- PostgreSQL migration
- Replication & failover
- Backup automation
- Query performance optimization
- Archival strategies

## Database Schema (Phase 2+)

### Planned Tables

#### emergencies
```sql
CREATE TABLE emergencies (
    id TEXT PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    victim_id TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT,
    emergency_type TEXT,
    severity_score REAL,
    priority_rank INTEGER,
    status TEXT,  -- 'pending', 'assigned', 'resolved'
    created_at INTEGER,
    updated_at INTEGER
);
```

#### messages
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    emergency_id TEXT NOT NULL,
    source_device_id TEXT,
    message_text TEXT,
    media_urls TEXT,  -- JSON array of URLs
    classification TEXT,
    confidence_score REAL,
    created_at INTEGER,
    FOREIGN KEY (emergency_id) REFERENCES emergencies(id)
);
```

#### users
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT,  -- 'victim', 'rescuer', 'coordinator'
    created_at INTEGER
);
```

#### teams
```sql
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    name TEXT,
    location_lat REAL,
    location_lon REAL,
    status TEXT,  -- 'available', 'assigned', 'offline'
    updated_at INTEGER
);
```

#### assignments
```sql
CREATE TABLE assignments (
    id TEXT PRIMARY KEY,
    emergency_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    assigned_at INTEGER,
    status TEXT,  -- 'assigned', 'in_progress', 'completed'
    FOREIGN KEY (emergency_id) REFERENCES emergencies(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);
```

#### damage_reports
```sql
CREATE TABLE damage_reports (
    id TEXT PRIMARY KEY,
    image_url TEXT,
    latitude REAL,
    longitude REAL,
    damage_class INTEGER,  -- 0-4 scale
    confidence_score REAL,
    created_at INTEGER
);
```

## Indexes (Phase 2+)

```sql
CREATE INDEX idx_emergencies_timestamp ON emergencies(timestamp DESC);
CREATE INDEX idx_emergencies_status ON emergencies(status);
CREATE INDEX idx_emergencies_priority ON emergencies(priority_rank);
CREATE INDEX idx_emergencies_location ON emergencies(latitude, longitude);
CREATE INDEX idx_messages_emergency ON messages(emergency_id);
CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_damage_location ON damage_reports(latitude, longitude);
```

## Connection String

### SQLite (Development)
```python
DATABASE_URL = "sqlite:///./disaster_response.db"
```

### PostgreSQL (Production - Phase 8)
```python
DATABASE_URL = "postgresql://user:password@localhost/disaster_db"
```

## Initialization

### Phase 2: Create Database

```bash
cd database
python scripts/init_db.py
```

### Using SQLAlchemy

```python
from backend.app.database import engine, Base

# Create all tables
Base.metadata.create_all(bind=engine)
```

## Backup & Recovery

### Manual Backup

```bash
cd database
python scripts/backup.py
# Creates: backups/disaster_response_2024-08-31_120000.db
```

### Automated Backup (Phase 8)

```bash
# Scheduled daily backup
0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
python scripts/restore.py backups/disaster_response_2024-08-31_120000.db
```

## Data Export

### Export to CSV

```bash
python scripts/export_csv.py --table emergencies --output data/emergencies.csv
```

### Export to JSON

```bash
python scripts/export_json.py --table messages --output data/messages.json
```

## Performance Optimization

### Query Tips
- Always use indexes for WHERE clauses
- Use LIMIT for large result sets
- Batch insert operations
- Use prepared statements

### Maintenance
```sql
-- Optimize database (SQLite)
VACUUM;
ANALYZE;

-- Reindex tables
REINDEX;
```

## Security Considerations

- Encrypt sensitive fields (passwords, phone numbers)
- Use parameterized queries (SQLAlchemy ORM handles this)
- Regular backups
- Access control & authentication (Phase 8)
- Audit logging (Phase 8)

## Disaster Recovery Plan (Phase 8)

1. **Regular Backups**: Daily automated backups
2. **Backup Storage**: On-site and off-site copies
3. **Recovery Testing**: Monthly restore tests
4. **RTO Target**: < 1 hour
5. **RPO Target**: < 1 hour (loss acceptable)

## Monitoring & Alerts (Phase 8)

- Database size monitoring
- Query performance tracking
- Backup success verification
- Disk space warnings
- Connection pool monitoring

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [Database Schema](../docs/database.md)
- [API Documentation](../docs/api.md)

## Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Design Best Practices](https://en.wikipedia.org/wiki/Database_design)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 2 (Schema Implementation)  
**Last Updated**: August 2026
