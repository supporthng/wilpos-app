import os
import re
import io
import json
import base64
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field

import streamlit as st
import pandas as pd
from PIL import Image

# Importaciones condicionales para manejo robusto de dependencias
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ==========================================
# 1. CONFIGURACIÓN INICIAL Y ESTADO GLOBAL
# ==========================================

st.set_page_config(
    page_title="WilPOS Móvil | Procesador de Facturas",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULTS = {
    "modo_oscuro": True,
    "inventario_acumulado": [],
    "firmas_facturas_procesadas": [],
    "ia_llamadas_principales": 0,
    "ia_llamadas_rescate": 0,
    "registro_errores": [],
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "config_margenes": {"ganancia_minima_pct": 25.0, "itbis_defecto_pct": 18.0},
    "plantillas_proveedores": {}
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==========================================
# 2. MOTOR DE TEMAS Y ESTILOS CSS ADAPTATIVOS
# ==========================================

def aplicar_tema_visual(modo_oscuro: bool):
    if modo_oscuro:
        bg_main = "#07111f"
        bg_card = "#111d33"
        bg_sidebar = "#0b1628"
        text_primary = "#f8fafc"
        text_secondary = "#94a3b8"
        border_color = "#1e293b"
        accent_color = "#2563eb"
    else:
        bg_main = "#f8fafc"
        bg_card = "#ffffff"
        bg_sidebar = "#f1f5f9"
        text_primary = "#0f172a"
        text_secondary = "#475569"
        border_color = "#e2e8f0"
        accent_color = "#3b82f6"

    css = f"""
    <style>
        .stApp {{
            background-color: {bg_main};
            color: {text_primary};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        section[data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            border-right: 1px solid {border_color};
        }}
        .wp-card {{
            background-color: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .wp-metric-title {{
            font-size: 0.85rem;
            color: {text_secondary};
            text-transform: uppercase;
            font-weight: 600;
        }}
        .wp-metric-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: {text_primary};
        }}
        .stButton>button {{
            background-color: {accent_color};
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            width: 100%;
        }}
        @media (max-width: 768px) {{
            .wp-card {{ padding: 12px; }}
            .wp-metric-value {{ font-size: 1.3rem; }}
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ==========================================
# 3. NORMALIZACIÓN Y MATEMÁTICAS DE UNIDADES
# ==========================================

@dataclass
class LineaFactura:
    codigo_barras: str
    descripcion: str
    cantidad: float
    precio_unitario: float
    itbis_monto: float
    subtotal: float
    total: float
    empaque_unidades: int = 1
    costo_unitario_neto: float = 0.0
    precio_sugerido_venta: float = 0.0

def _inferir_empaque_universal(descripcion: str, uom: str = "") -> int:
    """Infiere el factor de empaque/caja a partir de patrones en la descripción."""
    desc_upper = f"{descripcion} {uom}".upper()
    
    # Patrones comunes: 12X750ML, CAJA 24 UNID, CJA 12, PACK 6
    patron_caja = re.search(r'(\d+)\s*X\s*\d+|CJA\s*(\d+)|CAJA\s*(\d+)|PACK\s*(\d+)|(\d+)\s*UNID', desc_upper)
    if patron_caja:
        for g in patron_caja.groups():
            if g and g.isdigit() and int(g) > 0:
                return int(g)
    
    if "DOCENA" in desc_upper:
        return 12
    if "SIXPACK" in desc_upper or "6PACK" in desc_upper:
        return 6
        
    return 1

def _normalizar_costos_sin_itbis(linea: Dict[str, Any], pct_itbis_defecto: float = 18.0) -> LineaFactura:
    """Calcula y normaliza los costos unitarios netos y precios sugeridos."""
    cant = max(float(linea.get("cantidad", 1)), 1.0)
    precio_u = float(linea.get("precio_unitario", 0.0))
    subtotal = float(linea.get("subtotal", cant * precio_u))
    itbis = float(linea.get("itbis_monto", 0.0))
    
    # Si no viene ITBIS explícito pero la factura lo incluye en el precio
    if itbis == 0.0 and linea.get("incluye_itbis", False):
        costo_neto_total = subtotal / (1 + (pct_itbis_defecto / 100))
        itbis = subtotal - costo_neto_total
    else:
        costo_neto_total = subtotal

    empaque = _inferir_empaque_universal(linea.get("descripcion", ""), linea.get("uom", ""))
    costo_unitario_neto = (costo_neto_total / cant) / empaque
    
    # Precio sugerido aplicando margen mínimo de la tienda (30%)
    precio_sugerido = costo_unitario_neto * 1.30

    return LineaFactura(
        codigo_barras=str(linea.get("codigo_barras", "N/A")),
        descripcion=linea.get("descripcion", "Producto Desconocido"),
        cantidad=cant,
        precio_unitario=precio_u,
        itbis_monto=itbis,
        subtotal=subtotal,
        total=subtotal + itbis,
        empaque_unidades=empaque,
        costo_unitario_neto=round(costo_unitario_neto, 2),
        precio_sugerido_venta=round(precio_sugerido, 2)
    )

# ==========================================
# 4. MOTOR DE EXTRACCIÓN (PDF / OCR / VISION)
# ==========================================

def _ocr_multilectura(imagen: Image.Image) -> str:
    """Ejecuta OCR sobre la imagen evaluando múltiples ángulos si tesseract está activo."""
    if not pytesseract:
        return ""
    
    texto_extraido = ""
    for angulo in [0, 90, 270]:
        img_rot = imagen.rotate(angulo, expand=True) if angulo != 0 else imagen
        txt = pytesseract.image_to_string(img_rot, config="--psm 6")
        if len(txt.strip()) > len(texto_extraido.strip()):
            texto_extraido = txt
            
    return texto_extraido

def _extraer_factura_con_vision_api(imagen_bytes: bytes, api_key: str) -> Dict[str, Any]:
    """Analiza la factura usando OpenAI Vision API para estructurar JSON preciso."""
    if not OpenAI or not api_key:
        raise ValueError("OpenAI SDK no instalado o API Key no configurada.")
    
    client = OpenAI(api_key=api_key)
    base64_image = base64.b64encode(imagen_bytes).decode('utf-8')
    
    prompt = """
    Analiza esta factura/cotización comercial y devuelve un objeto JSON estructurado con el siguiente formato exacto:
    {
      "proveedor": "Nombre de la empresa",
      "rnc_proveedor": "RNC/NCF",
      "ncf": "Numero de comprobante fiscal",
      "fecha": "YYYY-MM-DD",
      "lineas": [
        {
          "codigo_barras": "UPC/EAN o N/A",
          "descripcion": "Nombre detallado del producto",
          "cantidad": 1.0,
          "uom": "CJ/UN/UND",
          "precio_unitario": 0.0,
          "subtotal": 0.0,
          "itbis_monto": 0.0
        }
      ]
    }
    Responde ÚNICAMENTE con el bloque JSON.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=1500,
    )
    
    st.session_state["ia_llamadas_principales"] += 1
    return json.loads(response.choices[0].message.content)

def procesar_archivo_factura(file_upload, metodo: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Punto de entrada universal para procesar PDFs e Imágenes."""
    try:
        bytes_data = file_upload.getvalue()
        
        if metodo == "OpenAI Vision (IA)":
            # Si es PDF, convertir primera página a imagen
            if file_upload.name.lower().endswith(".pdf"):
                if fitz:
                    doc = fitz.open(stream=bytes_data, filetype="pdf")
                    page = doc.load_page(0)
                    pix = page.get_pixmap()
                    bytes_data = pix.tobytes("png")
                else:
                    return None, "PyMuPDF (fitz) requerido para procesar PDF con Vision."
            
            res = _extraer_factura_con_vision_api(bytes_data, st.session_state["openai_api_key"])
            return res, "Éxito con OpenAI Vision API"

        elif metodo == "OCR Tesseract":
            img = Image.open(io.BytesIO(bytes_data))
            texto = _ocr_multilectura(img)
            return {"texto_raw": texto, "proveedor": "Extraído por OCR", "lineas": []}, "OCR Completado"

        else: # Extracción de Texto PDF Estándar
            texto_pdf = ""
            if pdfplumber and file_upload.name.lower().endswith(".pdf"):
                with pdfplumber.open(io.BytesIO(bytes_data)) as pdf:
                    for p in pdf.pages:
                        texto_pdf += p.extract_text() or ""
            return {"texto_raw": texto_pdf, "proveedor": "Lectura PDF", "lineas": []}, "PDF procesado"

    except Exception as e:
        st.session_state["registro_errores"].append(str(e))
        return None, f"Error en procesamiento: {str(e)}"

# ==========================================
# 5. INTERFAZ DE USUARIO Y NAVEGACIÓN
# ==========================================

aplicar_tema_visual(st.session_state["modo_oscuro"])

# Sidebar
with st.sidebar:
    st.title("⚙️ WilPOS Móvil")
    st.caption("v2.4 - Sistema Inteligente de Facturación")
    st.divider()
    
    st.session_state["modo_oscuro"] = st.toggle("🌙 Modo Oscuro", value=st.session_state["modo_oscuro"])
    
    st.divider()
    st.subheader("Estado del Sistema")
    st.metric("Llamadas IA (Vision)", st.session_state["ia_llamadas_principales"])
    st.metric("Facturas en Sesión", len(st.session_state["firmas_facturas_procesadas"]))
    
    if st.button("🗑️ Limpiar Sesión"):
        st.session_state["inventario_acumulado"] = []
        st.session_state["firmas_facturas_procesadas"] = []
        st.rerun()

# Pestañas Principales
tab_cargar, tab_inventario, tab_metricas, tab_config = st.tabs([
    "📥 Cargar Factura", 
    "📦 Inventario & Partidas", 
    "📊 Métricas & IA", 
    "⚙️ Configuración"
])

# --- PESTAÑA 1: CARGA DE FACTURA ---
with tab_cargar:
    st.markdown('<div class="wp-card"><h3>Procesamiento de Documentos</h3>', unsafe_allow_html=True)
    
    col_up, col_opt = st.columns([2, 1])
    
    with col_up:
        uploaded_file = st.file_uploader(
            "Arrastra o selecciona tu factura (PDF, PNG, JPG)", 
            type=["pdf", "png", "jpg", "jpeg"]
        )
        
    with col_opt:
        metodo_procesamiento = st.radio(
            "Método de Extracción",
            ["OpenAI Vision (IA)", "OCR Tesseract", "Texto PDF Directo"]
        )
        
    if uploaded_file and st.button("⚡ Procesar Factura Ahora"):
        with st.spinner("Analizando estructura de la factura y aplicando normalización..."):
            resultado, msj = procesar_archivo_factura(uploaded_file, metodo_procesamiento)
            
            if resultado:
                st.success(msj)
                
                # Procesar líneas extraídas
                lineas_raw = resultado.get("lineas", [])
                lineas_procesadas = []
                
                for l in lineas_raw:
                    linea_obj = _normalizar_costos_sin_itbis(
                        l, 
                        pct_itbis_defecto=st.session_state["config_margenes"]["itbis_defecto_pct"]
                    )
                    lineas_procesadas.append(asdict(linea_obj))
                
                if lineas_procesadas:
                    st.session_state["inventario_acumulado"].extend(lineas_procesadas)
                    st.session_state["firmas_facturas_procesadas"].append(uploaded_file.name)
                    st.subheader("Partidas Identificadas")
                    st.dataframe(pd.DataFrame(lineas_procesadas), use_container_width=True)
                else:
                    st.info("No se estructuraron líneas explícitas. Texto crudo extraído:")
                    st.text_area("Resultado Raw", resultado.get("texto_raw", JSON.dumps(resultado, indent=2)))
            else:
                st.error(msj)
                
    st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA 2: INVENTARIO & PARTIDAS ---
with tab_inventario:
    st.markdown('<div class="wp-card"><h3>Inventario Acumulado de Facturas</h3>', unsafe_allow_html=True)
    
    if st.session_state["inventario_acumulado"]:
        df_inv = pd.DataFrame(st.session_state["inventario_acumulado"])
        
        # Filtro de búsqueda
        busqueda = st.text_input("🔍 Buscar por descripción o código de barras")
        if busqueda:
            df_inv = df_inv[
                df_inv["descripcion"].str.contains(busqueda, case=False, na=False) |
                df_inv["codigo_barras"].str.contains(busqueda, case=False, na=False)
            ]
            
        st.dataframe(df_inv, use_container_width=True)
        
        # Descarga
        csv = df_inv.to_csv(index=False).encode('utf-8')
        st.download_button(
            "💾 Exportar Inventario a CSV",
            data=csv,
            file_name="inventario_wilpos_movil.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay partidas cargadas en esta sesión.")
        
    st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA 3: MÉTRICAS & LOGS ---
with tab_metricas:
    col1, col2, col3 = st.columns(3)
    
    total_invertido = sum([x["total"] for x in st.session_state["inventario_acumulado"]]) if st.session_state["inventario_acumulado"] else 0.0
    total_itbis = sum([x["itbis_monto"] for x in st.session_state["inventario_acumulado"]]) if st.session_state["inventario_acumulado"] else 0.0
    
    with col1:
        st.markdown(f'<div class="wp-card"><div class="wp-metric-title">Total Procesado</div><div class="wp-metric-value">RD$ {total_invertido:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="wp-card"><div class="wp-metric-title">Total ITBIS Computado</div><div class="wp-metric-value">RD$ {total_itbis:,.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="wp-card"><div class="wp-metric-title">Total Ítems</div><div class="wp-metric-value">{len(st.session_state["inventario_acumulado"])}</div></div>', unsafe_allow_html=True)

    st.subheader("Registro de Errores y Calibración")
    if st.session_state["registro_errores"]:
        for err in st.session_state["registro_errores"]:
            st.error(err)
    else:
        st.success("Sin errores registrados durante esta sesión.")

# --- PESTAÑA 4: CONFIGURACIÓN ---
with tab_config:
    st.markdown('<div class="wp-card"><h3>Configuración de Integraciones y Margen</h3>', unsafe_allow_html=True)
    
    api_key_input = st.text_input("OpenAI API Key", value=st.session_state["openai_api_key"], type="password")
    if api_key_input != st.session_state["openai_api_key"]:
        st.session_state["openai_api_key"] = api_key_input
        st.success("API Key actualizada.")
        
    st.divider()
    
    itbis_def = st.number_input(
        "ITBIS Defecto (%)", 
        value=st.session_state["config_margenes"]["itbis_defecto_pct"],
        min_value=0.0, max_value=30.0
    )
    st.session_state["config_margenes"]["itbis_defecto_pct"] = itbis_def
    
    st.markdown('</div>', unsafe_allow_html=True)
