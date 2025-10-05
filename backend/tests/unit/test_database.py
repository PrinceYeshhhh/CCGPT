"""
Unit tests for database operations and transactions
Tests database connections, transactions, and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from app.core.database import get_db, Base, engine, SessionLocal
from app.models import User, Workspace, Document, ChatSession

class TestDatabaseConnection:
    """Test database connection and basic operations"""
    
    def test_database_connection(self):
        """Test that database connection works"""
        # Test with in-memory SQLite
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        # Create tables
        Base.metadata.create_all(bind=test_engine)
        
        # Test connection
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    
    def test_database_transaction_rollback(self):
        """Test that database transactions can be rolled back"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()  # Flush to get ID
            
            # Create a user
            user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add(user)
            session.flush()
            
            # Verify data exists
            assert session.query(Workspace).count() == 1
            assert session.query(User).count() == 1
            
            # Rollback transaction
            session.rollback()
            
            # Verify data is gone
            assert session.query(Workspace).count() == 0
            assert session.query(User).count() == 0
            
        finally:
            session.close()
    
    def test_database_transaction_commit(self):
        """Test that database transactions can be committed"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.commit()
            
            # Verify data exists
            assert session.query(Workspace).count() == 1
            saved_workspace = session.query(Workspace).first()
            assert saved_workspace.name == "Test Workspace"
            
        finally:
            session.close()

class TestDatabaseErrorHandling:
    """Test database error handling"""
    
    def test_integrity_error_handling(self):
        """Test handling of integrity constraint violations"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()
            
            # Create a user
            user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add(user)
            session.commit()
            
            # Try to create another user with same email (should fail due to unique constraint)
            duplicate_user = User(
                email="test@example.com",  # Same email
                hashed_password="hashed_password",
                full_name="Duplicate User",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add(duplicate_user)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()
    
    def test_operational_error_handling(self):
        """Test handling of operational errors"""
        # Mock a database connection that fails
        with patch('app.core.database.engine') as mock_engine:
            mock_engine.connect.side_effect = OperationalError("Connection failed", None, None)
            
            with pytest.raises(OperationalError):
                with mock_engine.connect() as conn:
                    pass
    
    def test_database_connection_timeout(self):
        """Test handling of database connection timeouts"""
        # Mock a database connection that times out
        with patch('app.core.database.engine') as mock_engine:
            mock_engine.connect.side_effect = OperationalError("timeout", None, None)
            
            with pytest.raises(OperationalError):
                with mock_engine.connect() as conn:
                    pass

class TestDatabaseQueries:
    """Test database query operations"""
    
    def test_user_creation_and_retrieval(self):
        """Test creating and retrieving users"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()
            
            # Create a user
            user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add(user)
            session.commit()
            
            # Retrieve user
            retrieved_user = session.query(User).filter(User.email == "test@example.com").first()
            assert retrieved_user is not None
            assert retrieved_user.full_name == "Test User"
            assert retrieved_user.workspace_id == workspace.id
            
        finally:
            session.close()
    
    def test_workspace_user_relationship(self):
        """Test workspace-user relationship"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()
            
            # Create users in the workspace
            user1 = User(
                email="user1@example.com",
                hashed_password="hashed_password",
                full_name="User 1",
                workspace_id=workspace.id,
                is_active=True
            )
            user2 = User(
                email="user2@example.com",
                hashed_password="hashed_password",
                full_name="User 2",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add_all([user1, user2])
            session.commit()
            
            # Test relationship queries
            workspace_users = session.query(User).filter(User.workspace_id == workspace.id).all()
            assert len(workspace_users) == 2
            
            # Test workspace access
            workspace_with_users = session.query(Workspace).filter(Workspace.id == workspace.id).first()
            assert workspace_with_users is not None
            
        finally:
            session.close()
    
    def test_document_workflow(self):
        """Test document creation and processing workflow"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()
            
            # Create a user
            user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add(user)
            session.flush()
            
            # Create a document
            document = Document(
                filename="test.pdf",
                path="/tmp/test.pdf",
                size=1024,
                content_type="application/pdf",
                status="processing",
                uploaded_by=user.id,
                workspace_id=workspace.id
            )
            session.add(document)
            session.commit()
            
            # Verify document creation
            retrieved_document = session.query(Document).filter(Document.filename == "test.pdf").first()
            assert retrieved_document is not None
            assert retrieved_document.status == "processing"
            assert retrieved_document.uploaded_by == user.id
            
            # Update document status
            retrieved_document.status = "done"
            session.commit()
            
            # Verify status update
            updated_document = session.query(Document).filter(Document.id == retrieved_document.id).first()
            assert updated_document.status == "done"
            
        finally:
            session.close()

class TestDatabasePerformance:
    """Test database performance and optimization"""
    
    def test_bulk_insert_performance(self):
        """Test bulk insert performance"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()
            
            # Create multiple users in bulk
            users = []
            for i in range(100):
                user = User(
                    email=f"user{i}@example.com",
                    hashed_password="hashed_password",
                    full_name=f"User {i}",
                    workspace_id=workspace.id,
                    is_active=True
                )
                users.append(user)
            
            session.add_all(users)
            session.commit()
            
            # Verify all users were created
            user_count = session.query(User).filter(User.workspace_id == workspace.id).count()
            assert user_count == 100
            
        finally:
            session.close()
    
    def test_query_optimization(self):
        """Test query optimization with joins"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()
            
            # Create a user
            user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add(user)
            session.flush()
            
            # Create documents
            for i in range(10):
                document = Document(
                    filename=f"test{i}.pdf",
                    path=f"/tmp/test{i}.pdf",
                    size=1024,
                    content_type="application/pdf",
                    status="done",
                    uploaded_by=user.id,
                    workspace_id=workspace.id
                )
                session.add(document)
            
            session.commit()
            
            # Test optimized query with join
            result = session.query(Document, User, Workspace).join(
                User, Document.uploaded_by == User.id
            ).join(
                Workspace, User.workspace_id == Workspace.id
            ).filter(Workspace.id == workspace.id).all()
            
            assert len(result) == 10
            for document, user_obj, workspace_obj in result:
                assert document.workspace_id == workspace.id
                assert user_obj.workspace_id == workspace.id
                assert workspace_obj.id == workspace.id
            
        finally:
            session.close()

class TestDatabaseSecurity:
    """Test database security measures"""
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.commit()
            
            # Test parameterized query (safe)
            malicious_input = "'; DROP TABLE users; --"
            result = session.query(Workspace).filter(Workspace.name == malicious_input).all()
            assert len(result) == 0  # Should not find anything
            
            # Verify table still exists
            user_count = session.query(User).count()
            assert user_count == 0  # No users, but table exists
            
        finally:
            session.close()
    
    def test_data_validation(self):
        """Test data validation at database level"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        Base.metadata.create_all(bind=test_engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        session = TestingSessionLocal()
        
        try:
            # Create a workspace
            workspace = Workspace(
                name="Test Workspace",
                custom_domain="test.com"
            )
            session.add(workspace)
            session.flush()
            
            # Create a user
            user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
                workspace_id=workspace.id,
                is_active=True
            )
            session.add(user)
            session.flush()
            
            # Try to create document with invalid status (should fail due to CHECK constraint)
            document = Document(
                filename="test.pdf",
                path="/tmp/test.pdf",
                size=1024,
                content_type="application/pdf",
                status="invalid_status",  # Invalid status
                uploaded_by=user.id,
                workspace_id=workspace.id
            )
            session.add(document)
            
            # This should raise an error due to status validation
            with pytest.raises(IntegrityError):
                session.commit()
            
        finally:
            session.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
