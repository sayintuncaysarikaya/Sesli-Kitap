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

# --- 4. İŞLEM BUTONLARI (Düzeltilmiş Bölüm) ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔊 Profesyonel Seslendir", use_container_width=True):
        if st.session_state.text:
            with st.spinner(f"{secilen_ses} hazırlanıyor..."):
                try:
                    # Seslendirme motorunu çalıştıran gizli bölüm
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio_raw = loop.run_until_complete(
                        generate_voice(st.session_state.text, VOICES[secilen_ses], okuma_hizi)
                    )
                    st.audio(audio_raw)
                except Exception as e:
                    st.error(f"Ses hatası: {e}")
        else:
            st.warning("Önce metin yükleyin!")

with col2:
    if st.button("📝 Akıllı Özet", use_container_width=True):
        if st.session_state.text:
            # Metni cümlelere ayırıp ilk birkaçını özet olarak sunar
            ozet_cumleler = [s.strip() for s in st.session_state.text.split('.') if len(s) > 10]
            st.info("📌 **Özet Notlar:**\n\n• " + ". \n\n• ".join(ozet_cumleler[:5]) + ".")
        else:
            st.warning("Özetlenecek içerik yok!")

with col3:
    if st.button("❓ Soru Üret", use_container_width=True):
        if st.session_state.text:
            st.subheader("✍️ Çalışma Soruları")
            soru_cumleleri = [s.strip() for s in st.session_state.text.split('.') if len(s) > 30]
            if soru_cumleleri:
                for _ in range(min(3, len(soru_cumleleri))):
                    secilen = random.choice(soru_cumleleri)
                    st.write(f"👉 **{secilen[:80]}...** konusunu açıklar mısın?")
                    st.divider()
        else:
            st.warning("Soru üretilecek veri yok!")
