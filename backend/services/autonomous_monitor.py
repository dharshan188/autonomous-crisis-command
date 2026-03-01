"""
AUTONOMOUS FLOOD MONITOR v8
Stable + Real News Links + Live Weather + Smart Location
Includes:
- Temperature
- Rain (last 1 hour)
- Humidity
- Wind speed
- Top 2 news articles
"""

import requests
import xml.etree.ElementTree as ET
import spacy
from datetime import datetime
from geopy.geocoders import Nominatim


# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

FLOOD_KEYWORDS = [
    "flood", "flooded", "flooding",
    "waterlogging", "heavy rain",
    "overflow", "inundated"
]

RAIN_THRESHOLD_MM = 15  # rain trigger in 1 hour


# ─────────────────────────────────────────
# NLP + GEOCODER
# ─────────────────────────────────────────

nlp = spacy.load("en_core_web_sm")
geocoder = Nominatim(user_agent="flood_monitor_v8", timeout=10)


# ─────────────────────────────────────────
# LOCATION EXTRACTION
# ─────────────────────────────────────────

def extract_location(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            return ent.text
    return text  # fallback


def geocode_location(name):
    try:
        location = geocoder.geocode(name)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print("Geocode error:", e)
    return None, None


# ─────────────────────────────────────────
# LIVE WEATHER (Open-Meteo – Free API)
# ─────────────────────────────────────────

def get_weather(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "hourly": "precipitation",
            "forecast_days": 1
        }

        res = requests.get(url, params=params, timeout=5)
        data = res.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})

        rain_last_hour = 0
        if "precipitation" in hourly and len(hourly["precipitation"]) > 0:
            rain_last_hour = hourly["precipitation"][0]

        return {
            "temperature_c": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_kmh": current.get("wind_speed_10m"),
            "rain_last_1h_mm": rain_last_hour
        }

    except Exception as e:
        print("Weather error:", e)
        return {}


# ─────────────────────────────────────────
# GOOGLE NEWS RSS (Top 2)
# ─────────────────────────────────────────

def fetch_news(location):

    rss_url = (
        f"https://news.google.com/rss/search?"
        f"q={location}+flood&hl=en-IN&gl=IN&ceid=IN:en"
    )

    try:
        response = requests.get(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )

        return parse_rss(response.text)

    except Exception as e:
        print("News fetch error:", e)
        return []


def parse_rss(xml_data):

    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        print("RSS parse error:", e)
        return []

    articles = []

    for item in root.findall(".//item"):

        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()

        if not link.startswith("http"):
            continue

        articles.append({
            "title": title,
            "link": link
        })

    return articles[:2]   # 🔥 ONLY TOP 2


# ─────────────────────────────────────────
# MAIN FLOOD DETECTION
# ─────────────────────────────────────────

def detect_flood(text: str):

    location = extract_location(text)
    lat, lon = geocode_location(location)

    if not lat:
        return {
            "status": "NO_FLOOD",
            "reason": "Location not found"
        }

    weather_data = get_weather(lat, lon)
    news_articles = fetch_news(location)

    print("News Articles:", news_articles)

    keyword_trigger = any(
        keyword in text.lower()
        for keyword in FLOOD_KEYWORDS
    )

    heavy_rain = weather_data.get("rain_last_1h_mm", 0) > RAIN_THRESHOLD_MM
    strong_news = len(news_articles) >= 1

    if keyword_trigger or heavy_rain or strong_news:

        return {
            "status": "FLOOD_DETECTED",
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "weather": weather_data,
            "news_count": len(news_articles),
            "sources": news_articles,
            "rule_reason": "Triggered by keyword/news/weather",
            "timestamp": datetime.now().isoformat()
        }

    return {
        "status": "NO_FLOOD",
        "location": location,
        "coordinates": {"lat": lat, "lon": lon},
        "weather": weather_data,
        "news_count": len(news_articles),
        "sources": news_articles,
        "rule_reason": "No strong flood indicators",
        "timestamp": datetime.now().isoformat()
    }