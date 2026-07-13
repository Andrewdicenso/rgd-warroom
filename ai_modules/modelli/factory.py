from typing import Optional
from .base_model import AIModelInterface
from .provider_groq import GroqAIProvider

class AIFactory:
    """Factory per creare istanze di modelli AI in modo disaccoppiato."""
    
    @staticmethod
    def get_provider(provider_name: str = "groq") -> Optional[AIModelInterface]:
        """Restituisce il provider richiesto basandosi sulla configurazione."""
        
        providers = {
            "groq": GroqAIProvider,
            # In futuro aggiungeremo qui: "openai": OpenAIProvider, "local": LocalProvider
        }
        
        provider_class = providers.get(provider_name.lower())
        
        if provider_class:
            return provider_class()
        
        return None