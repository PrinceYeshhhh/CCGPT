"""
Multi-language support service with detection and translation
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
import structlog
try:
    from googletrans import Translator  # optional in dev/tests
except Exception:  # pragma: no cover
    Translator = None
import langdetect
from langdetect import DetectorFactory

from app.core.config import settings
from app.exceptions import ExternalServiceError, ConfigurationError

logger = structlog.get_logger()

# Set seed for consistent language detection
DetectorFactory.seed = 0


class LanguageService:
    """Service for language detection and translation"""
    
    def __init__(self):
        self.translator = None
        self.supported_languages = settings.SUPPORTED_LANGUAGES
        self.default_language = settings.DEFAULT_LANGUAGE
        self.auto_detect = settings.AUTO_DETECT_LANGUAGE
        self._initialize_translator()
    
    def _initialize_translator(self):
        """Initialize Google Translate client"""
        try:
            if Translator is not None:
                self.translator = Translator()
                logger.info("Language service initialized successfully")
            else:
                self.translator = None
                logger.warning("googletrans not installed; translation disabled")
        except Exception as e:
            logger.warning("Failed to initialize translation; continuing without", error=str(e))
            self.translator = None
    
    async def detect_language(self, text: str) -> str:
        """Detect the language of the given text"""
        try:
            if not text or len(text.strip()) < 3:
                return self.default_language
            
            # Use langdetect for better accuracy
            detected_lang = langdetect.detect(text)
            
            # Map to supported languages
            if detected_lang in self.supported_languages:
                return detected_lang
            else:
                # Try to find a close match
                lang_mapping = {
                    'zh-cn': 'zh', 'zh-tw': 'zh',
                    'pt-br': 'pt', 'pt-pt': 'pt',
                    'en-us': 'en', 'en-gb': 'en',
                    'es-es': 'es', 'es-mx': 'es',
                    'fr-fr': 'fr', 'fr-ca': 'fr',
                    'de-de': 'de', 'de-at': 'de',
                    'it-it': 'it', 'it-ch': 'it',
                    'ru-ru': 'ru', 'ru-ua': 'ru',
                    'ja-jp': 'ja', 'ko-kr': 'ko'
                }
                
                mapped_lang = lang_mapping.get(detected_lang, detected_lang.split('-')[0])
                if mapped_lang in self.supported_languages:
                    return mapped_lang
                
                logger.warning(
                    "Unsupported language detected",
                    detected_lang=detected_lang,
                    text_preview=text[:50]
                )
                return self.default_language
                
        except Exception as e:
            logger.error("Language detection failed", error=str(e), text_preview=text[:50])
            return self.default_language
    
    async def translate_text(
        self, 
        text: str, 
        target_language: str, 
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to target language"""
        try:
            if not text or not text.strip():
                return {
                    "original_text": text,
                    "translated_text": text,
                    "source_language": source_language or self.default_language,
                    "target_language": target_language,
                    "confidence": 1.0
                }
            
            # Auto-detect source language if not provided
            if not source_language:
                source_language = await self.detect_language(text)
            
            # Skip translation if source and target are the same
            if source_language == target_language:
                return {
                    "original_text": text,
                    "translated_text": text,
                    "source_language": source_language,
                    "target_language": target_language,
                    "confidence": 1.0
                }
            
            # Translate using Google Translate
            if self.translator is None:
                # Fallback: no-op translation
                return {
                    "original_text": text,
                    "translated_text": text,
                    "source_language": source_language,
                    "target_language": target_language,
                    "confidence": 1.0
                }
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.translator.translate,
                text,
                target_language,
                source_language
            )
            return {
                "original_text": text,
                "translated_text": result.text,
                "source_language": getattr(result, 'src', source_language or self.default_language),
                "target_language": target_language,
                "confidence": getattr(result, 'confidence', 0.8)
            }
            
        except Exception as e:
            logger.error(
                "Translation failed",
                error=str(e),
                text_preview=text[:50],
                target_language=target_language
            )
            raise ExternalServiceError(
                service="Google Translate",
                message="Translation failed",
                details={
                    "text_preview": text[:50],
                    "target_language": target_language,
                    "source_language": source_language,
                    "error": str(e)
                }
            )
    
    async def translate_batch(
        self, 
        texts: List[str], 
        target_language: str, 
        source_language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Translate multiple texts to target language"""
        try:
            if not texts:
                return []
            
            # Process translations in parallel
            tasks = [
                self.translate_text(text, target_language, source_language)
                for text in texts
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle Any exceptions
            translated_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "Translation failed for text in batch",
                        error=str(result),
                        text_index=i,
                        text_preview=texts[i][:50]
                    )
                    # Return original text as fallback
                    translated_results.append({
                        "original_text": texts[i],
                        "translated_text": texts[i],
                        "source_language": source_language or self.default_language,
                        "target_language": target_language,
                        "confidence": 0.0,
                        "error": str(result)
                    })
                else:
                    translated_results.append(result)
            
            return translated_results
            
        except Exception as e:
            logger.error("Batch translation failed", error=str(e))
            raise ExternalServiceError(
                service="Google Translate",
                message="Batch translation failed",
                details={"texts_count": len(texts), "error": str(e)}
            )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported"""
        return language in self.supported_languages
    
    def get_language_name(self, language_code: str) -> str:
        """Get human-readable language name"""
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean'
        }
        return language_names.get(language_code, language_code.upper())
    
    async def get_text_language_info(self, text: str) -> Dict[str, Any]:
        """Get comprehensive language information for text"""
        try:
            detected_lang = await self.detect_language(text)
            return {
                "detected_language": detected_lang,
                "language_name": self.get_language_name(detected_lang),
                "is_supported": self.is_language_supported(detected_lang),
                "text_length": len(text),
                "text_preview": text[:100]
            }
        except Exception as e:
            logger.error("Failed to get language info", error=str(e))
            return {
                "detected_language": self.default_language,
                "language_name": self.get_language_name(self.default_language),
                "is_supported": True,
                "text_length": len(text),
                "text_preview": text[:100],
                "error": str(e)
            }


# Global language service instance
language_service = LanguageService()
