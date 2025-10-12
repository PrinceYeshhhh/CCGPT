"""
Password utilities with enhanced security
"""

import secrets
import hashlib
from passlib.context import CryptContext
from passlib.hash import bcrypt
from typing import Tuple
import structlog

logger = structlog.get_logger()

# Enhanced password hashing context with bcrypt as primary
pwd_context = CryptContext(
    schemes=["bcrypt"],  # Use bcrypt as primary
    deprecated="auto",   # Accept old hashes during migration
    bcrypt__rounds=12,   # Increased rounds for better security
)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt with salt"""
    # Truncate password to 72 bytes to avoid bcrypt limitation
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Truncate password to 72 bytes to avoid bcrypt limitation
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def generate_salt() -> str:
    """Generate a cryptographically secure salt"""
    return secrets.token_hex(32)

def hash_password_with_salt(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash password with explicit salt for additional security"""
    if salt is None:
        salt = generate_salt()
    
    # Combine password with salt
    salted_password = f"{password}{salt}"
    
    # Hash using bcrypt
    hashed = bcrypt.hash(salted_password, rounds=12)
    
    return hashed, salt

def verify_password_with_salt(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Verify password with explicit salt"""
    salted_password = f"{plain_password}{salt}"
    return bcrypt.verify(salted_password, hashed_password)

def check_password_strength(password: str) -> dict:
    """Check password strength and return detailed analysis"""
    issues = []
    score = 0
    
    # Length check
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    elif len(password) < 12:
        issues.append("Consider using at least 12 characters for better security")
    else:
        score += 20
    
    # Character variety checks
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
    
    if not has_lower:
        issues.append("Password should contain lowercase letters")
    else:
        score += 10
    
    if not has_upper:
        issues.append("Password should contain uppercase letters")
    else:
        score += 10
    
    if not has_digit:
        issues.append("Password should contain numbers")
    else:
        score += 10
    
    if not has_special:
        issues.append("Password should contain special characters")
    else:
        score += 20
    
    # Common patterns check
    common_patterns = [
        "password", "123456", "qwerty", "admin", "letmein",
        "welcome", "monkey", "dragon", "master", "hello"
    ]
    
    if any(pattern in password.lower() for pattern in common_patterns):
        issues.append("Password contains common patterns")
        score -= 20
    
    # Sequential characters check
    if any(password[i:i+3] in "abcdefghijklmnopqrstuvwxyz" for i in range(len(password)-2)):
        issues.append("Password contains sequential characters")
        score -= 10
    
    # Determine strength level
    if score >= 80:
        strength = "very_strong"
    elif score >= 60:
        strength = "strong"
    elif score >= 40:
        strength = "medium"
    elif score >= 20:
        strength = "weak"
    else:
        strength = "very_weak"
    
    return {
        "score": min(max(score, 0), 100),
        "strength": strength,
        "issues": issues,
        "is_acceptable": score >= 40 and len(issues) <= 2
    }

def validate_password_requirements(password: str, min_length: int = 12) -> dict:
    """Validate password against security requirements"""
    strength_check = check_password_strength(password)
    
    # Additional requirements
    requirements_met = []
    requirements_failed = []
    
    if len(password) >= min_length:
        requirements_met.append(f"Minimum length ({min_length} characters)")
    else:
        requirements_failed.append(f"Must be at least {min_length} characters")
    
    if any(c.islower() for c in password):
        requirements_met.append("Contains lowercase letters")
    else:
        requirements_failed.append("Must contain lowercase letters")
    
    if any(c.isupper() for c in password):
        requirements_met.append("Contains uppercase letters")
    else:
        requirements_failed.append("Must contain uppercase letters")
    
    if any(c.isdigit() for c in password):
        requirements_met.append("Contains numbers")
    else:
        requirements_failed.append("Must contain numbers")
    
    if any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
        requirements_met.append("Contains special characters")
    else:
        requirements_failed.append("Must contain special characters")
    
    return {
        "is_valid": len(requirements_failed) == 0,
        "requirements_met": requirements_met,
        "requirements_failed": requirements_failed,
        "strength_analysis": strength_check
    }

