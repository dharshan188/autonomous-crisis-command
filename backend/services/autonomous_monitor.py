"""
AUTONOMOUS FLOOD MONITOR v4
Smart Location Matching + Always Live Weather + India Safe
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
from dotenv import load_dotenv

# ─────────────────────────────────────────
# LOAD ENV
# ─────────────────────────────────────────

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

TIME_WINDOW_HOURS = 48
CONFIRMATION_THRESHOLD = 1
STRONG_NEWS_THRESHOLD = 3  # lowered

FLOOD_KEYWORDS = [
    "flood", "flooded", "flooding",
    "flash flood",
    "heavy rain", "heavy rainfall",
    "inundated", "waterlogging"
]

# ─────────────────────────────────────────
# NLP + GEO
# ─────────────────────────────────────────

nlp = spacy.load("en_core_web_sm")
geocoder = Nominatim(user_agent="flood_monitor_v4", timeout=10)

# ─────────────────────────────────────────
# NEWS
# ─────────────────────────────────────────

def fetch_news(query):
    url = (
        "https://news.google.com/rss/search?"
        f"q={requests.utils.quote(query)}"
        "&hl=en-US&gl=US&ceid=US:en"
    )
    r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def parse_rss(xml):
    root = ET.fromstring(xml)
    now = datetime.now(timezone.utc)
    titles = []

    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        pub_date = item.findtext("pubDate")

        if not pub_date:
            continue

        try:
            pub_time = parsedate_to_datetime(pub_date)
        except:
            continue

        if now - pub_time > timedelta(hours=TIME_WINDOW_HOURS):
            continue

        titles.append(title)

    return titles

# ─────────────────────────────────────────
# WEATHER
# ─────────────────────────────────────────

def get_weather(lat, lon):

    if not OPENWEATHER_API_KEY:
        return {}

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={OPENWEATHER_API_KEY}"
        "&units=metric"
    )

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        return {
            "temperature": data.get("main", {}).get("temp"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "rain_1h": data.get("rain", {}).get("1h", 0),
            "description": data.get("weather", [{}])[0].get("description")
        }
    except:
        return {}

# ─────────────────────────────────────────
# LOCATION
# ─────────────────────────────────────────

def extract_location(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            return ent.text
    return None


def geocode_location(name):
    try:
        loc = geocoder.geocode(name)
        if not loc:
            return None

        return loc.latitude, loc.longitude
    except (GeocoderTimedOut, GeocoderServiceError):
        return None

# ─────────────────────────────────────────
# RULE ENGINE
# ─────────────────────────────────────────

def evaluate_flood(weather, news_count):

    rain = weather.get("rain_1h", 0)

    # Strong news override
    if news_count >= STRONG_NEWS_THRESHOLD:
        return True, "Multiple confirmed flood reports"

    # Lowered rain threshold (India friendly)
    if rain is not None and rain >= 2:
        return True, "Rainfall anomaly detected"

    return False, "Monitoring rainfall levels"

# ─────────────────────────────────────────
# MAIN DETECTION
# ─────────────────────────────────────────

def detect_flood(state=None):

    query = f"flood {state}" if state else "flood"

    try:
        xml = fetch_news(query)
        titles = parse_rss(xml)
    except:
        return {
            "status": "ERROR",
            "message": "News fetch failed",
            "weather": {}
        }

    matches = []

    for title in titles:
        if any(k in title.lower() for k in FLOOD_KEYWORDS):

            if state:
                if state.lower() in title.lower():
                    matches.append(title)
                else:
                    # Also allow state-level match using NLP
                    doc = nlp(title)
                    for ent in doc.ents:
                        if ent.label_ == "GPE":
                            if state.lower() in ent.text.lower():
                                matches.append(title)
                                break
            else:
                matches.append(title)

    # ALWAYS GET WEATHER
    weather = {}
    if state:
        geo = geocode_location(state)
        if geo:
            lat, lon = geo
            weather = get_weather(lat, lon)

    if len(matches) >= CONFIRMATION_THRESHOLD:

        alert, reason = evaluate_flood(weather, len(matches))

        return {
            "status": "FLOOD_DETECTED" if alert else "MONITORING",
            "location": state,
            "weather": weather,
            "rule_reason": reason,
            "news_count": len(matches),
            "detected_at": datetime.utcnow().isoformat()
        }

    return {
        "status": "SAFE",
        "location": state,
        "weather": weather,
        "message": "Monitoring — no flood signals",
        "checked_at": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    print(detect_flood("Chennai"))