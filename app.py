import streamlit as st
import pandas as pd
from postgrest import SyncPostgrestClient

SUPABASE_URL = "https://wffcuseusugwafljvavv.supabase.co/rest/v1"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmZmN1c2V1c3Vnd2FmbGp2YXZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzI3MzMsImV4cCI6MjA5MDM0ODczM30.LhC9OE3lRBROjabQsOAQVbt4L691Bwnt13MW8UZ2-qY"

# --- 1. SAHIFA VA DIZAYN SOZLAMALARI ---
st.set_page_config(page_title="OmniCloud Integrated System", layout="wide", page_icon="🌐")

# --- CSS: Chiroyli va Ko'rinadigan Dizayn ---
st.markdown("""
    <style>
    /* Asosiy fon rangini to'q qilish */
    .main { background-color: #0E1117; }
    
    /* 3 ta blok (Metrics) uchun yangi stil */
    div[data-testid="stMetricValue"] > div {
        color: #FFFFFF !important; /* Raqamlar rangi - OQ */
        font-size: 32px;
        font-weight: bold;
    }
    div[data-testid="stMetricLabel"] > label {
        color: #A0A0A0 !important; /* Sarlavhalar rangi - KULRANG */
        font-size: 16px;
    }
    
    /* Bloklarning o'zi (To'rtburchaklar) */
    .stMetric {
        background-color: #1E1E1E; /* Fon - TO'Q KULRANG */
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #262730; /* Nozik chegara */
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); /* Soya */
        transition: transform 0.2s; /* Sichqoncha borganda effekt */
    }
    
    /* Sichqoncha blok ustiga borganda ko'k chegara */
    .stMetric:hover {
        border-color: #4B9BFF;
        transform: translateY(-3px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MA'LUMOTLAR BAZASI (SQLite) SOZLAMALARI ---
# Baza bilan bog'lanish
conn = sqlite3.connect('omnicloud_data.db', check_same_thread=False)
c = conn.cursor()

# Jadvalni yaratish (Tizim loglari uchun)
c.execute('''CREATE TABLE IF NOT EXISTS system_logs 
             (timestamp TEXT, cpu REAL, ram REAL, disk REAL, sent REAL, recv REAL)''')
conn.commit()

def save_to_db(cpu, ram, disk, sent, recv):
    """Ma'lumotlarni bazaga saqlash funksiyasi"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO system_logs VALUES (?, ?, ?, ?, ?, ?)", 
              (now, cpu, ram, disk, sent, recv))
    conn.commit()

# --- 3. TIZIM METRIKALARINI OLISH ---
def get_system_metrics():
    net = psutil.net_io_counters()
    return {
        "vaqt": datetime.now().strftime("%H:%M:%S"),
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "sent": round(net.bytes_sent / (1024 * 1024), 2),
        "recv": round(net.bytes_recv / (1024 * 1024), 2)
    }
def scan_network(ip_range):
    # ARP so'rovini yuborish
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp
    result = srp(packet, timeout=3, verbose=0)[0]
    
    # Brendlarni qidirish uchun obyekt yaratish
    vendor_lookup = MacLookup()
    
    devices = []
    for sent, received in result:
        try:
            # MAC manzil orqali brendni aniqlash
            brand = vendor_lookup.lookup(received.hwsrc)
        except:
            brand = "Noma'lum qurilma"
            
        devices.append({
            'IP Manzil': received.psrc, 
            'MAC Manzil': received.hwsrc,
            'Ishlab chiqaruvchi': brand  # Jadvalda yangi ustun chiqadi
        })
    return devices

# --- 4. INTERFEYS (UI) ---
st.title("🌐 OmniCloud: Professional Monitoring & Integration")

# Sidebar
st.sidebar.header("⚙️ Sozlamalar")
update_interval = st.sidebar.slider("Yangilanish (sekund):", 1, 10, 2)

st.sidebar.markdown("---")
st.sidebar.header("📂 Bulutli Sinxronizatsiya")
sync_path = st.sidebar.text_input("Kuzatiladigan papka:", os.getcwd())
if st.sidebar.button("Sinxronizatsiyani faollashtirish"):
    st.sidebar.success(f"✅ {sync_path} kuzatilmoqda...")
st.sidebar.markdown("---")
st.sidebar.header("📊 Hisobot tayyorlash")

# Bazadagi eng oxirgi 20 ta ma'lumotni olish
if st.sidebar.button("Oxirgi 20 ta logni tayyorlash"):
    # SQL so'rovini o'zgartirdik: ORDER BY va LIMIT qo'shildi
    query = "SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 20"
    df_short = pd.read_sql_query(query, conn)
    
    # Excelda yaxshi ochilishi uchun CSV parametrlarini sozlaymiz (sep=';')
    csv = df_short.to_csv(index=False, sep=';').encode('utf-8-sig') # utf-8-sig Excel uchun muhim
    
    st.sidebar.download_button(
        label="📥 Saralangan hisobotni yuklash",
        data=csv,
        file_name='omnicloud_top20_logs.csv',
        mime='text/csv',
    )
    st.sidebar.success("Faqat oxirgi 20 ta log tayyor!")

# Asosiy Dashboard metrikalari
col1, col2, col3 = st.columns(3)
cpu_ph = col1.empty()
ram_ph = col2.empty()
disk_ph = col3.empty()

st.markdown("---")
col_chart, col_log = st.columns([2, 1])

with col_chart:
    st.subheader("📈 Real vaqt grafigi")
    chart_ph = st.empty()

with col_log:
    st.subheader("📋 Oxirgi Loglar (Baza)")
    log_ph = st.empty()

# Grafik uchun tarixni saqlash
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["vaqt", "cpu", "ram"])

st.markdown("---")
st.header("📡 Tarmoq Integratsiyasi: Skaner")
col_s1, col_s2 = st.columns([1, 2])
with col_s1:
    ip_range = st.text_input("Tarmoq diapazoni:", "192.168.1.1/24")
    scan_btn = st.button("Skanerlashni boshlash")
with col_s2:
    if scan_btn:
        with st.spinner("Qidirilmoqda..."):
            try:
                found = scan_network(ip_range)
                if found:
                    st.table(pd.DataFrame(found))
                else:
                    st.warning("Hech narsa topilmadi.")
            except Exception as e:
                st.error(f"Xato: {e}. Dasturni ADMIN sifatida oching!")

# --- 5. ASOSIY ISHLASH TSIKLI ---
while True:
    # 1. Ma'lumotni olish
    m = get_system_metrics()
    
    # 2. Bazaga saqlash
    save_to_db(m['cpu'], m['ram'], m['disk'], m['sent'], m['recv'])
    
    # 3. Metrikalarni ekranda yangilash
    cpu_ph.metric("CPU Yuklamasi", f"{m['cpu']}%")
    ram_ph.metric("RAM (Xotira)", f"{m['ram']}%")
    disk_ph.metric("Disk Bandligi", f"{m['disk']}%")
    
    # 4. Grafikni yangilash
    new_data = pd.DataFrame([{"vaqt": m['vaqt'], "cpu": m['cpu'], "ram": m['ram']}])
    st.session_state.history = pd.concat([st.session_state.history, new_data], ignore_index=True).tail(15)
    chart_ph.line_chart(st.session_state.history.set_index("vaqt"))
    
    # 5. Bazadan oxirgi 5 ta yozuvni chiqarish
    db_logs = pd.read_sql_query("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 5", conn)
    log_ph.dataframe(db_logs)
    
    # Kutish
    time.sleep(update_interval)
