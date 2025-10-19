
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Study Space Booking Dashboard", layout="wide")

DATA = Path(__file__).parent / "data"
def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

buildings = load_json("buildings.json")
floors_all = load_json("floors.json")
spaces_all = load_json("spaces.json")
occ_latest = load_json("occupancy_latest.json")
trend_raw = load_json("trend_15min.json")

# Sidebar filters
st.sidebar.title("Filters")
building_map = {b["building_name"]: b["building_id"] for b in buildings}
building_name = st.sidebar.selectbox("Building", list(building_map.keys()))
building_id = building_map[building_name]

floors = [f for f in floors_all if f["building_id"] == building_id]
floor_name_to_id = {f["floor_name"]: f["floor_id"] for f in floors}
floor_name = st.sidebar.selectbox("Floor", list(floor_name_to_id.keys()))
floor_id = floor_name_to_id[floor_name]

space_type = st.sidebar.selectbox("Space Type", ["desk", "room", "pc"])

# Data slices
spaces = [s for s in spaces_all if s["floor_id"] == floor_id]
occ_map = {o["space_id"]: o["occupied"] for o in occ_latest}
trend = [t for t in trend_raw if t["floor_id"] == floor_id and t["space_type"] == space_type]

# KPIs
total = len(spaces)
occupied = sum(1 for s in spaces if occ_map.get(s["space_id"], 0) == 1)
free = total - occupied
free_rooms = sum(1 for s in spaces if s["space_type"] == "room" and occ_map.get(s["space_id"], 0) == 0)
occ_rate = (occupied / total) if total else 0.0
mean = trend[0]["occ_rate_mean"] if trend else occ_rate
wait_min = max(0, round((mean - 0.85) * 30))

st.title("Study Space Booking Dashboard")
st.caption("Minimal runnable version for QBUS5010 – Filters → KPIs → Floor Map → Trend → Booking placeholder.")

# Top: KPIs
kpi_cols = st.columns(4)
kpi_cols[0].metric("Free Seats", f"{free}")
kpi_cols[1].metric("Occupancy", f"{occ_rate*100:.0f}%")
kpi_cols[2].metric("Free Rooms", f"{free_rooms}")
kpi_cols[3].metric("Est. Wait", f"{wait_min} min")

st.markdown("---")

# Floor Map (scatter over 0-100 coordinate plane)
st.subheader("Floor Map")
with st.container():
    # Build a scatter figure in 0-100 coords
    xs = [s["x"] for s in spaces]
    ys = [s["y"] for s in spaces]
    colors = ["red" if occ_map.get(s["space_id"], 0)==1 else "blue" for s in spaces]
    symbols = ["square" if s["space_type"] == "room" else "circle" for s in spaces]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(size=12, color=colors, symbol=symbols, line=dict(width=1, color="black")),
        text=[f'{s["space_id"]} • {s["space_type"]} • ' + ("Occupied" if occ_map.get(s["space_id"], 0)==1 else "Free")
              for s in spaces],
        hoverinfo="text"
    ))
    fig.update_layout(
        xaxis=dict(range=[0,100], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[0,100], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        height=420, margin=dict(l=10,r=10,t=10,b=10),
        plot_bgcolor="rgba(245,245,245,1)", paper_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)

# Trend
st.subheader("Trend (mean & p25)")
if trend:
    df = pd.DataFrame(trend)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["time_bucket"], y=df["occ_rate_mean"], name="mean", mode="lines"))
    fig2.add_trace(go.Scatter(x=df["time_bucket"], y=df["occ_rate_p25"], name="p25", mode="lines"))
    fig2.update_yaxes(range=[0,1], tickformat=".0%")
    fig2.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No trend data for this selection.")

# Booking placeholder
st.markdown("### Booking")
if st.button("Go to Booking"):
    st.success("This would open the official booking system. Placeholder only.")

st.markdown("---")
st.caption("Colors encode status (red=occupied, blue=free). Shapes encode type (circle=desk/pc, square=room).")
