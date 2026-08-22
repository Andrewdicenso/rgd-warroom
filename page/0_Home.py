import streamlit as st

st.set_page_config(
    page_title="RGD-Alpha | War Room Strategica",
    page_icon="🛡️",
    layout="wide"
)

# Header con logo/branding
st.title("🛡️ RGD-Alpha")
st.subheader("War Room Strategica Aziendale")

st.markdown("""
---
### Benvenuto nella tua War Room Personale

**RGD-Alpha** non è un semplice gestionale. È un sistema di **Risk Intelligence** 
che analizza il tuo inventario e calcola la **Solidità Operativa** della tua azienda.

---

### 🚀 Come Iniziare (30 secondi)

1. **Registrati** → Clicca su "Registrazione" in alto
2. **Carica un CSV** → Vai su "War Room Strategica" e carica il tuo file
3. **Ottieni l'Analisi** → Vedi immediatamente:
   - ✅ Solidità Operativa (%)
   - ⚠️ Rischio Medio (1-10)
   - 📊 Proiezione a 30/90 giorni

---

###  Cosa Ottieni

- **Analisi Predittiva**: Scopri quali asset rischiano di diventare obsoleti
- **Multi-Settore**: Supporto per alimentare, abbigliamento, e-commerce
- **Sicurezza Enterprise**: I tuoi dati sono cifrati con AES-256
- **Audit Trail Completo**: Ogni operazione è tracciata

---

### 🎯 Per Imprenditori Come Te

> "Mentre i comuni gestionali si limitano allo storico, 
> RGD-Alpha calcola in tempo reale la Solidità Operativa, 
> identificando i rischi **prima** che colpiscano il bilancio."

**Pronto a proteggere la tua azienda?**

👉 Clicca su **Registrazione** e inizia ora!
""")

# Call to action
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 1rem; color: white; margin: 2rem 0;'>
        <h3>🔐 Sicurezza Garantita</h3>
        <p>Dati cifrati AES-256 • Hosting Europeo • GDPR Compliant</p>
    </div>
    """, unsafe_allow_html=True)
