import time
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

if get_script_run_ctx() is None:
    print("Please run this app with Streamlit rather than plain Python:")
    print("    streamlit run main.py")
    raise SystemExit(1)

# AviationStack API Key
API_KEY = "48e05c79531d4da2cd4182da5b3cec53"
FLIGHTS_URL = "https://api.aviationstack.com/v1/flights"
AIRPORTS_URL = "https://api.aviationstack.com/v1/airports"

INDIAN_AIRPORTS = {
    "DEL": "Delhi - Indira Gandhi International",
    "BOM": "Mumbai - Chhatrapati Shivaji International",
    "BLR": "Bengaluru - Kempegowda International",
    "MAA": "Chennai - Chennai International",
    "HYD": "Hyderabad - Rajiv Gandhi International",
    "CCU": "Kolkata - Netaji Subhas Chandra Bose International",
    "COK": "Kochi - Cochin International",
    "AMD": "Ahmedabad - Sardar Vallabhbhai Patel International",
    "PNQ": "Pune - Pune International",
    "GOI": "Goa - Goa International",
    "IXC": "Chandigarh - Chandigarh International",
    "VTZ": "Visakhapatnam - Visakhapatnam International",
    "TRV": "Thiruvananthapuram - Trivandrum International",
    "IXB": "Bagdogra - Bagdogra Airport",
    "JAI": "Jaipur - Jaipur International",
    "LKO": "Lucknow - Chaudhary Charan Singh International",
    "NAG": "Nagpur - Dr. Babasaheb Ambedkar International",
    "PAT": "Patna - Jay Prakash Narayan Airport",
}

AIRPORT_COORDINATES = {
    "DEL": (28.5562, 77.1000),
    "BOM": (19.0896, 72.8656),
    "BLR": (13.1986, 77.7066),
    "MAA": (12.9941, 80.1709),
    "HYD": (17.2403, 78.4294),
    "CCU": (22.6547, 88.4467),
    "COK": (10.1520, 76.4019),
    "AMD": (23.0772, 72.6347),
    "PNQ": (18.5821, 73.9197),
    "GOI": (15.3808, 73.8314),
    "IXC": (30.6735, 76.7885),
    "VTZ": (17.7212, 83.2245),
    "TRV": (8.4821, 76.9201),
    "IXB": (26.6812, 88.3286),
    "JAI": (26.8242, 75.8122),
    "LKO": (26.7606, 80.8893),
    "NAG": (21.0922, 79.0472),
    "PAT": (25.5913, 85.0870),
}


st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
<style>
    [data-testid="stAppViewContainer"] {
        background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        font-family: 'Orbitron', monospace;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0, 0, 0, 0.7);
    }
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.9);
        font-family: 'Orbitron', monospace;
    }
    .main-header {
        font-size: 2.5em;
        color: #ffffff;
        text-align: center;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        font-family: 'Orbitron', monospace;
        font-weight: 700;
    }
    .metric-card {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-family: 'Orbitron', monospace;
    }
    .stDataFrame, .stPlotlyChart {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-family: 'Orbitron', monospace;
    }
    .stMarkdown, .stText {
        font-family: 'Orbitron', monospace;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<h1 class="main-header">Air Traffic Control System</h1>', unsafe_allow_html=True)
st.sidebar.header("Control Panel")


def resolve_airport_code(query: str | None) -> str | None:
    if not query:
        return None

    query = query.strip()
    if not query:
        return None

    if len(query) == 3 and query.isalpha():
        return query.upper()

    for code, name in INDIAN_AIRPORTS.items():
        if query.lower() in name.lower() or query.lower() in code.lower():
            return code

    params = {"access_key": API_KEY, "search": query}
    try:
        response = requests.get(AIRPORTS_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])
        if data:
            return data[0].get("iata_code") or data[0].get("icao_code")
    except requests.exceptions.RequestException:
        return None
    return None


