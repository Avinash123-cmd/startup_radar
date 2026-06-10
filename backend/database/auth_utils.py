import hashlib
import os

def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2 with HMAC-SHA256 and a random 16-byte salt.
    """
    salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}:{pwd_hash}"

def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies a password against its PBKDF2 HMAC-SHA256 hash.
    """
    try:
        salt, pwd_hash = hashed.split(":")
        check_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return check_hash == pwd_hash
    except ValueError:
        return False
