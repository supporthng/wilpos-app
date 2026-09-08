import io
import base64
import os
import hashlib
import html
import re
import json
import html as html_lib
import pandas as pd
import streamlit as st
import pdfplumber
from PIL import Image, ImageOps
from datetime import datetime
from urllib.request import Request, urlopen
from difflib import SequenceMatcher
import math

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

try:
    from openai import OpenAI
    OPENAI_SDK_DISPONIBLE = True
except ImportError:
    OpenAI = None
    OPENAI_SDK_DISPONIBLE = False


# pytesseract puede importar aunque el ejecutable "tesseract" no esté
# instalado en el servidor.
TESSERACT_MOTOR_LISTO = False
TESSERACT_ERROR = ""

if OCR_DISPONIBLE:
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_MOTOR_LISTO = True
    except Exception as exc:
        TESSERACT_MOTOR_LISTO = False
        TESSERACT_ERROR = str(exc)

st.set_page_config(
page_title="WilPOS Móvil | Procesador de Facturas",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="auto",
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

/* Sustituye visualmente Upload/Browse files por Cargar Facturas */
[data-testid="stMain"]
[data-testid="stFileUploader"]
section button p::after{
    content:"⬆  Cargar Facturas" !important;
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


/* ===== AJUSTES PRODUCTOS REPETIDOS / ARCHIVOS ===== */

/* Las fichas nativas se ocultan porque usamos una única fila compacta propia. */
[data-testid="stFileUploaderFile"]{
    display:none !important;
}

/* Tarjetas nativas creadas con st.container */
[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:10px !important;
}

/* Tablas de repetidos */
[data-testid="stDataFrame"]{
    margin-top:.35rem;
    margin-bottom:.45rem;
}


/* ===== DETALLE DE FACTURAS DUPLICADAS ===== */
[data-testid="stExpander"]{
    border-radius:10px !important;
}

[data-testid="stExpander"] summary{
    font-weight:750 !important;
}


/* =========================================================
   CTA PRINCIPAL — GENERAR ARCHIVO EXCEL
   ========================================================= */
.process-action-spacer{
    height: 1.15rem;
}

.process-ready{
    display:flex;
    align-items:center;
    gap:.75rem;
    width:100%;
    box-sizing:border-box;
    padding:.85rem .95rem;
    margin:.2rem 0 .7rem 0;
    border:1px solid #cfe0ff;
    border-radius:14px;
    background:linear-gradient(135deg,#f7faff 0%,#eef5ff 100%);
    color:#163a70;
}

.process-ready-icon{
    width:38px;
    height:38px;
    min-width:38px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:11px;
    background:#ffffff;
    box-shadow:0 4px 14px rgba(37,99,235,.10);
    font-size:1.15rem;
}

.process-ready b{
    display:block;
    font-size:.93rem;
    line-height:1.15;
    margin-bottom:.18rem;
}

.process-ready span{
    display:block;
    font-size:.72rem;
    line-height:1.25;
    color:#66758d;
}

/* El botón Streamlit inmediatamente posterior al bloque informativo */
.process-ready + div[data-testid="stButton"] > button,
.process-ready ~ div[data-testid="stButton"] > button{
    min-height:64px !important;
    border-radius:15px !important;
    font-size:1.05rem !important;
    font-weight:800 !important;
    letter-spacing:.01em !important;
    box-shadow:0 10px 24px rgba(37,99,235,.22) !important;
    transition:transform .16s ease, box-shadow .16s ease !important;
}

.process-ready + div[data-testid="stButton"] > button:hover,
.process-ready ~ div[data-testid="stButton"] > button:hover{
    transform:translateY(-2px);
    box-shadow:0 14px 28px rgba(37,99,235,.28) !important;
}

/* En móvil vuelve a flujo natural sin crear huecos */
@media (max-width: 900px){
    .process-action-spacer{
        height:.35rem;
    }
    .process-ready + div[data-testid="stButton"] > button,
    .process-ready ~ div[data-testid="stButton"] > button{
        min-height:58px !important;
    }
}


.process-waiting{
    opacity:.82;
}


/* ===== TABLA COMPLETA PRODUCTOS CONSOLIDADOS ===== */
.products-count-line{
    margin:.35rem 0 .5rem 0;
    font-size:.74rem;
    color:#64748b;
}

[data-testid="stTable"]{
    width:100% !important;
    overflow-x:auto !important;
}

[data-testid="stTable"] table{
    width:100% !important;
    font-size:.75rem !important;
}

[data-testid="stTable"] th{
    white-space:nowrap !important;
}

[data-testid="stTable"] td{
    vertical-align:middle !important;
}


/* =========================================================
   PRODUCTOS CONSOLIDADOS — TABLA COMPLETA SIN RECORTE
   ========================================================= */
.products-count-line{
    width:100%;
    box-sizing:border-box;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    margin:.45rem 0 .55rem 0;
    padding:.55rem .7rem;
    border:1px solid #dbe5f0;
    border-radius:8px;
    background:#f8fbff;
    color:#64748b;
    font-size:.75rem;
}

.products-ok{
    color:#15803d;
    font-weight:800;
    white-space:nowrap;
}

.wilpos-products-wrap{
    width:100% !important;
    height:auto !important;
    max-height:none !important;
    overflow-x:auto !important;
    overflow-y:visible !important;
    border:1px solid #dbe5f0;
    border-radius:9px;
    background:#fff;
}

.wilpos-products-table{
    width:100% !important;
    min-width:900px;
    border-collapse:collapse;
    table-layout:auto;
    margin:0 !important;
    font-size:.76rem;
}

.wilpos-products-table thead th{
    position:static !important;
    padding:.58rem .6rem;
    text-align:left;
    white-space:nowrap;
    color:#64748b;
    font-weight:650;
    background:#f8fafc;
    border-bottom:1px solid #dbe5f0;
    border-right:1px solid #e5e7eb;
}

.wilpos-products-table tbody td{
    padding:.55rem .6rem;
    color:#0f172a;
    background:#fff;
    border-bottom:1px solid #e5e7eb;
    border-right:1px solid #e5e7eb;
    vertical-align:middle;
    white-space:nowrap;
}

.wilpos-products-table tbody tr:last-child td{
    border-bottom:none;
}

.wilpos-products-table th:last-child,
.wilpos-products-table td:last-child{
    border-right:none;
}

/* Muy importante: ningún padre del bloque puede cortar la tabla */
[data-testid="stMain"] .section-card,
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] [data-testid="stVerticalBlock"]{
    max-height:none;
}

@media (max-width:720px){
    .products-count-line{
        align-items:flex-start;
        flex-direction:column;
        gap:.25rem;
    }

    .wilpos-products-table{
        font-size:.72rem;
    }
}


.products-scroll-hint{
    color:#2563eb;
    font-weight:800;
    white-space:nowrap;
}


/* =========================================================
   PRODUCTOS CONSOLIDADOS — SCROLL VERTICAL REAL
   ========================================================= */
.products-count-line{
    width:100%;
    box-sizing:border-box;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    margin:.45rem 0 .55rem 0;
    padding:.55rem .72rem;
    border:1px solid #dbe5f0;
    border-radius:9px;
    background:#f8fbff;
    color:#64748b;
    font-size:.76rem;
}

.products-scroll-hint{
    color:#2563eb;
    font-weight:800;
    white-space:nowrap;
}

.wilpos-scroll-container{
    width:100% !important;
    height:430px !important;
    max-height:430px !important;
    overflow-y:scroll !important;
    overflow-x:auto !important;
    scrollbar-gutter:stable !important;
    border:1px solid #dbe5f0 !important;
    border-radius:10px !important;
    background:#ffffff !important;
    box-sizing:border-box !important;
}

.wilpos-scroll-table{
    width:100% !important;
    min-width:980px !important;
    margin:0 !important;
    border-collapse:collapse !important;
    table-layout:auto !important;
    font-size:.76rem !important;
}

.wilpos-scroll-table thead th{
    position:sticky !important;
    top:0 !important;
    z-index:2 !important;
    padding:.58rem .62rem !important;
    background:#f8fafc !important;
    color:#64748b !important;
    text-align:left !important;
    white-space:nowrap !important;
    border-bottom:1px solid #dbe5f0 !important;
    border-right:1px solid #e5e7eb !important;
}

.wilpos-scroll-table tbody td{
    padding:.55rem .62rem !important;
    color:#0f172a !important;
    background:#fff !important;
    white-space:nowrap !important;
    vertical-align:middle !important;
    border-bottom:1px solid #e5e7eb !important;
    border-right:1px solid #e5e7eb !important;
}

.wilpos-scroll-table tbody tr:hover td{
    background:#f8fbff !important;
}

.wilpos-scroll-table th:last-child,
.wilpos-scroll-table td:last-child{
    border-right:none !important;
}

/* Barra de scroll claramente visible */
.wilpos-scroll-container::-webkit-scrollbar{
    width:14px !important;
    height:12px !important;
}

.wilpos-scroll-container::-webkit-scrollbar-track{
    background:#eef2f7 !important;
    border-left:1px solid #e2e8f0 !important;
}

.wilpos-scroll-container::-webkit-scrollbar-thumb{
    background:#94a3b8 !important;
    border-radius:999px !important;
    border:3px solid #eef2f7 !important;
}

.wilpos-scroll-container::-webkit-scrollbar-thumb:hover{
    background:#64748b !important;
}

/* Firefox */
.wilpos-scroll-container{
    scrollbar-width:auto !important;
    scrollbar-color:#94a3b8 #eef2f7 !important;
}

@media (max-width:720px){
    .products-count-line{
        flex-direction:column;
        align-items:flex-start;
        gap:.25rem;
    }

    .wilpos-scroll-container{
        height:380px !important;
        max-height:380px !important;
    }
}


/* ===== PRODUCTOS CONSOLIDADOS EN INICIO ===== */
.home-products-note{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    margin:.45rem 0 .5rem 0;
    padding:.5rem .65rem;
    border:1px solid #dbe5f0;
    border-radius:8px;
    background:#f8fbff;
    color:#64748b;
    font-size:.74rem;
}

.home-products-note span:last-child{
    color:#2563eb;
    font-weight:800;
    white-space:nowrap;
}

@media (max-width:720px){
    .home-products-note{
        flex-direction:column;
        align-items:flex-start;
        gap:.2rem;
    }
}


/* ===== RESUMEN DE FACTURAS VÁLIDAS / OMITIDAS ===== */
.validation-summary{
    padding:.78rem .85rem !important;
}

.validation-summary-body{
    flex:1;
    min-width:0;
}

.validation-row{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    padding:.15rem 0;
}

.validation-label{
    font-size:.78rem;
    font-weight:750;
    color:#475569;
}

.validation-value{
    min-width:28px;
    text-align:center;
    padding:.12rem .48rem;
    border-radius:999px;
    font-size:.76rem;
    font-weight:850;
}

.valid-row .validation-value{
    background:#dcfce7;
    color:#15803d;
}

.omitted-row .validation-value{
    background:#fee2e2;
    color:#b91c1c;
}

.validation-reason{
    margin-top:.42rem;
    padding-top:.42rem;
    border-top:1px solid #dbe5f0;
    color:#64748b;
    font-size:.69rem;
    line-height:1.35;
}


/* =========================================================
   WILPOS MÓVIL — RESPONSIVE FINAL
   ========================================================= */

/* Teléfonos y tablets */
@media (max-width: 900px){

    /* Contenido principal ocupa todo el ancho */
    .block-container{
        width:100% !important;
        max-width:100% !important;
        padding-top:.55rem !important;
        padding-left:.55rem !important;
        padding-right:.55rem !important;
        padding-bottom:1.25rem !important;
    }

    /* Hero y estadísticas uno debajo del otro */
    .hero-grid{
        grid-template-columns:1fr !important;
        gap:.65rem !important;
    }

    .hero-card,
    .stats-card,
    .section-card,
    .inventory-card{
        width:100% !important;
        max-width:100% !important;
        box-sizing:border-box !important;
        border-radius:12px !important;
    }

    .hero-card{
        min-height:auto !important;
        padding:.9rem !important;
    }

    .hero-card h1{
        font-size:1.55rem !important;
        line-height:1.15 !important;
        margin-bottom:.65rem !important;
    }

    .hero-card .subtitle{
        font-size:.9rem !important;
    }

    .hero-card p{
        font-size:.78rem !important;
        line-height:1.45 !important;
    }

    /* Ocultar ilustración grande para ganar espacio */
    .hero-visual{
        display:none !important;
    }

    /* Estadísticas 2 x 2 */
    .stats-grid{
        grid-template-columns:1fr 1fr !important;
        gap:.45rem !important;
    }

    .stat{
        min-height:78px !important;
        padding:.65rem !important;
    }

    .stat .label{
        font-size:.64rem !important;
    }

    .stat .value{
        font-size:.95rem !important;
    }

    /* Zona de carga pasa a una sola columna */
    .upload-grid{
        grid-template-columns:1fr !important;
        gap:.65rem !important;
    }

    .upload-zone{
        border-right:none !important;
        border-bottom:1px solid #e5e7eb !important;
        padding:.75rem !important;
    }

    .margin-zone{
        width:100% !important;
        padding:.75rem !important;
        box-sizing:border-box !important;
    }

    /* Las 3 tarjetas de carga se apilan */
    .fake-upload{
        grid-template-columns:1fr !important;
        min-height:auto !important;
    }

    .fake-upload-item{
        min-height:84px !important;
        border-right:none !important;
        border-bottom:1px solid #eef2f7 !important;
        padding:.65rem !important;
    }

    .fake-upload-item:last-child{
        border-bottom:none !important;
    }

    .fake-upload-icon{
        width:40px !important;
        height:40px !important;
        font-size:1.15rem !important;
    }

    .fake-upload-title{
        font-size:.82rem !important;
    }

    .fake-upload-sub{
        font-size:.68rem !important;
    }

    /* Uploader y cámara ocupan todo el ancho */
    div[data-testid="stFileUploader"],
    div[data-testid="stCameraInput"]{
        width:100% !important;
        max-width:100% !important;
    }

    div[data-testid="stFileUploader"] section{
        padding:.5rem !important;
    }

    /* Archivos seleccionados: una sola columna */
    .file-strip{
        grid-template-columns:1fr !important;
    }

    /* Controles numéricos y botones fáciles de tocar */
    .stButton > button,
    .stDownloadButton > button,
    div[data-testid="stNumberInput"] button{
        min-height:46px !important;
        font-size:.82rem !important;
    }

    div[data-testid="stNumberInput"] input{
        min-height:46px !important;
        font-size:.86rem !important;
    }

    /* Resumen válidas / omitidas */
    .process-ready,
    .validation-summary{
        width:100% !important;
        box-sizing:border-box !important;
        padding:.72rem !important;
        gap:.55rem !important;
        border-radius:12px !important;
    }

    .process-ready-icon{
        width:36px !important;
        height:36px !important;
        min-width:36px !important;
    }

    .validation-label{
        font-size:.75rem !important;
    }

    .validation-value{
        font-size:.74rem !important;
    }

    .validation-reason{
        font-size:.67rem !important;
        line-height:1.4 !important;
    }

    /* Botón principal */
    .process-ready + div[data-testid="stButton"] > button,
    .process-ready ~ div[data-testid="stButton"] > button{
        min-height:54px !important;
        font-size:.92rem !important;
        border-radius:12px !important;
    }

    /* Columnas de acciones pasan a ocupar ancho razonable */
    [data-testid="stHorizontalBlock"]{
        gap:.45rem !important;
    }

    /* Productos consolidados */
    .inventory-title{
        font-size:.82rem !important;
        flex-wrap:wrap !important;
    }

    .badge{
        font-size:.62rem !important;
    }

    .home-products-note,
    .products-count-line{
        flex-direction:column !important;
        align-items:flex-start !important;
        gap:.18rem !important;
        font-size:.69rem !important;
    }

    /* Dataframes: scroll horizontal natural */
    div[data-testid="stDataFrame"]{
        width:100% !important;
        max-width:100% !important;
        overflow:auto !important;
    }

    div[data-testid="stDataFrame"] > div{
        overflow:auto !important;
    }

    /* Expander más compacto */
    [data-testid="stExpander"] summary{
        font-size:.76rem !important;
        padding:.55rem !important;
    }

    /* Diálogos ocupan casi toda la pantalla */
    div[data-testid="stDialog"] > div{
        width:96vw !important;
        max-width:96vw !important;
    }

    /* Sidebar cuando se abre */
    [data-testid="stSidebar"]{
        width:82vw !important;
        min-width:82vw !important;
        max-width:320px !important;
    }

    [data-testid="stSidebar"] > div:first-child{
        width:100% !important;
        min-width:0 !important;
        max-width:none !important;
    }

    [data-testid="stSidebar"] div[data-testid="stRadio"] label p{
        font-size:.82rem !important;
        white-space:nowrap !important;
    }
}

/* Teléfonos pequeños */
@media (max-width: 600px){

    .block-container{
        padding-left:.4rem !important;
        padding-right:.4rem !important;
    }

    .stats-grid{
        grid-template-columns:1fr 1fr !important;
    }

    .stat{
        padding:.55rem !important;
    }

    /* Forzar cualquier set de columnas de acciones a apilarse */
    [data-testid="stHorizontalBlock"]{
        flex-wrap:wrap !important;
    }

    /* Evitar botones demasiado estrechos */
    [data-testid="stHorizontalBlock"] > div{
        min-width:0 !important;
    }

    /* Tablas y contenido nunca desbordan la pantalla */
    table{
        max-width:none !important;
    }

    .section-card,
    .inventory-card{
        padding:.65rem !important;
    }
}


/* =========================================================
   WILPOS MOBILE FIX — iPhone / Android
   ========================================================= */
@media (max-width: 900px){

    /* El contenido principal nunca queda por debajo del sidebar */
    [data-testid="stAppViewContainer"]{
        overflow-x:hidden !important;
    }

    /* Sidebar abierto = panel completo, no franja angosta */
    [data-testid="stSidebar"]{
        width:100vw !important;
        min-width:100vw !important;
        max-width:100vw !important;
        z-index:999999 !important;
    }

    [data-testid="stSidebar"] > div:first-child{
        width:100vw !important;
        min-width:100vw !important;
        max-width:100vw !important;
    }

    /* Contenedor principal a ancho real del teléfono */
    [data-testid="stMain"]{
        width:100% !important;
        max-width:100% !important;
        overflow-x:hidden !important;
    }

    [data-testid="stMainBlockContainer"],
    .block-container{
        width:100% !important;
        max-width:100% !important;
        margin:0 !important;
        padding:.5rem .45rem 1.25rem .45rem !important;
        box-sizing:border-box !important;
    }

    /* Hero y estadísticas 100% ancho */
    .hero-grid{
        display:block !important;
        width:100% !important;
    }

    .hero-card,
    .stats-card{
        width:100% !important;
        max-width:100% !important;
        margin:0 0 .65rem 0 !important;
        box-sizing:border-box !important;
    }

    .hero-visual{
        display:none !important;
    }

    .hero-card h1{
        font-size:1.45rem !important;
    }

    .hero-card p{
        font-size:.78rem !important;
        line-height:1.4 !important;
    }

    .stats-grid{
        grid-template-columns:1fr 1fr !important;
        gap:.42rem !important;
    }

    /* =====================================================
       CARGA DE FACTURAS: TODO APILADO
       ===================================================== */

    /* Cualquier bloque horizontal dentro del área de carga se vuelve columna */
    [data-testid="stMain"] .stHorizontalBlock,
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]{
        flex-direction:column !important;
        flex-wrap:nowrap !important;
        width:100% !important;
        gap:.55rem !important;
    }

    [data-testid="stMain"] .stHorizontalBlock > div,
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div{
        width:100% !important;
        flex:1 1 100% !important;
        max-width:100% !important;
        min-width:0 !important;
    }

    /* Excepción: estadísticas internas siguen 2x2 porque son CSS grid */
    .stats-grid{
        display:grid !important;
    }

    /* Opciones visuales de carga */
    .fake-upload{
        display:block !important;
        width:100% !important;
        min-height:0 !important;
    }

    .fake-upload-item{
        width:100% !important;
        min-height:88px !important;
        border-right:none !important;
        border-bottom:1px solid #eef2f7 !important;
        box-sizing:border-box !important;
    }

    .fake-upload-item:last-child{
        border-bottom:none !important;
    }

    /* Zona de carga y margen uno debajo del otro */
    .upload-grid{
        display:block !important;
        width:100% !important;
    }

    .upload-zone,
    .margin-zone{
        width:100% !important;
        max-width:100% !important;
        box-sizing:border-box !important;
        padding:.7rem !important;
        border-right:none !important;
    }

    .upload-zone{
        border-bottom:1px solid #e5e7eb !important;
    }

    /* File uploader no puede desbordarse */
    div[data-testid="stFileUploader"]{
        width:100% !important;
        max-width:100% !important;
        box-sizing:border-box !important;
    }

    div[data-testid="stFileUploader"] section{
        width:100% !important;
        max-width:100% !important;
        box-sizing:border-box !important;
    }

    /* Archivos seleccionados */
    .file-strip{
        grid-template-columns:1fr !important;
        width:100% !important;
    }

    /* Número / margen */
    div[data-testid="stNumberInput"]{
        width:100% !important;
        max-width:100% !important;
    }

    div[data-testid="stNumberInput"] input{
        width:100% !important;
        min-height:48px !important;
        font-size:.95rem !important;
    }

    /* Resumen validación */
    .process-ready,
    .validation-summary{
        width:100% !important;
        max-width:100% !important;
        box-sizing:border-box !important;
    }

    .validation-row{
        width:100% !important;
    }

    /* CTA grande y a ancho completo */
    .stButton > button,
    .stDownloadButton > button{
        width:100% !important;
        min-height:50px !important;
        font-size:.88rem !important;
    }

    /* Tablas: scroll horizontal */
    div[data-testid="stDataFrame"]{
        width:100% !important;
        max-width:100% !important;
        overflow-x:auto !important;
    }

    div[data-testid="stDataFrame"] > div{
        overflow-x:auto !important;
    }

    /* Cards generales */
    .section-card,
    .inventory-card{
        width:100% !important;
        max-width:100% !important;
        box-sizing:border-box !important;
        padding:.65rem !important;
        margin-left:0 !important;
        margin-right:0 !important;
    }
}

@media (max-width: 600px){
    .stats-grid{
        grid-template-columns:1fr 1fr !important;
    }

    .stat{
        min-height:92px !important;
        padding:.55rem !important;
    }

    .stat .label{
        font-size:.66rem !important;
        line-height:1.25 !important;
    }

    .stat .value{
        font-size:1rem !important;
    }

    .upload-foot{
        font-size:.62rem !important;
        line-height:1.35 !important;
    }
}


/* =========================================================
   FIX DEFINITIVO SIDEBAR MÓVIL
   ========================================================= */
@media (max-width: 900px){

    /* Estado cerrado: no debe quedar ninguna franja azul ocupando ancho */
    [data-testid="stSidebar"][aria-expanded="false"]{
        width:0 !important;
        min-width:0 !important;
        max-width:0 !important;
        transform:translateX(-100%) !important;
        overflow:hidden !important;
        border:none !important;
        box-shadow:none !important;
    }

    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child{
        width:0 !important;
        min-width:0 !important;
        max-width:0 !important;
        overflow:hidden !important;
    }

    /* Estado abierto: panel completo por encima del contenido */
    [data-testid="stSidebar"][aria-expanded="true"]{
        position:fixed !important;
        left:0 !important;
        top:0 !important;
        bottom:0 !important;
        width:min(86vw, 340px) !important;
        min-width:min(86vw, 340px) !important;
        max-width:min(86vw, 340px) !important;
        transform:translateX(0) !important;
        z-index:1000000 !important;
        box-shadow:8px 0 28px rgba(15,23,42,.22) !important;
        overflow-y:auto !important;
    }

    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child{
        width:100% !important;
        min-width:100% !important;
        max-width:100% !important;
    }

    /* El contenido principal siempre ocupa el 100% cuando el menú está cerrado */
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"]{
        margin-left:0 !important;
        padding-left:0 !important;
        width:100% !important;
        max-width:100% !important;
    }

    /* Botón nativo para abrir/cerrar menú siempre visible */
    [data-testid="stSidebarCollapsedControl"],
    button[kind="header"]{
        z-index:1000002 !important;
    }

    /* Si Streamlit deja un spacer/resizable handle, eliminar su ancho */
    [data-testid="stSidebar"] + div{
        margin-left:0 !important;
    }
}


