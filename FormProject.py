import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_folium import st_folium
import folium
import gspread
from google.oauth2.service_account import Credentials

# ============================================================

# KONFIGURASI HALAMAN

# ============================================================

st.set_page_config(
page_title = “Form Inspeksi Properti”,
page_icon = “🏠”,
layout = “wide”
)

# ============================================================

# KONEKSI GOOGLE SHEET — di-cache agar tidak reconnect tiap rerun

# ============================================================

@st.cache_resource
def get_sheet():
creds = Credentials.from_service_account_info(
st.secrets[“gspread”],
scopes=[
“https://spreadsheets.google.com/feeds”,
“https://www.googleapis.com/auth/drive”
]
)
client = gspread.authorize(creds)
return client.open_by_url(“https://docs.google.com/spreadsheets/d/…”)

# ============================================================

# AMBIL DATA PROPOSAL — di-cache 5 menit

# ============================================================

@st.cache_data(ttl=300)
def ambil_data_proposal():
“”“Ambil daftar nomor proposal dari Google Sheet tab pertama.”””
try:
sheet = get_sheet()
rows = sheet.get_all_records()
opsi = {
row[“Nomor Proposal”]: row[“Nama Perusahaan”]
for row in rows
if “Nomor Proposal” in row and “Nama Perusahaan” in row
}
return opsi
except Exception as e:
st.error(f”Gagal memuat data proposal: {e}”)
return {}

# ============================================================

# SIMPAN DATA KE GOOGLE SHEET

# ============================================================

def simpan_ke_sheet(data: dict) -> bool:
“”“Simpan satu baris data ke worksheet ‘Inspeksi’. Return True jika berhasil.”””
try:
sheet = get_sheet()
try:
ws = sheet.worksheet(“Inspeksi”)
except gspread.WorksheetNotFound:
# Buat worksheet baru jika belum ada
ws = sheet.add_worksheet(title=“Inspeksi”, rows=“1000”, cols=“20”)
headers = [
“Timestamp”, “Nomor Proposal”, “Nama Perusahaan”,
“Nama Penilai”, “Tanggal Inspeksi”, “Alamat”,
“Luas Tanah (m²)”, “Latitude”, “Longitude”,
“Desa”, “Kecamatan”, “Kabupaten”, “Provinsi”, “Catatan”
]
ws.append_row(headers)

```
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data["nomor_proposal"],
        data["nama_perusahaan"],
        data["nama_penilai"],
        str(data["tanggal"]),
        data["alamat"],
        data["luas_tanah"],
        data["lat"],
        data["lon"],
        data["desa"],
        data["kecamatan"],
        data["kabupaten"],
        data["provinsi"],
        data["catatan"],
    ]
    ws.append_row(row)
    return True
except Exception as e:
    st.error(f"Gagal menyimpan data: {e}")
    return False
```

# ============================================================

# REVERSE GEOCODE — dengan cache per koordinat

# ============================================================

@st.cache_data(ttl=3600)
def reverse_geocode(lat: float, lon: float) -> dict:
“”“Konversi koordinat ke alamat menggunakan Nominatim OSM.”””
try:
url = (
f”https://nominatim.openstreetmap.org/reverse”
f”?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1”
)
headers = {“User-Agent”: “srr-inspeksi-app/1.0”}
response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()
data = response.json()
address = data.get(“address”, {})
return {
“alamat”: data.get(“display_name”, “Alamat tidak ditemukan”),
“desa”: address.get(“village”) or address.get(“hamlet”) or address.get(“neighbourhood”) or “”,
“kecamatan”: address.get(“suburb”) or address.get(“district”) or “”,
“kabupaten”: address.get(“city”) or address.get(“regency”) or address.get(“county”) or “”,
“provinsi”: address.get(“state”) or “”,
}
except requests.Timeout:
st.warning(“Geocoding timeout. Coba klik ulang lokasi di peta.”)
return _empty_geo()
except requests.RequestException as e:
st.warning(f”Geocoding gagal: {e}”)
return _empty_geo()
except Exception as e:
st.warning(f”Error tidak terduga saat geocoding: {e}”)
return _empty_geo()

def _empty_geo() -> dict:
return {“alamat”: “”, “desa”: “”, “kecamatan”: “”, “kabupaten”: “”, “provinsi”: “”}

# ============================================================

# INISIALISASI SESSION STATE

# ============================================================

if “lat” not in st.session_state:
st.session_state[“lat”] = -6.200000
if “lon” not in st.session_state:
st.session_state[“lon”] = 106.816666
if “geo_data” not in st.session_state:
st.session_state[“geo_data”] = _empty_geo()
if “form_submitted” not in st.session_state:
st.session_state[“form_submitted”] = False

# ============================================================

# NAVIGASI SIDEBAR

# ============================================================

menu = st.sidebar.radio(
“Navigasi”,
[“📋 Form Inspeksi”, “📊 Data Google Sheet”],
index=0
)

# ============================================================

# HALAMAN 1: FORM INSPEKSI

# ============================================================

if menu == “📋 Form Inspeksi”:
st.title(“📋 Form Inspeksi Properti”)
st.caption(“Isi data inspeksi, klik lokasi di peta, lalu tekan Simpan.”)

```
# --- Pilih Proposal ---
opsi_proposal = ambil_data_proposal()
if not opsi_proposal:
    st.warning("Data proposal kosong atau gagal dimuat.")
    st.stop()

col_prop1, col_prop2 = st.columns([1, 2])
with col_prop1:
    nomor_pilihan = st.selectbox("Nomor Proposal", list(opsi_proposal.keys()))
with col_prop2:
    nama_perusahaan = opsi_proposal.get(nomor_pilihan, "")
    st.markdown(f"**🏢 Nama Perusahaan:** {nama_perusahaan}")

st.divider()

# --- PETA (di luar form agar koordinat terupdate real-time) ---
st.markdown("### 📍 Pilih Lokasi di Peta")
st.caption("Klik titik mana saja di peta untuk mengambil koordinat dan alamat otomatis.")

lat_now = st.session_state["lat"]
lon_now = st.session_state["lon"]

m = folium.Map(location=[lat_now, lon_now], zoom_start=13)
m.add_child(folium.LatLngPopup())

# Tampilkan marker jika koordinat sudah dipilih
if st.session_state["geo_data"]["alamat"]:
    folium.Marker(
        location=[lat_now, lon_now],
        tooltip=f"📍 {lat_now:.6f}, {lon_now:.6f}",
        icon=folium.Icon(color="red", icon="home", prefix="fa")
    ).add_to(m)

map_output = st_folium(m, width="100%", height=420, key="peta_inspeksi")

# Update koordinat & geocode hanya jika user klik lokasi baru
if map_output and map_output.get("last_clicked"):
    new_lat = round(map_output["last_clicked"]["lat"], 7)
    new_lon = round(map_output["last_clicked"]["lng"], 7)

    if (new_lat, new_lon) != (st.session_state["lat"], st.session_state["lon"]):
        st.session_state["lat"] = new_lat
        st.session_state["lon"] = new_lon
        with st.spinner("Mengambil alamat..."):
            st.session_state["geo_data"] = reverse_geocode(new_lat, new_lon)
        st.rerun()

geo = st.session_state["geo_data"]
lat = st.session_state["lat"]
lon = st.session_state["lon"]

# Info koordinat & alamat hasil geocode
col_geo1, col_geo2 = st.columns(2)
with col_geo1:
    st.info(f"🧭 **Koordinat:** {lat:.7f}, {lon:.7f}")
with col_geo2:
    if geo["alamat"]:
        st.info(f"📌 **Alamat:** {geo['alamat'][:120]}{'...' if len(geo['alamat']) > 120 else ''}")
    else:
        st.warning("Belum ada lokasi dipilih. Klik peta untuk memilih.")

st.divider()

# --- FORM DATA INSPEKSI ---
st.markdown("### 📝 Data Inspeksi")
with st.form("form_inspeksi", clear_on_submit=False):
    col1, col2 = st.columns(2)

    with col1:
        nama_penilai = st.text_input("Nama Penilai *", placeholder="Contoh: Budi Santoso, MAPPI")
        tanggal = st.date_input("Tanggal Inspeksi *", value=datetime.today())
        luas_tanah = st.number_input("Luas Tanah (m²) *", min_value=0.0, step=0.5, format="%.2f")
        alamat_override = st.text_area(
            "Override Alamat (opsional)",
            placeholder="Kosongkan untuk pakai alamat otomatis dari peta",
            height=90
        )

    with col2:
        # Tampilkan hasil geocode (read-only)
        st.text_input("Desa / Kelurahan", value=geo["desa"], disabled=True)
        st.text_input("Kecamatan", value=geo["kecamatan"], disabled=True)
        st.text_input("Kabupaten / Kota", value=geo["kabupaten"], disabled=True)
        st.text_input("Provinsi", value=geo["provinsi"], disabled=True)

    catatan = st.text_area("Catatan Tambahan", placeholder="Kondisi bangunan, akses jalan, dll.", height=80)

    submitted = st.form_submit_button("✅ Simpan Data Inspeksi", use_container_width=True)

# --- VALIDASI & SIMPAN ---
if submitted:
    errors = []
    if not nama_penilai.strip():
        errors.append("Nama Penilai wajib diisi.")
    if luas_tanah <= 0:
        errors.append("Luas Tanah harus lebih dari 0.")
    if lat == -6.200000 and lon == 106.816666:
        errors.append("Lokasi belum dipilih. Klik titik di peta terlebih dahulu.")

    if errors:
        for err in errors:
            st.error(f"❌ {err}")
    else:
        alamat_final = alamat_override.strip() if alamat_override.strip() else geo["alamat"]
        data_simpan = {
            "nomor_proposal": nomor_pilihan,
            "nama_perusahaan": nama_perusahaan,
            "nama_penilai": nama_penilai.strip(),
            "tanggal": tanggal,
            "alamat": alamat_final,
            "luas_tanah": luas_tanah,
            "lat": lat,
            "lon": lon,
            "desa": geo["desa"],
            "kecamatan": geo["kecamatan"],
            "kabupaten": geo["kabupaten"],
            "provinsi": geo["provinsi"],
            "catatan": catatan.strip(),
        }

        with st.spinner("Menyimpan ke Google Sheet..."):
            sukses = simpan_ke_sheet(data_simpan)

        if sukses:
            st.success("✅ Data berhasil disimpan ke Google Sheet!")
            st.session_state["form_submitted"] = True

            # Ringkasan
            st.subheader("📄 Ringkasan Data Tersimpan")
            df_ringkasan = pd.DataFrame([data_simpan]).T.rename(columns={0: "Nilai"})
            st.dataframe(df_ringkasan, use_container_width=True)

            # Mini-map konfirmasi
            st.subheader("📍 Konfirmasi Lokasi")
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=15)
```

# ============================================================

# HALAMAN 2: DATA GOOGLE SHEET

# ============================================================

elif menu == “📊 Data Google Sheet”:
st.title(“📊 Data Inspeksi dari Google Sheet”)

```
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

try:
    sheet = get_sheet()
    try:
        ws = sheet.worksheet("Inspeksi")
        data = ws.get_all_records()
    except gspread.WorksheetNotFound:
        st.info("Worksheet 'Inspeksi' belum ada. Simpan data pertama melalui Form Inspeksi.")
        st.stop()

    if not data:
        st.info("Belum ada data inspeksi.")
    else:
        df = pd.DataFrame(data)
        st.caption(f"Total {len(df)} record. Menampilkan 20 terbaru.")
        st.dataframe(df.tail(20), use_container_width=True)

        # Peta semua lokasi inspeksi
        if "Latitude" in df.columns and "Longitude" in df.columns:
            df_map = df[["Latitude", "Longitude"]].dropna().rename(
                columns={"Latitude": "lat", "Longitude": "lon"}
            )
            df_map["lat"] = pd.to_numeric(df_map["lat"], errors="coerce")
            df_map["lon"] = pd.to_numeric(df_map["lon"], errors="coerce")
            df_map = df_map.dropna()

            if not df_map.empty:
                st.subheader("🗺️ Peta Semua Lokasi Inspeksi")
                st.map(df_map, zoom=10)

except Exception as e:
    st.error(f"Gagal memuat data dari Google Sheet: {e}")
```

