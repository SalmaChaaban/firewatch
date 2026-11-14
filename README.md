# FireWatch 🔥
### MODIS and VIIRS Active-Fire Data Explorer

FireWatch is an interactive dashboard for exploring and comparing NASA satellite active-fire detections across California.

## Features

- Interactive map of active-fire detections.
- Daily fire activity charts and calendar heatmap.
- MODIS and VIIRS confidence distribution comparison.
- Fire Radiative Power (FRP) analysis.
- Spatial overlap analysis between satellite instruments.

## Data Source

Data was obtained from [NASA FIRMS – Archive Download](https://firms.modaps.eosdis.nasa.gov/download/).

Satellite instruments:
- MODIS Terra
- MODIS Aqua
- VIIRS Suomi-NPP (SNPP)

Geographic coverage: California, USA.

Observation coverage:
- MODIS: January 20, 2012 – August 31, 2026.
- VIIRS: January 20, 2012 – July 31, 2026.

## Methodology

The datasets were combined while preserving their original sensor identifiers.

Detection coordinates were projected to California Albers (EPSG:3310) and assigned to a common 1 km grid. Observations were then aggregated by date, grid cell, and sensor.

Confidence values were mapped to shared Low, Nominal, and High categories for visualization.

Spatial overlap was measured by identifying grid cells where both sensors recorded detections on the same day.

In the baseline analysis, 105,346 of 437,098 unique grid-cell days contained detections from both sensors (24.1%).

*This indicates overlap at the selected spatial and temporal scale, not necessarily detection of the same individual fire.*

## Technologies

- Python
- Pandas
- PyArrow
- PyProj
- Plotly
- Streamlit

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app.py
```

The application requires these processed datasets:

```text
data/processed/
├── fire_data.parquet
└── daily_grid.parquet
```

## Limitations

FireWatch is an exploratory visualization tool, not a fire prediction system. MODIS and VIIRS differ in spatial resolution, confidence reporting, and observation characteristics. The shared grid provides a common comparison framework but does not make their original observations equivalent.

## NASA Space Apps Challenge 2026

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

**Data:** [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/)