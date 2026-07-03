"""
Auth Service - Use Case: Autenticazione & Autorizzazione.
"""
import bcrypt
import uuid
from typing import Optional, Tuple
from datetime import datetime, timedelta
from src.domain import Utente, UserRole
from src.application.services.base_service import BaseService
from src.application.dto import LoginResponseDTO, RegistrationResponseDTO
from src.application.mappers import UserMapper


class AuthService(BaseService):
    """
    Servizio di autenticazione.
    Orchiestra login, registrazione, password reset, token management.
    
    NOTA: In produzione, userà UserRepository per persistenza.
    Per ora, usa in-memory storage per demo.
    """
    
    def __init__(self, admin_email: str = "andrewdicenso@libero.it"):
        """
        Inizializza AuthService.
        
        Args:
            admin_email: Email dell'amministratore (única)
        """
        super().__init__("AuthService")
        self.admin_email = admin_email.lower()
        self._users_store: dict = {}  # In-memory storage (demo only)
        self._reset_tokens: dict = {}  # In-memory reset tokens
        
        # Crea admin di default
        self._create_default_admin()
    
    def _create_default_admin(self) -> None:
        """Crea admin di default se non esiste."""
        admin_password = "WarRoom123!"
        admin_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        
        admin = Utente(
            email=self.admin_email,
            password_hash=admin_hash,
            ruolo=UserRole.ADMIN.value,
            azienda_id="rgd-alpha-001"
        )
        
        self._users_store[admin.id] = admin
        self.log_info(f"Default admin created: {self.admin_email}")
    
    def login(self, email: str, password: str) -> LoginResponseDTO:
        """
        Effettua il login di un utente.
        
        Args:
            email: Email utente
            password: Password in chiaro
            
        Returns:
            LoginResponseDTO con result e token
        """
        email = email.lower().strip()
        self.log_info(f"Login attempt: {email}")
        
        # Trova utente per email
        user = self._find_user_by_email(email)
        if not user:
            self.log_warning(f"Login failed: user not found {email}")
            return LoginResponseDTO(
                success=False,
                user_id="",
                email="",
                ruolo="",
                azienda="",
                azienda_id="",
                message="Email o password non validi"
            )
        
        # Verifica password
        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            self.log_warning(f"Login failed: wrong password for {email}")
            return LoginResponseDTO(
                success=False,
                user_id="",
                email="",
                ruolo="",
                azienda="",
                azienda_id="",
                message="Email o password non validi"
            )
        
        # Update last login
        user.data_ultimo_login = datetime.now()
        
        # Crea token (JWT semplice per demo)
        token = self._create_token(user.id)
        
        self.log_info(f"Login successful: {email}")
        
        return LoginResponseDTO(
            success=True,
            user_id=user.id,
            email=user.email,
            ruolo=user.ruolo,
            azienda="Demo Company",  # TODO: fetch from database
            azienda_id=user.azienda_id or "demo-001",
            token=token,
            message="Login effettuato con successo"
        )
    
    def register(
        self,
        email: str,
        password: str,
        confirm_password: str,
        azienda_name: Optional[str] = None
    ) -> RegistrationResponseDTO:
        """
        Registra un nuovo utente.
        
        Args:
            email: Email utente
            password: Password
            confirm_password: Conferma password
            azienda_name: Nome azienda (opzionale)
            
        Returns:
            RegistrationResponseDTO
        """
        email = email.lower().strip()
        self.log_info(f"Registration attempt: {email}")
        
        # Validazioni
        if password != confirm_password:
            return RegistrationResponseDTO(
                success=False,
                message="Le password non coincidono"
            )
        
        if len(password) < 8:
            return RegistrationResponseDTO(
                success=False,
                message="Password deve essere almeno 8 caratteri"
            )
        
        # Verifica se esiste già
        if self._find_user_by_email(email):
            self.log_warning(f"Registration failed: email già registrata {email}")
            return RegistrationResponseDTO(
                success=False,
                message="Email già registrata nel sistema"
            )
        
        # Crea nuovo utente
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        
        # Se è l'admin email, assegna ruolo admin
        ruolo = UserRole.ADMIN.value if email == self.admin_email else UserRole.USER.value
        
        utente = Utente(
            email=email,
            password_hash=password_hash,
            ruolo=ruolo,
            azienda_id=f"company-{uuid.uuid4().hex[:8]}"
        )
        
        self._users_store[utente.id] = utente
        
        self.log_info(f"User registered: {email}")
        
        return RegistrationResponseDTO(
            success=True,
            user_id=utente.id,
            message="Registrazione completata con successo"
        )
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """
        Richiede un reset della password.
        
        Args:
            email: Email utente
            
        Returns:
            (success, reset_token)
        """
        email = email.lower().strip()
        self.log_info(f"Password reset requested: {email}")
        
        user = self._find_user_by_email(email)
        if not user:
            # Security: non rivelare se email esiste
            return False, ""
        
        # Crea reset token (valido 24h)
        reset_token = str(uuid.uuid4())
        self._reset_tokens[reset_token] = {
            "user_id": user.id,
            "email": email,
            "expires_at": datetime.now() + timedelta(hours=24)
        }
        
        self.log_info(f"Reset token created for {email}")
        
        return True, reset_token
    
    def reset_password(self, token: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Completa il reset della password.
        
        Args:
            token: Reset token
            new_password: Nuova password
            confirm_password: Conferma password
            
        Returns:
            (success, message)
        """
        self.log_info(f"Password reset attempt with token")
        
        # Verifica token
        if token not in self._reset_tokens:
            return False, "Token non valido"
        
        token_data = self._reset_tokens[token]
        
        # Verifica scadenza
        if datetime.now() > token_data["expires_at"]:
            del self._reset_tokens[token]
            return False, "Token scaduto"
        
        # Validazioni password
        if new_password != confirm_password:
            return False, "Le password non coincidono"
        
        if len(new_password) < 8:
            return False, "Password deve essere almeno 8 caratteri"
        
        # Aggiorna password
        user_id = token_data["user_id"]
        user = self._users_store.get(user_id)
        
        if not user:
            return False, "Utente non trovato"
        
        user.password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")
        
        # Elimina token usato
        del self._reset_tokens[token]
        
        self.log_info(f"Password reset successful for {user.email}")
        
        return True, "Password aggiornata con successo"
    
    def _find_user_by_email(self, email: str) -> Optional[Utente]:
        """Trova utente per email (case-insensitive)."""
        for user in self._users_store.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    def _create_token(self, user_id: str) -> str:
        """Crea un token semplice (demo)."""
        # In produzione, usare JWT
        return f"token-{user_id}-{uuid.uuid4().hex[:8]}"
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verifica token e ritorna user_id se valido."""
        # In produzione, verificare JWT signature
        if token.startswith("token-"):
            parts = token.split("-")
            if len(parts) >= 2:
                return parts[1]
        return None
