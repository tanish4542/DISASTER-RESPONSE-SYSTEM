# Database Schema - Disaster Response System

## Overview

This document describes the database schema for the Disaster Response System. The database stores emergencies, messages, user information, and damage reports.

## Database Technology

### Phase 1-2: SQLite
- File-based database
- Good for development and testing
- Easy backup and portability
- Single-file format: `disaster_response.db`

### Phase 8+: PostgreSQL
- Enterprise-grade RDBMS
- Better for production scale
- Supports replication
- Connection pooling support

## Entity Relationship Diagram

```
[emergencies] 1 ←→ * [messages]
[emergencies] 1 ←→ * [assignments]
[users] 1 ←→ * [assignments]
[teams] 1 ←→ * [assignments]
[damage_reports] - - [emergencies]
[sync_state] 1 ←→ * [devices]
```

## Table Schemas

### emergencies
Stores emergency reports submitted by victims.

```sql
CREATE TABLE emergencies (
    id TEXT PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    victim_id TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT NOT NULL,
    emergency_type TEXT,
    severity_score REAL DEFAULT 0.0,
    priority_rank INTEGER,
    status TEXT DEFAULT 'pending',  -- pending, assigned, in_progress, resolved
    notes TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    resolved_at INTEGER
);

CREATE INDEX idx_emergencies_timestamp ON emergencies(timestamp DESC);
CREATE INDEX idx_emergencies_status ON emergencies(status);
CREATE INDEX idx_emergencies_priority ON emergencies(priority_rank);
CREATE INDEX idx_emergencies_location ON emergencies(latitude, longitude);
```

