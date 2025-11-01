# weather_app.py
# Live Weather Dashboard – Hyderabad
# By Sohail Ahmed (MCA Student)
#
# Requirements:
# streamlit, requests, pandas, numpy, matplotlib, seaborn

import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from matplotlib.ticker import MaxNLocator

# Page config
st.set_page_config(page_title="Live Weather Dashboard – Hyderabad",
                   layout="wide",
                   initial_sidebar_state="collapsed")

# ---- CSS for Apple-like clean style ----
st.markdown("""
    <style>
    :root {
      --bg: #f7f7f8;
      --card: #ffffff;
      --muted: #6b7280;
      --accent: #0a84ff;
    }
    .stApp {
      background: linear-gradient(180deg, var(--bg), #ffffff);
      color: #111827;
    }
    .header {
      padding: 28px 20px;
      border-radius: 14px;
      background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(250,250,250,0.9));
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      margin-bottom: 18px;
    }
    .title {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 4px;
    }
    .subtitle {
      color: var(--muted);
      margin-top: 0;
      font-size: 14px;
    }
    .card {
      background: var(--card);
      padding: 18px;
      border-radius: 12px;
      box-shadow: 0 6px 18px rgba(15,23,42,0.04);
    }
    .metric {
      font-size: 20px;
      font-weight: 600;
    }
    .small {
      color: var(--muted);
      font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Header ----
with st.container():
    st.markdown('<div class="header">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex; justify-content:space-between; align-items:center;">', unsafe_allow_html=True)
    st.markdown('<div><div class="title">Live Weather Dashboard – Hyderabad</div>'
                '<div class="subtitle">By Sohail Ahmed, MCA Student &nbsp;•&nbsp; Roll No: 51724862117</div></div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")  # spacing

# ---- Sidebar: API key (masked) + City (fixed to Hyderabad) ----
with st.sidebar:
    st.header("Settings")
    st.write("API key is required to fetch live data from OpenWeather.")
    # Try to get from Streamlit secrets
    api_key = ""
    if "OPENWEATHER_API_KEY" in st.secrets:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
        st.success("API key loaded from Streamlit Secrets.")
    else:
        api_key = st.text_input("Paste OpenWeather API key (masked)", type="password")
        if api_key:
            st.info("API key provided via input (only for this session).")

    st.markdown("---")
    city = st.text_input("City", value="Hyderabad")
    units = st.selectbox("Units", options=["metric"], index=0, help="metric = °C")
    st.markdown("---")
    st.write("Tip: For Streamlit Cloud, add the key under *Manage app → Settings → Secrets* as `OPENWEATHER_API_KEY`.")

# ---- Helper functions to fetch data ----
def fetch_current_weather(city_name: str, api_key: str):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city_name, "appid": api_key, "units": "metric"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_forecast(city_name: str, api_key: str):
    # 5 day / 3 hour forecast
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city_name, "appid": api_key, "units": "metric"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def prepare_forecast_df(forecast_json):
    # forecast_json['list'] contains items every 3 hours
    rows = []
    for item in forecast_json.get("list", []):
        dt = datetime.fromtimestamp(item["dt"])
        temp = item["main"]["temp"]
        humidity = item["main"]["humidity"]
        wind = item["wind"]["speed"]
        rain = 0.0
        # rainfall may be in 'rain' as '3h'
        if "rain" in item and item["rain"].get("3h"):
            rain = item["rain"]["3h"]
        rows.append({"dt": dt, "date": dt.date(), "time": dt.time(), "temp": temp,
                     "humidity": humidity, "wind": wind, "rain": rain,
                     "desc": item["weather"][0]["description"].title()})
    df = pd.DataFrame(rows)
    return df

# ---- Main content: try to fetch data ----
if not api_key:
    st.warning("Please provide your OpenWeather API key in the sidebar (or add to Streamlit Secrets).")
    st.stop()

try:
    with st.spinner("Fetching live weather data..."):
        current = fetch_current_weather(city, api_key)
        forecast = fetch_forecast(city, api_key)
except requests.HTTPError as e:
    st.error(f"Failed to fetch data from OpenWeather. HTTP Error: {e}")
    st.stop()
except Exception as e:
    st.error(f"Error fetching weather data: {e}")
    st.stop()

# ---- Parse current weather ----
cur_temp = current["main"]["temp"]
cur_feels = current["main"].get("feels_like", cur_temp)
cur_hum = current["main"]["humidity"]
cur_wind = current["wind"]["speed"]
cur_desc = current["weather"][0]["description"].title()
cur_icon = current["weather"][0]["icon"]  # can use to show icon

# ---- Forecast dataframe and daily aggregates ----
df_fore = prepare_forecast_df(forecast)
# Daily summary (next 5 days)
daily = df_fore.groupby("date").agg({
    "temp": ["mean", "min", "max"],
    "rain": "sum",
    "humidity": "mean"
}).reset_index()
daily.columns = ["date", "temp_mean", "temp_min", "temp_max", "rain_sum", "humidity_mean"]
daily["date_str"] = daily["date"].apply(lambda d: d.strftime("%a %d %b"))

# ---- Top cards ----
card_style = "card"
col1, col2, col3, col4 = st.columns([1.3, 1, 1, 1])
with col1:
    st.markdown(f'<div class="{card_style}">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric">{cur_temp:.1f}°C</div>')
    st.markdown(f'<div class="small">Current temperature in <b>{city.title()}</b></div>')
    st.markdown("</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="{card_style}">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric">{cur_hum}%</div>')
    st.markdown(f'<div class="small">Humidity</div>')
    st.markdown("</div>", unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="{card_style}">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric">{cur_wind} m/s</div>')
    st.markdown(f'<div class="small">Wind speed</div>')
    st.markdown("</div>", unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="{card_style}">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric">{cur_desc}</div>')
    st.markdown(f'<div class="small">Condition</div>')
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")  # spacing

# ---- Main panels: Charts & Table ----
left, right = st.columns((2, 1.2))

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("5-Day Forecast — Temperature & Rainfall")
    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    sns.set_style("whitegrid")
    ax2 = ax1.twinx()

    # line: mean temp per day
    ax1.plot(daily["date_str"], daily["temp_mean"], marker="o", linewidth=2.2, label="Avg Temp (°C)")
    ax1.fill_between(daily["date_str"], daily["temp_min"], daily["temp_max"], alpha=0.12)
    ax1.set_ylabel("Temperature (°C)", fontsize=10)
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # bar: rainfall
    ax2.bar(daily["date_str"], daily["rain_sum"], alpha=0.35, label="Rain (mm)")
    ax2.set_ylabel("Rainfall (mm)", fontsize=10)

    ax1.set_xlabel("")
    ax1.set_title(f"Temperature & Rainfall Forecast for {city.title()}", fontsize=12, pad=12)
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    plt.tight_layout()
    st.pyplot(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")  # spacing

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Detailed 3-hour Forecast")
    # show the next 12 timepoints (36 hours) as a small table and chart
    short = df_fore.head(12).copy()
    short["time_str"] = short["dt"].dt.strftime("%d %b %H:%M")
    st.dataframe(short[["time_str", "temp", "humidity", "wind", "rain", "desc"]].rename(
        columns={"time_str": "Date & Time", "temp": "Temp (°C)", "humidity": "Humidity (%)", "wind": "Wind (m/s)", "rain": "Rain (mm)", "desc": "Weather"}))

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Summary Insights")
    st.write(f"**Location:** {current.get('name', city)}")
    st.write(f"**Temperature (now):** {cur_temp:.1f} °C (feels like {cur_feels:.1f} °C)")
    st.write(f"**Humidity:** {cur_hum}%")
    st.write(f"**Wind:** {cur_wind} m/s")
    st.write(f"**Condition:** {cur_desc}")
    st.markdown("---")
    st.write("**Forecast Summary (next days)**")
    for _, r in daily.iterrows():
        st.write(f"- {r['date_str']}: Avg {r['temp_mean']:.1f}°C • Rain {r['rain_sum']:.1f} mm")
    st.markdown('</div>', unsafe_allow_html=True)

# ---- Footer ----
st.write("")
st.markdown("""
<div style="text-align:center; padding:14px; color:#6b7280; font-size:13px;">
    This live dashboard uses OpenWeather data. Designed for a professional mini project presentation by Sohail Ahmed.
</div>
""", unsafe_allow_html=True)
