# This is a simplified modular foundation — the full Streamlit app should be built using this as backend logic
# You still need to integrate this with Streamlit UI and Google Sheets/Drive setup

from datetime import datetime
from typing import List, Dict
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import requests
import os

# --- 1. Extract GPS from image EXIF ---
def extract_gps_info(image_file):
    """Extract GPS coordinates from an image's EXIF metadata."""
    try:
        image = Image.open(image_file)
        exif_data = image._getexif()
        gps_info = {}
        if exif_data:
            for tag, value in exif_data.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = value[t]

        def convert_to_degrees(value):
            d, m, s = value
            return d[0] / d[1] + m[0] / m[1] / 60 + s[0] / s[1] / 3600

        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = convert_to_degrees(gps_info["GPSLatitude"])
            lon = convert_to_degrees(gps_info["GPSLongitude"])
            if gps_info.get("GPSLatitudeRef") == "S":
                lat = -lat
            if gps_info.get("GPSLongitudeRef") == "W":
                lon = -lon
            return lat, lon
        return None, None
    except Exception:
        return None, None

# --- 2. Reverse geocoding (lat/lon → address) ---
def reverse_geocode(lat, lon):
    """Use Nominatim to reverse geocode coordinates into an address."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {'User-Agent': 'field-inspection-app'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("display_name", "")
        return ""
    except Exception:
        return ""

# --- 3. Prepare row for Data Tanah ---
def prepare_tanah_row(data: Dict):
    return [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data["property_id"],
        data["survey_date"],
        data["surveyor"],
        data["address"],
        data["land_area"],
        data["zoning"],
        data["access"],
        data["gps"][0],
        data["gps"][1],
        data["address_lookup"],
        ", ".join(data["photo_links"]),
        data["notes"]
    ]

# --- 4. Prepare rows for Data Bangunan ---
def prepare_bangunan_rows(buildings: List[Dict]):
    rows = []
    for b in buildings:
        rows.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            b["property_id"],
            b["type"],
            b["floor_area"],
            b["floors"],
            b["condition"],
            b["notes"],
            b["photo_link"]
        ])
    return rows

# --- 5. Prepare rows for Data Pembanding ---
def prepare_pembanding_rows(offers: List[Dict]):
    rows = []
    for p in offers:
        rows.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            p["property_id"],
            p["type"],
            p["description"],
            p["price"],
            p["source"],
            p["contact"],
            p["photo_link"]
        ])
    return rows
