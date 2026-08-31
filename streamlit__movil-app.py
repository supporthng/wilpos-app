import io
import re
import hashlib
import unicodedata
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import pytesseract
    OCR_DISPONIBLE = True
except Exception:
    pytesseract = None
    OCR_DISPONIBLE = False

try:
    import cv2
    CV2_DISPONIBLE = True
except Exception:
    cv2 = None
    CV2_DISPONIBLE = False

try:
    import fitz  # PyMuPDF
    FITZ_DISPONIBLE = True
except Exception:
    fitz = None
    FITZ_DISPONIBLE = False

try:
    import pdfplumber
    PDFPLUMBER_DISPONIBLE = True
except Exception:
    pdfplumber = None
    PDFPLUMBER_DISPONIBLE = False


# =========================================================
# CONFIGURACIÓN
# =========================================================
st.set_page_config(
    page_title="Procesador de Facturas WilPOS V2",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1200px; padding-top: .8rem; padding-bottom: 3rem;}
      .main-header {
        background: linear-gradient(135deg, #1F4E78 0%, #2E75B6 100%);
        padding: 1.4rem; border-radius: 14px; color: white; margin-bottom: .8rem;
      }
      .main-header h1 {color:white !important; margin:0; font-size:clamp(1.55rem,5vw,2.25rem);}
      .main-header p {color:#EAF3F8; margin:.45rem 0 0; font-size:clamp(.92rem,3vw,1.05rem);}
      .stButton > button, .stDownloadButton > button {min-height:46px; border-radius:10px; font-weight:600;}
      div[data-testid="stFileUploader"] {border-radius:12px;}
      @media (max-width: 640px) {
        .block-container {padding-left:.7rem; padding-right:.7rem;}
        .main-header {padding:1rem;}
        div[data-testid="stHorizontalBlock"] {gap:.45rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# ESTADO
# =========================================================
DEFAULTS = {
    "inventario_acumulado": {},
    "firmas_facturas_procesadas": set(),
    "hashes_archivos_procesados": set(),
    "detalle_facturas_procesadas": {},
    "margen_usado": 35.0,
    "uploader_key": 0,
    "camera_key": 0,
    "avisos_acumulacion": [],
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if hasattr(value, "copy") else value


# =========================================================
# NORMALIZACIÓN
# =========================================================
def sin_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(texto or ""))
        if not unicodedata.combining(c)
    )


def limpiar_espacios(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def normalizar_linea(texto: str) -> str:
    texto = str(texto or "").replace("|", " ")
    texto = texto.replace("—", "-").replace("–", "-")
    return limpiar_espacios(texto)


def lineas_limpias(texto: str) -> list[str]:
    return [normalizar_linea(x) for x in str(texto or "").splitlines() if normalizar_linea(x)]


def normalizar_codigo(codigo) -> str:
    codigo = str(codigo or "").strip()
    codigo = codigo.replace(" ", "").replace("-", "")
    return re.sub(r"[^A-Za-z0-9]", "", codigo)


def numero_decimal(valor, default=0.0) -> float:
    if valor is None:
        return default
    if isinstance(valor, (int, float, np.number)) and not pd.isna(valor):
        return float(valor)

    s = str(valor).strip()
    if not s:
        return default
    s = re.sub(r"[^0-9,.-]", "", s)
    if not s:
        return default

    # Facturas locales suelen usar coma de miles y punto decimal.
    if "," in s and "." in s:
        if s.rfind(".") > s.rfind(","):
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        partes = s.split(",")
        if len(partes[-1]) == 2:
            s = "".join(partes[:-1]) + "." + partes[-1]
        else:
            s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return default


def normalizar_itbis(valor) -> float:
    n = numero_decimal(valor, 0.18)
    if n > 1:
        n /= 100.0
    return max(0.0, min(n, 1.0))


def extraer_montos(linea: str) -> list[float]:
    tokens = re.findall(r"(?<!\w)(?:RD\$\s*)?\d{1,3}(?:,\d{3})*(?:\.\d{2})|(?<!\w)\d+\.\d{2}", linea)
    return [numero_decimal(x) for x in tokens]


def round_to_nearest_5(valor: float) -> int:
    return int(round(float(valor) / 5.0) * 5)


def categoria_por_nombre(nombre: str) -> str:
    n = sin_acentos(nombre).lower()
    if any(x in n for x in ["whisky", "vodka", "tequila", "ron ", "rom ", "licor", "brandy", "cognac"]):
        return "Licores"
    if any(x in n for x in ["cerveza", "beer", "malta"]):
        return "Cervezas"
    if any(x in n for x in ["vaso", "funda", "servilleta", "envase", "plato", "cuchara", "tenedor", "foam"]):
        return "Insumos"
    if any(x in n for x in ["agua", "refresco", "coca", "energizante", "jugo", "bebida", "tonica"]):
        return "Bebidas"
    return "General"


def inferir_empaque(descripcion: str, unidad: str = "", codigo: str = "") -> int:
    d = sin_acentos(descripcion).upper()
    u = sin_acentos(unidad).upper()

    # Ej.: 4X6PACK = 24 unidades.
    m = re.search(r"\b(\d{1,3})\s*[Xx]\s*(\d{1,3})\s*(?:PACK|PK|Paq)?\b", d)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if 1 <= a <= 200 and 1 <= b <= 500:
            return a * b

    # Ej.: 30/100, 40/25, 20/25.
    m = re.search(r"\b(\d{1,4})\s*/\s*(\d{1,4})\b", d)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a <= 500 and b <= 1000:
            return a * b

    # Ej.: 12/70 CL: el 12 indica unidades del empaque, no 840.
    m = re.search(r"\b(\d{1,3})\s*/\s*(\d{1,3})\s*(?:CL|ML|L)\b", d)
    if m:
        return int(m.group(1))

    # Caja-24 / Paquete-12.
    m = re.search(r"\b(?:CAJA|PAQUETE|PAQ|PACK)\s*[-:]?\s*(\d{1,4})\b", d)
    if m:
        return int(m.group(1))

    # Algunas presentaciones Yardow no muestran el multiplicador completo.
    # Se conserva un fallback muy pequeño por código conocido; el usuario lo puede editar.
    yardow_fallback = {
        "7460234PL7": 500,
    }
    cod = normalizar_codigo(codigo).upper()
    if cod in yardow_fallback:
        return yardow_fallback[cod]

    if any(x in u for x in ["UND", "UNIDAD", "EA"]):
        return 1
    return 1


def hash_bytes(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()


# =========================================================
# OCR / EXTRACCIÓN DE TEXTO
# =========================================================
def preparar_imagen_pil(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    max_width = 2400
    if image.width > max_width:
        factor = max_width / image.width
        image = image.resize((max_width, max(1, int(image.height * factor))))
    return image


def imagen_para_ocr(image: Image.Image) -> Image.Image:
    image = preparar_imagen_pil(image)

    if CV2_DISPONIBLE:
        arr = np.array(image)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        # Mantiene texto fino de impresoras térmicas y ayuda con sombras de celular.
        thr = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 15
        )
        return Image.fromarray(thr)

    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.7)
    image = ImageEnhance.Sharpness(image).enhance(1.7)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    return image


def ejecutar_ocr(image: Image.Image) -> tuple[str, str]:
    if not OCR_DISPONIBLE:
        return "", "OCR no disponible: instala Tesseract y pytesseract."

    preparada = imagen_para_ocr(image)
    errores = []

    # PSM 6 funciona bien en tickets/tablas; PSM 4 ayuda en documentos de columnas.
    resultados = []
    for lang in ("spa", "eng"):
        for psm in (6, 4):
            try:
                txt = pytesseract.image_to_string(
                    preparada,
                    lang=lang,
                    config=f"--oem 3 --psm {psm}",
                )
                if txt and txt.strip():
                    resultados.append(txt.strip())
            except Exception as exc:
                errores.append(str(exc))

        if resultados:
            break

    if not resultados:
        return "", (errores[-1] if errores else "Tesseract no devolvió texto.")

    # El más largo suele preservar más filas/columnas.
    mejor = max(resultados, key=len)
    return mejor, ""


@st.cache_data(show_spinner=False, max_entries=40)
def extraer_texto_desde_bytes(nombre: str, contenido: bytes) -> dict:
    nombre_lower = nombre.lower()
    textos = []
    errores = []
    paginas = 0

    if nombre_lower.endswith(".pdf"):
        # Primero intenta texto digital; si una página viene vacía, OCR de esa página.
        texto_paginas = []

        if PDFPLUMBER_DISPONIBLE:
            try:
                with pdfplumber.open(io.BytesIO(contenido)) as pdf:
                    paginas = len(pdf.pages)
                    texto_paginas = [(p.extract_text() or "").strip() for p in pdf.pages]
            except Exception as exc:
                errores.append(f"Lectura PDF: {exc}")

        if (not texto_paginas or any(not x for x in texto_paginas)) and FITZ_DISPONIBLE:
            try:
                doc = fitz.open(stream=contenido, filetype="pdf")
                paginas = max(paginas, len(doc))
                if not texto_paginas:
                    texto_paginas = [""] * len(doc)
                elif len(texto_paginas) < len(doc):
                    texto_paginas.extend([""] * (len(doc) - len(texto_paginas)))

                for i, page in enumerate(doc):
                    if texto_paginas[i].strip():
                        continue
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    txt, err = ejecutar_ocr(img)
                    texto_paginas[i] = txt
                    if err:
                        errores.append(f"OCR página {i + 1}: {err}")
            except Exception as exc:
                errores.append(f"Render/OCR PDF: {exc}")
        elif not FITZ_DISPONIBLE and any(not x for x in texto_paginas):
            errores.append("PyMuPDF no está disponible para OCR de PDFs escaneados.")

        textos = texto_paginas

    elif nombre_lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        paginas = 1
        try:
            img = Image.open(io.BytesIO(contenido))
            txt, err = ejecutar_ocr(img)
            textos = [txt]
            if err:
                errores.append(err)
        except Exception as exc:
            errores.append(f"Imagen: {exc}")
    else:
        errores.append("Tipo de archivo no soportado.")

    return {
        "texto": "\n\n".join(x for x in textos if x).strip(),
        "errores": errores,
        "paginas": paginas,
    }


# =========================================================
# METADATOS
# =========================================================
def buscar_fecha(texto: str) -> str:
    candidatos = re.findall(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b", texto)
    for valor in candidatos:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(valor, fmt).strftime("%d/%m/%Y")
            except ValueError:
                pass
    return ""


def buscar_por_patrones(texto: str, patrones: list[str]) -> str:
    for patron in patrones:
        m = re.search(patron, texto, flags=re.I | re.M)
        if m:
            return limpiar_espacios(m.group(1))
    return ""


def detectar_proveedor(texto: str, nombre: str = "") -> str:
    base = sin_acentos(f"{texto} {nombre}").lower()
    if "alvarez" in base and "sanchez" in base:
        return "Álvarez & Sánchez, S.A."
    if "farah group" in base or "farah" in base:
        return "Farah Group Company SRL"
    if "centro de distribucion" in base and "cristian" in base:
        return "Centro de Distribución Cristian SRL"
    if "cdc" in base and ("royal" in base or "factura" in base):
        return "Centro de Distribución Cristian SRL"
    # Yardow en la muestra puede salir con OCR imperfecto, pero el número 00494502 ayuda.
    if "yardow" in base or "00494502" in base or "mercasanto" in base or "merca santo" in base:
        return "Comercial Yardow SRL"
    return "Proveedor no identificado"


def extraer_metadata(texto: str, proveedor: str) -> dict:
    sinacc = sin_acentos(texto)

    if proveedor == "Álvarez & Sánchez, S.A.":
        factura = buscar_por_patrones(sinacc, [
            r"FACTURA[^\n]{0,80}?\b(\d{5,12})\b",
            r"FACTURA\s*(?:NO|NRO|NUMERO)?\s*[:#-]?\s*(\d{5,12})",
        ])
        fecha = buscar_por_patrones(sinacc, [r"FECHA\s*[:#-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})"]) or buscar_fecha(sinacc)

    elif proveedor == "Farah Group Company SRL":
        factura = buscar_por_patrones(sinacc, [
            r"Factura\s*(?:No\.?|Nro\.?|Numero)?\s*[:#-]?\s*(\d{5,15})",
        ])
        fecha = buscar_por_patrones(sinacc, [r"FECHA\s*[:#-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})"]) or buscar_fecha(sinacc)

    elif proveedor == "Comercial Yardow SRL":
        factura = buscar_por_patrones(sinacc, [
            r"No\.?\s*de\s*Factura\s*[:#-]?\s*(\d{5,15})",
            r"Factura\s*[:#-]?\s*(\d{5,15})",
        ])
        fecha = buscar_por_patrones(sinacc, [
            r"Fecha\s+de\s+Emision\s*[:#-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        ]) or buscar_fecha(sinacc)

    elif proveedor == "Centro de Distribución Cristian SRL":
        # Para CDC se conserva el NCF como número de factura/clave fiscal,
        # igual que en la versión anterior.
        factura = buscar_por_patrones(sinacc, [
            r"\bNCF\s*[:#-]?\s*(E\d{10,15})",
            r"\b(E31\d{8,15})\b",
        ])
        fecha = buscar_por_patrones(sinacc, [
            r"\bFecha\s*[:#-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        ]) or buscar_fecha(sinacc)
    else:
        factura = buscar_por_patrones(sinacc, [
            r"(?:Factura|No\.?\s*de\s*Factura)\s*[:#-]?\s*([A-Z0-9-]{5,20})",
            r"\b(E31\d{8,15})\b",
        ])
        fecha = buscar_fecha(sinacc)

    return {"num_factura": factura, "fecha": fecha}


# =========================================================
# PARSERS DE PRODUCTOS
# =========================================================
def producto(codigo, nombre, cant, emp, costo_total, itbis=0.18, cat=None):
    codigo = normalizar_codigo(codigo)
    nombre = limpiar_espacios(nombre)
    return {
        "codigo": codigo,
        "nombre": nombre,
        "cant": max(0.0, numero_decimal(cant, 0.0)),
        "emp": max(1, int(round(numero_decimal(emp, 1)))),
        "costo_total": max(0.0, numero_decimal(costo_total, 0.0)),
        "itbis": normalizar_itbis(itbis),
        "cat": cat or categoria_por_nombre(nombre),
    }


def parse_alvarez(texto: str) -> list[dict]:
    productos = []
    for linea in lineas_limpias(texto):
        s = sin_acentos(linea)
        # Cantidad | Unidad | código interno | código barras | tamaño | descripción | importes
        m = re.match(
            r"^\s*(\d+(?:[.,]\d+)?)\s+(CAJA|CAJ|UND|UNIDAD)\s+([A-Z0-9-]{2,12})\s+([A-Z0-9-]{6,18})\s+(.+)$",
            s,
            flags=re.I,
        )
        if not m:
            continue

        cant, unidad, _cod_interno, barcode, resto = m.groups()
        montos = extraer_montos(resto)
        if not montos:
            continue
        costo_total = montos[-1]

        # Descripción termina antes del primer monto monetario.
        pos = re.search(r"\d{1,3}(?:,\d{3})*\.\d{2}", resto)
        cuerpo = resto[:pos.start()].strip() if pos else resto

        # Tamaño típico: 12/70 CL. El primer número es el empaque.
        mt = re.match(r"^([0-9]{1,3}/[0-9]{1,4}\s*(?:CL|ML|L\.?)?)\s+(.+)$", cuerpo, flags=re.I)
        if mt:
            tamano, nombre = mt.groups()
            emp = inferir_empaque(tamano, unidad, barcode)
        else:
            nombre = cuerpo
            emp = inferir_empaque(nombre, unidad, barcode)

        productos.append(producto(barcode, nombre, cant, emp, costo_total, 0.18))

    return productos


def parse_farah(texto: str) -> list[dict]:
    productos = []
    for linea in lineas_limpias(texto):
        s = sin_acentos(linea)
        # Se trabaja desde el final: cantidad, UM, precio, ITBIS, total.
        m = re.match(
            r"^\s*([A-Z0-9-]{3,18})\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+(CAJA|CAJ|UND|UNIDAD)\s+"
            r"([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s*$",
            s,
            flags=re.I,
        )
        if not m:
            continue

        codigo, nombre, cant, unidad, _precio, _itbis_valor, total = m.groups()
        emp = inferir_empaque(nombre, unidad, codigo)
        productos.append(producto(codigo, nombre, cant, emp, total, 0.18))

    return productos


def parse_yardow(texto: str) -> list[dict]:
    productos = []
    for linea in lineas_limpias(texto):
        s = sin_acentos(linea)
        m = re.match(
            r"^\s*(\d+(?:[.,]\d+)?)\s+(PAL|CAJ|CAJA|UND|UNIDAD)\s+([A-Z0-9-]{3,18})\s+(.+)$",
            s,
            flags=re.I,
        )
        if not m:
            continue

        cant, unidad, codigo, resto = m.groups()
        montos = extraer_montos(resto)
        if len(montos) < 1:
            continue
        total = montos[-1]

        pos = re.search(r"\d{1,3}(?:,\d{3})*\.\d{2}", resto)
        nombre = resto[:pos.start()].strip() if pos else resto
        emp = inferir_empaque(nombre, unidad, codigo)
        productos.append(producto(codigo, nombre, cant, emp, total, 0.18))

    return productos


def _es_codigo_cdc(linea: str) -> bool:
    s = normalizar_codigo(linea)
    if not s or len(s) > 18:
        return False
    if re.fullmatch(r"\d{3,18}", s):
        return True
    if re.fullmatch(r"[A-Z]\d{2,10}", s.upper()):
        return True
    return False


def parse_cdc(texto: str) -> list[dict]:
    """Parser para tickets CDC: cantidad x precio, código, descripción, Caja/Paquete-N."""
    lines = lineas_limpias(texto)
    productos = []
    i = 0

    while i < len(lines):
        line = sin_acentos(lines[i])
        mq = re.search(r"\b(\d+(?:[.,]\d+)?)\s*[xX×]\s*([\d.,]+)", line)
        if not mq:
            i += 1
            continue

        cant = numero_decimal(mq.group(1))
        montos_q = extraer_montos(line)
        precio_unit = numero_decimal(mq.group(2))
        total = 0.0

        # Si Tesseract preservó columnas, el último monto suele ser el valor total.
        if len(montos_q) >= 2:
            candidatos = [x for x in montos_q if x > 0]
            if candidatos:
                total = candidatos[-1]
        if total <= 0:
            total = cant * precio_unit

        # Busca el código en las próximas 1-2 líneas.
        j = i + 1
        while j < min(len(lines), i + 4) and not _es_codigo_cdc(lines[j]):
            j += 1
        if j >= len(lines) or not _es_codigo_cdc(lines[j]):
            i += 1
            continue

        codigo = normalizar_codigo(lines[j])
        nombre_parts = []
        emp = 1
        k = j + 1

        while k < len(lines):
            cur = sin_acentos(lines[k])
            # Próximo producto.
            if re.search(r"\b\d+(?:[.,]\d+)?\s*[xX×]\s*[\d.,]+", cur):
                break

            mp = re.search(r"\b(?:Caja|Paquete|Paq|Pack)\s*[-:]?\s*(\d{1,4})\b", cur, flags=re.I)
            if mp:
                emp = int(mp.group(1))
                k += 1
                break

            # Evita encabezados/totales al final.
            if re.match(r"^(Subtotal|ITBIS|TOTAL|BANR|Codigo de Seguridad|Fecha de firma)", cur, flags=re.I):
                break

            # Si la línea parece puramente de columnas monetarias, no forma parte del nombre.
            if len(extraer_montos(cur)) >= 2 and len(cur.split()) <= 6:
                k += 1
                continue

            if cur:
                nombre_parts.append(cur)
            k += 1

        nombre = limpiar_espacios(" ".join(nombre_parts))
        if nombre:
            productos.append(producto(codigo, nombre, cant, emp, total, 0.18))
            i = max(k, i + 1)
        else:
            i += 1

    return productos


def parse_generico(texto: str) -> list[dict]:
    """Respaldo conservador para filas tabulares comunes."""
    productos = []
    for linea in lineas_limpias(texto):
        s = sin_acentos(linea)
        m = re.match(
            r"^\s*([A-Z0-9-]{4,18})\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+(CAJA|CAJ|UND|UNIDAD)\s+(.+)$",
            s,
            flags=re.I,
        )
        if not m:
            continue
        codigo, nombre, cant, unidad, resto = m.groups()
        montos = extraer_montos(resto)
        if not montos:
            continue
        emp = inferir_empaque(nombre, unidad, codigo)
        productos.append(producto(codigo, nombre, cant, emp, montos[-1], 0.18))
    return productos


def parsear_factura(texto: str, nombre: str) -> dict:
    proveedor = detectar_proveedor(texto, nombre)
    meta = extraer_metadata(texto, proveedor)

    if proveedor == "Álvarez & Sánchez, S.A.":
        productos = parse_alvarez(texto)
    elif proveedor == "Farah Group Company SRL":
        productos = parse_farah(texto)
    elif proveedor == "Comercial Yardow SRL":
        productos = parse_yardow(texto)
    elif proveedor == "Centro de Distribución Cristian SRL":
        productos = parse_cdc(texto)
    else:
        productos = parse_generico(texto)

    # El fallback genérico también ayuda si OCR rompió parte de una tabla.
    if not productos and proveedor != "Proveedor no identificado":
        productos = parse_generico(texto)

    return {
        "proveedor": proveedor,
        "num_factura": meta["num_factura"],
        "fecha": meta["fecha"],
        "productos": productos,
    }


@st.cache_data(show_spinner=False, max_entries=40)
def analizar_bytes(nombre: str, contenido: bytes) -> dict:
    extra = extraer_texto_desde_bytes(nombre, contenido)
    factura = parsear_factura(extra["texto"], nombre)
    return {
        "hash": hash_bytes(contenido),
        "texto": extra["texto"],
        "errores": extra["errores"],
        "paginas": extra["paginas"],
        "factura": factura,
    }


# =========================================================
# INVENTARIO / EXCEL
# =========================================================
def agregar_factura_al_inventario(factura: dict, archivo_hash: str):
    proveedor = factura["proveedor"].strip() or "Proveedor no identificado"
    num_factura = factura["num_factura"].strip() or archivo_hash[:12]
    fecha = factura["fecha"].strip()
    firma = (proveedor, num_factura)

    st.session_state.firmas_facturas_procesadas.add(firma)
    st.session_state.hashes_archivos_procesados.add(archivo_hash)
    st.session_state.detalle_facturas_procesadas[firma] = {
        "proveedor": proveedor,
        "num_factura": num_factura,
        "fecha": fecha,
        "cantidad_articulos": len(factura["productos"]),
    }

    for p in factura["productos"]:
        codigo = normalizar_codigo(p.get("codigo"))
        if not codigo:
            # No conviene mezclar artículos sin código bajo una llave vacía.
            codigo = "SIN" + hashlib.sha1(p.get("nombre", "").encode("utf-8")).hexdigest()[:10].upper()

        cant = max(0.0, numero_decimal(p.get("cant"), 0.0))
        emp = max(1, int(round(numero_decimal(p.get("emp"), 1))))
        unidades = cant * emp
        costo_total = max(0.0, numero_decimal(p.get("costo_total"), 0.0))
        itbis = normalizar_itbis(p.get("itbis", 0.18))
        nombre = limpiar_espacios(p.get("nombre")) or codigo
        categoria = limpiar_espacios(p.get("cat")) or categoria_por_nombre(nombre)

        if codigo in st.session_state.inventario_acumulado:
            art = st.session_state.inventario_acumulado[codigo]
            art["stock"] += unidades
            art["costo_total"] += costo_total
            art["proveedores"].setdefault(proveedor, {"unidades": 0.0, "costo_total": 0.0})
            art["proveedores"][proveedor]["unidades"] += unidades
            art["proveedores"][proveedor]["costo_total"] += costo_total
            st.session_state.avisos_acumulacion.append(f"{nombre} ({codigo}) — stock y costo acumulados.")
        else:
            st.session_state.inventario_acumulado[codigo] = {
                "nombre": nombre,
                "categoria": categoria,
                "stock": unidades,
                "costo_total": costo_total,
                "emp": emp,
                "itbis": itbis,
                "proveedores": {
                    proveedor: {"unidades": unidades, "costo_total": costo_total}
                },
            }


def construir_df_productos() -> pd.DataFrame:
    factor = 1 + st.session_state.margen_usado / 100.0
    filas = []
    for codigo, data in st.session_state.inventario_acumulado.items():
        costo_unit = data["costo_total"] / data["stock"] if data["stock"] > 0 else 0
        filas.append({
            "Nombre": data["nombre"],
            "Código Barra": codigo,
            "Categoría": data["categoria"],
            "Tipo": "producto",
            "Precio Venta": round_to_nearest_5(costo_unit * factor),
            "Costo": round(costo_unit, 4),
            "Stock": int(round(data["stock"])),
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


def generar_excel_wilpos(df_prod: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_prod.to_excel(writer, index=False, sheet_name="Productos")

        pd.DataFrame({
            "Nombre": ["Bebidas", "Insumos", "Cervezas", "Licores", "General"],
            "Descripción": [
                "Refrescos, agua, energizantes",
                "Fundas, vasos y consumibles",
                "Cervezas y maltas",
                "Whisky, tequila, vodka y otros licores",
                "Artículos varios",
            ],
        }).to_excel(writer, index=False, sheet_name="Categorías")

        proveedores = sorted({
            info["proveedor"] for info in st.session_state.detalle_facturas_procesadas.values()
        }) or ["Proveedor General"]
        pd.DataFrame({
            "Nombre": proveedores,
            "Contacto": [""] * len(proveedores),
            "Teléfono": [""] * len(proveedores),
            "Email": [""] * len(proveedores),
            "Dirección": [""] * len(proveedores),
            "RNC/Cédula": [""] * len(proveedores),
            "Tipo Identificación": ["RNC"] * len(proveedores),
        }).to_excel(writer, index=False, sheet_name="Proveedores")

        relaciones = []
        for codigo, data in st.session_state.inventario_acumulado.items():
            for proveedor, info in data.get("proveedores", {}).items():
                costo = info["costo_total"] / info["unidades"] if info["unidades"] > 0 else 0
                relaciones.append({
                    "Producto": data["nombre"],
                    "Proveedor": proveedor,
                    "Precio Costo": round(costo, 4),
                    "Principal": "Sí" if proveedor == next(iter(data["proveedores"])) else "No",
                })
        pd.DataFrame(relaciones).to_excel(writer, index=False, sheet_name="Producto-Proveedor")

        pd.DataFrame({
            "Instrucciones para cargar tu inventario": [
                "Revisa Productos y Producto-Proveedor antes de importar.",
                "Los datos OCR fueron validados/editados previamente en la aplicación.",
            ]
        }).to_excel(writer, index=False, sheet_name="Instrucciones")

    return output.getvalue()


# =========================================================
# UI
# =========================================================
head1, head2 = st.columns([4, 1])
with head1:
    st.markdown(
        """
        <div class="main-header">
          <h1>📦 Procesador de Facturas WilPOS V2</h1>
          <p>Foto desde el teléfono, PDF o galería → OCR → revisión editable → inventario → Excel.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with head2:
    if st.button("🧹 Reiniciar", use_container_width=True):
        for key, value in DEFAULTS.items():
            st.session_state[key] = value.copy() if hasattr(value, "copy") else value
        st.session_state.uploader_key += 1
        st.session_state.camera_key += 1
        st.rerun()

with st.container(border=True):
    st.subheader("1. Cargar factura")
    col_cfg, col_upload = st.columns([1, 2])

    with col_cfg:
        margen = st.number_input(
            "Margen de ganancia (%)",
            min_value=0.0,
            max_value=500.0,
            value=float(st.session_state.margen_usado),
            step=1.0,
        )

    with col_upload:
        modo = st.radio(
            "Origen",
            ["📁 Archivo / galería", "📷 Cámara del teléfono"],
            horizontal=True,
        )

        uploaded_files = []
        if modo == "📁 Archivo / galería":
            uploaded_files = st.file_uploader(
                "PDF, JPG, JPEG o PNG",
                type=["pdf", "png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key=f"uploader_{st.session_state.uploader_key}",
            ) or []
        else:
            foto = st.camera_input(
                "Incluye la factura completa, con buena luz y sin reflejos",
                key=f"camera_{st.session_state.camera_key}",
            )
            if foto is not None:
                uploaded_files = [foto]

    if not OCR_DISPONIBLE:
        st.error("OCR no disponible. Instala Tesseract + pytesseract para procesar fotos/PDF escaneados.")


revisadas = []
if uploaded_files:
    st.subheader("2. Revisar lectura")

    for idx, archivo in enumerate(uploaded_files):
        contenido = archivo.getvalue()
        analisis = analizar_bytes(archivo.name, contenido)
        f = analisis["factura"]
        keybase = f"{analisis['hash'][:12]}_{idx}"

        with st.container(border=True):
            st.markdown(f"#### 📄 {archivo.name}")

            if analisis["hash"] in st.session_state.hashes_archivos_procesados:
                st.warning("Este archivo idéntico ya fue procesado anteriormente.")
                continue

            for error in analisis["errores"]:
                st.caption(f"⚠️ {error}")

            c1, c2, c3 = st.columns(3)
            with c1:
                proveedor = st.text_input("Proveedor", value=f["proveedor"], key=f"prov_{keybase}")
            with c2:
                num_factura = st.text_input("No. factura / NCF", value=f["num_factura"], key=f"fac_{keybase}")
            with c3:
                fecha = st.text_input("Fecha", value=f["fecha"], placeholder="dd/mm/aaaa", key=f"fecha_{keybase}")

            firma = (proveedor.strip(), num_factura.strip())
            duplicada = bool(num_factura.strip()) and firma in st.session_state.firmas_facturas_procesadas
            if duplicada:
                st.warning("Esta combinación proveedor + factura ya fue procesada.")

            df_base = pd.DataFrame(f["productos"], columns=[
                "codigo", "nombre", "cant", "emp", "costo_total", "itbis", "cat"
            ])
            if df_base.empty:
                df_base = pd.DataFrame([{
                    "codigo": "", "nombre": "", "cant": 1.0, "emp": 1,
                    "costo_total": 0.0, "itbis": 0.18, "cat": "General"
                }])
                st.warning("No pude reconstruir líneas automáticamente. Puedes agregarlas manualmente en la tabla.")
            else:
                st.success(f"Se detectaron {len(df_base)} línea(s). Revísalas antes de procesar.")

            editado = st.data_editor(
                df_base,
                key=f"editor_{keybase}",
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                column_config={
                    "codigo": st.column_config.TextColumn("Código", help="Código de barras o código del artículo"),
                    "nombre": st.column_config.TextColumn("Descripción", width="large"),
                    "cant": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=1.0, format="%.2f"),
                    "emp": st.column_config.NumberColumn("Empaque", min_value=1, step=1, format="%d"),
                    "costo_total": st.column_config.NumberColumn("Costo total", min_value=0.0, step=0.01, format="%.2f"),
                    "itbis": st.column_config.NumberColumn("ITBIS", min_value=0.0, max_value=1.0, step=0.01, format="%.2f"),
                    "cat": st.column_config.SelectboxColumn("Categoría", options=["Bebidas", "Insumos", "Cervezas", "Licores", "General"]),
                },
            )

            # Descarta filas totalmente vacías.
            productos_editados = []
            for _, row in editado.fillna("").iterrows():
                if not str(row.get("nombre", "")).strip() and not str(row.get("codigo", "")).strip():
                    continue
                productos_editados.append(producto(
                    row.get("codigo", ""),
                    row.get("nombre", ""),
                    row.get("cant", 0),
                    row.get("emp", 1),
                    row.get("costo_total", 0),
                    row.get("itbis", 0.18),
                    row.get("cat", "General") or "General",
                ))

            with st.expander("🔎 Ver texto OCR", expanded=False):
                st.text_area("Texto detectado", analisis["texto"][:12000], height=240, key=f"ocr_{keybase}")

            revisadas.append({
                "hash": analisis["hash"],
                "duplicada": duplicada,
                "factura": {
                    "proveedor": proveedor.strip(),
                    "num_factura": num_factura.strip(),
                    "fecha": fecha.strip(),
                    "productos": productos_editados,
                },
            })


if revisadas:
    st.subheader("3. Incorporar al inventario")
    nuevas = [x for x in revisadas if not x["duplicada"] and x["factura"]["productos"]]

    if margen <= 15:
        st.warning("El margen debe ser mayor al 15% para procesar.")

    if st.button(
        f"✅ Procesar {len(nuevas)} factura(s) revisada(s)",
        type="primary",
        use_container_width=True,
        disabled=(not nuevas or margen <= 15),
    ):
        st.session_state.margen_usado = margen
        st.session_state.avisos_acumulacion = []
        for item in nuevas:
            agregar_factura_al_inventario(item["factura"], item["hash"])
        st.session_state.uploader_key += 1
        st.session_state.camera_key += 1
        st.rerun()


# =========================================================
# RESULTADO
# =========================================================
if st.session_state.inventario_acumulado:
    st.divider()
    st.subheader("4. Inventario consolidado")

    df_productos = construir_df_productos()
    total_facturas = len(st.session_state.detalle_facturas_procesadas)
    st.success(
        f"✅ {total_facturas} factura(s) procesada(s) · "
        f"{len(df_productos)} producto(s) único(s) · margen {st.session_state.margen_usado:g}%"
    )

    if st.session_state.avisos_acumulacion:
        with st.expander("🔄 Productos encontrados en más de una factura"):
            for aviso in st.session_state.avisos_acumulacion:
                st.info(aviso)

    with st.expander("📋 Facturas procesadas"):
        df_facturas = pd.DataFrame([
            {
                "Proveedor": info["proveedor"],
                "No. Factura": info["num_factura"],
                "Fecha": info["fecha"],
                "Artículos": info["cantidad_articulos"],
            }
            for info in st.session_state.detalle_facturas_procesadas.values()
        ])
        st.dataframe(df_facturas, use_container_width=True, hide_index=True)

    st.dataframe(df_productos, use_container_width=True, hide_index=True)

    excel_data = generar_excel_wilpos(df_productos)
    st.download_button(
        "📥 Descargar Excel para WilPOS",
        data=excel_data,
        file_name="Inventario_WilPOS_Acumulado_V2.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
else:
    st.info("Carga una factura para comenzar. En el teléfono puedes usar directamente la cámara.")
