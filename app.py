import streamlit as st
from pypdf import PdfReader
import edge_tts
import asyncio
import random
import re

# Sayfa Ayarları 🎙️
st.set_page_config(page_title="Pro Ders Asistanı", page_icon="🎙️", layout="wide")

# SADECE EN STABİL SESLER 🎤
VOICES = {
    "Ahmet (Doğal/Erkek)": "tr-TR-AhmetNeural",
    "Emel (Yumuşak/Kadın)": "tr-TR-EmelNeural"
}

# KARAKTER ONARICI 🛠️
def temizle(text):
    if not text: return ""
    # PDF'lerdeki bozuk Türkçe karakterleri düzeltir
    harita = {'ý': 'ı', 'þ': 'ş', 'ð': 'ğ', 'Ý': 'İ', 'Þ': 'Ş', 'Ð': 'Ğ'}
    for h, d in harita.items():
        text = text.replace(h, d)
    return re.sub(r'\s+', ' ', text).strip()

# SES ÜRETİCİ FONKSİYON 🔊
async def generate_voice(text, voice_code, rate):
    speed = f"{rate:+d}%"
    # Kararlılık için metnin sadece ilk kısmını işleme alır
    communicate = edge_tts.Communicate(text[:4000], voice_code, rate=speed)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- ARAYÜZ BAŞLANGICI ---
st.title("🎙️ Profesyonel Sesli Ders Asistanı")

if "text" not in st.session_state:
    st.session_state.text = ""

# 1. DOSYA YÜKLEME 📂
file = st.file_uploader("PDF Notlarınızı Buraya Yükleyin", type=["pdf"])

if file:
    with st.spinner("Metin PDF'den ayıklanıyor..."):
        try:
            reader = PdfReader(file)
            raw_text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
            st.session_state.text = temizle(raw_text)
        except Exception as e:
            st.error(f"PDF okuma hatası: {e}")

# 2. METİN ALANI ✍️
st.session_state.text = st.text_area(
    "Ders Metni (Düzenleyebilirsiniz):", 
    value=st.session_state.text, 
    height=250
)

# 3. SES VE HIZ AYARLARI 🎚️
st.markdown("### 🎚️ Ses ve Hız Ayarları")
c_alt1, c_alt2 = st.columns(2)
with c_alt1:
    secilen_ses = st.selectbox("Ses Sanatçısı Seçin", list(VOICES.keys()))
with c_alt2:
    okuma_hizi = st.slider("Okuma Hızı", -50, 50, 0)

st.markdown("---")

# 4. İŞLEM BUTONLARI 🚀
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔊 Profesyonel Seslendir", use_container_width=True):
        if st.session_state.text:
            with st.spinner(f"{secilen_ses} hazırlanıyor..."):
                try:
                    # Asenkron işlemi güvenli bir şekilde çalıştırıyoruz
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio_raw = loop.run_until_complete(
                        generate_voice(st.session_state.text, VOICES[secilen_ses], okuma_hizi)
                    )
                    if audio_raw:
                        st.audio(audio_raw)
                    else:
                        st.error("Ses verisi alınamadı.")
                except Exception as e:
                    st.error(f"Seslendirme şu an yapılamıyor: {e}")
        else:
            st.warning("Lütfen önce bir metin girin.")

with col2:
    if st.button("📝 Akıllı Özet", use_container_width=True):
        if st.session_state.text:
            # Metni cümlelere ayırıp ilk 5 anlamlı cümleyi seçer
            sentences = [s.strip() for s in st.session_state.text.split('.') if len(s) > 15]
            if sentences:
                st.info("📌 **Özet Notlar:**\n\n• " + ". \n\n• ".join(sentences[:5]) + ".")
            else:
                st.warning("Özetlenecek yeterli uzunlukta metin bulunamadı.")
        else:
            st.warning("Özetlenecek içerik yok!")

with col3:
    if st.button("❓ Soru Üret", use_container_width=True):
        if st.session_state.text:
            st.subheader("✍️ Çalışma Soruları")
            # Uzun cümlelerden rastgele 3 soru üretir
            soru_adaylari = [s.strip() for s in st.session_state.text.split('.') if len(s) > 40]
            if soru_adaylari:
                secilenler = random.sample(soru_adaylari, min(3, len(soru_adaylari)))
                for s in secilenler:
                    st.write(f"👉 **{s[:90]}...** konusunu açıklayınız.")
                    st.divider()
            else:
                st.warning("Soru üretmek için metin çok kısa veya uygun değil.")
        else:
            st.warning("Soru üretilecek veri yok!")
