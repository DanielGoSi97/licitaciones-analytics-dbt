import os
import time
import argparse
import pandas as pd
import logging
from dotenv import load_dotenv
from client import MercadoPublicoClient
from collections import Counter
from models import (TenderAPIResponse, TIPO_LICITACION_MAP, ESTADO_MAP,
                    categoria_tematica, clasificar_entidad)
from datetime import datetime, timedelta

# Configuración de logging para el script principal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")


def fetch_detail(client, codigo, max_retries=6):
    """Obtiene el detalle de una licitación, reintentando ante el rate-limit (10500).

    Tolera cualquier error de red/HTTP por licitación: devuelve None en vez de propagar,
    para que una fila problemática no aborte todo el proceso.
    """
    for _ in range(max_retries):
        try:
            det = client.fetch_tenders(codigo=codigo)
        except Exception as e:
            logger.warning(f"  detalle {codigo} falló: {e}")
            return None
        if isinstance(det, dict) and det.get('Codigo') == 10500:
            time.sleep(4)
            continue
        listado = det.get('Listado') if isinstance(det, dict) else None
        if listado:
            return listado[0]
        return None
    return None


def calcular_vigencia(estado, fecha_cierre):
    """Determina si la licitación está vigente (se puede postular) o fuera de plazo."""
    # Solo las 'Publicada' admiten ofertas; el resto ya cerró su ciclo.
    if estado == "Publicada":
        if fecha_cierre:
            try:
                cierre = datetime.fromisoformat(str(fecha_cierre).replace("Z", ""))
                return "Vigente" if cierre >= datetime.now() else "Fuera de plazo"
            except (ValueError, TypeError):
                return "Vigente"
        return "Vigente"
    return "Fuera de plazo"


def categoria_desde_items(items):
    """Categoría real (UNSPSC): nivel superior más frecuente entre los ítems del detalle."""
    tops = []
    for it in items or []:
        cat = it.get('Categoria')
        if cat:
            tops.append(cat.split('/')[0].strip())
    if not tops:
        return None
    return Counter(tops).most_common(1)[0][0]


def enrich_tender(detalle):
    """Aplana el detalle de una licitación en los campos relevantes para análisis."""
    comprador = detalle.get('Comprador') or {}
    fechas = detalle.get('Fechas') or {}
    adjudicacion = detalle.get('Adjudicacion') or {}
    items = (detalle.get('Items') or {}).get('Listado') or []
    tipo_code = detalle.get('Tipo')
    estado = ESTADO_MAP.get(detalle.get('CodigoEstado'), detalle.get('Estado'))
    fecha_cierre = detalle.get('FechaCierre') or fechas.get('FechaCierre')
    fecha_pub = fechas.get('FechaPublicacion')
    anio, mes_num, mes_nom = partes_fecha(fecha_cierre)
    organismo = comprador.get('NombreOrganismo')
    # Categoría real desde los ítems (UNSPSC); si no hay, cae al heurístico por nombre
    categoria = categoria_desde_items(items) or categoria_tematica(detalle.get('Nombre'))
    # Adjudicación por ítem: monto total y proveedor(es) ganador(es)
    adj_items = [it.get('Adjudicacion') for it in items if it.get('Adjudicacion')]
    monto_adj = sum((a.get('MontoUnitario') or 0) * (a.get('Cantidad') or 0) for a in adj_items)
    proveedores = sorted({a.get('NombreProveedor') for a in adj_items if a.get('NombreProveedor')})
    return {
        'CodigoExterno': detalle.get('CodigoExterno'),
        'Nombre': detalle.get('Nombre'),
        'Descripcion': detalle.get('Descripcion'),
        'Categoria': categoria,
        'Estado': estado,
        'Vigencia': calcular_vigencia(estado, fecha_cierre),
        'Tipo': TIPO_LICITACION_MAP.get(tipo_code, tipo_code),
        'Organismo': organismo,
        'TipoEntidad': clasificar_entidad(organismo),
        'Region': comprador.get('RegionUnidad'),
        'Comuna': comprador.get('ComunaUnidad'),
        'MontoEstimado': detalle.get('MontoEstimado'),
        'Moneda': detalle.get('Moneda'),
        'FechaPublicacion': fecha_pub,
        'FechaCierre': fecha_cierre,
        'AnioCierre': anio, 'MesCierreNum': mes_num, 'MesCierre': mes_nom,
        'DiasParaCierre': detalle.get('DiasCierreLicitacion'),
        'NumeroOferentes': adjudicacion.get('NumeroOferentes'),
        'CantidadItems': (detalle.get('Items') or {}).get('Cantidad'),
        'FuenteFinanciamiento': detalle.get('FuenteFinanciamiento'),
        'CantidadReclamos': detalle.get('CantidadReclamos'),
        'MontoAdjudicado': monto_adj or None,
        'ProveedorAdjudicado': "; ".join(proveedores) or None,
    }


MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def partes_fecha(fecha_iso):
    """Devuelve (anio, numero_mes, nombre_mes) desde una fecha ISO; (None, None, None) si falla."""
    if not fecha_iso:
        return None, None, None
    try:
        d = datetime.fromisoformat(str(fecha_iso).replace("Z", ""))
        return d.year, d.month, MESES[d.month - 1]
    except (ValueError, TypeError):
        return None, None, None


