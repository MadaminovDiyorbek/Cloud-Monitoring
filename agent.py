import psutil
import time
import socket
from postgrest import SyncPostgrestClient

# 1. BU YERGA O'ZINGIZNING NUSXALANGAN MA'LUMOTLARINGIZNI QO'YING
# TO'G'RI FORMAT:
SUPABASE_URL = "https://wffcuseusugwafljvavv.supabase.co/rest/v1"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmZmN1c2V1c3Vnd2FmbGp2YXZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzI3MzMsImV4cCI6MjA5MDM0ODczM30.LhC9OE3lRBROjabQsOAQVbt4L691Bwnt13MW8UZ2-qY"

# Klientni yaratish
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
client = SyncPostgrestClient(SUPABASE_URL, headers=headers)

hostname = socket.gethostname()

def send_data():
    print(f"🚀 {hostname} qurilmasi kuzatilyapti...")
    while True:
        try:
            # Tizim ma'lumotlarini yig'ish
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            data = {
                "hostname": hostname,
                "cpu_percent": cpu,
                "ram_percent": ram,
                "disk_percent": disk
            }
            
            # Supabase'ga yuborish
            client.table("monitor_logs").insert(data).execute()
            print(f"✅ Ma'lumot yuborildi: CPU: {cpu}% | RAM: {ram}%")
            
        except Exception as e:
            print(f"❌ Xatolik yuz berdi: {e}")
            
        time.sleep(10) # Har 10 soniyada yuboradi

if __name__ == "__main__":
    send_data()