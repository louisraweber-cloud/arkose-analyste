import streamlit as st
import pandas as pd
import plotly.express as px


# =========================================================
# 🎯 CONFIG + HEADER PRODUIT
# =========================================================
st.set_page_config(page_title="Arkose Analyste", layout="centered")

st.markdown(
    """
    <style>
    .reload-btn button {
        background-color: transparent;
        border: none;
        font-size: 20px;
        cursor: pointer;
        opacity: 0.4;
        transition: all 0.2s ease;
    }
    .reload-btn button:hover {
        opacity: 1;
        transform: rotate(20deg);
    }
    </style>
    """,
    unsafe_allow_html=True
)

col_title, col_button = st.columns([10, 1])

with col_title:
    st.title("Arkose Analyste")

with col_button:
    if "file_uploaded" in st.session_state and st.session_state.file_uploaded:
        st.markdown('<div class="reload-btn">', unsafe_allow_html=True)
        if st.button("🔄", help="Recharger un fichier"):
            st.session_state.file_uploaded = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 📂 UPLOAD
# =========================================================
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False

if not st.session_state.file_uploaded:
    uploaded_file = st.file_uploader(
        "Importer ton fichier Arkose (Excel)", 
        type=["xlsx"]
    )

    if uploaded_file is not None:
        st.session_state.file_uploaded = True
        st.session_state.file = uploaded_file
        st.rerun()
else:
    uploaded_file = st.session_state.file


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
# 🧗 CONVERSION FONTAINEBLEAU
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

    days_offset = today - start_current
    end_prev = start_prev + days_offset

    return df[
        (df["date"] >= start_prev) &
        (df["date"] <= end_prev)
    ]


def filter_last_12_months(df):
    today = pd.Timestamp.today()
    one_year_ago = today - pd.DateOffset(years=1)

    return df[(df["date"] >= one_year_ago) & (df["date"] <= today)]


# =========================================================
# 📊 CALCULS
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


def get_best_blocks(df):

    best_all = df.loc[df["grade_score"].idxmax()]

    df_flash = df[df["flashé"] == "Oui"]

    if len(df_flash) > 0:
        best_flash = df_flash.loc[df_flash["grade_score"].idxmax()]
    else:
        best_flash = None

    return best_all, best_flash


def get_coach_message(df_12m, df_current_q, df_previous_q):

    sessions_current = df_current_q["date"].dt.date.nunique()
    sessions_previous = df_previous_q["date"].dt.date.nunique()

    weekly_avg = df_12m.groupby(df_12m["date"].dt.to_period("W")).size().mean()

    last_week = df_12m[
        df_12m["date"] >= (pd.Timestamp.today() - pd.Timedelta(days=7))
    ].shape[0]

    messages = []

    if sessions_current < sessions_previous:
        messages.append("📉 Moins de séances que le trimestre précédent.")
    else:
        messages.append("📈 Bonne régularité ce trimestre.")

    if last_week < weekly_avg * 0.6:
        messages.append("⚡ Semaine légère → récup ou technique.")

    if len(messages) == 0:
        messages.append("🧠 Continue sur ta dynamique actuelle.")

    return " ".join(messages)


# =========================================================
# 📈 VISUALISATIONS
# =========================================================
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
        line=dict(width=2, dash="dash")
    )

    fig.update_layout(
        template="simple_white",
        yaxis_title="",
        xaxis_title="",
        showlegend=False
    )

    return fig


def plot_styles(style_counts):

    fig = px.bar(style_counts, x="style", y="count")

    fig.update_layout(
        template="simple_white",
        xaxis_title="",
        yaxis_title="",
        showlegend=False
    )

    return fig


# =========================================================
# 🚀 APP
# =========================================================
if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df = clean_data(df)

    df_current_q = filter_current_quarter(df)
    df_previous_q = filter_previous_quarter_same_period(df)
    df_12m = filter_last_12_months(df)

    weekly_12m = compute_weekly_score(df_12m)

    best_all, best_flash = get_best_blocks(df_12m)

    # =========================================================
    # 📊 SYNTHÈSE
    # =========================================================
    st.markdown("### Synthèse")

    with st.expander("📘 Échelle Arkose → Fontainebleau"):
        st.markdown("""
| Niveau Arkose | Barre 1 | Barre 2 | Barre 3 | Barre 4 | Barre 5 |
| ------------- | ------- | ------- | ------- | ------- | -------- |
| **1** | 3 | 3+ | 4A | 4A+ | 4B |
| **2** | 4B | 4C | 5A | 5A+ | 5B |
| **3** | 5A+ | 5B | 5B+ | 5C | 5C+ |
| **4** | 5C+ | 6A | 6A+ | 6B | 6B+ |
| **5** | 6B | 6B+ | 6C | 6C+ | 7A |
| **6** | 7A | 7A+ | 7B | 7B+ | 7C / 7C+ |
""")

    today = pd.Timestamp.today()
    current_q = today.to_period("Q")
    prev_q = current_q - 1

    sessions_current = df_current_q["date"].dt.date.nunique()
    sessions_previous = df_previous_q["date"].dt.date.nunique()

    delta = sessions_current - sessions_previous if sessions_previous > 0 else 0
    pct = (delta / sessions_previous * 100) if sessions_previous > 0 else 0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"Séances T{current_q.quarter} {current_q.year}",
        sessions_current,
        f"{delta:+} ({pct:.0f}%) vs T{prev_q.quarter} {prev_q.year}",
        delta_color="normal"
    )

    col2.metric(
        "Bloc le plus dur",
        to_font_grade(best_all["level"], best_all["sub_level"])
    )

    col3.metric(
        "Meilleur flash",
        to_font_grade(best_flash["level"], best_flash["sub_level"]) if best_flash is not None else "N/A"
    )

    # =========================================================
    # 📊 GRAPHS
    # =========================================================
    st.markdown("## Volume de la semaine")
    st.plotly_chart(plot_weekly(weekly_12m), use_container_width=True)

    st.markdown("## Analyse des styles")
    st.plotly_chart(plot_styles(compute_styles_top20(df_12m)), use_container_width=True)

    # =========================================================
    # 🧠 COACH
    # =========================================================
    st.markdown("## 🧠 Un mot de ton Coach")
    st.info(get_coach_message(df_12m, df_current_q, df_previous_q))
