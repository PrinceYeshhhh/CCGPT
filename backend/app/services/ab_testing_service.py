"""
A/B Testing service for widget configurations
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import structlog

from app.core.config import settings
from app.models.embed import EmbedCode
from app.exceptions import ABTestingError, ConfigurationError

logger = structlog.get_logger()


class ABTest:
    """Represents an A/B test configuration"""
    
    def __init__(self, test_id: str, name: str, variants: List[Dict[str, Any]], traffic_split: float = 0.5):
        self.test_id = test_id
        self.name = name
        self.variants = variants
        self.traffic_split = traffic_split
        self.created_at = datetime.now()
        self.is_active = True
    
    def get_variant_for_user(self, user_id: str) -> Dict[str, Any]:
        """Determine which variant a user should see based on consistent hashing"""
        # Use consistent hashing to ensure same user always gets same variant
        hash_input = f"{self.test_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Use hash to determine variant
        if (hash_value % 100) < (self.traffic_split * 100):
            return self.variants[0]  # Variant A
        else:
            return self.variants[1]  # Variant B


class ABTestingService:
    """Service for managing A/B tests for widget configurations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_tests: Dict[str, ABTest] = {}
        self._load_active_tests()
    
    def _load_active_tests(self):
        """Load active A/B tests from database or configuration"""
        try:
            # For now, create some default tests
            # In production, these would be loaded from a database
            default_tests = [
                ABTest(
                    test_id="widget_color_test",
                    name="Widget Color A/B Test",
                    variants=[
                        {
                            "name": "Variant A",
                            "primary_color": "#4f46e5",
                            "secondary_color": "#f8f9fa"
                        },
                        {
                            "name": "Variant B", 
                            "primary_color": "#059669",
                            "secondary_color": "#f0fdf4"
                        }
                    ],
                    traffic_split=0.5
                ),
                ABTest(
                    test_id="widget_position_test",
                    name="Widget Position A/B Test",
                    variants=[
                        {
                            "name": "Variant A",
                            "position": "bottom-right"
                        },
                        {
                            "name": "Variant B",
                            "position": "bottom-left"
                        }
                    ],
                    traffic_split=0.5
                ),
                ABTest(
                    test_id="welcome_message_test",
                    name="Welcome Message A/B Test",
                    variants=[
                        {
                            "name": "Variant A",
                            "welcome_message": "Hello! How can I help you today?"
                        },
                        {
                            "name": "Variant B",
                            "welcome_message": "Hi there! What can I assist you with?"
                        }
                    ],
                    traffic_split=0.5
                )
            ]
            
            for test in default_tests:
                self.active_tests[test.test_id] = test
            
            logger.info(f"Loaded {len(self.active_tests)} active A/B tests")
            
        except Exception as e:
            logger.error("Failed to load A/B tests", error=str(e))
            raise ABTestingError("Failed to load A/B tests", details={"error": str(e)})
    
    def get_variant_for_user(self, test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the variant configuration for a user in a specific test"""
        try:
            if test_id not in self.active_tests:
                logger.warning(f"A/B test not found: {test_id}")
                return None
            
            test = self.active_tests[test_id]
            if not test.is_active:
                return None
            
            variant = test.get_variant_for_user(user_id)
            logger.info(
                "A/B test variant assigned",
                test_id=test_id,
                user_id=user_id,
                variant_name=variant.get("name", "Unknown")
            )
            
            return variant
            
        except Exception as e:
            logger.error("Failed to get A/B test variant", error=str(e))
            return None
    
    def get_all_variants_for_user(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all active A/B test variants for a user"""
        try:
            variants = {}
            
            for test_id, test in self.active_tests.items():
                if test.is_active:
                    variant = self.get_variant_for_user(test_id, user_id)
                    if variant:
                        variants[test_id] = variant
            
            return variants
            
        except Exception as e:
            logger.error("Failed to get all A/B test variants", error=str(e))
            return {}
    
    def apply_variants_to_config(self, base_config: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Apply A/B test variants to a base widget configuration"""
        try:
            if not settings.AB_TESTING_ENABLED:
                return base_config
            
            # Get all variants for this user
            variants = self.get_all_variants_for_user(user_id)
            
            # Start with base configuration
            enhanced_config = base_config.copy()
            
            # Apply each variant
            for test_id, variant in variants.items():
                # Apply variant properties to config
                for key, value in variant.items():
                    if key != "name":  # Skip variant name
                        enhanced_config[key] = value
                        logger.debug(
                            "Applied A/B test variant",
                            test_id=test_id,
                            key=key,
                            value=value,
                            user_id=user_id
                        )
            
            return enhanced_config
            
        except Exception as e:
            logger.error("Failed to apply A/B test variants", error=str(e))
            return base_config
    
    def create_test(
        self,
        test_id: str,
        name: str,
        variants: List[Dict[str, Any]],
        traffic_split: float = 0.5
    ) -> bool:
        """Create a new A/B test"""
        try:
            if test_id in self.active_tests:
                raise ABTestingError(f"A/B test already exists: {test_id}")
            
            if len(variants) != 2:
                raise ABTestingError("A/B tests must have exactly 2 variants")
            
            if not 0 <= traffic_split <= 1:
                raise ABTestingError("Traffic split must be between 0 and 1")
            
            test = ABTest(test_id, name, variants, traffic_split)
            self.active_tests[test_id] = test
            
            logger.info(f"Created A/B test: {test_id}")
            return True
            
        except Exception as e:
            logger.error("Failed to create A/B test", error=str(e))
            raise ABTestingError("Failed to create A/B test", details={"error": str(e)})
    
    def stop_test(self, test_id: str) -> bool:
        """Stop an A/B test"""
        try:
            if test_id not in self.active_tests:
                raise ABTestingError(f"A/B test not found: {test_id}")
            
            self.active_tests[test_id].is_active = False
            logger.info(f"Stopped A/B test: {test_id}")
            return True
            
        except Exception as e:
            logger.error("Failed to stop A/B test", error=str(e))
            raise ABTestingError("Failed to stop A/B test", details={"error": str(e)})
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get results for an A/B test"""
        try:
            if test_id not in self.active_tests:
                raise ABTestingError(f"A/B test not found: {test_id}")
            
            test = self.active_tests[test_id]
            
            # In a real implementation, this would query analytics data
            # For now, return mock results
            results = {
                "test_id": test_id,
                "test_name": test.name,
                "is_active": test.is_active,
                "traffic_split": test.traffic_split,
                "variants": test.variants,
                "results": {
                    "variant_a": {
                        "name": test.variants[0]["name"],
                        "conversions": random.randint(100, 500),
                        "conversion_rate": round(random.uniform(0.1, 0.3), 3),
                        "avg_session_duration": round(random.uniform(120, 300), 2)
                    },
                    "variant_b": {
                        "name": test.variants[1]["name"],
                        "conversions": random.randint(100, 500),
                        "conversion_rate": round(random.uniform(0.1, 0.3), 3),
                        "avg_session_duration": round(random.uniform(120, 300), 2)
                    }
                },
                "statistical_significance": random.uniform(0.7, 0.95),
                "recommended_variant": random.choice(["A", "B"])
            }
            
            return results
            
        except Exception as e:
            logger.error("Failed to get A/B test results", error=str(e))
            raise ABTestingError("Failed to get A/B test results", details={"error": str(e)})
    
    def get_all_tests(self) -> List[Dict[str, Any]]:
        """Get all A/B tests"""
        try:
            tests = []
            for test_id, test in self.active_tests.items():
                tests.append({
                    "test_id": test_id,
                    "name": test.name,
                    "is_active": test.is_active,
                    "traffic_split": test.traffic_split,
                    "variants": test.variants,
                    "created_at": test.created_at.isoformat()
                })
            
            return tests
            
        except Exception as e:
            logger.error("Failed to get A/B tests", error=str(e))
            raise ABTestingError("Failed to get A/B tests", details={"error": str(e)})
    
    def track_conversion(self, test_id: str, user_id: str, conversion_type: str) -> bool:
        """Track a conversion for an A/B test"""
        try:
            if test_id not in self.active_tests:
                return False
            
            # In a real implementation, this would store conversion data
            logger.info(
                "A/B test conversion tracked",
                test_id=test_id,
                user_id=user_id,
                conversion_type=conversion_type
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to track A/B test conversion", error=str(e))
            return False
