select
    codigo_serie,
    nome_serie,
    data,
    valor::numeric(14, 4) as valor
from {{ source('raw', 'sgs_series') }}
