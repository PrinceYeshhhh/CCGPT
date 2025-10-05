"""
Google Gemini AI service for generating responses
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
import structlog

from app.core.config import settings
from app.services.language_service import language_service
from app.exceptions import ExternalServiceError

logger = structlog.get_logger()


class GeminiService:
    """Google Gemini AI service for generating responses"""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini model"""
        try:
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not configured, using fallback mode")
                self.model = None
                return
                
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Gemini service", error=str(e))
            self.model = None
    
    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        sources: Optional[List[Dict[str, Any]]] = None,
        target_language: Optional[str] = None,
        tone: Optional[str] = None,
        source_type: Optional[str] = None,
        few_shots: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate AI response using Gemini"""
        try:
            # Check if model is available
            if not self.model:
                return self._generate_fallback_response(user_message, context, sources)
            
            # Prepare prompt with language support
            prompt = self._build_prompt(
                user_message=user_message,
                context=context,
                sources=sources,
                target_language=target_language,
                tone=tone,
                source_type=source_type,
                few_shots=few_shots
            )
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Extract response text
            response_text = response.text if response.text else "I apologize, but I couldn't generate a response."
            
            # Translate response if target language is specified and different from default
            if target_language and target_language != settings.DEFAULT_LANGUAGE:
                try:
                    translation_result = await language_service.translate_text(
                        response_text, 
                        target_language, 
                        settings.DEFAULT_LANGUAGE
                    )
                    response_text = translation_result["translated_text"]
                    logger.info(
                        "Response translated",
                        target_language=target_language,
                        confidence=translation_result.get("confidence", 0.8)
                    )
                except Exception as e:
                    logger.warning(
                        "Translation failed, using original response",
                        error=str(e),
                        target_language=target_language
                    )
            
            # Determine confidence based on response quality
            confidence_label = self._assess_confidence(response_text, sources)
            confidence_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
            confidence_value = confidence_map.get(confidence_label, 0.6)
            
            # Prepare sources information
            sources_info = self._format_sources(sources) if sources else []
            
            return {
                "content": response_text,
                "model_used": "gemini-pro",
                "confidence_score": confidence_label,
                "confidence": confidence_value,
                "sources_used": sources_info,
                "tokens_used": self._estimate_tokens(prompt + response_text),
                "tone": tone or "friendly",
                "source_type": source_type or ("document" if (sources_info and len(sources_info) > 0) else "generic")
            }
            
        except Exception as e:
            logger.error(
                "Gemini response generation failed",
                error=str(e),
                user_message=user_message[:100]
            )
            return self._generate_fallback_response(user_message, context, sources)
    
    def _generate_fallback_response(
        self,
        user_message: str,
        context: str = "",
        sources: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a fallback response when Gemini is unavailable"""
        try:
            # Simple keyword-based responses for common queries
            user_lower = user_message.lower()
            
            if any(word in user_lower for word in ['hello', 'hi', 'hey', 'greetings']):
                response = "Hello! I'm here to help you with your questions. How can I assist you today?"
            elif any(word in user_lower for word in ['help', 'support', 'assistance']):
                response = "I'm here to help! Please let me know what specific information you're looking for, and I'll do my best to assist you."
            elif any(word in user_lower for word in ['thank', 'thanks']):
                response = "You're welcome! Is there anything else I can help you with?"
            elif any(word in user_lower for word in ['bye', 'goodbye', 'see you']):
                response = "Goodbye! Feel free to come back anytime if you have more questions."
            elif context:
                response = f"Based on the information available, I can help you with questions related to: {context[:200]}... Please ask me something specific about this topic."
            else:
                response = "I'm here to help! Please ask me a specific question, and I'll do my best to provide you with accurate information."
            
            return {
                "content": response,
                "model_used": "fallback",
                "confidence_score": "medium",
                "sources_used": self._format_sources(sources) if sources else [],
                "tokens_used": 0
            }
            
        except Exception as e:
            logger.error("Fallback response generation failed", error=str(e))
            return {
                "content": "I apologize, but I'm having trouble processing your request right now. Please try again later or contact support if the issue persists.",
                "model_used": "fallback",
                "confidence_score": "low",
                "sources_used": [],
                "tokens_used": 0
            }
    
    def _build_prompt(
        self,
        user_message: str,
        context: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        target_language: Optional[str] = None,
        tone: Optional[str] = None,
        source_type: Optional[str] = None,
        few_shots: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build prompt for Gemini with persona, tone presets, and few-shot examples"""
        # Get language-specific instructions
        language_instruction = ""
        if target_language and target_language != settings.DEFAULT_LANGUAGE:
            language_name = language_service.get_language_name(target_language)
            language_instruction = f"Please respond in {language_name} ({target_language}). "
        
        # Tone presets (formal, friendly, playful)
        tone = (tone or "friendly").lower()
        if tone not in {"formal", "friendly", "playful"}:
            tone = "friendly"

        persona_block = (
            "You are CustomerCareGPT, an intelligent, polite, and professional customer support representative. "
            "Always sound friendly, helpful, and calm. Never use overly technical or robotic language. "
            "Never break character as a support agent. "
        )

        tone_block = {
            "formal": "Use a professional and concise tone. Avoid colloquialisms.",
            "friendly": "Use a warm, approachable tone. Keep it empathetic and supportive.",
            "playful": "Use a light, upbeat tone while staying professional and clear."
        }[tone]

        fallback_block = (
            "If you don’t have enough data, acknowledge this with empathy (e.g., 'Let me check that for you') "
            "and suggest contacting human support when appropriate."
        )

        prompt_parts = [
            persona_block,
            tone_block + "\n",
            fallback_block + "\n\n",
            f"{language_instruction}Respond in the same language as the customer's question.\n\n"
        ]

        # Few-shot examples to reinforce tone and structure
        default_few_shots = [
            {"user": "I can’t log in.", "agent": "I’m sorry to hear that! Please try resetting your password using the ‘Forgot Password’ link."},
            {"user": "How can I track my order?", "agent": "Sure! You can track your order from your dashboard under ‘My Orders.’ Would you like me to send the link?"},
            {"user": "The product I received is defective.", "agent": "I apologize for the inconvenience. Could you please share your order ID so I can check this for you?"}
        ]
        examples = few_shots if few_shots is not None else default_few_shots
        prompt_parts.append("Examples:\n")
        for ex in examples[:4]:
            u = ex.get("user", "")
            a = ex.get("agent", "")
            if u and a:
                prompt_parts.append(f"User: {u}\nAgent: {a}\n\n")
        
        if context:
            prompt_parts.extend([
                "Context (use when relevant):\n",
                "---\n",
                context,
                "\n---\n\n"
            ])
        
        prompt_parts.extend([
            "Customer question: ",
            user_message,
            "\n\n",
            "Please provide a structured, concise answer. If context lacks the answer, acknowledge and suggest next steps, including contacting support if needed."
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