.wilpos-brand-header{
    display:flex;
    align-items:center;
    margin:0 0 14px 0;
}
.wilpos-brand-header img{
    height:46px;
    width:auto;
    max-width:180px;
    object-fit:contain;
}
@media (max-width:900px){
    .wilpos-brand-header{margin-bottom:10px;}
    .wilpos-brand-header img{
        height:38px;
        max-width:150px;
    }
}

/* =========================================================
   HERO WILPOS — LOGO DENTRO DEL CUADRO DE BIENVENIDA
   ========================================================= */
.hero-card-logo{
    position:relative !important;
    min-height:185px !important;
    padding:1.15rem 1.25rem !important;
    overflow:hidden !important;
}

/* Texto: deja zona libre a la derecha */
.hero-card-logo .hero-copy{
    position:relative !important;
    z-index:3 !important;
    width:52% !important;
    max-width:620px !important;
}

.hero-card-logo .hero-copy h1{
    margin:0 0 .42rem 0 !important;
}

.hero-card-logo .hero-copy p{
    max-width:100% !important;
}

/* Zona independiente para el logo */
.hero-brand-zone{
    position:absolute !important;
    right:205px !important;
    top:50% !important;
    transform:translateY(-50%) !important;
    width:220px !important;
    height:112px !important;

    display:flex !important;
    align-items:center !important;
    justify-content:center !important;

    background:transparent !important;
    border:none !important;
    box-shadow:none !important;
    z-index:2 !important;
}

