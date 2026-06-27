"""
app.py
Entry point aplikasi Streamlit Prediksi ISPU DKI Jakarta.
Semua fungsi helper (kategori ISPU, konversi konsentrasi->ISPU) ditulis
langsung di file ini agar tidak perlu modul .py tambahan. File pages/
mengimpornya kembali lewat 'from app import ...'.
"""

import streamlit as st
import base64
import os



# ============================================================
# KATEGORI ISPU (label, warna, deskripsi, saran)
# ============================================================
ISPU_CATEGORIES = [
    {"min": 0,   "max": 50,  "label": "Baik",                "color": "#4CAF50"},
    {"min": 51,  "max": 100, "label": "Sedang",               "color": "#FFC107"},
    {"min": 101, "max": 200, "label": "Tidak Sehat",          "color": "#FF7043"},
    {"min": 201, "max": 300, "label": "Sangat Tidak Sehat",   "color": "#E53935"},
    {"min": 301, "max": 500, "label": "Berbahaya",            "color": "#8E24AA"},
]

ISPU_DESCRIPTIONS = {
    "Baik": "Kualitas udara sangat baik dan tidak memberikan efek negatif terhadap kesehatan manusia maupun hewan.",
    "Sedang": "Kualitas udara masih dapat diterima pada kesehatan manusia dan makhluk hidup lainnya.",
    "Tidak Sehat": "Kualitas udara yang bersifat merugikan pada manusia maupun kelompok hewan yang sensitif.",
    "Sangat Tidak Sehat": "Kualitas udara yang dapat meningkatkan risiko kesehatan pada sejumlah segmen populasi.",
    "Berbahaya": "Kualitas udara berbahaya yang secara umum dapat merugikan kesehatan serius pada populasi.",
}

ISPU_SARAN = {
    "Baik": "Nikmati aktivitas di luar ruangan seperti biasa.",
    "Sedang": "Kelompok sensitif sebaiknya mengurangi aktivitas fisik berat di luar ruangan.",
    "Tidak Sehat": "Hindari aktivitas berat di luar ruangan dan gunakan masker saat berada di luar.",
    "Sangat Tidak Sehat": "Batasi aktivitas luar ruangan, gunakan masker N95, dan tutup ventilasi rumah.",
    "Berbahaya": "Hindari sepenuhnya aktivitas luar ruangan. Gunakan air purifier dan masker N95 jika harus keluar.",
}

POLLUTANT_LABELS = {
    "pm_sepuluh": "PM10",
    "pm_duakomalima": "PM2.5",
    "sulfur_dioksida": "SO2",
    "karbon_monoksida": "CO",
    "ozon": "O3",
    "nitrogen_dioksida": "NO2",
}

# ============================================================
# BREAKPOINT ISPU -- IDENTIK DENGAN KODE COLAB
# ============================================================
ISPU_BREAKPOINTS = {
    "pm_sepuluh": [
        (0, 50, 0, 50),
        (51, 150, 51, 100),
        (151, 350, 101, 200),
        (351, 420, 201, 300),
        (421, 500, 301, 500),
    ],
    "pm_duakomalima": [
        (0, 15.5, 0, 50),
        (15.6, 55.4, 51, 100),
        (55.5, 150.4, 101, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500, 301, 500),
    ],
    "sulfur_dioksida": [
        (0, 52, 0, 50),
        (53, 180, 51, 100),
        (181, 400, 101, 200),
        (401, 800, 201, 300),
        (801, 1200, 301, 500),
    ],
    "karbon_monoksida": [  # satuan ug/m3, sesuai breakpoint_co di Colab
        (0, 4000, 0, 50),
        (4001, 8000, 51, 100),
        (8001, 15000, 101, 200),
        (15001, 30000, 201, 300),
        (30001, 45000, 301, 500),
    ],
    "ozon": [
        (0, 120, 0, 50),
        (121, 235, 51, 100),
        (236, 400, 101, 200),
        (401, 800, 201, 300),
        (801, 1000, 301, 500),
    ],
    "nitrogen_dioksida": [
        (0, 80, 0, 50),
        (81, 200, 51, 100),
        (201, 1130, 101, 200),
        (1131, 2260, 201, 300),
        (2261, 3000, 301, 500),
    ],
}


