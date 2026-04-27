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
    end = today

    return df[(df["date"] >= start) & (df["date"] <= end)]


def filter_previous_quarter(df):
    today = pd.Timestamp.today()

    current_q = today.to_period("Q")
    prev_q = current_q - 1

    return df[
        (df["date"] >= prev_q.start_time) &
        (df["date"] <= prev_q.end_time)
    ]


# =============================
# 🏆 BEST BLOCKS
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
# 📊 KPI COHERENT
# =============================
def compute_sessions(df):
    return df["date"].dt.date.nunique()


# =============================
# 🚀 APP
# =============================
if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df = clean_data(df)

    # =============================
    # 📅 DATA TRIMESTRES
    # =============================
    df_current = filter_current_quarter(df)
    df_previous = filter_previous_quarter(df)

    # =============================
    # 📊 KPI SÉANCES
    # =============================
    st.markdown("### Synthèse")

    today = pd.Timestamp.today()
    current_q = today.to_period("Q")
    prev_q = current_q - 1

    sessions_current = compute_sessions(df_current)
    sessions_previous = compute_sessions(df_previous)

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

    # =============================
    # 🏆 BEST BLOCKS
    # =============================
    best_all, best_flash = get_best_blocks(df)

    col2.metric(
        "Meilleur bloc (année)",
        int(best_all["grade_score"])
    )

    if best_flash is not None:
        col3.metric(
            "Meilleur flash (année)",
            int(best_flash["grade_score"])
        )
    else:
        col3.metric(
            "Meilleur flash (année)",
            "N/A"
        )


    # =============================
    # 🧠 COACH SIMPLE
    # =============================
    if len(df_current) > 0 and len(df_previous) > 0:
        if sessions_current < sessions_previous:
            st.warning("📉 Moins de séances que le trimestre précédent → attention à la régularité")
        else:
            st.success("📈 Bonne dynamique de fréquentation")