.wilpos-hero-logo{
    display:block !important;
    width:100% !important;
    height:100% !important;
    object-fit:contain !important;

    background:transparent !important;
    border:none !important;
    box-shadow:none !important;
}

/* La ilustración conserva su propia zona al extremo derecho */
.hero-card-logo .hero-visual{
    right:.9rem !important;
    top:1.05rem !important;
    width:185px !important;
    height:135px !important;
    transform:scale(.82) !important;
    transform-origin:right center !important;
    z-index:1 !important;
}

/* Escritorio: sidebar visible desde el inicio */
@media (min-width:901px){
    [data-testid="stSidebar"]{
        transform:none !important;
        visibility:visible !important;
    }
}

/* Tablet */
@media (max-width:1100px) and (min-width:901px){
    .hero-card-logo .hero-copy{
        width:48% !important;
    }

    .hero-brand-zone{
        right:170px !important;
        width:180px !important;
        height:95px !important;
    }

    .hero-card-logo .hero-visual{
        width:160px !important;
        transform:scale(.72) !important;
    }
}

/* =========================================================
   MÓVIL
   ========================================================= */
@media (max-width:900px){

    /* En móvil el logo sigue DENTRO del hero */
    .hero-card-logo{
        display:flex !important;
        flex-direction:column !important;
        align-items:flex-start !important;
        min-height:auto !important;
        padding:.9rem !important;
    }

    .hero-card-logo .hero-copy{
        width:100% !important;
        max-width:100% !important;
        order:1 !important;
    }

    .hero-brand-zone{
        position:static !important;
        transform:none !important;
        order:2 !important;

        width:155px !important;
        height:72px !important;
        margin:.55rem auto .1rem auto !important;

        background:transparent !important;
    }

    .wilpos-hero-logo{
        width:100% !important;
        height:100% !important;
    }

    /* La ilustración se oculta en móvil para no saturar */
    .hero-card-logo .hero-visual{
        display:none !important;
    }

    /* Sidebar cerrado = cero ancho */
    [data-testid="stSidebar"][aria-expanded="false"]{
        width:0 !important;
        min-width:0 !important;
        max-width:0 !important;
        transform:translateX(-100%) !important;
        overflow:hidden !important;
        border:none !important;
        box-shadow:none !important;
    }

    /* Sidebar abierto = panel flotante */
    [data-testid="stSidebar"][aria-expanded="true"]{
        position:fixed !important;
        left:0 !important;
        top:0 !important;
        bottom:0 !important;

        width:min(86vw,340px) !important;
        min-width:min(86vw,340px) !important;
        max-width:min(86vw,340px) !important;

        transform:translateX(0) !important;
        z-index:1000000 !important;
        box-shadow:8px 0 28px rgba(15,23,42,.22) !important;
    }
}


