"""
2_🌫️_Informasi_ISPU.py
Halaman Informasi ISPU: penjelasan 5 kategori kualitas udara
(Baik, Sedang, Tidak Sehat, Sangat Tidak Sehat, Berbahaya).
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from app import load_css, ISPU_CATEGORIES, ISPU_DESCRIPTIONS, ISPU_SARAN

st.set_page_config(page_title="Informasi ISPU", layout="wide")
load_css()

st.markdown("## Informasi ISPU")
st.caption("Indeks Standar Pencemar Udara (ISPU) dan kategori kualitas udara, "
           "mengacu pada Peraturan Menteri LHK No. 14 Tahun 2020.")

for cat in ISPU_CATEGORIES:
    label = cat["label"]
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(
                f"""
                <div style="background:{cat['color']};color:white;border-radius:10px;
                            padding:1rem;text-align:center;font-weight:700;">
                    {cat['min']}–{cat['max']}<br>
                    <span style="font-size:0.85rem;">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(f"#### {label}")
            st.write(ISPU_DESCRIPTIONS[label])
            st.markdown(f"**Saran:** {ISPU_SARAN[label]}")