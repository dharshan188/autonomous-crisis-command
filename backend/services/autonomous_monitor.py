"""
AUTONOMOUS FLOOD MONITOR v7 (STABLE)
Accurate Area Detection + News Sources + Live Weather
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
STRONG_NEWS_THRESHOLD = 3

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
geocoder = Nominatim(user_agent="autonomous_crisis_monitor_v7", timeout=10)

# ─────────────────────────────────────────
# NEWS FETCH
# ─────────────────────────────────────────

def fetch_news(query):
    try:
        url = (
            "https://news.google.com/rss/search?"
            f"q={requests.utils.quote(query)}"
            "&hl=en-US&gl=US&ceid=US:en"
        )

        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        response.raise_for_status()
        return response.text

    except Exception as e:
        print("NEWS FETCH ERROR:", e)
        return None


def parse_rss(xml):
    if not xml:
        return []

    root = ET.fromstring(xml)
    now = datetime.now(timezone.utc)
    articles = []

    for item in root.findall(".//item"):

        title = item.findtext("title", "").strip()
        link = item.findtext("link", "")
        guid = item.findtext("guid", "")
        pub_date = item.findtext("pubDate")

        if not pub_date:
            continue

        try:
            pub_time = parsedate_to_datetime(pub_date)
        except:
            continue

        if now - pub_time > timedelta(hours=TIME_WINDOW_HOURS):
            continue

        if not link and guid.startswith("http"):
            link = guid

        if not link:
            continue

        articles.append({
            "title": title,
            "link": link
        })

    return articles

# ─────────────────────────────────────────
# WEATHER
# ─────────────────────────────────────────

def get_weather(lat, lon):

    if not OPENWEATHER_API_KEY:
        return {}

    try:
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}"
            f"&appid={OPENWEATHER_API_KEY}"
            "&units=metric"
        )

        response = requests.get(url, timeout=10)
        data = response.json()

        return {
            "temperature": data.get("main", {}).get("temp"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "rain_1h": data.get("rain", {}).get("1h", 0),
            "description": data.get("weather", [{}])[0].get("description")
        }

    except Exception as e:
        print("WEATHER FETCH ERROR:", e)
        return {}

# ─────────────────────────────────────────
# GEO LOCATION
# ─────────────────────────────────────────

def geocode_location(name):
    try:
        location = geocoder.geocode(name)
        if not location:
            return None
        return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print("GEOCODE ERROR:", e)
        return None

# ─────────────────────────────────────────
# RULE ENGINE
# ─────────────────────────────────────────

def evaluate_flood(weather, news_count):

    rain = weather.get("rain_1h", 0)

    if news_count >= STRONG_NEWS_THRESHOLD:
        return True, "Multiple confirmed flood reports"

    if rain and rain >= 2:
        return True, "Rainfall anomaly detected"

    return False, "Monitoring rainfall levels"

# ─────────────────────────────────────────
# EXTRACT MOST SPECIFIC LOCATION
# ─────────────────────────────────────────

def extract_precise_location(matches, fallback_state):

    for article in matches:
        doc = nlp(article["title"])
        for ent in doc.ents:
            if ent.label_ == "GPE":
                if fallback_state and fallback_state.lower() not in ent.text.lower():
                    return ent.text

    return fallback_state

# ─────────────────────────────────────────
# MAIN DETECTION
# ─────────────────────────────────────────

def detect_flood(state=None):

    query = f"flood {state}" if state else "flood"

    xml = fetch_news(query)
    articles = parse_rss(xml)

    matches = []

    for article in articles:

        title_lower = article["title"].lower()

        if any(keyword in title_lower for keyword in FLOOD_KEYWORDS):

            if state:
                if state.lower() in title_lower:
                    matches.append(article)
                else:
                    doc = nlp(article["title"])
                    for ent in doc.ents:
                        if ent.label_ == "GPE" and state.lower() in ent.text.lower():
                            matches.append(article)
                            break
            else:
                matches.append(article)

    precise_location = extract_precise_location(matches, state)

    geo = geocode_location(precise_location) if precise_location else None

    weather = {}
    lat = lon = None

    if geo:
        lat, lon = geo
        weather = get_weather(lat, lon)

    if len(matches) >= CONFIRMATION_THRESHOLD:

        alert, reason = evaluate_flood(weather, len(matches))

        return {
            "status": "FLOOD_DETECTED" if alert else "MONITORING",
            "location": precise_location,
            "latitude": lat,
            "longitude": lon,
            "weather": weather,
            "rule_reason": reason,
            "news_count": len(matches),
            "sources": matches[:3],
            "detected_at": datetime.utcnow().isoformat()
        }

    return {
        "status": "SAFE",
        "location": precise_location,
        "latitude": lat,
        "longitude": lon,
        "weather": weather,
        "sources": [],
        "message": "Monitoring — no flood signals",
        "checked_at": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────
# LOCAL TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    result = detect_flood("Sydney")
    print(result)