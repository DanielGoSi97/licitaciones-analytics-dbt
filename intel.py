"""Construye los datos de inteligencia de mercado desde los datos abiertos de ChileCompra.

Descarga los archivos mensuales de licitaciones (nivel oferta por línea) desde
transparenciachc.blob.core.windows.net/lic-da/<año>-<mes>.zip y genera dos
agregados compactos para el dashboard:

  - intel_licitaciones.csv : una fila por licitación (estado, organismo, sector,
    rubro, oferentes, monto estimado vs adjudicado, reclamos).
  - intel_proveedores.csv  : una fila por licitación×proveedor ganador (con rubro,
    organismo, período y monto): alimenta el top de proveedores y la ficha de competidor.

Uso:  python intel.py [--meses 6]
"""
import argparse
import io
import logging
import zipfile
from datetime import date

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger("intel")

URL = "https://transparenciachc.blob.core.windows.net/lic-da/{anio}-{mes}.zip"

USECOLS = [
    "CodigoExterno", "Nombre", "CodigoEstado", "Estado", "NombreOrganismo", "sector",
    "RegionUnidad", "CantidadReclamos", "CodigoMoneda", "MontoEstimado",
    "NumeroOferentes", "FechaCierre", "Tipo", "Rubro1",
    "RutProveedor", "NombreProveedor", "MontoLineaAdjudica", "Oferta seleccionada",
]


def meses_previos(n, ref=None):
    """Últimos n meses completos antes del mes actual, como (año, mes)."""
    ref = ref or date.today()
    anio, mes = ref.year, ref.month
    salida = []
    for _ in range(n):
        mes -= 1
        if mes == 0:
            anio, mes = anio - 1, 12
        salida.append((anio, mes))
    return sorted(salida)


def leer_mes(anio, mes):
    """Descarga y lee el CSV mensual (dentro del zip) con las columnas necesarias."""
    url = URL.format(anio=anio, mes=mes)
    logger.info(f"Descargando {url}")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    nombre = zf.namelist()[0]
    for enc in ("utf-8", "latin-1"):
        try:
            with zf.open(nombre) as f:
                df = pd.read_csv(f, sep=";", usecols=USECOLS, encoding=enc,
                                 dtype=str, on_bad_lines="skip")
            break
        except UnicodeDecodeError:
            continue
    df["Periodo"] = f"{anio}-{mes:02d}"
    logger.info(f"  {anio}-{mes:02d}: {len(df):,} filas (oferta-línea)")
    return df


def agregar(df):
    """Colapsa el nivel oferta-línea a una fila por licitación + agregado proveedor-rubro."""
    for col in ("MontoEstimado", "MontoLineaAdjudica", "NumeroOferentes", "CantidadReclamos"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    sel = df["Oferta seleccionada"].str.strip().str.lower().eq("seleccionada")

    # Monto adjudicado por licitación: solo líneas seleccionadas y en CLP
    # (UTM/USD/EUR distorsionarían las sumas sin conversión).
    # Los datos abiertos traen errores de digitación groseros (líneas por sobre
    # los $20.000M, montos 10^5 veces el presupuesto): se excluyen del monto.
    clp = df["CodigoMoneda"].str.strip().eq("CLP")
    linea_ok = df["MontoLineaAdjudica"].between(0, 2e10)
    adj = (df[sel & clp & linea_ok].groupby("CodigoExterno")["MontoLineaAdjudica"]
           .sum().rename("MontoAdjudicado"))

    lic = (df.groupby("CodigoExterno", as_index=False)
             .agg(Estado=("Estado", "first"), CodigoEstado=("CodigoEstado", "first"),
                  Organismo=("NombreOrganismo", "first"), Sector=("sector", "first"),
                  Region=("RegionUnidad", "first"), Tipo=("Tipo", "first"),
                  Rubro=("Rubro1", lambda s: s.mode().iat[0] if not s.mode().empty else None),
                  Moneda=("CodigoMoneda", "first"), MontoEstimado=("MontoEstimado", "max"),
                  NumeroOferentes=("NumeroOferentes", "max"),
                  CantidadReclamos=("CantidadReclamos", "max"),
                  FechaCierre=("FechaCierre", "first"), Periodo=("Periodo", "max"))
             .merge(adj, on="CodigoExterno", how="left"))
    sospechosa = (lic["MontoEstimado"] > 0) & (lic["MontoAdjudicado"] > 300 * lic["MontoEstimado"])
    lic.loc[sospechosa, "MontoAdjudicado"] = None

    # Ganadores: una fila por licitación×proveedor, con los atributos de la licitación
    wins = (df[sel & clp & linea_ok & df["NombreProveedor"].notna()]
            .groupby(["CodigoExterno", "RutProveedor", "NombreProveedor"], as_index=False)
            .agg(NombreLicitacion=("Nombre", "first"),
                 MontoAdjudicado=("MontoLineaAdjudica", "sum")))
    wins = wins.merge(lic[["CodigoExterno", "Rubro", "Organismo", "Region", "Periodo"]],
                      on="CodigoExterno", how="left")
    return lic, wins


def main():
    parser = argparse.ArgumentParser(description="Inteligencia de mercado desde datos abiertos ChileCompra")
    parser.add_argument("--meses", type=int, default=6, help="Meses completos hacia atrás (por defecto 6)")
    args = parser.parse_args()

    lics, provs = [], []
    for anio, mes in meses_previos(args.meses):
        try:
            df = leer_mes(anio, mes)
        except Exception as e:
            logger.warning(f"  {anio}-{mes:02d}: no disponible ({e}), se omite")
            continue
        lic, prov = agregar(df)
        lics.append(lic)
        provs.append(prov)
        del df

    if not lics:
        logger.error("No se pudo descargar ningún mes.")
        return

    # Una licitación puede aparecer en varios meses (publicación vs adjudicación):
    # se conserva la versión más reciente, que trae el estado final
    lic = (pd.concat(lics, ignore_index=True)
             .sort_values("Periodo")
             .drop_duplicates("CodigoExterno", keep="last"))
    prov = (pd.concat(provs, ignore_index=True)
              .sort_values("Periodo")
              .drop_duplicates(["CodigoExterno", "RutProveedor"], keep="last"))

    lic.to_csv("intel_licitaciones.csv", index=False, encoding="utf-8-sig")
    prov.to_csv("intel_proveedores.csv", index=False, encoding="utf-8-sig")
    logger.info(f"intel_licitaciones.csv: {len(lic):,} licitaciones | "
                f"intel_proveedores.csv: {len(prov):,} filas licitación-ganador")


if __name__ == "__main__":
    main()
