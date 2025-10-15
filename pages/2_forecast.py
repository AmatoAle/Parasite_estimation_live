# pages/2_forecast.py
from datetime import timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

@st.cache_data
def load_cicalino_data(path="temp_humid_data.xlsx", sheet="Sheet3"):
    df = pd.read_excel(path, sheet_name=sheet)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["temperature_mean", "relativehumidity_mean", "no. of Adult males"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Date", "temperature_mean", "relativehumidity_mean", "no. of Adult males"])
    df = df.sort_values("Date").set_index("Date").asfreq("D")
    # Interpola piccole lacune
    df[["temperature_mean", "relativehumidity_mean", "no. of Adult males"]] = (
        df[["temperature_mean", "relativehumidity_mean", "no. of Adult males"]]
        .interpolate(limit_direction="both")
    )
    y = df["no. of Adult males"].astype(float).rename("captures")
    ex = df[["temperature_mean", "relativehumidity_mean"]].rename(
        columns={"temperature_mean": "temperature", "relativehumidity_mean": "humidity"}
    )
    return y, ex

def auto_arimax(y, ex):
    """Selezione (p,d,q) via AIC su griglia compatta."""
    p_vals, d_vals, q_vals = range(4), (0, 1), range(4)
    best = (None, np.inf, None)
    for p in p_vals:
        for d in d_vals:
            for q in q_vals:
                try:
                    m = SARIMAX(
                        y, exog=ex, order=(p, d, q),
                        enforce_stationarity=False, enforce_invertibility=False
                    )
                    r = m.fit(disp=False)
                    if r.aic < best[1]:
                        best = ((p, d, q), r.aic, r)
                except Exception:
                    continue
    return best

def dynamic_pdq_interpretation(p, d, q, adf_p):
    msgs = []
    # d (stazionarietà)
    if d == 0 and adf_p is not None:
        if adf_p < 0.05:
            msgs.append("**d = 0** → la serie appare già **abbastanza stazionaria** (ADF p-value < 0.05).")
        else:
            msgs.append("**d = 0** → nessuna differenziazione: la stazionarietà sembra gestita da AR/MA o dagli esogeni (ADF p-value ≥ 0.05).")
    elif d >= 1 and adf_p is not None:
        if adf_p >= 0.05:
            msgs.append(f"**d = {d}** → applicata **differenziazione** per attenuare trend/non-stazionarietà (ADF p-value ≥ 0.05).")
        else:
            msgs.append(f"**d = {d}** → il modello preferisce differenziare per ottimizzare l’AIC (pur con ADF che suggerisce stazionarietà).")
    else:
        msgs.append(f"**d = {d}** → grado di differenziazione selezionato per migliorare la stabilità del modello.")
    # p (memoria)
    if p == 0:
        msgs.append("**p = 0** → il contributo delle osservazioni passate è limitato.")
    elif p in (1, 2):
        msgs.append(f"**p = {p}** → il modello sfrutta **memoria moderata** dal passato.")
    else:
        msgs.append(f"**p = {p}** → presenza di **memoria più profonda** nelle dipendenze temporali.")
    # q (media mobile)
    if q == 0:
        msgs.append("**q = 0** → il rumore residuo risulta **poco strutturato**.")
    elif q in (1, 2):
        msgs.append(f"**q = {q}** → il modello cattura **shock di breve periodo** nel residuo.")
    else:
        msgs.append(f"**q = {q}** → il rumore mostra **strutture più complesse**.")
    return msgs

def gentle_fidelity_notes(rmse, y_std):
    """
    Restituisce note 'dolci' sulla fedeltà del modello basate su RMSE rispetto alla variabilità naturale (σ).
    """
    msgs = []
    if y_std is None or y_std == 0 or np.isnan(y_std):
        msgs.append("La variabilità naturale della serie è molto bassa: piccoli scostamenti possono pesare relativamente di più.")
        return msgs

    ratio = rmse / y_std
    if ratio < 0.5:
        msgs.append("Gli scostamenti medi risultano **contenuti** rispetto alla variabilità naturale della serie.")
    elif ratio < 1.0:
        msgs.append("Gli scostamenti medi sono **in linea** con la variabilità naturale; il modello cattura buona parte del segnale, pur con rumore fisiologico.")
    else:
        msgs.append("Gli scostamenti medi sono **superiori** alla variabilità naturale; può essere utile considerare più dati o ulteriori fattori esplicativi.")
    msgs.append("Suggerimento: confronta il profilo addestrato con i picchi reali per valutare eventuali ritardi o attenuazioni.")
    return msgs

def main():
    st.title("📈 Forecast (ARIMAX Automatico – Cicalino Data)")
    st.caption("Selezione automatica di (p,d,q) via AIC. Previsione **+1 giorno** con esogene in **persistenza**. Previsioni e intervalli sono mostrati come **interi non negativi**.")

    # 1) Dati
    y, ex = load_cicalino_data()

    # 2) ADF informativo
    try:
        adf_stat, adf_p, *_ = adfuller(y)
        st.write(f"**Test ADF** (serie originale): statistica = {adf_stat:.2f}, p-value = {adf_p:.3f}")
        st.caption("p-value < 0.05 → indicazione di stazionarietà (regola pratica).")
    except Exception:
        adf_p = None
        st.info("Test ADF non disponibile su questa serie (lunghezza/qualità dati).")

    # 3) Stima automatica ARIMAX (AIC)
    (p, d, q), aic, res = auto_arimax(y, ex)
    if res is None:
        st.error("Nessun modello ARIMAX valido trovato.")
        st.stop()

    # 4) Forecast +1 (esogene in persistenza) → interi non negativi
    last_day = y.index.max()
    next_day = last_day + timedelta(days=1)
    ex_future = pd.DataFrame([ex.iloc[-1]], index=[next_day])

    fc = res.get_forecast(steps=1, exog=ex_future)
    # Grezzi
    y_hat_raw = float(fc.predicted_mean.iloc[0])
    conf = fc.conf_int(alpha=0.05).iloc[0]
    lower_raw = float(min(conf[0], conf[1]))
    upper_raw = float(max(conf[0], conf[1]))
    # → Interi non negativi (clipping + round)
    y_hat = max(0, int(round(y_hat_raw)))
    lower = max(0, int(round(lower_raw)))
    upper = max(0, int(round(upper_raw)))

    # 5) Grafico (ultimi 30 giorni) + forecast intero
    lookback = 30
    y_tail = y.iloc[-lookback:]
    fitted_tail = res.fittedvalues.reindex(y_tail.index)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=y_tail.index, y=y_tail, name="Actual", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=fitted_tail.index, y=fitted_tail, name="Fitted", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(
        x=[next_day], y=[y_hat], name="Forecast(+1, int)",
        mode="markers", marker=dict(color="green", size=10)
    ))
    fig.add_trace(go.Scatter(
        x=[next_day, next_day], y=[lower, upper],
        mode="lines", name="95% CI (int)", line=dict(color="green", dash="dot")
    ))
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="no. of Adult males",
        legend=dict(orientation="h")
    )
    st.plotly_chart(fig, use_container_width=True)

    # 6) Metriche principali (solo forecast/CI interi)
    m1, m2 = st.columns(2)
    m1.metric("Previsione giorno +1 (int)", f"{y_hat}")
    m2.metric("Intervallo 95% (int)", f"[{lower}, {upper}]")

    # 7) Diagnostica (nascosta/mostra): MAE, RMSE, AIC + note 'dolci'
    with st.expander("📊 Diagnostica modello (mostra/nascondi)", expanded=False):
        fitted = res.fittedvalues
        df_eval = pd.DataFrame({"y": y}).join(fitted.rename("yhat"), how="inner").dropna()
        mae = float(np.mean(np.abs(df_eval["y"] - df_eval["yhat"])))
        rmse = float(np.sqrt(np.mean((df_eval["y"] - df_eval["yhat"])**2)))
        y_std = float(df_eval["y"].std()) if df_eval["y"].std() > 0 else None

        d1, d2, d3 = st.columns(3)
        d1.metric("MAE", f"{mae:.3f}")
        d2.metric("RMSE", f"{rmse:.3f}")
        d3.metric("AIC", f"{aic:.2f}")

        st.markdown("**Lettura delle metriche**")
        for msg in gentle_fidelity_notes(rmse, y_std):
            st.markdown(f"- {msg}")

    # 8) Interpretazione dinamica di (p,d,q) e ADF
    st.subheader("🧠 Interpretazione del modello")
    for msg in dynamic_pdq_interpretation(p, d, q, adf_p):
        st.markdown(f"- {msg}")

    st.caption("Nota: per il giorno successivo le esogene (temperatura/umidità) sono assunte uguali all’ultimo giorno osservato (persistenza). "
               "Forecast e intervalli sono mostrati come **interi non negativi**; la diagnostica è pensata per una lettura **morbida** della qualità di adattamento.")

if __name__ == "__main__":
    main()
