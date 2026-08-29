import io
import math
import re
import pandas as pd
import streamlit as st
import openpyxl
import pdfplumber
from PIL import Image

try:
    import pytesseract
    OCR_DISPONIBLE = True
except ImportError:
    OCR_DISPONIBLE = False

# Configuración de la página
st.set_page_config(
    page_title="Generador de Inventario WilPOS", 
    page_icon="📦", 
    layout="wide"
)

# Estilos CSS avanzados
st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #1F4E78 0%, #2E75B6 100%);
            padding: 2.5rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(31, 78, 120, 0.15);
        }
        .main-header h1 {
            color: white !important;
            font-size: 2.3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .main-header p {
            color: #E2EFDA;
            font-size: 1.1rem;
            margin-bottom: 0;
        }
        .card-container {
            background-color: #ffffff;
            border: 1px solid #E1E8ED;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# Inicializar estados de la sesión de manera aislada
if "inventario_activo" not in st.session_state:
    st.session_state.inventario_activo = {}
if "detalle_factura_activa" not in st.session_state:
    st.session_state.detalle_factura_activa = {}
if "margen_usado" not in st.session_state:
    st.session_state.margen_usado = 35.0
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# Cabecera con título y botón de reinicio total
col_head1, col_head2 = st.columns([3, 1], gap="medium")

with col_head1:
    st.markdown("""
        <div class="main-header" style="margin-bottom: 0rem;">
            <h1>📦 Procesador Dinámico de Facturas WilPOS</h1>
            <p>Análisis OCR con anclaje estricto por código de producto (Margen 35%).</p>
        </div>
    """, unsafe_allow_html=True)

with col_head2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Limpiar Todo", type="secondary", use_container_width=True):
        st.session_state.inventario_activo = {}
        st.session_state.detalle_factura_activa = {}
        st.session_state.margen_usado = 35.0
        st.session_state.uploader_key += 1
        st.success("¡Memoria limpiada por completo!")
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="card-container">', unsafe_allow_html=True)
st.markdown("### ⚙️ Panel de Configuración y Carga de Factura")
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    margen_porcentaje = st.number_input(
        "💡 Digite el margen de ganancia (%)", 
        min_value=0.0, 
        max_value=500.0, 
        value=st.session_state.get("margen_usado", 35.0), 
        step=1.0,
        help="Debe ser mayor al 15% para procesar el inventario."
    )

with col2:
    uploaded_file = st.file_uploader(
        "📂 Selecciona o arrastra tu factura actual (PDF o foto de celular)", 
        type=["pdf", "png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.uploader_key}"
    )

st.markdown('</div>', unsafe_allow_html=True)

def round_to_nearest_5(val):
    return int(round(val / 5.0) * 5)

def procesar_factura_por_codigo(file):
    file_name = file.name.lower()
    extracted_text = ""
    
    if file_name.endswith('.pdf'):
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() or ""
        except Exception:
            pass
    elif file_name.endswith(('.png', '.jpg', '.jpeg')) and OCR_DISPONIBLE:
        try:
            image = Image.open(file)
            extracted_text = pytesseract.image_to_string(image, config='--psm 6')
        except Exception as e:
            st.error(f"Error en OCR: {e}")
            
    lines = [l.strip() for l in extracted_text.split('\n') if l.strip()]
    full_text_lower = extracted_text.lower()
    
    proveedor = "Proveedor General"
    for line in lines[:5]:
        line_clean = line.strip().upper()
        if len(line_clean) > 3 and not any(w in line_clean for w in ["RNC", "TEL", "CALLE", "SANTO", "DOMINGO", "FACTURA", "ID", "FECHA"]):
            proveedor = line_clean
            break

    if "cristian" in full_text_lower or "cdc" in full_text_lower:
        proveedor = "Centro de Distribución Cristian SRL (CDC)"
    elif "alvarez" in full_text_lower or "sanchez" in full_text_lower:
        proveedor = "Álvarez & Sánchez, S.A."

    num_factura = f"FAC-{abs(hash(file.name)) % 90000 + 10000}"
    fecha = "29/08/2026"
    
    for line in lines:
        ncf_m = re.search(r'(E31\d+|B01\d+|NCF[:\s]*([\w\d]+))', line, re.IGNORECASE)
        if ncf_m:
            num_factura = ncf_m.group(0).upper()
            break

    black_list = [
        "ROYAL", "DUSP", "CLUB", "RNC", "NCF", "SUBTOTAL", "ITBIS", "TOTAL", 
        "VALIDO", "HASTA", "ATENDIDO", "BANR", "TRANSFERENCIA", "POPULAR", "BANRESERVAS", 
        "BANESCO", "BHD", "FIRMA", "DIGITAL", "DIRECCION", "TELEFONO", "CLIENTE",
        "CENTRO", "DE", "DISTRIBUCION", "CRISTIAN", "SRL", "CALLE", "DUARTE", 
        "SANTO", "DOMINGO", "REPUBLICA", "DOMINICANA", "AUT.", "VIEJA", "KM", 
        "ID", "FECHA", "DESCRIPCION", "VALOR", "FACTURA", "CREDITO", "FISCAL", "ELECTRONICA"
    ]

    productos = {}
    
    # Motor de análisis anclado por Código de Producto (ej: P1016, 7501035010192, etc.)
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detectar si la línea es un código válido (alfanumérico de 4 a 15 caracteres sin espacios)
        if re.match(r'^([A-Z0-9]{4,15})$', line) and not any(b in line.upper() for b in black_list) and not re.search(r'[\d]\s*[xX]\s*[\d]', line):
            codigo = line
            nombre_partes = []
            cant = 1.0
            emp = 12
            costo_total = 1000.00
            
            # Recorrer hacia adelante desde el código para extraer nombre, empaque y cantidad x precio
            j = i + 1
            while j < len(lines) and j < i + 6:
                sig_line = lines[j]
                sig_upper = sig_line.upper()
                
                # Si encontramos la línea de cantidad x precio, extraemos los valores y paramos el bloque
                match_cant_precio = re.search(r'([\d\.]+)\s*[xX]\s*([\d,\.]+)', sig_line)
                if match_cant_precio:
                    try:
                        cant = float(match_cant_precio.group(1))
                    except ValueError:
                        pass
                    match_vals = re.findall(r'([\d]{1,3}(?:,\d{3})*\.\d{2})', sig_line)
                    if match_vals:
                        try:
                            costo_total = float(match_vals[-1].replace(',', ''))
                        except ValueError:
                            pass
                    break
                
                # Detectar empaques
                if "PAQUETE" in sig_upper or "CAJA" in sig_upper or "DISPLAY" in sig_upper:
                    nums_emp = re.findall(r'\d+', sig_line)
                    if nums_emp:
                        emp = int(nums_emp[-1])
                    j += 1
                    continue
                elif "UNIDAD" in sig_upper:
                    emp = 1
                    j += 1
                    continue
                
                # Acumular texto descriptivo limpio
                if not any(b in sig_upper for b in black_list):
                    clean_l = re.sub(r'\d{1,3}(?:,\d{3})*\.\d{2}|[;\\:]', '', sig_line).strip()
                    if len(clean_l) > 2 and not clean_l.isdigit():
                        nombre_partes.append(clean_l.upper())
                
                j += 1
            
            nombre = " ".join(nombre_partes).strip()
            if not nombre:
                nombre = f"PRODUCTO {codigo}"

            cat = "General"
            n_lower = nombre.lower()
            if any(w in n_lower for w in ["whisky", "tequila", "ron", "vodka", "licor"]):
                cat = "Licores"
            elif any(w in n_lower for w in ["cerveza", "prestige"]):
                cat = "Cervezas"
            elif any(w in n_lower for w in ["agua", "refresco", "ciclon", "energizante", "tonica"]):
                cat = "Bebidas"
            elif any(w in n_lower for w in ["servilleta", "funda", "vaso", "papel", "dispenser", "insumo"]):
                cat = "Insumos"

            if codigo not in productos:
                productos[codigo] = {
                    "nombre": nombre,
                    "categoria": cat,
                    "stock": cant * emp,
                    "costo_total": costo_total,
                    "emp": emp,
                    "itbis": 0.18
                }
            i = j # Saltar las líneas ya procesadas de este producto
        else:
            i += 1

    return proveedor, num_factura, fecha, productos

if uploaded_file:
    prov, num_fac, fecha_fac, prods_extraidos = procesar_factura_por_codigo(uploaded_file)
    
    st.session_state.inventario_activo = prods_extraidos
    st.session_state.detalle_factura_activa = {
        "proveedor": prov,
        "num_factura": num_fac,
        "fecha": fecha_fac,
        "cantidad_articulos": len(prods_extraidos)
    }
    st.session_state.margen_usado = margen_porcentaje

if len(st.session_state.inventario_activo) > 0:
    factor_margen = 1 + (st.session_state.margen_usado / 100.0)
    
    filas_productos = []
    for codigo, data in st.session_state.inventario_activo.items():
        costo_unitario = data["costo_total"] / data["stock"] if data["stock"] > 0 else 0
        precio_venta = round_to_nearest_5(costo_unitario * factor_margen)
        
        filas_productos.append({
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
            "Descuento Nota": None
        })

    df_productos = pd.DataFrame(filas_productos)
    info_factura = st.session_state.detalle_factura_activa

    st.markdown(f"""
        <div style="background-color: #D9EAD3; padding: 1.2rem; border-radius: 8px; border-left: 6px solid #38761D; margin-bottom: 1.5rem;">
            <h4 style="color: #274E13; margin: 0 0 8px 0;">✅ Factura Procesada Exitosamente</h4>
            <p style="color: #274E13; margin: 0 0 4px 0;">📂 <strong>Proveedor:</strong> {info_factura.get('proveedor', 'N/A')}</p>
            <p style="color: #274E13; margin: 0 0 4px 0;">📄 <strong>Factura No.:</strong> {info_factura.get('num_factura', 'N/A')}</p>
            <p style="color: #274E13; margin: 0 0 4px 0;">📦 <strong>Productos extraídos:</strong> {len(df_productos)}</p>
            <p style="color: #274E13; margin: 0;">📊 <strong>Margen aplicado:</strong> {st.session_state.margen_usado:g}%</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.markdown(f"### 📊 Vista Previa de Artículos Detectados ({len(df_productos)})")
    st.dataframe(df_productos, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    def generar_excel_wilpos(df_prod):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_prod.to_excel(writer, index=False, sheet_name='Productos')
            
            df_cat = pd.DataFrame({
                "Nombre": ["Bebidas", "Insumos", "Cervezas", "Licores", "General"],
                "Descripción": ["Refrescos, agua, energizantes", "Fundas y vasos", "Cervezas y maltas", "Whisky, tequila, vodka", "Artículos varios"]
            })
            df_cat.to_excel(writer, index=False, sheet_name='Categorías')
            
            prov_nombre = info_factura.get('proveedor', 'Proveedor General')
            df_prov = pd.DataFrame({
                "Nombre": [prov_nombre],
                "Contacto": ["Ventas"],
                "Teléfono": ["809-000-0000"],
                "Email": [""],
                "Dirección": ["Santo Domingo"],
                "RNC/Cédula": ["131000000"],
                "Tipo Identificación": ["RNC"]
            })
            df_prov.to_excel(writer, index=False, sheet_name='Proveedores')
            
            df_pp = pd.DataFrame({
                "Producto": [df_prod.loc[0, "Nombre"] if len(df_prod) > 0 else "Producto"],
                "Proveedor": [prov_nombre],
                "Precio Costo": [df_prod.loc[0, "Costo"] if len(df_prod) > 0 else 0],
                "Principal": ["Sí"]
            })
            df_pp.to_excel(writer, index=False, sheet_name='Producto-Proveedor')
            
            df_inst = pd.DataFrame({
                "Instrucciones para cargar tu inventario": [
                    "Llena la hoja Productos con tus artículos.",
                    "Generado dinámicamente mediante WilPOS."
                ]
            })
            df_inst.to_excel(writer, index=False, sheet_name='Instrucciones')
            
        return output.getvalue()

    excel_data = generar_excel_wilpos(df_productos)

    st.markdown('<div class="card-container" style="text-align: center; background-color: #F8F9FA;">', unsafe_allow_html=True)
    st.markdown("### 📥 ¡Todo Listo para Importar!")
    st.markdown("Descarga tu archivo Excel listo para WilPOS.")
    
    st.download_button(
        label="📥 Descargar Excel de la Factura (.xlsx)",
        data=excel_data,
        file_name="Inventario_WilPOS_Actual.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
        <div style="background-color: #FFF2CC; padding: 1.5rem; border-radius: 10px; border-left: 6px solid #D6B656; text-align: center; margin-top: 1rem;">
            <h4 style="color: #8C6B00; margin-bottom: 0.5rem;">⚠️ Esperando Factura Actual</h4>
            <p style="color: #555555; margin-bottom: 0;">Sube tu archivo para que la aplicación analice y extraiga los artículos de manera independiente.</p>
        </div>
    """, unsafe_allow_html=True)
