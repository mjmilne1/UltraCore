"""Password Encryption for Tenant Credentials"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class PasswordEncryption:
    """Encrypt/decrypt tenant database passwords"""
    
    def __init__(self, master_password: str, salt: bytes = None):
        """Initialize with master password"""
        self.master_password = master_password
        self.salt = salt or b'ultracore_multitenancy_salt_v1'
        self.key = self._derive_key()
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from master password using PBKDF2"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=self.salt,
            iterations=100000,
        )
        return kdf.derive(self.master_password.encode())
    
    def encrypt(self, password: str) -> str:
        """Encrypt password using AES-256-GCM"""
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        
        ciphertext = aesgcm.encrypt(
            nonce,
            password.encode(),
            None  # No additional authenticated data
        )
        
        # Combine nonce + ciphertext and encode as base64
        encrypted = nonce + ciphertext
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_password: str) -> str:
        """Decrypt password"""
        aesgcm = AESGCM(self.key)
        
        # Decode from base64
        encrypted = base64.b64decode(encrypted_password)
        
        # Split nonce and ciphertext
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        
        # Decrypt
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    
    def rotate_password(self, old_encrypted: str, new_password: str) -> str:
        """Rotate password (decrypt old, encrypt new)"""
        # Verify old password can be decrypted
        self.decrypt(old_encrypted)
        
        # Encrypt new password
        return self.encrypt(new_password)

def hash_master_password(master_password: str) -> str:
    """Hash master password for storage"""
    import hashlib
    return hashlib.sha256(master_password.encode()).hexdigest()
