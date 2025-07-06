import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_folium import st_folium
import folium
import requests

def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {"User-Agent": "streamlit-inspection-app"}
        response = requests.get(url, headers=headers)
        data = response.json()
        return data.get("display_name", "Alamat tidak ditemukan")
    except:
        return "Gagal mengambil alamat"

st.set_page_config(page_title="Form Inspeksi Properti", layout="wide")
st.title("📋 Form Inspeksi Properti dengan Lokasi Interaktif & Alamat Otomatis")

with st.form("form_inspeksi", clear_on_submit=False, height=500):
    col1, col2 = st.columns(2)
    with col1:
        nama_penilai = st.text_input("Nama Penilai")
        tanggal = st.date_input("Tanggal Inspeksi", value=datetime.today())
        alamat_manual = st.text_area("Alamat Properti (bisa kosong, akan diisi otomatis jika titik dipilih)")

    with col2:
        luas_tanah = st.number_input("Luas Tanah (m²)", min_value=0.0)
        default_lat = -6.200000
        default_lon = 106.816666

        st.markdown("### 📍 Klik di peta untuk memilih koordinat")
        m = folium.Map(location=[default_lat, default_lon], zoom_start=12)
        m.add_child(folium.LatLngPopup())
        output = st_folium(m, width=700, height=400)

        lat = output["last_clicked"]["lat"] if output["last_clicked"] else default_lat
        lon = output["last_clicked"]["lng"] if output["last_clicked"] else default_lon

        st.write(f"🧭 Koordinat yang dipilih: **{lat:.6f}, {lon:.6f}**")

        alamat_otomatis = reverse_geocode(lat, lon)
        st.write(f"📌 Alamat dari koordinat: `{alamat_otomatis}`")

    submitted = st.form_submit_button("✅ Simpan")

if submitted:
    lokasi_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
    st.success("✅ Data berhasil disimpan!")

    st.subheader("📄 Ringkasan Data")
    st.write({
        "Nama Penilai": nama_penilai,
        "Tanggal": tanggal,
        "Alamat": alamat_manual if alamat_manual else alamat_otomatis,
        "Luas Tanah": luas_tanah,
        "Latitude": lat,
        "Longitude": lon
    })

    st.subheader("📍 Lokasi Properti")
    st.map(lokasi_df)