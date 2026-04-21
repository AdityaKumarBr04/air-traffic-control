# ✈️ Air Traffic Control System

A modern, attractive air traffic control dashboard built with Python and Streamlit, using the AviationStack API to fetch real-time flight data. Features a stunning sky background image with planes and a futuristic Orbitron font for an immersive experience.

## Features

- **Real-time Data**: View active, scheduled, landed, cancelled, incident, or diverted flights.
- **Advanced Control Panel**: 
  - Filter by flight status and result limit.
  - Search by departure/arrival airports (IATA codes).
  - Filter by airline (IATA code).
  - Search specific flight numbers.
- **Visual Analytics**: 
  - Metrics cards showing flight counts.
  - Pie chart for flight status distribution.
  - Interactive map with live flight positions.
- **Dynamic UI**: Custom styling with background image, Orbitron font, refresh button, and loading spinners.
- **Detailed Table**: Comprehensive flight information in an interactive table.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   streamlit run main.py
   ```

3. Open the provided URL in your browser to view the dashboard.

## API

This project uses the AviationStack API. The API key is included in the code. Note that free plans have limitations on the number of requests.

## Requirements

- Python 3.7+
- requests
- streamlit
- pandas
- plotly