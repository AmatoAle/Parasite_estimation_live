import streamlit as st

def main():
    st.title("🏠 Home — Introduzione")

    st.markdown("""
### 🎯 Obiettivo
Studiare l’andamento delle catture di parassiti in funzione delle condizioni meteorologiche  
(temperatura e umidità) e sviluppare un modello **ARIMAX** per prevedere il rischio futuro.

### 🧩 Dataset
- Fonte: *Cicalino Historical Data* (`temp_humid_data.xlsx`)
- Variabili principali:
  - `Date`: giorno dell’osservazione
  - `temperature_mean`: temperatura media (°C)
  - `relativehumidity_mean`: umidità relativa media (%)
  - `no. of Adult males`: numero di maschi adulti (target)

### 🔍 Metodologia
- Analisi temporale dei dati storici.
- Stima automatica del modello **ARIMAX(p,d,q)** tramite minimizzazione dell’AIC.
- Forecast a un giorno con previsione degli agenti infestanti.
- Dashboard interattiva per interpretazione e analisi locale.
---
""")

if __name__ == "__main__":
    main()
