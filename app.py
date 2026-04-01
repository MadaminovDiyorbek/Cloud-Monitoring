import streamlit as st
import pandas as pd
import os
from postgrest import SyncPostgrestClient
from streamlit_autorefresh import st_autorefresh

# --- 1. SOZLAMALAR ---
# Streamlit Secrets orqali Supabase kalitlarini olish
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Xato: Supabase kalitlari topilmadi! Streamlit Cloud 'Secrets' bo'limini tekshiring.")
    st.stop()

# Supabase Klientini yaratish
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
client = SyncPostgrestClient(SUPABASE_URL, headers=headers)

# Sahifa sozlamalari
st.set_page_config(page_title="OmniCloud Pro Monitoring", layout="wide", page_icon="📊")

# Avtomatik yangilanish: Har 10 soniyada sahifani yangilaydi
st_autorefresh(interval=10000, key="datarefresh")

# --- 2. YORDAMCHI FUNKSIYALAR ---
def get_status_emoji(val):
    """Qiymatga qarab rangli emoji qaytaradi"""
    if val < 50: return "🟢"
    if val < 85: return "🟡"
    return "🔴"

def get_data_from_supabase():
    """Bazadan oxirgi 30 ta yozuvni olib keladi"""
    try:
        response = client.table("monitor_logs").select("*").order("created_at", desc=True).limit(30).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Baza bilan aloqa yuzaga kelmadi: {e}")
        return pd.DataFrame()

# --- 3. ASOSIY INTERFEYS ---
st.title("🌐 OmniCloud: Advanced Cloud Monitoring")

df = get_data_from_supabase()

if not df.empty:
    # Eng oxirgi kelgan ma'lumot
    latest = df.iloc[0]
    
    # Yuqori Metrikalar Paneli (5 ta ustun)
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        st.metric(f"{get_status_emoji(latest['cpu_percent'])} CPU", f"{latest['cpu_percent']}%")
    with m2:
        st.metric(f"{get_status_emoji(latest['ram_percent'])} RAM", f"{latest['ram_percent']}%")
    with m3:
        st.metric("💽 Disk", f"{latest['disk_percent']}%")
    with m4:
        # get('ustun_nomi', 0) - agar ustun bo'sh bo'lsa xato bermaydi
        st.metric("⬇️ Download", f"{latest.get('net_down', 0)} MB/s")
    with m5:
        st.metric("⬆️ Upload", f"{latest.get('net_up', 0)} MB/s")

    st.markdown("---")
    
    # Grafiklarni joylashtirish (Chap va O'ng ustun)
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Vaqtni grafik uchun chiroyli formatlash
        df['time'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
        
        st.subheader("🚀 Tarmoq Tezligi Dinamikasi (MB/s)")
        # Internet tezligi grafigi (Download va Upload birga)
        st.area_chart(df.set_index('time')[['net_down', 'net_up']])
        
        st.subheader("📊 Tizim Yuklamasi (%)")
        # CPU va RAM grafigi
        st.line_chart(df.set_index('time')[['cpu_percent', 'ram_percent']])

    with col_right:
        st.subheader("📋 Oxirgi Loglar")
        # Loglar jadvali (eng kerakli ustunlar bilan)
        log_df = df[['time', 'cpu_percent', 'ram_percent', 'net_down']].head(10)
        st.dataframe(log_df, use_container_width=True)
        
        # Kritik ogohlantirishlar paneli
        st.subheader("⚠️ Holat")
        if latest['cpu_percent'] > 85:
            st.error(f"Kritik: Protsessor yuklamasi {latest['cpu_percent']}% !")
        elif latest['ram_percent'] > 90:
            st.warning(f"Diqqat: Operativ xotira deyarli to'ldi!")
        else:
            st.success("Tizim barqaror ishlamoqda.")

else:
    st.info("Ma'lumotlar bazadan kutilmoqda... Agent.py ishlayotganiga ishonch hosil qiling.")

# Footer qismi
st.markdown("---")
st.caption(f"Oxirgi yangilanish: {pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')}")