### messages
Stores individual emergency messages and communication.

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    emergency_id TEXT NOT NULL,
    source_device_id TEXT NOT NULL,
    message_text TEXT NOT NULL,
    media_urls TEXT,  -- JSON array of URLs
    classification TEXT,  -- Emergency type classification
    confidence_score REAL DEFAULT 0.0,
    hop_count INTEGER DEFAULT 3,
    is_forwarded BOOLEAN DEFAULT 0,
    ack_received BOOLEAN DEFAULT 0,
    created_at INTEGER NOT NULL,
    delivered_at INTEGER,
    FOREIGN KEY (emergency_id) REFERENCES emergencies(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_messages_emergency ON messages(emergency_id);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_messages_status ON messages(ack_received);
```

### users
Stores user information (victims, rescuers, coordinators).

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    role TEXT NOT NULL,  -- victim, rescuer, coordinator, admin
    status TEXT DEFAULT 'active',
    device_id TEXT,
    location_lat REAL,
    location_lon REAL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_device ON users(device_id);
CREATE INDEX idx_users_location ON users(location_lat, location_lon);
```

### teams
Stores rescue team information.

```sql
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    location_lat REAL,
    location_lon REAL,
    status TEXT DEFAULT 'available',  -- available, assigned, offline, on_break
    team_lead TEXT,
    capacity INTEGER DEFAULT 5,
    current_members INTEGER DEFAULT 0,
    vehicle_type TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX idx_teams_status ON teams(status);
CREATE INDEX idx_teams_location ON teams(location_lat, location_lon);
```

### assignments
Tracks assignment of teams to emergencies.

```sql
CREATE TABLE assignments (
    id TEXT PRIMARY KEY,
    emergency_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    assigned_at INTEGER NOT NULL,
    status TEXT DEFAULT 'assigned',  -- assigned, in_progress, completed, failed
    estimated_arrival_time INTEGER,
    actual_arrival_time INTEGER,
    completion_time INTEGER,
    notes TEXT,
    FOREIGN KEY (emergency_id) REFERENCES emergencies(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
);

CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_assignments_emergency ON assignments(emergency_id);
CREATE INDEX idx_assignments_team ON assignments(team_id);
```

### damage_reports
Stores computer vision damage detection results.

```sql
CREATE TABLE damage_reports (
    id TEXT PRIMARY KEY,
    image_url TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    damage_class INTEGER NOT NULL,  -- 0-4: none, minor, moderate, severe, destroyed
    confidence_score REAL NOT NULL,
    model_version TEXT,
    image_metadata TEXT,  -- JSON
    analysis_timestamp INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX idx_damage_location ON damage_reports(latitude, longitude);
CREATE INDEX idx_damage_timestamp ON damage_reports(created_at DESC);
CREATE INDEX idx_damage_class ON damage_reports(damage_class);
```

### sync_state
Tracks synchronization state for device-to-device communication.

```sql
CREATE TABLE sync_state (
    peer_id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    last_sync INTEGER,
    message_count INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'idle',  -- idle, syncing, error
    last_error TEXT,
    updated_at INTEGER NOT NULL
);

CREATE INDEX idx_sync_device ON sync_state(device_id);
```

### media_attachments
Stores file metadata for photos and videos.

```sql
CREATE TABLE media_attachments (
    id TEXT PRIMARY KEY,
    emergency_id TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- photo, video, audio
    file_size INTEGER NOT NULL,
    file_url TEXT NOT NULL,
    file_hash TEXT,
    upload_timestamp INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (emergency_id) REFERENCES emergencies(id) ON DELETE CASCADE
);

CREATE INDEX idx_media_emergency ON media_attachments(emergency_id);
CREATE INDEX idx_media_type ON media_attachments(file_type);
```

## Data Types

| Type | Size | Range | Usage |
|------|------|-------|-------|
| TEXT | Variable | 0-1GB | Strings, descriptions |
| INTEGER | 8 bytes | -2^63 to 2^63-1 | Timestamps, counts, enums |
| REAL | 8 bytes | Double precision | Latitude, longitude, scores |
| BLOB | Variable | 0-1GB | Binary data, encrypted fields |

## Constraints & Validations

### Primary Keys
- All tables use unique TEXT identifier (UUID)
- Format: `{table}_{timestamp}_{random}`

### Foreign Keys
- Enforced referential integrity
- CASCADE delete for related records

### Check Constraints

```sql
ALTER TABLE emergencies 
  ADD CHECK (severity_score >= 0 AND severity_score <= 10);

ALTER TABLE damage_reports
  ADD CHECK (damage_class >= 0 AND damage_class <= 4);

ALTER TABLE assignments
  ADD CHECK (estimated_arrival_time >= 0);
```

## Indexes

### Performance Indexes
```sql
-- Emergency lookup by status
CREATE INDEX idx_emergencies_status_rank 
  ON emergencies(status, priority_rank DESC);

-- Geospatial queries
CREATE INDEX idx_emergencies_bbox 
  ON emergencies(latitude, longitude)
  WHERE status != 'resolved';

-- Time range queries
CREATE INDEX idx_messages_timerange 
  ON messages(created_at DESC)
  WHERE ack_received = 0;
```

## Sample Queries

### Active Emergencies
```sql
SELECT id, latitude, longitude, severity_score, priority_rank
FROM emergencies
WHERE status IN ('pending', 'assigned', 'in_progress')
ORDER BY priority_rank ASC
LIMIT 50;
```

### Priority Queue
```sql
SELECT e.id, e.description, e.priority_rank, 
       t.name as assigned_team, t.location_lat, t.location_lon
FROM emergencies e
LEFT JOIN assignments a ON e.id = a.emergency_id
LEFT JOIN teams t ON a.team_id = t.id
WHERE e.status = 'pending'
ORDER BY e.priority_rank ASC;
```

### Damage Statistics
```sql
SELECT 
  damage_class,
  COUNT(*) as count,
  AVG(confidence_score) as avg_confidence,
  MAX(confidence_score) as max_confidence
FROM damage_reports
WHERE created_at > datetime('now', '-24 hours')
GROUP BY damage_class
ORDER BY damage_class;
```

### Team Workload
```sql
SELECT 
  t.id, t.name, t.status,
  COUNT(a.id) as active_assignments,
  COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed
FROM teams t
LEFT JOIN assignments a ON t.id = a.team_id
GROUP BY t.id
ORDER BY active_assignments DESC;
```

## Backup & Recovery

### SQLite Backup
```bash
# Full backup
cp disaster_response.db disaster_response.db.backup

# Incremental backup (Phase 8)
sqlite3 disaster_response.db ".backup disaster_response_$(date +%Y%m%d_%H%M%S).db"
```

### PostgreSQL Backup (Phase 8)
```bash
# Full backup
pg_dump -U postgres disaster_db > backup.sql

# Restore
psql -U postgres disaster_db < backup.sql
```

## Maintenance

### Analyze Query Performance
```sql
ANALYZE;
```

### Optimize Database
```sql
VACUUM;  -- Reclaim space
REINDEX; -- Rebuild indexes
```

### Data Cleanup (Phase 8)

```sql
-- Delete resolved emergencies older than 90 days
DELETE FROM emergencies 
WHERE status = 'resolved' 
  AND resolved_at < datetime('now', '-90 days');

-- Delete old sync state
DELETE FROM sync_state
WHERE updated_at < datetime('now', '-30 days');
```

## Disaster Recovery

### RTO (Recovery Time Objective)
- Target: < 1 hour
- Backup frequency: Daily
- Off-site storage: Yes

### RPO (Recovery Point Objective)
- Target: < 1 hour
- Acceptable data loss: < 1 hour

## Migration Strategy (Phase 2→8)

### SQLite to PostgreSQL

```sql
-- 1. Create PostgreSQL database
CREATE DATABASE disaster_db;

-- 2. Create tables (same schema)
-- 3. Export SQLite data
sqlite3 disaster_response.db ".dump" > sqlite_dump.sql

-- 4. Import to PostgreSQL
psql disaster_db < sqlite_dump.sql

-- 5. Verify data integrity
-- 6. Update connection string
```

## Compliance & Security

- **Encryption**: Enable at-rest encryption (Phase 8)
- **Audit Logging**: Track all changes (Phase 8)
- **Access Control**: Role-based database permissions (Phase 8)
- **GDPR Compliance**: Data retention policies (Phase 8)

---

**Version**: 1.0  
**Phase**: 1 (Schema Definition)  
**Last Updated**: August 2026  
**Status**: ✅ Ready for Phase 2 Implementation
