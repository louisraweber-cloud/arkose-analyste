import streamlit as st
import pandas as pd
import plotly.express as px
import time


# =========================================================
# 🎯 CONFIG
# =========================================================
st.set_page_config(page_title="Arkose Analyste", layout="centered")


# =========================================================
# 🧠 STATE
# =========================================================
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False

if "processing" not in st.session_state:
    st.session_state.processing = False


# =========================================================
# 🧭 HEADER
# =========================================================
st.title("Arkose Analyste")

if st.session_state.file_uploaded:
    if st.button("🔄 Changer de fichier"):
        st.session_state.file_uploaded = False
        st.rerun()


# =========================================================
# 🟦 LANDING
# =========================================================
if not st.session_state.file_uploaded and not st.session_state.processing:

    st.markdown("""
### Importer tes données Arkose

1. Accéder à ton compte : https://accounts.arkose.com/?userEdit=true  
2. Se connecter  
3. Scrolle un peu vers le bas puis clique sur **Exporter mes données**  
4. Importer le fichier Excel ci-dessous  
""")

    uploaded_file = st.file_uploader(
        "Importer ton fichier Arkose (Excel)",
        type=["xlsx"]
    )

    if uploaded_file is not None:
        st.session_state.processing = True
        st.session_state.temp_file = uploaded_file
        st.rerun()


# =========================================================
# ⏳ LOADING
# =========================================================
if st.session_state.processing:

    st.progress(0.5)
    st.write("Analyse des blocs...")

    time.sleep(0.3)

    st.session_state.file_uploaded = True
    st.session_state.file = st.session_state.temp_file
    st.session_state.processing = False

    st.rerun()


# =========================================================
# 🧗 GRADING ARKOSE (OFFICIEL)
# =========================================================
ARKOSE_GRADE_MAP = {
    "jaune": {1: "3", 2: "3+", 3: "4A", 4: "4A+", 5: "4B"},
    "vert": {1: "4B", 2: "4C", 3: "5A", 4: "5A+", 5: "5B"},
    "bleu": {1: "5A+", 2: "5B", 3: "5B+", 4: "5C", 5: "5C+"},
    "rouge": {1: "5C+", 2: "6A", 3: "6A+", 4: "6B", 5: "6B+"},
    "noir": {1: "6B", 2: "6B+", 3: "6C", 4: "6C+", 5: "7A"},
    "violet": {1: "7A", 2: "7A+", 3: "7B", 4: "7B+", 5: "7C"}
}


def to_font_grade(color, sub_level):
    color = str(color).strip().lower()
    sub_level = int(sub_level)
    return ARKOSE_GRADE_MAP.get(color, {}).get(sub_level, "?")


def format_block(row):
    if row is None:
        return "N/A"
    return to_font_grade(row["color"], row["sub_level"])


# =========================================================
# 🧹 DATA CLEANING
# =========================================================
def clean_data(df):
    df = df.copy()

    df = df.rename(columns={
        "date de réussite": "date",
        "couleur des prises": "color",
        "sous-niveau": "sub_level"
    })

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["sub_level"] = pd.to_numeric(df["sub_level"], errors="coerce")

    return df


# =========================================================
# 📅 FILTERS
# =========================================================
def filter_current_quarter(df):
    today = pd.Timestamp.today()
    start = today.to_period("Q").start_time
    return df[(df["date"] >= start) & (df["date"] <= today)]


def filter_previous_quarter_same_period(df):
    today = pd.Timestamp.today()
    start_current = today.to_period("Q").start_time
    start_prev = (today.to_period("Q") - 1).start_time

    offset = today - start_current
    end_prev = start_prev + offset

    return df[(df["date"] >= start_prev) & (df["date"] <= end_prev)]


def filter_last_12_months(df):
    today = pd.Timestamp.today()
    return df[df["date"] >= (today - pd.DateOffset(years=1))]


# =========================================================
# 📊 ANALYSES
# =========================================================
def compute_weekly_score(df):

    df = df.copy()
    df["week"] = df["date"].dt.to_period("W")

    weekly = df.groupby("week").size().reset_index(name="count")
    weekly["week"] = weekly["week"].dt.start_time

    return weekly


def compute_styles_top20(df):

    df = df.copy().dropna(subset=["styles"])

    top = df.head(int(len(df) * 0.2))

    styles = (
        top["styles"]
        .astype(str)
        .str.split("#")
        .explode()
        .str.strip()
    )

    styles = styles[styles != ""]

    result = styles.value_counts().reset_index()
    result.columns = ["style", "count"]

    return result


def get_best_blocks(df):

    df_valid = df.dropna(subset=["sub_level", "color"])

    best_all = df_valid.loc[df_valid["sub_level"].idxmax()]

    df_flash = df_valid[df_valid["flashé"] == "Oui"]

    if len(df_flash) > 0:
        best_flash = df_flash.loc[df_flash["sub_level"].idxmax()]
    else:
        best_flash = None

    return best_all, best_flash


# =========================================================
# 📈 VISUALISATIONS
# =========================================================
def plot_weekly(df):
    fig = px.bar(df, x="week", y="count")
    fig.update_layout(template="simple_white", showlegend=False)
    return fig


def plot_styles(df):

    if df.empty:
        return px.bar(title="Aucune donnée")

    fig = px.bar(df, x="style", y="count")
    fig.update_layout(template="simple_white", showlegend=False)

    return fig


# =========================================================
# 🚀 DASHBOARD
# =========================================================
if st.session_state.file_uploaded:

    df = pd.read_excel(st.session_state.file)
    df = clean_data(df)

    df_current_q = filter_current_quarter(df)
    df_previous_q = filter_previous_quarter_same_period(df)
    df_12m = filter_last_12_months(df)

    weekly = compute_weekly_score(df_12m)

    best_all, best_flash = get_best_blocks(df_12m)

    # =========================
    # SYNTHÈSE
    # =========================
    st.markdown("### Synthèse")

    col1, col2, col3 = st.columns(3)

    col1.metric("Séances", df_current_q["date"].nunique())

    col2.metric(
        "Meilleur Bloc 2026",
        format_block(best_all)
    )

    col3.metric(
        "Meilleur Flash 2026",
        format_block(best_flash)
    )

    # =========================
    # GRAPHS
    # =========================
    st.markdown("## Volume de la semaine")
    st.plotly_chart(plot_weekly(weekly), use_container_width=True)

    st.markdown("## Analyse des styles")
    st.caption("Top 20% des voies les plus dures sur 12 mois")
    st.plotly_chart(plot_styles(compute_styles_top20(df_12m)), use_container_width=True)

    # =========================
    # COACH
    # =========================
    st.markdown("## Un mot du Coach")
    st.info("Continue à grimper régulièrement et proprement.")

    # =========================
    # GRENIER
    # =========================
    st.markdown("## Grenier")

    st.markdown("""
|  | 1 barre | 2 barres | 3 barres | 4 barres | 5 barres |
| - | ------- | -------- | -------- | -------- | -------- |
| 🟡 | 3 | 3+ | 4A | 4A+ | 4B |
| 🟢 | 4B | 4C | 5A | 5A+ | 5B |
| 🔵 | 5A+ | 5B | 5B+ | 5C | 5C+ |
| 🔴 | 5C+ | 6A | 6A+ | 6B | 6B+ |
| ⚫ | 6B | 6B+ | 6C | 6C+ | 7A |
| 🟣 | 7A | 7A+ | 7B | 7B+ | 7C / 7C+ |
""")
