import streamlit as st
import pandas as pd
import plotly.express as px
import time


# =========================================================
# 🎯 CONFIG
# =========================================================
st.set_page_config(page_title="Arkose Analyste", layout="centered")


# =========================================================
# 🧠 STATE (SAFE INIT)
# =========================================================
st.session_state.setdefault("file_uploaded", False)
st.session_state.setdefault("processing", False)
st.session_state.setdefault("file", None)


# =========================================================
# 🧭 HEADER
# =========================================================
st.title("Arkose Analyste")

if st.session_state.get("file_uploaded", False):
    if st.button("🔄 Changer de fichier"):
        st.session_state.file_uploaded = False
        st.session_state.file = None
        st.rerun()


# =========================================================
# 🟦 LANDING
# =========================================================
if not st.session_state.get("file_uploaded", False) and not st.session_state.get("processing", False):

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
if st.session_state.get("processing", False):

    st.progress(0.5)
    st.write("Analyse des blocs…")

    time.sleep(0.3)

    st.session_state.file_uploaded = True
    st.session_state.file = st.session_state.temp_file
    st.session_state.processing = False

    st.rerun()


# =========================================================
# 🧗 GRADING ARKOSE
# =========================================================

ARKOSE_GRADE_MAP = {

    "jaunes": {
        1: "3",
        2: "3+",
        3: "4A",
        4: "4A+",
        5: "4B"
    },

    "vertes": {
        1: "4B+",
        2: "4C",
        3: "5A",
        4: "5A+",
        5: "5A+"
    },

    "bleues": {
        1: "5B",
        2: "5B",
        3: "5B+",
        4: "5C",
        5: "5C"
    },

    "rouges": {
        1: "5C+",
        2: "6A",
        3: "6A+",
        4: "6B",
        5: "6B"
    },

    "noires": {
        1: "6B+",
        2: "6B+",
        3: "6C",
        4: "6C+",
        5: "6C+"
    },

    "violettes": {
        1: "7A",
        2: "7A+",
        3: "7B",
        4: "7B+",
        5: "7C"
    }
}


def to_font_grade(color, sub_level):

    if pd.isna(color) or pd.isna(sub_level):
        return "N/A"

    color = str(color).strip().lower()

    try:
        sub_level = int(float(sub_level))
    except:
        return "N/A"

    if color not in ARKOSE_GRADE_MAP:
        return "N/A"

    if sub_level not in ARKOSE_GRADE_MAP[color]:
        return "N/A"

    return ARKOSE_GRADE_MAP[color][sub_level]

# =========================================================
# 🧼 CLEAN DATA
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

    df = df.dropna(subset=["date", "color", "sub_level"])

    return df


def format_salle(value):
    if pd.isna(value):
        return "N/A"
    return str(value).replace("arkose/", "").strip().title()


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

    return df[
        (df["date"] >= start_prev) &
        (df["date"] <= end_prev)
    ]


def filter_last_12_months(df):
    today = pd.Timestamp.today()

    return df[
        df["date"] >= (today - pd.DateOffset(years=1))
    ]


# =========================================================
# 📊 ANALYSES
# =========================================================
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

    if df is None or df.empty:
        return None, None

    df_valid = df.dropna(subset=["sub_level", "color"])

    if df_valid.empty:
        return None, None

    best_all = df_valid.loc[df_valid["sub_level"].idxmax()]

    df_flash = df_valid[df_valid["flashé"] == "Oui"]

    if not df_flash.empty and df_flash["sub_level"].notna().any():
        best_flash = df_flash.loc[df_flash["sub_level"].idxmax()]
    else:
        best_flash = None

    return best_all, best_flash


# =========================================================
# 📈 VISUALISATIONS
# =========================================================
def plot_styles(df):

    if df.empty:
        return px.bar(title="Aucune donnée")

    fig = px.bar(df, x="style", y="count")

    fig.update_layout(
        template="simple_white",
        showlegend=False
    )

    return fig


# =========================================================
# 🚀 DASHBOARD
# =========================================================
if st.session_state.get("file_uploaded", False):

    df = pd.read_excel(st.session_state.file)
    df = clean_data(df)

    df_current_q = filter_current_quarter(df)
    df_previous_q = filter_previous_quarter_same_period(df)
    df_12m = filter_last_12_months(df)

    best_all, best_flash = get_best_blocks(df_12m)

    if best_all is None:
        st.warning("Pas assez de données pour analyser")
        st.stop()

    # =========================
    # SYNTHÈSE
    # =========================
    st.markdown("### Synthèse")

    current_sessions = df_current_q["date"].nunique()
    previous_sessions = df_previous_q["date"].nunique()

    if previous_sessions > 0:
        delta = current_sessions - previous_sessions
        pct = (delta / previous_sessions) * 100

        delta_text = (
            f"{delta:+} ({pct:.0f}%) vs trimestre précédent"
        )

    else:
        delta_text = "vs trimestre précédent"

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Séances",
        current_sessions,
        delta_text
    )

    col2.metric(
        "Bloc le plus dur",
        to_font_grade(
            best_all["color"],
            best_all["sub_level"]
        )
    )

    col2.caption(
        f"Salle : {format_salle(best_all['salle']) if 'salle' in best_all else 'N/A'}"
    )

    if best_flash is not None:

        col3.metric(
            "Meilleur flash",
            to_font_grade(
                best_flash["color"],
                best_flash["sub_level"]
            )
        )

        col3.caption(
            f"Salle : {format_salle(best_flash['salle']) if 'salle' in best_flash else 'N/A'}"
        )

    else:
        col3.metric("Meilleur flash", "N/A")

    # =========================
    # GRAPHE
    # =========================
    st.markdown("## Analyse des styles")

    st.caption(
        "Top 20% des voies les plus dures sur 12 mois"
    )

    st.plotly_chart(
        plot_styles(compute_styles_top20(df_12m)),
        use_container_width=True
    )

    # =========================
    # GRENIER
    # =========================
    st.markdown("## Grenier")

    st.markdown("""
|  | 1 barre | 2 barres | 3 barres | 4 barres | 5 barres |
| - | ------- | -------- | -------- | -------- | -------- |
| 🟡 | 3 | 3+ | 4A | 4A+ | 4B |
| 🟢 | 4B+ | 4C | 5A | 5A+ | 5A+ |
| 🔵 | 5B | 5B | 5B+ | 5C | 5C |
| 🔴 | 5C+ | 6A | 6A+ | 6B | 6B |
| ⚫ | 6B+ | 6B+ | 6C | 6C+ | 6C+ |
| 🟣 | 7A | 7A+ | 7B | 7B+ | 7C |
""")
