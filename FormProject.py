import streamlit as st
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import requests

# --- 1. Extract GPS coordinates from photo EXIF ---
def extract_gps_info(image_file):
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

# --- 2. Reverse geocode to address using OpenStreetMap ---
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {'User-Agent': 'field-inspection-app'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("display_name", "")
        return ""
    except Exception:
        return ""

# --- 3. Streamlit UI ---
st.set_page_config(page_title="Form Data Tanah", layout="wide")
st.title("📋 Formulir Data Tanah")

with st.form("form_data_tanah"):
    surveyor = st.text_input("Nama Surveyor")
    property_id = st.text_input("Kode Properti")
    survey_date = st.date_input("Tanggal Survei", value=datetime.today())
    address = st.text_area("Alamat Properti")
    land_area = st.number_input("Luas Tanah (m²)", min_value=0.0)
    zoning = st.selectbox("Peruntukan", ["Hunian", "Komersial", "Industri", "Lainnya"])
    access = st.selectbox("Akses", ["Jalan Utama", "Gang", "Pribadi", "Lainnya"])
    notes = st.text_area("Catatan Tambahan")
    photo = st.file_uploader("Unggah Foto Properti", type=["jpg", "jpeg", "png"])

    submitted = st.form_submit_button("✅ Kirim Data")

    if submitted:
        gps = ("", "")
        address_lookup = ""
        photo_links = []

        if photo:
            gps = extract_gps_info(photo)
            if gps[0] and gps[1]:
                address_lookup = reverse_geocode(gps[0], gps[1])
            photo_links.append(photo.name)

        data_row = {
            "property_id": property_id,
            "survey_date": survey_date.strftime("%Y-%m-%d"),
            "surveyor": surveyor,
            "address": address,
            "land_area": land_area,
            "zoning": zoning,
            "access": access,
            "gps": gps,
            "address_lookup": address_lookup,
            "photo_links": photo_links,
            "notes": notes
        }

        st.success("✅ Data berhasil diproses!")
        st.json(data_row)