def concentration_to_ispu(value: float, pollutant: str):
    """
    Konversi 1 nilai konsentrasi polutan menjadi nilai ISPU.
    Logic IDENTIK dengan fungsi hitung_ispu() di Colab.
    """
    pollutant = pollutant.lower()
    if pollutant not in ISPU_BREAKPOINTS:
        return None

    breakpoints = ISPU_BREAKPOINTS[pollutant]
    for x_low, x_high, i_low, i_high in breakpoints:
        if x_low <= value <= x_high:
            ispu = ((i_high - i_low) / (x_high - x_low)) * (value - x_low) + i_low
            return round(ispu, 2)
    return None


def convert_all_pollutants(concentration_dict: dict) -> dict:
    """dict {nama_polutan: konsentrasi} -> dict {nama_polutan: nilai_ispu}"""
    return {p: concentration_to_ispu(v, p) for p, v in concentration_dict.items()}


def get_ispu_category(value):
    """
    Mengembalikan dict {label, color} berdasarkan nilai ISPU.
    Logic IDENTIK dengan fungsi kategori_ispu() di Colab.
    """
    if value is None:
        return {"label": "-", "color": "#9E9E9E"}
    if value <= 50:
        return {"label": "Baik", "color": "#4CAF50"}
    elif value <= 100:
        return {"label": "Sedang", "color": "#FFC107"}
    elif value <= 200:
        return {"label": "Tidak Sehat", "color": "#FF7043"}
    elif value <= 300:
        return {"label": "Sangat Tidak Sehat", "color": "#E53935"}
    else:
        return {"label": "Berbahaya", "color": "#8E24AA"}


def get_dominant_pollutant(ispu_dict: dict) -> tuple:
    """Mengembalikan (nama_polutan_dominan, nilai_tertinggi), mengabaikan nilai None."""
    valid = {k: v for k, v in ispu_dict.items() if v is not None}
    if not valid:
        return None, None
    dominant = max(valid, key=valid.get)
    return dominant, valid[dominant]


# ============================================================
# STYLING
# ============================================================
def load_css():
    """
    Memuat style.css dari direktori yang sama dengan app.py.
    Menggunakan pathlib agar path selalu benar, tidak bergantung
    pada working directory saat Streamlit dijalankan.
    """
    from pathlib import Path
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_logo_base64(path="assets/logo.png"):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


# ============================================================
# HALAMAN UTAMA (landing)
# ============================================================
if __name__ == "__main__":
    # set_page_config() HARUS di sini (bukan di level modul) agar tidak
    # dieksekusi ulang saat pages/ melakukan `from app import ...`.
    # Jika dipanggil dua kali, Streamlit akan melempar StreamlitAPIException.
    st.set_page_config(
        page_title="Prediksi ISPU DKI Jakarta",
        page_icon="🌫️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    load_css()

    with st.sidebar:
        logo_b64 = get_logo_base64()
        logo_html = (
            f'<img src="data:image/png;base64,{logo_b64}" width="42" style="border-radius:50%;">'
            if logo_b64
            else '<div style="background:#2563EB;border-radius:50%;width:42px;height:42px;'
                 'display:flex;align-items:center;justify-content:center;">'
                 '<span style="color:white;font-size:1.3rem;">🌫️</span></div>'
        )
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px;padding:0.5rem 0 1rem 0;">
                {logo_html}
                <div>
                    <div style="color:white;font-weight:700;font-size:1.05rem;line-height:1.2;">Prediksi ISPU</div>
                    <div style="color:#CBD5E1;font-size:0.85rem;">DKI Jakarta</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.title("Prediksi ISPU DKI Jakarta")
    st.markdown(
        "Selamat datang. Gunakan menu di sidebar kiri untuk melihat "
        "**Prediksi Besok** atau membaca **Informasi ISPU**."
    )
    st.info("👈 Pilih salah satu menu di sidebar untuk memulai.")