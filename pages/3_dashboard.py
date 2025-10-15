# pages/3_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ===============================
# STREAMLIT CONFIG
# ===============================
st.set_page_config(
    page_title="Analytical Dashboard – Parasite Monitoring",
    page_icon="🪲",
    layout="wide",                     # <<< forces full-width mode
    initial_sidebar_state="expanded",
)


# ---------- Data ----------
@st.cache_data
def load_data():
    df = pd.read_excel("temp_humid_data.xlsx", sheet_name="Sheet3")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["temperature_mean", "relativehumidity_mean", "no. of Adult males"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Date", "temperature_mean", "relativehumidity_mean", "no. of Adult males"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Feature temporali (senza usare locale di sistema)
    IT_MONTHS = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
                 "luglio","agosto","settembre","ottobre","novembre","dicembre"]
    IT_WEEKDAYS = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]  # 0=Mon

    df["month"] = df["Date"].dt.month            # 1..12
    df["month_name"] = df["month"].apply(lambda m: IT_MONTHS[m-1])

    df["weekday"] = df["Date"].dt.weekday        # 0..6 (Mon..Sun)
    df["weekday_name"] = df["weekday"].apply(lambda d: IT_WEEKDAYS[d])

    # ISO week (int)
    df["week"] = df["Date"].dt.isocalendar().week.astype(int)

    # Rolling stats (7 giorni)
    df["adults_7d_ma"] = df["no. of Adult males"].rolling(7, min_periods=1).mean()
    df["temp_7d_ma"] = df["temperature_mean"].rolling(7, min_periods=1).mean()
    df["hum_7d_ma"] = df["relativehumidity_mean"].rolling(7, min_periods=1).mean()
    return df


