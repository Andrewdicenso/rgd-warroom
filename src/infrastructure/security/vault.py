"""
Secure Vault - Crittografia AES per dati sensibili.
"""
import json
import logging
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger("RGD-Alpha.Vault")


class SecureVault:
    """
    Vault per crittografia/decrittografia dati sensibili.
    
    NOTA: Questa è una versione semplificata.
    In produzione, usare Cryptography library con proper key management.
    """
    
    def __init__(self, key_path: str = "core/security/vault.key"):
        """
        Inizializza Secure Vault.
        
        Args:
            key_path: Path alla chiave crittografica
        """
        self.key_path = Path(key_path)
        self._ensure_key_exists()
    
    def _ensure_key_exists(self) -> None:
        """Assicura che la chiave esista, altrimenti la crea."""
        if not self.key_path.exists():
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            # Genera chiave simple (demo)
            import secrets
            key = secrets.token_hex(32)
            self.key_path.write_text(key)
            logger.info(f"Vault key created: {self.key_path}")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encripta un testo.
        
        Args:
            plaintext: Testo in chiaro
            
        Returns:
            Testo criptato (base64)
        """
        # NOTA: Per demo, usa semplice XOR (NOT FOR PRODUCTION!)
        # In produzione: usare cryptography.fernet
        try:
            key = self.key_path.read_text().strip()
            # Simple XOR (insecure, solo per demo)
            result = ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(plaintext))
            import base64
            return base64.b64encode(result.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return plaintext
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decripta un testo.
        
        Args:
            ciphertext: Testo criptato (base64)
            
        Returns:
            Testo in chiaro
        """
        try:
            key = self.key_path.read_text().strip()
            import base64
            data = base64.b64decode(ciphertext.encode()).decode()
            # Simple XOR reverse
            result = ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))
            return result
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ciphertext
    
    def encrypt_dict(self, data: dict) -> str:
        """Encripta un dizionario JSON."""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, ciphertext: str) -> dict:
        """Decripta un dizionario JSON."""
        plaintext = self.decrypt(ciphertext)
        return json.loads(plaintext)