/* ===== FIX HERO HTML + DISTRIBUCIÓN FINAL ===== */
.hero-card-logo{
    display:grid !important;
    grid-template-columns:minmax(0,1fr) 190px 155px !important;
    gap:12px !important;
    align-items:center !important;
    min-height:185px !important;
    padding:1.1rem 1.2rem !important;
}

.hero-card-logo .hero-copy{
    position:relative !important;
    width:auto !important;
    max-width:none !important;
    z-index:2 !important;
}

.hero-card-logo .hero-brand-zone{
    position:static !important;
    transform:none !important;
    width:190px !important;
    height:90px !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    background:transparent !important;
    border:0 !important;
    box-shadow:none !important;
    z-index:2 !important;
}

.hero-card-logo .wilpos-hero-logo{
    width:100% !important;
    height:100% !important;
    object-fit:contain !important;
    display:block !important;
    background:transparent !important;
    border:0 !important;
    box-shadow:none !important;
}

.hero-card-logo .hero-visual{
    position:relative !important;
    inset:auto !important;
    width:155px !important;
    height:130px !important;
    transform:none !important;
    z-index:1 !important;
}

@media (max-width:1100px){
    .hero-card-logo{
        grid-template-columns:minmax(0,1fr) 165px 130px !important;
    }
    .hero-card-logo .hero-brand-zone{
        width:165px !important;
        height:78px !important;
    }
    .hero-card-logo .hero-visual{
        width:130px !important;
        transform:scale(.8) !important;
        transform-origin:center !important;
    }
}

