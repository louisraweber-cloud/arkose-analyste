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
# 📅 FILTRE 12 MOIS
# =============================
def filter_last_year(df):
    today = pd.Timestamp.today()
    one_year_ago = today - pd.DateOffset(years=1)
    return df[df["date"] >= one_year_ago]


# =============================
# 📊 HEBDO SCORE
# =============================
def compute_weekly_score(df):
    
    df["week"] = df["date"].dt.to_period("W")
    
    weekly = df.groupby("week").agg(
        total_score=("grade_score", "sum")
    ).reset_index()
    
    weekly["week"] = weekly["week"].dt.start_time
    
    # 📈 moyenne mobile 4 semaines
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
# 📈 GRAPH HEBDO
# =============================
def plot_weekly(weekly):
    
    fig = px.area(
        weekly,
        x="week",
        y="total_score",
        line_shape="spline"
    )
    
    fig.update_traces(
        line=dict(width=3),
        opacity=0.9
    )
    
    # 📈 moyenne mobile
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
    
    fig.update_xaxes(
        showgrid=False,
        tickformat="%b %y",
        ticklabelmode="period"
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)"
    )
    
    # 🔥 meilleure semaine
    best = weekly.loc[weekly["total_score"].idxmax()]
    
    fig.add_scatter(
        x=[best["week"]],
        y=[best["total_score"]],
        mode="markers+text",
        text=["🔥"],
        textposition="top center",
        marker=dict(size=12),
        showlegend=False
    )
    
    return fig


# =============================
# 📊 GRAPH STYLES
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
    
    fig.update_xaxes(
        tickangle=45,
        showgrid=False
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)"
    )
    
    return fig


# =============================
# 🚀 APP
# =============================
if uploaded_file:
    
    df = pd.read_excel(uploaded_file)
    
    df = clean_data(df)
    df = filter_last_year(df)
    
    weekly = compute_weekly_score(df)
    
    # =============================
    # 📊 KPI
    # =============================
    st.markdown("### Synthèse")

    col1, col2, col3 = st.columns(3)

    # ✅ correction importante ici
    col1.metric("Séances", df["date"].dt.date.nunique())

    col2.metric("Volume total", int(df["grade_score"].sum()))
    col3.metric("Pic hebdo", int(weekly["total_score"].max()))


    # =============================
    # 📊 GRAPH 1 - VOLUME
    # =============================
    st.markdown("## Volume de la semaine")

    st.caption(
        "Le volume correspond à la somme des difficultés des blocs réalisés chaque semaine "
        "(Jaune 1 barre = 1 point. +1 point pour chaque barre supplémentaire et donc une verte 2 barres = 7 points)."
    )

    fig1 = plot_weekly(weekly)
    st.plotly_chart(fig1, use_container_width=True)


    # =============================
    # 📊 GRAPH 2 - STYLES
    # =============================
    st.markdown("## Analyse des styles")

    st.caption(
        "Ce graphique montre la répartition des styles de blocs parmi les 20% des voies les plus difficiles réalisées sur la période."
    )

    style_counts = compute_styles_top20(df)

    fig2 = plot_styles(style_counts)
    st.plotly_chart(fig2, use_container_width=True)


    # =============================
    # 🧠 COACH SIMPLE
    # =============================
    if weekly["total_score"].iloc[-1] < weekly["total_score"].mean():
        st.warning("📉 Semaine récente sous ta moyenne → possible fatigue ou baisse de volume")
    else:
        st.success("📈 Bonne dynamique récente")