def main():
    st.title("📊 Dashboard Analitica — Cicalino Data")
    st.caption("Visualizzazioni professionali sui dati storici: trend, relazioni, pattern stagionali e distribuzioni.")

    df = load_data()

    # ------------------ Sidebar filtri ------------------
    st.sidebar.header("⚙️ Filtri")
    dmin, dmax = df["Date"].min().date(), df["Date"].max().date()
    start_date = st.sidebar.date_input("Data iniziale", dmin)
    end_date   = st.sidebar.date_input("Data finale", dmax)
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    subset = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

    if subset.empty:
        st.warning("Nessun dato per l'intervallo selezionato.")
        return

    # ------------------ KPI cards ------------------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🪲 Totale adulti (periodo)", f"{subset['no. of Adult males'].sum():.0f}")
    k2.metric("🌡️ Temperatura media", f"{subset['temperature_mean'].mean():.1f} °C")
    k3.metric("💧 Umidità media", f"{subset['relativehumidity_mean'].mean():.1f} %")
    max_row = subset.loc[subset['no. of Adult males'].idxmax()]
    k4.metric("🔝 Picco adulti", f"{max_row['no. of Adult males']:.0f}", max_row['Date'].strftime("%Y-%m-%d"))

    # ------------------ Tabs layout ------------------
    t1, t2, t3, t4 = st.tabs(["📈 Panoramica", "🔗 Relazioni", "📅 Pattern", "📦 Distribuzioni"])

    # ================== TAB 1: Panoramica ==================
    with t1:
        st.subheader("Trend delle catture (7d MA)")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=subset["Date"], y=subset["no. of Adult males"],
            name="Adulti (giornaliero)", mode="lines", line=dict(width=1)
        ))
        fig_trend.add_trace(go.Scatter(
            x=subset["Date"], y=subset["adults_7d_ma"],
            name="Adulti (media mobile 7g)", mode="lines",
            line=dict(width=3)
        ))
        fig_trend.update_layout(
            xaxis_title="Data", yaxis_title="N. adulti maschi",
            legend=dict(orientation="h")
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.subheader("Andamento meteo (Temperatura & Umidità)")
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Scatter(x=subset["Date"], y=subset["temp_7d_ma"], name="Temp (7d MA)", mode="lines"),
            secondary_y=False
        )
        fig_dual.add_trace(
            go.Scatter(x=subset["Date"], y=subset["hum_7d_ma"], name="Umidità (7d MA)", mode="lines"),
            secondary_y=True
        )
        fig_dual.update_yaxes(title_text="Temperatura (°C)", secondary_y=False)
        fig_dual.update_yaxes(title_text="Umidità (%)", secondary_y=True)
        fig_dual.update_layout(xaxis_title="Data", legend=dict(orientation="h"))
        st.plotly_chart(fig_dual, use_container_width=True)

    # ================== TAB 2: Relazioni ==================
    with t2:
        c1, c2 = st.columns([1,1])
        with c1:
            st.subheader("Temperatura vs Umidità")
            fig_scatter = px.scatter(
                subset, x="temperature_mean", y="relativehumidity_mean",
                size="no. of Adult males", color="no. of Adult males",
                color_continuous_scale="Plasma",
                labels={
                    "temperature_mean": "Temperatura (°C)",
                    "relativehumidity_mean": "Umidità (%)",
                    "no. of Adult males": "Adulti maschi"
                },
                title="Relazione 2D con intensità catture"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        with c2:
            st.subheader("Densità congiunta T–U")
            fig_density = px.density_heatmap(
                subset, x="temperature_mean", y="relativehumidity_mean",
                nbinsx=30, nbinsy=30, histfunc="avg", z="no. of Adult males",
                color_continuous_scale="Viridis",
                labels={
                    "temperature_mean": "Temperatura (°C)",
                    "relativehumidity_mean": "Umidità (%)",
                    "no. of Adult males": "Adulti (media)"
                },
                title="Heatmap densità (media adulti per cella)"
            )
            st.plotly_chart(fig_density, use_container_width=True)

        st.subheader("Matrice di correlazione")
        corr_cols = ["temperature_mean", "relativehumidity_mean", "no. of Adult males"]
        corr = subset[corr_cols].corr()
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r")
        st.plotly_chart(fig_corr, use_container_width=True)

        st.caption("Suggerimento: valori positivi/negativi forti indicano relazioni lineari; osserva comunque anche pattern non lineari nei grafici a dispersione.")

    # ================== TAB 3: Pattern ==================
    with t3:
        st.subheader("Media adulti per mese")
        monthly = (
            subset.groupby("month_name", sort=False)["no. of Adult males"]
            .mean()
            .reindex(pd.Series(subset["month_name"].unique(), name="month_name"))
        )
        fig_month = px.bar(
            monthly, labels={"value":"Adulti (media)", "month_name":"Mese"},
            title="Pattern medio mensile"
        )
        st.plotly_chart(fig_month, use_container_width=True)

        st.subheader("Media adulti per giorno della settimana")
        # Ordine naturale lun→dom (weekday: 0=Mon)
        order_week = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]
        # Gestione sicurezza se locale non disponibile
        if subset["weekday_name"].dtype == object:
            cats = pd.Categorical(subset["weekday_name"], categories=order_week, ordered=True)
            week_avg = subset.assign(weekday_name=cats).groupby("weekday_name")["no. of Adult males"].mean()
        else:
            week_avg = subset.groupby("weekday")["no. of Adult males"].mean()
            week_avg.index = ["lun","mar","mer","gio","ven","sab","dom"]
        fig_week = px.bar(week_avg, labels={"value":"Adulti (media)", "weekday_name":"Giorno"},
                          title="Pattern medio settimanale")
        st.plotly_chart(fig_week, use_container_width=True)

        st.subheader("Heatmap calendario (settimana vs giorno)")
        cal = subset.copy()
        cal["dow"] = cal["Date"].dt.weekday  # 0-6
        cal["week"] = cal["Date"].dt.isocalendar().week.astype(int)
        pivot = cal.pivot_table(index="week", columns="dow", values="no. of Adult males", aggfunc="mean")
        pivot = pivot.sort_index()
        fig_cal = px.imshow(
            pivot, aspect="auto", color_continuous_scale="YlOrRd",
            labels=dict(color="Adulti (media)")
        )
        fig_cal.update_xaxes(
            tickmode="array",
            tickvals=list(range(7)),
            ticktext=["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]
        )
        fig_cal.update_yaxes(title="Settimana ISO")
        fig_cal.update_layout(title="Intensità media per settimana/giorno")
        st.plotly_chart(fig_cal, use_container_width=True)

    # ================== TAB 4: Distribuzioni ==================
    with t4:
        c1, c2 = st.columns([1,1])
        with c1:
            st.subheader("Distribuzione catture (istogramma)")
            fig_hist = px.histogram(
                subset, x="no. of Adult males", nbins=30, marginal="box",
                labels={"no. of Adult males":"N. adulti maschi"},
                title="Distribuzione globale delle catture"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with c2:
            st.subheader("Box plot per mese")
            fig_box = px.box(
                subset, x="month_name", y="no. of Adult males",
                labels={"month_name":"Mese", "no. of Adult males":"N. adulti maschi"},
                title="Variabilità mensile"
            )
            st.plotly_chart(fig_box, use_container_width=True)

        st.subheader("📈 Scatter Matrix (ingrandita)")
        st.caption("Mostra relazioni pairwise tra temperatura, umidità e catture con codifica cromatica sull’intensità di infestazione.")

        fig_matrix = px.scatter_matrix(
            subset,
            dimensions=["temperature_mean", "relativehumidity_mean", "no. of Adult males"],
            color="no. of Adult males",
            color_continuous_scale="Viridis",
            title="Matrice di dispersione — relazioni tra variabili chiave",
            height=1000,   # 🔥 Altezza ingrandita
            width=1000     # 🔥 Larghezza ingrandita
        )

        fig_matrix.update_traces(diagonal_visible=False, marker=dict(size=6, opacity=0.7))
        fig_matrix.update_layout(
            font=dict(size=12),
            dragmode="select",
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(orientation="h", y=-0.2)
        )

        st.plotly_chart(fig_matrix, use_container_width=False)

    # ------------------ Note di lettura ------------------
    st.markdown(
        "<hr style='margin-top:2rem;margin-bottom:0.5rem;'>",
        unsafe_allow_html=True
    )
    st.caption(
        "Suggerimenti: usa i filtri temporali (sidebar) per focalizzarti su periodi specifici; "
        "confronta i trend smussati (media mobile 7g) con i valori giornalieri; "
        "osserva le aree ad alta densità nella heatmap T–U per individuare combinazioni meteo critiche."
    )


if __name__ == "__main__":
    main()


