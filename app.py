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
    "Seda (Akıcı/Kadın)": "tr-TR-Standard-A",
    "Can (Net/Erkek)": "tr-TR-Standard-B"
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
    speed = f"{rate:+d}%"
    # Sunucuyu yormamak için ilk 8000 karakteri alır
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

# Session State Hazırlığı (Metnin silinmemesi için)
if "text" not in st.session_state:
    st.session_state.text = ""

# PDF'den metin çıkarma işlemi
if file:
    with st.spinner("Metin PDF'den ayıklanıyor..."):
        reader = PdfReader(file)
        raw = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        st.session_state.text = temizle(raw)

# METİN YAZMA/DÜZENLEME KUTUCUĞU (Her zaman görünür)
st.session_state.text = st.text_area(
    "Ders Metni (Buraya yazabilir veya PDF yükleyebilirsiniz):", 
    value=st.session_state.text, 
    height=300
)

st.markdown("---")

# İŞLEM BUTONLARI
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔊 Profesyonel Seslendir", use_container_width=True):
        if st.session_state.text:
            with st.spinner("Yapay zeka sesi hazırlanıyor..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio = loop.run_until_complete(
                        generate_voice(st.session_state.text, VOICES[secilen_ses], okuma_hizi)
                    )
                    st.audio(audio)
                except Exception as e:
                    st.error(f"Ses oluşturulamadı: {e}")
        else:
            st.warning("Seslendirecek metin bulunamadı!")

with col2:
    if st.button("📝 Akıllı Özet", use_container_width=True):
        if st.session_state.text:
            sentences = [s.strip() for s in st.session_state.text.split('.') if len(s) > 10]
            st.info("📌 **Özet Notlar:**\n\n• " + ". \n\n• ".join(sentences[:6]) + ".")
        else:
            st.warning("Özetlenecek metin yok!")

with col3:
    if st.button("❓ Soru Tahmini", use_container_width=True):
        if st.session_state.text:
            st.subheader("✍️ Muhtemel Sınav Soruları")
            sentences = [s.strip() for s in st.session_state.text.split('.') if len(s) > 30]
            if sentences:
                for _ in range(min(4, len(sentences))):
                    soru_temeli = random.choice(sentences)
                    st.write(f"👉 {soru_temeli[:90]}... konusunu nasıl açıklarsınız?")
                    st.divider()
        else:
            st.warning("Soru üretilecek metin yok!")