@media (max-width:900px){
    .hero-card-logo{
        display:flex !important;
        flex-direction:column !important;
        align-items:flex-start !important;
        min-height:auto !important;
    }
    .hero-card-logo .hero-brand-zone{
        width:150px !important;
        height:68px !important;
        margin:.4rem auto 0 !important;
    }
    .hero-card-logo .hero-visual{
        display:none !important;
    }
}


/* ===== HERO DEFINITIVO: SIN MARKDOWN-CODE Y SIN SOLAPES ===== */
.hero-card-logo{
    display:grid !important;
    grid-template-columns:minmax(420px,1fr) 185px 150px !important;
    column-gap:18px !important;
    align-items:center !important;
    min-height:185px !important;
    padding:1.15rem 1.25rem !important;
    box-sizing:border-box !important;
}
.hero-card-logo .hero-copy{
    position:relative !important;
    width:100% !important;
    max-width:none !important;
    z-index:3 !important;
}
.hero-card-logo .hero-brand-zone{
    position:static !important;
    inset:auto !important;
    transform:none !important;
    width:185px !important;
    height:86px !important;
    margin:0 !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    background:transparent !important;
    border:0 !important;
    box-shadow:none !important;
    overflow:visible !important;
}
.hero-card-logo .wilpos-hero-logo{
    display:block !important;
    width:100% !important;
    height:100% !important;
    object-fit:contain !important;
    background:transparent !important;
    border:0 !important;
    box-shadow:none !important;
}
.hero-card-logo .hero-visual{
    position:relative !important;
    left:auto !important;
    right:auto !important;
    top:auto !important;
    bottom:auto !important;
    width:150px !important;
    height:130px !important;
    transform:scale(.82) !important;
    transform-origin:center !important;
    margin:0 !important;
}
@media (max-width:1100px){
    .hero-card-logo{
        grid-template-columns:minmax(340px,1fr) 160px 125px !important;
        column-gap:10px !important;
    }
    .hero-card-logo .hero-brand-zone{
        width:160px !important;
        height:76px !important;
    }
    .hero-card-logo .hero-visual{
        width:125px !important;
        transform:scale(.7) !important;
    }
}
@media (max-width:900px){
    .hero-card-logo{
        display:flex !important;
        flex-direction:column !important;
        align-items:flex-start !important;
        min-height:auto !important;
    }
    .hero-card-logo .hero-brand-zone{
        width:150px !important;
        height:68px !important;
        margin:.5rem auto 0 !important;
        align-self:center !important;
    }
    .hero-card-logo .hero-visual{
        display:none !important;
    }
}


