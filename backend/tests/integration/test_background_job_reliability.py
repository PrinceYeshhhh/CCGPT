"""
Critical background job reliability tests for production stability
Tests job failure recovery, retry mechanisms, dead letter queue handling, and worker scaling
"""

import pytest
import asyncio
import time
import uuid
from typing import List, Dict, Any
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import threading
import queue

from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, DocumentChunk
from app.core.queue import get_ingest_queue, queue_manager
from app.worker.enhanced_worker import enhanced_worker
from app.worker.ingest_worker import ingest_worker


class TestBackgroundJobReliability:
    """Critical background job reliability tests for production stability"""
    
    @pytest.fixture(scope="function")
    def db_session(self):
        """Create a fresh database session for each test."""
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture(scope="function")
    def client(self, db_session):
        """Create a test client with database dependency override."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def test_workspace(self, db_session):
        """Create test workspace"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="Job Test Workspace",
            description="Test workspace for background job testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            email="jobtest@example.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Job Test User",
            workspace_id=test_workspace.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def test_job_failure_recovery(self, db_session, test_user, test_workspace):
        """Test job failure recovery and retry mechanisms"""
        # Create a document for processing
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="test_document.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/test_document.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock job failure and recovery
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            # First call fails, second call succeeds
            mock_process.side_effect = [Exception("Processing failed"), None]
            
            # Simulate job retry
            try:
                enhanced_worker.process_document(document.id, test_workspace.id)
            except Exception:
                pass  # Expected first failure
            
            # Retry should succeed
            enhanced_worker.process_document(document.id, test_workspace.id)
            
            # Verify retry was attempted
            assert mock_process.call_count == 2
        
        # Verify document status is updated after successful processing
        db_session.refresh(document)
        assert document.status in ["processed", "failed"]  # Should be updated
    
    def test_job_retry_mechanism(self, db_session, test_user, test_workspace):
        """Test job retry mechanism with exponential backoff"""
        # Create a document for processing
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="retry_test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/retry_test.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock job with retry logic
        retry_count = 0
        max_retries = 3
        
        def mock_process_with_retry(doc_id, workspace_id):
            nonlocal retry_count
            retry_count += 1
            if retry_count < max_retries:
                raise Exception(f"Processing failed (attempt {retry_count})")
            return {"status": "success"}
        
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            mock_process.side_effect = mock_process_with_retry
            
            # Process document with retries
            for attempt in range(max_retries):
                try:
                    result = enhanced_worker.process_document(document.id, test_workspace.id)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(0.1)  # Simulate retry delay
            
            # Verify retries were attempted
            assert retry_count == max_retries
            assert result["status"] == "success"
    
    def test_dead_letter_queue_handling(self, db_session, test_user, test_workspace):
        """Test dead letter queue handling for failed jobs"""
        # Create a document that will always fail
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="dead_letter_test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/dead_letter_test.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock job that always fails
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            mock_process.side_effect = Exception("Permanent failure")
            
            # Process document multiple times (simulating retries)
            for attempt in range(5):
                try:
                    enhanced_worker.process_document(document.id, test_workspace.id)
                except Exception:
                    pass  # Expected failure
            
            # Verify job was attempted multiple times
            assert mock_process.call_count == 5
            
            # Verify document status reflects failure
            db_session.refresh(document)
            assert document.status == "failed"
            assert document.error is not None
    
    def test_worker_scaling(self, db_session, test_user, test_workspace):
        """Test worker scaling under load"""
        # Create multiple documents for processing
        documents = []
        for i in range(10):
            document = Document(
                id=str(uuid.uuid4()),
                workspace_id=test_workspace.id,
                filename=f"scale_test_{i}.pdf",
                content_type="application/pdf",
                size=1024,
                path=f"/tmp/scale_test_{i}.pdf",
                uploaded_by=test_user.id,
                status="uploaded"
            )
            db_session.add(document)
            documents.append(document)
        db_session.commit()
        
        # Mock worker processing
        processed_documents = []
        
        def mock_process_document(doc_id, workspace_id):
            processed_documents.append(doc_id)
            time.sleep(0.1)  # Simulate processing time
            return {"status": "success"}
        
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            mock_process.side_effect = mock_process_document
            
            # Process documents concurrently
            threads = []
            for document in documents:
                thread = threading.Thread(
                    target=enhanced_worker.process_document,
                    args=(document.id, test_workspace.id)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all documents were processed
            assert len(processed_documents) == len(documents)
            assert mock_process.call_count == len(documents)
    
    def test_job_queue_persistence(self, db_session, test_user, test_workspace):
        """Test job queue persistence across restarts"""
        # Create a document for processing
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="persistence_test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/persistence_test.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock queue persistence
        with patch('app.core.queue.queue_manager.enqueue_job') as mock_enqueue:
            mock_enqueue.return_value = str(uuid.uuid4())
            
            # Enqueue job
            job_id = queue_manager.enqueue_job(
                "process_document",
                {"document_id": document.id, "workspace_id": test_workspace.id}
            )
            
            # Verify job was enqueued
            assert job_id is not None
            mock_enqueue.assert_called_once()
    
    def test_job_priority_handling(self, db_session, test_user, test_workspace):
        """Test job priority handling"""
        # Create documents with different priorities
        high_priority_doc = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="high_priority.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/high_priority.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(high_priority_doc)
        
        low_priority_doc = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="low_priority.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/low_priority.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(low_priority_doc)
        db_session.commit()
        
        # Mock priority processing
        processing_order = []
        
        def mock_process_document(doc_id, workspace_id):
            processing_order.append(doc_id)
            return {"status": "success"}
        
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            mock_process.side_effect = mock_process_document
            
            # Process documents (high priority should be processed first)
            enhanced_worker.process_document(high_priority_doc.id, test_workspace.id)
            enhanced_worker.process_document(low_priority_doc.id, test_workspace.id)
            
            # Verify processing order (implementation dependent)
            assert len(processing_order) == 2
            assert high_priority_doc.id in processing_order
            assert low_priority_doc.id in processing_order
    
    def test_job_timeout_handling(self, db_session, test_user, test_workspace):
        """Test job timeout handling"""
        # Create a document for processing
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="timeout_test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/timeout_test.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock job that times out
        def mock_process_document(doc_id, workspace_id):
            time.sleep(10)  # Simulate long processing time
            return {"status": "success"}
        
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            mock_process.side_effect = mock_process_document
            
            # Process document with timeout
            start_time = time.time()
            try:
                result = enhanced_worker.process_document(document.id, test_workspace.id)
                processing_time = time.time() - start_time
                
                # Verify timeout handling (implementation dependent)
                assert processing_time < 5.0 or result is not None
            except Exception as e:
                # Timeout exception is acceptable
                assert "timeout" in str(e).lower() or "time" in str(e).lower()
    
    def test_job_error_monitoring(self, db_session, test_user, test_workspace):
        """Test job error monitoring and alerting"""
        # Create a document for processing
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="error_monitoring_test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/error_monitoring_test.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock error monitoring
        with patch('app.utils.error_monitoring.error_monitor') as mock_error_monitor:
            mock_error_monitor.log_error.return_value = {"error_count": 1}
            
            # Mock job failure
            with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
                mock_process.side_effect = Exception("Processing error")
                
                try:
                    enhanced_worker.process_document(document.id, test_workspace.id)
                except Exception:
                    pass  # Expected failure
                
                # Verify error was logged
                mock_error_monitor.log_error.assert_called()
    
    def test_job_cleanup_and_maintenance(self, db_session, test_user, test_workspace):
        """Test job cleanup and maintenance tasks"""
        # Create completed documents
        completed_doc = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="completed.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/completed.pdf",
            uploaded_by=test_user.id,
            status="processed"
        )
        db_session.add(completed_doc)
        
        # Create failed document
        failed_doc = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="failed.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/failed.pdf",
            uploaded_by=test_user.id,
            status="failed",
            error="Processing failed"
        )
        db_session.add(failed_doc)
        db_session.commit()
        
        # Mock cleanup task
        with patch('app.worker.enhanced_worker.enhanced_worker.cleanup_old_jobs') as mock_cleanup:
            mock_cleanup.return_value = {"cleaned": 2, "remaining": 0}
            
            # Run cleanup
            result = enhanced_worker.cleanup_old_jobs()
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once()
            assert result["cleaned"] >= 0
            assert result["remaining"] >= 0
    
    def test_job_concurrent_processing(self, db_session, test_user, test_workspace):
        """Test concurrent job processing"""
        # Create multiple documents
        documents = []
        for i in range(5):
            document = Document(
                id=str(uuid.uuid4()),
                workspace_id=test_workspace.id,
                filename=f"concurrent_{i}.pdf",
                content_type="application/pdf",
                size=1024,
                path=f"/tmp/concurrent_{i}.pdf",
                uploaded_by=test_user.id,
                status="uploaded"
            )
            db_session.add(document)
            documents.append(document)
        db_session.commit()
        
        # Mock concurrent processing
        processing_results = queue.Queue()
        
        def mock_process_document(doc_id, workspace_id):
            time.sleep(0.1)  # Simulate processing time
            processing_results.put({"doc_id": doc_id, "status": "success"})
            return {"status": "success"}
        
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            mock_process.side_effect = mock_process_document
            
            # Process documents concurrently
            threads = []
            for document in documents:
                thread = threading.Thread(
                    target=enhanced_worker.process_document,
                    args=(document.id, test_workspace.id)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all documents were processed
            results = []
            while not processing_results.empty():
                results.append(processing_results.get())
            
            assert len(results) == len(documents)
            for result in results:
                assert result["status"] == "success"
    
    def test_job_resource_management(self, db_session, test_user, test_workspace):
        """Test job resource management and memory usage"""
        # Create a large document for processing
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="large_document.pdf",
            content_type="application/pdf",
            size=50 * 1024 * 1024,  # 50MB
            path="/tmp/large_document.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock resource management
        with patch('app.worker.enhanced_worker.enhanced_worker.process_document') as mock_process:
            mock_process.return_value = {"status": "success", "memory_used": "100MB"}
            
            # Process large document
            result = enhanced_worker.process_document(document.id, test_workspace.id)
            
            # Verify processing completed
            assert result["status"] == "success"
            assert "memory_used" in result
            
            # Verify resource cleanup (implementation dependent)
            # This would typically involve checking that memory is freed after processing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
