-- Serie de tiempo mensual del mercado: volumen, montos y competencia por periodo.
with f as (

    select * from {{ ref('fct_licitaciones') }}

)

select
    periodo,                                                        -- YYYY-MM
    count(*)                                                        as n_licitaciones,
    sum(monto_adjudicado)                                           as monto_adjudicado_total,
    avg(numero_oferentes)                                           as oferentes_promedio,
    sum(case when es_desierta then 1 else 0 end) * 1.0
        / nullif(count(*), 0)                                       as pct_desierta
from f
where periodo is not null
group by periodo
order by periodo
