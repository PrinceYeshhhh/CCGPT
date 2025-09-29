"""
Production-grade RAG API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import structlog

from app.core.deps import get_db
from app.services.production_rag_service import (
    ProductionRAGService,
    RAGConfig,
    ResponseStyle
)
from app.services.production_vector_service import SearchMode
from app.services.production_rag_system import ChunkingStrategy
from app.schemas.rag import RAGQueryResponse, RAGQueryRequest
from app.schemas.common import SuccessResponse, ErrorResponse
from app.models.subscriptions import Subscription

logger = structlog.get_logger()

router = APIRouter()


@router.post("/process-file", response_model=SuccessResponse)
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    chunking_strategy: str = Form("semantic"),
    db: Session = Depends(get_db)
):
    """
    Process and index a file with production-grade capabilities
    
    - **file**: File to process (PDF, DOCX, TXT, MD, CSV, XLSX, JSON, HTML)
    - **workspace_id**: Workspace identifier
    - **chunk_size**: Maximum chunk size in characters
    - **chunk_overlap**: Overlap between chunks
    - **chunking_strategy**: Chunking strategy (semantic, hierarchical, adaptive, fixed_size)
    """
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/json",
            "text/html"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Create RAG service
        rag_service = ProductionRAGService(db)
        
        # Create configuration
        chunking_strategy_enum = ChunkingStrategy(chunking_strategy)
        config = RAGConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy_enum
        )
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process file
            result = await rag_service.process_file(
                file_path=temp_file_path,
                content_type=file.content_type,
                workspace_id=workspace_id,
                config=config
            )
            
            if not result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"File processing failed: {result.get('error', 'Unknown error')}"
                )
            
            # Clean up temporary file
            background_tasks.add_task(os.unlink, temp_file_path)
            
            return SuccessResponse(
                success=True,
                message="File processed successfully",
                data=result
            )
            
        except Exception as e:
            # Clean up temporary file
            background_tasks.add_task(os.unlink, temp_file_path)
            raise e
            
    except Exception as e:
        logger.error("File processing failed", error=str(e), workspace_id=workspace_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query documents using production-grade RAG
    
    - **query**: Search query
    - **workspace_id**: Workspace identifier
    - **session_id**: Optional session ID for conversation continuity
    - **search_mode**: Search mode (similarity, hybrid, semantic, multi_query, fusion)
    - **top_k**: Number of results to retrieve
    - **response_style**: Response style (conversational, technical, summarized, detailed, step_by_step)
    - **use_reranking**: Whether to use reranking
    - **stream_response**: Whether to stream the response
    """
    try:
        # Enforce subscription query quota per workspace
        sub = db.query(Subscription).filter(Subscription.workspace_id == request.workspace_id).first()
        if sub and sub.monthly_query_quota is not None and sub.queries_this_period >= sub.monthly_query_quota:
            plan_name = sub.tier.replace('_', ' ').title()
            raise HTTPException(
                status_code=402, 
                detail=f"Query quota exceeded for your {plan_name} plan. You have used {sub.queries_this_period}/{sub.monthly_query_quota} queries. Please upgrade your plan or wait for reset."
            )
        # Create RAG service
        rag_service = ProductionRAGService(db)
        
        # Create configuration
        config = RAGConfig(
            search_mode=SearchMode(request.search_mode) if request.search_mode else SearchMode.HYBRID,
            top_k=request.top_k or 10,
            similarity_threshold=request.similarity_threshold or 0.7,
            use_reranking=request.use_reranking if request.use_reranking is not None else True,
            rerank_top_k=request.rerank_top_k or 5,
            response_style=ResponseStyle(request.response_style) if request.response_style else ResponseStyle.CONVERSATIONAL,
            stream_response=request.stream_response if request.stream_response is not None else False,
            use_cache=request.use_cache if request.use_cache is not None else True
        )
        
        # Process query
        response = await rag_service.process_query(
            query=request.query,
            workspace_id=request.workspace_id,
            session_id=request.session_id,
            config=config,
            document_ids=request.document_ids or None
        )
        
        return response
        
    except Exception as e:
        logger.error("Query processing failed", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SuccessResponse)
async def search_documents(
    query: str = Form(...),
    workspace_id: str = Form(...),
    search_mode: str = Form("hybrid"),
    top_k: int = Form(10),
    similarity_threshold: float = Form(0.7),
    use_reranking: bool = Form(True),
    rerank_top_k: int = Form(5),
    db: Session = Depends(get_db)
):
    """
    Search documents without generating a response
    
    - **query**: Search query
    - **workspace_id**: Workspace identifier
    - **search_mode**: Search mode (similarity, hybrid, semantic, multi_query, fusion)
    - **top_k**: Number of results to retrieve
    - **similarity_threshold**: Minimum similarity threshold
    - **use_reranking**: Whether to use reranking
    - **rerank_top_k**: Number of results to rerank
    """
    try:
        # Create RAG service
        rag_service = ProductionRAGService(db)
        
        # Create configuration
        config = RAGConfig(
            search_mode=SearchMode(search_mode),
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            use_reranking=use_reranking,
            rerank_top_k=rerank_top_k
        )
        
        # Search documents
        results = await rag_service.search_documents(
            query=query,
            workspace_id=workspace_id,
            config=config
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata,
                "search_method": result.search_method,
                "rank": result.rank,
                "reranked_score": result.reranked_score,
                "explanation": result.explanation
            })
        
        return SuccessResponse(
            success=True,
            message=f"Found {len(formatted_results)} results",
            data={
                "results": formatted_results,
                "query": query,
                "workspace_id": workspace_id,
                "search_mode": search_mode,
                "total_results": len(formatted_results)
            }
        )
        
    except Exception as e:
        logger.error("Search failed", error=str(e), query=query)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/{workspace_id}/stats", response_model=SuccessResponse)
