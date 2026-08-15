import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Carica subito le variabili d'ambiente dal file .env
load_dotenv()

# 2. Risolvi percorsi per gli import del progetto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 3. Import dei moduli dell'applicazione
import streamlit as st
from src.config import get_settings
from src.presentation.state import SessionManager
from src.presentation.components import render_login_tabs
from src.application.services import AuthService, AssetService, AnalysisService
from src.infrastructure import configure_logging

# 4. Inizializzazione configurazioni globali
settings = get_settings()
configure_logging()

# ==========================================
# STILE PROFESSIONALE E SFONDO (CORRETTO & OTTIMIZZATO)
# ==========================================
st.markdown(
    """
    <style>
        /* 1. Pulizia Header e Navigazione */
        [data-testid="stHeader"], [data-testid="stDecoration"] {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
        }

        /* Nasconde i contenuti dell'header TRANNE il pulsante sidebar */
        header[data-testid="stHeader"] > div:first-child > div:first-child > div:nth-child(2) {
            display: none !important;
        }

        header[data-testid="stHeader"] {
            height: 3.5rem !important;
            background: transparent !important;
        }

        /* 1.1 Nasconde Navigazione Automatica Sidebar */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* 1.2 Correzione Colore Testi Sidebar */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stMarkdown {
            color: #31333f !important;
        }

        /* 2. Sfondo della pagina senza interruzioni */
        .stApp {
            background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                            url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=2072") !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }

        /* 3. Contenitore principale (Card) */
        .stMainBlockContainer {
            background: rgba(255, 255, 255, 0.07) !important;
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            border-radius: 24px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 3rem !important;
            max-width: 900px !important;
            margin-top: 2rem !important;
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5) !important;
        }

        /* 4. Testi Generali */
        h1, h2, h3, p, span, label, .stMarkdown { 
            color: #ffffff !important; 
        }
        
        /* 5. FIX PULSANTI (Forza testo scuro visibile) */
        .stButton > button, div.stButton > button, div.stFormSubmitButton > button {
            border-radius: 10px !important;
            background: #ffffff !important; /* Fondo bianco solido */
            color: #1f2937 !important;     /* TESTO SCURO LEGGIBILE */
            width: 100% !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            transition: all 0.3s ease !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
        }
        
        /* Forza il colore scuro su qualsiasi elemento figlio del pulsante */
        .stButton > button *, div.stButton > button *, div.stFormSubmitButton > button * {
            color: #1f2937 !important;
        }
        
        /* Hover del pulsante */
        .stButton > button:hover, div.stButton > button:hover, div.stFormSubmitButton > button:hover { 
            background: #2563eb !important; /* Blu brillante */
            color: #ffffff !important;
            border: 1px solid #2563eb !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
        }

        .stButton > button:hover *, div.stButton > button:hover *, div.stFormSubmitButton > button:hover * {
            color: #ffffff !important;
        }

        /* 6. FIX TABS (Login, Registrazione, Recupero) */
        div[data-baseweb="tab-list"] {
            gap: 2px !important;
            background-color: transparent !important;
        }

        div[data-baseweb="tab"] {
            padding: 4px 8px !important;
            font-size: 0.82rem !important;
            border-radius: 6px !important;
        }

        /* Elimina la barra bianca/rettangolo di overflow a destra nei Tab */
        div[data-testid="stTabs"] > div:first-child {
            overflow-x: visible !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)
# ==========================================
# SERVICES INITIALIZATION (Singleton Pattern)
# ==========================================

@st.cache_resource
def get_auth_service() -> AuthService:
    """Ottiene l'istanza AuthService (cached)."""
    from src.config.settings import get_settings
    cfg = get_settings()
    return AuthService(admin_email=cfg.ADMIN_EMAIL)


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
    """Renderizza le pagine di autenticazione (Login, Reg., Reset password)."""
    st.markdown(
        """
        <style>
            /* Nasconde sidebar e freccette di apertura */
            [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    
    st.title("🛡️ RGD-Alpha | War Room Strategica")
    st.subheader("Gestione Strategica d'Azienda")

    col1, col2 = st.columns([1.2, 1], gap="large")

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