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
if not st.session_state.file_uploaded and not st.session_state.processing:

    st.markdown("## Analyse tes performances d’escalade")

    st.markdown("""
Cette application te permet de suivre :

- ton volume d’entraînement  
- ta progression  
- tes styles dominants  
- tes meilleurs blocs  

---

### 📥 Étapes

1. 👉 [Accéder à ton compte Arkose](https://accounts.arkose.com/?userEdit=true)  
2. Se connecter  
3. Cliquer sur **Exporter mes données**  
4. Télécharger le fichier Excel  
5. L’importer ci-dessous
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
# ⏳ LOADING SCREEN
# =========================================================
if st.session_state.processing:

    st.markdown("## Analyse de tes performances")

    st.progress(0.2)
    st.write("Chargement des données…")

    df_temp = pd.read_excel(st.session_state.temp_file)

    st.progress(0.6)
    st.write("Analyse des blocs…")

    time.sleep(0.4)

    st.progress(1.0)
    st.write("Finalisation…")

    st.session_state.file_uploaded = True
    st.session_state.file = st.session_state.temp_file
    st.session_state.processing = False

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
# 🧗 FONTAINEBLEAU
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
# 🎨 COLORS
# =========================================================
def arkose_level_icon(level):
    mapping = {
        1: "🟡",
        2: "🟢",
        3: "🔵",
        4: "🔴",
        5: "⚫",
        6: "🟣"
    }
    return mapping.get(int(level), "?")


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

    weekly = df.groupby("week").agg(
        total_score=("grade_score", "sum")
    ).reset_index()

    weekly["week"] = weekly["week"].dt.start_time
    weekly["moving_avg"] = weekly["total_score"].rolling(4).mean()

    return weekly


def compute_styles_top20(df):

    df = df.copy().sort_values("grade_score", ascending=False)

    top = df.head(int(len(df) * 0.2))

    styles = top["styles"].dropna().str.split("#").explode().str.strip()
    styles = styles[styles != ""]

    return styles.value_counts().reset_index(name="count").rename(columns={"index": "style"})


def get_best_blocks(df):

    best_all = df.loc[df["grade_score"].idxmax()]

    df_flash = df[df["flashé"] == "Oui"]

    if len(df_flash) > 0:
        best_flash = df_flash.loc[df_flash["grade_score"].idxmax()]
    else:
        best_flash = None

    return best_all, best_flash


def get_coach_message(df_12m, df_current_q, df_previous_q):

    cur = df_current_q["date"].dt.date.nunique()
    prev = df_previous_q["date"].dt.date.nunique()

    msgs = []

    if cur >= prev:
        msgs.append("Bonne régularité ce trimestre.")
    else:
        msgs.append("Moins de séances que le trimestre précédent.")

    return " ".join(msgs)


# =========================================================
# 📈 VISU
# =========================================================
def plot_weekly(df):

    fig = px.area(df, x="week", y="total_score", line_shape="spline")

    fig.update_traces(line=dict(width=3))

    fig.add_scatter(
        x=df["week"],
        y=df["moving_avg"],
        mode="lines",
        line=dict(width=2, dash="dash")
    )

    fig.update_layout(template="simple_white", showlegend=False)

    return fig


def plot_styles(df):

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
    col2.metric("Bloc le plus dur", to_font_grade(best_all["level"], best_all["sub_level"]))
    col3.metric(
        "Meilleur flash",
        to_font_grade(best_flash["level"], best_flash["sub_level"]) if best_flash is not None else "N/A"
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
    st.info(get_coach_message(df_12m, df_current_q, df_previous_q))

    # =========================
    # GRENIER
    # =========================
    st.markdown("## Grenier")

    with st.expander("Échelle Arkose → Fontainebleau"):

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
