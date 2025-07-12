# Input validation
"""
Input validation utilities
Provides functions to validate different types of input data
"""
import re
import os
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        Boolean indicating if email is valid
    """
    # Simple email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        Boolean indicating if phone number is valid
    """
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
    
    # Check if result is a valid phone number (simple check)
    return bool(re.match(r'^\+?[0-9]{10,15}$', cleaned))

def validate_password_strength(password: str) -> tuple:
    """
    Validate password strength
    
    Args:
        password: Password string to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension
    
    Args:
        filename: Name of the file to validate
        allowed_extensions: List of allowed file extensions (without dot)
        
    Returns:
        Boolean indicating if file extension is allowed
    """
    # Get file extension (lowercase)
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    
    return ext in [x.lower().lstrip('.') for x in allowed_extensions]

def validate_file_size(file_size: int, max_size_mb: float = 10.0) -> bool:
    """
    Validate file size
    
    Args:
        file_size: Size of the file in bytes
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        Boolean indicating if file size is within limit
    """
    # Convert max_size_mb to bytes
    max_size_bytes = max_size_mb * 1024 * 1024
    
    return file_size <= max_size_bytes

def sanitize_input(text: str) -> str:
    """
    Sanitize text input to prevent common attacks
    
    Args:
        text: Text string to sanitize
        
    Returns:
        Sanitized text string
    """
    # Replace potentially dangerous characters
    text = re.sub(r'[<>&\'"]', '', text)
    
    # Limit length
    return text[:1000]  # Arbitrary limit for safety

def validate_date_format(date_str: str) -> bool:
    """
    Validate if string is in YYYY-MM-DD format
    
    Args:
        date_str: Date string to validate
        
    Returns:
        Boolean indicating if date format is valid
    """
    try:
        # Check format
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return False
        
        # Further validation could check for valid month/day ranges
        year, month, day = map(int, date_str.split('-'))
        
        # Basic validation
        if year < 1900 or year > 2100:
            return False
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
            
        return True
    except:
        return False