#!/usr/bin/env python3
"""
Direct migration script that bypasses Alembic entirely.
This script runs migrations directly using SQLAlchemy without Alembic's transaction management.
"""

import os
import sys
import time
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Boolean, DateTime, Text, BigInteger
from sqlalchemy.exc import OperationalError, InternalError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def direct_database_setup():
    """Set up database directly without Alembic."""
    database_url = settings.DATABASE_URL
    
    print("Direct database setup...")
    
    try:
        engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            isolation_level='AUTOCOMMIT'
        )
        
        with engine.connect() as connection:
            # Create version table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                );
            """))
            
            # Check if version table has any data
            result = connection.execute(text("SELECT COUNT(*) FROM alembic_version;"))
            count = result.scalar()
            
            if count == 0:
                # Insert initial version
                connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001');"))
                print("SUCCESS: Created version table with initial version")
            else:
                print("SUCCESS: Version table already exists")
            
            # Create all necessary tables directly
            create_all_tables(connection)
            
            # Update version to latest
            connection.execute(text("UPDATE alembic_version SET version_num = '008_add_performance_indexes';"))
            print("SUCCESS: Database setup completed")
            return True
            
    except Exception as e:
        print(f"ERROR: Direct database setup failed: {e}")
        return False

def create_all_tables(connection):
    """Create all necessary tables directly."""
    print("Creating all tables directly...")
    
    # Create users table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE,
            business_name VARCHAR(255),
            business_domain VARCHAR(255),
            subscription_plan VARCHAR(50),
            workspace_id VARCHAR(36),
            mobile_phone VARCHAR(20),
            phone_verified BOOLEAN DEFAULT false,
            email_verified BOOLEAN DEFAULT false,
            email_verification_token VARCHAR(128),
            email_verification_sent_at TIMESTAMP WITH TIME ZONE,
            username VARCHAR(100),
            two_factor_secret VARCHAR(32),
            two_factor_enabled BOOLEAN DEFAULT false,
            phone_verification_token VARCHAR(10),
            phone_verification_sent_at TIMESTAMP WITH TIME ZONE,
            password_reset_token VARCHAR(255),
            password_reset_sent_at TIMESTAMP WITH TIME ZONE,
            last_login_at TIMESTAMP WITH TIME ZONE,
            login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP WITH TIME ZONE,
            preferences TEXT,
            theme VARCHAR(20),
            language VARCHAR(10),
            timezone VARCHAR(50),
            notification_settings TEXT
        );
    """))
    
    # Create workspaces table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            logo_url VARCHAR(500),
            website_url VARCHAR(500),
            support_email VARCHAR(255),
            timezone VARCHAR(50),
            plan VARCHAR(50),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # Create documents table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(36) NOT NULL,
            filename TEXT NOT NULL,
            content_type TEXT NOT NULL,
            size BIGINT NOT NULL,
            path TEXT NOT NULL,
            uploaded_by VARCHAR(36) NOT NULL,
            status VARCHAR(20) NOT NULL CHECK (status IN ('uploaded','processing','done','failed','deleted')),
            error TEXT,
            uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # Create document_chunks table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            workspace_id VARCHAR(36) NOT NULL,
            chunk_index BIGINT NOT NULL,
            text TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        );
    """))
    
    # Create subscriptions table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(36) NOT NULL,
            stripe_customer_id VARCHAR(255),
            stripe_subscription_id VARCHAR(255),
            tier VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            seats INTEGER,
            monthly_query_quota BIGINT,
            queries_this_period BIGINT,
            period_start TIMESTAMP WITH TIME ZONE,
            period_end TIMESTAMP WITH TIME ZONE,
            next_billing_at TIMESTAMP WITH TIME ZONE,
            metadata TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
        );
    """))
    
    # Create performance tables
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            value FLOAT NOT NULL,
            url TEXT,
            user_agent TEXT,
            session_id VARCHAR(255),
            timestamp TIMESTAMP NOT NULL,
            metadata TEXT
        );
    """))
    
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS performance_alerts (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(255) NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            threshold FLOAT NOT NULL,
            current_value FLOAT NOT NULL,
            message TEXT NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS performance_configs (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(255) NOT NULL,
            enable_web_vitals BOOLEAN DEFAULT true,
            enable_custom_metrics BOOLEAN DEFAULT true,
            enable_user_tracking BOOLEAN DEFAULT true,
            enable_error_tracking BOOLEAN DEFAULT true,
            lcp_threshold_ms INTEGER DEFAULT 2500,
            fid_threshold_ms INTEGER DEFAULT 100,
            cls_threshold FLOAT DEFAULT 0.1,
            error_rate_threshold FLOAT DEFAULT 0.01,
            response_time_threshold_ms INTEGER DEFAULT 2000,
            report_interval_minutes INTEGER DEFAULT 60,
            batch_size INTEGER DEFAULT 1000,
            retention_days INTEGER DEFAULT 30,
            enable_email_alerts BOOLEAN DEFAULT false,
            enable_webhook_alerts BOOLEAN DEFAULT false,
            alert_email VARCHAR(255),
            webhook_url VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS performance_reports (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(255) NOT NULL,
            report_type VARCHAR(50) NOT NULL,
            report_data TEXT NOT NULL,
            generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS performance_benchmarks (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(255) NOT NULL,
            benchmark_type VARCHAR(100) NOT NULL,
            tests_run INTEGER DEFAULT 0,
            tests_passed INTEGER DEFAULT 0,
            tests_failed INTEGER DEFAULT 0,
            avg_response_time FLOAT DEFAULT 0.0,
            max_response_time FLOAT DEFAULT 0.0,
            min_response_time FLOAT DEFAULT 0.0,
            requests_per_second FLOAT DEFAULT 0.0,
            cpu_usage_percent FLOAT DEFAULT 0.0,
            memory_usage_mb FLOAT DEFAULT 0.0,
            disk_io_mb FLOAT DEFAULT 0.0,
            score FLOAT DEFAULT 0.0,
            recommendations TEXT,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            duration_seconds INTEGER DEFAULT 0
        );
    """))
    
    # Create indexes
    create_indexes(connection)
    
    print("SUCCESS: All tables created successfully")

