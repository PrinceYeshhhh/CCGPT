# CustomerCareGPT Backup & Disaster Recovery Guide

This comprehensive guide covers backup strategies, disaster recovery procedures, and business continuity planning for the CustomerCareGPT platform.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [Disaster Recovery Plans](#disaster-recovery-plans)
4. [Implementation](#implementation)
5. [Management Tools](#management-tools)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Testing Procedures](#testing-procedures)
8. [Recovery Procedures](#recovery-procedures)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## 🎯 Overview

The CustomerCareGPT backup and disaster recovery system provides:

- **Automated Backups**: Scheduled full, incremental, and differential backups
- **Multi-Component Support**: Database, Redis, ChromaDB, uploads, and configuration
- **Disaster Recovery Plans**: Pre-defined recovery procedures for different scenarios
- **Validation & Testing**: Comprehensive validation and testing procedures
- **Monitoring & Alerting**: Real-time monitoring and alerting for backup operations
- **Command-Line Tools**: Easy-to-use management tools for backup operations

## 🔄 Backup Strategy

### Backup Types

#### 1. Full Backup
- **Frequency**: Weekly (Sunday 3:00 AM)
- **Retention**: 30 days
- **Components**: All components (database, Redis, ChromaDB, uploads, config)
- **Size**: ~2-5GB (depending on data volume)

#### 2. Incremental Backup
- **Frequency**: Daily (2:00 AM)
- **Retention**: 7 days
- **Components**: Database and Redis only
- **Size**: ~100-500MB

#### 3. Differential Backup
- **Frequency**: On-demand
- **Retention**: 14 days
- **Components**: All components since last full backup
- **Size**: ~500MB-2GB

#### 4. WAL (Write-Ahead Log) Backup
- **Frequency**: Continuous (if configured)
- **Retention**: 3 days
- **Components**: PostgreSQL WAL files
- **Size**: ~50-100MB per hour

### Backup Components

#### Database (PostgreSQL)
- **Method**: `pg_dump` with custom format
- **Includes**: Schema, data, indexes, constraints
- **Excludes**: Temporary tables, system catalogs
- **Compression**: gzip compression
- **Validation**: Checksum verification

#### Redis Cache
- **Method**: RDB snapshot + JSON export
- **Includes**: All keys and data structures
- **Compression**: gzip compression
- **Validation**: Key count verification

#### ChromaDB Vector Database
- **Method**: Directory tar archive
- **Includes**: All collections and embeddings
- **Compression**: gzip compression
- **Validation**: Collection count verification

#### Uploaded Files
- **Method**: Directory tar archive
- **Includes**: All user-uploaded files
- **Compression**: gzip compression
- **Validation**: File count and size verification

#### Configuration
- **Method**: JSON export
- **Includes**: Environment variables, application config
- **Compression**: None (small files)
- **Validation**: JSON schema validation

## 🚨 Disaster Recovery Plans

### 1. Full System Recovery
- **RTO**: 60 minutes
- **RPO**: 15 minutes
- **Priority**: 1 (Highest)
- **Components**: All components
- **Use Case**: Complete system failure

### 2. Database Recovery
- **RTO**: 30 minutes
- **RPO**: 5 minutes
- **Priority**: 2 (High)
- **Components**: Database only
- **Use Case**: Database corruption or failure

### 3. Application Recovery
- **RTO**: 15 minutes
- **RPO**: 0 minutes
- **Priority**: 3 (Medium)
- **Components**: Application and configuration
- **Use Case**: Application failure, configuration issues

### 4. Data Recovery
- **RTO**: 45 minutes
- **RPO**: 10 minutes
- **Priority**: 2 (High)
- **Components**: Uploads and ChromaDB
- **Use Case**: Data loss, file system issues

## 🛠️ Implementation

### Backup Service

The backup service (`app/services/backup_service.py`) provides:

```python
from app.services.backup_service import backup_service, BackupType

# Create a full backup
metadata = await backup_service.create_backup(
    backup_type=BackupType.FULL,
    components=["database", "redis", "chromadb", "uploads", "config"],
    retention_days=30
)

# List available backups
backups = await backup_service.list_backups()

# Restore from backup
success = await backup_service.restore_backup(
    backup_id="backup_20240101_120000",
    components=["database", "redis"]
)
```

### Backup Scheduler

The backup scheduler (`app/services/backup_scheduler.py`) provides:

```python
from app.services.backup_scheduler import backup_scheduler

# Start the scheduler
backup_scheduler.start()

# Add a custom schedule
schedule = BackupSchedule(
    schedule_id="custom_daily",
    schedule_type=ScheduleType.DAILY,
    backup_type=BackupType.INCREMENTAL,
    components=["database", "redis"],
    retention_days=7,
    time_of_day="01:00"
)
backup_scheduler.add_schedule(schedule)
```

### Disaster Recovery Service

The disaster recovery service (`app/services/disaster_recovery.py`) provides:

```python
from app.services.disaster_recovery import disaster_recovery_service

# Initiate recovery
operation = await disaster_recovery_service.initiate_recovery(
    plan_id="full_system_recovery",
    backup_id="backup_20240101_120000"
)

# Get recovery plans
plans = disaster_recovery_service.get_recovery_plans()
```

## 🔧 Management Tools

### Command-Line Tool

The backup manager script provides comprehensive CLI functionality:

```bash
# Create a backup
python backend/scripts/backup_manager.py create --type full --components database redis

# List backups
python backend/scripts/backup_manager.py list --status completed --limit 10

# Restore from backup
python backend/scripts/backup_manager.py restore backup_20240101_120000 --components database

# Delete a backup
python backend/scripts/backup_manager.py delete backup_20240101_120000 --force

# Clean up old backups
python backend/scripts/backup_manager.py cleanup

# Manage schedules
python backend/scripts/backup_manager.py schedule list
python backend/scripts/backup_manager.py schedule enable daily_incremental

# Disaster recovery
python backend/scripts/backup_manager.py disaster-recovery plans
python backend/scripts/backup_manager.py disaster-recovery initiate --plan-id full_system_recovery

# Health check
python backend/scripts/backup_manager.py health
```

### API Endpoints

#### Backup Management
- `POST /api/v1/backup/create` - Create a new backup
- `GET /api/v1/backup/list` - List available backups
- `GET /api/v1/backup/{backup_id}` - Get backup details
- `POST /api/v1/backup/{backup_id}/restore` - Restore from backup
- `DELETE /api/v1/backup/{backup_id}` - Delete a backup
- `POST /api/v1/backup/cleanup` - Clean up old backups

#### Disaster Recovery
- `GET /api/v1/disaster-recovery/plans` - Get recovery plans
- `POST /api/v1/disaster-recovery/initiate` - Initiate recovery
- `GET /api/v1/disaster-recovery/operations` - Get recovery operations
- `GET /api/v1/disaster-recovery/status` - Get recovery status

## 📊 Monitoring & Alerting

### Backup Monitoring

#### Metrics
- Backup success/failure rates
- Backup duration and size
- Storage usage and growth
- Recovery time objectives (RTO)
- Recovery point objectives (RPO)

#### Alerts
- Backup failures
- Backup size anomalies
- Storage space warnings
- Recovery operation failures
- Validation check failures

### Health Checks

#### System Health
- Backup directory accessibility
- S3 connectivity (if configured)
- Recent backup availability
- Scheduler status
- Service dependencies

#### Validation Checks
- Database connectivity
- Redis connectivity
- ChromaDB connectivity
- Application health
- API endpoints
- Data integrity
- Schema validation

## 🧪 Testing Procedures

### Backup Testing

#### 1. Backup Creation Test
```bash
# Create test backup
python backend/scripts/backup_manager.py create --type full

# Verify backup was created
python backend/scripts/backup_manager.py list --status completed
```

#### 2. Backup Validation Test
```bash
# Check backup integrity
python backend/scripts/backup_manager.py health
```

#### 3. Restore Test
```bash
# Test restore in isolated environment
python backend/scripts/backup_manager.py restore backup_20240101_120000 --components database
```

### Disaster Recovery Testing

#### 1. Recovery Plan Test
```bash
# Test recovery plan without actual recovery
python backend/scripts/backup_manager.py disaster-recovery test full_system_recovery
```

#### 2. Full Recovery Test
```bash
# Test full system recovery (in test environment)
python backend/scripts/backup_manager.py disaster-recovery initiate --plan-id full_system_recovery
```

### Scheduled Testing

#### Weekly Tests
- Backup creation and validation
- Restore testing in isolated environment
- Recovery plan validation

#### Monthly Tests
- Full disaster recovery simulation
- Cross-region backup testing
- Recovery time measurement

## 🔄 Recovery Procedures

### Emergency Recovery

#### 1. Immediate Response
1. Assess the scope of the disaster
2. Activate the disaster recovery team
3. Choose appropriate recovery plan
4. Initiate recovery procedures

#### 2. Recovery Execution
1. Stop affected services
2. Restore from most recent backup
3. Validate system integrity
4. Start services in correct order
5. Perform post-recovery validation

#### 3. Post-Recovery
1. Monitor system stability
2. Validate data integrity
3. Update stakeholders
4. Document lessons learned
5. Update recovery procedures

### Step-by-Step Recovery

#### Database Recovery
```bash
# 1. Stop application services
docker-compose down

# 2. Restore database
python backend/scripts/backup_manager.py restore backup_20240101_120000 --components database

# 3. Start database services
docker-compose up -d postgres

# 4. Validate database
python backend/scripts/backup_manager.py health

# 5. Start application services
docker-compose up -d
```

#### Full System Recovery
```bash
# 1. Initiate full recovery
python backend/scripts/backup_manager.py disaster-recovery initiate --plan-id full_system_recovery

# 2. Monitor recovery progress
python backend/scripts/backup_manager.py disaster-recovery status

# 3. Validate system health
python backend/scripts/backup_manager.py health
```

## ✅ Best Practices

### Backup Best Practices

#### 1. Backup Frequency
- **Critical Data**: Daily incremental backups
- **Important Data**: Weekly full backups
- **Configuration**: On every change
- **Logs**: Daily rotation

#### 2. Backup Storage
- **Local Storage**: For quick recovery
- **Remote Storage**: For disaster protection
- **Multiple Locations**: Geographic distribution
- **Encryption**: At rest and in transit

#### 3. Backup Validation
- **Regular Testing**: Weekly restore tests
- **Integrity Checks**: Checksum verification
- **Size Monitoring**: Anomaly detection
- **Retention Management**: Automated cleanup

### Disaster Recovery Best Practices

#### 1. Planning
- **Documentation**: Keep procedures updated
- **Training**: Regular team training
- **Testing**: Regular recovery tests
- **Communication**: Clear escalation procedures

#### 2. Recovery
- **Prioritization**: Critical systems first
- **Validation**: Verify each step
- **Monitoring**: Continuous health checks
- **Documentation**: Record all actions

#### 3. Post-Recovery
- **Analysis**: Root cause analysis
- **Improvement**: Update procedures
- **Communication**: Stakeholder updates
- **Prevention**: Implement safeguards

## 🚨 Troubleshooting

### Common Issues

#### Backup Failures

**Issue**: Backup creation fails
```bash
# Check system resources
python backend/scripts/backup_manager.py health

# Check logs
docker-compose logs backup-service

# Retry backup
python backend/scripts/backup_manager.py create --type full
```

**Issue**: Backup restore fails
```bash
# Verify backup integrity
python backend/scripts/backup_manager.py list --status completed

# Check system resources
python backend/scripts/backup_manager.py health

# Retry restore
python backend/scripts/backup_manager.py restore backup_20240101_120000
```

#### Scheduler Issues

**Issue**: Scheduler not running
```bash
# Check scheduler status
python backend/scripts/backup_manager.py schedule status

# Start scheduler
python backend/scripts/backup_manager.py schedule enable daily_incremental
```

**Issue**: Scheduled backups not executing
```bash
# Check system time
date

# Check scheduler logs
docker-compose logs backup-scheduler

# Manually trigger backup
python backend/scripts/backup_manager.py create --type incremental
```

#### Recovery Issues

**Issue**: Recovery operation fails
```bash
# Check recovery status
python backend/scripts/backup_manager.py disaster-recovery status

# Check system health
python backend/scripts/backup_manager.py health

# Retry recovery
python backend/scripts/backup_manager.py disaster-recovery initiate --plan-id database_recovery
```

### Debug Commands

```bash
# Check backup system health
python backend/scripts/backup_manager.py health

# List all backups with details
python backend/scripts/backup_manager.py list --limit 50

# Check scheduler status
python backend/scripts/backup_manager.py schedule status

# Test recovery plan
python backend/scripts/backup_manager.py disaster-recovery test full_system_recovery

# Check system resources
docker stats

# Check service logs
docker-compose logs -f
```

## 📞 Support

### Emergency Contacts

- **Primary On-Call**: +1-XXX-XXX-XXXX
- **Secondary On-Call**: +1-XXX-XXX-XXXX
- **Escalation**: +1-XXX-XXX-XXXX

### Documentation

- **Runbooks**: `/docs/runbooks/`
- **Procedures**: `/docs/procedures/`
- **Architecture**: `/docs/architecture/`

### Monitoring

- **Dashboard**: https://monitoring.customercaregpt.com
- **Alerts**: https://alerts.customercaregpt.com
- **Logs**: https://logs.customercaregpt.com

---

**Note**: This guide should be reviewed and updated regularly to ensure it remains current with the system architecture and procedures.
