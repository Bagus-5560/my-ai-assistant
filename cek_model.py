import google.generativeai as genai
import os

# --- PENTING: PASTE API KEY KAMU DI SINI ---
MY_API_KEY = "AIzaSyCWyO74CF5M5ReVClEn_OvzEAV_fdo_20o" \
"" \
""

genai.configure(api_key=MY_API_KEY)

print("--- SEDANG MENGECEK MENU MODEL ---")

try:
    available_models = []
    for m in genai.list_models():
        # Cek apakah model ini bisa buat chat/text
        if 'generateContent' in m.supported_generation_methods:
            # Kita print tanpa emoji biar gak error
            print(f"[ADA] {m.name}")
            available_models.append(m.name)
            
    if not available_models:
        print("[INFO] Tidak ada model yang ditemukan. Cek API Key.")
        
except Exception as e:
    print(f"[ERROR] Terjadi masalah: {e}")