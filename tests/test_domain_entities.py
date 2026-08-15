"""
Test Suite for Domain Entities.
Tests le entità di dominio: Asset, Azienda, Utente.
"""

import pytest
from src.domain import (
    Asset,
    AssetDiMercato,
    AssetDiValore,
    AssetDiRelazione,
    Azienda,
    Utente,
    RiscoScore,
    InvalidAssetException,
    AssetCategory
)


class TestAsset:
    """Test cases for Asset entity."""

    def test_asset_creation(self):
        """Crea un asset valido."""
        asset = Asset(
            nome="Test Asset",
            company_id="company-123",
            rischio=RiscoScore(5.0)
        )
        
        assert asset.nome == "Test Asset"
        assert asset.company_id == "company-123"
        assert asset.rischio.value == 5.0

    def test_asset_nome_required(self):
        """Asset senza nome deve fallire."""
        with pytest.raises(InvalidAssetException):
            Asset(nome="", company_id="company-123")

    def test_asset_company_id_required(self):
        """Asset senza company_id deve fallire."""
        with pytest.raises(InvalidAssetException):
            Asset(nome="Test", company_id="")

    def test_asset_is_critical_property(self):
        """Verifica la proprietà is_critical."""
        asset_safe = Asset(nome="Safe", company_id="company-123", rischio=RiscoScore(3.0))
        asset_critical = Asset(nome="Critical", company_id="company-123", rischio=RiscoScore(9.0))
        
        assert not asset_safe.is_critical
        assert asset_critical.is_critical

    def test_asset_aggiorna_rischio(self):
        """Aggiorna il rischio di un asset."""
        asset = Asset(nome="Test", company_id="company-123", rischio=RiscoScore(3.0))
        asset.aggiorna_rischio(7.5)
        
        assert asset.rischio.value == 7.5


class TestAssetDiMercato:
    """Test cases for AssetDiMercato (Logistics)."""

    def test_asset_di_mercato_creation(self):
        """Crea un asset logistico."""
        asset = AssetDiMercato(
            nome="Inventory Item",
            company_id="company-123",
            quantita=100.0,
            sku="SKU-001",
            ubicazione="Magazzino A"
        )
        
        assert asset.nome == "Inventory Item"
        assert asset.quantita == 100.0
        assert asset.categoria == AssetCategory.LOGISTICS

    def test_asset_di_mercato_negative_quantity(self):
        """Quantità negativa deve fallire."""
        with pytest.raises(InvalidAssetException):
            AssetDiMercato(
                nome="Bad Item",
                company_id="company-123",
                quantita=-10.0
            )


class TestAssetDiValore:
    """Test cases for AssetDiValore (Finance)."""

    def test_asset_di_valore_creation(self):
        """Crea un asset finanziario."""
        asset = AssetDiValore(
            nome="Financial Asset",
            company_id="company-123",
            prezzo=1500.00,
            valuta="EUR",
            stato_pagamento="Pagato"
        )
        
        assert asset.nome == "Financial Asset"
        assert asset.prezzo == 1500.00
        assert asset.categoria == AssetCategory.FINANCE

    def test_asset_di_valore_negative_price(self):
        """Prezzo negativo deve fallire."""
        with pytest.raises(InvalidAssetException):
            AssetDiValore(
                nome="Bad Price",
                company_id="company-123",
                prezzo=-100.0
            )


class TestAssetDiRelazione:
    """Test cases for AssetDiRelazione (Relations)."""

    def test_asset_di_relazione_creation(self):
        """Crea un asset relazionale."""
        asset = AssetDiRelazione(
            nome="Partner Relationship",
            company_id="company-123",
            partner="Acme Corp",
            livello_servizio=8.5
        )
        
        assert asset.nome == "Partner Relationship"
        assert asset.partner == "Acme Corp"
        assert asset.categoria == AssetCategory.RELATIONS

    def test_asset_di_relazione_invalid_level(self):
        """Livello servizio fuori range deve fallire."""
        with pytest.raises(InvalidAssetException):
            AssetDiRelazione(
                nome="Bad Level",
                company_id="company-123",
                livello_servizio=15.0  # Fuori range 0-10
            )


class TestAzienda:
    """Test cases for Azienda entity."""

    def test_azienda_creation(self):
        """Crea un'azienda."""
        azienda = Azienda(
            nome="Test Company",
            partita_iva="12345678901"
        )
        
        assert azienda.nome == "Test Company"
        assert azienda.partita_iva == "12345678901"

    def test_azienda_nome_required(self):
        """Azienda senza nome deve fallire."""
        with pytest.raises(InvalidAssetException):
            Azienda(nome="", partita_iva="123")

    def test_aggiungi_asset_ad_azienda(self):
        """Aggiunge un asset all'azienda."""
        azienda = Azienda(nome="Test Company", partita_iva="123")
        asset = Asset(nome="Asset 1", company_id="temp-id")
        
        azienda.aggiungi_asset(asset)
        
        assert len(azienda.assets) == 1
        assert asset.company_id == azienda.id
        assert azienda.assets[asset.id] == asset

    def test_recupera_asset(self):
        """Recupera un asset dall'azienda."""
        azienda = Azienda(nome="Test Company", partita_iva="123")
        asset = Asset(nome="Asset 1", company_id="temp-id")
        
        azienda.aggiungi_asset(asset)
        retrieved = azienda.recupera_asset(asset.id)
        
        assert retrieved is not None
        assert retrieved.nome == "Asset 1"

    def test_asset_critici(self):
        """Filtra asset critici."""
        azienda = Azienda(nome="Test Company", partita_iva="123")
        
        # Asset safe
        a1 = Asset(nome="Safe", company_id="temp-id", rischio=RiscoScore(3.0))
        # Asset critical
        a2 = Asset(nome="Critical", company_id="temp-id", rischio=RiscoScore(9.0))
        
        azienda.aggiungi_asset(a1)
        azienda.aggiungi_asset(a2)
        
        critical = azienda.asset_critici()
        
        assert len(critical) == 1
        assert critical[0].nome == "Critical"


class TestUtente:
    """Test cases for Utente entity."""

    def test_utente_creation(self):
        """Crea un utente."""
        utente = Utente(
            email="test@example.com",
            password_hash="hashed_password_123",
            ruolo="user",
            azienda_id="company-123"
        )
        
        assert utente.email == "test@example.com"
        assert utente.ruolo == "user"

    def test_utente_email_required(self):
        """Utente senza email deve fallire."""
        with pytest.raises(InvalidAssetException):
            Utente(
                email="",
                password_hash="password"
            )

    def test_utente_password_hash_required(self):
        """Utente senza password_hash deve fallire."""
        with pytest.raises(InvalidAssetException):
            Utente(
                email="test@example.com",
                password_hash=""
            )

    def test_utente_is_admin_property(self):
        """Verifica la proprietà is_admin."""
        admin = Utente(
            email="admin@example.com",
            password_hash="hash",
            ruolo="admin"
        )
        user = Utente(
            email="user@example.com",
            password_hash="hash",
            ruolo="user"
        )
        
        assert admin.is_admin
        assert not user.is_admin
