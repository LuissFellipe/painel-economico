-- O IPCA 12 meses e a variação do dólar usam as 12 linhas anteriores. Um mês
-- faltando no meio da série faria a janela cobrir 13 meses sem erro nenhum.
select mes, proximo
from (
    select mes, lead(mes) over (order by mes) as proximo
    from {{ ref('fct_indicadores_mensais') }}
) m
where proximo is not null and proximo <> (mes + interval '1 month')::date
