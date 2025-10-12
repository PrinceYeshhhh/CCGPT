# Migration System Documentation

## Overview

The CustomerCareGPT backend uses a robust, multi-layered migration system designed to handle database schema changes reliably across different environments (development, testing, production) and database types (SQLite, PostgreSQL).

## Architecture

The migration system consists of several components working together:

1. **Alembic** - Primary migration framework
2. **Direct Migration Scripts** - Bypass Alembic for maximum reliability
3. **Validation Scripts** - Ensure migration state consistency
4. **Health Check Scripts** - Monitor system health
5. **Rollback Scripts** - Safe migration reversal
6. **Test Suite** - Comprehensive testing

## Migration Scripts

### Core Migration Scripts

#### 1. `run_migration_chain.py`
**Purpose**: Main entry point for running migrations in CI/CD environments.

**Usage**:
```bash
python run_migration_chain.py
```

**Features**:
- PowerShell-compatible (no Unicode emojis)
- Runs migration chain with fallback strategies
- Comprehensive error handling
- Timeout protection

#### 2. `direct_migrate.py`
**Purpose**: Direct database migration bypassing Alembic completely.

**Usage**:
```bash
python direct_migrate.py
```

**Features**:
- Creates all tables and indexes directly using SQLAlchemy
- 100% reliable - no Alembic dependencies
- Handles both PostgreSQL and SQLite
- Idempotent operations

#### 3. `smart_migrate.py`
**Purpose**: Intelligent migration with database state detection.

**Usage**:
```bash
python smart_migrate.py
```

**Features**:
- Detects actual database state
- Sets Alembic version to match database
- Prevents circular dependency errors
- Handles fresh databases

#### 4. `nuclear_migrate.py`
**Purpose**: Aggressive migration reset for problematic databases.

**Usage**:
```bash
python nuclear_migrate.py
```

**Features**:
- Force kills existing connections
- Uses `DISCARD ALL` for PostgreSQL
- Creates fresh version table
- Emergency recovery tool

#### 5. `simple_migrate.py`
**Purpose**: Simple Alembic migration without retry logic.

**Usage**:
```bash
python simple_migrate.py
```

**Features**:
- Direct Alembic execution
- No complex retry logic
- Fast execution
- Good for clean databases

#### 6. `migrate_with_retry.py`
**Purpose**: Migration with retry logic and connection recovery.

**Usage**:
```bash
python migrate_with_retry.py
```

**Features**:
- Retry logic with exponential backoff
- Connection state recovery
- Transaction error handling
- Comprehensive logging

#### 7. `ultra_migrate.py`
**Purpose**: Ultra-aggressive migration with complete reset.

**Usage**:
```bash
python ultra_migrate.py
```

**Features**:
- Complete database reset
- Force version table recreation
- Handles corrupted states
- Last resort option

### Validation and Health Scripts

#### 1. `validate_migration_state.py`
**Purpose**: Validates migration state before running migrations.

**Usage**:
```bash
python validate_migration_state.py
```

**Features**:
- Detects version mismatches
- Identifies circular dependency risks
- Automatically fixes version issues
- Comprehensive state analysis

#### 2. `migration_health_check.py`
**Purpose**: Comprehensive health check of the migration system.

**Usage**:
```bash
python migration_health_check.py
```

**Features**:
- Database connection testing
- Schema validation
- Permission checking
- Script validation
- Detailed reporting

#### 3. `rollback_migration.py`
**Purpose**: Safe migration rollback functionality.

**Usage**:
```bash
# Interactive mode
python rollback_migration.py

# Command line mode
python rollback_migration.py previous
python rollback_migration.py initial
python rollback_migration.py base
python rollback_migration.py emergency
python rollback_migration.py to:003_add_subscriptions_table
```

**Features**:
- Multiple rollback strategies
- Interactive and command-line modes
- Emergency rollback option
- Safe operation validation

### Test Scripts

#### 1. `test_migration_system.py`
**Purpose**: Comprehensive test suite for migration system.

**Usage**:
```bash
python test_migration_system.py
```

**Features**:
- Fresh database testing
- Migration validation testing
- Rollback testing
- Schema consistency testing
- Circular dependency testing

## Migration Chain Strategy

The migration system uses a fallback chain approach:

1. **Migration State Validation** - Validates current state
2. **Direct Migration** - Bypasses Alembic (most reliable)
3. **Nuclear Migration** - Aggressive reset
4. **Smart Migration** - Intelligent detection
5. **Simple Migration** - Direct Alembic
6. **Retry Migration** - Complex retry logic
7. **Ultra Migration** - Ultra-aggressive reset

## Database Compatibility