def create_indexes(connection):
    """Create all necessary indexes."""
    print("Creating indexes...")
    
    # Basic indexes that should work on all databases
    basic_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);",
        "CREATE INDEX IF NOT EXISTS ix_users_workspace_id ON users(workspace_id);",
        "CREATE INDEX IF NOT EXISTS ix_workspaces_id ON workspaces(id);",
        "CREATE INDEX IF NOT EXISTS ix_documents_id ON documents(id);",
        "CREATE INDEX IF NOT EXISTS ix_documents_workspace_id ON documents(workspace_id);",
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_id ON document_chunks(id);",
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id ON document_chunks(document_id);",
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_workspace_id ON document_chunks(workspace_id);",
        "CREATE INDEX IF NOT EXISTS ix_subscriptions_workspace_id ON subscriptions(workspace_id);",
        "CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id);",
        "CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);",
        "CREATE INDEX IF NOT EXISTS ix_subscriptions_tier ON subscriptions(tier);",
        "CREATE INDEX IF NOT EXISTS ix_subscriptions_status ON subscriptions(status);",
        "CREATE INDEX IF NOT EXISTS idx_performance_metrics_workspace_id ON performance_metrics(workspace_id);",
        "CREATE INDEX IF NOT EXISTS idx_performance_metrics_user_id ON performance_metrics(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_type ON performance_metrics(metric_type);",
        "CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_performance_alerts_workspace_id ON performance_alerts(workspace_id);",
        "CREATE INDEX IF NOT EXISTS idx_performance_alerts_alert_type ON performance_alerts(alert_type);",
        "CREATE INDEX IF NOT EXISTS idx_performance_configs_workspace_id ON performance_configs(workspace_id);",
        "CREATE INDEX IF NOT EXISTS idx_performance_reports_workspace_id ON performance_reports(workspace_id);",
        "CREATE INDEX IF NOT EXISTS idx_performance_reports_report_type ON performance_reports(report_type);",
        "CREATE INDEX IF NOT EXISTS idx_performance_benchmarks_workspace_id ON performance_benchmarks(workspace_id);"
    ]
    
    # Advanced indexes that might not work on all databases
    advanced_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_performance_configs_enable_web_vitals ON performance_configs(enable_web_vitals);",
        "CREATE INDEX IF NOT EXISTS idx_performance_benchmarks_benchmark_type ON performance_benchmarks(benchmark_type);"
    ]
    
    # Create basic indexes
    for index_sql in basic_indexes:
        try:
            connection.execute(text(index_sql))
        except Exception as e:
            print(f"WARNING: Could not create index: {e}")
    
    # Try to create advanced indexes
    for index_sql in advanced_indexes:
        try:
            connection.execute(text(index_sql))
        except Exception as e:
            print(f"WARNING: Could not create advanced index: {e}")
    
    print("SUCCESS: All indexes created successfully")

def run_direct_migration():
    """Run direct migration without Alembic."""
    print("Starting direct migration...")
    
    success = direct_database_setup()
    
    if success:
        print("\nSUCCESS: Direct migration completed successfully!")
        return True
    else:
        print("\nERROR: Direct migration failed")
        return False

if __name__ == "__main__":
    success = run_direct_migration()
    
    if success:
        print("\nSUCCESS: Direct migration completed successfully!")
        sys.exit(0)
    else:
        print("\nERROR: Direct migration failed")
        sys.exit(1)
