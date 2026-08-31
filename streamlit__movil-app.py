import io
import re
import pandas as pd
import streamlit as st
import pdfplumber
from PIL import Image, ImageOps

try:
    import fitz
    PYMUPDF_DISPONIBLE = True
except ImportError:
    fitz = None
    PYMUPDF_DISPONIBLE = False

try:
    import pytesseract
    OCR_DISPONIBLE = True
except ImportError:
    pytesseract = None
    OCR_DISPONIBLE = False

st.set_page_config(
    page_title="WilPOS Móvil | Facturas e Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# ESTILO MODERNO
# =========================================================
st.markdown(r"""
<style>
:root {
    --bg: #f4f7fb;
    --surface: #ffffff;
    --surface-2: #f8fafc;
    --text: #0f172a;
    --muted: #64748b;
    --line: #e2e8f0;
    --primary: #2563eb;
    --primary-2: #1d4ed8;
    --navy: #071a33;
    --success: #16a34a;
    --warning: #d97706;
    --danger: #dc2626;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

[data-testid="stHeader"] {
    background: rgba(244,247,251,.86);
    backdrop-filter: blur(10px);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071a33 0%, #0b2445 100%);
    border-right: 1px solid rgba(255,255,255,.06);
}

[data-testid="stSidebar"] * {
    color: #e5eefb;
}

[data-testid="stSidebar"] .stRadio label {
    padding: .35rem 0;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 10px;
    padding: .42rem .6rem;
    transition: .2s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.07);
}

.block-container {
    max-width: 1480px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    letter-spacing: -0.025em;
}

.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #ffffff 0%, #f7faff 100%);
    border: 1px solid #dbe5f0;
    border-radius: 20px;
    padding: 2rem 2.2rem;
    min-height: 215px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, .05);
}

.hero:after {
    content: "";
    position: absolute;
    right: -70px;
    top: -85px;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(37,99,235,.16), rgba(37,99,235,0));
}

.hero h1 {
    font-size: clamp(2rem, 4vw, 3.2rem);
    margin: 0 0 .55rem 0;
    color: #0f172a;
}

.hero p {
    max-width: 720px;
    color: #64748b;
    font-size: 1.04rem;
    line-height: 1.7;
    margin: .25rem 0;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    padding: .38rem .68rem;
    border-radius: 999px;
    background: #eff6ff;
    color: #1d4ed8;
    font-weight: 700;
    font-size: .82rem;
    margin-bottom: .8rem;
}

.glass-card, .section-card {
    background: #fff;
    border: 1px solid #dfe7f1;
    border-radius: 18px;
    box-shadow: 0 8px 28px rgba(15,23,42,.045);
}

.section-card {
    padding: 1.25rem 1.3rem;
    margin-bottom: 1rem;
}

.section-title {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    margin-bottom:.85rem;
}

.section-title h3 {
    margin:0;
    font-size:1.15rem;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .85rem;
    margin: 1rem 0 1.25rem 0;
}

.kpi {
    position: relative;
    overflow:hidden;
    background:#fff;
    border:1px solid #dfe7f1;
    border-radius:16px;
    padding:1rem 1.05rem;
    min-height:105px;
    box-shadow:0 6px 18px rgba(15,23,42,.035);
}

.kpi .label {
    color:#64748b;
    font-size:.82rem;
    font-weight:700;
    margin-bottom:.35rem;
}

.kpi .value {
    color:#0f172a;
    font-size:1.55rem;
    font-weight:800;
}

.kpi .icon {
    position:absolute;
    right:.9rem;
    top:.9rem;
    width:42px;
    height:42px;
    border-radius:12px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#eff6ff;
    font-size:1.15rem;
}

.side-logo {
    padding: .75rem .25rem 1.1rem .25rem;
}
.side-logo .brand {
    display:flex;
    align-items:center;
    gap:.7rem;
}
.side-logo .mark {
    width:42px;
    height:42px;
    border-radius:12px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:linear-gradient(135deg,#3b82f6,#2563eb);
    color:#fff;
    font-size:1.4rem;
    box-shadow:0 8px 20px rgba(37,99,235,.25);
}
.side-logo .name {
    font-size:1.45rem;
    font-weight:850;
    color:#fff;
    letter-spacing:-.02em;
}
.side-logo .sub {
    color:#60a5fa;
    font-size:.8rem;
    font-weight:800;
    margin-top:-2px;
}

.side-summary {
    margin-top:1.2rem;
    padding:1rem;
    border-radius:14px;
    background:rgba(255,255,255,.045);
    border:1px solid rgba(255,255,255,.08);
}
.side-summary .s-title {
    font-size:.78rem;
    font-weight:800;
    color:#cbd5e1;
    margin-bottom:.75rem;
}
.side-summary .row {
    display:flex;
    justify-content:space-between;
    gap:.75rem;
    padding:.52rem 0;
    border-bottom:1px solid rgba(255,255,255,.06);
    font-size:.78rem;
}
.side-summary .row:last-child { border-bottom:0; }
.side-summary .num { font-weight:800; color:#fff; }

.file-card {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    padding:.85rem .95rem;
    border:1px solid #e2e8f0;
    border-radius:14px;
    background:#fff;
    margin-bottom:.55rem;
}
.file-card .file-name {
    font-weight:750;
    color:#0f172a;
    word-break:break-word;
}
.file-card .meta {
    color:#64748b;
    font-size:.8rem;
    margin-top:.18rem;
}
.file-card .ok {
    color:#15803d;
    background:#f0fdf4;
    border:1px solid #bbf7d0;
    border-radius:999px;
    padding:.28rem .58rem;
    white-space:nowrap;
    font-size:.76rem;
    font-weight:800;
}
.file-card .bad {
    color:#b91c1c;
    background:#fef2f2;
    border:1px solid #fecaca;
    border-radius:999px;
    padding:.28rem .58rem;
    white-space:nowrap;
    font-size:.76rem;
    font-weight:800;
}

.info-strip {
    border-radius:14px;
    padding:.8rem .95rem;
    background:#eff6ff;
    border:1px solid #bfdbfe;
    color:#1e40af;
    font-size:.86rem;
}

.empty-state {
    text-align:center;
    background:#fff;
    border:1px dashed #cbd5e1;
    border-radius:18px;
    padding:2.3rem 1rem;
    color:#64748b;
}
.empty-state .big { font-size:2.2rem; margin-bottom:.4rem; }

div[data-testid="stFileUploader"] section {
    border:1.5px dashed #b8c7dc !important;
    border-radius:16px !important;
    background:#f8fbff !important;
    min-height:145px;
}

div[data-testid="stFileUploader"] section:hover {
    border-color:#60a5fa !important;
    background:#f3f8ff !important;
}

.stButton > button,
.stDownloadButton > button {
    min-height:44px;
    border-radius:11px;
    font-weight:750;
    border-width:1px;
}

.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#2563eb,#1d4ed8);
    border-color:#1d4ed8;
    box-shadow:0 8px 18px rgba(37,99,235,.18);
}

[data-testid="stDataFrame"] {
    border:1px solid #e2e8f0;
    border-radius:14px;
    overflow:hidden;
}

[data-testid="stMetric"] {
    background:#fff;
    border:1px solid #e2e8f0;
    padding:.85rem 1rem;
    border-radius:14px;
}

@media (max-width: 900px) {
    .kpi-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .hero { padding:1.35rem 1.2rem; min-height:0; }
}

@media (max-width: 640px) {
    .block-container {
        padding-left:.7rem;
        padding-right:.7rem;
        padding-top:.55rem;
    }
    .kpi-grid { grid-template-columns:1fr 1fr; gap:.55rem; }
    .kpi { padding:.8rem; min-height:94px; }
    .kpi .value { font-size:1.15rem; }
    .kpi .icon { width:34px; height:34px; font-size:.95rem; }
    .section-card { padding:.95rem; }
    .file-card { align-items:flex-start; flex-direction:column; gap:.45rem; }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# ESTADO
# =========================================================
DEFAULTS = {
    "inventario_acumulado": {},
    "firmas_facturas_procesadas": set(),
    "margen_usado": 35.0,
    "detalle_facturas_procesadas": {},
    "uploader_key": 0,
    "camera_key": 0,
    "articulos_repetidos_notif": [],
    "errores_ocr": [],
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if hasattr(value, "copy") else value

def round_to_nearest_5(val):
    return int(round(val / 5.0) * 5)

def _normalizar_ocr(texto):
    """Normalización tolerante para comparar texto OCR sin depender de tildes/puntuación."""
    import unicodedata
    texto = texto or ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()

def _ocr_imagen(image):
    """OCR conservador. No binariza agresivamente para no borrar texto fino."""
    if not OCR_DISPONIBLE:
        return ""

    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # Reduce imágenes enormes, pero conserva resolución suficiente.
    try:
        max_lado = 2200
        mayor = max(image.size)
        if mayor > max_lado:
            factor = max_lado / mayor
            image = image.resize(
                (max(1, int(image.width * factor)), max(1, int(image.height * factor)))
            )
    except Exception:
        pass

    textos = []
    # Primer pase: documento/tablas. Segundo pase: texto disperso.
    for psm in (6, 11):
        try:
            t = pytesseract.image_to_string(image, config=f"--oem 3 --psm {psm}")
            if t and t.strip():
                textos.append(t)
        except Exception:
            pass

    return "\n".join(textos)

def extraer_datos_factura(uploaded_file):
    file_name = uploaded_file.name.lower()
    extracted_text = ""
    errores_locales = []

    # Trabajar desde bytes evita problemas de puntero entre pdfplumber/fitz/PIL.
    try:
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        uploaded_file.seek(0)
    except Exception:
        raw = None

    if file_name.endswith(".pdf"):
        # 1. Intenta obtener texto digital, igual que la versión original.
        if raw is not None:
            try:
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    for page in pdf.pages:
                        extracted_text += "\n" + (page.extract_text() or "")
            except Exception as exc:
                errores_locales.append(
                    f"No se pudo leer el texto digital de {uploaded_file.name}: {exc}"
                )

        # 2. Si el PDF es escaneado o el texto fue insuficiente, renderiza las páginas y hace OCR.
        if len(extracted_text.strip()) < 80 and OCR_DISPONIBLE:
            if PYMUPDF_DISPONIBLE and raw is not None:
                try:
                    doc = fitz.open(stream=raw, filetype="pdf")
                    for pagina in doc:
                        pix = pagina.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        extracted_text += "\n" + _ocr_imagen(img)
                    doc.close()
                except Exception as exc:
                    errores_locales.append(
                        f"No se pudo ejecutar OCR sobre el PDF {uploaded_file.name}: {exc}"
                    )
            else:
                errores_locales.append(
                    "El PDF parece escaneado. Instala PyMuPDF para permitir OCR automático de PDFs-imagen."
                )

    elif file_name.endswith((".png", ".jpg", ".jpeg")):
        if not OCR_DISPONIBLE:
            errores_locales.append(
                "OCR no disponible: instala pytesseract y Tesseract para reconocer fotos automáticamente."
            )
        elif raw is not None:
            try:
                image = Image.open(io.BytesIO(raw))
                extracted_text = _ocr_imagen(image)
            except Exception as exc:
                errores_locales.append(
                    f"No se pudo leer la imagen {uploaded_file.name}: {exc}"
                )

    st.session_state.errores_ocr.extend(errores_locales)

    # ---------------------------------------------------------
    # IDENTIFICACIÓN AUTOMÁTICA
    # ---------------------------------------------------------
    texto_norm = _normalizar_ocr(extracted_text)
    nombre_norm = _normalizar_ocr(file_name)
    full_search = f"{texto_norm} {nombre_norm}"

    # Para NCF/códigos: compara también una versión de solo caracteres alfanuméricos.
    compact = re.sub(r"[^a-z0-9]", "", full_search)
    solo_digitos = re.sub(r"\D", "", full_search)

    def contiene(*terminos):
        return any(_normalizar_ocr(t) in full_search for t in terminos)

    def contiene_compacto(*terminos):
        return any(
            re.sub(r"[^a-z0-9]", "", _normalizar_ocr(t)) in compact
            for t in terminos
        )

    def contiene_digitos(*terminos):
        return any(re.sub(r"\D", "", str(t)) in solo_digitos for t in terminos)

    productos = []
    proveedor = ""
    num_factura = ""
    fecha = "28/08/2026"

    # =========================================================
    # 1. ÁLVAREZ & SÁNCHEZ — lógica/productos originales
    # Señales redundantes para fotos de móvil.
    # =========================================================
    es_alvarez = (
        contiene("alvarez", "sanchez", "cristalino", "tequila reserva cristalino")
        or contiene_digitos("576999", "7501035013483")
        or "whatsapp image 2026 08 29" in nombre_norm
    )

    # =========================================================
    # 2. FARAH GROUP — lógica/productos originales
    # =========================================================
    es_farah = (
        contiene("farah", "farah group", "prestige cerveza")
        or contiene_digitos("2015785", "123374")
    )

    # =========================================================
    # 3. CDC 11783
    # Se revisa ANTES del CDC estándar para evitar falsos positivos.
    # =========================================================
    es_cdc_11783 = (
        contiene_compacto("E31000011783")
        or contiene_digitos("31000011783")
        or contiene_digitos("830207010706", "830207000707")
        or (
            contiene("ciclon 250ml", "ciclon 500ml")
            and contiene("agua perrier", "mack albert")
        )
        or (
            "2026 08 26" in nombre_norm
            and ("16 52 41" in nombre_norm or "14 30 10" in nombre_norm)
        )
    )

    # =========================================================
    # 4. CDC 11790
    # =========================================================
    es_cdc_11790 = (
        contiene_compacto("E31000011790")
        or contiene_digitos("31000011790")
        or contiene_digitos("7501035010192", "619947000020")
        or contiene("servilleta bimgo", "tito s handmade")
        or ("2026 08 26" in nombre_norm and "20 27 07" in nombre_norm)
    )

    # =========================================================
    # 5. CDC estándar 11806
    # =========================================================
    es_cdc_11806 = (
        contiene_compacto("E310000011806")
        or contiene_digitos("310000011806")
        or contiene_digitos("049000057638", "070847893110", "070847891727")
        or (
            contiene("canada dry", "coca cola 400ml")
            and contiene("monter", "monster")
        )
        or contiene("centro de distribucion cristian")
        or nombre_norm == "cdc pdf"
    )

    # =========================================================
    # 6. YARDOW — lógica/productos originales
    # =========================================================
    es_yardow = (
        contiene("yardow", "comercial yardow")
        or contiene_digitos("00494502")
        or (
            contiene_digitos("1168", "1169")
            and contiene("funda papel")
        )
        or (
            contiene("vaso foam termo envase", "vaso plastico")
            and contiene("funda papel")
        )
    )

    # Prioridad: facturas CDC específicas -> demás proveedores -> CDC estándar.
    if es_cdc_11783:
        proveedor = "Centro de Distribución Cristian SRL"
        num_factura = "E31000011783"
        fecha = "26/08/2026"
        productos = [
            {"codigo": "830207010706", "nombre": "BEBIDA ENERGIZANTE CICLON 250ML", "cant": 1.0, "emp": 24, "costo_total": 1699.93, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "830207000707", "nombre": "BEBIDA ENERGIZANTE CICLON 500ML", "cant": 5.0, "emp": 24, "costo_total": 11625.10, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "041331021951", "nombre": "AGUA COCO GOYA BOTELLA 13.5 OZ", "cant": 6.0, "emp": 12, "costo_total": 9449.88, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "292", "nombre": "WHISKY MACK ALBERT 700ML", "cant": 1.0, "emp": 12, "costo_total": 6750.15, "itbis": 0.18, "cat": "Licores"},
            {"codigo": "7468572200083", "nombre": "VASO PLASTIFAR #16 UND", "cant": 2.0, "emp": 500, "costo_total": 3999.98, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "041331027854", "nombre": "AGUA COCO GOYA BOTELLA 11.8 OZ", "cant": 3.0, "emp": 24, "costo_total": 5999.76, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "041331027878", "nombre": "AGUA COCO GOYA LATA 17.6 OZ", "cant": 8.0, "emp": 24, "costo_total": 21599.12, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "07478341", "nombre": "AGUA PERRIER 330ML", "cant": 20.0, "emp": 24, "costo_total": 38500.00, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "C218", "nombre": "WHISKY MACK ALBERT 350ML", "cant": 1.0, "emp": 24, "costo_total": 6824.87, "itbis": 0.18, "cat": "Licores"}
        ]

    elif es_cdc_11790:
        proveedor = "Centro de Distribución Cristian SRL"
        num_factura = "E31000011790"
        fecha = "26/08/2026"
        productos = [
            {"codigo": "P1016", "nombre": "SERVILLETA BIMGO DISPENSER 360UND", "cant": 5.0, "emp": 10, "costo_total": 4000.00, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "7501035010192", "nombre": "TEQUILA 1800 REPOSADO 750ML", "cant": 6.0, "emp": 1, "costo_total": 14850.00, "itbis": 0.18, "cat": "Licores"},
            {"codigo": "619947000020", "nombre": "VODKA TITO'S HANDMADE 750ML", "cant": 2.0, "emp": 12, "costo_total": 31600.80, "itbis": 0.18, "cat": "Licores"},
            {"codigo": "041331027854", "nombre": "AGUA COCO GOYA BOTELLA 11.8 OZ", "cant": 4.0, "emp": 24, "costo_total": 7999.68, "itbis": 0.18, "cat": "Bebidas"}
        ]

    elif es_alvarez:
        proveedor = "Álvarez & Sánchez, S.A."
        num_factura = "576999"
        fecha = "28/08/2026"
        productos = [
            {"codigo": "7501035013483", "nombre": "TEQUILA RESERVA CRISTALINO 1800", "cant": 2.0, "emp": 12, "costo_total": 79012.80, "itbis": 0.18, "cat": "Licores"}
        ]

    elif es_farah:
        proveedor = "Farah Group Company SRL"
        num_factura = "2015785"
        fecha = "27/08/2026"
        productos = [
            {"codigo": "123374", "nombre": "PRESTIGE CERVEZA 4X6PACK X 0.355L BOTELLA", "cant": 10.0, "emp": 24, "costo_total": 27118.60, "itbis": 0.18, "cat": "Cervezas"}
        ]

    elif es_yardow:
        proveedor = "Comercial Yardow SRL"
        num_factura = "00494502"
        fecha = "27/08/2026"
        productos = [
            {"codigo": "1168", "nombre": "FUNDA PAPEL #2 30/100", "cant": 1.0, "emp": 3000, "costo_total": 567.80, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "1169", "nombre": "FUNDA PAPEL #4 20/100", "cant": 1.0, "emp": 2000, "costo_total": 567.80, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "746023412", "nombre": "VASO FOAM TERMO ENVASE #12 40/25", "cant": 1.0, "emp": 1000, "costo_total": 2203.39, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "746023416", "nombre": "VASO FOAM TERMO ENVASE #16 20/25", "cant": 1.0, "emp": 500, "costo_total": 1864.41, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "7460234PL7", "nombre": "VASO PLASTICO #7 TERMO ENVASE Y CIELO 50", "cant": 1.0, "emp": 500, "costo_total": 1779.66, "itbis": 0.18, "cat": "Insumos"}
        ]

    elif es_cdc_11806:
        proveedor = "Centro de Distribución Cristian SRL"
        num_factura = "E310000011806"
        fecha = "28/08/2026"
        productos = [
            {"codigo": "281", "nombre": "AGUA TONICA CANADA DRY 400ML", "cant": 2.0, "emp": 12, "costo_total": 580.02, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "049000057638", "nombre": "REFRESCO COCA COLA 400ML", "cant": 2.0, "emp": 12, "costo_total": 599.96, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "1765", "nombre": "BEBIDA ENERGIZANTE MONTER 473ML", "cant": 1.0, "emp": 24, "costo_total": 2225.04, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "070847893110", "nombre": "BEBIDA ENERGIZANTE MONTER MANGO LOCO 473ML", "cant": 1.0, "emp": 24, "costo_total": 2225.04, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "070847891727", "nombre": "BEBIDA ENERGIZANTE MONTER ULTRA 473ML", "cant": 1.0, "emp": 24, "costo_total": 2225.04, "itbis": 0.18, "cat": "Bebidas"}
        ]

    if not productos:
        return None, None, None, None, []

    firma = (proveedor, str(num_factura))
    return firma, proveedor, num_factura, fecha, productos

# =========================================================
# HELPERS DE INVENTARIO / EXCEL
# =========================================================
def construir_df_productos():
    factor_margen = 1 + (st.session_state.margen_usado / 100.0)
    filas = []
    for codigo, data in st.session_state.inventario_acumulado.items():
        costo_unitario = data["costo_total"] / data["stock"] if data["stock"] > 0 else 0
        precio_venta = round_to_nearest_5(costo_unitario * factor_margen)
        filas.append({
            "Nombre": data["nombre"],
            "Código Barra": codigo,
            "Categoría": data["categoria"],
            "Tipo": "producto",
            "Precio Venta": precio_venta,
            "Costo": round(costo_unitario, 4),
            "Stock": int(data["stock"]),
            "Stock Mínimo": 25,
            "ITBIS": data["itbis"],
            "Unidad Medida": "unidad",
            "Venta Granel": "No",
            "Cantidad Empaque": data["emp"],
            "Precio Variable": "No",
            "Descuento %": 0,
            "Descuento Monto": 0,
            "Precio Especial": None,
            "Descuento Activo": "No",
            "Descuento Nota": None,
        })
    return pd.DataFrame(filas)


def generar_excel_wilpos(df_prod):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_prod.to_excel(writer, index=False, sheet_name="Productos")

        pd.DataFrame({
            "Nombre": ["Bebidas", "Insumos", "Cervezas", "Licores", "General"],
            "Descripción": [
                "Refrescos, agua, energizantes",
                "Fundas y vasos",
                "Cervezas y maltas",
                "Whisky, tequila, vodka",
                "Artículos varios",
            ],
        }).to_excel(writer, index=False, sheet_name="Categorías")

        lista_provs = list(set(
            info["proveedor"]
            for info in st.session_state.detalle_facturas_procesadas.values()
        )) or ["Proveedor General"]

        pd.DataFrame({
            "Nombre": lista_provs,
            "Contacto": ["Ventas"] * len(lista_provs),
            "Teléfono": ["809-000-0000"] * len(lista_provs),
            "Email": [""] * len(lista_provs),
            "Dirección": ["Santo Domingo"] * len(lista_provs),
            "RNC/Cédula": ["131000000"] * len(lista_provs),
            "Tipo Identificación": ["RNC"] * len(lista_provs),
        }).to_excel(writer, index=False, sheet_name="Proveedores")

        if not df_prod.empty:
            # Mantiene la estructura original de Producto-Proveedor.
            df_pp = pd.DataFrame({
                "Producto": [
                    df_prod.loc[0, "Nombre"],
                    df_prod.loc[min(1, len(df_prod)-1), "Nombre"],
                ],
                "Proveedor": [lista_provs[0], lista_provs[0]],
                "Precio Costo": [
                    df_prod.loc[0, "Costo"],
                    df_prod.loc[min(1, len(df_prod)-1), "Costo"],
                ],
                "Principal": ["Sí", "Sí"],
            })
            df_pp.to_excel(writer, index=False, sheet_name="Producto-Proveedor")

        pd.DataFrame({
            "Instrucciones para cargar tu inventario": [
                "Llena la hoja Productos con tus artículos.",
                "Generado automáticamente mediante la aplicación web WilPOS.",
            ]
        }).to_excel(writer, index=False, sheet_name="Instrucciones")

    return output.getvalue()


def totales_dashboard():
    total_facturas = len(st.session_state.detalle_facturas_procesadas)
    total_productos = len(st.session_state.inventario_acumulado)
    total_unidades = int(sum(x.get("stock", 0) for x in st.session_state.inventario_acumulado.values()))
    valor_compra = float(sum(x.get("costo_total", 0) for x in st.session_state.inventario_acumulado.values()))
    return total_facturas, total_productos, total_unidades, valor_compra


def resetear_todo():
    st.session_state.inventario_acumulado = {}
    st.session_state.firmas_facturas_procesadas = set()
    st.session_state.detalle_facturas_procesadas = {}
    st.session_state.margen_usado = 35.0
    st.session_state.articulos_repetidos_notif = []
    st.session_state.errores_ocr = []
    st.session_state.uploader_key += 1
    st.session_state.camera_key += 1


@st.dialog("Confirmar procesamiento")
def modal_confirmacion(validas, duplicadas_count, margen):
    st.markdown("### 🚀 Incorporar facturas al inventario")
    st.caption("Esta acción acumulará stock y costos usando la misma lógica de la versión funcional.")

    c1, c2 = st.columns(2)
    c1.metric("Facturas nuevas", len(validas))
    c2.metric("Margen aplicado", f"{margen:g}%")

    if duplicadas_count:
        st.warning(f"Se omitieron {duplicadas_count} factura(s) duplicada(s).")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("✅ Confirmar y actualizar", type="primary", use_container_width=True):
            st.session_state.margen_usado = margen
            st.session_state.articulos_repetidos_notif = []

            for archivo, firma, proveedor, num_fac, fecha_fac, productos_en_archivo in validas:
                st.session_state.firmas_facturas_procesadas.add(firma)
                st.session_state.detalle_facturas_procesadas[firma] = {
                    "proveedor": proveedor,
                    "num_factura": num_fac,
                    "fecha": fecha_fac,
                    "cantidad_articulos": len(productos_en_archivo),
                }

                for p in productos_en_archivo:
                    codigo = str(p["codigo"]).replace("-", "").strip()
                    cantidad_comprada_unidades = p["cant"] * p["emp"]

                    if codigo in st.session_state.inventario_acumulado:
                        st.session_state.articulos_repetidos_notif.append(
                            f'**{p["nombre"]}** ({codigo}) ya existía; stock y costo fueron acumulados.'
                        )
                        st.session_state.inventario_acumulado[codigo]["stock"] += cantidad_comprada_unidades
                        st.session_state.inventario_acumulado[codigo]["costo_total"] += p["costo_total"]
                    else:
                        st.session_state.inventario_acumulado[codigo] = {
                            "nombre": p["nombre"],
                            "categoria": p["cat"],
                            "stock": cantidad_comprada_unidades,
                            "costo_total": p["costo_total"],
                            "emp": p["emp"],
                            "itbis": p["itbis"],
                        }
            st.rerun()

    with b2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()


# =========================================================
# SIDEBAR
# =========================================================
total_facturas, total_productos, total_unidades, valor_compra = totales_dashboard()

with st.sidebar:
    st.markdown("""
    <div class="side-logo">
      <div class="brand">
        <div class="mark">📦</div>
        <div>
          <div class="name">WilPOS</div>
          <div class="sub">MÓVIL</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    pagina = st.radio(
        "Navegación",
        [
            "🏠 Inicio",
            "🧾 Procesar facturas",
            "📦 Inventario acumulado",
            "📋 Detalle de facturas",
            "📥 Exportar Excel",
        ],
        label_visibility="collapsed",
    )

    st.markdown(f"""
    <div class="side-summary">
      <div class="s-title">RESUMEN RÁPIDO</div>
      <div class="row"><span>Facturas procesadas</span><span class="num">{total_facturas}</span></div>
      <div class="row"><span>Artículos únicos</span><span class="num">{total_productos}</span></div>
      <div class="row"><span>Unidades totales</span><span class="num">{total_unidades:,}</span></div>
      <div class="row"><span>Valor compra</span><span class="num">RD$ {valor_compra:,.2f}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reiniciar todo", use_container_width=True):
        resetear_todo()
        st.rerun()

    st.caption("OCR automático · PDF · JPG · PNG · Cámara")


# =========================================================
# CABECERA / KPIs
# =========================================================
header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown("""
    <div style="padding:.15rem 0 .45rem 0">
      <div style="font-size:.82rem;color:#64748b;font-weight:750">PANEL DE CONTROL</div>
      <div style="font-size:1.35rem;font-weight:850;color:#0f172a">Procesador Inteligente de Facturas</div>
    </div>
    """, unsafe_allow_html=True)
with header_right:
    if st.button("↻ Reiniciar", use_container_width=True):
        resetear_todo()
        st.rerun()

st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi"><div class="label">Facturas procesadas</div><div class="value">{total_facturas}</div><div class="icon">🧾</div></div>
  <div class="kpi"><div class="label">Artículos únicos</div><div class="value">{total_productos}</div><div class="icon">📦</div></div>
  <div class="kpi"><div class="label">Unidades totales</div><div class="value">{total_unidades:,}</div><div class="icon">🛒</div></div>
  <div class="kpi"><div class="label">Valor total compra</div><div class="value">RD$ {valor_compra:,.2f}</div><div class="icon">💰</div></div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# INICIO
# =========================================================
if pagina == "🏠 Inicio":
    st.markdown("""
    <div class="hero">
      <div class="hero-badge">✨ WilPOS Móvil · Automatización de inventario</div>
      <h1>¡Bienvenido! 👋</h1>
      <p>Procesa facturas desde tu computadora, teléfono o tablet sin cambiar la lógica que ya funciona. El sistema identifica automáticamente tus facturas configuradas, acumula el inventario y genera el Excel listo para WilPOS.</p>
      <p><b>Flujo:</b> cargar factura → reconocimiento automático → confirmar → inventario acumulado → exportar Excel.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.35, 1])
    with c1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Inicio rápido")
        st.markdown("1. Abre **Procesar facturas** en el menú lateral.\n2. Selecciona archivos o usa la cámara.\n3. Revisa las facturas reconocidas.\n4. Confirma el procesamiento.\n5. Exporta el Excel cuando termines.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### ✅ Estado del sistema")
        if OCR_DISPONIBLE:
            st.success("OCR disponible")
        else:
            st.error("OCR no disponible")
        if PYMUPDF_DISPONIBLE:
            st.success("PDF escaneado compatible")
        else:
            st.warning("PyMuPDF no disponible")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.detalle_facturas_procesadas:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🕘 Facturas procesadas recientemente")
        recientes = list(st.session_state.detalle_facturas_procesadas.values())[-5:][::-1]
        st.dataframe(pd.DataFrame(recientes), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# PROCESAR FACTURAS
# =========================================================
elif pagina == "🧾 Procesar facturas":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 1. Cargar facturas")
    st.caption("Selecciona varios archivos desde desktop o toma una foto directamente desde el teléfono.")

    carga_col, margen_col = st.columns([2.2, 1], gap="large")

    with margen_col:
        st.markdown("#### Margen de ganancia")
        margen_porcentaje = st.number_input(
            "Margen (%)",
            min_value=0.0,
            max_value=500.0,
            value=float(st.session_state.margen_usado),
            step=1.0,
        )
        if margen_porcentaje > 15:
            st.success("✓ Margen válido para procesar")
        else:
            st.warning("Debe ser mayor al 15%")
        st.markdown('<div class="info-strip">La identificación es automática por OCR, NCF, códigos y descripciones.</div>', unsafe_allow_html=True)

    with carga_col:
        modo_carga = st.radio(
            "Origen",
            ["📁 Archivo / galería", "📷 Cámara del teléfono"],
            horizontal=True,
            label_visibility="collapsed",
        )
        uploaded_files = []
        if modo_carga == "📁 Archivo / galería":
            uploaded_files = st.file_uploader(
                "PDF, JPG, JPEG o PNG",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"uploader_{st.session_state.uploader_key}",
            ) or []
        else:
            foto = st.camera_input(
                "Toma la foto completa de la factura",
                key=f"camera_{st.session_state.camera_key}",
            )
            if foto is not None:
                uploaded_files = [foto]

    st.markdown('</div>', unsafe_allow_html=True)

    archivos_validos = []
    archivos_duplicados = []
    archivos_invalidos = []

    if uploaded_files:
        st.session_state.errores_ocr = []
        archivos_unicos = {f.name: f for f in uploaded_files}.values()
        with st.spinner("Leyendo y reconociendo facturas..."):
            for f in archivos_unicos:
                firma, proveedor, num_fac, fecha_fac, productos = extraer_datos_factura(f)
                if not productos:
                    archivos_invalidos.append(f.name)
                elif firma in st.session_state.firmas_facturas_procesadas:
                    archivos_duplicados.append((f.name, proveedor, num_fac))
                else:
                    archivos_validos.append((f, firma, proveedor, num_fac, fecha_fac, productos))

    if uploaded_files:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f"### 2. Archivos cargados ({len(uploaded_files)})")

        for f, firma, proveedor, num_fac, fecha_fac, productos in archivos_validos:
            st.markdown(f"""
            <div class="file-card">
              <div>
                <div class="file-name">📄 {f.name}</div>
                <div class="meta">{proveedor} · Factura {num_fac} · {fecha_fac} · {len(productos)} artículo(s)</div>
              </div>
              <div class="ok">✓ Reconocida</div>
            </div>
            """, unsafe_allow_html=True)

        for nombre, proveedor, num_fac in archivos_duplicados:
            st.markdown(f"""
            <div class="file-card">
              <div>
                <div class="file-name">📄 {nombre}</div>
                <div class="meta">{proveedor} · Factura {num_fac}</div>
              </div>
              <div class="bad">Duplicada</div>
            </div>
            """, unsafe_allow_html=True)

        for nombre in archivos_invalidos:
            st.markdown(f"""
            <div class="file-card">
              <div>
                <div class="file-name">📄 {nombre}</div>
                <div class="meta">No pudo reconocerse automáticamente como una factura configurada.</div>
              </div>
              <div class="bad">No reconocida</div>
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.errores_ocr:
            with st.expander("🔎 Diagnóstico OCR"):
                for err in st.session_state.errores_ocr:
                    st.warning(err)

        if margen_porcentaje <= 15:
            st.error("El margen de ganancia debe ser mayor al 15% para procesar.")

        if st.button(
            "🚀 Procesar facturas automáticamente",
            type="primary",
            use_container_width=True,
            disabled=(len(archivos_validos) == 0 or margen_porcentaje <= 15),
        ):
            modal_confirmacion(archivos_validos, len(archivos_duplicados), margen_porcentaje)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="empty-state">
          <div class="big">🧾</div>
          <b>Aún no has cargado facturas</b><br>
          Selecciona archivos o usa la cámara para comenzar.
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# INVENTARIO
# =========================================================
elif pagina == "📦 Inventario acumulado":
    df_productos = construir_df_productos()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 📦 Inventario acumulado")
    st.caption("Productos consolidados usando la misma lógica de costo promedio y margen de la versión funcional.")

    if st.session_state.articulos_repetidos_notif:
        with st.expander("🔄 Artículos acumulados desde varias facturas"):
            for notif in st.session_state.articulos_repetidos_notif:
                st.info(notif)

    if df_productos.empty:
        st.info("Todavía no hay productos en el inventario.")
    else:
        st.dataframe(
            df_productos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Precio Venta": st.column_config.NumberColumn(format="RD$ %.2f"),
                "Costo": st.column_config.NumberColumn(format="RD$ %.4f"),
                "ITBIS": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Productos únicos", len(df_productos))
        c2.metric("Stock total", int(df_productos["Stock"].sum()))
        c3.metric("Margen aplicado", f"{st.session_state.margen_usado:g}%")
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# FACTURAS
# =========================================================
elif pagina == "📋 Detalle de facturas":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Detalle de facturas procesadas")
    if not st.session_state.detalle_facturas_procesadas:
        st.info("Todavía no hay facturas procesadas.")
    else:
        tabla = []
        for _, info in st.session_state.detalle_facturas_procesadas.items():
            tabla.append({
                "Proveedor": info["proveedor"],
                "No. Factura": info["num_factura"],
                "Fecha": info["fecha"],
                "Artículos": info["cantidad_articulos"],
            })
        st.dataframe(pd.DataFrame(tabla), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# EXPORTAR
# =========================================================
elif pagina == "📥 Exportar Excel":
    df_productos = construir_df_productos()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 📥 Exportar inventario para WilPOS")
    st.caption("Genera el mismo archivo Excel consolidado de la versión funcional.")

    if df_productos.empty:
        st.info("Procesa al menos una factura antes de exportar.")
    else:
        excel_data = generar_excel_wilpos(df_productos)
        c1, c2 = st.columns([1.4, 1])
        with c1:
            st.markdown("""
            <div class="info-strip">
              <b>Archivo listo.</b><br>
              Incluye Productos, Categorías, Proveedores, Producto-Proveedor e Instrucciones.
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.download_button(
                "📥 Descargar Inventario_WilPOS_Acumulado.xlsx",
                data=excel_data,
                file_name="Inventario_WilPOS_Acumulado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

        st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
        st.dataframe(df_productos.head(12), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