def fetch_flight_data(url: str, params: dict, retries: int = 3, delay: int = 2) -> dict | None:
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, dict) and result.get("error"):
                st.error(f"AviationStack API error: {result['error'].get('message', 'Unknown error')}")
                return None
            return result
        except requests.exceptions.HTTPError as exc:
            response = exc.response
            if response is not None and response.status_code == 429:
                st.error(
                    "AviationStack rate limit exceeded (429). "
                    "Please wait a moment, reduce request frequency, or use a different API key."
                )
                return None
            if attempt < retries - 1:
                st.warning(
                    f"Request failed (attempt {attempt + 1}/{retries}): {exc}. "
                    f"Retrying in {delay} seconds..."
                )
                time.sleep(delay)
            else:
                st.error(f"Failed to fetch data after {retries} attempts: {exc}")
                return None
        except requests.exceptions.RequestException as exc:
            if attempt < retries - 1:
                st.warning(
                    f"Request failed (attempt {attempt + 1}/{retries}): {exc}. "
                    f"Retrying in {delay} seconds..."
                )
                time.sleep(delay)
            else:
                st.error(f"Failed to fetch data after {retries} attempts: {exc}")
                return None
    return None


def parse_datetime(value: object) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def get_airport_coords(airport_data: object, fallback_iata: object) -> tuple[float | None, float | None]:
    if isinstance(airport_data, dict):
        for lat_key, lon_key in (
            ("latitude", "longitude"),
            ("lat", "lon"),
            ("lat", "lng"),
        ):
            lat = airport_data.get(lat_key)
            lon = airport_data.get(lon_key)
            try:
                if lat not in (None, "") and lon not in (None, ""):
                    return float(lat), float(lon)
            except (TypeError, ValueError):
                pass

        iata_code = airport_data.get("iata")
        if isinstance(iata_code, str) and iata_code.upper() in AIRPORT_COORDINATES:
            return AIRPORT_COORDINATES[iata_code.upper()]

    if isinstance(fallback_iata, str) and fallback_iata.upper() in AIRPORT_COORDINATES:
        return AIRPORT_COORDINATES[fallback_iata.upper()]

    return None, None


def estimate_flight_position(row: pd.Series) -> tuple[float | None, float | None]:
    dep_lat, dep_lon = get_airport_coords(row.get("departure"), row.get("Departure IATA"))
    arr_lat, arr_lon = get_airport_coords(row.get("arrival"), row.get("Arrival IATA"))
    if None in (dep_lat, dep_lon, arr_lat, arr_lon):
        return None, None

    departure_info = row.get("departure")
    arrival_info = row.get("arrival")
    departure_time = None
    arrival_time = None

    if isinstance(departure_info, dict):
        departure_time = (
            parse_datetime(departure_info.get("actual"))
            or parse_datetime(departure_info.get("estimated"))
            or parse_datetime(departure_info.get("scheduled"))
        )
    if isinstance(arrival_info, dict):
        arrival_time = (
            parse_datetime(arrival_info.get("estimated"))
            or parse_datetime(arrival_info.get("scheduled"))
            or parse_datetime(arrival_info.get("actual"))
        )

    ratio = 0.5
    now = datetime.now(timezone.utc)
    if departure_time and arrival_time and arrival_time > departure_time:
        total_seconds = (arrival_time - departure_time).total_seconds()
        elapsed_seconds = (now - departure_time).total_seconds()
        ratio = max(0.08, min(0.92, elapsed_seconds / total_seconds))
    elif str(row.get("flight_status", "")).lower() == "active":
        ratio = 0.55
    elif str(row.get("flight_status", "")).lower() == "scheduled":
        ratio = 0.15

    lat = dep_lat + (arr_lat - dep_lat) * ratio
    lon = dep_lon + (arr_lon - dep_lon) * ratio
    return round(lat, 4), round(lon, 4)


