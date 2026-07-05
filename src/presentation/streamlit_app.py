import sys
from pathlib import Path

# Risolvi percorsi per import
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.config import get_settings
from src.presentation.state import SessionManager
from src.presentation.components import render_login_tabs
from src.application.services import AuthService, AssetService, AnalysisService
from src.infrastructure import configure_logging

# Inizializzazione configurazioni globali
settings = get_settings()
configure_logging()


# ==========================================
# SERVICES INITIALIZATION (Singleton Pattern)
# ==========================================

@st.cache_resource
def get_auth_service() -> AuthService:
    """Ottiene l'istanza AuthService (cached)."""
    return AuthService(admin_email=settings.ADMIN_EMAIL)


@st.cache_resource
def get_asset_service() -> AssetService:
    """Ottiene l'istanza AssetService (cached)."""
    return AssetService()


@st.cache_resource
def get_analysis_service() -> AnalysisService:
    """Ottiene l'istanza AnalysisService (cached)."""
    return AnalysisService()


# ==========================================
# CORE UI CONFIGURATION
# ==========================================

def load_css() -> None:
    """Carica il design system CSS."""
    css_path = PROJECT_ROOT / "style.css"
    if css_path.exists():
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Errore nel caricamento CSS: {e}")


def configure_page() -> None:
    """Configura la pagina Streamlit."""
    st.set_page_config(**settings.ST_PAGE_CONFIG)
    load_css()


# ==========================================
# ACTION HANDLERS (Logica di Business)
# ==========================================

def handle_login(email: str, password: str) -> bool:
    """Gestisce il login dell'utente e rinfresca lo stato visivo."""
    auth_service = get_auth_service()
    response = auth_service.login(email, password)
    
    if response.success:
        SessionManager.login(
            user_id=response.user_id,
            email=response.email,
            ruolo=response.ruolo,
            azienda=response.azienda,
            azienda_id=response.azienda_id,
        )
        st.success(f"✅ {response.message}")
        st.rerun()
        return True
    
    st.error(f"❌ {response.message}")
    return False


def handle_register(email: str, password: str, confirm: str) -> bool:
    """Gestisce la registrazione di un nuovo utente."""
    auth_service = get_auth_service()
    response = auth_service.register(email, password, confirm)

    if response.success:
        st.success(f"✅ {response.message}")
        return True
    
    st.error(f"❌ {response.message}")
    return False


def handle_request_reset(email: str) -> bool:
    """Gestisce la richiesta di reset password."""
    auth_service = get_auth_service()
    success, reset_token = auth_service.request_password_reset(email)

    if success:
        # TODO: Inviare email con reset_token
        st.success("✅ Se l'email è registrata, riceverai un link di reset")
        return True
    
    st.warning("⚠️ Se l'email è registrata, riceverai un link di reset")
    return False


def handle_reset_password(token: str, password: str, confirm: str) -> bool:
    """Gestisce il reset effettivo della password via token."""
    auth_service = get_auth_service()
    success, message = auth_service.reset_password(token, password, confirm)

    if success:
        st.success(f"✅ {message}")
        return True
    
    st.error(f"❌ {message}")
    return False


# ==========================================
# PRESENTATION LAYER (Rendering delle Pagine)
# ==========================================

def render_auth_pages() -> None:
    """Renderizza le pagine di autenticazione (login, registrazione, recupero password)."""
    st.title("🛡️ RGD-Alpha | War Room Strategica")
    st.subheader("Gestione Strategica d'Azienda")

    col1, col2 = st.columns([1.5, 1], gap="large")

    with col1:
        st.markdown("""
        ### Benvenuto in RGD-Alpha
        
        La piattaforma di **Business Intelligence e Risk Management** 
        progettata per PMI italiane.
        
        **Funzionalità Principali:**
        - 📊 Analisi Predittiva del Rischio
        - 🎯 Dashboard Strategica (War Room)
        - ⚡ Alerting Automatico
        - 📈 Simulazioni What-If
        
        ---
        """)

    with col2:
        st.markdown("### 🔐 Accedi al Sistema")

        # Recupera reset_token dalla URL se presente
        reset_token = st.query_params.get("reset_token")

        # Renderizza i form di autenticazione passando i gestori reali
        render_login_tabs(
            on_login=handle_login,
            on_register=handle_register,
            on_request_reset=handle_request_reset,
            reset_token=reset_token,
            on_reset=handle_reset_password,
        )


def render_app_pages() -> None:
    """Pagine interne dell'app con Sidebar e Menu integrato post-login."""

    # 1. SIDEBAR DI NAVIGAZIONE
    with st.sidebar:
        st.markdown(f"### 👤 {SessionManager.get_email()}")
        st.caption(f"Ruolo: **{str(SessionManager.get_ruolo()).upper()}**")
        st.caption(f"Azienda: **{SessionManager.get_azienda()}**")

        st.divider()

        menu = st.radio(
            "Navigazione:",
            ["🏠 Home", "📊 War Room", "📁 Archivio Dati"],
            index=0,
        )

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            SessionManager.logout()
            st.rerun()

    # 2. LOGICA DEI CONTENUTI
    if menu == "🏠 Home":
        st.title("🏠 Homepage RGD-Alpha")
        st.info(f"""
        ✨ **Benvenuto nella Dashboard, {SessionManager.get_azienda()}!**
        
        Usa la barra laterale per navigare tra le sezioni:
        1. **War Room**: Per l'analisi degli asset in tempo reale.
        2. **Archivio Dati**: Per gestire i file caricati ed elaborati.
        """)

    elif menu == "📊 War Room":
        try:
            from src.presentation.pages.war_room import show
            show()
        except ImportError:
            st.error("Errore nel caricamento del modulo War Room. Verifica il percorso del file.")

    elif menu == "📁 Archivio Dati":
        st.title("📁 Archivio Dati Operativi")
        st.write("Qui verranno elencati i file elaborati dal sistema e quelli prelevati dai gestionali aziendali.")
        st.info("Nessun file presente nell'archivio al momento.")


# ==========================================
# APPLICATION ENTRY POINT
# ==========================================

def main() -> None:
    """Ciclo di vita principale dell'applicazione."""
    configure_page()
    SessionManager.initialize()
    
    if SessionManager.is_autenticato():
        render_app_pages()
    else:
        render_auth_pages()


if __name__ == "__main__":
    main()