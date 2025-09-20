"""
Google Gemini AI service for generating responses
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class GeminiService:
    """Google Gemini AI service for generating responses"""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini model"""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Gemini service", error=str(e))
            raise
    
    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        sources: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate AI response using Gemini"""
        try:
            # Prepare prompt
            prompt = self._build_prompt(user_message, context, sources)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Extract response text
            response_text = response.text if response.text else "I apologize, but I couldn't generate a response."
            
            # Determine confidence based on response quality
            confidence = self._assess_confidence(response_text, sources)
            
            # Prepare sources information
            sources_info = self._format_sources(sources) if sources else []
            
            return {
                "content": response_text,
                "model_used": "gemini-pro",
                "confidence_score": confidence,
                "sources_used": sources_info,
                "tokens_used": self._estimate_tokens(prompt + response_text)
            }
            
        except Exception as e:
            logger.error(
                "Gemini response generation failed",
                error=str(e),
                user_message=user_message[:100]
            )
            raise
    
    def _build_prompt(
        self,
        user_message: str,
        context: str,
        sources: List[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for Gemini"""
        prompt_parts = [
            "You are CustomerCareGPT, an intelligent customer support assistant. ",
            "Your role is to provide helpful, accurate, and friendly responses to customer inquiries ",
            "based on the provided knowledge base. Follow these guidelines:\n\n",
            
            "1. Be helpful, professional, and empathetic\n",
            "2. Base your answers on the provided context when available\n",
            "3. If you don't know something, say so clearly\n",
            "4. Keep responses concise but comprehensive\n",
            "5. Use a friendly, conversational tone\n",
            "6. If relevant, provide specific examples or steps\n\n"
        ]
        
        if context:
            prompt_parts.extend([
                "Here is relevant information from our knowledge base:\n",
                "---\n",
                context,
                "\n---\n\n"
            ])
        
        prompt_parts.extend([
            "Customer question: ",
            user_message,
            "\n\n",
            "Please provide a helpful response based on the information above. ",
            "If the context doesn't contain relevant information, let the customer know ",
            "and suggest they contact support for more specific help."
        ])
        
        return "".join(prompt_parts)
    
    def _assess_confidence(
        self,
        response_text: str,
        sources: List[Dict[str, Any]] = None
    ) -> str:
        """Assess confidence level of the response"""
        if not sources or len(sources) == 0:
            return "low"
        
        # Check if response contains uncertainty indicators
        uncertainty_indicators = [
            "i don't know", "i'm not sure", "i can't find",
            "i'm unable to", "i don't have", "i'm not certain"
        ]
        
        response_lower = response_text.lower()
        has_uncertainty = any(indicator in response_lower for indicator in uncertainty_indicators)
        
        if has_uncertainty:
            return "low"
        
        # Check source quality
        high_quality_sources = sum(1 for source in sources if source.get("similarity_score", 0) > 0.8)
        
        if high_quality_sources >= 2:
            return "high"
        elif high_quality_sources >= 1:
            return "medium"
        else:
            return "low"
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for response"""
        formatted_sources = []
        
        for source in sources:
            metadata = source.get("metadata", {})
            formatted_sources.append({
                "content": source["content"][:200] + "..." if len(source["content"]) > 200 else source["content"],
                "similarity_score": source.get("similarity_score", 0),
                "section_title": metadata.get("section_title", ""),
                "document_id": metadata.get("document_id"),
                "chunk_index": metadata.get("chunk_index")
            })
        
        return formatted_sources
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
    
    async def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            test_response = self.model.generate_content("Hello, this is a test.")
            return test_response.text is not None
        except Exception as e:
            logger.error("Gemini connection test failed", error=str(e))
            return False
