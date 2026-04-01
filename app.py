import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from postgrest import SyncPostgrestClient
from streamlit_autorefresh import st_autorefresh

# --- 1. SUPABASE SOZLAMALARI ---
SUPABASE_URL = "https://wffcuseusugwafljvavv.supabase.co/rest/v1"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmZmN1c2V1c3Vnd2FmbGp2YXZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzI3MzMsImV4cCI6MjA5MDM0ODczM30.LhC9OE3lRBROjabQsOAQVbt4L691Bwnt13MW8UZ2-qY"

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
client = SyncPostgrestClient(SUPABASE_URL, headers=headers)

# --- 2. SAHIFA DIZAYNI ---
st.set_page_config(page_title="OmniCloud Monitoring", layout="wide", page_icon="🌐")

# Avtomatik yangilanish (Har 10 soniyada)
st_autorefresh(interval=10000, key="datarefresh")

st.markdown("""
    <style>
    .stMetric {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MA'LUMOTLARNI SUPABASE'DAN OLISH ---
def get_data_from_supabase():
    try:
        response = client.table("monitor_logs").select("*").order("created_at", desc=True).limit(20).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Baza bilan aloqa yo'q: {e}")
        return pd.DataFrame()

# --- 4. INTERFEYS ---
st.title("🌐 OmniCloud: Cloud Monitoring System")

df = get_data_from_supabase()

if not df.empty:
    # Oxirgi holatni olish
    latest = df.iloc[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("CPU", f"{latest['cpu_percent']}%")
    col2.metric("RAM", f"{latest['ram_percent']}%")
    col3.metric("Disk", f"{latest['disk_percent']}%")

    st.markdown("---")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("📈 Tizim grafigi (Oxirgi 20 ta holat)")
        # Grafik uchun vaqtni formatlash
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
        st.line_chart(df.set_index('created_at')[['cpu_percent', 'ram_percent']])
        
    with c2:
        st.subheader("📋 Oxirgi Loglar")
        st.dataframe(df[['hostname', 'cpu_percent', 'ram_percent', 'created_at']].head(10))

else:
    st.info("Hozircha ma'lumot yo'q. Agent.py kodi ishlayotganiga ishonch hosil qiling.")

# Tarmoq skaneri (Vercel'da cheklangan bo'lishi mumkin)
with st.expander("📡 Tarmoq skaneri (Lokal uchun)"):
    st.warning("Eslatma: Ushbu funksiya faqat lokal tarmoqda va admin huquqi bilan ishlaydi.")
    ip_range = st.text_input("IP diapazon:", "192.168.1.1/24")
    if st.button("Skanerlash"):
        st.error("Cloud serverda xavfsizlik tufayli taqiqlangan.")
