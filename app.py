import streamlit as st
from pypdf import PdfReader
import edge_tts
import asyncio
import random
import re

# Sayfa Ayarları
st.set_page_config(page_title="Pro Ders Asistanı", page_icon="🎙️", layout="wide")

# GÜNCEL SES LİSTESİ (Seda ve Can düzeltildi)
VOICES = {
    "Ahmet (Doğal/Erkek)": "tr-TR-AhmetNeural",
    "Emel (Yumuşak/Kadın)": "tr-TR-EmelNeural",
    "Seda (Akıcı/Kadın)": "tr-TR-SedaNeural",
    "Can (Net/Erkek)": "tr-TR-CanNeural"
}

# KARAKTER ONARICI
def temizle(text):
    if not text: return ""
    harita = {'ý': 'ı', 'þ': 'ş', 'ð': 'ğ', 'Ý': 'İ', 'Þ': 'Ş', 'Ð': 'Ğ'}
    for h, d in harita.items():
        text = text.replace(h, d)
    return re.sub(r'\s+', ' ', text).strip()

# SES ÜRETİCİ FONKSİYON
async def generate_voice(text, voice_code, rate):
    speed = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text[:8000], voice_code, rate=speed)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- ARAYÜZ ---
st.title("🎙️ Profesyonel Sesli Ders Asistanı")

# Session State Hazırlığı
if "text" not in st.session_state:
    st.session_state.text = ""

# 1. DOSYA YÜKLEME
file = st.file_uploader("PDF Notlarınızı Buraya Yükleyin", type=["pdf"])

if file:
    with st.spinner("Metin PDF'den ayıklanıyor..."):
        reader = PdfReader(file)
        raw = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        st.session_state.text = temizle(raw)

# 2. METİN ALANI (Düzenlenebilir)
st.session_state.text = st.text_area(
    "Ders Metni:", 
    value=st.session_state.text, 
    height=250
)

# 3. SES AYARLARI (Mobilde kolay erişim için ana ekranda)
st.markdown("### 🎚️ Ses ve Hız Ayarları")
c_alt1, c_alt2 = st.columns(2)
with c_alt1:
    secilen_ses = st.selectbox("Ses Sanatçısı Seçin", list(VOICES.keys()))
with c_alt2:
    okuma_hizi = st.slider("Okuma Hızı", -50, 50, 0)

st.markdown("---")

# 4. İŞLEM BUTONLARI
col1, col2, col3 = st.columns(3)

