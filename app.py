import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib


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
# 📅 FILTRES
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
# 🏆 BEST BLOCKS (12M)
# =============================
def get_best_blocks(df):

    best_all = df.loc[df["grade_score"].idxmax()]

    df_flash = df[df["flashé"] == "Oui"]

    if len(df_flash) > 0:
        best_flash = df_flash.loc[df_flash["grade_score"].idxmax()]
    else:
        best_flash = None

    return best_all, best_flash


# =============================
# 🧠 COACH INTELLIGENT
# =============================
def get_coach_message(df_12m, df_current_q, df_previous_q):

    sessions_current = df_current_q["date"].dt.date.nunique()
    sessions_previous = df_previous_q["date"].dt.date.nunique()

    weekly_avg = df_12m.groupby(df_12m["date"].dt.to_period("W")).size().mean()

    last_week = df_12m[
        df_12m["date"] >= (pd.Timestamp.today() - pd.Timedelta(days=7))
    ].shape[0]

    best_recent = df_12m.sort_values("date").tail(20)["grade_score"].max()

    messages = []

    if sessions_current < sessions_previous:
        messages.append("📉 Moins de séances que le trimestre précédent → attention à la régularité.")
    else:
        messages.append("📈 Bonne régularité ce trimestre.")

    if last_week < weekly_avg * 0.6:
        messages.append("⚡ Semaine légère → idéal pour technique ou récupération.")

    if best_recent >= df_12m["grade_score"].quantile(0.9):
        messages.append("🔥 Tu es en forme → bon moment pour tenter un projet dur.")

    if len(messages) == 0:
        messages.append("🧠 Continue à grimper propre et régulier.")

    return " ".join(messages)


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
    # 📅 DATA
    # =============================
    df_current_q = filter_current_quarter(df)
    df_previous_q = filter_previous_quarter(df)
    df_12m = filter_last_12_months(df)

    weekly_12m = compute_weekly_score(df_12m)

    best_all, best_flash = get_best_blocks(df_12m)

    # =============================
    # 📊 KPI
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

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"Séances T{current_q.quarter} {current_q.year}",
        sessions_current,
        f"{delta:+} ({pct:.0f}%) vs T{prev_q.quarter} {prev_q.year}"
    )

    col2.metric(
        "Bloc le plus dur (12 mois)",
        int(best_all["grade_score"])
    )

    if best_flash is not None:
        col3.metric(
            "Meilleur flash (12 mois)",
            int(best_flash["grade_score"])
        )
    else:
        col3.metric(
            "Meilleur flash (12 mois)",
            "N/A"
        )


    # =============================
    # 📊 GRAPH 1
    # =============================
    st.markdown("## Volume de la semaine")

    st.caption(
        "Volume = somme des difficultés des blocs réalisés chaque semaine (sur les 12 derniers mois)."
    )

    st.plotly_chart(plot_weekly(weekly_12m), use_container_width=True)


    # =============================
    # 📊 GRAPH 2
    # =============================
    st.markdown("## Analyse des styles")

    st.caption(
        "Répartition des styles parmi les 20% des voies les plus difficiles sur les 12 derniers mois."
    )

    style_counts = compute_styles_top20(df_12m)

    st.plotly_chart(plot_styles(style_counts), use_container_width=True)


    # =============================
    # 🧠 COACH
    # =============================
    st.markdown("## 🧠 Un mot de ton Coach")

    st.info(get_coach_message(df_12m, df_current_q, df_previous_q))