async def get_workspace_stats(
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """
    Get statistics for a workspace
    
    - **workspace_id**: Workspace identifier
    """
    try:
        # Create RAG service
        rag_service = ProductionRAGService(db)
        
        # Get performance stats
        stats = await rag_service.get_performance_stats()
        
        return SuccessResponse(
            success=True,
            message="Statistics retrieved successfully",
            data={
                "workspace_id": workspace_id,
                "performance_stats": stats
            }
        )
        
    except Exception as e:
        logger.error("Failed to get workspace stats", error=str(e), workspace_id=workspace_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=SuccessResponse)
async def health_check(
    db: Session = Depends(get_db)
):
    """
    Health check for the production RAG system
    """
    try:
        # Create RAG service
        rag_service = ProductionRAGService(db)
        
        # Perform health check
        health = await rag_service.health_check()
        
        return SuccessResponse(
            success=True,
            message="Health check completed",
            data=health
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workspace/{workspace_id}", response_model=SuccessResponse)
async def delete_workspace(
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete all data for a workspace
    
    - **workspace_id**: Workspace identifier
    """
    try:
        # Create RAG service
        rag_service = ProductionRAGService(db)
        
        # Delete workspace
        success = await rag_service.delete_workspace(workspace_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete workspace"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Workspace {workspace_id} deleted successfully"
        )
        
    except Exception as e:
        logger.error("Failed to delete workspace", error=str(e), workspace_id=workspace_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/{workspace_id}/batch-process", response_model=SuccessResponse)
async def batch_process_files(
    background_tasks: BackgroundTasks,
    workspace_id: str,
    files: List[UploadFile] = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    chunking_strategy: str = Form("semantic"),
    db: Session = Depends(get_db)
):
    """
    Process multiple files in batch
    
    - **workspace_id**: Workspace identifier
    - **files**: List of files to process
    - **chunk_size**: Maximum chunk size in characters
    - **chunk_overlap**: Overlap between chunks
    - **chunking_strategy**: Chunking strategy
    """
    try:
        # Create RAG service
        rag_service = ProductionRAGService(db)
        
        # Create configuration
        chunking_strategy_enum = ChunkingStrategy(chunking_strategy)
        config = RAGConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy_enum
        )
        
        # Process files
        results = []
        temp_files = []
        
        try:
            for file in files:
                # Save file temporarily
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                    temp_files.append(temp_file_path)
                
                # Process file
                result = await rag_service.process_file(
                    file_path=temp_file_path,
                    content_type=file.content_type,
                    workspace_id=workspace_id,
                    config=config
                )
                
                results.append({
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "success": result["success"],
                    "document_id": result.get("document_id"),
                    "chunks_created": result.get("chunks_created", 0),
                    "error": result.get("error")
                })
            
            # Clean up temporary files
            for temp_file in temp_files:
                background_tasks.add_task(os.unlink, temp_file)
            
            # Calculate summary
            successful = sum(1 for r in results if r["success"])
            failed = len(results) - successful
            total_chunks = sum(r.get("chunks_created", 0) for r in results)
            
            return SuccessResponse(
                success=True,
                message=f"Batch processing completed: {successful} successful, {failed} failed",
                data={
                    "workspace_id": workspace_id,
                    "total_files": len(files),
                    "successful": successful,
                    "failed": failed,
                    "total_chunks": total_chunks,
                    "results": results
                }
            )
            
        except Exception as e:
            # Clean up temporary files
            for temp_file in temp_files:
                background_tasks.add_task(os.unlink, temp_file)
            raise e
            
    except Exception as e:
        logger.error("Batch processing failed", error=str(e), workspace_id=workspace_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/{workspace_id}/documents", response_model=SuccessResponse)
async def list_workspace_documents(
    workspace_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List documents in a workspace
    
    - **workspace_id**: Workspace identifier
    - **limit**: Maximum number of documents to return
    - **offset**: Number of documents to skip
    """
    try:
        from app.models.document import Document
        
        # Query documents
        documents = db.query(Document).filter(
            Document.workspace_id == workspace_id
        ).offset(offset).limit(limit).all()
        
        # Format results
        formatted_documents = []
        for doc in documents:
            formatted_documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at
            })
        
        return SuccessResponse(
            success=True,
            message=f"Retrieved {len(formatted_documents)} documents",
            data={
                "workspace_id": workspace_id,
                "documents": formatted_documents,
                "total": len(formatted_documents),
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error("Failed to list documents", error=str(e), workspace_id=workspace_id)
        raise HTTPException(status_code=500, detail=str(e))
