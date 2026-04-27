import streamlit as st
import pandas as pd
import plotly.express as px


# =========================================================
# 🎯 CONFIG
# =========================================================
st.set_page_config(page_title="Arkose Analyste", layout="centered")


# =========================================================
# 🧠 STATE
# =========================================================
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False


# =========================================================
# 🎯 HEADER
# =========================================================
st.title("Arkose Analyste")

if st.session_state.file_uploaded:
    if st.button("🔄 Changer de fichier"):
        st.session_state.file_uploaded = False
        st.rerun()


# =========================================================
# 🟦 LANDING
# =========================================================
if not st.session_state.file_uploaded:

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
        st.session_state.file_uploaded = True
        st.session_state.file = uploaded_file
        st.rerun()


# =========================================================
# 🧹 DATA CLEANING
# =========================================================
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


# =========================================================
# 🧗 GRADES
# =========================================================
def to_font_grade(level, sub_level):

    base_map = {
        1: "3",
        2: "4",
        3: "5",
        4: "6A",
        5: "6B",
        6: "6C",
        7: "7A",
        8: "7B"
    }

    base = base_map.get(int(level), "?")

    if sub_level <= 1:
        suffix = "-"
    elif sub_level <= 3:
        suffix = ""
    else:
        suffix = "+"

    if base in ["3", "4", "5"]:
        return base

    return f"{base}{suffix}"


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
def compute_styles_top20(df):

    df = df.copy().sort_values("grade_score", ascending=False)

    top = df.head(int(len(df) * 0.2))

    styles = (
        top["styles"]
        .dropna()
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

    best_all = df.loc[df["grade_score"].idxmax()]

    df_flash = df[df["flashé"] == "Oui"]

    if len(df_flash) > 0:
        best_flash = df_flash.loc[df_flash["grade_score"].idxmax()]
    else:
        best_flash = None

    return best_all, best_flash


# =========================================================
# 🚀 DASHBOARD
# =========================================================
if st.session_state.file_uploaded:

    df = pd.read_excel(st.session_state.file)
    df = clean_data(df)

    df_current_q = filter_current_quarter(df)
    df_previous_q = filter_previous_quarter_same_period(df)
    df_12m = filter_last_12_months(df)

    best_all, best_flash = get_best_blocks(df_12m)

    # =========================
    # SYNTHÈSE
    # =========================
    st.markdown("### Synthèse")

    today = pd.Timestamp.today()
    year = today.year
    quarter = today.to_period("Q").quarter

    sessions_current = df_current_q["date"].nunique()
    sessions_previous = df_previous_q["date"].nunique()

    delta = sessions_current - sessions_previous
    pct = (delta / sessions_previous * 100) if sessions_previous > 0 else 0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"Séances - T{quarter} {year}",
        sessions_current,
        f"{delta:+} ({pct:.0f}%) vs trimestre précédent"
    )

    col2.metric(
        f"Bloc le plus dur {year}",
        to_font_grade(best_all["level"], best_all["sub_level"])
    )

    col3.metric(
        f"Meilleur flash {year}",
        to_font_grade(best_flash["level"], best_flash["sub_level"]) if best_flash is not None else "N/A"
    )

    # =========================
    # GRAPHS
    # =========================
    st.markdown("## Analyse des styles")
    st.caption("Top 20% des voies les plus dures sur 12 mois")

    st.plotly_chart(
        px.bar(compute_styles_top20(df_12m), x="style", y="count"),
        use_container_width=True
    )

    # =========================
    # COACH
    # =========================
    st.markdown("## Un mot du Coach")
    st.info("Continue sur ta dynamique actuelle.")

    # =========================
    # ANNEXE
    # =========================
    st.markdown("## Annexe")

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
