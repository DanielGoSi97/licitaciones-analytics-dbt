-- Dimension de proveedores adjudicados, con metricas de actividad agregada.
with adj as (

    select * from {{ ref('stg_intel_proveedores') }}

)

select
    rut_proveedor,
    max(nombre_proveedor)                       as nombre_proveedor,
    count(distinct codigo_externo)              as n_licitaciones_ganadas,
    count(distinct organismo)                   as n_organismos_cliente,
    count(distinct rubro)                       as n_rubros,
    sum(monto_adjudicado)                       as monto_adjudicado_total,
    avg(monto_adjudicado)                       as monto_adjudicado_promedio,
    min(periodo)                                as primer_periodo_activo,
    max(periodo)                                as ultimo_periodo_activo
from adj
group by rut_proveedor
