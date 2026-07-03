"""
User Repository - Persistence per Utente entities.
"""
from typing import Optional, List
from src.domain import Utente
from .base_repository import BaseRepository


class UserRepository(BaseRepository[Utente]):
    """
    Repository per Utente.
    
    NOTA: Questa è una implementazione in-memory per demo.
    In produzione, usare SQLAlchemy ORM + database vero.
    """
    
    def __init__(self):
        """Inizializza UserRepository."""
        super().__init__("User")
        self._store: dict = {}  # In-memory storage
        self._email_index: dict = {}  # Index per email lookup rapido
    
    def create(self, user: Utente) -> Utente:
        """Crea e salva un utente."""
        self._store[user.id] = user
        self._email_index[user.email.lower()] = user.id
        self.log_info(f"User created: {user.email}")
        return user
    
    def read(self, id: str) -> Optional[Utente]:
        """Legge un utente per ID."""
        return self._store.get(id)
    
    def read_by_email(self, email: str) -> Optional[Utente]:
        """Legge un utente per email."""
        user_id = self._email_index.get(email.lower())
        if user_id:
            return self._store.get(user_id)
        return None
    
    def update(self, user: Utente) -> Utente:
        """Aggiorna un utente."""
        if user.id not in self._store:
            raise ValueError(f"User {user.id} not found")
        
        # Update email index se changed
        old_user = self._store[user.id]
        if old_user.email != user.email:
            del self._email_index[old_user.email.lower()]
            self._email_index[user.email.lower()] = user.id
        
        self._store[user.id] = user
        self.log_info(f"User updated: {user.email}")
        return user
    
    def delete(self, id: str) -> bool:
        """Cancella un utente."""
        if id in self._store:
            user = self._store[id]
            del self._email_index[user.email.lower()]
            del self._store[id]
            self.log_info(f"User deleted: {id}")
            return True
        return False
    
    def list_all(self) -> List[Utente]:
        """Lista tutti gli utenti."""
        return list(self._store.values())
