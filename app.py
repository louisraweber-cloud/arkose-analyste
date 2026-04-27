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

    col1, col2, col3 = st.columns(3)

    col1.metric("Séances", df_current_q["date"].nunique())

    col2.metric(
        "Bloc le plus dur",
        to_font_grade(best_all["color"], best_all["sub_level"])
    )

    col3.metric(
        "Meilleur flash",
        to_font_grade(best_flash["color"], best_flash["sub_level"]) if best_flash is not None else "N/A"
    )

    # =========================
    # GRAPHIQUE UNIQUE RESTANT
    # =========================
    st.markdown("## Analyse des styles")
    st.caption("Top 20% des voies les plus dures sur 12 mois")

    st.plotly_chart(
        plot_styles(compute_styles_top20(df_12m)),
        use_container_width=True
    )

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
