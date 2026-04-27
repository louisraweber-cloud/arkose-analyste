arrow = "↑" if delta >= 0 else "↓"

delta_color = "normal"
if delta > 0:
    delta_color = "normal"  # Streamlit affiche vert automatiquement si positif
elif delta < 0:
    delta_color = "inverse"

col1.metric(
    f"Séances T{current_q.quarter} {current_q.year}",
    sessions_current,
    f"{arrow} {delta:+} ({pct:.0f}%) vs T{prev_q.quarter} {prev_q.year}",
    delta_color=delta_color
)
