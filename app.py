
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="FireWatch | California",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 FireWatch")
st.caption("Exploring historical wildfire activity across California using NASA MODIS and VIIRS observations.")

# -----------------------------
# Load data
# -----------------------------

@st.cache_data
def load_data():
    fire = pd.read_parquet(
        "data/processed/fire_data.parquet",
        columns=[
            "acq_date", "sensor", "latitude", "longitude",
            "confidence_class", "frp"
        ]
    )

    daily = pd.read_parquet(
        "data/processed/daily_grid.parquet",
        columns=[
            "acq_date", "sensor", "grid_x", "grid_y",
            "hotspot_count"
        ]
    )

    fire["acq_date"] = pd.to_datetime(fire["acq_date"])
    daily["acq_date"] = pd.to_datetime(daily["acq_date"])

    fire["sensor"] = fire["sensor"].astype("category")
    fire["confidence_class"] = fire["confidence_class"].astype("category")
    daily["sensor"] = daily["sensor"].astype("category")

    fire["latitude"] = fire["latitude"].astype("float32")
    fire["longitude"] = fire["longitude"].astype("float32")
    fire["frp"] = fire["frp"].astype("float32")

    return fire, daily


fire, daily = load_data()

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Explore the data")

min_date = fire["acq_date"].min().date()
max_date = fire["acq_date"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

sensors = st.sidebar.multiselect(
    "Satellite sensors",
    ["MODIS", "VIIRS"],
    default=["MODIS", "VIIRS"]
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date


# -----------------------------
# Filter data
# -----------------------------
start = pd.Timestamp(start_date)
end = pd.Timestamp(end_date) + pd.Timedelta(days=1)

fire_mask = (
    (fire["acq_date"] >= start) &
    (fire["acq_date"] < end) &
    (fire["sensor"].isin(sensors))
)

daily_mask = (
    (daily["acq_date"] >= start) &
    (daily["acq_date"] < end) &
    (daily["sensor"].isin(sensors))
)

filtered = fire.loc[fire_mask]
filtered_daily = daily.loc[daily_mask]


# -----------------------------
# Summary metrics
# -----------------------------
st.subheader("Activity overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total detections", f"{len(filtered):,}")
col2.metric("MODIS detections", f"{(filtered['sensor'] == 'MODIS').sum():,}")
col3.metric("VIIRS detections", f"{(filtered['sensor'] == 'VIIRS').sum():,}")

st.divider()

# -----------------------------
# Activity chart
# -----------------------------
st.subheader("Fire activity over time")

daily_counts = (
    filtered.groupby(["acq_date", "sensor"])
    .size()
    .reset_index(name="detections")
)

fig = px.line(
    daily_counts,
    x="acq_date",
    y="detections",
    color="sensor",
    title="Daily active fire detections",
    labels={
        "acq_date": "Date",
        "detections": "Detection count",
        "sensor": "Sensor"
    }
)

st.plotly_chart(fig, use_container_width=True)


st.subheader("Burning activity calendar")

# Aggregate detections by date across the selected sensors
calendar_data = (
    filtered_daily
    .groupby("acq_date")["hotspot_count"]
    .sum()
    .reset_index()
)

# Extract year and day of year
calendar_data["year"] = calendar_data["acq_date"].dt.year
calendar_data["day_of_year"] = calendar_data["acq_date"].dt.dayofyear

# Build a year × day-of-year matrix
calendar_matrix = calendar_data.pivot(
    index="year",
    columns="day_of_year",
    values="hotspot_count"
).fillna(0)

# Use the same colour scale for both sensors

reference_max = (
    daily.loc[
        (daily["acq_date"] >= start) &
        (daily["acq_date"] < end)
    ]
    .groupby("acq_date")["hotspot_count"]
    .sum()
    .max()
)

# Display the heatmap
fig_calendar = px.imshow(
    calendar_matrix,
    aspect="auto",
    origin="lower",
    zmin=0,
    zmax=reference_max,
    labels={
        "x": "Day of year",
        "y": "Year",
        "color": "Detections"
    },
    title="Daily active-fire detections by year"
)

# Label the horizontal axis by month
month_positions = [
    pd.Timestamp(year=2024, month=m, day=15).dayofyear
    for m in range(1, 13)
]

fig_calendar.update_xaxes(
    tickmode="array",
    tickvals=month_positions,
    ticktext=[
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
)

st.plotly_chart(fig_calendar, use_container_width=True)

st.caption(
    "Daily detections are aggregated across selected sensors. "
    "A day with zero recorded detections does not necessarily mean "
    "there was no fire; satellites provide periodic observations."
)


st.subheader("Cross-sensor spatial overlap")

# Keep both sensors in this comparison, regardless of the sidebar selection
comparison_daily = daily.loc[
    (daily["acq_date"] >= start) &
    (daily["acq_date"] < end)
]
# Identify which sensors detected activity in each grid cell on each day

overlap_by_cell = (
    comparison_daily
    .groupby(
        ["acq_date", "grid_x", "grid_y", "sensor"],
        observed=True
    )
    .size()
    .unstack("sensor", fill_value=0)
    .reindex(columns=["MODIS", "VIIRS"], fill_value=0)
)

both_sensors = (
    (overlap_by_cell["MODIS"] > 0) &
    (overlap_by_cell["VIIRS"] > 0)
).sum()

modis_only = (
    (overlap_by_cell["MODIS"] > 0) &
    (overlap_by_cell["VIIRS"] == 0)
).sum()

viirs_only = (
    (overlap_by_cell["VIIRS"] > 0) &
    (overlap_by_cell["MODIS"] == 0)
).sum()

total_cell_days = len(overlap_by_cell)


col1, col2, col3 = st.columns(3)

col1.metric("Both sensors", f"{both_sensors:,}")
col2.metric("MODIS only", f"{modis_only:,}")
col3.metric("VIIRS only", f"{viirs_only:,}")

overlap_percentage = (
    both_sensors / total_cell_days * 100
    if total_cell_days else 0
)

st.caption(
    f"{overlap_percentage:.1f}% of detected grid-cell days "
    "were observed by both sensors. A grid-cell day means one "
    "1 km grid cell on one calendar day. This indicates spatial "
    "and daily co-occurrence, not confirmation of the same fire."
)


# -----------------------------
# Map
# -----------------------------
st.subheader("Geographic distribution")

st.caption(
    "Map displays a sample of detections to keep rendering responsive. "
    "Each point represents a satellite detection, not a confirmed individual fire."
)

# map_data = filtered.groupby("sensor", group_keys=False).apply(
#     lambda group: group.sample(
#         min(len(group), 15000),
#         random_state=42
#     )
# ).reset_index(drop=True) if not filtered.empty else filtered.copy()


map_data = filtered.sample(
    n=min(len(filtered), 10000),
    random_state=42
)[
    [
        "latitude",
        "longitude",
        "sensor",
        "acq_date",
        "confidence_class",
        "frp"
    ]
].copy()


# print("Filtered columns:", filtered.columns.tolist())
# print("Map columns:", map_data.columns.tolist())
# print("Map sensor counts:")
# print(map_data["sensor"].value_counts())

fig_map = px.scatter_map(
    map_data,
    lat="latitude",
    lon="longitude",
    color="sensor",
    hover_data=["acq_date", "confidence_class", "frp"],
    zoom=5,
    height=600,
    title="NASA active fire observations across California"
)

st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------
# Confidence comparison
# -----------------------------
st.subheader("Detection confidence")

confidence = (
    filtered.groupby(["sensor", "confidence_class"])
    .size()
    .reset_index(name="detections")
)

if not confidence.empty:
    confidence["percentage"] = (
        confidence["detections"] /
        confidence.groupby("sensor")["detections"].transform("sum") * 100
    )

    fig_conf = px.bar(
        confidence,
        x="sensor",
        y="percentage",
        color="confidence_class",
        barmode="stack",
        title="Confidence distribution by sensor",
        labels={"percentage": "Percentage (%)"}
    )

    st.plotly_chart(fig_conf, use_container_width=True)

# -----------------------------
# Fire Radiative Power
# -----------------------------
st.subheader("Fire Radiative Power (FRP)")

frp = (
    filtered.groupby("sensor")["frp"]
    .agg(["mean", "median", "max"])
    .reset_index()
)

st.dataframe(frp, use_container_width=True)

st.caption(
    "FRP is reported in megawatts (MW). Values from different sensors "
    "should be interpreted with their differing sensor characteristics in mind."
)

st.divider()
st.caption("FireWatch | NASA Space Apps Challenge 2026")