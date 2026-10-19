with mensal as (
    select
        date_trunc('month', data)::date as mes,
        avg(valor) filter (where nome_serie = 'selic_meta') as selic_media_aa,
        max(valor) filter (where nome_serie = 'ipca_mensal') as ipca_mes,
        avg(valor) filter (where nome_serie = 'dolar_venda') as dolar_medio
    from {{ ref('stg_bcb__series') }}
    group by 1
),

com_acumulados as (
    select
        *,
        (exp(sum(ln(1 + ipca_mes / 100)) over (
            order by mes rows between 11 preceding and current row
        )) - 1) * 100 as ipca_12m,
        count(ipca_mes) over (
            order by mes rows between 11 preceding and current row
        ) as meses_na_janela
    from mensal
)

select
    mes,
    round(selic_media_aa, 2) as selic_media_aa,
    round(ipca_mes, 2) as ipca_mes,
    round(case when meses_na_janela = 12 then ipca_12m end, 2) as ipca_12m,
    round(case when meses_na_janela = 12
        then ((1 + selic_media_aa / 100) / (1 + ipca_12m / 100) - 1) * 100 end, 2) as juro_real_aa,
    round(dolar_medio, 4) as dolar_medio,
    round((dolar_medio / lag(dolar_medio, 12) over (order by mes) - 1) * 100, 2) as dolar_var_12m
from com_acumulados
order by mes
