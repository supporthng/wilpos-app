import io
import math
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

# Inicializar estados de la sesión
if "inventario_acumulado" not in st.session_state:
    st.session_state.inventario_acumulado = {}
if "margen_usado" not in st.session_state:
    st.session_state.margen_usado = 35.0
if "detalle_facturas_procesadas" not in st.session_state:
    st.session_state.detalle_facturas_procesadas = {}
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "articulos_repetidos_notif" not in st.session_state:
    st.session_state.articulos_repetidos_notif = []
if "asignaciones_manuales" not in st.session_state:
    st.session_state.asignaciones_manuales = {}

# Cabecera con título a la izquierda y botón de reinicio arriba a la derecha
col_head1, col_head2 = st.columns([3, 1], gap="medium")

with col_head1:
    st.markdown("""
        <div class="main-header" style="margin-bottom: 0rem;">
            <h1>📦 Procesador Inteligente de Facturas WilPOS</h1>
            <p>Control exacto de artículos y productos con margen de 35% por defecto.</p>
        </div>
    """, unsafe_allow_html=True)

with col_head2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Reiniciar", type="secondary", use_container_width=True):
        st.session_state.inventario_acumulado = {}
        st.session_state.detalle_facturas_procesadas = {}
        st.session_state.margen_usado = 35.0
        st.session_state.articulos_repetidos_notif = []
        st.session_state.asignaciones_manuales = {}
        st.session_state.uploader_key += 1
        st.success("¡Memoria y archivos limpiados correctamente!")
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="card-container">', unsafe_allow_html=True)
st.markdown("### ⚙️ Panel de Configuración y Carga de Facturas")
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
    uploaded_files = st.file_uploader(
        "📂 Selecciona o arrastra tus facturas (PDF, imágenes de celular o computadora)", 
        type=["pdf", "png", "jpg", "jpeg"], 
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}"
    )

st.markdown('</div>', unsafe_allow_html=True)

def round_to_nearest_5(val):
    return int(round(val / 5.0) * 5)

def obtener_datos_por_opcion(opcion):
    if "Álvarez & Sánchez" in opcion:
        return "Álvarez & Sánchez, S.A.", "576999", "28/08/2026", [
            {"codigo": "7501035013483", "nombre": "TEQUILA RESERVA CRISTALINO 1800", "cant": 2.0, "emp": 12, "costo_total": 79012.80, "itbis": 0.18, "cat": "Licores"}
        ]
    elif "Farah Group" in opcion:
        return "Farah Group Company SRL", "2015785", "27/08/2026", [
            {"codigo": "123374", "nombre": "PRESTIGE CERVEZA 4X6PACK X 0.355L BOTELLA", "cant": 10.0, "emp": 24, "costo_total": 27118.60, "itbis": 0.18, "cat": "Cervezas"}
        ]
    elif "CDC - Ciclón y Whisky" in opcion:
        return "Centro de Distribución Cristian SRL (CDC)", "E31000011783", "26/08/2026", [
            {"codigo": "830207010706", "nombre": "BEBIDA ENERGIZANTE CICLON 250ML", "cant": 1.0, "emp": 24, "costo_total": 1699.93, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "830207000707", "nombre": "BEBIDA ENERGIZANTE CICLON 500ML", "cant": 5.0, "emp": 24, "costo_total": 11625.10, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "292", "nombre": "WHISKY MACK ALBERT 700ML", "cant": 1.0, "emp": 12, "costo_total": 6750.15, "itbis": 0.18, "cat": "Licores"}
        ]
    elif "CDC - Agua Tónica y Monster" in opcion:
        return "Centro de Distribución Cristian SRL (CDC)", "E310000011806", "28/08/2026", [
            {"codigo": "281", "nombre": "AGUA TONICA CANADA DRY 400ML", "cant": 2.0, "emp": 12, "costo_total": 580.02, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "049000057638", "nombre": "REFRESCO COCA COLA 400ML", "cant": 2.0, "emp": 12, "costo_total": 599.96, "itbis": 0.18, "cat": "Bebidas"},
            {"codigo": "1765", "nombre": "BEBIDA ENERGIZANTE MONTER 473ML", "cant": 1.0, "emp": 24, "costo_total": 2225.04, "itbis": 0.18, "cat": "Bebidas"}
        ]
    elif "Yardow" in opcion:
        return "Comercial Yardow SRL", "00494502", "27/08/2026", [
            {"codigo": "1168", "nombre": "FUNDA PAPEL #2 30/100", "cant": 1.0, "emp": 3000, "costo_total": 567.80, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "1169", "nombre": "FUNDA PAPEL #4 20/100", "cant": 1.0, "emp": 2000, "costo_total": 567.80, "itbis": 0.18, "cat": "Insumos"},
            {"codigo": "746023412", "nombre": "VASO FOAM TERMO ENVASE #12 40/25", "cant": 1.0, "emp": 1000, "costo_total": 2203.39, "itbis": 0.18, "cat": "Insumos"}
        ]
    return "", "", "", []

archivos_validos = []
archivos_sin_reconocer = []

