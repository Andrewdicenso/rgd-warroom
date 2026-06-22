from cryptography.fernet import Fernet, InvalidToken
import os
import logging

logger = logging.getLogger("RGD-Alpha.Vault")

class SecureVault:
    """
    Vault aziendale: Cifratura simmetrica AES per la protezione dei dati sensibili.
    Gestisce automaticamente la persistenza della Master Key.
    """
    def __init__(self, key_path="core/security/vault.key"):
        self.key_path = os.path.abspath(key_path)
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """Carica la chiave da Environment Variable (Render) o da File (Locale)."""
        try:
            # 1. Variabile d'ambiente (Render)
            env_key = os.getenv("VAULT_KEY_CONTENT")
            if env_key:
                key = env_key.strip().encode("utf-8")
                logger.info("🛡️ Chiave caricata da variabile d'ambiente.")
                return key

            # 2. File locale
            if os.path.exists(self.key_path):
                with open(self.key_path, "rb") as key_file:
                    key_data = key_file.read().strip()
                    if key_data:
                        logger.info("🛡️ Chiave caricata da file locale.")
                        return key_data

            # 3. Generazione nuova chiave (solo locale)
            if not os.getenv("DATABASE_URL"):
                key = Fernet.generate_key()
                folder = os.path.dirname(self.key_path)
                os.makedirs(folder, exist_ok=True)
                with open(self.key_path, "wb") as key_file:
                    key_file.write(key)
                logger.warning("⚠️ Nuova chiave generata (Locale).")
                return key

            raise ValueError("ERRORE CRITICO: Chiave mancante su Render!")

        except Exception as e:
            logger.critical(f"❌ FALLIMENTO SECURITY: {e}")
            raise

    def encrypt_data(self, data) -> str:
        """Cifra una stringa o numero e restituisce una stringa sicura per il DB."""
        if data is None:
            return None
        try:
            if not isinstance(data, str):
                data = str(data)
            return self.cipher.encrypt(data.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error(f"Errore cifratura: {e}")
            raise

def decrypt_data(self, encrypted_data):
    """Decifra i dati. Accetta stringhe o bytes."""
    if not encrypted_data:
        return ""
    try:
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode("utf-8")
        return self.cipher.decrypt(encrypted_data).decode("utf-8")
    except InvalidToken:
        logger.error("⚠️ ALERT SICUREZZA: Token non valido o dati manomessi!")
        return None
    except Exception as e:
        logger.error(f"Errore decifratura: {e}")
        return None


# --- TEST DI INTEGRITÀ ---
if __name__ == "__main__":
    vault = SecureVault()
    test_msg = "Azienda_Segreta_123"
    criptato = vault.encrypt_data(test_msg)
    decriptato = vault.decrypt_data(criptato)
    print(f"Originale: {test_msg}")
    print(f"Criptato: {criptato}")
    print(f"Decriptato correttamente: {test_msg == decriptato}")
