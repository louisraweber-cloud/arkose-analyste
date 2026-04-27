import streamlit as st
import pandas as pd
import plotly.express as px


# =============================
# 🎯 CONFIG APP
# =============================
st.set_page_config(page_title="Arkose Analyste", layout="centered")
st.title("Arkose Analyste")


# =============================
# 📂 UPLOAD
# =============================
uploaded_file = st.file_uploader(
    "Importer ton fichier Arkose (Excel)",
    type=["xlsx"]
)


# =============================
# 🧹 NETTOYAGE
# =============================
def clean_data(df):
    df = df.copy()

    df = df.rename(columns={
        "date de réussite": "date",
        "niveau": "level",
        "sous-niveau": "sub_level"
    })

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["level"] = pd.to_numeric(df["level"], errors="coerce")
    df["sub_level"] = pd.to_numeric(df["sub_level"], errors="coerce")

    df["grade_score"] = (df["level"] - 6) * 5 + df["sub_level"]

    return df


# =============================
# 📅 TRIMESTRES (FAIR COMPARISON)
# =============================
def filter_current_quarter(df):
    today = pd.Timestamp.today()
    start = today.to_period("Q").start_time
    return df[(df["date"] >= start) & (df["date"] <= today)]


def filter_previous_quarter_same_period(df):
    today = pd.Timestamp.today()

    start_current = today.to_period("Q").start_time
    start_prev = (today.to_period("Q") - 1).start_time

    days_offset = today - start_current
    end_prev = start_prev + days_offset

    return df[
        (df["date"] >= start_prev) &
        (df["date"] <= end_prev)
    ]


# =============================
# 📅 12 MOIS
# =============================
def filter_last_12_months(df):
    today = pd.Timestamp.today()
    one_year_ago = today - pd.DateOffset(years=1)

    return df[(df["date"] >= one_year_ago) & (df["date"] <= today)]


# =============================
# 📈 WEEKLY SCORE
# =============================
def compute_weekly_score(df):
    df = df.copy()
    df["week"] = df["date"].dt.to_period("W")

    weekly = df.groupby("week").agg(
        total_score=("grade_score", "sum")
    ).reset_index()

    weekly["week"] = weekly["week"].dt.start_time
    weekly["moving_avg"] = weekly["total_score"].rolling(4).mean()

    return weekly


# =============================
# 🚀 APP
# =============================
if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df = clean_data(df)

    # =============================
    # 📅 DATASETS
    # =============================
    df_current_q = filter_current_quarter(df)
    df_previous_q = filter_previous_quarter_same_period(df)
    df_12m = filter_last_12_months(df)

    weekly_12m = compute_weekly_score(df_12m)

    # =============================
    # 📊 KPI SÉANCES
    # =============================
    st.markdown("### Synthèse")

    today = pd.Timestamp.today()
    current_q = today.to_period("Q")
    prev_q = current_q - 1

    sessions_current = df_current_q["date"].dt.date.nunique()
    sessions_previous = df_previous_q["date"].dt.date.nunique()

    if sessions_previous > 0:
        delta = sessions_current - sessions_previous
        pct = (delta / sessions_previous) * 100
    else:
        delta = 0
        pct = 0

    arrow = "↑" if delta >= 0 else "↓"

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"Séances T{current_q.quarter} {current_q.year}",
        sessions_current,
        f"{arrow} {delta:+} ({pct:.0f}%) vs T{prev_q.quarter} {prev_q.year}",
        delta_color="normal"
    )


    # =============================
    # 📊 GRAPH 1 - VOLUME
    # =============================
    st.markdown("## Volume de la semaine")

    st.caption(
        "Volume = somme des difficultés des blocs réalisés chaque semaine (12 derniers mois)."
    )

    fig = px.area(
        weekly_12m,
        x="week",
        y="total_score",
        line_shape="spline"
    )

    fig.add_scatter(
        x=weekly_12m["week"],
        y=weekly_12m["moving_avg"],
        mode="lines",
        line=dict(width=2, dash="dash"),
        name="Moyenne 4 semaines"
    )

    fig.update_layout(
        template="simple_white",
        yaxis_title="",
        xaxis_title="",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


    # =============================
    # 🧠 COACH SIMPLE
    # =============================
    st.markdown("## 🧠 Un mot de ton Coach")

    messages = []

    weekly_avg = weekly_12m["total_score"].mean()
    last_week = weekly_12m.tail(1)["total_score"].values[0] if len(weekly_12m) > 0 else 0

    if sessions_current < sessions_previous:
        messages.append("📉 Moins de séances que le trimestre précédent.")

    if last_week < weekly_avg * 0.6:
        messages.append("⚡ Semaine légère → récup ou technique.")

    if len(messages) == 0:
        messages.append("🧠 Bonne dynamique, continue comme ça.")

    st.info(" ".join(messages))
