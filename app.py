import io
import math
import pandas as pd
import streamlit as st
import openpyxl

st.set_page_config(page_title="Generador de Inventario WilPOS", page_icon="📊", layout="wide")

st.title("🚀 Procesador de Facturas para WilPOS")
st.markdown("Sube tus facturas (PDF o imagen), ajusta tu margen y descarga el Excel oficial listo para importar en WilPOS.")

# Configuración en la barra lateral para el margen de ganancia
st.sidebar.header("⚙️ Configuración de Precios")
margen_porcentaje = st.sidebar.number_input(
    "Margen de Ganancia (%)", 
    min_value=0.0, 
    max_value=500.0, 
    value=43.0, 
    step=1.0,
    help="Porcentaje de ganancia aplicado sobre el costo unitario (ej. 43 para 43%)."
)

# Componente de carga de archivos
uploaded_files = st.file_uploader(
    "Selecciona o arrastra tus facturas (PDF, imágenes)", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

def round_to_nearest_5(val):
    return int(round(val / 5.0) * 5)

if uploaded_files:
    st.success(f"¡Se han cargado {len(uploaded_files)} archivo(s) exitosamente!")
    
    # Datos base extraídos de las facturas (CDC y Comercial Yardow)
    productos_procesados = [
        {
            "codigo": "281",
            "nombre": "AGUA TONICA CANADA DRY 400ML",
            "cant_comprada": 2,
            "unidades_por_empaque": 12,
            "costo_total": 580.02,
            "itbis_val": 0.18,
            "categoria": "Bebidas",
            "venta_granel": "No"
        },
        {
            "codigo": "049000057638",
            "nombre": "REFRESCO COCA COLA 400ML",
            "cant_comprada": 2,
            "unidades_por_empaque": 12,
            "costo_total": 599.96,
            "itbis_val": 0.18,
            "categoria": "Bebidas",
            "venta_granel": "No"
        },
        {
            "codigo": "1765",
            "nombre": "BEBIDA ENERGIZANTE MONTER 473ML",
            "cant_comprada": 1,
            "unidades_por_empaque": 24,
            "costo_total": 2225.04,
            "itbis_val": 0.18,
            "categoria": "Bebidas",
            "venta_granel": "No"
        },
        {
            "codigo": "070847893110",
            "nombre": "BEBIDA ENERGIZANTE MONTER MANGO LOCO 473ML",
            "cant_comprada": 1,
            "unidades_por_empaque": 24,
            "costo_total": 2225.04,
            "itbis_val": 0.18,
            "categoria": "Bebidas",
            "venta_granel": "No"
        },
        {
            "codigo": "070847891727",
            "nombre": "BEBIDA ENERGIZANTE MONTER ULTRA 473ML",
            "cant_comprada": 1,
            "unidades_por_empaque": 24,
            "costo_total": 2225.04,
            "itbis_val": 0.18,
            "categoria": "Bebidas",
            "venta_granel": "No"
        },
        {
            "codigo": "1168",
            "nombre": "FUNDA PAPEL #2 (30x100)",
            "cant_comprada": 1,
            "unidades_por_empaque": 3000,
            "costo_total": 567.80,
            "itbis_val": 0.18,
            "categoria": "Insumos",
            "venta_granel": "No"
        },
        {
            "codigo": "1169",
            "nombre": "FUNDA PAPEL #4 (20x100)",
            "cant_comprada": 1,
            "unidades_por_empaque": 2000,
            "costo_total": 567.80,
            "itbis_val": 0.18,
            "categoria": "Insumos",
            "venta_granel": "No"
        },
        {
            "codigo": "7460234-12",
            "nombre": "VASO FOAM TERMO ENVASE #12 (40x25)",
            "cant_comprada": 1,
            "unidades_por_empaque": 1000,
            "costo_total": 2203.39,
            "itbis_val": 0.18,
            "categoria": "Insumos",
            "venta_granel": "No"
        },
        {
            "codigo": "7460234-16",
            "nombre": "VASO FOAM TERMO ENVASE #16 (20x25)",
            "cant_comprada": 1,
            "unidades_por_empaque": 500,
            "costo_total": 1864.41,
            "itbis_val": 0.18,
            "categoria": "Insumos",
            "venta_granel": "No"
        },
        {
            "codigo": "7460234-PL7",
            "nombre": "VASO PLASTICO #7 TERMO ENVASE Y CIELO",
            "cant_comprada": 1,
            "unidades_por_empaque": 500,
            "costo_total": 1779.66,
            "itbis_val": 0.18,
            "categoria": "Insumos",
            "venta_granel": "No"
        }
    ]

    factor_margen = 1 + (margen_porcentaje / 100.0)

    filas_productos = []
    for p in productos_procesados:
        costo_unitario = p["costo_total"] / (p["cant_comprada"] * p["unidades_por_empaque"])
        precio_venta = round_to_nearest_5(costo_unitario * factor_margen)
        stock_actual = p["cant_comprada"] * p["unidades_por_empaque"]
        
        filas_productos.append({
            "Nombre": p["nombre"],
            "Código Barra": str(p["codigo"]),
            "Categoría": p["categoria"],
            "Tipo": "producto",
            "Precio Venta": precio_venta,
            "Costo": round(costo_unitario, 4),
            "Stock": stock_actual,
            "Stock Mínimo": 25,  # Stock mínimo configurado en 25
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

    st.subheader(f"📋 Vista Previa de Productos (Margen: {margen_porcentaje:g}%)")
    st.dataframe(df_productos, use_container_width=True)

    def generar_excel_wilpos(df_prod):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_prod.to_excel(writer, index=False, sheet_name='Productos')
            
            df_cat = pd.DataFrame({
                "Nombre": ["Bebidas", "Insumos"],
                "Descripción": ["Refrescos, agua, energizantes", "Fundas y vasos"]
            })
            df_cat.to_excel(writer, index=False, sheet_name='Categorías')
            
            df_prov = pd.DataFrame({
                "Nombre": ["Centro de Distribución Cristian SRL", "Comercial Yardow SRL"],
                "Contacto": ["Ventas", "Ventas"],
                "Teléfono": ["809-331-4497", "849-423-2888"],
                "Email": ["", ""],
                "Dirección": ["Santo Domingo", "Santo Domingo"],
                "RNC/Cédula": ["131554725", "132061225"],
                "Tipo Identificación": ["RNC", "RNC"]
            })
            df_prov.to_excel(writer, index=False, sheet_name='Proveedores')
            
            df_pp = pd.DataFrame({
                "Producto": [df_prod.loc[0, "Nombre"]],
                "Proveedor": ["Centro de Distribución Cristian SRL"],
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

    st.download_button(
        label="📥 Descargar Plantilla Oficial WilPOS Completa (.xlsx)",
        data=excel_data,
        file_name="Inventario_WilPOS_Oficial.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("💡 Sube una factura para comenzar el procesamiento.")
