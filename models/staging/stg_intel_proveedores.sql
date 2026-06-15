-- Adjudicaciones a nivel licitacion x proveedor ganador.
with source as (

    select * from {{ source('chilecompra', 'intel_proveedores') }}

),

renamed as (

    select
        trim(CodigoExterno)                  as codigo_externo,
        trim(RutProveedor)                   as rut_proveedor,
        trim(NombreProveedor)                as nombre_proveedor,
        trim(NombreLicitacion)               as nombre_licitacion,
        try_cast(MontoAdjudicado as double)  as monto_adjudicado,
        upper(trim(Rubro))                   as rubro,
        trim(Organismo)                      as organismo,
        trim(Region)                         as region,
        trim(Periodo)                        as periodo
    from source
    where RutProveedor is not null
      and CodigoExterno is not null

)

select * from renamed