def basico(t):
    """Fila desde el listado (sin consultar el detalle). El listado de 'activas' ya trae FechaCierre."""
    anio, mes_num, mes_nom = partes_fecha(t.FechaCierre)
    return {
        'CodigoExterno': t.CodigoExterno, 'Nombre': t.Nombre,
        'Categoria': categoria_tematica(t.Nombre),
        'Estado': t.estado, 'Vigencia': calcular_vigencia(t.estado, t.FechaCierre),
        'Tipo': t.tipo_licitacion, 'FechaCierre': t.FechaCierre,
        'AnioCierre': anio, 'MesCierreNum': mes_num, 'MesCierre': mes_nom,
    }


def rango_fechas(desde, hasta):
    """Genera fechas ddmmaaaa entre dos fechas (inclusive)."""
    d0 = datetime.strptime(desde, "%d%m%Y")
    d1 = datetime.strptime(hasta, "%d%m%Y")
    actual = d0
    while actual <= d1:
        yield actual.strftime("%d%m%Y")
        actual += timedelta(days=1)


def recolectar(client, fecha=None, estado=None, max_retries=6):
    """Devuelve la lista de objetos Tender publicados, reintentando ante el rate-limit (10500)."""
    for _ in range(max_retries):
        raw = client.fetch_tenders(fecha=fecha, estado=estado)
        if isinstance(raw, dict) and raw.get('Codigo') == 10500:
            time.sleep(4)
            continue
        break
    if isinstance(raw, dict) and raw.get('Codigo') and raw.get('Codigo') != 0:
        logger.warning(f"La API respondió código {raw.get('Codigo')}: {raw.get('Mensaje')}")
    return TenderAPIResponse(**raw).Listado


def main():
    parser = argparse.ArgumentParser(description="Extractor de licitaciones de Mercado Público")
    parser.add_argument("fecha", nargs="?", help="Fecha única en formato ddmmaaaa (por defecto: hoy)")
    parser.add_argument("--desde", help="Inicio de rango ddmmaaaa")
    parser.add_argument("--hasta", help="Fin de rango ddmmaaaa")
    parser.add_argument("--estado", help="activas, publicada, cerrada, adjudicada, etc.")
    parser.add_argument("--sin-detalle", action="store_true",
                        help="No consulta el detalle (más rápido, menos campos). Útil para rangos grandes.")
    parser.add_argument("--salida", help="Nombre del CSV de salida (por defecto licitaciones_<timestamp>.csv)")
    parser.add_argument("--solo-cierre", action="store_true",
                        help="Guarda solo código y fecha de cierre (para series de evolución). Implica --sin-detalle.")
    args = parser.parse_args()
    if args.solo_cierre:
        args.sin_detalle = True

    load_dotenv()
    ticket = os.getenv('MERCADO_PUBLICO_API_TICKET')
    if not ticket:
        logger.error("No se encontró MERCADO_PUBLICO_API_TICKET en .env")
        return
    client = MercadoPublicoClient(ticket)

    # Construir la lista de fechas a consultar
    if args.desde and args.hasta:
        fechas = list(rango_fechas(args.desde, args.hasta))
        logger.info(f"Rango: {len(fechas)} días desde {args.desde} hasta {args.hasta}")
    else:
        fechas = [args.fecha]  # None => día actual

    try:
        # 1) Recolectar el listado de todas las fechas
        tenders = []
        for f in fechas:
            try:
                lote = recolectar(client, fecha=f, estado=args.estado)
                tenders.extend(lote)
                if f:
                    logger.info(f"  {f}: {len(lote)} licitaciones")
            except Exception as e:
                logger.warning(f"  {f}: error ({e}), se omite")

        if not tenders:
            logger.info("No se encontraron licitaciones para la consulta.")
            return

        # 2) Enriquecer con el detalle (salvo --sin-detalle)
        total = len(tenders)
        data = []
        if args.solo_cierre:
            for t in tenders:
                anio, mes_num, mes_nom = partes_fecha(t.FechaCierre)
                data.append({'CodigoExterno': t.CodigoExterno, 'FechaCierre': t.FechaCierre,
                             'AnioCierre': anio, 'MesCierreNum': mes_num, 'MesCierre': mes_nom})
            logger.info(f"{total} licitaciones (solo cierre).")
        elif args.sin_detalle:
            data = [basico(t) for t in tenders]
            logger.info(f"{total} licitaciones (sin detalle).")
        else:
            logger.info(f"{total} licitaciones. Enriqueciendo con el detalle...")
            for i, t in enumerate(tenders, 1):
                try:
                    detalle = fetch_detail(client, t.CodigoExterno)
                    data.append(enrich_tender(detalle) if detalle else basico(t))
                except Exception as e:
                    logger.warning(f"  [{i}/{total}] {t.CodigoExterno} error ({e}); fila básica")
                    data.append(basico(t))
                logger.info(f"  [{i}/{total}] {t.CodigoExterno}")

        df = pd.DataFrame(data)
        if args.salida:
            output_file = args.salida
        else:
            output_file = f'licitaciones_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"Datos guardados en {output_file} ({len(df)} licitaciones)")

    except Exception as e:
        logger.error(f"Error crítico durante la ejecución: {e}", exc_info=True)


if __name__ == "__main__":
    main()
