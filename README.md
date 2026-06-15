# Licitaciones Analytics — dbt + DuckDB

Modelo de datos analítico (ELT) sobre las licitaciones del **Mercado Público de Chile (ChileCompra)**.
Toma los CSV crudos que genera un pipeline de Python desde la API oficial y los datos abiertos masivos,
y los transforma en un **esquema en estrella** listo para BI e inteligencia de mercado.

> **Warehouse-agnostic:** el proyecto corre localmente sobre **DuckDB** (cero credenciales, `dbt build` en segundos)
> y los mismos modelos se materializan en **BigQuery** cambiando solo el `profiles.yml`.

## Arquitectura

```
CSV crudos (API + datos abiertos)
        │  read_csv_auto (DuckDB)
        ▼
sources (chilecompra)
        ▼
staging/  ── limpieza, casteo de tipos, normalización, flags
        ▼
marts/    ── esquema en estrella + data marts de negocio
```

### Modelos

| Capa | Modelo | Descripción |
|------|--------|-------------|
| staging | `stg_intel_licitaciones` | Histórico limpio + flags de competencia (desierta, oferente único, brecha adj/est) |
| staging | `stg_intel_proveedores` | Adjudicaciones licitación × proveedor |
| staging | `stg_licitaciones_vigentes` | Licitaciones vigentes desde la API oficial |
| marts | `fct_licitaciones` | **Hechos**: una fila por licitación con métricas de competencia y adjudicación |
| marts | `dim_proveedor` | **Dimensión**: proveedores con actividad agregada |
| marts | `mart_competencia_por_rubro` | % oferente único, % desierta y brecha de precios por rubro |
| marts | `mart_evolucion_mensual` | Serie de tiempo del mercado |

## Cómo correrlo

```bash
pip install dbt-duckdb
dbt deps          # instala dbt_utils
dbt build         # ejecuta modelos + tests
dbt docs generate && dbt docs serve   # documentación y linaje
```

El repo incluye un snapshot de datos en `data/`, así que `dbt build` funciona apenas clonas.
Para apuntar a otra ubicación (p.ej. la salida en vivo del pipeline de Python):

```bash
dbt build --vars '{data_dir: ../}'
```

> **Nota de entorno:** dbt requiere Python 3.11–3.12 (no 3.13/3.14). Con [`uv`](https://docs.astral.sh/uv/):
> `uv venv --python 3.12 .venv && uv pip install --python .venv dbt-duckdb`

## Actualización automática (CI/CD)

Un GitHub Action (`.github/workflows/refresh-data.yml`) mantiene los datos frescos **sin depender de ninguna máquina local**:

1. **Descarga** los últimos 6 meses de datos abiertos de ChileCompra (`pipeline/intel.py`).
2. **Reconstruye** los modelos dbt y corre los tests (`dbt build`).
3. **Commitea** los CSV actualizados al repo.

Se ejecuta cada lunes (cron), de forma manual desde la pestaña *Actions*, y valida los modelos en cada push a `models/`.

## Calidad de datos

Tests declarativos en dbt (`not_null`, `unique`) sobre claves de negocio y métricas críticas.
La limpieza en staging castea tipos con `try_cast`, normaliza texto (trim/upper) y deriva los flags de competencia.

## Stack

`dbt` · `DuckDB` (dev) / `BigQuery` (prod) · `dbt_utils` · SQL · datos abiertos de ChileCompra
