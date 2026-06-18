import os
import glob
import time
import html as _html
from itertools import product
import pandas as pd
import altair as alt
import streamlit as st
from dotenv import load_dotenv

# ---------------- Paleta (teal moderno + neutros slate) ----------------
PRIMARIO = "#0F766E"       # teal 700
PRIM_OSC = "#115E59"       # teal 800
PRIM_TINTE = "#CCFBF1"     # teal 100
CIAN = "#0E7490"           # cian 700 (segundo acento)
FONDO = "#F5F7F7"
CARD = "#FFFFFF"
BORDE = "#E2E8F0"
TXT = "#0F172A"
TXT_MED = "#64748B"
TXT_SUAVE = "#94A3B8"
ROJO = "#DC2626"
AMBAR = "#B45309"
VERDE_OK = "#047857"

MESES_ORDEN = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

st.set_page_config(page_title="Licitaciones Públicas · Chile", layout="wide",
                   page_icon="📋", initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, .stApp, [class*="st-"] {{
        font-family:'Inter', -apple-system, 'Segoe UI', sans-serif;
    }}
    /* Restaurar la fuente de los iconos Material (la regla global la pisa) */
    span[data-testid="stIconMaterial"] {{
        font-family:'Material Symbols Rounded' !important;
    }}
    .stApp {{ background-color:{FONDO}; }}
    .block-container {{ padding-top:1.2rem; padding-bottom:2rem; max-width:1280px; }}
    h1,h2,h3,h4 {{ color:{TXT}; font-weight:700; letter-spacing:-0.3px; }}

    /* ---- Hero ---- */
    .hero {{
        background:linear-gradient(120deg, #0B3B36 0%, {PRIM_OSC} 55%, {PRIMARIO} 100%);
        border-radius:18px; padding:26px 32px 22px 32px; margin-bottom:18px;
        box-shadow:0 8px 24px rgba(11,59,54,0.18);
    }}
    .hero-title {{ color:#FFFFFF; font-size:1.65rem; font-weight:800; letter-spacing:-0.6px; margin:0; }}
    .hero-sub {{ color:#A7E8DF; font-size:0.88rem; margin-top:4px; font-weight:500; }}
    .hero-badge {{
        display:inline-block; background:rgba(255,255,255,0.14); color:#E6FFFA;
        border:1px solid rgba(255,255,255,0.22); border-radius:999px;
        padding:3px 12px; font-size:0.72rem; font-weight:600; margin-top:10px; margin-right:6px;
    }}

    /* ---- Tarjetas (contenedores st-key-card*) ---- */
    div[class*="st-key-card"] {{
        background:{CARD} !important; border:1px solid {BORDE} !important;
        border-radius:16px !important; padding:14px 20px !important;
        box-shadow:0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.04) !important;
    }}
    div[class*="st-key-card"] .vega-embed, div[class*="st-key-card"] canvas {{ background:transparent !important; }}

    /* ---- KPIs ---- */
    div[data-testid="stMetric"] {{
        background:{CARD}; border:1px solid {BORDE}; border-radius:16px;
        padding:16px 20px; min-height:128px;
        box-shadow:0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.04);
    }}
    div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] > div {{
        color:{TXT}; font-weight:800; letter-spacing:-0.5px; font-size:1.6rem !important;
    }}
    div[data-testid="stMetricLabel"] p {{
        color:{TXT_MED} !important; font-size:0.74rem !important; font-weight:600 !important;
        text-transform:uppercase; letter-spacing:0.6px;
    }}
    div[data-testid="stMetricDelta"] {{ font-size:0.8rem; }}
    section[data-testid="stSidebar"] {{ background:{CARD}; }}

    /* ---- Pestañas ---- */
    button[data-baseweb="tab"] {{ font-weight:600; color:{TXT_MED}; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color:{PRIMARIO}; }}
    div[data-baseweb="tab-highlight"] {{ background-color:{PRIMARIO} !important; height:3px; border-radius:3px; }}
    div[data-testid="stTabs"] div[role="tabpanel"] {{ background:transparent !important; }}

    /* ---- Píldoras de urgencia ---- */
    .pill-c {{ display:inline-block; border-radius:999px; padding:2px 10px;
        font-size:0.74rem; font-weight:700; white-space:nowrap; }}
    .pill-rojo {{ background:#FEE2E2; color:#B91C1C; }}
    .pill-ambar {{ background:#FEF3C7; color:{AMBAR}; }}
    .pill-verde {{ background:#D1FAE5; color:{VERDE_OK}; }}
    .pill-gris {{ background:#F1F5F9; color:{TXT_MED}; }}
    .fecha-sm {{ font-size:0.72rem; color:{TXT_SUAVE}; }}

    /* ---- Vista detalle ---- */
    .det-head {{ background:{CARD}; border:1px solid {BORDE}; border-left:5px solid {PRIMARIO};
        border-radius:14px; padding:20px 24px; margin-bottom:12px;
        box-shadow:0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.04); }}
    .det-head h2 {{ margin:10px 0 6px 0; font-size:1.35rem; }}
    .det-desc {{ color:{TXT_MED}; font-size:0.93rem; line-height:1.55; }}
    .pill {{ display:inline-block; background:{PRIM_TINTE}; color:{PRIM_OSC}; border-radius:999px;
        padding:4px 14px; font-size:0.78rem; font-weight:600; margin-right:8px; }}
    .infocard {{ background:{CARD}; border:1px solid {BORDE}; border-radius:14px;
        border-top:3px solid {PRIMARIO}; padding:14px 18px; height:100%; min-height:120px;
        box-sizing:border-box; display:flex; flex-direction:column;
        box-shadow:0 1px 2px rgba(15,23,42,0.04); }}
    .ic-label {{ color:{TXT_MED}; font-size:0.74rem; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:7px; font-weight:600; }}
    .ic-value {{ color:{TXT}; font-size:1.0rem; font-weight:700; line-height:1.3; word-break:break-word; }}
    .ic-monto {{ color:{PRIMARIO}; font-size:1.3rem; font-weight:800; }}
    div[class*="st-key-detcols"] div[data-testid="stColumn"] {{ display:flex; }}

    .meta-table {{ width:100%; border-collapse:collapse; font-size:0.9rem; }}
    .meta-table td {{ padding:10px 14px; border-bottom:1px solid {BORDE}; color:{TXT}; }}
    .meta-table tr:last-child td {{ border-bottom:none; }}
    .meta-table td:first-child {{ color:{TXT_MED}; font-weight:600; width:210px; background:#F8FAFC; }}

    /* ---- Botones ---- */
    div[data-testid="stButton"] > button {{ background:{PRIMARIO}; color:#fff; border:none;
        border-radius:10px; font-weight:600; }}
    div[data-testid="stButton"] > button:hover {{ background:{PRIM_OSC}; color:#fff; }}
    div[data-testid="stDownloadButton"] > button {{
        background:{CARD}; color:{PRIMARIO}; border:1.5px solid {PRIMARIO}; border-radius:10px; font-weight:600; }}
    div[data-testid="stDownloadButton"] > button:hover {{ background:{PRIM_TINTE}; }}
    div[data-testid="stLinkButton"] > a {{ background:{PRIMARIO}; color:#fff !important; border:none;
        border-radius:10px; font-weight:600; }}
    div[data-testid="stLinkButton"] > a:hover {{ background:{PRIM_OSC}; color:#fff !important; }}

    /* ---- Chip de código ---- */
    .cod-chip {{ font-family:'SF Mono', Consolas, monospace; font-size:0.74rem; background:#F1F5F9;
        color:#334155; border:1px solid {BORDE}; padding:3px 8px; border-radius:7px;
        display:inline-block; word-break:break-all; line-height:1.4; }}

    /* ---- Tabla ---- */
    div[class*="st-key-card_tabla"] div[data-testid="stButton"] > button {{
        background:transparent !important; border:none !important; color:{PRIMARIO} !important;
        padding:2px 4px !important; min-height:0 !important; }}
    div[class*="st-key-card_tabla"] div[data-testid="stButton"] > button:hover {{
        color:{PRIM_OSC} !important; background:{PRIM_TINTE} !important; border-radius:8px; }}
    div[class*="st-key-fila"] div[data-testid="stHorizontalBlock"] {{ align-items:center; }}
    div[class*="st-key-fila"] p {{ font-size:0.85rem; margin-bottom:0; overflow-wrap:anywhere; line-height:1.4; }}
    div[class*="st-key-filapar"] {{ background:#F8FAFC; border-bottom:1px solid #EEF2F6; padding:7px 6px; }}
    div[class*="st-key-filaimp"] {{ background:{CARD}; border-bottom:1px solid #EEF2F6; padding:7px 6px; }}
    div[class*="st-key-filahead"] {{ background:{PRIM_OSC}; border-radius:10px; margin-bottom:4px; padding:2px 6px; }}
    div[class*="st-key-filahead"] p {{ color:#fff !important; font-weight:700; margin-bottom:0; font-size:0.8rem; }}

    .org-cap {{ color:{TXT_SUAVE}; font-size:0.74rem; }}
</style>
""", unsafe_allow_html=True)


def _leer(path):
    df = pd.read_csv(path)
    # format="ISO8601": la API mezcla fechas con y sin milisegundos; sin esto
    # pandas infiere el formato de la primera fila y anula las que no calzan
    df["_cierre_dt"] = pd.to_datetime(df.get("FechaCierre"), errors="coerce", format="ISO8601")
    if "AnioCierre" in df.columns:
        df = df[(df["AnioCierre"].isna()) | (df["AnioCierre"] >= 2024)].reset_index(drop=True)
    return df


@st.cache_data
def load_data(mtimes):
    """Un solo dataset: histórico anual + enriquecido de vigentes (sin duplicados).
    Así todos los filtros afectan a todos los elementos y se conserva la vista anual.
    `mtimes` solo invalida el caché cuando un CSV se actualiza."""
    frames = []
    if os.path.exists("licitaciones_anio.csv"):
        frames.append(_leer("licitaciones_anio.csv"))
    if os.path.exists("vigentes.csv"):
        frames.append(_leer("vigentes.csv"))
    if not frames:
        files = glob.glob("licitaciones_*.csv")
        if not files:
            return None, None
        frames.append(_leer(max(files, key=os.path.getctime)))
    df = pd.concat(frames, ignore_index=True)
    # Dedup por código, prefiriendo la fila enriquecida (la que tiene Región)
    if "Region" in df.columns:
        df["_enr"] = df["Region"].notna().astype(int)
        df = (df.sort_values("_enr", ascending=False)
                .drop_duplicates("CodigoExterno", keep="first")
                .drop(columns="_enr"))
    else:
        df = df.drop_duplicates("CodigoExterno", keep="first")
    return df.reset_index(drop=True), "combinado"


@st.cache_data
def load_evolucion(mtime):
    """Serie mensual de licitaciones (por fecha de cierre) desde evolucion.csv."""
    df = pd.read_csv("evolucion.csv", usecols=["FechaCierre"])
    dt = pd.to_datetime(df["FechaCierre"], errors="coerce", format="ISO8601").dropna()
    mes = dt.dt.to_period("M").dt.to_timestamp()
    out = mes.value_counts().sort_index().reset_index()
    out.columns = ["Mes", "Cantidad"]
    lim_sup = pd.Timestamp.now() + pd.DateOffset(months=12)
    return out[(out["Mes"] >= "2020-01-01") & (out["Mes"] <= lim_sup)]


@st.cache_data
def load_intel(mtime):
    """Agregados de inteligencia de mercado construidos por intel.py (datos abiertos ChileCompra)."""
    lic = pd.read_csv("intel_licitaciones.csv")
    lic["CodigoEstado"] = pd.to_numeric(lic["CodigoEstado"], errors="coerce")
    for c in ("NumeroOferentes", "MontoEstimado", "MontoAdjudicado", "CantidadReclamos"):
        lic[c] = pd.to_numeric(lic[c], errors="coerce")
    prov = pd.read_csv("intel_proveedores.csv")
    return lic, prov


HAY_INTEL = os.path.exists("intel_licitaciones.csv") and os.path.exists("intel_proveedores.csv")
E_DESIERTA, E_ADJUDICADA = 7, 8


@st.cache_resource
def get_client():
    from client import MercadoPublicoClient
    load_dotenv()
    ticket = os.getenv("MERCADO_PUBLICO_API_TICKET")
    if not ticket:
        try:
            ticket = st.secrets["MERCADO_PUBLICO_API_TICKET"]
        except Exception:
            ticket = None
    return MercadoPublicoClient(ticket) if ticket else None


data, source_file = load_data(tuple(os.path.getmtime(f) for f in
                                    ("licitaciones_anio.csv", "vigentes.csv") if os.path.exists(f)))
if data is None:
    st.warning("No se encontró ningún CSV. Ejecuta:  `python main.py --estado activas --salida vigentes.csv`")
    st.stop()

HOY = pd.Timestamp.now().normalize()


def fmt_pesos(v):
    """Formato CLP abreviado: $850.000, $8,5M, $25M, $1.500M."""
    if v >= 1e7:
        return "$" + f"{v/1e6:,.0f}".replace(",", ".") + "M"
    if v >= 1e6:
        return "$" + f"{v/1e6:.1f}".replace(".", ",") + "M"
    return "$" + f"{v:,.0f}".replace(",", ".")


def pill_cierre(dt):
    """Píldora con los días restantes al cierre, coloreada por urgencia."""
    if pd.isna(dt):
        return "—"
    d = (dt.normalize() - HOY).days
    fecha = dt.strftime("%d-%m-%Y")
    if d < 0:
        return f"<span class='pill-c pill-gris'>Cerrada</span><br><span class='fecha-sm'>{fecha}</span>"
    if d == 0:
        cls, txt = "pill-rojo", "Cierra hoy"
    elif d <= 3:
        cls, txt = "pill-rojo", f"{d} día{'s' if d > 1 else ''}"
    elif d <= 7:
        cls, txt = "pill-ambar", f"{d} días"
    else:
        cls, txt = "pill-verde", f"{d} días"
    return f"<span class='pill-c {cls}'>{txt}</span><br><span class='fecha-sm'>{fecha}</span>"


# ================= VISTA DETALLE (pantalla separada, SPA por estado) =================
@st.fragment
def detalle_contenido(codigo, df):
    cliente = get_client()
    fila = df[df["CodigoExterno"] == codigo]
    if cliente is None:
        st.error("No hay ticket configurado (.env) para cargar el detalle.")
        return
    with st.spinner("Cargando detalle desde la API..."):
        det = None
        for _ in range(6):
            r = cliente.fetch_tenders(codigo=codigo)
            if isinstance(r, dict) and r.get("Codigo") == 10500:
                time.sleep(3); continue
            lst = r.get("Listado") if isinstance(r, dict) else None
            det = lst[0] if lst else None
            break
    if not det:
        st.warning("No se pudo cargar el detalle (rate-limit de la API).")
        if st.button("Reintentar"):
            st.rerun(scope="fragment")
        return

    comprador = det.get("Comprador") or {}
    fechas = det.get("Fechas") or {}
    monto = det.get("MontoEstimado")
    cat = fila["Categoria"].iloc[0] if not fila.empty and "Categoria" in fila else "—"
    tipo = fila["Tipo"].iloc[0] if not fila.empty and "Tipo" in fila else "—"
    estado = det.get("Estado") or (fila["Estado"].iloc[0] if not fila.empty else "—")
    e = _html.escape
    desc = det.get("Descripcion") or "Sin descripción"

    cierre_raw = det.get("FechaCierre") or fechas.get("FechaCierre")
    cierre_dt = pd.to_datetime(cierre_raw, errors="coerce")
    cierre_pill = ""
    if pd.notna(cierre_dt):
        d = (cierre_dt.normalize() - HOY).days
        if d >= 0:
            cls = "pill-rojo" if d <= 3 else ("pill-ambar" if d <= 7 else "pill-verde")
            txt = "Cierra hoy" if d == 0 else f"Cierra en {d} día{'s' if d > 1 else ''}"
            cierre_pill = f'<span class="pill-c {cls}">{txt}</span>'

    st.markdown(
        f'<div class="det-head">'
        f'<span class="pill">{e(str(codigo))}</span>'
        f'<span class="pill">{e(str(cat))}</span>'
        f'<span class="pill">{e(str(estado))}</span>'
        f'{cierre_pill}'
        f'<h2>{e(det.get("Nombre","") or "")}</h2>'
        f'<div class="det-desc">{e(desc[:800])}{"…" if len(desc) > 800 else ""}</div>'
        f'</div>', unsafe_allow_html=True)
    if len(desc) > 800:
        with st.expander("Ver descripción completa"):
            st.write(desc)

    monto_txt = f"${monto:,.0f}".replace(",", ".") if monto else "No publicado"
    with st.container(key="detcols"):
        cols = st.columns(3)
        for col, (lab, val, extra) in zip(cols, [
            ("Organismo", comprador.get("NombreOrganismo") or "—", ""),
            ("Región", (comprador.get("RegionUnidad") or "—").strip(), ""),
            ("Monto estimado", monto_txt, "ic-monto")]):
            col.markdown(f'<div class="infocard"><div class="ic-label">{lab}</div>'
                         f'<div class="ic-value {extra}">{e(str(val))}</div></div>',
                         unsafe_allow_html=True)

    def f_fecha(v):
        d = pd.to_datetime(v, errors="coerce")
        if pd.isna(d):
            return None
        return d.strftime("%d-%m-%Y %H:%M") if (d.hour or d.minute) else d.strftime("%d-%m-%Y")

    def si_no(v):
        return {"1": "Sí", "0": "No", 1: "Sí", 0: "No"}.get(v)

    def tabla_meta(pares):
        filas = "".join(
            f"<tr><td>{e(str(k))}</td><td>{e(str(v) if v not in (None, '') else '—')}</td></tr>"
            for k, v in pares)
        return f'<table class="meta-table">{filas}</table>'

    contacto = " · ".join(x for x in [comprador.get("NombreUsuario"),
                                      comprador.get("CargoUsuario")] if x)
    reclamos = det.get("CantidadReclamos")
    meta = [
        ("Tipo", tipo), ("Estado", estado),
        ("Comuna", comprador.get("ComunaUnidad")),
        ("Unidad de compra", comprador.get("NombreUnidad")),
        ("Dirección de la unidad", comprador.get("DireccionUnidad")),
        ("Contacto", contacto),
        ("Moneda", det.get("Moneda")),
        ("Fuente de financiamiento", det.get("FuenteFinanciamiento")),
        ("Permite subcontratación", si_no(det.get("SubContratacion"))),
        ("Contrato renovable", si_no(det.get("EsRenovable"))),
        ("Responsable del pago", det.get("NombreResponsablePago")),
        ("Responsable del contrato", det.get("NombreResponsableContrato")),
        ("Reclamos históricos al organismo", f"{reclamos:,}".replace(",", ".") if reclamos else None),
    ]
    # El cronograma completo viene en el bloque Fechas del detalle de la API
    crono = [(lab, f_fecha(v)) for lab, v in [
        ("Publicación", fechas.get("FechaPublicacion")),
        ("Inicio de preguntas", fechas.get("FechaInicio")),
        ("Fin de preguntas", fechas.get("FechaFinal")),
        ("Publicación de respuestas", fechas.get("FechaPubRespuestas")),
        ("Visita a terreno", fechas.get("FechaVisitaTerreno")),
        ("Entrega de antecedentes", fechas.get("FechaEntregaAntecedentes")),
        ("Cierre de ofertas", cierre_raw),
        ("Apertura técnica", fechas.get("FechaActoAperturaTecnica")),
        ("Apertura económica", fechas.get("FechaActoAperturaEconomica")),
        ("Adjudicación estimada", fechas.get("FechaEstimadaAdjudicacion") or fechas.get("FechaAdjudicacion")),
    ] if f_fecha(v)]

    st.write("")
    c_izq, c_der = st.columns(2)
    with c_izq, st.container(key="card_crono"):
        st.markdown("##### Cronograma del proceso")
        st.markdown(tabla_meta(crono), unsafe_allow_html=True)
    with c_der, st.container(key="card_meta"):
        st.markdown("##### Información adicional")
        st.markdown(tabla_meta(meta), unsafe_allow_html=True)

    items = (det.get("Items") or {}).get("Listado") or []
    if items:
        st.write("")
        with st.container(key="card_items"):
            st.markdown(f"##### Ítems solicitados ({len(items)})")
            df_items = pd.DataFrame([{
                "Producto": it.get("NombreProducto"),
                "Descripción": it.get("Descripcion"),
                "Cantidad": it.get("Cantidad"),
                "Unidad": it.get("UnidadMedida"),
                "Rubro (UNSPSC)": it.get("Categoria"),
            } for it in items])
            st.dataframe(df_items, hide_index=True, width="stretch")

    # Inteligencia: competencia histórica en el rubro (datos abiertos, últimos meses)
    if items and HAY_INTEL:
        rubro_det = (items[0].get("Categoria") or "").split("/")[0].strip().upper()
        lic_i, prov_i = load_intel(os.path.getmtime("intel_licitaciones.csv"))
        sub = lic_i[lic_i["Rubro"].astype(str).str.strip().str.upper() == rubro_det]
        res = sub[sub["CodigoEstado"].isin([E_DESIERTA, E_ADJUDICADA])]
        if len(res) >= 20:
            adjs_r = res[res["CodigoEstado"] == E_ADJUDICADA]
            st.write("")
            with st.container(key="card_compet"):
                st.markdown("##### Competencia esperada en este rubro")
                cc = st.columns(4)
                cc[0].metric("Licitaciones resueltas", f"{len(res):,}".replace(",", "."),
                             delta="últimos 6 meses", delta_color="off")
                prom = adjs_r["NumeroOferentes"].mean()
                cc[1].metric("Promedio de oferentes", f"{prom:.1f}" if pd.notna(prom) else "—")
                unico = (adjs_r["NumeroOferentes"] == 1).mean() * 100 if len(adjs_r) else None
                cc[2].metric("Adjudicada a oferente único", f"{unico:.0f}%" if unico is not None else "—",
                             help="Licitaciones donde solo ofertó una empresa: señal de baja competencia")
                desierta = (res["CodigoEstado"] == E_DESIERTA).mean() * 100
                cc[3].metric("Queda desierta", f"{desierta:.0f}%",
                             help="Sin oferentes o con ofertas inadmisibles: oportunidad si puedes cumplir las bases")
                top_prov = (prov_i[prov_i["Rubro"].astype(str).str.strip().str.upper() == rubro_det]
                            .groupby("NombreProveedor")["MontoAdjudicado"].sum()
                            .sort_values(ascending=False).head(3))
                if len(top_prov):
                    lst = " · ".join(f"**{e(str(n))}** ({fmt_pesos(m)})" for n, m in top_prov.items())
                    st.markdown(f"Quiénes más ganan en este rubro: {lst}")
                st.caption(f"Rubro: {rubro_det.title()} · Fuente: datos abiertos ChileCompra")

    adj = det.get("Adjudicacion")
    if adj:
        adj_items = [(it, it.get("Adjudicacion")) for it in items if it.get("Adjudicacion")]
        total_adj = sum((a.get("MontoUnitario") or 0) * (a.get("Cantidad") or 0)
                        for _, a in adj_items)
        st.write("")
        with st.container(key="card_adj"):
            st.markdown("##### Resultado de adjudicación")
            ca = st.columns(3)
            ca[0].metric("Oferentes", adj.get("NumeroOferentes") or "—")
            ca[1].metric("Fecha de adjudicación", f_fecha(adj.get("Fecha")) or "—")
            ca[2].metric("Monto adjudicado (total)",
                         "$" + f"{total_adj:,.0f}".replace(",", ".") if total_adj else "—")
            if adj_items:
                df_adj = pd.DataFrame([{
                    "Producto": it.get("NombreProducto"),
                    "Proveedor adjudicado": a.get("NombreProveedor"),
                    "RUT": a.get("RutProveedor"),
                    "Cantidad": a.get("Cantidad"),
                    "Monto unitario": a.get("MontoUnitario"),
                } for it, a in adj_items])
                st.dataframe(df_adj, hide_index=True, width="stretch",
                             column_config={"Monto unitario": st.column_config.NumberColumn(format="$%d")})
            if adj.get("UrlActa"):
                st.link_button("Ver acta de adjudicación oficial ↗", adj["UrlActa"])

    st.write("")
    # idlicitacion=<código> redirige a la ficha oficial exacta (DetailsAcquisition con token qs)
    st.link_button(
        "Abrir esta licitación en Mercado Público ↗",
        f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}")


if st.session_state.get("codigo"):
    if st.button("← Volver al dashboard", key="volver"):
        st.session_state.pop("codigo", None)
        st.rerun()
    st.write("")
    detalle_contenido(st.session_state["codigo"], data)
    st.stop()


# ================= DASHBOARD =================
n_vig_total = int((data.get("Vigencia") == "Vigente").sum())
act = ""
if os.path.exists("vigentes.csv"):
    act = pd.Timestamp(os.path.getmtime("vigentes.csv"), unit="s").strftime("%d-%m-%Y %H:%M")
st.markdown(
    f'<div class="hero">'
    f'<p class="hero-title">Licitaciones Públicas de Chile</p>'
    f'<p class="hero-sub">Explorador de oportunidades de negocio con el Estado · API Mercado Público · ChileCompra</p>'
    f'<span class="hero-badge">⏱ Actualizado: {act or "—"}</span>'
    f'<span class="hero-badge">📂 {len(data):,} licitaciones</span>'.replace(",", ".") +
    f'<span class="hero-badge">✅ {n_vig_total:,} abiertas para postular</span>'.replace(",", ".") +
    f'</div>', unsafe_allow_html=True)


def opciones_de(col):
    if col not in data.columns or data[col].dropna().empty:
        return []
    return sorted(data[col].dropna().astype(str).unique().tolist())


hay_monto = "MontoEstimado" in data.columns and (data["MontoEstimado"].fillna(0) > 0).any()

FLT_KEYS = ["flt_busqueda", "flt_vista", "flt_cat", "flt_ent", "flt_reg", "flt_monto", "flt_rango"]


def reset_filtros():
    for k in FLT_KEYS:
        st.session_state.pop(k, None)


with st.container(border=True, key="card_filtros"):
    fc = st.columns([1.8, 1.3, 1.4, 1.4, 1.4])
    busqueda = fc[0].text_input("Buscar", placeholder="nombre, organismo o código…", key="flt_busqueda")
    vista = fc[1].segmented_control("Mostrar", ["Abiertas", "Todas"], default="Abiertas", key="flt_vista")
    sel_cat = fc[2].multiselect("Categoría", opciones_de("Categoria"), key="flt_cat")
    sel_ent = fc[3].multiselect("Tipo de entidad", opciones_de("TipoEntidad"), key="flt_ent")
    sel_reg = fc[4].multiselect("Región", opciones_de("Region"), key="flt_reg")
    if hay_monto:
        maxm = float(data["MontoEstimado"].fillna(0).max())
        cortes = [c for c in [0, 1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6,
                              500e6, 1e9, 2.5e9, 5e9, 10e9] if c < maxm] + [maxm]
        opciones = [fmt_pesos(c) for c in cortes[:-1]] + ["Sin tope"]
        valores = dict(zip(opciones, cortes))
        fcm = st.columns([1.2, 3, 1])
        solo_monto = fcm[0].checkbox("Solo con monto publicado", key="flt_monto")
        sel_rango = fcm[1].select_slider("Monto estimado (CLP)", options=opciones,
                                         value=(opciones[0], opciones[-1]), key="flt_rango")
        rango_monto = (valores[sel_rango[0]], valores[sel_rango[1]])
        rango_es_todo = (sel_rango[0] == opciones[0] and sel_rango[1] == opciones[-1])
        fcm[2].button("Restablecer filtros", on_click=reset_filtros)
    else:
        solo_monto, rango_monto, rango_es_todo = False, None, True
        st.button("Restablecer filtros", on_click=reset_filtros)


def aplicar(df, completo=True, incluir_cerradas=False):
    d = df
    if busqueda:
        mask = pd.Series(False, index=d.index)
        for col in ["Nombre", "Organismo", "CodigoExterno", "Descripcion"]:
            if col in d.columns:
                mask |= d[col].astype(str).str.contains(busqueda, case=False, na=False)
        d = d[mask]
    if not incluir_cerradas and vista == "Abiertas" and "Vigencia" in d.columns:
        d = d[d["Vigencia"] == "Vigente"]
    if completo:
        for col, sel in [("Categoria", sel_cat), ("TipoEntidad", sel_ent), ("Region", sel_reg)]:
            if sel and col in d.columns:
                d = d[d[col].astype(str).isin(sel)]
        if hay_monto and solo_monto and "MontoEstimado" in d.columns:
            d = d[d["MontoEstimado"].fillna(0) > 0]
        if hay_monto and not rango_es_todo and "MontoEstimado" in d.columns:
            # Al acotar el rango se excluyen las licitaciones sin monto publicado:
            # quien filtra por monto quiere comparar montos reales
            m = d["MontoEstimado"].fillna(0)
            d = d[(m > 0) & m.between(rango_monto[0], rango_monto[1])]
    return d


f = aplicar(data).reset_index(drop=True)

# ---------------- KPIs ----------------
fmt = lambda n: f"{int(n):,}".replace(",", ".")
dias = (f["_cierre_dt"] - HOY).dt.days
n_vig = int((f.get("Vigencia") == "Vigente").sum())
pct_vig = (n_vig / len(f) * 100) if len(f) else 0
urgentes = int(((dias >= 0) & (dias <= 7)).sum())
hoy_cierran = int((dias == 0).sum())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Abiertas para postular", fmt(n_vig),
          delta=f"{pct_vig:.0f}% de {fmt(len(f))} resultados", delta_color="off")
k2.metric("Cierran en ≤ 7 días", fmt(urgentes),
          delta=f"{fmt(hoy_cierran)} cierran hoy", delta_color="off",
          help="Oportunidades urgentes: requieren preparar la oferta de inmediato")
if hay_monto:
    m_pos = f["MontoEstimado"].dropna()
    m_pos = m_pos[m_pos > 0]
    mediana = m_pos.median() if len(m_pos) else 0
    k3.metric("Monto típico (mediana)", fmt_pesos(mediana) if mediana else "—",
              delta=f"Total {fmt_pesos(m_pos.sum())}" if len(m_pos) else "Sin montos publicados",
              delta_color="off",
              help="Mediana de los montos publicados: el tamaño típico de una licitación, sin la distorsión de los mega-contratos")
else:
    k3.metric("Categorías", fmt(f["Categoria"].nunique()) if "Categoria" in f else "—",
              delta="clasificación temática", delta_color="off")
n_org = f["Organismo"].nunique() if "Organismo" in f.columns else 0
n_reg = f["Region"].nunique() if "Region" in f.columns else 0
k4.metric("Organismos compradores", fmt(n_org) if n_org else "—",
          delta=f"en {fmt(n_reg)} regiones" if n_reg else "sin dato de comprador", delta_color="off",
          help="Entidades públicas distintas presentes en los resultados filtrados")

st.download_button("⬇ Descargar resultados (CSV)",
                   f.drop(columns=["_cierre_dt"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                   "licitaciones_filtrado.csv", "text/csv")

AXIS = dict(labelColor=TXT, titleColor=TXT_MED)


def barra_horizontal(df_count, campo, color):
    return (
        alt.Chart(df_count).mark_bar(color=color, cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
        .encode(
            x=alt.X("Cantidad:Q", title=None,
                    scale=alt.Scale(domain=[0, df_count["Cantidad"].max() * 1.12]),
                    axis=alt.Axis(labelColor=TXT_MED, gridColor="#EEF2F6")),
            y=alt.Y(f"{campo}:N", sort="-x", title=None, axis=alt.Axis(labelColor=TXT, labelLimit=420)),
            tooltip=[campo, "Cantidad"],
        )
        .properties(height=max(220, 32 * len(df_count)), padding={"right": 16}, background="transparent")
        .configure_view(strokeWidth=0)
    )


# ---------------- Gráficos en pestañas ----------------
hay_evo = os.path.exists("evolucion.csv")
nombres_tabs = ["Contexto anual", "Categoría", "Tipo de entidad", "Tipo de licitación"]
if hay_evo:
    nombres_tabs.append("Evolución 2020-2026")
if HAY_INTEL:
    nombres_tabs.append("Inteligencia de mercado")

with st.container(border=True, key="card_charts"):
    pestañas = st.tabs(nombres_tabs)

    with pestañas[0]:
        # Flujo completo: incluye las cerradas aunque la vista esté en "Abiertas"
        actual = str(HOY.year)
        g = aplicar(data, incluir_cerradas=True).dropna(subset=["MesCierre", "AnioCierre"]).copy()
        if g.empty:
            st.info("Sin datos para el contexto anual.")
        else:
            g["AnioCierre"] = g["AnioCierre"].astype("Int64").astype(str)
            top = g["AnioCierre"].value_counts().head(3).index.tolist()
            g["AnioGrupo"] = g["AnioCierre"].where(g["AnioCierre"].isin(top), "Otros")
            # El año en curso se divide en dos series apiladas: ya cerradas / por cerrar.
            # Los años anteriores son siempre cerradas: se explicita en la leyenda.
            es_act = g["AnioGrupo"] == actual
            previo = ~es_act & (g["AnioGrupo"] != "Otros")
            g["Serie"] = g["AnioGrupo"]
            g.loc[es_act & (g["Vigencia"] == "Vigente"), "Serie"] = f"{actual} · por cerrar"
            g.loc[es_act & (g["Vigencia"] != "Vigente"), "Serie"] = f"{actual} · ya cerradas"
            g.loc[previo, "Serie"] = g.loc[previo, "AnioGrupo"] + " · cerradas"
            grupos = sorted([a for a in g["AnioGrupo"].unique() if a != "Otros"])
            if "Otros" in g["AnioGrupo"].values:
                grupos += ["Otros"]
            dominio, colores = [], []
            gris_seq = ["#475569", "#94A3B8"]  # slate oscuro y medio: visibles sobre blanco
            gi = 0
            for a in grupos:
                if a == actual:
                    dominio += [f"{actual} · ya cerradas", f"{actual} · por cerrar"]
                    colores += ["#F0B429", PRIMARIO]
                elif a == "Otros":
                    dominio.append("Otros"); colores.append("#CBD5E1")
                else:
                    dominio.append(f"{a} · cerradas"); colores.append(gris_seq[gi % 2]); gi += 1
            conteo = g.groupby(["MesCierre", "Serie"]).size().reset_index(name="Cantidad")
            grid = pd.DataFrame(list(product(MESES_ORDEN, dominio)), columns=["MesCierre", "Serie"])
            conteo = grid.merge(conteo, on=["MesCierre", "Serie"], how="left").fillna({"Cantidad": 0})
            conteo["Cantidad"] = conteo["Cantidad"].astype(int)
            conteo["AnioGrupo"] = conteo["Serie"].map(
                {s: (actual if s.startswith(f"{actual} ·") else s.replace(" · cerradas", "")) for s in dominio})
            ymax = conteo.groupby(["MesCierre", "AnioGrupo"])["Cantidad"].sum().max()
            chart = (
                alt.Chart(conteo).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                .encode(
                    x=alt.X("MesCierre:N", sort=MESES_ORDEN, title="Mes de cierre", axis=alt.Axis(labelAngle=0, **AXIS)),
                    y=alt.Y("sum(Cantidad):Q", title=None,
                            scale=alt.Scale(domain=[0, ymax * 1.18]),
                            axis=alt.Axis(labelColor=TXT_MED, gridColor="#EEF2F6", tickCount=5)),
                    color=alt.Color("Serie:N", title="Año / estado",
                                    scale=alt.Scale(domain=dominio, range=colores)),
                    xOffset=alt.XOffset("AnioGrupo:N", sort=grupos),
                    order=alt.Order("color_Serie_sort_index:Q"),
                    tooltip=["Serie", "MesCierre", "Cantidad"],
                )
                .properties(height=330, padding={"top": 16, "right": 12}, background="transparent")
                .configure_view(strokeWidth=0)
            )
            st.altair_chart(chart, width="stretch")
            st.caption(f"Los años anteriores (grises) son licitaciones ya cerradas. La barra de {actual} apila lo ya "
                       "cerrado (ámbar) y lo aún abierto para postular (teal): la proporción muestra el flujo del año. "
                       "Este gráfico ignora el selector Abiertas/Todas; el resto de los filtros sí aplica.")

    with pestañas[1]:
        cat = f["Categoria"].fillna("Sin clasificar").value_counts().head(15).reset_index()
        cat.columns = ["Categoria", "Cantidad"]
        st.altair_chart(barra_horizontal(cat, "Categoria", PRIMARIO), width="stretch")

    with pestañas[2]:
        if "TipoEntidad" in f.columns:
            ent = f["TipoEntidad"].fillna("Sin dato").value_counts().reset_index()
            ent.columns = ["TipoEntidad", "Cantidad"]
            st.altair_chart(barra_horizontal(ent, "TipoEntidad", CIAN), width="stretch")
        else:
            st.info("Disponible al terminar el enriquecimiento de vigentes.")

    with pestañas[3]:
        tip = f["Tipo"].fillna("(Sin dato)").value_counts().head(12).reset_index()
        tip.columns = ["Tipo", "Cantidad"]
        st.altair_chart(barra_horizontal(tip, "Tipo", "#64748B"), width="stretch")

    if hay_evo:
        with pestañas[4]:
            evo = load_evolucion(os.path.getmtime("evolucion.csv"))
            if evo.empty:
                st.info("Aún no hay datos de evolución.")
            else:
                base = alt.Chart(evo).encode(
                    x=alt.X("Mes:T", title=None, axis=alt.Axis(format="%b %Y", labelColor=TXT_MED)),
                    y=alt.Y("Cantidad:Q", title="Licitaciones por mes de cierre",
                            axis=alt.Axis(labelColor=TXT_MED, titleColor=TXT_MED, gridColor="#EEF2F6")),
                    tooltip=[alt.Tooltip("Mes:T", format="%b %Y"), "Cantidad"],
                )
                area = base.mark_area(opacity=0.18, color=PRIMARIO)
                linea = base.mark_line(color=PRIMARIO, strokeWidth=2.5, point=alt.OverlayMarkDef(size=18, color=PRIM_OSC))
                st.altair_chart((area + linea).properties(height=330, background="transparent")
                                .configure_view(strokeWidth=0), width="stretch")
                st.caption("Serie histórica completa (2020 a hoy), independiente de los filtros superiores.")

    if HAY_INTEL:
        with pestañas[nombres_tabs.index("Inteligencia de mercado")]:
            lic_i, prov_i = load_intel(os.path.getmtime("intel_licitaciones.csv"))
            per_min, per_max = lic_i["Periodo"].min(), lic_i["Periodo"].max()

            ic = st.columns(3)
            si_sector = ic[0].multiselect("Sector", sorted(lic_i["Sector"].dropna().unique()), key="int_sector")
            si_rubro = ic[1].multiselect("Rubro (UNSPSC)", sorted(lic_i["Rubro"].dropna().unique()), key="int_rubro")
            si_region = ic[2].multiselect("Región", sorted(lic_i["Region"].dropna().unique()), key="int_region")
            d_i = lic_i
            for col, sel in [("Sector", si_sector), ("Rubro", si_rubro), ("Region", si_region)]:
                if sel:
                    d_i = d_i[d_i[col].isin(sel)]

            res = d_i[d_i["CodigoEstado"].isin([E_DESIERTA, E_ADJUDICADA])]
            adjs = res[res["CodigoEstado"] == E_ADJUDICADA]
            ki = st.columns(4)
            ki[0].metric("Licitaciones resueltas", fmt(len(res)),
                         delta=f"de {fmt(len(d_i))} analizadas", delta_color="off",
                         help="Licitaciones que terminaron adjudicadas o desiertas en el período")
            unico = (adjs["NumeroOferentes"] == 1).mean() * 100 if len(adjs) else 0
            ki[1].metric("Adjudicadas a oferente único", f"{unico:.0f}%",
                         delta="señal de baja competencia", delta_color="off",
                         help="Solo una empresa ofertó: nichos con espacio para nuevos proveedores")
            desierta = (res["CodigoEstado"] == E_DESIERTA).mean() * 100 if len(res) else 0
            ki[2].metric("Quedan desiertas", f"{desierta:.0f}%",
                         delta="nadie ofertó o nada cumplió", delta_color="off",
                         help="El organismo suele relicitar: oportunidad para quien sí cumple las bases")
            b = adjs[(adjs["Moneda"] == "CLP") & (adjs["MontoEstimado"] > 0) & (adjs["MontoAdjudicado"] > 0)]
            ratio = (b["MontoAdjudicado"] / b["MontoEstimado"]).median() if len(b) else None
            ki[3].metric("Adjudicado vs presupuesto", f"{ratio*100:.0f}%" if ratio else "—",
                         delta="mediana sobre el monto estimado", delta_color="off",
                         help="Bajo 100%: en este segmento se gana ofertando por debajo del presupuesto publicado")

            g1, g2 = st.columns(2)
            with g1:
                st.markdown("###### ¿Cuánta competencia hay por rubro?")
                rub = (adjs.dropna(subset=["Rubro"]).groupby("Rubro")
                       .agg(Licitaciones=("CodigoExterno", "count"),
                            Oferentes=("NumeroOferentes", "mean"),
                            Unico=("NumeroOferentes", lambda s: (s == 1).mean() * 100))
                       .reset_index().nlargest(12, "Licitaciones"))
                if rub.empty:
                    st.info("Sin datos con los filtros actuales.")
                else:
                    st.altair_chart(
                        alt.Chart(rub).mark_bar(color=PRIMARIO, cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                        .encode(
                            x=alt.X("Oferentes:Q", title="Promedio de oferentes",
                                    axis=alt.Axis(labelColor=TXT_MED, gridColor="#EEF2F6")),
                            y=alt.Y("Rubro:N", sort="-x", title=None,
                                    axis=alt.Axis(labelColor=TXT, labelLimit=300)),
                            tooltip=["Rubro", alt.Tooltip("Oferentes:Q", format=".1f"),
                                     "Licitaciones", alt.Tooltip("Unico:Q", title="% oferente único", format=".0f")],
                        ).properties(height=380, background="transparent").configure_view(strokeWidth=0),
                        width="stretch")
                    st.caption("Pocos oferentes = más fácil ganar. Pasa el cursor para ver el % con oferente único.")
            with g2:
                st.markdown("###### ¿Dónde quedan desiertas? (por sector)")
                des = (res.dropna(subset=["Sector"]).groupby("Sector")
                       .agg(Resueltas=("CodigoExterno", "count"),
                            Desiertas=("CodigoEstado", lambda s: (s == E_DESIERTA).mean() * 100))
                       .reset_index())
                des = des[des["Resueltas"] >= 50].nlargest(12, "Desiertas")
                if des.empty:
                    st.info("Sin sectores con volumen suficiente (≥50 resueltas).")
                else:
                    st.altair_chart(
                        alt.Chart(des).mark_bar(color=AMBAR, cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                        .encode(
                            x=alt.X("Desiertas:Q", title="% que queda desierta",
                                    axis=alt.Axis(labelColor=TXT_MED, gridColor="#EEF2F6")),
                            y=alt.Y("Sector:N", sort="-x", title=None,
                                    axis=alt.Axis(labelColor=TXT, labelLimit=300)),
                            tooltip=["Sector", alt.Tooltip("Desiertas:Q", format=".0f"), "Resueltas"],
                        ).properties(height=380, background="transparent").configure_view(strokeWidth=0),
                        width="stretch")
                    st.caption("Una tasa alta de desiertas indica demanda insatisfecha: el organismo deberá relicitar.")

            st.markdown("###### ¿Quiénes más le venden al Estado?" +
                        (f" · rubro: {', '.join(si_rubro)}" if si_rubro else ""))
            pv = prov_i[prov_i["Rubro"].isin(si_rubro)] if si_rubro else prov_i
            top_pv = (pv.groupby("NombreProveedor", as_index=False)
                      .agg(Monto=("MontoAdjudicado", "sum"), Licitaciones=("CodigoExterno", "nunique"))
                      .nlargest(15, "Monto"))
            top_pv["MontoM"] = top_pv["Monto"] / 1e6
            st.altair_chart(
                alt.Chart(top_pv).mark_bar(color=CIAN, cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                .encode(
                    x=alt.X("MontoM:Q", title="Monto adjudicado (millones CLP)",
                            axis=alt.Axis(labelColor=TXT_MED, gridColor="#EEF2F6", format=",.0f")),
                    y=alt.Y("NombreProveedor:N", sort="-x", title=None,
                            axis=alt.Axis(labelColor=TXT, labelLimit=340)),
                    tooltip=["NombreProveedor", alt.Tooltip("MontoM:Q", title="Millones CLP", format=",.0f"),
                             "Licitaciones"],
                ).properties(height=400, background="transparent").configure_view(strokeWidth=0),
                width="stretch")
            st.caption(f"Tu competencia directa: a quiénes se les adjudicó más (solo CLP). Responde al filtro de rubro; "
                       f"sector y región no aplican aquí. Fuente: datos abiertos ChileCompra, períodos {per_min} a {per_max}.")

            st.divider()
            st.markdown("###### Ficha de competidor")
            fc1, fc2 = st.columns([2, 3])
            q_prov = fc1.text_input("Buscar proveedor", placeholder="nombre o RUT (mín. 3 caracteres)…",
                                    key="int_prov_q")
            rut_sel = None
            if q_prov and len(q_prov.strip()) >= 3:
                qn = q_prov.strip()
                m = prov_i[prov_i["NombreProveedor"].astype(str).str.contains(qn, case=False, na=False, regex=False) |
                           prov_i["RutProveedor"].astype(str).str.contains(qn, na=False, regex=False)]
                cands = (m.groupby(["RutProveedor", "NombreProveedor"])["MontoAdjudicado"].sum()
                          .sort_values(ascending=False).head(25).reset_index())
                if cands.empty:
                    fc2.info("Sin adjudicaciones que coincidan en los últimos 6 meses.")
                else:
                    opciones = {f"{r.NombreProveedor} · {r.RutProveedor}": r.RutProveedor
                                for r in cands.itertuples()}
                    elegido = fc2.selectbox("Coincidencias (ordenadas por monto adjudicado)",
                                            list(opciones), key="int_prov_sel")
                    rut_sel = opciones[elegido]
            if rut_sel:
                pvf = prov_i[prov_i["RutProveedor"] == rut_sel]
                kf = st.columns(4)
                kf[0].metric("Monto adjudicado (6 meses)", fmt_pesos(pvf["MontoAdjudicado"].sum()))
                kf[1].metric("Licitaciones ganadas", fmt(pvf["CodigoExterno"].nunique()))
                kf[2].metric("Organismos clientes", fmt(pvf["Organismo"].nunique()))
                kf[3].metric("Rubros distintos", fmt(pvf["Rubro"].nunique()))

                tend = (pvf.groupby("Periodo", as_index=False)
                        .agg(MontoM=("MontoAdjudicado", lambda s: s.sum() / 1e6),
                             Licitaciones=("CodigoExterno", "nunique")))
                st.altair_chart(
                    alt.Chart(tend).mark_bar(color=PRIMARIO, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=42)
                    .encode(x=alt.X("Periodo:N", title=None, axis=alt.Axis(labelAngle=0, labelColor=TXT)),
                            y=alt.Y("MontoM:Q", title="Adjudicado (millones CLP)",
                                    axis=alt.Axis(labelColor=TXT_MED, titleColor=TXT_MED, gridColor="#EEF2F6", format=",.0f")),
                            tooltip=["Periodo", alt.Tooltip("MontoM:Q", title="Millones CLP", format=",.0f"), "Licitaciones"])
                    .properties(height=180, background="transparent").configure_view(strokeWidth=0),
                    width="stretch")

                ga, gb = st.columns(2)
                for col, campo, titulo, color in [(ga, "Rubro", "Sus rubros (por monto)", CIAN),
                                                  (gb, "Organismo", "Sus clientes (por monto)", "#64748B")]:
                    top_f = (pvf.dropna(subset=[campo]).groupby(campo, as_index=False)
                             .agg(MontoM=("MontoAdjudicado", lambda s: s.sum() / 1e6),
                                  Licitaciones=("CodigoExterno", "nunique"))
                             .nlargest(8, "MontoM"))
                    with col:
                        st.markdown(f"**{titulo}**")
                        st.altair_chart(
                            alt.Chart(top_f).mark_bar(color=color, cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                            .encode(x=alt.X("MontoM:Q", title="Millones CLP",
                                            axis=alt.Axis(labelColor=TXT_MED, gridColor="#EEF2F6", format=",.0f")),
                                    y=alt.Y(f"{campo}:N", sort="-x", title=None,
                                            axis=alt.Axis(labelColor=TXT, labelLimit=280)),
                                    tooltip=[campo, alt.Tooltip("MontoM:Q", title="Millones CLP", format=",.0f"),
                                             "Licitaciones"])
                            .properties(height=260, background="transparent").configure_view(strokeWidth=0),
                            width="stretch")

                st.markdown("**Últimas licitaciones que ganó**")
                rec = (pvf.sort_values(["Periodo", "MontoAdjudicado"], ascending=False).head(12)
                       [["CodigoExterno", "NombreLicitacion", "Organismo", "MontoAdjudicado", "Periodo"]]
                       .copy())
                rec["Ficha"] = ("https://www.mercadopublico.cl/Procurement/Modules/RFB/"
                                "DetailsAcquisition.aspx?idlicitacion=" + rec["CodigoExterno"].astype(str))
                st.dataframe(rec, hide_index=True, width="stretch", column_config={
                    "CodigoExterno": "Código",
                    "NombreLicitacion": "Licitación",
                    "MontoAdjudicado": st.column_config.NumberColumn("Monto adjudicado", format="$%d"),
                    "Ficha": st.column_config.LinkColumn("Ficha oficial", display_text="abrir ↗"),
                })
                st.caption("Qué gana, a quién le vende y cuánto: tu competencia directa con nombre y apellido. "
                           "Solo adjudicaciones en CLP de los últimos 6 meses.")


# ---------------- Tabla con filas nativas (flecha = detalle, SPA) ----------------
def monto_txt(v):
    if pd.notna(v) and v and v > 0:
        return "$" + format(int(v), ",").replace(",", ".")
    return "—"


with st.container(border=True, key="card_tabla"):
    ct = st.columns([3, 1.6])
    ct[0].markdown(f"##### Listado · {len(f):,} licitaciones".replace(",", "."))
    orden = ct[1].selectbox("Ordenar por", ["Cierre más próximo", "Mayor monto"],
                            key="ord_tabla", label_visibility="collapsed")
    if orden == "Cierre más próximo":
        futuro = f["_cierre_dt"].where(f["_cierre_dt"] >= HOY)
        f = f.assign(_ord=futuro).sort_values("_ord", na_position="last").drop(columns="_ord")
    elif "MontoEstimado" in f.columns:
        f = f.sort_values("MontoEstimado", ascending=False, na_position="last")

    page_size = 15
    n_pages = max(1, (len(f) + page_size - 1) // page_size)
    cpg = st.columns([1, 4])
    pagina = cpg[0].number_input("Página", 1, n_pages, 1, key="pg_tabla")
    cpg[1].caption(f"Página {pagina} de {n_pages}")
    sub = f.iloc[(pagina - 1) * page_size: pagina * page_size]

    RAT = [0.45, 1.7, 4.2, 2.4, 1.4, 1.6]
    with st.container(key="filahead"):
        h = st.columns(RAT)
        for c, t in zip(h, ["", "Código", "Nombre", "Organismo", "Monto est.", "Cierre"]):
            c.markdown(f"**{t}**")

    e = _html.escape
    for pos, (i, row) in enumerate(sub.iterrows()):
        rk = f"filapar_{i}" if pos % 2 == 0 else f"filaimp_{i}"
        with st.container(key=rk):
            rc = st.columns(RAT, vertical_alignment="center")
            if rc[0].button("", key=f"go_{row['CodigoExterno']}",
                            icon=":material/chevron_right:", type="tertiary",
                            help="Ver detalle"):
                st.session_state["codigo"] = row["CodigoExterno"]
                st.rerun()
            rc[1].markdown(f"<span class='cod-chip'>{e(str(row['CodigoExterno']))}</span>", unsafe_allow_html=True)
            nombre_html = e(str(row.get("Nombre", "")))
            cat_row = row.get("Categoria")
            if pd.notna(cat_row) and cat_row:
                nombre_html += f"<br><span class='org-cap'>{e(str(cat_row))}</span>"
            rc[2].markdown(nombre_html, unsafe_allow_html=True)
            org = row.get("Organismo")
            rc[3].markdown(e(str(org)) if pd.notna(org) and org else "—")
            rc[4].markdown(monto_txt(row.get("MontoEstimado")) if hay_monto else "—")
            rc[5].markdown(pill_cierre(row["_cierre_dt"]), unsafe_allow_html=True)