/* =========================================================
   DETALLE DE FACTURAS OMITIDAS — DESKTOP + MÓVIL
   ========================================================= */
.duplicate-details-box{
    width:100%;
    margin:.55rem 0 .7rem 0;
    border:1px solid #dbe5f0;
    border-radius:11px;
    background:#ffffff;
    overflow:hidden;
    box-sizing:border-box;
}

.duplicate-details-box > summary{
    list-style:none;
    cursor:pointer;
    padding:.72rem .8rem;
    color:#1e40af;
    background:#f8fbff;
    font-size:.76rem;
    font-weight:800;
    line-height:1.3;
    user-select:none;
}

.duplicate-details-box > summary::-webkit-details-marker{
    display:none;
}

.duplicate-details-box > summary::after{
    content:"＋";
    float:right;
    color:#2563eb;
    font-size:1rem;
    font-weight:800;
}

.duplicate-details-box[open] > summary::after{
    content:"−";
}

.duplicate-details-body{
    padding:.55rem;
    background:#fff;
}

.duplicate-mobile-card{
    width:100%;
    box-sizing:border-box;
    margin:0 0 .55rem 0;
    padding:.65rem;
    border:1px solid #fecaca;
    border-radius:9px;
    background:#fffafa;
}

.invalid-mobile-card{
    border-color:#fed7aa;
    background:#fffbeb;
}

.duplicate-mobile-head{
    display:flex;
    justify-content:flex-end;
    margin-bottom:.35rem;
}

.duplicate-mobile-status{
    display:inline-flex;
    align-items:center;
    padding:.16rem .42rem;
    border-radius:999px;
    background:#fee2e2;
    color:#b91c1c;
    font-size:.62rem;
    font-weight:850;
    letter-spacing:.03em;
}

.invalid-status{
    background:#ffedd5;
    color:#c2410c;
}

.duplicate-mobile-row{
    display:grid;
    grid-template-columns:78px minmax(0,1fr);
    gap:.5rem;
    align-items:start;
    padding:.22rem 0;
    border-bottom:1px solid rgba(148,163,184,.16);
    font-size:.69rem;
    line-height:1.35;
}

.duplicate-mobile-row:last-child{
    border-bottom:0;
}

.duplicate-mobile-row b{
    color:#475569;
    font-weig
