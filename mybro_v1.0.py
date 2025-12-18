import sys
# FIX EMOJI (Biar di terminal gak error simbol aneh)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

import ollama
from duckduckgo_search import DDGS
from datetime import datetime
import edge_tts
import pygame
import asyncio
import os
import time
import re  # PENTING: Buat deteksi WA Gaya 2
from AppOpener import open as buka_aplikasi
import speech_recognition as sr 
import pywhatkit 

# --- KONFIGURASI UTAMA ---
BOT_NAME = "My Bro"
VOICE_ID = "id-ID-ArdiNeural" 

# --- BUKU TELEPON DIGITAL ---
# Format: "nama_panggilan": "nomor_wa"
DAFTAR_KONTAK = {
    "wahyu": "+6283133006690",
    "budi": "+6281234567890" # Contoh
}

SYSTEM_PROMPT = """
Kamu adalah asisten AI bernama My Bro.
Kepribadian: Asik, laki banget, dan penurut.
TUGAS:
1. Jika user menyuruh membuka aplikasi, konfirmasi.
2. Jawab pertanyaan user dengan singkat (Bahasa Indonesia gaul).
3. Jika user suruh kirim WA, konfirmasi nama tujuannya.
"""

# --- SETUP AUDIO ---
recognizer = sr.Recognizer()
try:
    pygame.mixer.init()
except:
    pass

# --- FUNGSI DENGAR ---
def dengarkan_suara():
    with sr.Microphone() as source:
        print(f"\n🎤 {BOT_NAME} mendengarkan... (Ngomong aja bro!)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("⏳ Memproses...")
            teks = recognizer.recognize_google(audio, language="id-ID")
            print(f"🗣️ Kamu bilang: '{teks}'")
            return teks
        except:
            print("❌ Gak kedengeran/Timeout")
            return ""

# --- FUNGSI SUARA AI ---
async def generate_suara(teks):
    communicate = edge_tts.Communicate(teks, VOICE_ID)
    await communicate.save("suara_bot.mp3")

def ngomong(teks):
    """Fungsi Suara Cowok"""
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

# --- FUNGSI INTERNET ---
def search_web(query):
    print(f"\n[Sistem] Browsing: '{query}'...")
    try:
        results = DDGS().text(query, max_results=2)
        if not results: return "Gak nemu info."
        knowledge = ""
        for i, res in enumerate(results):
            knowledge += f"- {res['title']}: {res['body']}\n"
        return knowledge
    except: return "Koneksi error."

# --- FUNGSI UTAMA ---
def chat_loop():
    print(f"--- {BOT_NAME} Siap ---")
    print("1. Ketik sesuatu lalu Enter -> Chat Biasa")
    print("2. Langsung Enter (Kosong) -> Pakai Suara 🎤")
    print("---------------------------------------------")
    
    chat_history = []

    while True:
        print("\n[Ketik / Tekan Enter utk Bicara]")
        try:
            user_input = input("Kamu: ")
        except KeyboardInterrupt:
            print("\nBye!")
            break

        # LOGIC ENTER: Kalau kosong, nyalain mic
        if user_input.strip() == "":
            user_input = dengarkan_suara()
            if user_input == "": continue # Kalau gak ada suara, ulang loop
        
        if user_input.lower() in ['keluar', 'exit', 'bye']:
            ngomong("Oke, cabut dulu bro.")
            break

        info_aksi = ""
        clean_input = user_input.lower()

        # --- FITUR 1: KIRIM WA (GAYA 1 & 2) ---
        if "kirim wa" in clean_input or "kirim pesan" in clean_input:
            try:
                target_raw = ""
                isi_pesan = ""

                # Logic Deteksi (Gaya 1 vs Gaya 2)
                if " pesan " in clean_input:
                    # Gaya 1: Ada kata kunci "pesan"
                    parts = clean_input.split("ke")[1].split("pesan")
                    target_raw = parts[0].strip()
                    isi_pesan = parts[1].strip()
                else:
                    # Gaya 2: Langsung (Implicit Regex)
                    # Pola: cari kata setelah 'ke' (Nama), ambil sisanya (Pesan)
                    match = re.search(r"ke\s+(\w+)\s+(.+)", clean_input)
                    if match:
                        target_raw = match.group(1) # Ambil 1 kata (Nama)
                        isi_pesan = match.group(2)  # Ambil sisanya
                    else:
                        # Fallback kalau format aneh
                        info_aksi = "(Info: Format WA gak jelas bro)"

                # Proses Pengiriman
                if target_raw:
                    nomor_tujuan = ""
                    nama_panggilan = target_raw

                    # Cek Buku Telepon
                    if target_raw in DAFTAR_KONTAK:
                        nomor_tujuan = DAFTAR_KONTAK[target_raw]
                    # Cek Input Nomor Langsung
                    elif target_raw.replace("+", "").replace(" ", "").isdigit():
                        nomor_tujuan = target_raw
                        if nomor_tujuan.startswith("0"): 
                            nomor_tujuan = "+62" + nomor_tujuan[1:]
                    
                    if nomor_tujuan:
                        info_aksi = f"(Info: Mengirim WA ke {nama_panggilan})"
                        ngomong(f"Oke, kirim ke {nama_panggilan}. Jangan gerak dulu.")
                        # Kirim WA
                        pywhatkit.sendwhatmsg_instantly(nomor_tujuan, isi_pesan, 10, tab_close=True)
                    else:
                        info_aksi = f"(Info: Gagal. Kontak '{target_raw}' gak ada di codingan)"
                        ngomong(f"Waduh, nomor si {target_raw} belum disave di kodingan bro.")

            except Exception as e:
                print(f"Error WA: {e}")

        # --- FITUR 2: BUKA APLIKASI ---
        elif "buka" in clean_input:
            kata_kunci = ["buka ", "bukain ", "jalankan "]
            for kata in kata_kunci:
                if kata in clean_input:
                    try:
                        nama_app = clean_input.split(kata)[1].strip()
                        buka_aplikasi(nama_app, match_closest=True, throw_error=True)
                        info_aksi = f"(Info: Membuka {nama_app})"
                        ngomong(f"Membuka {nama_app}")
                    except: pass
                    break

        # --- FITUR 3: INTERNET & AI ---
        jam_sekarang = datetime.now().strftime("%H:%M")
        trigger_search = ["cari", "browsing", "googling", "search", "berita", "info", "siapa", "apa itu"]
        is_online = any(word in clean_input for word in trigger_search)
        
        context_data = ""
        if is_online:
            search_result = search_web(user_input)
            context_data = f"DATA INTERNET:\n{search_result}\n"

        # Rakit Prompt
        messages = []
        messages.append({'role': 'system', 'content': SYSTEM_PROMPT + "\n" + context_data})
        messages.extend(chat_history)
        pesan_final = f"{user_input} (Info: Jam {jam_sekarang}. {info_aksi})"
        messages.append({'role': 'user', 'content': pesan_final})

        print(f"{BOT_NAME}: (Mikir...)", end="\r")
        
        try:
            response = ollama.chat(model='llama3', messages=messages)
            answer = response['message']['content']
            print(f"                                      ", end="\r") # Clear baris
            print(f"{BOT_NAME}: {answer}")
            ngomong(answer)
            
            chat_history.append({'role': 'user', 'content': user_input})
            chat_history.append({'role': 'assistant', 'content': answer})
            if len(chat_history) > 10: chat_history.pop(0); chat_history.pop(0)

        except Exception as e:
            print(f"\nError AI: {e}")

if __name__ == "__main__":
    chat_loop()