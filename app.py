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
# 📊 TRIMESTRES
# =============================
def filter_current_quarter(df):
    today = pd.Timestamp.today()
    start = today.to_period("Q").start_time
    return df[(df["date"] >= start) & (df["date"] <= today)]


def filter_previous_quarter(df):
    today = pd.Timestamp.today()
    current_q = today.to_period("Q")
    prev_q = current_q - 1

    return df[
        (df["date"] >= prev_q.start_time) &
        (df["date"] <= prev_q.end_time)
    ]


# =============================
# 📈 HEBDO SCORE
# =============================
def compute_weekly_score(df):

    df["week"] = df["date"].dt.to_period("W")

    weekly = df.groupby("week").agg(
        total_score=("grade_score", "sum")
    ).reset_index()

    weekly["week"] = weekly["week"].dt.start_time

    weekly["moving_avg"] = weekly["total_score"].rolling(4).mean()

    return weekly


# =============================
# 📊 STYLES TOP 20%
# =============================
def compute_styles_top20(df):

    df = df.copy()

    df = df.sort_values("grade_score", ascending=False)
    top20 = df.head(int(len(df) * 0.2))

    top20 = top20.dropna(subset=["styles"])

    styles = top20["styles"].str.split("#").explode()
    styles = styles.str.strip()
    styles = styles[styles != ""]

    style_counts = styles.value_counts().reset_index()
    style_counts.columns = ["style", "count"]

    return style_counts


# =============================
# 📈 GRAPH 1
# =============================
def plot_weekly(weekly):

    fig = px.area(
        weekly,
        x="week",
        y="total_score",
        line_shape="spline"
    )

    fig.update_traces(line=dict(width=3), opacity=0.9)

    fig.add_scatter(
        x=weekly["week"],
        y=weekly["moving_avg"],
        mode="lines",
        line=dict(width=2, dash="dash"),
        name="Moyenne 4 semaines"
    )

    fig.update_layout(
        template="simple_white",
        yaxis_title="",
        xaxis_title="",
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10)
    )

    fig.update_xaxes(showgrid=False, tickformat="%b %y")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)")

    return fig


# =============================
# 📊 GRAPH 2
# =============================
def plot_styles(style_counts):

    fig = px.bar(
        style_counts,
        x="style",
        y="count"
    )

    fig.update_layout(
        template="simple_white",
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    fig.update_xaxes(tickangle=45, showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)")

    return fig


# =============================
# 🚀 APP
# =============================
if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df = clean_data(df)

    # =============================
    # 📅 TRIMESTRE DATA
    # =============================
    df_current = filter_current_quarter(df)
    df_previous = filter_previous_quarter(df)

    weekly = compute_weekly_score(df_current)

    # =============================
    # 📊 KPI SEANCES
    # =============================
    st.markdown("### Synthèse")

    today = pd.Timestamp.today()
    current_q = today.to_period("Q")
    prev_q = current_q - 1

    sessions_current = df_current["date"].dt.date.nunique()
    sessions_previous = df_previous["date"].dt.date.nunique()

    if sessions_previous > 0:
        delta = sessions_current - sessions_previous
        pct = (delta / sessions_previous) * 100
    else:
        delta = 0
        pct = 0

    col1, col2 = st.columns(2)

    col1.metric(
        f"Séances T{current_q.quarter} {current_q.year}",
        sessions_current,
        f"{delta:+} ({pct:.0f}%) vs T{prev_q.quarter} {prev_q.year}"
    )

    # =============================
    # 📊 GRAPH 1
    # =============================
    st.markdown("## Volume de la semaine")

    st.caption(
        "Le volume correspond à la somme des difficultés des blocs réalisés chaque semaine "
        "(Jaune 1 barre = 1 point. +1 point pour chaque barre supplémentaire et donc une verte 2 barres = 7 points)."
    )

    st.plotly_chart(plot_weekly(weekly), use_container_width=True)


    # =============================
    # 📊 GRAPH 2
    # =============================
    st.markdown("## Analyse des styles")

    st.caption(
        "Répartition des styles parmi les 20% des voies les plus difficiles réalisées sur la période."
    )

    style_counts = compute_styles_top20(df_current)

    st.plotly_chart(plot_styles(style_counts), use_container_width=True)


    # =============================
    # 🧠 COACH SIMPLE
    # =============================
    if sessions_current < sessions_previous:
        st.warning("📉 Moins de séances que le trimestre précédent")
    else:
        st.success("📈 Bonne régularité ce trimestre")
