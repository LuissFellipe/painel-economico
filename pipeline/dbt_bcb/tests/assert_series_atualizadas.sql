-- Avisa quando a API parou de entregar: a Selic e o dólar saem todo dia útil,
-- o IPCA uma vez por mês, uns 10 dias depois de o mês fechar.
{{ config(severity='warn') }}

select nome_serie, max(data) as ultima
from {{ ref('stg_bcb__series') }}
group by 1
having max(data) < current_date - case nome_serie when 'ipca_mensal' then 75 else 7 end
