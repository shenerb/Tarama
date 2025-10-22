import streamlit as st
import easyocr
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from io import BytesIO
import re

st.set_page_config(page_title="Şirket Kimlik Okuyucu", page_icon="🪪", layout="centered")

st.title("🪪 Kimlik Kartı Okuyucu (EasyOCR Editable)")
st.markdown("""
Bu uygulama EasyOCR kullanarak kimlik kartlarından **Ad** ve **Soyad** bilgilerini çıkarır.  
OCR başarısız olursa kullanıcı tabloyu manuel olarak düzenleyebilir ve Excel olarak indirebilir.
""")

# --- EasyOCR modeli ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['tr', 'en'], gpu=False)
reader = load_ocr()

# --- Session State ---
if "veriler" not in st.session_state:
    st.session_state.veriler = pd.DataFrame(columns=["Ad", "Soyad"])

# --- Görsel Alma ---
secim = st.radio("📷 Görseli nasıl almak istersin?", ["Kamera", "Dosya yükle"])

img_input = None
if secim == "Kamera":
    img_input = st.camera_input("Kameradan kimlik fotoğrafını çek")
else:
    img_input = st.file_uploader("Kimlik fotoğrafını yükle", type=["jpg", "jpeg", "png"])

if img_input is not None:
    try:
        # --- Dosya güvenli şekilde oku ---
        image = Image.open(img_input).convert("RGB")
        img_np = np.array(image)

        # --- Büyük fotoğrafları küçült ---
        max_dim = 1024
        h, w = img_np.shape[:2]
        scale = max_dim / max(h, w)
        if scale < 1:
            img_np = cv2.resize(img_np, (int(w*scale), int(h*scale)))

        # --- Görüntü işleme ---
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        gray = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )

        # --- OCR ---
        with st.spinner("Kimlik üzerindeki metin okunuyor..."):
            results = reader.readtext(gray)

        full_text = "\n".join([res[1] for res in results])
        st.subheader("📄 Okunan Metin:")
        st.text(full_text)

        # --- Ad/Soyad çıkarma ---
        ad, soyad = "", ""
        lines = [res[1].strip() for res in results if len(res[1].strip()) > 0]
        uppercase_lines = [l for l in lines if re.match(r"^[A-ZÇĞİÖŞÜ\s]{3,}$", l)]

        if len(uppercase_lines) > 0:
            parts = uppercase_lines[0].split()
            if len(parts) >= 2:
                ad, soyad = parts[0].capitalize(), parts[-1].capitalize()
            elif len(parts) == 1:
                ad = parts[0].capitalize()
        if len(uppercase_lines) >= 2 and not soyad:
            soyad = uppercase_lines[1].split()[-1].capitalize()

        # --- Yeni satırı session'a ekle ---
        yeni_satir = pd.DataFrame({"Ad": [ad], "Soyad": [soyad]})
        st.session_state.veriler = pd.concat([st.session_state.veriler, yeni_satir], ignore_index=True)

        st.success(f"✅ {ad} {soyad} eklendi!")

    except Exception as e:
        st.error(f"Dosya okunamadı veya işlenemedi: {e}")

# --- Editable Tablo ---
if not st.session_state.veriler.empty:
    st.subheader("📋 Tüm Kayıtlar (Düzenlenebilir)")
    edited_df = st.data_editor(
        st.session_state.veriler,
        num_rows="dynamic",
        use_container_width=True
    )
    st.session_state.veriler = edited_df

    # --- Excel İndir ---
    output = BytesIO()
    st.session_state.veriler.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        label="⬇️ Excel olarak indir",
        data=output,
        file_name="sirket_kimlik_listesi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("🧹 Tüm Verileri Temizle"):
        st.session_state.veriler = pd.DataFrame(columns=["Ad", "Soyad"])
        st.rerun()
else:
    st.info("Henüz kimlik eklenmedi. Kamera veya dosya ile bir kimlik yükleyin.")
