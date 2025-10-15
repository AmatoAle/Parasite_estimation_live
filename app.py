import streamlit as st

st.set_page_config(
    page_title="ALGORITMI DI INTELLIGENZA ARTIFICIALE PER IL MONITORAGGIO DIINFESTANTI IN OLIVOCOLTURA",
    page_icon="🪲",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🪲 ALGORITMI DI INTELLIGENZA ARTIFICIALE PER IL MONITORAGGIO DI INFESTANTI IN OLIVOCOLTURA")

st.markdown("""
CORSO DI LAUREA IN SCIENZE E TECNOLOGIE ALIMENTARI
autore: Alessandra Amato ;  supervisore: Prof. Francesco Giannino""")           
st.markdown("""
Benvenuto nella piattaforma interattiva per la previsione e analisi delle catture di parassiti.  
Il sistema è composto da tre sezioni principali:
1. **Home**  Introduzione e obiettivi.  
2. **Forecast (ARIMAX)**  Previsione automatica basata sui dati storici Cicalino.  
3. **Dashboard Analitica**  Visualizzazioni interattive e analisi what-if.
""")

st.sidebar.success("Usa il menu in alto a sinistra per navigare tra le pagine.")
