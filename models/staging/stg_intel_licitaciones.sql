-- Historico de licitaciones (grano: una fila por CodigoExterno).
-- Limpia tipos, normaliza texto y deriva flags de competencia.
with source as (

    select * from {{ source('chilecompra', 'intel_licitaciones') }}

),

renamed as (

    select
        trim(CodigoExterno)                              as codigo_externo,
        trim(Estado)                                     as estado,
        try_cast(CodigoEstado as integer)                as codigo_estado,
        trim(Organismo)                                  as organismo,
        trim(Sector)                                     as sector,
        trim(Region)                                     as region,
        trim(Tipo)                                       as tipo,
        upper(trim(Rubro))                               as rubro,
        trim(Moneda)                                     as moneda,
        try_cast(MontoEstimado as double)                as monto_estimado,
        try_cast(NumeroOferentes as integer)             as numero_oferentes,
        try_cast(CantidadReclamos as integer)            as cantidad_reclamos,
        try_cast(FechaCierre as date)                    as fecha_cierre,
        trim(Periodo)                                    as periodo,        -- YYYY-MM
        try_cast(MontoAdjudicado as double)              as monto_adjudicado
    from source
    where CodigoExterno is not null

),

final as (

    select
        *,
        -- Una licitacion "desierta" no recibio ofertas o no se adjudico.
        (coalesce(numero_oferentes, 0) = 0 or monto_adjudicado is null) as es_desierta,
        -- Riesgo de baja competencia: un solo oferente.
        (numero_oferentes = 1)                                          as es_oferente_unico,
        -- Brecha adjudicado vs estimado (>1 = se adjudico por sobre lo estimado).
        case
            when monto_estimado > 0 then monto_adjudicado / monto_estimado
        end                                                             as brecha_adj_estimado
    from renamed

)

select * from final
