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
        # Normalizziamo il percorso per evitare errori su Windows
        self.key_path = os.path.abspath(key_path)
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """Carica la chiave da Environment Variable (Render) o da File (Locale)."""
        try:
            # 1. TENTATIVO: Cerca nelle variabili d'ambiente (per Render)
            env_key = os.getenv("VAULT_KEY_CONTENT")
            if env_key:
                logger.info("🛡️ Chiave caricata con successo da variabile d'ambiente.")
                return env_key.encode('utf-8') if isinstance(env_key, str) else env_key

            # 2. TENTATIVO: Cerca nel file locale (per VS Code)
            if os.path.exists(self.key_path):
                with open(self.key_path, "rb") as key_file:
                    key_data = key_file.read().strip()
                    if key_data:
                        logger.info("🛡️ Chiave caricata con successo da file locale.")
                        return key_data

            # 3. FALLBACK: Genera nuova (solo se siamo in locale e manca tutto)
            if not os.getenv("DATABASE_URL"): # Se non siamo su Render
                key = Fernet.generate_key()
                folder = os.path.dirname(self.key_path)
                os.makedirs(folder, exist_ok=True)
                with open(self.key_path, "wb") as key_file:
                    key_file.write(key)
                logger.warning("⚠️ Nuova chiave generata (Locale).")
                return key
            else:
                # Se siamo su Render e arriviamo qui, significa che manca la variabile d'ambiente
                raise ValueError("ERRORE CRITICO: Chiave mancante su Render! Aggiungi VAULT_KEY_CONTENT nelle variabili.")

        except Exception as e:
            logger.critical(f"❌ FALLIMENTO SECURITY: {e}")
            raise

    def encrypt_data(self, data: str) -> str:
        """Cifra una stringa e restituisce una stringa sicura per il DB."""
        if data is None: return None
        try:
            return self.cipher.encrypt(data.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Errore cifratura: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decifra i dati. Accetta stringhe o bytes (massima compatibilità)."""
        if not encrypted_data: return ""
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode('utf-8')
            return self.cipher.decrypt(encrypted_data).decode('utf-8')
        except InvalidToken:
            logger.error("⚠️ ALERT SICUREZZA: Chiave non valida o dati manomessi!")
            return "ERR_SEC_INVALID_TOKEN"
        except Exception as e:
            logger.error(f"Errore decifratura: {e}")
            return "ERR_SEC_GENERIC"

# --- TEST DI INTEGRITÀ RAPIDO ---
if __name__ == "__main__":
    vault = SecureVault()
    test_msg = "Azienda_Segreta_123"
    criptato = vault.encrypt_data(test_msg)
    decriptato = vault.decrypt_data(criptato)
    print(f"Originale: {test_msg}")
    print(f"Criptato: {criptato}")
    print(f"Decriptato correttamente: {test_msg == decriptato}")