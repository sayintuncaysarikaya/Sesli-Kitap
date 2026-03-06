import streamlit as st
from pypdf import PdfReader
import edge_tts
import asyncio
import random
import re

# Sayfa Ayarları
st.set_page_config(page_title="Pro Ders Asistanı", page_icon="🎙️", layout="wide")

# PROFESYONEL SES LİSTESİ
VOICES = {
    "Ahmet (Doğal/Erkek)": "tr-TR-AhmetNeural",
    "Emel (Yumuşak/Kadın)": "tr-TR-EmelNeural",
    "Google (Net/Erkek)": "tr-TR-Standard-B", # Alternatif tonlar için
    "Seda (Akıcı/Kadın)": "tr-TR-Standard-A"
}

# KARAKTER ONARICI
def temizle(text):
    if not text: return ""
    harita = {'ý': 'ı', 'þ': 'ş', 'ð': 'ğ', 'Ý': 'İ', 'Þ': 'Ş', 'Ð': 'Ğ'}
    for h, d in harita.items():
        text = text.replace(h, d)
    return re.sub(r'\s+', ' ', text).strip()

# GELİŞMİŞ SES ÜRETİCİ
async def generate_voice(text, voice_code, rate):
    # Rate formatı: +10% veya -10% şeklinde olmalı
    speed = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text[:8000], voice_code, rate=speed)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- ARAYÜZ ---
st.title("🎙️ Profesyonel Sesli Ders Asistanı")

# Yan Panel: Ses Ayarları
st.sidebar.header("🎚️ Ses Özelleştirme")
secilen_ses = st.sidebar.selectbox("Ses Sanatçısı Seçin", list(VOICES.keys()))
okuma_hizi = st.sidebar.slider("Okuma Hızı", -50, 50, 0)

# PDF YÜKLEME
file = st.file_uploader("Notlarınızı Yükleyin (PDF)", type=["pdf"])

if file:
    with st.spinner("Metin işleniyor..."):
        reader = PdfReader(file)
        raw = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        st.session_state.text = temizle(raw)

if "text" in st.session_state:
    st.text_area("İşlenen Metin (Düzenlenebilir):", value=st.session_state.text, height=200)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔊 Profesyonel Seslendir", use_container_width=True):
            if st.session_state.text:
                with st.spinner("Yapay zeka sesi hazırlanıyor..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio = loop.run_until_complete(
                        generate_voice(st.session_state.text, VOICES[secilen_ses], okuma_hizi)
                    )
                    st.audio(audio)
            else: st.error("Lütfen önce bir PDF yükleyin.")

    with col2:
        if st.button("📝 Akıllı Özet", use_container_width=True):
            sentences = [s.strip() for s in st.session_state.text.split('.') if len(s) > 10]
            st.info("📌 **Özet Notlar:**\n\n" + ". \n\n• ".join(sentences[:6]) + ".")

    with col3:
        if st.button("❓ Soru Tahmini", use_container_width=True):
            st.subheader("✍️ Muhtemel Sınav Soruları")
            sentences = [s.strip() for s in st.session_state.text.split('.') if len(s) > 30]
            for _ in range(4):
                st.write(f"👉 {random.choice(sentences)[:90]}... konusunu nasıl açıklarsınız?")
                st.divider()