def build_display_dataframe(flights: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(flights)
    df_display = df.copy()

    if "departure" in df.columns:
        df_display["Departure Airport"] = df["departure"].apply(
            lambda value: value.get("airport", "") if isinstance(value, dict) else ""
        )
        df_display["Departure IATA"] = df["departure"].apply(
            lambda value: value.get("iata", "") if isinstance(value, dict) else ""
        )
    if "arrival" in df.columns:
        df_display["Arrival Airport"] = df["arrival"].apply(
            lambda value: value.get("airport", "") if isinstance(value, dict) else ""
        )
        df_display["Arrival IATA"] = df["arrival"].apply(
            lambda value: value.get("iata", "") if isinstance(value, dict) else ""
        )
    if "airline" in df.columns:
        df_display["Airline"] = df["airline"].apply(
            lambda value: value.get("name", "") if isinstance(value, dict) else ""
        )
    if "flight" in df.columns:
        df_display["Flight Number"] = df["flight"].apply(
            lambda value: value.get("iata", "") if isinstance(value, dict) else ""
        )

    def extract_coordinate(live_data: object, key: str) -> float | None:
        try:
            if isinstance(live_data, dict):
                value = live_data.get(key)
                if value not in (None, ""):
                    return float(value)
        except (ValueError, TypeError):
            return None
        return None

    if "live" in df.columns:
        df_display["Latitude"] = df["live"].apply(lambda value: extract_coordinate(value, "latitude"))
        df_display["Longitude"] = df["live"].apply(lambda value: extract_coordinate(value, "longitude"))
    else:
        df_display["Latitude"] = None
        df_display["Longitude"] = None

    df_display["Position Source"] = df_display.apply(
        lambda row: "Live" if pd.notna(row.get("Latitude")) and pd.notna(row.get("Longitude")) else "Unavailable",
        axis=1,
    )

    needs_estimate = df_display["Position Source"] == "Unavailable"
    if needs_estimate.any():
        estimated_positions = df_display.loc[needs_estimate].apply(estimate_flight_position, axis=1)
        df_display.loc[needs_estimate, "Latitude"] = estimated_positions.apply(lambda value: value[0])
        df_display.loc[needs_estimate, "Longitude"] = estimated_positions.apply(lambda value: value[1])
        df_display.loc[
            needs_estimate
            & df_display["Latitude"].notna()
            & df_display["Longitude"].notna(),
            "Position Source",
        ] = "Estimated"

    return df_display


def get_route_fallback_map(base_params: dict) -> pd.DataFrame:
    fallback_points = []
    dep_code = base_params.get("dep_iata")
    arr_code = base_params.get("arr_iata")
    for key, label, other_label, other_code in (
        ("dep_iata", "Departure Airport", "Arrival Airport", arr_code),
        ("arr_iata", "Arrival Airport", "Departure Airport", dep_code),
    ):
        code = base_params.get(key)
        if isinstance(code, str) and code.upper() in AIRPORT_COORDINATES:
            lat, lon = AIRPORT_COORDINATES[code.upper()]
            fallback_points.append(
                {
                    "Flight Number": code.upper(),
                    "Airline": "Route Endpoint",
                    label: code.upper(),
                    other_label: other_code.upper() if isinstance(other_code, str) else "",
                    "Position Source": "Route",
                    "Latitude": lat,
                    "Longitude": lon,
                }
            )
    if not fallback_points:
        return pd.DataFrame()
    return pd.DataFrame(fallback_points)


def get_live_flights_for_map(
    base_df: pd.DataFrame,
    base_params: dict,
    selected_status: str,
    limit: int,
) -> pd.DataFrame:
    map_flights = base_df.dropna(subset=["Latitude", "Longitude"])
    if not map_flights.empty:
        return map_flights

    has_route_filter = "dep_iata" in base_params or "arr_iata" in base_params
    if not has_route_filter:
        return map_flights

    fallback_df = get_route_fallback_map(base_params)
    live_params = {"access_key": API_KEY, "limit": limit, "flight_status": "active"}
    for key in ("dep_iata", "arr_iata", "airline_iata", "flight_number"):
        if key in base_params:
            live_params[key] = base_params[key]

    st.sidebar.info("Checking active flights for live positions on this route.")
    with st.spinner("Checking active flights for live positions..."):
        live_data = fetch_flight_data(FLIGHTS_URL, live_params, retries=2, delay=1)
        live_rows = live_data.get("data", []) if live_data else []

    live_df = build_display_dataframe(live_rows) if live_rows else pd.DataFrame()
    route_live_flights = live_df.dropna(subset=["Latitude", "Longitude"]) if not live_df.empty else pd.DataFrame()
    if not route_live_flights.empty:
        return pd.concat([route_live_flights, fallback_df], ignore_index=True) if not fallback_df.empty else route_live_flights

    return fallback_df


flight_status = st.sidebar.selectbox(
    "Flight Status",
    ["all", "active", "scheduled", "landed", "cancelled", "incident", "diverted"],
)
limit = st.sidebar.slider("Number of Flights", 10, 100, 50)

st.sidebar.subheader("Advanced Filters")
selected_dep = st.sidebar.selectbox(
    "Departure Airport (India)",
    ["Select one"] + list(INDIAN_AIRPORTS.values()),
)
selected_arr = st.sidebar.selectbox(
    "Arrival Airport (India)",
    ["Select one"] + list(INDIAN_AIRPORTS.values()),
)
dep_iata = st.sidebar.text_input(
    "Departure Airport (IATA or city name)",
    placeholder="e.g., DEL or Mumbai",
)
arr_iata = st.sidebar.text_input(
    "Arrival Airport (IATA or city name)",
    placeholder="e.g., BOM or Delhi",
)
airline_iata = st.sidebar.text_input("Airline (IATA)", placeholder="e.g., AI")
flight_number = st.sidebar.text_input("Flight Number", placeholder="e.g., 1004")

if selected_dep != "Select one":
    dep_iata = next(code for code, name in INDIAN_AIRPORTS.items() if name == selected_dep)
if selected_arr != "Select one":
    arr_iata = next(code for code, name in INDIAN_AIRPORTS.items() if name == selected_arr)

if st.sidebar.button("Refresh Data"):
    st.rerun()

params = {"access_key": API_KEY, "limit": limit}
if flight_status != "all":
    params["flight_status"] = flight_status

if dep_iata:
    dep_code = resolve_airport_code(dep_iata)
    if dep_code:
        params["dep_iata"] = dep_code
    else:
        st.sidebar.error("Departure airport could not be resolved. Use a valid IATA code or airport/city name.")
if arr_iata:
    arr_code = resolve_airport_code(arr_iata)
    if arr_code:
        params["arr_iata"] = arr_code
    else:
        st.sidebar.error("Arrival airport could not be resolved. Use a valid IATA code or airport/city name.")
if airline_iata:
    params["airline_iata"] = airline_iata.upper()
if flight_number:
    params["flight_number"] = flight_number.strip()

with st.spinner("Fetching flight data..."):
    data = fetch_flight_data(FLIGHTS_URL, params)
    flights = data.get("data", []) if data else []

if flights:
    df = pd.DataFrame(flights)
    df_display = build_display_dataframe(flights)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Flights", len(flights))
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Active Flights", len([f for f in flights if f.get("flight_status") == "active"]))
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Scheduled Flights", len([f for f in flights if f.get("flight_status") == "scheduled"]))
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Landed Flights", len([f for f in flights if f.get("flight_status") == "landed"]))
        st.markdown("</div>", unsafe_allow_html=True)

    if "flight_status" in df.columns and not df["flight_status"].dropna().empty:
        status_counts = df["flight_status"].value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Flight Status Distribution",
        )
        st.plotly_chart(fig_pie, width="stretch")

    st.subheader("Flight Details")
    columns_to_show = [
        "Flight Number",
        "Airline",
        "Departure Airport",
        "Arrival Airport",
        "flight_status",
        "Position Source",
        "Latitude",
        "Longitude",
    ]
    df_table = df_display[[col for col in columns_to_show if col in df_display.columns]]
    st.dataframe(df_table, width="stretch")

    st.subheader("Live Flight Positions")
    live_flights = get_live_flights_for_map(df_display, params, flight_status, limit)

    if not live_flights.empty:
        live_count = len(live_flights[live_flights["Position Source"] == "Live"])
        estimated_count = len(live_flights[live_flights["Position Source"] == "Estimated"])
        route_count = len(live_flights[live_flights["Position Source"] == "Route"])
        message = f"Showing {len(live_flights)} positions on the map"
        if live_count or estimated_count:
            message += f" ({live_count} live, {estimated_count} estimated)"
        if route_count:
            message += f" and {route_count} route endpoints"
        st.info(message)
        try:
            fig_map = px.scatter_map(
                live_flights,
                lat="Latitude",
                lon="Longitude",
                hover_name="Flight Number",
                hover_data=["Airline", "Departure Airport", "Arrival Airport", "Position Source"],
                color="Position Source",
                zoom=3,
                height=450,
                title="Flight Locations",
            )
            fig_map.update_layout(mapbox_style="open-street-map", hovermode="closest")
            st.plotly_chart(fig_map, width="stretch")
        except Exception as exc:
            st.warning(f"Could not display map: {exc}")
            st.info("Flight position data is available but the map could not be rendered.")
    else:
        st.warning("Live position data is not available for the current result set.")
        st.info(
            """
Why this can happen:
- Live position data is only available for flights currently in the air.
- Scheduled, landed, or cancelled flights do not include real-time coordinates.
- Some AviationStack plans return limited live tracking data.
- Try the `active` status filter or choose a route with flights currently operating.
- Estimated positions are shown automatically when route and airport data are available.
"""
        )
else:
    st.write("No flights found for the selected criteria.")
