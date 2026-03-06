import subprocess
import sys
import os

# OTOMATİK KÜTÜPHANE YÜKLEYİCİ
# Eksik modülleri terminale gerek kalmadan kendi kurar
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from pypdf import PdfReader
except ImportError:
    install('pypdf')
    from pypdf import PdfReader

import streamlit as st
import edge_tts
import asyncio
import re
import random

# Sayfa Ayarları
st.set_page_config(page_title="AI Ders Asistanı Pro", page_icon="🎓", layout="wide")

# TÜRKÇE KARAKTER ONARICI (Görseldeki tüm hataları düzeltir)
def karakter_onari(text):
    if not text: return ""
    # Görseldeki hatalı karakter haritası (ý->ı, þ->ş vb.)
    duzeltmeler = {
        'ý': 'ı', 'þ': 'ş', 'ð': 'ğ', 
        'Ý': 'İ', 'Þ': 'Ş', 'Ð': 'Ğ',
        'º': 'ş', '¿': 'ğ', '¡': 'i'
    }
    for hatali, dogru in duzeltmeler.items():
        text = text.replace(hatali, dogru)
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# SES ÜRETİMİ
async def generate_voice(text, voice, rate):
    try:
        # Metni parçalara bölerek hata riskini azaltıyoruz
        communicate = edge_tts.Communicate(text[:5000], voice, rate=f"{rate:+d}%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_data += chunk["data"]
        return audio_data
    except: return None

# --- ARAYÜZ ---
st.title("🎓 Profesyonel Ders Asistanı")

if "metin" not in st.session_state: st.session_state.metin = ""
if "ozet" not in st.session_state: st.session_state.ozet = ""
if "soru" not in st.session_state: st.session_state.soru = []

# YAN PANEL
st.sidebar.header("🎙️ Ses Ayarları")
ses_tipi = st.sidebar.selectbox("Ses Seçin", ["Ahmet (Erkek)", "Emel (Kadın)"])
ses_kodu = "tr-TR-AhmetNeural" if "Ahmet" in ses_tipi else "tr-TR-EmelNeural"
hiz = st.sidebar.slider("Hız", -50, 50, -10)

# PDF YÜKLEME
file = st.file_uploader("PDF Yükle", type=["pdf"])
if file:
    with st.spinner("Karakterler onarılıyor..."):
        reader = PdfReader(file)
        ham_metin = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: ham_metin += t + " "
        st.session_state.metin = karakter_onari(ham_metin)

# METİN KUTUSU
input_text = st.text_area("Düzenlenmiş Metin:", value=st.session_state.metin, height=300)

st.markdown("---")

# İŞLEM BUTONLARI
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🔊 Seslendir", use_container_width=True):
        if input_text:
            with st.spinner("Okunuyor..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio = loop.run_until_complete(generate_voice(input_text, ses_kodu, hiz))
                if audio: st.audio(audio)

with c2:
    if st.button("📝 Özet Çıkar", use_container_width=True):
        if input_text:
            cumleler = [c.strip() for c in input_text.split('.') if len(c) > 15]
            st.session_state.ozet = ". ".join(cumleler[:min(6, len(cumleler))]) + "."

with c3:
    if st.button("❓ Sınav Hazırla", use_container_width=True):
        if input_text:
            cumleler = [c.strip() for c in input_text.split('.') if len(c) > 20]
            soru_listesi = []
            for c in cumleler:
                if any(k in c.lower() for k in ["nedir", "önemli", "temel", "amacı"]):
                    soru_listesi.append(f"✍️ **Soru:** {c} (Açıklayınız)")
            
            if not soru_listesi and len(cumleler) > 0:
                for _ in range(3):
                    soru_listesi.append(f"✍️ **Soru:** '{random.choice(cumleler)[:60]}...' konusunu anlatınız.")
            st.session_state.soru = list(set(soru_listesi))[:6]

# SONUÇLAR
if st.session_state.ozet:
    st.info(st.session_state.ozet)

if st.session_state.soru:
    st.subheader("📝 Deneme Sınavı")
    for s in st.session_state.soru:
        st.write(s)
        st.divider()