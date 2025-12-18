import sys
import os
import warnings

# --- PEREDAM SUARA (SUPPRESS WARNINGS) ---
warnings.filterwarnings("ignore") 
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

# FIX EMOJI (Force UTF-8)
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

import ollama
import google.generativeai as genai
from duckduckgo_search import DDGS
from datetime import datetime
import edge_tts
import pygame
import asyncio
import time
import re
from AppOpener import open as buka_aplikasi
import speech_recognition as sr 
import pywhatkit 

# ==============================================================================
# KONFIGURASI
# ==============================================================================
BOT_NAME = "My Bro"
VOICE_ID = "id-ID-ArdiNeural" 
GEMINI_API_KEY = "AIzaSyCWyO74CF5M5ReVClEn_OvzEAV_fdo_20o" 

# Setup Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model_gemini = genai.GenerativeModel('gemini-2.5-flash')
    USE_GEMINI = True
except:
    print("Warning: Gemini Error.")
    USE_GEMINI = False

DAFTAR_KONTAK = {
    "wahyu": "+6283133006690",
    "budi": "+6281234567890"
}


SYSTEM_PROMPT_LOCAL = """
Kamu adalah asisten AI bernama My Bro.
Gunakan Bahasa Indonesia gaul (lo-gue, bro, siap).
Jawab singkat dan padat.
"""

# ==============================================================================
# FUNGSI BANTUAN (HELPER)
# ==============================================================================
def cetak_aman(teks):
    """Fungsi print anti-crash emoji"""
    try:
        print(teks)
    except UnicodeEncodeError:
        # Hapus karakter emoji jika terminal menolak
        print(teks.encode('ascii', 'ignore').decode('ascii'))

# ==============================================================================
# FUNGSI AUDIO & INPUT
# ==============================================================================
recognizer = sr.Recognizer()
try: pygame.mixer.init()
except: pass

