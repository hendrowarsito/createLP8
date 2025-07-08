import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_folium import st_folium
import folium
import gspread
from google.oauth2.service_account import Credentials
import json

# === KONFIG GOOGLE SHEET ===
creds_dict = st.secrets["gspread"]
creds = Credentials.from_service_account_info(creds_dict)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/...")

def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {"User-Agent": "streamlit-inspection-app"}
        response = requests.get(url, headers=headers)
        data = response.json()
        address = data.get("address", {})
        return {
            "alamat": data.get("display_name", "Alamat tidak ditemukan"),
            "desa": address.get("village") or address.get("hamlet") or "",
            "kecamatan": address.get("suburb") or address.get("district") or "",
            "kabupaten": address.get("city") or address.get("county") or "",
            "provinsi": address.get("state") or ""
        }
    except:
        return {"alamat": "Gagal mengambil alamat", "desa": "", "kecamatan": "", "kabupaten": "", "provinsi": ""}

# === AMBIL NOMOR PROPOSAL ===
def ambil_data_proposal():
    rows = sheet.get_all_records()
    opsi = {row['Nomor Proposal']: row['Nama Perusahaan'] for row in rows if 'Nomor Proposal' in row and 'Nama Perusahaan' in row}
    return opsi

# === STREAMLIT APP ===
st.set_page_config(page_title="Form Inspeksi Properti", layout="wide")

menu = st.sidebar.radio("Navigasi", ["📋 Form Inspeksi", "📊 Data Google Sheet"])

if menu == "📋 Form Inspeksi":
    st.title("📋 Form Inspeksi Properti dengan Lokasi Interaktif & Alamat Otomatis")

    opsi_proposal = ambil_data_proposal()
    nomor_pilihan = st.selectbox("Pilih Nomor Proposal", list(opsi_proposal.keys()))
    nama_perusahaan = opsi_proposal.get(nomor_pilihan, "")
    st.markdown(f"**🏢 Nama Perusahaan:** {nama_perusahaan}")

    with st.form("form_inspeksi", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            nama_penilai = st.text_input("Nama Penilai")
            tanggal = st.date_input("Tanggal Inspeksi", value=datetime.today())
            alamat_manual = st.text_area("Alamat Manual (boleh kosong)")

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

            geo_data = reverse_geocode(lat, lon)

            st.write(f"🧭 Koordinat: **{lat:.6f}, {lon:.6f}**")
            st.write(f"📌 Alamat: `{geo_data['alamat']}`")

        submitted = st.form_submit_button("✅ Simpan")

    if submitted:
        lokasi_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.success("✅ Data berhasil disimpan!")

        st.subheader("📄 Ringkasan Data")
        st.write({
            "Nomor Proposal": nomor_pilihan,
            "Nama Perusahaan": nama_perusahaan,
            "Nama Penilai": nama_penilai,
            "Tanggal": tanggal,
            "Alamat Manual": alamat_manual if alamat_manual else geo_data['alamat'],
            "Luas Tanah": luas_tanah,
            "Latitude": lat,
            "Longitude": lon,
            "Desa": geo_data['desa'],
            "Kecamatan": geo_data['kecamatan'],
            "Kabupaten": geo_data['kabupaten'],
            "Provinsi": geo_data['provinsi']
        })

        st.subheader("📍 Lokasi Properti")
        st.map(lokasi_df)

elif menu == "📊 Data Google Sheet":
    st.title("📊 Data Terakhir dari Google Sheet")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    st.dataframe(df.tail(10), use_container_width=True)