### SQLite
- Uses batch mode for `ALTER TABLE` operations
- Handles column type differences gracefully
- Creates indexes with warnings for missing columns
- Uses `CURRENT_TIMESTAMP` instead of `now()`

### PostgreSQL
- Uses autocommit mode to avoid transaction issues
- Handles `InFailedSqlTransaction` errors
- Uses `DISCARD ALL` for connection reset
- Proper transaction isolation

## Common Issues and Solutions

### 1. Circular Dependency Error
**Problem**: `sqlalchemy.exc.CircularDependencyError`

**Solution**: Use `smart_migrate.py` to detect and fix version mismatches.

### 2. Failed Transaction Error
**Problem**: `psycopg2.errors.InFailedSqlTransaction`

**Solution**: Use `nuclear_migrate.py` or `ultra_migrate.py` to reset connection state.

### 3. Version Mismatch
**Problem**: Alembic version doesn't match database state

**Solution**: Use `validate_migration_state.py` to detect and fix mismatches.

### 4. Missing Tables/Columns
**Problem**: Database schema doesn't match expected structure

**Solution**: Use `direct_migrate.py` to recreate schema from scratch.

### 5. Unicode Issues
**Problem**: Unicode emoji characters in Windows PowerShell

**Solution**: All scripts now use plain text (no emojis).

## GitHub Actions Integration

The migration system is integrated into GitHub Actions workflows:

```yaml
- name: Run database migrations
  working-directory: ./backend
  run: |
    python run_migration_chain.py
  env:
    DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
```

## Best Practices

### 1. Development
- Use `direct_migrate.py` for local development
- Run `migration_health_check.py` before committing
- Test with both SQLite and PostgreSQL

### 2. CI/CD
- Use `run_migration_chain.py` in GitHub Actions
- Monitor migration logs for issues
- Have rollback plan ready

### 3. Production
- Test migrations on staging first
- Use `validate_migration_state.py` before running
- Keep `rollback_migration.py` available
- Monitor database health

### 4. Troubleshooting
- Start with `migration_health_check.py`
- Use `validate_migration_state.py` for state issues
- Use `nuclear_migrate.py` for connection issues
- Use `direct_migrate.py` as last resort

## File Structure

```
backend/
├── alembic/
│   ├── env.py                    # Alembic environment configuration
│   ├── versions/                 # Migration files
│   └── alembic.ini              # Alembic configuration
├── run_migration_chain.py       # Main migration runner
├── direct_migrate.py            # Direct migration (bypasses Alembic)
├── smart_migrate.py             # Smart migration with detection
├── nuclear_migrate.py           # Nuclear migration (aggressive reset)
├── simple_migrate.py            # Simple Alembic migration
├── migrate_with_retry.py        # Migration with retry logic
├── ultra_migrate.py             # Ultra migration (complete reset)
├── validate_migration_state.py  # Migration state validation
├── migration_health_check.py    # Health check system
├── rollback_migration.py        # Migration rollback
├── test_migration_system.py     # Test suite
└── MIGRATION_SYSTEM_DOCUMENTATION.md
```

## Environment Variables

- `DATABASE_URL`: Database connection string
- `ENVIRONMENT`: Environment name (development, testing, production)
- `SECRET_KEY`: Application secret key
- `JWT_SECRET`: JWT secret key

## Monitoring and Logging

All migration scripts provide detailed logging:
- Success messages for completed operations
- Warning messages for non-critical issues
- Error messages for failures
- Progress indicators for long operations

## Security Considerations

- Migration scripts run with database credentials
- No sensitive data in migration files
- Rollback scripts require confirmation for destructive operations
- All operations are logged for audit trails

## Performance Considerations

- Direct migration is fastest for fresh databases
- Smart migration is most efficient for existing databases
- Retry migration adds overhead but provides reliability
- Health checks are lightweight and can run frequently

## Future Improvements

1. **Automated Testing**: Add automated migration testing in CI/CD
2. **Monitoring**: Add migration monitoring and alerting
3. **Backup Integration**: Integrate with backup systems
4. **Performance Metrics**: Add performance monitoring
5. **Documentation**: Keep documentation updated with changes

## Support and Troubleshooting

For issues with the migration system:

1. Run `python migration_health_check.py` to diagnose issues
2. Check the logs for specific error messages
3. Use the appropriate migration script based on the issue
4. Consult this documentation for common solutions
5. Test in a development environment first

## Conclusion

The migration system provides a robust, reliable way to manage database schema changes across different environments and database types. The multi-layered approach ensures that migrations can be applied successfully even in challenging conditions, while the comprehensive tooling provides visibility and control over the migration process.
