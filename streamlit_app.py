import streamlit as st
from PIL import Image
import pytesseract

st.title("Prueba de Lectura OCR Directa")

uploaded_file = st.file_uploader("Sube la foto de tu factura", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Foto cargada", use_column_width=True)
    
    # Extraer texto crudo sin filtros para ver qué lee el celular
    texto_crudo = pytesseract.image_to_string(image)
    
    st.subheader("Texto crudo leído por OCR:")
    st.text(texto_crudo)
