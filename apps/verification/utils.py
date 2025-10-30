import secrets
import hashlib
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def generate_otp_code(length=6):
    """
    Generate a random numeric OTP code.
    
    Args:
        length: Length of the OTP code (default: 6)
    
    Returns:
        str: Random numeric OTP code
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def hash_otp_code(code, salt=None):
    """
    Hash an OTP code using SHA-256.
    
    Args:
        code: The OTP code to hash
        salt: Optional salt (if None, generates a new one)
    
    Returns:
        tuple: (hashed_code, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine code and salt
    combined = f"{code}{salt}".encode('utf-8')
    hashed = hashlib.sha256(combined).hexdigest()
    
    return f"{salt}:{hashed}", salt


def verify_otp_code(code, stored_hash):
    """
    Verify an OTP code against a stored hash.
    
    Args:
        code: The OTP code to verify
        stored_hash: The stored hash (format: "salt:hash")
    
    Returns:
        bool: True if code matches, False otherwise
    """
    try:
        salt, stored_hash_value = stored_hash.split(':', 1)
        combined = f"{code}{salt}".encode('utf-8')
        computed_hash = hashlib.sha256(combined).hexdigest()
        return secrets.compare_digest(computed_hash, stored_hash_value)
    except (ValueError, AttributeError):
        return False


def get_otp_expiry_time(minutes=None):
    """
    Get expiry time for OTP code.
    
    Args:
        minutes: Minutes until expiry (default: from settings)
    
    Returns:
        datetime: Expiry timestamp
    """
    if minutes is None:
        minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    return timezone.now() + timedelta(minutes=minutes)

