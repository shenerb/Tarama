import streamlit as st
import easyocr
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from io import BytesIO
import re

st.set_page_config(page_title="Şirket Kimlik Okuyucu", page_icon="🪪", layout="centered")

st.title("🪪 Şirket Kimlik Kartı Okuyucu (EasyOCR)")
st.markdown("""
Bu uygulama, **EasyOCR** kullanarak şirket kimlik kartlarından **Ad** ve **Soyad** bilgilerini çıkarır  
ve Excel (.xlsx) olarak indirmenizi sağlar.  
Artık birden fazla kimlik tarayıp hepsini tek Excel dosyasında toplayabilirsiniz.
""")

# --- EasyOCR modeli başlat ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['tr', 'en'], gpu=False)
reader = load_ocr()

# --- Session State ---
if "veriler" not in st.session_state:
    st.session_state.veriler = []

# --- Görsel Alma ---
secim = st.radio("📷 Görseli nasıl almak istersin?", ["Kamera", "Dosya yükle"])

if secim == "Kamera":
    img_input = st.camera_input("Kameradan kimlik fotoğrafını çek")
else:
    img_input = st.file_uploader("Kimlik fotoğrafını yükle", type=["jpg", "jpeg", "png"])

if img_input is not None:
    image = Image.open(img_input).convert("RGB")
    img_np = np.array(image)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # --- Görüntü İşleme (ön hazırlık) ---
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    gray = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
    )

    st.spinner("Kimlik üzerindeki metin okunuyor...")
    results = reader.readtext(gray)
    st.subheader("📄 Okunan Metin:")

    full_text = "\n".join([res[1] for res in results])
    st.text(full_text)

    # --- Ad / Soyad çıkarma ---
    ad, soyad = "", ""
    lines = [res[1].strip() for res in results if len(res[1].strip()) > 0]

    # Büyük harflerle yazılmış olabilecek ad soyad satırlarını yakala
    uppercase_lines = [l for l in lines if re.match(r"^[A-ZÇĞİÖŞÜ\s]{3,}$", l)]

    if len(uppercase_lines) > 0:
        parts = uppercase_lines[0].split()
        if len(parts) >= 2:
            ad, soyad = parts[0].capitalize(), parts[-1].capitalize()
        elif len(parts) == 1:
            ad = parts[0].capitalize()

    if len(uppercase_lines) >= 2 and not soyad:
        soyad = uppercase_lines[1].split()[-1].capitalize()

    kayit = {"Ad": ad, "Soyad": soyad}
    st.session_state.veriler.append(kayit)

    st.success(f"✅ {ad} {soyad} eklendi!")

# --- Kayıt Tablosu ---
if len(st.session_state.veriler) > 0:
    st.subheader("📋 Tüm Kayıtlar")
    df = pd.DataFrame(st.session_state.veriler)
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        label="⬇️ Excel olarak indir",
        data=output,
        file_name="sirket_kimlik_listesi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("🧹 Tüm Verileri Temizle"):
        st.session_state.veriler = []
        st.rerun()
else:
    st.info("Henüz kimlik eklenmedi. Kamera veya dosya ile bir kimlik yükleyin.")
