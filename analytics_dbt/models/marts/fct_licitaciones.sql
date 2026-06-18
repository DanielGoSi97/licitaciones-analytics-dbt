-- Tabla de hechos: una fila por licitacion historica, con metricas de
-- competencia y adjudicacion listas para BI.
with licitaciones as (

    select * from {{ ref('stg_intel_licitaciones') }}

),

ganadores as (

    -- Proveedor con mayor monto adjudicado por licitacion (ganador principal).
    select
        codigo_externo,
        count(distinct rut_proveedor)                       as n_proveedores_adjudicados,
        sum(monto_adjudicado)                               as monto_adjudicado_total,
        arg_max(nombre_proveedor, monto_adjudicado)         as proveedor_principal,
        arg_max(rut_proveedor, monto_adjudicado)            as rut_proveedor_principal
    from {{ ref('stg_intel_proveedores') }}
    group by 1

)

select
    l.codigo_externo,
    l.estado,
    l.organismo,
    l.sector,
    l.region,
    l.tipo,
    l.rubro,
    l.periodo,
    l.fecha_cierre,
    l.monto_estimado,
    l.monto_adjudicado,
    l.numero_oferentes,
    l.cantidad_reclamos,
    l.es_desierta,
    l.es_oferente_unico,
    l.brecha_adj_estimado,
    coalesce(g.n_proveedores_adjudicados, 0) as n_proveedores_adjudicados,
    g.proveedor_principal,
    g.rut_proveedor_principal
from licitaciones l
left join ganadores g
    on l.codigo_externo = g.codigo_externo
