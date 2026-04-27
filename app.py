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
        st.session_state.file = uploaded_file
        st.session_state.file_uploaded = True
        st.rerun()


# =========================================================
# 🎨 COULEURS ARKOSE
# =========================================================
COLOR_RANK = {
    "jaune": 1,
    "vert": 2,
    "bleu": 3,
    "rouge": 4,
    "noir": 5,
    "violet": 6
}


# =========================================================
# 🧹 CLEAN DATA
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

    df["couleur des prises"] = (
        df["couleur des prises"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    if "salle" not in df.columns:
        df["salle"] = "Inconnue"

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
# 🏆 BEST BLOCKS (COULEURS)
# =========================================================
def get_best_blocks(df):

    df = df.copy()

    df["rank"] = df["couleur des prises"].map(COLOR_RANK)
    df = df.dropna(subset=["rank"])

    if len(df) == 0:
        return None, None

    # 🏆 meilleur top
    best_all = df.loc[df["rank"].idxmax()]

    # ⚡ flash
    df_flash = df[df["flashé"].astype(str).str.lower().str.strip() == "oui"]

    if len(df_flash) > 0:
        df_flash = df_flash.dropna(subset=["rank"])
        best_flash = df_flash.loc[df_flash["rank"].idxmax()]
    else:
        best_flash = None

    return best_all, best_flash


# =========================================================
# 📊 STYLES (VERSION COULEUR)
# =========================================================
def compute_styles_top20(df):

    df = df.copy()

    df = df[df["couleur des prises"].isin(["rouge", "noir", "violet"])]

    styles = (
        df["styles"]
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


# =========================================================
# 🚀 APP
# =========================================================
if st.session_state.file_uploaded:

    df = pd.read_excel(st.session_state.file)
    df = clean_data(df)

    df_current_q = filter_current_quarter(df)
    df_previous_q = filter_previous_quarter_same_period(df)
    df_12m = filter_last_12_months(df)

    best_all, best_flash = get_best_blocks(df_12m)

    today = pd.Timestamp.today()
    year = today.year
    quarter = today.to_period("Q").quarter

    sessions_current = df_current_q["date"].nunique()
    sessions_previous = df_previous_q["date"].nunique()

    delta = sessions_current - sessions_previous
    pct = (delta / sessions_previous * 100) if sessions_previous > 0 else 0


    # =====================================================
    # 🧠 SYNTHÈSE
    # =====================================================
    st.markdown("### Synthèse")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"Séances - T{quarter} {year}",
        sessions_current,
        f"{delta:+} ({pct:.0f}%) vs trimestre précédent"
    )

    col2.metric(
        f"Meilleur Top {year}",
        best_all["couleur des prises"].capitalize() if best_all is not None else "N/A"
    )
    st.caption(f"Salle : {best_all.get('salle', 'Inconnue')}")

    col3.metric(
        f"Meilleur Flash {year}",
        best_flash["couleur des prises"].capitalize() if best_flash is not None else "N/A"
    )

    if best_flash is not None:
        st.caption(f"Salle : {best_flash.get('salle', 'Inconnue')}")


    # =====================================================
    # 📊 GRAPHIQUE STYLES
    # =====================================================
    st.markdown("## Analyse des styles")
    st.caption("Top zones de difficulté sur 12 mois")

    st.plotly_chart(
        px.bar(compute_styles_top20(df_12m), x="style", y="count"),
        use_container_width=True
    )


    # =====================================================
    # 🧠 COACH
    # =====================================================
    st.markdown("## Un mot du Coach")
    st.info("Continue sur ta dynamique actuelle.")


    # =====================================================
    # 📦 ANNEXE
    # =====================================================
    st.markdown("## Annexe")

    st.markdown("""
|  | 1 barre | 2 barres | 3 barres | 4 barres | 5 barres |
| - | ------- | -------- | -------- | -------- | -------- |
| 🟡 | 3 | 3+ | 4a | 4a+ | 4b |
| 🟢 | 4b | 4c | 5a | 5a+ | 5b |
| 🔵 | 5a+ | 5b | 5b+ | 5c | 5c+ |
| 🔴 | 5c+ | 6a | 6a+ | 6b | 6b+ |
| ⚫ | 6b | 6b+ | 6c | 6c+ | 7a |
| 🟣 | 7a | 7a+ | 7b | 7b+ | 7c / 7c+ |
""")
