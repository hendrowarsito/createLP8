import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Form Inspeksi Properti", layout="wide")
st.title("📋 Form Inspeksi Properti")

with st.form("form_inspeksi", clear_on_submit=False, height=500):
    col1, col2 = st.columns(2)
    with col1:
        nama_penilai = st.text_input("Nama Penilai")
        tanggal = st.date_input("Tanggal Inspeksi", value=datetime.today())
        alamat = st.text_area("Alamat Properti")
    with col2:
        luas_tanah = st.number_input("Luas Tanah (m²)", min_value=0.0)
        lat = st.number_input("Latitude (Koordinat)", format="%.6f")
        lon = st.number_input("Longitude (Koordinat)", format="%.6f")

    submitted = st.form_submit_button("✅ Simpan")

if submitted:
    lokasi_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
    st.success("Data berhasil disimpan!")
    
    # Tampilkan ringkasan
    st.subheader("📄 Ringkasan Data")
    st.write({
        "Nama Penilai": nama_penilai,
        "Tanggal": tanggal,
        "Alamat": alamat,
        "Luas Tanah": luas_tanah,
        "Latitude": lat,
        "Longitude": lon
    })

    # Tampilkan peta
    st.subheader("📍 Lokasi Properti di Peta")
    st.map(lokasi_df)