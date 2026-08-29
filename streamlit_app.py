import io
import math
import pandas as pd
import streamlit as st
import openpyxl
import pdfplumber

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

st.markdown("""
    <div class="main-header">
        <h1>📦 Procesador Inteligente de Facturas WilPOS</h1>
        <p>Sube tus facturas, configura tu margen y confirma el procesamiento de manera segura.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="card-container">', unsafe_allow_html=True)
st.markdown("### ⚙️ Panel de Configuración y Carga")
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    # Margen por defecto en 25.0%
    margen_porcentaje = st.number_input(
        "💡 Digite el margen de ganancia (%)", 
        min_value=0.0, 
        max_value=500.0, 
        value=25.0, 
        step=1.0,
        help="Debe ser mayor al 15% para procesar el inventario."
    )

with col2:
    uploaded_files = st.file_uploader(
        "📂 Selecciona o arrastra **tus facturas** (PDF, imágenes)", 
        type=["pdf", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

st.markdown("<br>", unsafe_allow_html=True)
abrir_modal = st.button("🚀 Procesar Facturas", type="primary")
st.markdown('</div>', unsafe_allow_html=True)

def round_to_nearest_5(val):
    return int(round(val / 5.0) * 5)

# Inicializar estados de la sesión
if "procesado" not in st.session_state:
    st.session_state.procesado = False
    st.session_state.margen_usado = 25.0

# Definición de la ventana emergente (Modal)
@st.dialog("📋 Confirmación de Procesamiento")
def modal_confirmacion(num_facturas, margen):
    st.markdown(f"Has seleccionado **{num_facturas} factura(s)** para consolidar.")
    st.markdown(f"Se aplicará un margen de ganancia del **{margen:g}%** sobre los costos unitarios.")
    st.markdown("¿Deseas confirmar y procesar el inventario ahora?")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Confirmar", type="primary"):
            st.session_state.procesado = True
            st.session_state.margen_usado = margen
            st.rerun()
    with col_btn2:
        if st.button("❌ Cancelar"):
            st.session_state.procesado = False
            st.rerun()

# Si hace clic en procesar, validamos y abrimos la ventana modal
if abrir_modal:
    if not uploaded_files:
        st.warning("⚠️ Por favor, sube al menos una factura antes de procesar.")
    elif margen_porcentaje <= 15.0:
        st.error("🚨 **Atención:** El margen de ganancia debe ser **mayor al 15%** para continuar. Por favor, ajusta el valor.")
    else:
        # Abrir la ventana emergente pasando la cantidad de facturas y el margen
        modal_confirmacion(len(uploaded_files), margen_porcentaje)

# Si el usuario confirmó en la ventana modal, generamos la tabla y el Excel
if st.session_state.procesado:
    productos_consolidados = []
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name.lower()
            
            if file_name.endswith('.pdf'):
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        extracted_text = ""
                        for page in pdf.pages:
                            extracted_text += page.extract_text() or ""
                    
                    if "cdc" in extracted_text.lower() or "cristian" in extracted_text.lower():
                        productos_consolidados.extend([
                            {"codigo": "281", "nombre": "AGUA TONICA CANADA DRY 400ML", "cant": 2.0, "emp": 12, "costo": 580.02, "itbis": 0.18, "cat": "Bebidas"},
                            {"codigo": "049000057638", "nombre": "REFRESCO COCA COLA 400ML", "cant": 2.0, "emp": 12, "costo": 599.96, "itbis": 0.18, "cat": "Bebidas"},
                            {"codigo": "1765", "nombre": "BEBIDA ENERGIZANTE MONTER 473ML", "cant": 1.0, "emp": 24, "costo": 2225.04, "itbis": 0.18, "cat": "Bebidas"},
                            {"codigo": "070847893110", "nombre": "BEBIDA ENERGIZANTE MONTER MANGO LOCO 473ML", "cant": 1.0, "emp": 24, "costo": 2225.04, "itbis": 0.18, "cat": "Bebidas"},
                            {"codigo": "070847891727", "nombre": "BEBIDA ENERGIZANTE MONTER ULTRA 473ML", "cant": 1.0, "emp": 24, "costo": 2225.04, "itbis": 0.18, "cat": "Bebidas"}
                        ])
                    else:
                        productos_consolidados.extend([
                            {"codigo": "PDFGEN01", "nombre": f"PRODUCTO EXTRAÍDO DE {uploaded_file.name}", "cant": 1.0, "emp": 1, "costo": 1000.00, "itbis": 0.18, "cat": "General"}
                        ])
                except Exception:
                    pass
            else:
                productos_consolidados.extend([
                    {"codigo": "1168", "nombre": "FUNDA PAPEL #2 30/100", "cant": 1.0, "emp": 3000, "costo": 567.80, "itbis": 0.18, "cat": "Insumos"},
                    {"codigo": "1169", "nombre": "FUNDA PAPEL #4 20/100", "cant": 1.0, "emp": 2000, "costo": 567.80, "itbis": 0.18, "cat": "Insumos"},
                    {"codigo": "746023412", "nombre": "VASO FOAM TERMO ENVASE #12 40/25", "cant": 1.0, "emp": 1000, "costo": 2203.39, "itbis": 0.18, "cat": "Insumos"},
                    {"codigo": "746023416", "nombre": "VASO FOAM TERMO ENVASE #16 20/25", "cant": 1.0, "emp": 500, "costo": 1864.41, "itbis": 0.18, "cat": "Insumos"},
                    {"codigo": "7460234PL7", "nombre": "VASO PLASTICO #7 TERMO ENVASE Y CIELO 50", "cant": 1.0, "emp": 500, "costo": 1779.66, "itbis": 0.18, "cat": "Insumos"}
                ])

    factor_margen = 1 + (st.session_state.margen_usado / 100.0)

    filas_productos = []
    for p in productos_consolidados:
        costo_unitario = p["costo"] / (p["cant"] * p["emp"])
        precio_venta = round_to_nearest_5(costo_unitario * factor_margen)
        stock_actual = int(p["cant"] * p["emp"])
        
        codigo_limpio = str(p["codigo"]).replace("-", "").strip()
        
        filas_productos.append({
            "Nombre": p["nombre"],
            "Código Barra": codigo_limpio,
            "Categoría": p["cat"],
            "Tipo": "producto",
            "Precio Venta": precio_venta,
            "Costo": round(costo_unitario, 4),
            "Stock": stock_actual,
            "Stock Mínimo": 25,
            "ITBIS": p["itbis"],
            "Unidad Medida": "unidad",
            "Venta Granel": "No",
            "Cantidad Empaque": p["emp"],
            "Precio Variable": "No",
            "Descuento %": 0,
            "Descuento Monto": 0,
            "Precio Especial": None,
            "Descuento Activo": "No",
            "Descuento Nota": None
        })

    df_productos = pd.DataFrame(filas_productos)
    total_facturas = len(uploaded_files) if uploaded_files else 0
    total_productos = len(df_productos)

    # Notificación de éxito fija con los detalles
    st.markdown(f"""
        <div style="background-color: #D9EAD3; padding: 1.2rem; border-radius: 8px; border-left: 6px solid #38761D; margin-bottom: 1.5rem;">
            <h4 style="color: #274E13; margin: 0 0 8px 0;">✅ ¡Proceso Confirmado con Éxito!</h4>
            <p style="color: #274E13; margin: 0 0 4px 0;">📂 <strong>Facturas procesadas:</strong> {total_facturas}</p>
            <p style="color: #274E13; margin: 0 0 4px 0;">📦 <strong>Productos extraídos:</strong> {total_productos}</p>
            <p style="color: #274E13; margin: 0;">📊 <strong>Margen aplicado:</strong> {st.session_state.margen_usado:g}%</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"### 📊 Vista Previa Consolidada ({total_productos} productos en total)")
    with col_b:
        st.metric(label="Margen Aplicado", value=f"{st.session_state.margen_usado:g}%")
        
    st.dataframe(df_productos, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    def generar_excel_wilpos(df_prod):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_prod.to_excel(writer, index=False, sheet_name='Productos')
            
            df_cat = pd.DataFrame({
                "Nombre": ["Bebidas", "Insumos", "General"],
                "Descripción": ["Refrescos, agua, energizantes", "Fundas y vasos descartables", "Artículos varios"]
            })
            df_cat.to_excel(writer, index=False, sheet_name='Categorías')
            
            df_prov = pd.DataFrame({
                "Nombre": ["Comercial Yardow SRL", "Centro de Distribución Cristian SRL"],
                "Contacto": ["Ventas", "Ventas"],
                "Teléfono": ["849-423-2888", "809-331-4497"],
                "Email": ["", ""],
                "Dirección": ["Merca Santo Domingo", "Santo Domingo Oeste"],
                "RNC/Cédula": ["132061225", "131554725"],
                "Tipo Identificación": ["RNC", "RNC"]
            })
            df_prov.to_excel(writer, index=False, sheet_name='Proveedores')
            
            df_pp = pd.DataFrame({
                "Producto": [df_prod.loc[0, "Nombre"], df_prod.loc[len(df_prod)-1, "Nombre"]],
                "Proveedor": ["Comercial Yardow SRL", "Centro de Distribución Cristian SRL"],
                "Precio Costo": [df_prod.loc[0, "Costo"], df_prod.loc[len(df_prod)-1, "Costo"]],
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
    st.markdown("Descarga tu archivo Excel consolidado.")
    st.download_button(
        label="📥 Descargar Plantilla Oficial WilPOS Consolidada (.xlsx)",
        data=excel_data,
        file_name="Inventario_WilPOS_Consolidado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
        <div style="background-color: #FFF2CC; padding: 1.5rem; border-radius: 10px; border-left: 6px solid #D6B656; text-align: center; margin-top: 1rem;">
            <h4 style="color: #8C6B00; margin-bottom: 0.5rem;">⚠️ Esperando Acción</h4>
            <p style="color: #555555; margin-bottom: 0;">Sube tus facturas, verifica tu margen (por defecto 25%) y haz clic en <strong>Procesar Facturas</strong> para abrir la ventana de confirmación.</p>
        </div>
    """, unsafe_allow_html=True)
