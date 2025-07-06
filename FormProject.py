import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Form Inspeksi Properti", layout="wide")
st.title("📋 Form Inspeksi Properti dengan Lokasi Interaktif")

with st.form("form_inspeksi", clear_on_submit=False, height=500):
    col1, col2 = st.columns(2)
    with col1:
        nama_penilai = st.text_input("Nama Penilai")
        tanggal = st.date_input("Tanggal Inspeksi", value=datetime.today())
        alamat = st.text_area("Alamat Properti")
    with col2:
        luas_tanah = st.number_input("Luas Tanah (m²)", min_value=0.0)
        default_lat = -6.200000
        default_lon = 106.816666

        st.markdown("### 📍 Klik di peta untuk memilih koordinat")
        m = folium.Map(location=[default_lat, default_lon], zoom_start=12)
        marker = folium.Marker(location=[default_lat, default_lon], draggable=True)
        marker.add_to(m)

        # Tambahkan fitur klik
        m.add_child(folium.LatLngPopup())

        output = st_folium(m, width=700, height=400)
        
        lat = output["last_clicked"]["lat"] if output["last_clicked"] else default_lat
        lon = output["last_clicked"]["lng"] if output["last_clicked"] else default_lon

        st.write(f"🧭 Koordinat yang dipilih: **{lat:.6f}, {lon:.6f}**")

    submitted = st.form_submit_button("✅ Simpan")

if submitted:
    lokasi_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
    st.success("Data berhasil disimpan!")

    st.subheader("📄 Ringkasan Data")
    st.write({
        "Nama Penilai": nama_penilai,
        "Tanggal": tanggal,
        "Alamat": alamat,
        "Luas Tanah": luas_tanah,
        "Latitude": lat,
        "Longitude": lon
    })

    st.subheader("📍 Lokasi Properti")
    st.map(lokasi_df)