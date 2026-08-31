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
:root{
    --bg:#f8fafc;
    --panel:#ffffff;
    --border:#dfe7f1;
    --text:#0f172a;
    --muted:#64748b;
    --blue:#2563eb;
    --blue2:#1d4ed8;
    --navy:#071a33;
    --navy2:#0b2445;
    --green:#16a34a;
    --orange:#f59e0b;
    --purple:#7c3aed;
    --red:#ef4444;
}

html, body, [class*="css"]{
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stApp{
    background:var(--bg);
    color:var(--text);
}

[data-testid="stHeader"]{
    background:rgba(248,250,252,.92);
    backdrop-filter:blur(8px);
}

.block-container{
    max-width:1320px;
    padding-top:1rem;
    padding-bottom:2rem;
}

/* =============== SIDEBAR =============== */
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,var(--navy) 0%, var(--navy2) 100%);
    border-right:1px solid rgba(255,255,255,.05);
}

[data-testid="stSidebar"] *{
    color:#e5eefb;
}

.side-logo{
    padding:.5rem .15rem .85rem .15rem;
}
.side-logo .brand{
    display:flex;
    align-items:center;
    gap:.65rem;
}
.side-logo .mark{
    width:38px;
    height:38px;
    border-radius:10px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:linear-gradient(135deg,#3b82f6,#2563eb);
    color:white;
    font-size:1.2rem;
    box-shadow:0 7px 18px rgba(37,99,235,.25);
}
.side-logo .name{
    font-size:1.22rem;
    font-weight:850;
    line-height:1;
    color:#fff;
}
.side-logo .sub{
    color:#60a5fa;
    font-size:.67rem;
    font-weight:800;
    margin-top:.18rem;
    letter-spacing:.08em;
}

[data-testid="stSidebar"] .stRadio > label{
    display:none;
}
[data-testid="stSidebar"] [role="radiogroup"]{
    gap:.18rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label{
    width:100%;
    padding:.48rem .55rem !important;
    border-radius:8px;
    border:1px solid transparent;
    transition:.15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{
    background:rgba(255,255,255,.07);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
    background:#1d4ed8 !important;
    border-color:#2563eb !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child{
    display:none !important;
}
[data-testid="stSidebar"] [role="radiogroup"] p{
    font-size:.82rem;
    font-weight:650;
}

.side-summary{
    margin-top:1rem;
    padding:.78rem;
    border-radius:12px;
    background:rgba(255,255,255,.045);
    border:1px solid rgba(255,255,255,.08);
}
.side-summary .s-title{
    font-size:.68rem;
    font-weight:800;
    color:#94a3b8 !important;
    margin-bottom:.45rem;
    letter-spacing:.08em;
}
.side-summary .row{
    display:flex;
    justify-content:space-between;
    gap:.6rem;
    padding:.34rem 0;
    border-bottom:1px solid rgba(255,255,255,.05);
    font-size:.75rem;
}
.side-summary .row:last-child{
    border-bottom:none;
}
.side-summary .row span{
    color:#cbd5e1 !important;
}
.side-summary .num{
    color:#fff !important;
    font-weight:800;
}

/* =============== TOPBAR =============== */
.top-actions{
    display:flex;
    align-items:center;
    justify-content:flex-end;
    gap:.45rem;
    margin-bottom:.55rem;
}

.top-icon{
    width:34px;
    height:34px;
    border-radius:10px;
    border:1px solid #dbe3ef;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#fff;
    color:#475569;
    font-size:.9rem;
}

/* =============== HERO =============== */
.hero-grid{
    display:grid;
    grid-template-columns:minmax(0,1.65fr) minmax(320px,1fr);
    gap:1rem;
    margin-bottom:1rem;
}

.hero-card{
    position:relative;
    overflow:hidden;
    min-height:185px;
    background:linear-gradient(135deg,#ffffff 0%,#f8fbff 100%);
    border:1px solid var(--border);
    border-radius:14px;
    padding:1.35rem 1.4rem;
    box-shadow:0 6px 18px rgba(15,23,42,.045);
}

.hero-card h1{
    margin:0 0 .45rem 0;
    font-size:2rem;
    letter-spacing:-.04em;
}
.hero-card .subtitle{
    font-size:1rem;
    color:#0f172a;
    margin-bottom:.8rem;
}
.hero-card p{
    color:var(--muted);
    margin:.2rem 0;
    font-size:.88rem;
    line-height:1.55;
    max-width:560px;
}
.hero-visual{
    position:absolute;
    right:1.15rem;
    top:1.1rem;
    width:220px;
    height:145px;
    opacity:.95;
}
.hero-visual .phone{
    position:absolute;
    left:28px;
    top:10px;
    width:62px;
    height:110px;
    border:5px solid #0f2a4d;
    border-radius:13px;
    background:white;
}
.hero-visual .phone:before{
    content:"";
    position:absolute;
    left:16px;
    top:12px;
    width:20px;
    height:4px;
    background:#cbd5e1;
    border-radius:5px;
}
.hero-visual .phone:after{
    content:"";
    position:absolute;
    left:14px;
    bottom:16px;
    width:28px;
    height:7px;
    background:#2563eb;
    border-radius:2px;
}
.hero-visual .sheet{
    position:absolute;
    right:22px;
    top:13px;
    width:96px;
    height:116px;
    background:linear-gradient(180deg,#e8f0ff,#dbeafe);
    border-radius:9px;
    transform:rotate(2deg);
}
.hero-visual .sheet:before,
.hero-visual .sheet:after{
    content:"";
    position:absolute;
    left:18px;
    width:56px;
    height:8px;
    background:#b7cdfc;
    border-radius:4px;
}
.hero-visual .sheet:before{top:26px;}
.hero-visual .sheet:after{top:44px;}

/* =============== STATS =============== */
.stats-card{
    background:#fff;
    border:1px solid var(--border);
    border-radius:14px;
    padding:.95rem;
    box-shadow:0 6px 18px rgba(15,23,42,.045);
}
.stats-title{
    font-weight:800;
    font-size:.88rem;
    margin-bottom:.6rem;
}
.stats-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:.55rem;
}
.stat{
    position:relative;
    border:1px solid #dce5f0;
    border-radius:10px;
    padding:.7rem .75rem;
    min-height:72px;
}
.stat .label{
    font-size:.69rem;
    color:#64748b;
    font-weight:700;
}
.stat .value{
    margin-top:.15rem;
    font-size:1.15rem;
    font-weight:850;
}
.stat.blue{background:#f7faff;border-color:#bfdbfe;}
.stat.purple{background:#faf7ff;border-color:#ddd6fe;}
.stat.orange{background:#fffbeb;border-color:#fde68a;}
.stat.green{background:#f0fdf4;border-color:#bbf7d0;}
.stat.blue .value{color:#2563eb;}
.stat.purple .value{color:#7c3aed;}
.stat.orange .value{color:#d97706;}
.stat.green .value{color:#15803d;}
.stat-icon{
    position:absolute;
    right:.65rem;
    top:.65rem;
    width:32px;
    height:32px;
    border-radius:9px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:rgba(255,255,255,.8);
}
.stats-link{
    margin-top:.55rem;
    padding:.42rem;
    border-radius:8px;
    background:#eef4ff;
    color:#2563eb;
    font-size:.72rem;
    font-weight:700;
    text-align:center;
}

/* =============== MAIN CARDS =============== */
.main-card{
    background:#fff;
    border:1px solid var(--border);
    border-radius:14px;
    box-shadow:0 6px 18px rgba(15,23,42,.04);
    margin-bottom:1rem;
    overflow:hidden;
}
.main-card-header{
    padding:.85rem 1rem .65rem 1rem;
    font-size:.92rem;
    font-weight:850;
}
.main-card-body{
    padding:.9rem 1rem 1rem 1rem;
}

.upload-grid{
    display:grid;
    grid-template-columns:1.15fr .55fr;
    gap:0;
}
.upload-zone{
    padding:.9rem 1rem;
    border-right:1px solid #e5e7eb;
}
.margin-zone{
    padding:.9rem 1rem;
}

.fake-upload{
    border:1px dashed #cbd5e1;
    border-radius:10px;
    min-height:116px;
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    overflow:hidden;
    background:#fbfdff;
}
.fake-upload-item{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    gap:.28rem;
    border-right:1px solid #eef2f7;
    padding:.75rem;
}
.fake-upload-item:last-child{
    border-right:none;
}
.fake-upload-item.active{
    background:#f7faff;
    outline:1px solid #bfdbfe;
    outline-offset:-1px;
}
.fake-upload-icon{
    width:36px;
    height:36px;
    border-radius:9px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#eef4ff;
    color:#2563eb;
    font-size:1rem;
}
.fake-upload-title{
    color:#2563eb;
    font-size:.75rem;
    font-weight:750;
}
.fake-upload-sub{
    font-size:.67rem;
    color:#64748b;
}

.upload-foot{
    margin-top:.45rem;
    color:#94a3b8;
    font-size:.66rem;
}

/* actual uploader */
div[data-testid="stFileUploader"]{
    border:1px solid #e2e8f0;
    border-radius:10px;
    background:#fff;
    padding:.25rem;
}
div[data-testid="stFileUploader"] section{
    padding:.55rem !important;
}
div[data-testid="stCameraInput"]{
    border-radius:10px;
}

.file-strip{
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:.55rem;
    margin:.45rem 0 .75rem 0;
}
.file-chip{
    border:1px solid #dfe7f1;
    border-radius:9px;
    background:#fff;
    padding:.55rem .65rem;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:.5rem;
    min-height:54px;
}
.file-chip .file-name{
    font-size:.72rem;
    font-weight:700;
    color:#0f172a;
    overflow:hidden;
    text-overflow:ellipsis;
    white-space:nowrap;
}
.file-chip .file-meta{
    font-size:.62rem;
    color:#64748b;
}
.ok{
    color:#16a34a;
    font-weight:850;
}

.process-wrap{
    display:flex;
    justify-content:center;
    margin-top:.6rem;
}
.process-note{
    text-align:center;
    font-size:.68rem;
    color:#dbeafe;
}

/* =============== INVENTORY =============== */
.inventory-card{
    background:#fff;
    border:1px solid var(--border);
    border-radius:14px;
    box-shadow:0 6px 18px rgba(15,23,42,.04);
    padding:.8rem .9rem .9rem .9rem;
    margin-top:.7rem;
}
.inventory-head{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:.6rem;
    margin-bottom:.55rem;
}
.inventory-title{
    display:flex;
    align-items:center;
    gap:.45rem;
    font-size:.9rem;
    font-weight:850;
}
.badge{
    padding:.2rem .45rem;
    border-radius:999px;
    background:#ecfdf5;
    color:#15803d;
    font-size:.65rem;
    font-weight:750;
}

/* =============== STREAMLIT CONTROLS =============== */
.stButton>button,
.stDownloadButton>button{
    border-radius:8px;
    min-height:38px;
    font-weight:750;
}
.stButton>button[kind="primary"]{
    background:linear-gradient(180deg,#2563eb,#1d4ed8);
    border-color:#1d4ed8;
}
div[data-testid="stDataFrame"]{
    border:1px solid #e2e8f0;
    border-radius:9px;
    overflow:hidden;
}
div[data-testid="stNumberInput"] input{
    border-radius:8px;
}

#MainMenu{visibility:hidden;}
footer{visibility:hidden;}

@media (max-width: 980px){
    .hero-grid{grid-template-columns:1fr;}
    .hero-visual{display:none;}
    .upload-grid{grid-template-columns:1fr;}
    .upload-zone{border-right:none;border-bottom:1px solid #e5e7eb;}
}

@media (max-width: 720px){
    .block-container{
        padding-left:.65rem;
        padding-right:.65rem;
        padding-top:.7rem;
    }
    .stats-grid{grid-template-columns:1fr 1fr;}
    .fake-upload{grid-template-columns:1fr;}
    .fake-upload-item{
        border-right:none;
        border-bottom:1px solid #eef2f7;
    }
    .fake-upload-item:last-child{border-bottom:none;}
    .file-strip{grid-template-columns:1fr;}
    .hero-card h1{font-size:1.65rem;}
}

/* Componentes utilizados por las páginas internas */
.section-card{
    background:#fff;
    border:1px solid var(--border);
    border-radius:14px;
    padding:1rem;
    margin-bottom:.85rem;
    box-shadow:0 5px 16px rgba(15,23,42,.035);
}

.file-card{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:.8rem;
    padding:.72rem .8rem;
    margin:.45rem 0;
    border:1px solid #e2e8f0;
    border-radius:9px;
    background:#fff;
}

.file-card .file-name{
    font-size:.78rem;
    font-weight:750;
    color:#0f172a;
}

.file-card .meta{
    margin-top:.15rem;
    color:#64748b;
    font-size:.68rem;
}

.bad{
    color:#dc2626;
    font-size:.7rem;
    font-weight:800;
    white-space:nowrap;
}

.info-strip{
    padding:.7rem .8rem;
    background:#eff6ff;
    border:1px solid #bfdbfe;
    color:#1e40af;
    border-radius:9px;
    font-size:.75rem;
    line-height:1.45;
}

.empty-state{
    padding:2rem 1rem;
    border:1px dashed #cbd5e1;
    border-radius:12px;
    background:#fbfdff;
    color:#64748b;
    text-align:center;
}

.empty-state .big{
    font-size:2rem;
    margin-bottom:.4rem;
}


/* ===== Ajuste de presentación final ===== */
.block-container{
    width:100% !important;
    max-width:1280px !important;
    margin:0 auto !important;
    padding-top:.65rem !important;
    padding-left:1rem !important;
    padding-right:1rem !important;
    padding-bottom:1.4rem !important;
}

.hero-grid{
    grid-template-columns:minmax(0,1.55fr) minmax(320px,.95fr) !important;
    gap:.8rem !important;
    margin-bottom:.75rem !important;
}

.hero-card{
    min-height:150px !important;
    padding:1rem 1.15rem !important;
}

.hero-card h1{
    font-size:1.7rem !important;
    margin-bottom:.25rem !important;
}

.hero-card .subtitle{
    font-size:.9rem !important;
    margin-bottom:.45rem !important;
}

.hero-card p{
    font-size:.8rem !important;
    line-height:1.4 !important;
}

.hero-visual{
    transform:scale(.76) !important;
    transform-origin:right top !important;
    right:.4rem !important;
    top:.45rem !important;
}

.stats-card{
    padding:.72rem !important;
}

.stats-grid{
    gap:.38rem !important;
}

.stat{
    min-height:58px !important;
    padding:.48rem .55rem !important;
}

.stat .label{
    font-size:.64rem !important;
}

.stat .value{
    font-size:.95rem !important;
}

.stat-icon{
    width:28px !important;
    height:28px !important;
    font-size:.8rem !important;
}

.section-card,
.main-card,
.inventory-card{
    margin-bottom:.7rem !important;
}

.section-card{
    padding:.8rem !important;
}

.stButton>button,
.stDownloadButton>button{
    min-height:36px !important;
}

[data-testid="stSidebar"]{
    min-width:205px !important;
    max-width:205px !important;
}

@media (min-width: 1500px){
    .block-container{
        max-width:1360px !important;
    }
}

@media (max-width: 1100px){
    .block-container{
        max-width:100% !important;
        padding-left:.75rem !important;
        padding-right:.75rem !important;
    }
    .hero-grid{
        grid-template-columns:1fr !important;
    }
    .hero-visual{
        display:none !important;
    }
}

@media (max-width: 720px){
    .block-container{
        padding:.5rem !important;
    }
    .stats-grid{
        grid-template-columns:1fr 1fr !important;
    }
    .hero-card{
        min-height:0 !important;
    }
}


/* ===== FIX DEFINITIVO: contenido debajo de la barra de Streamlit ===== */

/* Streamlit puede usar cualquiera de estos dos contenedores según versión */
.block-container,
[data-testid="stMainBlockContainer"]{
    width:100% !important;
    max-width:1280px !important;
    margin:0 auto !important;

    /* IMPORTANTE: evita que el header flotante tape el dashboard */
    padding-top:4.25rem !important;
    padding-left:1rem !important;
    padding-right:1rem !important;
    padding-bottom:1.5rem !important;

    box-sizing:border-box !important;
}

/* Mantiene visible la barra de Streamlit sin superponer el contenido */
[data-testid="stHeader"]{
    height:3.25rem !important;
    background:rgba(248,250,252,.96) !important;
    backdrop-filter:blur(10px);
}

/* El área principal no debe recortar las tarjetas */
[data-testid="stAppViewContainer"],
[data-testid="stMain"]{
    overflow-x:hidden !important;
}

/* Sidebar alineado con el inicio visual */
[data-testid="stSidebar"] > div:first-child{
    padding-top:1rem !important;
}

/* Desktop grande */
@media (min-width:1500px){
    .block-container,
    [data-testid="stMainBlockContainer"]{
        max-width:1360px !important;
        padding-top:4.1rem !important;
    }
}

/* Laptop / desktop mediano */
@media (max-width:1100px){
    .block-container,
    [data-testid="stMainBlockContainer"]{
        max-width:100% !important;
        padding-top:4rem !important;
        padding-left:.8rem !important;
        padding-right:.8rem !important;
    }

    .hero-grid{
        grid-template-columns:1fr !important;
    }

    .hero-visual{
        display:none !important;
    }
}

/* Móvil */
@media (max-width:720px){
    .block-container,
    [data-testid="stMainBlockContainer"]{
        width:100% !important;
        max-width:100% !important;
        padding-top:3.75rem !important;
        padding-left:.55rem !important;
        padding-right:.55rem !important;
        padding-bottom:1rem !important;
    }

    .stats-grid{
        grid-template-columns:1fr 1fr !important;
    }

    .hero-card{
        min-height:0 !important;
    }
}


/* ===== AJUSTE DE ANCHO FINAL ===== */

/* Desktop: aprovechar casi todo el ancho disponible */
.block-container,
[data-testid="stMainBlockContainer"]{
    width:calc(100% - 2rem) !important;
    max-width:none !important;
    margin:0 auto !important;
    padding-left:.75rem !important;
    padding-right:.75rem !important;
    box-sizing:border-box !important;
}

/* Cuando el sidebar está abierto, el main debe usar todo su espacio restante */
[data-testid="stAppViewContainer"] main{
    width:100% !important;
    max-width:none !important;
}

/* El contenido interno tampoco debe volver a limitarse */
[data-testid="stMain"] > div{
    width:100% !important;
    max-width:none !important;
}

/* Mantener tarjetas proporcionadas en pantallas anchas */
.hero-grid{
    width:100% !important;
    grid-template-columns:minmax(0,1.65fr) minmax(360px,.9fr) !important;
}

.main-card,
.inventory-card,
.section-card{
    width:100% !important;
    box-sizing:border-box !important;
}

/* Pantallas muy grandes: dejar un margen visual mínimo */
@media (min-width:1800px){
    .block-container,
    [data-testid="stMainBlockContainer"]{
        width:calc(100% - 3rem) !important;
    }
}

/* Laptop */
@media (max-width:1200px){
    .block-container,
    [data-testid="stMainBlockContainer"]{
        width:calc(100% - 1rem) !important;
        padding-left:.5rem !important;
        padding-right:.5rem !important;
    }
}

/* Tablet / móvil */
@media (max-width:900px){
    .block-container,
    [data-testid="stMainBlockContainer"]{
        width:100% !important;
        padding-left:.55rem !important;
        padding-right:.55rem !important;
    }

    .hero-grid{
        grid-template-columns:1fr !important;
    }
}


/* ===== FIX CONTRASTE DE BOTONES ===== */

/* Botones primarios azules: texto e iconos siempre blancos */
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"]{
    background:linear-gradient(180deg,#2563eb,#1d4ed8) !important;
    border-color:#1d4ed8 !important;
    color:#ffffff !important;
}

.stButton > button[kind="primary"] *,
.stDownloadButton > button[kind="primary"] *{
    color:#ffffff !important;
    fill:#ffffff !important;
}

/* Botones secundarios normales: texto oscuro */
.stButton > button:not([kind="primary"]),
.stDownloadButton > button:not([kind="primary"]){
    color:#0f172a !important;
}

.stButton > button:not([kind="primary"]) *,
.stDownloadButton > button:not([kind="primary"]) *{
    color:#0f172a !important;
}

/* El botón blanco del sidebar estaba heredando texto claro del menú */
[data-testid="stSidebar"] .stButton > button{
    background:#ffffff !important;
    border:1px solid #dbe3ef !important;
    color:#0f172a !important;
}

[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span{
    color:#0f172a !important;
}

/* Hover */
[data-testid="stSidebar"] .stButton > button:hover{
    background:#f8fafc !important;
    color:#0f172a !important;
    border-color:#cbd5e1 !important;
}

/* Asegura contraste del botón principal aunque Streamlit cambie el DOM interno */
button[data-testid="stBaseButton-primary"]{
    color:#ffffff !important;
}

button[data-testid="stBaseButton-primary"] *{
    color:#ffffff !important;
}

button[data-testid="stBaseButton-secondary"]{
    color:#0f172a !important;
}

button[data-testid="stBaseButton-secondary"] *{
    color:#0f172a !important;
}


/* ===== POPUP / DIALOG CENTRADO ===== */

/* Dialog nativo de Streamlit */
div[data-testid="stDialog"]{
    align-items:center !important;
    justify-content:center !important;
}

div[data-testid="stDialog"] > div{
    margin:auto !important;
}

/* Compatibilidad con versiones que usan role=dialog */
div[role="dialog"]{
    margin:auto !important;
}

/* Contenedor visual del popup */
div[data-testid="stDialog"] div[data-testid="stVerticalBlock"]{
    margin-left:auto !important;
    margin-right:auto !important;
}

/* En desktop, ancho cómodo y centrado */
@media (min-width:721px){
    div[data-testid="stDialog"] > div,
    div[role="dialog"]{
        width:min(520px, calc(100vw - 3rem)) !important;
        max-width:520px !important;
    }
}

/* En móvil mantiene márgenes seguros */
@media (max-width:720px){
    div[data-testid="stDialog"] > div,
    div[role="dialog"]{
        width:calc(100vw - 1.25rem) !important;
        max-width:calc(100vw - 1.25rem) !important;
        margin-left:auto !important;
        margin-right:auto !important;
    }
}


/* ===== TIPOGRAFÍA MÁS LEGIBLE ===== */

/* Texto general de la aplicación */
.stApp{
    font-size:16px !important;
}

p, label, li,
[data-testid="stMarkdownContainer"] p{
    font-size:.94rem !important;
    line-height:1.5 !important;
}

/* Sidebar */
[data-testid="stSidebar"] [role="radiogroup"] p{
    font-size:.91rem !important;
    font-weight:650 !important;
}

.side-summary .s-title{
    font-size:.75rem !important;
}

.side-summary .row{
    font-size:.83rem !important;
}

/* Bienvenida */
.hero-card h1{
    font-size:1.95rem !important;
}

.hero-card .subtitle{
    font-size:1rem !important;
}

.hero-card p{
    font-size:.9rem !important;
}

/* Estadísticas */
.stats-title{
    font-size:.96rem !important;
}

.stat .label{
    font-size:.75rem !important;
}

.stat .value{
    font-size:1.1rem !important;
}

.stats-link{
    font-size:.78rem !important;
}

/* Formularios */
[data-testid="stWidgetLabel"] p,
.stRadio label p,
.stCheckbox label p{
    font-size:.9rem !important;
}

input,
textarea{
    font-size:.92rem !important;
}

/* Botones */
.stButton > button,
.stDownloadButton > button{
    font-size:.92rem !important;
    font-weight:750 !important;
    min-height:40px !important;
}

.stButton > button p,
.stDownloadButton > button p{
    font-size:.92rem !important;
    font-weight:750 !important;
}

/* Títulos y tarjetas */
.main-card-header{
    font-size:1rem !important;
}

.inventory-title{
    font-size:1rem !important;
}

.file-card .file-name{
    font-size:.84rem !important;
}

.file-card .meta,
.upload-foot,
.fake-upload-sub{
    font-size:.75rem !important;
}

.fake-upload-title{
    font-size:.83rem !important;
}

/* Tablas */
[data-testid="stDataFrame"]{
    font-size:.86rem !important;
}

/* Móvil: evitar que todo se vuelva excesivamente grande */
@media (max-width:720px){
    .stApp{
        font-size:15px !important;
    }

    .hero-card h1{
        font-size:1.65rem !important;
    }

    .stButton > button,
    .stDownloadButton > button{
        font-size:.88rem !important;
    }
}


/* ===== NUEVO SELECTOR DE CARGA: BOTONES REALES ===== */

.load-title{
    font-size:1.02rem;
    font-weight:850;
    color:#0f172a;
    margin:0 0 .65rem 0;
}

.mode-icon{
    height:54px;
    display:flex;
    align-items:center;
    justify-content:center;
    margin:0;
    border:1px solid #dbe5f0;
    border-bottom:none;
    border-radius:12px 12px 0 0;
    background:linear-gradient(180deg,#fbfdff 0%,#f4f8ff 100%);
    font-size:1.7rem;
}

.mode-caption{
    min-height:34px;
    display:flex;
    align-items:flex-start;
    justify-content:center;
    text-align:center;
    padding:.35rem .35rem .2rem;
    color:#64748b;
    font-size:.72rem;
    line-height:1.25;
    border-left:1px solid #dbe5f0;
    border-right:1px solid #dbe5f0;
    border-bottom:1px solid #dbe5f0;
    border-radius:0 0 12px 12px;
    background:#fff;
    margin-top:-.05rem;
}

/* Botones del selector principal */
[data-testid="stMain"] .stButton > button{
    border-radius:0 !important;
    min-height:43px !important;
    margin:0 !important;
    font-size:.88rem !important;
    font-weight:800 !important;
}

/* El botón seleccionado forma parte visual de la tarjeta */
[data-testid="stMain"] button[data-testid="stBaseButton-primary"]{
    background:#2563eb !important;
    border-color:#2563eb !important;
    color:#fff !important;
}
[data-testid="stMain"] button[data-testid="stBaseButton-primary"] *{
    color:#fff !important;
}

/* Botones no seleccionados */
[data-testid="stMain"] button[data-testid="stBaseButton-secondary"]{
    background:#fff !important;
    border-color:#dbe5f0 !important;
    color:#1d4ed8 !important;
}
[data-testid="stMain"] button[data-testid="stBaseButton-secondary"] *{
    color:#1d4ed8 !important;
}

.load-supported{
    margin:.5rem 0 .5rem 0;
    color:#94a3b8;
    font-size:.68rem;
}

/* Uploader real */
[data-testid="stMain"] div[data-testid="stFileUploader"]{
    width:100% !important;
    max-width:none !important;
    margin-top:.35rem !important;
}
[data-testid="stMain"] div[data-testid="stFileUploader"] section{
    width:100% !important;
    min-height:94px !important;
    display:flex !important;
    align-items:center !important;
    border:1.5px dashed #cbd5e1 !important;
    border-radius:12px !important;
    background:#fbfdff !important;
    box-sizing:border-box !important;
}

/* Cámara real */
[data-testid="stMain"] div[data-testid="stCameraInput"]{
    width:100% !important;
    max-width:none !important;
    margin-top:.35rem !important;
}

/* Margen */
.margin-heading{
    font-size:.84rem;
    font-weight:800;
    color:#0f172a;
    margin:.1rem 0 .55rem 0;
}

[data-testid="stMain"] div[data-testid="stNumberInput"] input{
    min-height:44px !important;
    font-size:.92rem !important;
    background:#fff !important;
}

.margin-status{
    min-height:44px;
    margin-top:.65rem;
    padding:.65rem .75rem;
    border-radius:9px;
    display:flex;
    align-items:center;
    font-size:.75rem;
    font-weight:650;
}
.ok-status{
    background:#f0fdf4;
    border:1px solid #bbf7d0;
    color:#15803d;
}
.warn-status{
    background:#fff7ed;
    border:1px solid #fed7aa;
    color:#c2410c;
}

/* No afectar botones del sidebar */
[data-testid="stSidebar"] .stButton > button{
    border-radius:8px !important;
}

/* Móvil */
@media (max-width:800px){
    .mode-icon{
        height:48px;
        font-size:1.5rem;
    }
    .mode-caption{
        min-height:36px;
        font-size:.68rem;
    }
}

@media (max-width:640px){
    .mode-icon{
        height:44px;
        font-size:1.35rem;
    }
    [data-testid="stMain"] .stButton > button{
        font-size:.78rem !important;
        min-height:40px !important;
    }
    .mode-caption{
        font-size:.64rem;
        min-height:40px;
    }
}


/* ===== SIDEBAR FINAL: SIN CÍRCULOS, ALINEACIÓN LIMPIA ===== */

/* Oculta por completo los controles circulares del radio en el sidebar */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label > div:first-child{
    display:none !important;
}

/* Menú vertical compacto */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"]{
    display:flex !important;
    flex-direction:column !important;
    gap:.28rem !important;
    width:100% !important;
}

/* Cada opción del menú */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label{
    width:100% !important;
    min-height:42px !important;
    padding:.58rem .72rem !important;
    margin:0 !important;

    display:flex !important;
    align-items:center !important;
    justify-content:flex-start !important;

    border:1px solid transparent !important;
    border-radius:8px !important;
    background:transparent !important;
    box-shadow:none !important;

    cursor:pointer !important;
    transition:background .15s ease,border-color .15s ease !important;
}

/* Texto/icono */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label p{
    margin:0 !important;
    width:100% !important;
    text-align:left !important;

    color:#e5eefb !important;
    font-size:.92rem !important;
    font-weight:650 !important;
    line-height:1.35 !important;
}

/* Hover */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:hover{
    background:rgba(255,255,255,.07) !important;
    border-color:rgba(255,255,255,.05) !important;
}

/* Opción activa */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked){
    background:#2563eb !important;
    border-color:#3b82f6 !important;
    box-shadow:0 5px 14px rgba(37,99,235,.20) !important;
}

[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p{
    color:#ffffff !important;
    font-weight:800 !important;
}

/* Evita cualquier pseudo-icono residual */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label::before,
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label::after{
    display:none !important;
    content:none !important;
}


/* ===== SIDEBAR: OPCIONES EN UNA SOLA LÍNEA ===== */

/* Aprovechar todo el ancho disponible */
[data-testid="stSidebar"] div[data-testid="stRadio"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"]{
    width:100% !important;
    max-width:none !important;
}

/* Ocultar el indicador circular nativo de forma más amplia */
[data-testid="stSidebar"] div[data-testid="stRadio"] input[type="radio"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radio"] > div:first-child{
    display:none !important;
}

/* Fila compacta */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label{
    width:100% !important;
    min-width:0 !important;
    min-height:40px !important;
    padding:.52rem .55rem !important;
    display:flex !important;
    flex-direction:row !important;
    align-items:center !important;
    justify-content:flex-start !important;
    box-sizing:border-box !important;
}

/* Texto + emoji siempre en una sola línea */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label p,
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label [data-testid="stMarkdownContainer"]{
    width:auto !important;
    max-width:100% !important;
    margin:0 !important;
    padding:0 !important;
    white-space:nowrap !important;
    word-break:keep-all !important;
    overflow-wrap:normal !important;
    line-height:1.2 !important;
    font-size:.86rem !important;
}

/* Evitar que contenedores internos fuercen ancho pequeño */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label > div{
    width:auto !important;
    min-width:0 !important;
    flex:0 1 auto !important;
}


/* ===== SIDEBAR DEFINITIVO ===== */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"]{
    width:100% !important;
    display:flex !important;
    flex-direction:column !important;
    gap:.28rem !important;
}

/* Ocultar TODOS los elementos visuales del radio salvo el texto */
[data-testid="stSidebar"] div[data-testid="stRadio"] input,
[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child,
[data-testid="stSidebar"] div[data-testid="stRadio"] label [data-testid="stRadio"]{
    position:absolute !important;
    opacity:0 !important;
    width:0 !important;
    height:0 !important;
    min-width:0 !important;
    padding:0 !important;
    margin:0 !important;
    overflow:hidden !important;
}

/* Opción completa */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label{
    width:100% !important;
    max-width:100% !important;
    min-height:42px !important;
    padding:.58rem .7rem !important;
    margin:0 !important;
    box-sizing:border-box !important;
    display:block !important;
    border-radius:8px !important;
    border:1px solid transparent !important;
    background:transparent !important;
}

/* Contenedor del texto */
[data-testid="stSidebar"] div[data-testid="stRadio"] label [data-testid="stMarkdownContainer"]{
    display:block !important;
    width:100% !important;
    max-width:none !important;
    overflow:visible !important;
}

/* Una sola línea */
[data-testid="stSidebar"] div[data-testid="stRadio"] label p{
    display:block !important;
    width:100% !important;
    max-width:none !important;
    margin:0 !important;
    padding:0 !important;
    white-space:nowrap !important;
    word-break:normal !important;
    overflow-wrap:normal !important;
    overflow:visible !important;
    text-overflow:clip !important;
    font-size:.84rem !important;
    line-height:1.25 !important;
    font-weight:700 !important;
    color:#f8fafc !important;
}

/* Selección */
[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked){
    background:#2563eb !important;
    border-color:#3b82f6 !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p{
    color:#fff !important;
}

/* Hover */
[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover{
    background:rgba(255,255,255,.07) !important;
}

/* Nada de pseudo-círculos */
[data-testid="stSidebar"] div[data-testid="stRadio"] label::before,
[data-testid="stSidebar"] div[data-testid="stRadio"] label::after{
    content:none !important;
    display:none !important;
}




/* ===== AJUSTE FINAL SIDEBAR + UPLOADER ===== */

/* Sidebar un poco más ancho para que todas las opciones entren completas */
[data-testid="stSidebar"]{
    width:250px !important;
    min-width:250px !important;
    max-width:250px !important;
}

[data-testid="stSidebar"] > div:first-child{
    width:250px !important;
    min-width:250px !important;
    max-width:250px !important;
    box-sizing:border-box !important;
}

/* Texto de navegación siempre completo, en una sola línea */
[data-testid="stSidebar"] div[data-testid="stRadio"] label p{
    white-space:nowrap !important;
    overflow:visible !important;
    text-overflow:clip !important;
    font-size:.84rem !important;
}

/* =========================================================
   FILE UPLOADER
   El texto personalizado SOLO afecta el botón del dropzone.
   No afecta archivos cargados, X de eliminar ni botón +.
   ========================================================= */
[data-testid="stMain"]
[data-testid="stFileUploader"]
section button{
    min-width:150px !important;
}

/* Oculta solo el texto interno del botón de selección */
[data-testid="stMain"]
[data-testid="stFileUploader"]
section button p{
    font-size:0 !important;
}

/* Sustituye visualmente Upload/Browse files por Cargar Archivo */
[data-testid="stMain"]
[data-testid="stFileUploader"]
section button p::after{
    content:"⬆  Cargar Archivo" !important;
    display:inline-block !important;
    font-size:.88rem !important;
    font-weight:750 !important;
    color:#2563eb !important;
    white-space:nowrap !important;
}

/* Los botones de cada archivo cargado conservan su apariencia nativa */
[data-testid="stMain"]
[data-testid="stFileUploader"]
button:not(section button){
    font-size:inherit !important;
    min-width:auto !important;
}

/* Pantallas pequeñas: sidebar vuelve al comportamiento responsivo de Streamlit */
@media (max-width:900px){
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child{
        width:auto !important;
        min-width:0 !important;
        max-width:none !important;
    }
}


/* ===== ANIMACIÓN SUAVE DEL ICONO PRINCIPAL ===== */
.hero-visual{
    isolation:isolate;
}

.hero-visual::before{
    content:"";
    position:absolute;
    left:18px;
    top:1px;
    width:155px;
    height:135px;
    border-radius:50%;
    background:radial-gradient(circle, rgba(37,99,235,.14) 0%, rgba(96,165,250,.07) 42%, rgba(255,255,255,0) 72%);
    animation:wilposAura 3.8s ease-in-out infinite;
    z-index:-1;
}

.hero-visual::after{
    content:"✦";
    position:absolute;
    right:8px;
    top:3px;
    color:#93c5fd;
    font-size:1rem;
    opacity:.45;
    animation:wilposSpark 2.6s ease-in-out infinite;
}

.hero-visual .phone{
    animation:wilposFloat 3.4s ease-in-out infinite;
    transform-origin:center;
}

.hero-visual .sheet{
    animation:wilposSheet 4.1s ease-in-out infinite;
    transform-origin:center;
}

@keyframes wilposFloat{
    0%,100%{ transform:translateY(0) rotate(0deg); }
    50%{ transform:translateY(-7px) rotate(-1deg); }
}

@keyframes wilposSheet{
    0%,100%{ transform:translateY(0) rotate(2deg); }
    50%{ transform:translateY(4px) rotate(3.5deg); }
}

@keyframes wilposAura{
    0%,100%{ transform:scale(.92); opacity:.45; }
    50%{ transform:scale(1.08); opacity:.9; }
}

@keyframes wilposSpark{
    0%,100%{ transform:translateY(2px) scale(.8) rotate(0deg); opacity:.25; }
    50%{ transform:translateY(-7px) scale(1.15) rotate(18deg); opacity:.85; }
}

@media (prefers-reduced-motion: reduce){
    .hero-visual::before,
    .hero-visual::after,
    .hero-visual .phone,
    .hero-visual .sheet{
        animation:none !important;
    }
}

/* Diálogo de vista previa */
div[data-testid="stDialog"] img{
    max-height:68vh !important;
    object-fit:contain !important;
}

@media (max-width:900px){
    .preview-file-card{
        min-height:170px;
    }
}

@media (max-width:640px){
    .preview-file-card{
        min-height:0;
    }
}


/* ===== ARCHIVOS CARGADOS: COMPACTOS, SIN PREVIEW AUTOMÁTICO ===== */
.uploaded-preview-title{
    margin:.65rem 0 .45rem 0;
    font-size:.92rem;
    font-weight:850;
    color:#0f172a;
}

.file-click-card-head{
    min-height:76px;
    display:flex;
    align-items:center;
    gap:.7rem;
    padding:.7rem .75rem .4rem;
    border:1px solid #dbe5f0;
    border-bottom:none;
    border-radius:11px 11px 0 0;
    background:#fff;
}

.file-click-icon{
    width:40px;
    height:40px;
    flex:0 0 40px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:9px;
    background:#f1f5f9;
    font-size:1.3rem;
}

.file-click-info{
    min-width:0;
    flex:1;
}

.file-click-name{
    color:#0f172a;
    font-size:.76rem;
    font-weight:780;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.file-click-meta{
    margin-top:.15rem;
    color:#64748b;
    font-size:.66rem;
}

/* Botón unido visualmente a la tarjeta */
[data-testid="stMain"] .file-click-card-head + div .stButton > button,
[data-testid="stMain"] .file-click-card-head + div button{
    border-radius:0 0 11px 11px !important;
    border-top:none !important;
    min-height:36px !important;
    font-size:.78rem !important;
    background:#f8fbff !important;
    color:#2563eb !important;
}

[data-testid="stMain"] .file-click-card-head + div button *{
    color:#2563eb !important;
}

/* Popup */
div[data-testid="stDialog"] img{
    max-height:68vh !important;
    object-fit:contain !important;
}


/* ===== ARCHIVOS CARGADOS: OJO JUNTO A X ===== */

/* Oculta las fichas nativas de archivos del uploader.
   La selección sigue existiendo y se procesa normalmente. */
[data-testid="stFileUploaderFile"]{
    display:none !important;
}

.uploaded-preview-title{
    margin:.62rem 0 .42rem;
    font-size:.9rem;
    font-weight:850;
    color:#0f172a;
}

.file-action-card{
    min-height:64px;
    display:flex;
    align-items:center;
    gap:.6rem;
    padding:.62rem .68rem;
    border:1px solid #dbe5f0;
    border-radius:11px 11px 0 0;
    background:#fff;
}

.file-action-icon{
    width:38px;
    height:38px;
    flex:0 0 38px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:8px;
    background:#f1f5f9;
    font-size:1.2rem;
}

.file-action-info{
    min-width:0;
    flex:1;
}

.file-action-name{
    color:#0f172a;
    font-size:.73rem;
    font-weight:780;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.file-action-meta{
    margin-top:.12rem;
    color:#64748b;
    font-size:.64rem;
}

/* Los dos botones de acción forman el pie de la tarjeta */
[data-testid="stMain"] .file-action-card + div{
    gap:0 !important;
}

[data-testid="stMain"] .file-action-card + div button{
    min-height:34px !important;
    border-radius:0 !important;
    border-color:#dbe5f0 !important;
    background:#fff !important;
    font-size:.9rem !important;
    padding:.2rem !important;
}

[data-testid="stMain"] .file-action-card + div > div:first-child button{
    border-radius:0 0 0 11px !important;
    color:#2563eb !important;
}

[data-testid="stMain"] .file-action-card + div > div:last-child button{
    border-radius:0 0 11px 0 !important;
    color:#ef4444 !important;
}

[data-testid="stMain"] .file-action-card + div > div:first-child button:hover{
    background:#eff6ff !important;
    border-color:#93c5fd !important;
}

[data-testid="stMain"] .file-action-card + div > div:last-child button:hover{
    background:#fff1f2 !important;
    border-color:#fca5a5 !important;
}

/* En móvil: dos tarjetas por fila se adaptan por las columnas de Streamlit */
@media (max-width:640px){
    .file-action-card{
        min-height:60px;
    }
    .file-action-name{
        font-size:.69rem;
    }
}


/* ===== ÚNICA SECCIÓN DE ARCHIVOS SELECCIONADOS ===== */

.selected-files-title{
    margin:.55rem 0 .42rem 0;
    font-size:.88rem;
    font-weight:850;
    color:#0f172a;
}

.selected-file-card{
    min-height:66px;
    display:flex;
    align-items:center;
    gap:.62rem;
    padding:.62rem .68rem;

    border:1px solid #dbe5f0;
    border-bottom:none;
    border-radius:11px 11px 0 0;
    background:#fff;
}

.selected-file-icon{
    width:40px;
    height:40px;
    flex:0 0 40px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:8px;
    background:#f1f5f9;
    font-size:1.2rem;
}

.selected-file-info{
    flex:1;
    min-width:0;
}

.selected-file-name{
    color:#0f172a;
    font-size:.74rem;
    font-weight:780;

    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.selected-file-meta{
    margin-top:.12rem;
    color:#64748b;
    font-size:.64rem;
}

/* Ojo y X como pie compacto de la misma tarjeta */
[data-testid="stMain"] .selected-file-card + div{
    gap:0 !important;
    margin-top:0 !important;
}

[data-testid="stMain"] .selected-file-card + div button{
    min-height:34px !important;
    border-radius:0 !important;
    background:#fff !important;
    border-color:#dbe5f0 !important;
    padding:.15rem !important;
}

[data-testid="stMain"] .selected-file-card + div > div:first-child button{
    border-radius:0 0 0 11px !important;
    color:#2563eb !important;
}

[data-testid="stMain"] .selected-file-card + div > div:last-child button{
    border-radius:0 0 11px 0 !important;
    color:#ef4444 !important;
}

[data-testid="stMain"] .selected-file-card + div > div:first-child button:hover{
    background:#eff6ff !important;
    border-color:#93c5fd !important;
}

[data-testid="stMain"] .selected-file-card + div > div:last-child button:hover{
    background:#fff1f2 !important;
    border-color:#fca5a5 !important;
}

/* Ocultar las fichas nativas del uploader para no duplicar archivos */
[data-testid="stFileUploaderFile"]{
    display:none !important;
}

/* Popup de vista previa */
div[data-testid="stDialog"] img{
    max-height:68vh !important;
    object-fit:contain !important;
}


/* ===== ARCHIVOS SELECCIONADOS - VERSIÓN FINAL ===== */

/* Ocultar solamente las fichas de archivos nativas.
   El uploader y su botón de agregar archivos siguen funcionando. */
[data-testid="stFileUploaderFile"]{
    display:none !important;
}

/* Compactar las filas creadas con st.container(border=True) */
[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:10px !important;
}

/* Botones pequeños de acción dentro de las fichas */
[data-testid="stMain"] button[aria-label*="Vista previa"],
[data-testid="stMain"] button[aria-label*="Quitar"]{
    min-width:34px !important;
    min-height:34px !important;
    padding:.2rem !important;
    border-radius:999px !important;
}

/* En móvil, mantener botones cómodos para tocar */
@media (max-width:720px){
    [data-testid="stMain"] button[aria-label*="Vista previa"],
    [data-testid="stMain"] button[aria-label*="Quitar"]{
        min-width:40px !important;
        min-height:40px !important;
    }
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
    "modo_carga_ui": "archivos",
    "archivos_ocultos_ui": set(),
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
    total_lineas = int(sum(
        info.get("cantidad_articulos", 0)
        for info in st.session_state.detalle_facturas_procesadas.values()
    ))
    total_unidades = int(sum(
        x.get("stock", 0)
        for x in st.session_state.inventario_acumulado.values()
    ))
    valor_compra = float(sum(
        x.get("costo_total", 0)
        for x in st.session_state.inventario_acumulado.values()
    ))
    return total_facturas, total_productos, total_lineas, total_unidades, valor_compra


def resetear_todo():
    st.session_state.inventario_acumulado = {}
    st.session_state.firmas_facturas_procesadas = set()
    st.session_state.detalle_facturas_procesadas = {}
    st.session_state.margen_usado = 35.0
    st.session_state.articulos_repetidos_notif = []
    st.session_state.errores_ocr = []
    st.session_state.uploader_key += 1
    st.session_state.archivos_ocultos_ui = set()
    st.session_state.camera_key += 1


@st.dialog("Confirmar procesamiento")
def modal_confirmacion(validas, duplicadas_count, margen):
    st.markdown("### 🚀 Incorporar facturas al inventario")
    st.caption("Esta acción acumulará stock y costos usando la misma lógica de la versión funcional.")

    c1, c2 = st.columns(2)
    c1.metric("Facturas nuevas", len(validas))
    c2.metric("Margen aplicado", f"{margen:g}%")

    if duplicadas_count:
        st.warning(
            f"⚠️ Se omitieron {duplicadas_count} factura(s) duplicada(s). "
            "No se agregarán al inventario."
        )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("✅ Confirmar y actualizar", type="primary", use_container_width=True):
            st.session_state.margen_usado = margen
            st.session_state.articulos_repetidos_notif = []

            # Solo se recorren facturas válidas y únicas; los duplicados nunca llegan aquí.
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




@st.dialog("👁 Vista previa del archivo", width="large")
def mostrar_vista_previa_archivo(nombre, tipo_mime, datos):
    """Muestra imágenes y la primera página de PDFs sin alterar el archivo."""
    nombre_lower = nombre.lower()

    st.markdown(f"**{nombre}**")
    st.caption(f"Tamaño: {len(datos) / 1024:.1f} KB")

    if nombre_lower.endswith((".jpg", ".jpeg", ".png")):
        try:
            imagen = Image.open(io.BytesIO(datos))
            imagen = ImageOps.exif_transpose(imagen)
            st.image(imagen, use_container_width=True)
        except Exception as exc:
            st.error(f"No se pudo mostrar la imagen: {exc}")

    elif nombre_lower.endswith(".pdf"):
        if PYMUPDF_DISPONIBLE:
            try:
                doc = fitz.open(stream=datos, filetype="pdf")
                if len(doc) > 0:
                    pagina = doc[0]
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
                    imagen = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(imagen, caption="Primera página", use_container_width=True)
                doc.close()
            except Exception as exc:
                st.error(f"No se pudo generar la vista previa del PDF: {exc}")
        else:
            st.info("La vista previa de PDF requiere PyMuPDF.")

    else:
        st.info("Este tipo de archivo no tiene vista previa disponible.")

    st.download_button(
        "⬇️ Descargar archivo",
        data=datos,
        file_name=nombre,
        mime=tipo_mime or "application/octet-stream",
        use_container_width=True,
        key=f"preview_download_{abs(hash(nombre))}",
    )

def render_carga_facturas(titulo=True):
    """Carga y procesa facturas con un selector visual robusto basado en botones reales."""

    st.markdown(
        '<div class="load-title">1. Cargar facturas</div>',
        unsafe_allow_html=True,
    )

    carga_col, margen_col = st.columns([3.2, 1], gap="medium")

    # =========================================================
    # IZQUIERDA: selector real de modo de carga
    # =========================================================
    with carga_col:
        b1, b2, b3 = st.columns(3, gap="small")

        with b1:
            st.markdown(
                """
                <div class="mode-icon">📁</div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Seleccionar archivos",
                use_container_width=True,
                type="primary" if st.session_state.modo_carga_ui == "archivos" else "secondary",
                key="modo_archivos_btn",
            ):
                st.session_state.modo_carga_ui = "archivos"
                st.rerun()
            st.markdown(
                '<div class="mode-caption">PDF, JPG, JPEG o PNG</div>',
                unsafe_allow_html=True,
            )

        with b2:
            st.markdown(
                """
                <div class="mode-icon">📷</div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Tomar foto",
                use_container_width=True,
                type="primary" if st.session_state.modo_carga_ui == "camara" else "secondary",
                key="modo_camara_btn",
            ):
                st.session_state.modo_carga_ui = "camara"
                st.rerun()
            st.markdown(
                '<div class="mode-caption">Usar cámara del teléfono</div>',
                unsafe_allow_html=True,
            )

        with b3:
            st.markdown(
                """
                <div class="mode-icon">☁️</div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Arrastrar y soltar",
                use_container_width=True,
                type="primary" if st.session_state.modo_carga_ui == "arrastrar" else "secondary",
                key="modo_arrastrar_btn",
            ):
                st.session_state.modo_carga_ui = "arrastrar"
                st.rerun()
            st.markdown(
                '<div class="mode-caption">Suelta tus archivos aquí</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="load-supported">Formatos soportados: PDF, JPG, JPEG, PNG · Puedes seleccionar múltiples archivos</div>',
            unsafe_allow_html=True,
        )

        uploaded_files = []

        if st.session_state.modo_carga_ui == "archivos":
            uploaded_files = st.file_uploader(
                "Selecciona tus facturas",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"uploader_{st.session_state.uploader_key}",
            ) or []

        elif st.session_state.modo_carga_ui == "camara":
            foto = st.camera_input(
                "Toma una foto completa de la factura",
                key=f"camera_{st.session_state.camera_key}",
            )
            if foto is not None:
                uploaded_files = [foto]

        else:
            uploaded_files = st.file_uploader(
                "Arrastra y suelta tus facturas",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"drag_uploader_{st.session_state.uploader_key}",
                help="Arrastra uno o varios archivos dentro del área punteada.",
            ) or []

    # =========================================================
    # DERECHA: margen real
    # =========================================================
    with margen_col:
        st.markdown(
            '<div class="margin-heading">Margen de ganancia (%)</div>',
            unsafe_allow_html=True,
        )

        margen_porcentaje = st.number_input(
            "Margen (%)",
            min_value=0.0,
            max_value=500.0,
            value=float(st.session_state.margen_usado),
            step=1.0,
            format="%.2f",
            label_visibility="collapsed",
            key=f"margen_input_{st.session_state.uploader_key}_{st.session_state.camera_key}",
        )

        if margen_porcentaje > 15:
            st.markdown(
                """
                <div class="margin-status ok-status">
                    ✓ Margen válido para procesar
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="margin-status warn-status">
                    El margen debe ser mayor al 15%
                </div>
                """,
                unsafe_allow_html=True,
            )

    # =========================================================
    # ARCHIVOS SELECCIONADOS — una sola vista compacta
    # =========================================================
    def _huella_archivo_ui(archivo):
        try:
            datos = archivo.getvalue()
            return f"{archivo.name}|{len(datos)}"
        except Exception:
            return f"{archivo.name}|0"

    # Excluir únicamente los archivos quitados con la X personalizada.
    uploaded_files = [
        f for f in uploaded_files
        if _huella_archivo_ui(f) not in st.session_state.archivos_ocultos_ui
    ]

    if uploaded_files:
        # No añadimos otro título "Selecciona tus facturas":
        # el file_uploader ya muestra ese texto.

        max_cols = 3

        for fila_inicio in range(0, len(uploaded_files), max_cols):
            grupo = uploaded_files[fila_inicio:fila_inicio + max_cols]
            columnas_archivos = st.columns(len(grupo), gap="small")

            for offset, archivo in enumerate(grupo):
                indice = fila_inicio + offset

                try:
                    datos = archivo.getvalue()
                except Exception:
                    archivo.seek(0)
                    datos = archivo.read()
                    archivo.seek(0)

                nombre = archivo.name
                mime = getattr(archivo, "type", None)
                extension = (
                    nombre.lower().rsplit(".", 1)[-1]
                    if "." in nombre else ""
                )

                if extension in ("jpg", "jpeg", "png"):
                    icono = "🖼️"
                    tipo = "Imagen"
                elif extension == "pdf":
                    icono = "📄"
                    tipo = "PDF"
                else:
                    icono = "📎"
                    tipo = extension.upper() or "Archivo"

                nombre_corto = (
                    nombre
                    if len(nombre) <= 24
                    else nombre[:21] + "…"
                )

                with columnas_archivos[offset]:
                    with st.container(border=True):
                        fila_info, fila_ojo, fila_x = st.columns(
                            [6.6, 1.15, 1.15],
                            gap="small",
                            vertical_alignment="center",
                        )

                        with fila_info:
                            # Usamos controles nativos de Streamlit para evitar
                            # que HTML termine mostrándose como texto.
                            st.markdown(f"{icono} **{nombre_corto}**")
                            st.caption(f"{len(datos)/1024:.1f} KB · {tipo}")

                        with fila_ojo:
                            if st.button(
                                "👁",
                                key=(
                                    f"preview_btn_{indice}_"
                                    f"{st.session_state.uploader_key}_"
                                    f"{st.session_state.camera_key}"
                                ),
                                help=f"Vista previa de {nombre}",
                                use_container_width=True,
                            ):
                                mostrar_vista_previa_archivo(
                                    nombre,
                                    mime,
                                    datos,
                                )

                        with fila_x:
                            if st.button(
                                "✕",
                                key=(
                                    f"remove_btn_{indice}_"
                                    f"{st.session_state.uploader_key}_"
                                    f"{st.session_state.camera_key}"
                                ),
                                help=f"Quitar {nombre}",
                                use_container_width=True,
                            ):
                                st.session_state.archivos_ocultos_ui.add(
                                    _huella_archivo_ui(archivo)
                                )
                                st.rerun()

        st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)

    archivos_validos = []
    archivos_duplicados = []
    archivos_invalidos = []

    if uploaded_files:
        st.session_state.errores_ocr = []

        # Evita procesar dos veces el mismo nombre de archivo dentro del lote.
        archivos_por_nombre = {}
        for f in uploaded_files:
            if f.name in archivos_por_nombre:
                archivos_duplicados.append(
                    (f.name, "Archivo repetido en esta carga", "")
                )
            else:
                archivos_por_nombre[f.name] = f

        archivos_unicos = list(archivos_por_nombre.values())

        # También evita duplicados por factura aunque tengan nombres de archivo distintos.
        firmas_detectadas_en_lote = set()

        with st.spinner("Leyendo y reconociendo facturas..."):
            for f in archivos_unicos:
                firma, proveedor, num_fac, fecha_fac, productos = extraer_datos_factura(f)

                if not productos:
                    archivos_invalidos.append(f.name)

                elif firma in st.session_state.firmas_facturas_procesadas:
                    archivos_duplicados.append(
                        (f.name, proveedor, num_fac)
                    )

                elif firma in firmas_detectadas_en_lote:
                    archivos_duplicados.append(
                        (f.name, proveedor, num_fac)
                    )

                else:
                    firmas_detectadas_en_lote.add(firma)
                    archivos_validos.append(
                        (f, firma, proveedor, num_fac, fecha_fac, productos)
                    )

    if uploaded_files:
        if archivos_duplicados:
            st.warning(
                f"⚠️ Se detectaron {len(archivos_duplicados)} factura(s) duplicada(s). "
                "Fueron omitidas automáticamente y no se agregarán al inventario."
            )

        if st.session_state.errores_ocr:
            with st.expander("🔎 Diagnóstico OCR"):
                for err in st.session_state.errores_ocr:
                    st.warning(err)

        if margen_porcentaje <= 15:
            st.error("El margen de ganancia debe ser mayor al 15% para procesar.")

        if st.button(
            "🚀 Procesar Facturas",
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
# SIDEBAR
# =========================================================
total_facturas, total_productos, total_lineas, total_unidades, valor_compra = totales_dashboard()

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

    st.markdown("""
    <div style="height:1px;background:rgba(255,255,255,.08);margin:.9rem 0;"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="side-summary">
      <div class="s-title">RESUMEN RÁPIDO</div>
      <div class="row"><span>Facturas procesadas</span><span class="num">{total_facturas}</span></div>
      <div class="row"><span>Productos únicos</span><span class="num">{total_productos}</span></div>
      <div class="row"><span>Líneas procesadas</span><span class="num">{total_lineas}</span></div>
      <div class="row"><span>Unidades totales</span><span class="num">{total_unidades:,}</span></div>
      <div class="row"><span>Valor compra</span><span class="num">RD$ {valor_compra:,.2f}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reiniciar todo", use_container_width=True):
        resetear_todo()
        st.rerun()


# =========================================================
# INICIO
# =========================================================
if pagina == "🏠 Inicio":
    st.markdown(f"""
    <div class="hero-grid">
      <div class="hero-card">
        <h1>¡Bienvenido! 👋</h1>
        <div class="subtitle">Procesador Inteligente de Facturas WilPOS Móvil</div>
        <p>Carga tus facturas desde tu teléfono o computadora.</p>
        <p>El sistema actualizará tu inventario y dejará el archivo listo para WilPOS.</p>
        <div class="hero-visual">
          <div class="phone"></div>
          <div class="sheet"></div>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-title">Estadísticas generales</div>
        <div class="stats-grid">
          <div class="stat blue">
            <div class="label">Facturas procesadas</div>
            <div class="value">{total_facturas}</div>
            <div class="stat-icon">🧾</div>
          </div>
          <div class="stat purple">
            <div class="label">Productos únicos</div>
            <div class="value">{total_productos}</div>
            <div class="stat-icon">📦</div>
          </div>
          <div class="stat orange">
            <div class="label">Unidades totales</div>
            <div class="value">{total_unidades:,}</div>
            <div class="stat-icon">🛒</div>
          </div>
          <div class="stat green">
            <div class="label">Valor total compra</div>
            <div class="value">RD$ {valor_compra:,.2f}</div>
            <div class="stat-icon">💰</div>
          </div>
        </div>
        <div class="stats-link">Ver detalle completo →</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    render_carga_facturas(titulo=False)



    if st.session_state.detalle_facturas_procesadas:
        st.markdown('<div class="inventory-card">', unsafe_allow_html=True)

        inv_c1, inv_c2 = st.columns([4, 1])
        with inv_c1:
            st.markdown(
                f'<div class="inventory-title">📦 Inventario acumulado <span class="badge">{total_productos} productos únicos</span></div>',
                unsafe_allow_html=True
            )

        df_inicio = construir_df_productos()

        with inv_c2:
            if not df_inicio.empty:
                excel_inicio = generar_excel_wilpos(df_inicio)
                st.download_button(
                    "📥 Descargar Excel",
                    data=excel_inicio,
                    file_name="Inventario_WilPOS_Acumulado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                    key="download_excel_inicio",
                )

        if not df_inicio.empty:
            cols = [
                c for c in
                ["Código Barra", "Nombre", "Cantidad Empaque", "Stock", "Costo", "Precio Venta", "Categoría"]
                if c in df_inicio.columns
            ]
            st.dataframe(
                df_inicio[cols].head(8),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# PROCESAR FACTURAS
# =========================================================
elif pagina == "🧾 Procesar facturas":
    render_carga_facturas(titulo=True)


# =========================================================
# INVENTARIO
# =========================================================
elif pagina == "📦 Inventario acumulado":
    df_productos = construir_df_productos()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 📦 Inventario acumulado")
    st.caption("Los productos repetidos entre facturas se consolidan en una sola fila. Las líneas procesadas pueden ser mayores que los productos únicos.")

    if st.session_state.articulos_repetidos_notif:
        with st.expander("🔄 Artículos acumulados desde varias facturas"):
            for notif in st.session_state.articulos_repetidos_notif:
                st.info(notif)

    if df_productos.empty:
        st.info("Todavía no hay productos en el inventario.")
    else:
        top_inv1, top_inv2 = st.columns([4, 1])
        with top_inv2:
            excel_inventario = generar_excel_wilpos(df_productos)
            st.download_button(
                "📥 Descargar Excel",
                data=excel_inventario,
                file_name="Inventario_WilPOS_Acumulado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
                key="download_excel_inventario",
            )

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
