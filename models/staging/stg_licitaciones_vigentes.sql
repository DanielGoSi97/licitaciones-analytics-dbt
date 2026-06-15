-- Licitaciones vigentes enriquecidas desde la API oficial (grano: una por licitacion).
with source as (

    select * from {{ source('chilecompra', 'vigentes') }}

),

renamed as (

    select
        trim(CodigoExterno)                      as codigo_externo,
        trim(Nombre)                             as nombre,
        trim(Categoria)                          as categoria,
        trim(Estado)                             as estado,
        trim(Tipo)                               as tipo,
        trim(Organismo)                          as organismo,
        trim(Region)                             as region,
        trim(Comuna)                             as comuna,
        trim(Moneda)                             as moneda,
        try_cast(MontoEstimado as double)        as monto_estimado,
        try_cast(FechaPublicacion as date)       as fecha_publicacion,
        try_cast(FechaCierre as date)            as fecha_cierre,
        try_cast(DiasParaCierre as integer)      as dias_para_cierre,
        try_cast(NumeroOferentes as integer)     as numero_oferentes,
        try_cast(CantidadItems as integer)       as cantidad_items,
        trim(FuenteFinanciamiento)               as fuente_financiamiento,
        try_cast(CantidadReclamos as integer)    as cantidad_reclamos,
        try_cast(MontoAdjudicado as double)      as monto_adjudicado,
        trim(ProveedorAdjudicado)                as proveedor_adjudicado
    from source
    where CodigoExterno is not null

)

select * from renamed
