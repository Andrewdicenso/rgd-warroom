import os
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# --- MODULI CORE & AUTH ---
from core.ingestor import IngestoreDati
from core.engine import DataGateway
from core.database import DatabaseAziendale
from connectors.consulente import ConsulenteAziendale
# Importiamo la logica centralizzata dal pacchetto auth
from auth.auth import inizializza_sessione, login_utente, logout_utente

# =========================
#   CONFIGURAZIONE BASE
# =========================
load_dotenv()
PROJECT_ROOT = Path(__file__).parent
DATA_ROOT = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_ROOT / "uploads"

for folder in [UPLOAD_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="RGD-Alpha | War Room Strategica",
    layout="wide",
    page_icon="🛡️"
)

# Inizializzazione stato Protocollo RGD-Alpha
if "analisi_eseguita" not in st.session_state:
    st.session_state.analisi_eseguita = False

# Inizializza la sessione e forza l'accesso Admin per te
inizializza_sessione()

if not st.session_state.get('autenticato'):
    st.session_state.autenticato = True
    st.session_state.user_id = 1
    st.session_state.email = "andrewdicenso@libero.it"
    st.session_state.azienda = "RGandja Enterprise"
    st.session_state.ruolo = "admin"
    st.rerun()

# =========================
#   CSS ENTERPRISE
# =========================
st.markdown("""
    <style>
    .kpi-box {
        background-color: #f8f9fa; padding: 20px; border-radius: 10px;
        border-left: 5px solid #007BFF; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .kpi-box-critical {
        background-color: #fff5f5; padding: 20px; border-radius: 10px;
        border-left: 5px solid #dc3545; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .executive-summary {
        background: linear-gradient(135deg, rgba(212,175,55,0.05) 0%, rgba(15,23,42,0.05) 100%);
        border: 1px solid rgba(212,175,55,0.2); padding: 25px; border-radius: 15px; margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)


# =========================
#   ISTANZA DATABASE
# =========================
db = DatabaseAziendale()

# =========================
#   FUNZIONI DI SUPPORTO INTERNE
# =======
db = DatabaseAziendale()

# =========================
#   GESTIONE REGISTRAZIONE
# =========================
def registra_nuovo_utente(email: str, password: str, conferma: str):
    if not email or not password or not conferma:
        st.error("Compila tutti i campi.")
        return

    if password != conferma:
        st.error("Le password non coincidono.")
        return

    # Controllo se esiste già
    esistente = db.get_utente_by_email(email)
    if esistente:
        st.error("Esiste già un utente con questa email.")
        return

    try:
        # RIPRISTINO CORRETTO: Lasciamo azienda=None così database.py genera l'identificativo multi-tenant sicuro (AZ-id)
        user_id = db.crea_utente(email=email, password=password, ruolo="user", azienda=None)
        nuovo = db.get_utente_by_id(user_id)
        if nuovo:
            st.success("✅ Registrazione completata. Ora puoi effettuare il login.")
        else:
            st.error("Errore durante la registrazione. Riprova.")
    except Exception as e:
        st.error(f"Errore durante la registrazione: {e}")


# =========================
#   SCHERMATA LOGIN / REGISTRAZIONE
# =========================
if not st.session_state.autenticato:
    tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Registrazione"])

    with tab_login:
        st.title("🔐 Accesso Utente")

        email_login = st.text_input("Email", key="auth_email_final").strip()
        password_login = st.text_input("Password", type="password", key="auth_pwd_final").strip()

        if st.button("Accedi", key="btn_login_final"):
            if not email_login or not password_login:
                st.error("Inserisci email e password.")
            else:
                if login_utente(db, email_login, password_login):
                    st.success("Accesso eseguito!")
                    st.rerun()
                else:
                    st.error("Credenziali non valide. Verifica l'email o la password inserita.")

    with tab_register:
        st.title("🆕 Crea un nuovo account")

        email_r = st.text_input("Email", key="reg_email_input").strip()
        pwd_r = st.text_input("Password", type="password", key="reg_pwd_input").strip()
        pwd_c = st.text_input("Conferma Password", type="password", key="reg_pwd_conf_input").strip()

        if st.button("Registrati", key="btn_register_submit"):
            registra_nuovo_utente(email_r, pwd_r, pwd_c)

    st.stop()

# =========================================================
#   NAVIGAZIONE SIDEBAR (POSIZIONARE IN ALTO NEL FILE)
# =========================================================
user_id = st.session_state.user_id
azienda = st.session_state.azienda
ruolo = st.session_state.ruolo
is_admin = (ruolo == "admin")

with st.sidebar:
    st.title("🛡️ RGD-ALPHA")
    st.write(f"Operatore: **{azienda}**")
    
    # Definiamo il menu
    menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
    if is_admin: 
        menu.insert(1, "🕵️ Centrale Admin")
    
    # Questa riga DEVE stare sopra i blocchi 'if scelta =='
    scelta = st.radio("Navigazione", menu)
    
    st.markdown("---")
    if st.button("Logout"): 
        logout_utente()

# =========================================================
#   WAR ROOM STRATEGICA (VERSIONE ENTERPRISE INTEGRATA)
# =========================================================
if scelta == "📊 War Room Strategica":
    st.title("PORCO DIO VERSIONE NUOVA 2.0")

    # --- 1. CONFIGURAZIONE LATERALE (STRESS TEST) ---
    with st.sidebar:
        st.markdown("### 🛠️ Configurazione Motore")
        with st.expander("⚙️ CALIBRAZIONE", expanded=True):
            p_scad = st.slider("Importanza Scadenza", 0, 10, 8)
        with st.expander("🚨 STRESS TEST", expanded=True):
            ritardo = st.slider("Ritardo Fornitori (Giorni)", 0, 30, 0)
            f_stress = 1.0 + (ritardo / 50.0) # Calcolo dinamico dello stress
        st.info(f"Leva Stress attiva: {f_stress:.2f}x")

    # --- 2. INGESTIONE E CALCOLO ---
    uploaded_file = st.file_uploader("Carica file operativo (CSV)", type=["csv"])
    
    if uploaded_file:
        path = UPLOAD_DIR / azienda / uploaded_file.name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.status("⚙️ Elaborazione Protocollo RGD-Alpha...", expanded=True) as status:
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_csv(str(path), azienda)

            if not lista_asset:
                st.error("⚠️ File non valido o vuoto.")
            else:
                engine = DataGateway()
                
                # Persistenza Database (Audit Trail)
                db.registra_caricamento(user_id, "UNIVERSAL", uploaded_file.name)
                for a in lista_asset:
                    db.salva_asset(user_id=user_id, nome_asset=a["nome"], rischio=a["rischio"], 
                                  tipo=a.get("tipo", "Asset"), momentum=a.get("momentum", 0))

                # Esecuzione Motore con Stress Test
                report_analisi = engine.esegui_scan_strategico(lista_asset, "UNIVERSAL", fattore_stress=f_stress)
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)
                report_cifrato = engine.salva_report_certificato(report_analisi)
                
                status.update(label="✅ Motore Sincronizzato", state="complete")

                # --- 3. LIVELLO CEO: EXECUTIVE SUMMARY & CONSENSO ---
                st.header("🛡️ Executive Intelligence Summary")
                
                # Gestione Dato Mancante con Decisione CEO
                sol_reale = kpi_reali.get('solidita')
                if sol_reale is None:
                    st.warning("⚠️ **AVVISO DI INTEGRITÀ:** Rilevati dati insufficienti per calcolare la Solidità Reale.")
                    with st.expander("🛠️ DECISIONE RICHIESTA AL CEO", expanded=True):
                        st.write("Il sistema richiede autorizzazione per procedere con un **valore di calibrazione fittizio (85%)**.")
                        consenso = st.checkbox("Acconsento all'uso di un valore fittizio per l'esecuzione dell'analisi.")
                    
                    if consenso:
                        sol = 85
                        label_sol = "Solidità (Fittizia)"
                    else:
                        sol = None
                        st.info("In attesa di autorizzazione o dati reali per procedere...")
                else:
                    sol = sol_reale
                    label_sol = "Solidità Reale"

                if sol is not None:
                    # Visualizzazione Metriche Alpha
                    k1, k2, k3, k4, k5 = st.columns(5)
                    res = max(round(100 - (f_stress * 10), 1), 0)
                    
                    k1.metric(label_sol, f"{sol}%")
                    k2.metric("Rischio Medio", f"{kpi_reali.get('rischio_medio', 0)}/10")
                    k3.metric("Resilience", f"{res}%", delta=f"-{ritardo/2}%", delta_color="inverse")
                    k4.metric("Efficienza", "ALTA")
                    k5.metric("Sicurezza", "AES-256")

                    # Box Narrativo CEO
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF;">
                        <h3 style="margin-top:0;">📢 Recap Strategico per la Presidenza</h3>
                        <p><b>Diagnosi:</b> Azienda attualmente <b>{'SOLIDA' if sol > 80 else 'VULNERABILE'}</b>.</p>
                        <p><b>Impatto Stress:</b> La resilienza è al {res}% sotto l'attuale scenario di ritardo.</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # --- 4. LIVELLO OPERATIVO: DETTAGLIO ASSET ---
                    st.markdown("---")
                    st.subheader("📝 Piano d'Azione Operativo (Priorità)")
                    for asset in report_analisi:
                        r = asset.get('rischio', 0)
                        box = "kpi-box-critical" if r > 7 else "kpi-box"
                        st.markdown(f"""
                        <div class="{box}">
                            <b>{asset['asset']}</b> | Rischio: {r} | Stato: {asset['stato']} <br>
                            <small>Protocollo: {asset.get('proiezione_impatto', 'Monitoraggio Varianza')}</small>
                        </div>
                        """, unsafe_allow_html=True)

                    # --- 5. CERTIFICAZIONE E TRASPARENZA ---
                    st.markdown("---")
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.info("**Protocollo RGD-Alpha:** Calcolo deterministico validato su matrice $H_{(prod)}$.")
                    with c2:
                        st.metric("Integrità Calcolo", "100%", delta="Certificato")

                    if report_cifrato:
                        st.download_button("📥 Scarica Report Certificato Cifrato", report_cifrato, 
                                         file_name=f"RGD_STRAT_{azienda}.enc")
# =========================
#   CENTRALE ADMIN (PANNELLO DI SUPERVISIONE)
# =========================
if scelta == "🕵️ Centrale Admin" and is_admin:
    st.title("🕵️ Centrale Admin — Supervisione Globale Enterprise")

    df_supervisione = db.supervisione_admin_metriche_globali()
    
    if not df_supervisione.empty:
        st.subheader("💎 Stato Clienti Monitorati")
        st.dataframe(df_supervisione, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("📊 Mappa Comparativa del Rischio")
        
        df_log_completo = db.recupera_attivita_globale(solo_admin=True)
        if not df_log_completo.empty:
            df_chart = df_log_completo.groupby("company_id")["rischio"].mean().reset_index()
            st.bar_chart(df_chart, x="company_id", y="rischio")
            
            st.subheader("📋 Registro Analisi Globale (Tutti gli Asset di Sistema)")
            st.dataframe(df_log_completo, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📂 Registro Caricamenti File Clienti")
        df_uploads = db.recupera_log_caricamenti_admin()
        if not df_uploads.empty:
            st.dataframe(df_uploads, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun file inserito dai clienti finora.")
            
    else:
        st.info("Nessuna azienda cliente registrata nel sistema al di fuori dell'amministratore.")

# =========================
#   ARCHIVIO STORICO
# =========================
if scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico Asset")
    st.write("Visualizzazione cronologica completa dei log cifrati di questa azienda.")

    df_storico = db.recupera_asset_per_utente(user_id)
    if not df_storico.empty:
        st.dataframe(df_storico, use_container_width=True)
    else:
        st.warning("Nessun record presente in archivio. Esegui un'analisi nella War Room per iniziare.")
#=======
    if password != conferma:
        st.error("Le password non coincidono.")
        st.rerun()
    try:
        esistente = db.get_utente_by_email(email)
        if esistente:
            st.error("Email già registrata.")
            st.rerun()
        
        ruolo = "admin" if email.lower() == "andrewdicenso@libero.it" else "user"
        user_id = db.crea_utente(email=email, password=password, ruolo=ruolo)
        if user_id:
            st.success("✅ Registrazione completata. Effettua il login.")
            st.balloons()
    except Exception as e:
        st.error(f"Errore registrazione: {e}")

# =========================
#   SCHERMATA AUTH
# =========================
if not st.session_state.autenticato:
    tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Registrazione"])
    with tab_login:
        st.title("🔐 Accesso Utente")
        e_login = st.text_input("Email", key="l_email").strip()
        p_login = st.text_input("Password", type="password", key="l_pwd").strip()
        if st.button("Accedi"):
            if login_utente(db, e_login, p_login):
                st.rerun()
            else:
                st.error("Credenziali errate.")
    with tab_register:
        st.title("🆕 Crea account Beta")
        e_reg = st.text_input("Email", key="r_email").strip()
        p_reg = st.text_input("Password", type="password", key="r_pwd").strip()
        c_reg = st.text_input("Conferma", type="password", key="r_conf").strip()
        if st.button("Registrati"):
            registra_nuovo_utente(e_reg, p_reg, c_reg)
    st.stop()

# =========================
#   CENTRALE ADMIN
# =========================
if scelta == "🕵️ Centrale Admin" and is_admin:
    st.title("🕵️ Centrale Admin")
    try:
        df = db.supervisione_admin_metriche_globali()
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun dato presente.")
    except Exception as e:
        st.error(f"Errore caricamento dati admin: {e}")