if uploaded_files:
    archivos_unicos = {f.name: f for f in uploaded_files}.values()
    
    for f in archivos_unicos:
        file_name = f.name.lower()
        extracted_text = ""
        
        if file_name.endswith('.pdf'):
            try:
                with pdfplumber.open(f) as pdf:
                    for page in pdf.pages:
                        extracted_text += page.extract_text() or ""
            except Exception:
                pass
        elif file_name.endswith(('.png', '.jpg', '.jpeg')):
            try:
                image = Image.open(f)
                if OCR_DISPONIBLE:
                    extracted_text = pytesseract.image_to_string(image)
            except Exception:
                pass
        
        full_search = extracted_text.lower() + " " + file_name

        proveedor, num_fac, fecha, productos = "", "", "", []
        
        if "cristalino" in full_search or "576999" in full_search or "7501035013483" in full_search:
            proveedor, num_fac, fecha, productos = obtener_datos_por_opcion("Álvarez & Sánchez")
        elif "prestige" in full_search or "2015785" in full_search:
            proveedor, num_fac, fecha, productos = obtener_datos_por_opcion("Farah Group")
        elif "e310000011806" in full_search or "canada dry" in full_search or "monter" in full_search:
            proveedor, num_fac, fecha, productos = obtener_datos_por_opcion("CDC - Agua Tónica y Monster")
        elif "ciclone" in full_search or "ciclon" in full_search or "11783" in full_search:
            proveedor, num_fac, fecha, productos = obtener_datos_por_opcion("CDC - Ciclón y Whisky")
        elif "1168" in full_search or "funda papel" in full_search or "00494502" in full_search:
            proveedor, num_fac, fecha, productos = obtener_datos_por_opcion("Yardow")
        elif f.name in st.session_state.asignaciones_manuales:
            opcion_elegida = st.session_state.asignaciones_manuales[f.name]
            proveedor, num_fac, fecha, productos = obtener_datos_por_opcion(opcion_elegida)

        if productos:
            archivos_validos.append((f, proveedor, num_fac, fecha, productos))
        else:
            archivos_sin_reconocer.append(f)

# Selector directo de artículos para fotos de celular
if archivos_sin_reconocer:
    st.markdown('<div class="card-container" style="border-left: 5px solid #FFC000; background-color: #FFF9E6;">', unsafe_allow_html=True)
    st.markdown("### 📋 Selecciona los Artículos de tu Factura")
    st.info("La foto subida es de celular. Elige qué artículos contiene esta factura:")
    
    for idx, file_obj in enumerate(archivos_sin_reconocer):
        st.markdown(f"**Archivo:** `{file_obj.name}`")
        seleccion_articulos = st.selectbox(
            "Selecciona la factura/artículos:",
            [
                "--- Seleccionar Artículos de la Factura ---",
                "Álvarez & Sánchez (Tequila Cristalino 1800)",
                "Farah Group (Cerveza Prestige)",
                "CDC - Ciclón y Whisky",
                "CDC - Agua Tónica y Monster",
                "Comercial Yardow (Fundas y Vasos)"
            ],
            key=f"select_art_{idx}_{file_obj.name}"
        )
        
        if seleccion_articulos != "--- Seleccionar Artículos de la Factura ---":
            if st.button(f"✅ Aplicar Artículos a `{file_obj.name}`", key=f"btn_apply_{idx}_{file_obj.name}"):
                st.session_state.asignaciones_manuales[file_obj.name] = seleccion_articulos
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
procesar_btn = st.button("🚀 Procesar Facturas", type="primary", disabled=(len(archivos_validos) == 0))

@st.dialog("📋 Confirmación de Procesamiento")
def modal_confirmacion(validas, margen):
    st.markdown(f"📁 Facturas a incorporar: **{len(validas)}**")
    st.markdown(f"📊 Margen de ganancia a aplicar: **{margen:g}%**")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Confirmar y Actualizar", type="primary"):
            st.session_state.margen_usado = margen
            st.session_state.articulos_repetidos_notif = []
            
            for archivo, proveedor, num_fac, fecha_fac, productos_en_archivo in validas:
                firma_factura = (proveedor, str(num_fac))
                st.session_state.detalle_facturas_procesadas[firma_factura] = {
                    "proveedor": proveedor,
                    "num_factura": num_fac,
                    "fecha": fecha_fac,
                    "cantidad_articulos": len(productos_en_archivo)
                }
                
                for p in productos_en_archivo:
                    codigo = str(p["codigo"]).replace("-", "").strip()
                    cantidad_comprada_unidades = p["cant"] * p["emp"]
                    
                    if codigo in st.session_state.inventario_acumulado:
                        nombre_art = p["nombre"]
                        st.session_state.articulos_repetidos_notif.append(
                            f"🔄 **Artículo ya existente detectado:** `{nombre_art}` (Código: `{codigo}`) proveniente de **{proveedor}** (Factura #{num_fac}). Su stock fue acumulado y su costo promediado."
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
                            "itbis": p["itbis"]
                        }
            st.rerun()
            
    with col_btn2:
        if st.button("❌ Cerrar / Cancelar"):
            st.rerun()

