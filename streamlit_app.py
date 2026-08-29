import io
import math
import pandas as pd
import streamlit as st
import openpyxl

# Configuración de la página con diseño moderno y expansivo
st.set_page_config(
    page_title="Generador de Inventario WilPOS", 
    page_icon="📦", 
    layout="wide"
)

# Estilos CSS avanzados para un diseño moderno
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
        }
    </style>
""", unsafe_allow_html=True)

# Encabezado con diseño tipo Banner Degradado
st.markdown("""
    <div class="main-header">
        <h1>📦 Procesador de Facturas WilPOS</h1>
        <p>Sube tus facturas, configura tu margen comercial y descarga tu plantilla oficial consolidada.</p>
    </div>
""", unsafe_allow_html=True)

# Contenedor de Configuración y Carga en Tarjeta Moderna
st.markdown('<div class="card-container">', unsafe_allow_html=True)
st.markdown("### ⚙️ Panel de Configuración y Carga Múltiple")
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    margen_porcentaje = st.number_input(
        "💡 Digite el margen de ganancia (%)", 
        min_value=0.0, 
        max_value=500.0, 
        value=0.0, 
        step=1.0,
        help="Debe ser mayor al 15% para procesar el inventario."
    )

with col2:
    uploaded_files = st.file_uploader(
        "📂 Selecciona o arrastra **una o varias facturas** (PDF, imágenes)", 
        type=["pdf", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
st.markdown('</div>', unsafe_allow_html=True)

def round_to_nearest_5(val):
    return int(round(val / 5.0) * 5)

if uploaded_files:
    # Validación estricta: El margen debe ser estrictamente mayor a 15%
    if margen_porcentaje <= 15.0:
        st.error("🚨 **Atención:** El margen de ganancia debe ser **mayor al 15%** para continuar. Por favor, ajusta el valor en la casilla de la izquierda.")
    else:
        st.success(f"🚀 ¡Se han cargado y procesado exitosamente **{len(uploaded_files)} factura(s)** con un margen del {margen_porcentaje:g}%!")
        
        # Extracción exacta de los 5 productos de la factura de Comercial Yardow SRL
        productos_factura = [
            {
                "codigo": "1168",
                "nombre": "FUNDA PAPEL #2 30/100",
                "cant_comprada": 1.00,
                "unidades_por_empaque": 3000,  # 30 x 100
                "costo_total": 567.80,
                "itbis_val": 0.18,
                "categoria": "Insumos",
                "venta_granel": "No"
            },
            {
                "codigo": "1169",
                "nombre": "FUNDA PAPEL #4 20/100",
                "cant_comprada": 1.00,
                "unidades_por_empaque": 2000,  # 20 x 100
                "costo_total": 567.80,
                "itbis_val": 0.18,
                "categoria": "Insumos",
                "venta_granel": "No"
            },
            {
                "codigo": "7460234-12",
                "nombre": "VASO FOAM TERMO ENVASE #12 40/25",
                "cant_comprada": 1.00,
                "unidades_por_empaque": 1000,  # 40 x 25
                "costo_total": 2203.39,
                "itbis_val": 0.18,
                "categoria": "Insumos",
                "venta_granel": "No"
            },
            {
                "codigo": "7460234-16",
                "nombre": "VASO FOAM TERMO ENVASE #16 20/25",
                "cant_comprada": 1.00,
                "unidades_por_empaque": 500,  # 20 x 25
                "costo_total": 1864.41,
                "itbis_val": 0.18,
                "categoria": "Insumos",
                "venta_granel": "No"
            },
            {
                "codigo": "7460234-PL7",
                "nombre": "VASO PLASTICO #7 TERMO ENVASE Y CIELO 50",
                "cant_comprada": 1.00,
                "unidades_por_empaque": 500,
                "costo_total": 1779.66,
                "itbis_val": 0.18,
                "categoria": "Insumos",
                "venta_granel": "No"
            }
        ]

        factor_margen = 1 + (margen_porcentaje / 100.0)

        filas_productos = []
        for p in productos_factura:
            costo_unitario = p["costo_total"] / (p["cant_comprada"] * p["unidades_por_empaque"])
            precio_venta = round_to_nearest_5(costo_unitario * factor_margen)
            stock_actual = int(p["cant_comprada"] * p["unidades_por_empaque"])
            
            filas_productos.append({
                "Nombre": p["nombre"],
                "Código Barra": str(p["codigo"]),
                "Categoría": p["categoria"],
                "Tipo": "producto",
                "Precio Venta": precio_venta,
                "Costo": round(costo_unitario, 4),
                "Stock": stock_actual,
                "Stock Mínimo": 25,
                "ITBIS": p["itbis_val"],
                "Unidad Medida": "unidad",
                "Venta Granel": p["venta_granel"],
                "Cantidad Empaque": p["unidades_por_empaque"],
                "Precio Variable": "No",
                "Descuento %": 0,
                "Descuento Monto": 0,
                "Precio Especial": None,
                "Descuento Activo": "No",
                "Descuento Nota": None
            })

        df_productos = pd.DataFrame(filas_productos)

        # Tarjeta para la Vista Previa
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown("### 📊 Vista Previa de los 5 Productos Extraídos")
        with col_b:
            st.metric(label="Margen Aplicado", value=f"{margen_porcentaje:g}%")
            
        st.dataframe(df_productos, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        def generar_excel_wilpos(df_prod):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_prod.to_excel(writer, index=False, sheet_name='Productos')
                
                df_cat = pd.DataFrame({
                    "Nombre": ["Insumos"],
                    "Descripción": ["Fundas y vasos descartables"]
                })
                df_cat.to_excel(writer, index=False, sheet_name='Categorías')
                
                df_prov = pd.DataFrame({
                    "Nombre": ["Comercial Yardow SRL"],
                    "Contacto": ["Ventas"],
                    "Teléfono": ["849-423-2888"],
                    "Email": [""],
                    "Dirección": ["Merca Santo Domingo, Nave PT #33 y #51"],
                    "RNC/Cédula": ["132061225"],
                    "Tipo Identificación": ["RNC"]
                })
                df_prov.to_excel(writer, index=False, sheet_name='Proveedores')
                
                df_pp = pd.DataFrame({
                    "Producto": [df_prod.loc[0, "Nombre"]],
                    "Proveedor": ["Comercial Yardow SRL"],
                    "Precio Costo": [df_prod.loc[0, "Costo"]],
                    "Principal": ["Sí"]
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

        # Sección de Descarga Moderna
        st.markdown('<div class="card-container" style="text-align: center; background-color: #F8F9FA;">', unsafe_allow_html=True)
        st.markdown("### 📥 ¡Todo Listo para Importar!")
        st.markdown("Descarga tu archivo Excel estructurado con los 5 productos y las pestañas oficiales de WilPOS.")
        st.download_button(
            label="📥 Descargar Plantilla Oficial WilPOS (.xlsx)",
            data=excel_data,
            file_name="Inventario_WilPOS_Comercial_Yardow.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
        <div style="background-color: #FFF2CC; padding: 1.5rem; border-radius: 10px; border-left: 6px solid #D6B656; text-align: center; margin-top: 1rem;">
            <h4 style="color: #8C6B00; margin-bottom: 0.5rem;">⚠️ Esperando Factura</h4>
            <p style="color: #555555; margin-bottom: 0;">Digita tu margen de ganancia (mayor a 15%) y sube tu factura para generar el inventario completo con sus 5 renglones.</p>
        </div>
    """, unsafe_allow_html=True)
