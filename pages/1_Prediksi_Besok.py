"""
1_📈_Prediksi_Besok.py
Halaman Dashboard utama: kondisi saat ini, prediksi besok (Stacked LSTM - Hampel),
tabel konsentrasi polutan, tren 7 hari, dan ringkasan prediksi.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import numpy as np
import pandas as pd
import pickle
import plotly.graph_objects as go
import tensorflow as tf

st.success("✅ TensorFlow berhasil diimport")
st.write("TensorFlow Version:", tf.__version__)

st.stop()
from datetime import datetime, timedelta

from app import (
    load_css,
    convert_all_pollutants,
    get_ispu_category,
    get_dominant_pollutant,
    ISPU_DESCRIPTIONS,
    ISPU_SARAN,
    POLLUTANT_LABELS,
)

st.set_page_config(page_title="Prediksi Besok - ISPU", layout="wide")
load_css()

# ============================================================
# LOAD MODEL & ASET (cached supaya tidak reload tiap interaksi)
# ============================================================
# @st.cache_resource
# def load_model():
#     return tf.keras.models.load_model(
#         "model/model_hampel_22.keras",
#         compile=False
#     )


@st.cache_resource
def load_pickle_file(path):
    with open(path, "rb") as f:
        return pickle.load(f)


try:
    # model = load_model()
    min_vals_hampel = load_pickle_file("data/min_vals_hampel.pkl")   # dict {nama_fitur: nilai_min}
    max_vals_hampel = load_pickle_file("data/max_vals_hampel.pkl")   # dict {nama_fitur: nilai_max}
    features = load_pickle_file("data/features.pkl")                  # list nama fitur, urutan sesuai training
    last_7_days_raw = load_pickle_file("data/last_7_days.pkl")        # SUDAH ternormalisasi (dari Dataset_Hampel_Norm)
except FileNotFoundError as e:
    st.error(f"File tidak ditemukan: {e}. Pastikan folder model/ dan data/ sudah lengkap.")
    st.stop()

# last_7_days bisa berupa DataFrame ATAU array numpy -- tangani keduanya,
# lalu pastikan urutan kolom mengikuti 'features' (PENTING untuk konsistensi model).
# CATATAN: data ini SUDAH ternormalisasi (diambil dari Dataset_Hampel_Norm di Colab),
# jadi TIDAK dinormalisasi ulang -- langsung dipakai sebagai input model.
if isinstance(last_7_days_raw, pd.DataFrame):
    last_7_days_norm = last_7_days_raw[features].to_numpy(dtype=float)
else:
    last_7_days_norm = np.array(last_7_days_raw, dtype=float)
    if last_7_days_norm.ndim == 1:
        last_7_days_norm = last_7_days_norm.reshape(1, -1)

# Susun min_vals & max_vals sebagai array, urutannya MENGIKUTI 'features'
# (karena min_vals_hampel & max_vals_hampel aslinya dictionary, bukan array)
min_vals = np.array([min_vals_hampel[f] for f in features], dtype=float)
max_vals = np.array([max_vals_hampel[f] for f in features], dtype=float)

st.success("✅ Dashboard berhasil dibuka tanpa TensorFlow")

st.write("Features:", features)
st.write("Shape:", last_7_days_norm.shape)

st.stop()

# ============================================================
# PREDIKSI -- IDENTIK DENGAN KODE COLAB (TANPA NORMALISASI ULANG)
# ============================================================
model_input = last_7_days_norm.reshape(1, last_7_days_norm.shape[0], last_7_days_norm.shape[1])

pred_scaled = model.predict(model_input, verbose=0).flatten()

# DENORMALISASI -- identik dengan loop di Colab
pred_concentration_arr = pred_scaled * (max_vals - min_vals) + min_vals

tomorrow_concentration = {feat: float(val) for feat, val in zip(features, pred_concentration_arr)}
tomorrow_ispu = convert_all_pollutants(tomorrow_concentration)

# Kondisi hari ini = baris terakhir dari last_7_days, DIDENORMALISASI dulu
today_row_norm = last_7_days_norm[-1]
today_concentration_arr = today_row_norm * (max_vals - min_vals) + min_vals
today_concentration = {feat: float(val) for feat, val in zip(features, today_concentration_arr)}
today_ispu = convert_all_pollutants(today_concentration)

ispu_today_value = max(v for v in today_ispu.values() if v is not None)
ispu_tomorrow_value = max(v for v in tomorrow_ispu.values() if v is not None)

cat_today = get_ispu_category(ispu_today_value)
cat_tomorrow = get_ispu_category(ispu_tomorrow_value)

dominant_today, _ = get_dominant_pollutant(today_ispu)
dominant_tomorrow, _ = get_dominant_pollutant(tomorrow_ispu)

# PENTING: tanggal di dashboard mengikuti tanggal TERAKHIR pada dataset historis
# (hari ke-700 dari 700 hari data = 30 November 2025), BUKAN tanggal sistem laptop.
# Model hanya memprediksi 1 hari ke depan dari data historis yang tersedia
# (hari ke-701), sehingga dashboard ini bukan prediksi kualitas udara real-time.
today_date = datetime(2025, 11, 30)
tomorrow_date = today_date + timedelta(days=1)


def render_gauge(value, key_suffix=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"size": 38}},
        gauge={
            "axis": {"range": [0, 500]},
            "bar": {"color": "black", "thickness": 0.25},
            "steps": [
                {"range": [0, 50], "color": "#4CAF50"},
                {"range": [50, 100], "color": "#FFC107"},
                {"range": [100, 200], "color": "#FF7043"},
                {"range": [200, 300], "color": "#E53935"},
                {"range": [300, 500], "color": "#8E24AA"},
            ],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10))
    return fig


# ============================================================
# HEADER
# ============================================================
col_title, col_update = st.columns([3, 1])
with col_title:
    st.markdown("## Prediksi ISPU DKI Jakarta")
    st.caption("Satu Hari ke Depan")
with col_update:
    with st.container(border=True):
        st.markdown(f"📅 **Data Terakhir**  \n{today_date.strftime('%d %B %Y')}")

# ============================================================
# ROW 1: KONDISI SAAT INI & PREDIKSI BESOK
# ============================================================
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("**KONDISI SAAT INI**  `Data Aktual`")
        st.caption(today_date.strftime("%A, %d %B %Y"))
        g1, g2 = st.columns([1.2, 1])
        with g1:
            st.plotly_chart(render_gauge(ispu_today_value), use_container_width=True, key="gauge_today")
        with g2:
            st.markdown(
                f"<span style='background:{cat_today['color']};color:white;padding:0.25rem 0.8rem;"
                f"border-radius:999px;font-size:0.78rem;font-weight:700;'>{cat_today['label']}</span>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='font-size:0.85rem;color:#64748B;margin-top:0.5rem;'>Polutan dominan</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:1.4rem;font-weight:700;color:#1E3A8A;'>{POLLUTANT_LABELS.get(dominant_today, dominant_today)}</div>", unsafe_allow_html=True)
            st.caption(ISPU_DESCRIPTIONS[cat_today["label"]])

with col2:
    with st.container(border=True):
        st.markdown("**PREDIKSI BESOK**  `Model: Stacked LSTM`")
        st.caption(tomorrow_date.strftime("%A, %d %B %Y"))
        g1, g2 = st.columns([1.2, 1])
        with g1:
            st.plotly_chart(render_gauge(ispu_tomorrow_value), use_container_width=True, key="gauge_tomorrow")
        with g2:
            st.markdown(
                f"<span style='background:{cat_tomorrow['color']};color:white;padding:0.25rem 0.8rem;"
                f"border-radius:999px;font-size:0.78rem;font-weight:700;'>{cat_tomorrow['label']}</span>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='font-size:0.85rem;color:#64748B;margin-top:0.5rem;'>Polutan dominan</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:1.4rem;font-weight:700;color:#1E3A8A;'>{POLLUTANT_LABELS.get(dominant_tomorrow, dominant_tomorrow)}</div>", unsafe_allow_html=True)
            st.caption(ISPU_SARAN[cat_tomorrow["label"]])

# ============================================================
# ROW 2: TABEL KONSENTRASI POLUTAN & TREN 7 HARI
# ============================================================
col3, col4 = st.columns([1.4, 1])

with col3:
    with st.container(border=True):
        st.markdown("**KONSENTRASI POLUTAN (µg/m³)**")
        t1, t2 = st.columns(2)
        with t1:
            st.markdown("*Kondisi Saat Ini*")
            df_today = pd.DataFrame({
                "Polutan": [POLLUTANT_LABELS.get(f, f) for f in features],
                "Konsentrasi": [round(today_concentration[f], 1) for f in features],
                "Kategori": [get_ispu_category(today_ispu[f])["label"] for f in features],
            })
            st.dataframe(df_today, hide_index=True, use_container_width=True)
        with t2:
            st.markdown("*Prediksi Besok*")
            df_tomorrow = pd.DataFrame({
                "Polutan": [POLLUTANT_LABELS.get(f, f) for f in features],
                "Prediksi": [round(tomorrow_concentration[f], 1) for f in features],
                "Kategori": [get_ispu_category(tomorrow_ispu[f])["label"] for f in features],
            })
            st.dataframe(df_tomorrow, hide_index=True, use_container_width=True)

with col4:
    with st.container(border=True):
        st.markdown("**TREN ISPU 7 HARI TERAKHIR**")
        ispu_per_day = []
        for row_norm in last_7_days_norm:
            # Denormalisasi dulu (row_norm masih skala 0-1) sebelum hitung ISPU
            row_concentration = row_norm * (max_vals - min_vals) + min_vals
            conc = {f: float(v) for f, v in zip(features, row_concentration)}
            ispu_vals = convert_all_pollutants(conc)
            valid_vals = [v for v in ispu_vals.values() if v is not None]
            ispu_per_day.append(max(valid_vals) if valid_vals else 0)

        dates_7 = [(today_date - timedelta(days=6 - i)).strftime("%d %b") for i in range(len(ispu_per_day))]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates_7, y=ispu_per_day, mode="lines+markers", name="ISPU Aktual"))
        fig.add_trace(go.Scatter(
            x=[dates_7[-1], tomorrow_date.strftime("%d %b")],
            y=[ispu_per_day[-1], ispu_tomorrow_value],
            mode="lines+markers", name="Prediksi", line=dict(dash="dot"),
        ))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, key="tren_7_hari")

# ============================================================
# ROW 3: RINGKASAN PREDIKSI
# ============================================================
with st.container(border=True):
    st.markdown("**RINGKASAN PREDIKSI**")
    r1, r2 = st.columns(2)
    with r1:
        st.write(f"📅 **Tanggal Prediksi:** {tomorrow_date.strftime('%d %B %Y')}")
        st.write(f"📈 **Prediksi ISPU:** {ispu_tomorrow_value:.0f}")
    with r2:
        st.markdown(
            f"🏷️ **Kategori:** <span style='background:{cat_tomorrow['color']};color:white;"
            f"padding:0.2rem 0.7rem;border-radius:999px;font-size:0.78rem;font-weight:700;'>"
            f"{cat_tomorrow['label']}</span>",
            unsafe_allow_html=True,
        )
        st.write(f"👤 **Polutan Dominan:** {POLLUTANT_LABELS.get(dominant_tomorrow, dominant_tomorrow)}")
    st.write(f"ℹ️ **Saran:** {ISPU_SARAN[cat_tomorrow['label']]}")

st.caption("Catatan: Prediksi dilakukan menggunakan model Stacked Long Short-Term Memory (LSTM) "
           "dengan penanganan outlier Hampel Filter, berdasarkan data 7 hari terakhir.")