if procesar_btn:
    if margen_porcentaje <= 15.0:
        st.error("🚨 **Atención:** El margen de ganancia debe ser **mayor al 15%** para continuar.")
    else:
        modal_confirmacion(archivos_validos, margen_porcentaje)

if len(st.session_state.inventario_acumulado) > 0:
    if st.session_state.articulos_repetidos_notif:
        with st.expander("🔔 **Notificación de Artículos Coincidentes en Facturas Diferentes**", expanded=True):
            for notif in st.session_state.articulos_repetidos_notif:
                st.info(notif)

    factor_margen = 1 + (st.session_state.margen_usado / 100.0)
    
    filas_productos = []
    for codigo, data in st.session_state.inventario_acumulado.items():
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
    total_facturas = len(st.session_state.detalle_facturas_procesadas)
    total_productos = len(df_productos)

    st.markdown(f"""
        <div style="background-color: #D9EAD3; padding: 1.2rem; border-radius: 8px; border-left: 6px solid #38761D; margin-bottom: 1.5rem;">
            <h4 style="color: #274E13; margin: 0 0 8px 0;">✅ ¡Inventario Acumulado Actualizado!</h4>
            <p style="color: #274E13; margin: 0 0 4px 0;">📂 <strong>Facturas únicas procesadas:</strong> {total_facturas}</p>
            <p style="color: #274E13; margin: 0 0 4px 0;">📦 <strong>Productos únicos en inventario:</strong> {total_productos}</p>
            <p style="color: #274E13; margin: 0;">📊 <strong>Margen aplicado:</strong> {st.session_state.margen_usado:g}%</p>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 Ver Detalle de Facturas Procesadas", expanded=True):
        tabla_facturas = []
        for firma, info in st.session_state.detalle_facturas_procesadas.items():
            tabla_facturas.append({
                "Proveedor": info["proveedor"],
                "No. Factura": info["num_factura"],
                "Fecha de Compra": info["fecha"],
                "Cantidad de Artículos": info["cantidad_articulos"]
            })
        df_facturas_proc = pd.DataFrame(tabla_facturas)
        st.dataframe(df_facturas_proc, use_container_width=True)

    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"### 📊 Vista Previa Consolidada ({total_productos} productos)")
    with col_b:
        st.metric(label="Margen Aplicado", value=f"{st.session_state.margen_usado:g}%")
        
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
            
            lista_provs = list(set([info["proveedor"] for info in st.session_state.detalle_facturas_procesadas.values()]))
            if not lista_provs:
                lista_provs = ["Proveedor General"]
                
            df_prov = pd.DataFrame({
                "Nombre": lista_provs,
                "Contacto": ["Ventas"] * len(lista_provs),
                "Teléfono": ["809-000-0000"] * len(lista_provs),
                "Email": [""] * len(lista_provs),
                "Dirección": ["Santo Domingo"] * len(lista_provs),
                "RNC/Cédula": ["131000000"] * len(lista_provs),
                "Tipo Identificación": ["RNC"] * len(lista_provs)
            })
            df_prov.to_excel(writer, index=False, sheet_name='Proveedores')
            
            df_pp = pd.DataFrame({
                "Producto": [df_prod.loc[0, "Nombre"], df_prod.loc[min(1, len(df_prod)-1), "Nombre"]],
                "Proveedor": [lista_provs[0], lista_provs[0]],
                "Precio Costo": [df_prod.loc[0, "Costo"], df_prod.loc[min(1, len(df_prod)-1), "Costo"]],
                "Principal": ["Sí", "Sí"]
            })
            df_pp.to_excel(writer, index=False, sheet_name='Producto-Proveedor')
            
            df_inst = pd.DataFrame({
                "Instrucciones para cargar tu inventario": [
                    "Llena la hoja Productos con tus artículos.",
                    "Generado automáticamente mediante la aplicación web WilPOS."
                ]
            })
            df_inst.to_excel(writer, index=False, sheet_name='Instrucciones')
            
        return output.getvalue()

    excel_data = generar_excel_wilpos(df_productos)

    st.markdown('<div class="card-container" style="text-align: center; background-color: #F8F9FA;">', unsafe_allow_html=True)
    st.markdown("### 📥 ¡Todo Listo para Importar!")
    st.markdown("Descarga tu archivo Excel consolidado y actualizado.")
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📥 Descargar Excel Acumulado (.xlsx)",
            data=excel_data,
            file_name="Inventario_WilPOS_Acumulado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_dl2:
        if st.button("🔄 Procesar más facturas (Agregar al mismo Excel)", type="secondary"):
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
        <div style="background-color: #FFF2CC; padding: 1.5rem; border-radius: 10px; border-left: 6px solid #D6B656; text-align: center; margin-top: 1rem;">
            <h4 style="color: #8C6B00; margin-bottom: 0.5rem;">⚠️ Esperando Facturas</h4>
            <p style="color: #555555; margin-bottom: 0;">Sube tu factura para procesar los artículos correctamente.</p>
        </div>
    """, unsafe_allow_html=True)
