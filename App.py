import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from io import BytesIO
import re

# Eğer Windows'ta test edeceksen şu satırı aç:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="Şirket Kimlik Okuyucu", page_icon="🪪", layout="centered")

st.title("🪪 Şirket Kimlik Kartı Okuyucu (OCR)")
st.markdown("""
Bu uygulama şirket kimlik kartlarından **Ad** ve **Soyad** bilgilerini OCR (Optik Karakter Tanıma) yöntemiyle çıkarır  
ve Excel (.xlsx) formatında indirmenizi sağlar.  
Artık birden fazla kimlik tarayıp hepsini tek Excel dosyasında toplayabilirsiniz.
""")

# Session state başlat
if "veriler" not in st.session_state:
    st.session_state.veriler = []

# Görsel alma seçeneği
secim = st.radio("📷 Görseli nasıl almak istersin?", ["Kamera", "Dosya yükle"])

if secim == "Kamera":
    img_input = st.camera_input("Kameradan kimlik fotoğrafını çek")
else:
    img_input = st.file_uploader("Kimlik fotoğrafını yükle", type=["jpg", "jpeg", "png"])

if img_input is not None:
    # Görseli oku
    image = Image.open(img_input).convert("RGB")
    img_np = np.array(image)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Görüntü işleme (gri ton + filtre + threshold)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR işlemi
    with st.spinner("Kimlik üzerindeki metin okunuyor..."):
        text = pytesseract.image_to_string(th, lang="tur+eng", config="--oem 3 --psm 6")

    st.subheader("📄 Okunan Metin:")
    st.text(text)

    # Ad / Soyad bilgisi bulma
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    candidate_lines = [l for l in lines if re.match(r"^[A-ZÇĞİÖŞÜ\s]+$", l)]

    ad, soyad = "", ""
    if len(candidate_lines) >= 1:
        parts = candidate_lines[0].split()
        if len(parts) >= 2:
            ad = parts[0].capitalize()
            soyad = parts[-1].capitalize()
        elif len(parts) == 1:
            ad = parts[0].capitalize()
    if len(candidate_lines) >= 2 and not soyad:
        soyad = candidate_lines[1].split()[-1].capitalize()

    # Yeni veriyi session'a ekle
    kayit = {"Ad": ad, "Soyad": soyad}
    st.session_state.veriler.append(kayit)

    st.success(f"✅ {ad} {soyad} eklendi!")

# Tüm kayıtları göster
if len(st.session_state.veriler) > 0:
    st.subheader("📋 Tüm Kayıtlar")
    df = pd.DataFrame(st.session_state.veriler)
    st.dataframe(df)

    # Excel oluştur
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        label="⬇️ Excel olarak indir",
        data=output,
        file_name="sirket_kimlik_listesi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Silme seçeneği
    if st.button("🧹 Tüm Verileri Temizle"):
        st.session_state.veriler = []
        st.rerun()
else:
    st.info("Henüz kimlik eklenmedi. Kamera veya dosya ile bir kimlik yükleyin.")
