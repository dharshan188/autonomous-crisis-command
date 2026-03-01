import requests
import math
from geopy.geocoders import Nominatim

geocoder = Nominatim(user_agent="crisis_nearby_lookup")

# --------------------------------------------------
# Distance Calculation (Haversine Formula)
# --------------------------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# --------------------------------------------------
# Estimate ETA (Assume 40 km/h city speed)
# --------------------------------------------------

def estimate_eta(distance_km):
    speed = 40  # km/h average
    hours = distance_km / speed
    minutes = hours * 60
    return round(minutes, 1)


# --------------------------------------------------
# Fetch Nearby Services (OpenStreetMap Overpass API)
# --------------------------------------------------

def find_nearby_services(location):

    geo = geocoder.geocode(location)
    if not geo:
        return []

    lat, lon = geo.latitude, geo.longitude

    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:3000,{lat},{lon});
      node["amenity"="fire_station"](around:3000,{lat},{lon});
      node["amenity"="police"](around:3000,{lat},{lon});
    );
    out;
    """

    response = requests.get(overpass_url, params={"data": query})
    data = response.json()

    results = []

    for element in data.get("elements", []):
        name = element.get("tags", {}).get("name", "Unknown")
        amenity = element.get("tags", {}).get("amenity")
        el_lat = element.get("lat")
        el_lon = element.get("lon")

        distance = calculate_distance(lat, lon, el_lat, el_lon)
        eta = estimate_eta(distance)

        results.append({
            "name": name,
            "type": amenity,
            "distance_km": distance,
            "eta_minutes": eta
        })

    # Sort by distance
    results.sort(key=lambda x: x["distance_km"])

    return results[:5]  # return top 5 closest