def dengarkan_suara():
    with sr.Microphone() as source:
        cetak_aman(f"\n🎤 {BOT_NAME} mendengarkan... (Ngomong aja bro!)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            cetak_aman("⏳ Memproses...")
            teks = recognizer.recognize_google(audio, language="id-ID")
            cetak_aman(f"🗣️ Kamu bilang: '{teks}'")
            return teks
        except:
            cetak_aman("❌ Gak kedengeran/Timeout")
            return ""

async def generate_suara(teks, nama_file="suara_bot.mp3"):
    communicate = edge_tts.Communicate(teks, VOICE_ID)
    await communicate.save(nama_file)

def ngomong(teks):
    try:
        asyncio.run(generate_suara(teks))
        pygame.mixer.music.load("suara_bot.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
        try: os.remove("suara_bot.mp3")
        except: pass
    except: pass

def ngomong_background(nama_file):
    try:
        pygame.mixer.music.load(nama_file)
        pygame.mixer.music.play()
    except: pass

# ==============================================================================
# LOGIKA UTAMA (WA & SEARCH)
# ==============================================================================

def clean_search_query(original_query):
    triggers = ["cari", "browsing", "googling", "search", "info", "siapa", "apa itu", "dimana", "tolong", "bro"]
    time_wasters = ["sekarang", "saat ini", "hari ini", "terbaru"]
    clean_q = original_query.lower()
    for word in triggers + time_wasters:
        clean_q = clean_q.replace(word, "")
    return clean_q.strip()

def search_web(query):
    cetak_aman(f"\n[Sistem] 🌐 Browsing DuckDuckGo: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='id-id', safesearch='off', max_results=3))
        if not results: return ""
        knowledge = ""
        for i, res in enumerate(results):
            knowledge += f"- {res['title']}: {res['body']}\n"
        return knowledge
    except Exception as e:
        print(f"Error Browsing: {e}")
        return ""

def tanya_gemini(query_user, context_data):
    cetak_aman(f"[Sistem] 🧠 Mengirim data ke Gemini AI...")
    tanggal_ini = datetime.now().strftime("%d %B %Y")
    prompt = f"""
    Kamu adalah 'My Bro'. HARI INI ADALAH: {tanggal_ini}.
    Pertanyaan User: {query_user}
    Data Fakta: {context_data}
    Instruksi: Jawab berdasarkan fakta di atas. Jika data lama, gunakan logika waktu sekarang. Jawab santai.
    """
    try:
        response = model_gemini.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error Gemini: {e}"

def tanya_ollama(query_user, history):
    cetak_aman(f"[Sistem] 🦙 Chatting sama Ollama (Lokal)...")
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT_LOCAL}]
    messages.extend(history)
    messages.append({'role': 'user', 'content': query_user})
    try:
        response = ollama.chat(model='llama3', messages=messages)
        return response['message']['content']
    except Exception as e:
        return "Llama error bro."

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def chat_loop():
    cetak_aman(f"--- {BOT_NAME} HYBRID VERSION Siap ---")
    
    chat_history = []

    while True:
        print("\n[Ketik / Tekan Enter utk Bicara]")
        try:
            user_input = input("Kamu: ")
        except KeyboardInterrupt:
            break

        if user_input.strip() == "":
            cetak_aman(f"{BOT_NAME}: Oke, gw dengerin...") 
            ngomong_background("aset_cue.mp3")
            user_input = dengarkan_suara()
            if user_input == "": continue 
        
        if user_input.lower() in ['keluar', 'exit', 'bye', 'cabut']:
            ngomong("Oke, cabut dulu bro. Sehat selalu!")
            break

        clean_input = user_input.lower()
        command_executed = False 

        # --- FITUR 1: KIRIM WA (LOGIKA BARU - GAYA BEBAS) ---
        if "kirim wa" in clean_input or "kirim pesan" in clean_input:
            try:
                target_raw = ""
                isi_pesan = ""
                
                # Cek apakah ada kata "ke"
                if " ke " in clean_input:
                    # Ambil semua teks setelah "ke"
                    # Contoh: "wahyu nanti malam futsal"
                    sisa_kalimat = clean_input.split(" ke ", 1)[1].strip()
                    
                    # Pecah jadi kata-kata: ["wahyu", "nanti", "malam", "futsal"]
                    kata_kata = sisa_kalimat.split()
                    
                    if len(kata_kata) > 0:
                        # Kata pertama pasti NAMA
                        target_raw = kata_kata[0] # "wahyu"
                        
                        # Sisanya adalah PESAN
                        if len(kata_kata) > 1:
                            # Cek dulu, apakah kata kedua itu "pesan"?
                            # Misal: "ke wahyu pesan nanti malam..." -> Buang kata 'pesan' biar gak dobel
                            mulai_pesan = 1
                            if kata_kata[1] == "pesan":
                                mulai_pesan = 2
                            
                            isi_pesan = " ".join(kata_kata[mulai_pesan:])
                        else:
                            # Kalau cuma "Kirim wa ke wahyu" (Gak ada pesan)
                            ngomong(f"Mau kirim pesan apa ke {target_raw}?")
                            continue

                if target_raw and isi_pesan:
                    nomor_tujuan = ""
                    # Cek Kontak
                    if target_raw in DAFTAR_KONTAK:
                        nomor_tujuan = DAFTAR_KONTAK[target_raw]
                    elif target_raw.replace(" ", "").isdigit():
                        nomor_tujuan = target_raw
                        if nomor_tujuan.startswith("0"): nomor_tujuan = "+62" + nomor_tujuan[1:]
                    
                    if nomor_tujuan:
                        ngomong(f"Oke, kirim ke {target_raw}. Jangan gerakin mouse yah.")
                        cetak_aman(f"[WA] Ke: {target_raw} | Isi: {isi_pesan}")
                        pywhatkit.sendwhatmsg_instantly(nomor_tujuan, isi_pesan, 10, tab_close=True)
                        ngomong("Terkirim.")
                        command_executed = True
                    else:
                        ngomong(f"Kontak {target_raw} gak ketemu bro.")
                else:
                    ngomong("Formatnya: Kirim WA ke [Nama] [Pesan]")
                    
            except Exception as e:
                print(f"Error WA: {e}")
            
            if command_executed: continue

        # --- FITUR 2: BUKA APLIKASI ---
        elif "buka" in clean_input:
            kata_kunci = ["buka ", "jalankan "]
            for kata in kata_kunci:
                if kata in clean_input:
                    nama_app = clean_input.split(kata)[1].strip()
                    try:
                        buka_aplikasi(nama_app, match_closest=True, throw_error=True)
                        ngomong(f"Membuka {nama_app}")
                        command_executed = True
                    except: pass
                    break
            if command_executed: continue

        # --- FITUR 3: CEK WAKTU, HARI, TANGGAL (UPDATE LENGKAP) ---
        elif any(w in clean_input for w in ["jam", "pukul", "waktu", "tanggal", "hari", "kapan"]):
            now = datetime.now()
            
            # Kamus Hari & Bulan (Biar ngomongnya 'Senin', bukan 'Monday')
            kamus_hari = {
                'Sunday': 'Minggu', 'Monday': 'Senin', 'Tuesday': 'Selasa', 
                'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu'
            }
            kamus_bulan = {
                1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
                7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
            }

            # Logika 1: User tanya JAM ("Jam berapa?", "Pukul berapa?")
            if any(w in clean_input for w in ["jam", "pukul", "waktu"]):
                jam = now.strftime("%H")
                menit = now.strftime("%M")
                ngomong(f"Sekarang jam {jam} lewat {menit} menit bro.")
            
            # Logika 2: User tanya HARI/TANGGAL ("Hari apa?", "Tanggal berapa?")
            else:
                hari_inggris = now.strftime("%A") # Dapat 'Monday'
                hari_indo = kamus_hari.get(hari_inggris, hari_inggris) # Ubah ke 'Senin'
                bulan_indo = kamus_bulan[now.month] # Ubah '12' ke 'Desember'
                
                ngomong(f"Hari ini {hari_indo}, tanggal {now.day} {bulan_indo} {now.year}.")
            
            continue

        # --- FITUR 4: HYBRID AI ---
        trigger_search = ["cari", "browsing", "siapa", "apa itu", "dimana", "berita", "info", "presiden"]
        is_search_mode = any(word in clean_input for word in trigger_search)

        final_answer = ""
        if is_search_mode and USE_GEMINI:
            query_search = clean_search_query(clean_input)
            data_internet = search_web(query_search)
            if data_internet:
                cetak_aman(f"[DEBUG] Data Internet: {len(data_internet)} chars.")
                final_answer = tanya_gemini(user_input, data_internet)
            else:
                final_answer = tanya_gemini(user_input, "Data internet kosong.")
        else:
            final_answer = tanya_ollama(user_input, chat_history)

        cetak_aman(f"{BOT_NAME}: {final_answer}")
        ngomong(final_answer)

        chat_history.append({'role': 'user', 'content': user_input})
        chat_history.append({'role': 'assistant', 'content': final_answer})
        if len(chat_history) > 10: chat_history = chat_history[-10:]

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # SETUP AWAL (BIAR GAK ERROR AUDIO)
    print("⚙️ Menyiapkan aset...")
    asyncio.run(generate_suara("Oke, gw dengerin", "aset_cue.mp3"))

    sapaan = "My Bro di sini, ada yang bisa dibantu?"
    print(f"{BOT_NAME}: {sapaan}")
    ngomong(sapaan)
    
    chat_loop()