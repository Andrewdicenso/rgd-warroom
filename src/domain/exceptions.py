"""
Domain Exceptions - Eccezioni di Dominio.
Eccezioni specifiche della logica di business.
"""


class DomainException(Exception):
    """Eccezione base per il dominio."""
    pass


class AssetException(DomainException):
    """Eccezione relativa agli Asset."""
    pass


class RiskException(DomainException):
    """Eccezione relativa al calcolo del rischio."""
    pass


class ValidationException(DomainException):
    """Eccezione di validazione."""
    pass


class InvalidRiscoScoreException(ValidationException):
    """Rischio score non valido (deve essere 0-10)."""
    pass


class InvalidAssetException(ValidationException):
    """Asset non valido."""
    pass


class AssetNotFound(DomainException):
    """Asset non trovato."""
    pass
