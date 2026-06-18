-- Inteligencia de mercado por rubro: nivel de competencia, tasa de licitaciones
-- desiertas y brecha de precios adjudicado vs estimado.
with f as (

    select * from {{ ref('fct_licitaciones') }}

)

select
    rubro,
    count(*)                                                        as n_licitaciones,
    avg(numero_oferentes)                                           as oferentes_promedio,
    sum(case when es_oferente_unico then 1 else 0 end) * 1.0
        / nullif(count(*), 0)                                       as pct_oferente_unico,
    sum(case when es_desierta then 1 else 0 end) * 1.0
        / nullif(count(*), 0)                                       as pct_desierta,
    median(brecha_adj_estimado)                                     as brecha_adj_estimado_mediana,
    sum(monto_adjudicado)                                           as monto_adjudicado_total
from f
where rubro is not null
group by rubro
having count(*) >= 5   -- evita rubros con muy pocos casos
order by n_licitaciones desc
