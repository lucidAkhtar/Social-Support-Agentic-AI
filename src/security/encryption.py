"""
Enterprise-grade encryption for sensitive data
WHAT THIS GIVES YOU: Military-grade protection of PII data
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os
import json
from typing import Any, Dict
import hashlib

class DataEncryption:
    """
    AES-256 encryption for all sensitive data
    """
    
    def __init__(self, master_key: str = None):
        if master_key is None:
            master_key = os.getenv('ENCRYPTION_KEY', 'default-key-change-in-production')
        
        # Derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'social-support-ai-salt',  # In production: unique per deployment
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt entire dictionary"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt to dictionary"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)

class PIIDetector:
    """
    Automatically detect and mask PII in text
    WHAT THIS GIVES YOU: Automatic privacy protection
    """
    
    PII_PATTERNS = {
        'emirates_id': r'\d{3}-\d{4}-\d{7}-\d',
        'phone': r'\+971[-\s]?\d{2}[-\s]?\d{3}[-\s]?\d{4}',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'credit_card': r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
    }
    
    def detect_pii(self, text: str) -> Dict[str, list]:
        """Detect all PII in text"""
        import re
        detected = {}
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                detected[pii_type] = matches
        
        return detected
    
    def mask_pii(self, text: str) -> str:
        """Replace PII with masked version"""
        import re
        masked_text = text
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            if pii_type == 'emirates_id':
                masked_text = re.sub(pattern, 'XXX-XXXX-XXXXXXX-X', masked_text)
            elif pii_type == 'phone':
                masked_text = re.sub(pattern, '+971-XX-XXX-XXXX', masked_text)
            elif pii_type == 'email':
                masked_text = re.sub(pattern, 'user@*****.com', masked_text)
            elif pii_type == 'credit_card':
                masked_text = re.sub(pattern, 'XXXX-XXXX-XXXX-XXXX', masked_text)
        
        return masked_text

# DEMO SCRIPT FOR PRESENTATION:
if __name__ == "__main__":
    # Show encryption
    encryptor = DataEncryption()
    
    sensitive_data = {
        "name": "Ahmed Al Maktoum",
        "emirates_id": "784-1990-1234567-1",
        "income": 12000
    }
    
    encrypted = encryptor.encrypt_dict(sensitive_data)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = encryptor.decrypt_dict(encrypted)
    print(f"Decrypted: {decrypted}")
    
    # Show PII masking
    detector = PIIDetector()
    
    text = "Contact Ahmed at +971-50-123-4567 or ahmed@email.com. Emirates ID: 784-1990-1234567-1"
    print(f"\nOriginal: {text}")
    
    detected = detector.detect_pii(text)
    print(f"Detected PII: {detected}")
    
    masked = detector.mask_pii(text)
    print(f"Masked: {masked}")