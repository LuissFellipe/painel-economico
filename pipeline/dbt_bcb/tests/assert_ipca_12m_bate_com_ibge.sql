-- O IPCA 12 meses de dezembro tem de ser o IPCA do ano que o IBGE divulga.
-- O BCB publica o IPCA mensal com duas casas, e compor doze valores
-- arredondados dá até 0,01 ponto de diferença (2022: 5,78 contra 5,79).
-- Acima de 0,02 ponto, a conta composta ou a janela de 12 meses estão erradas.
select
    i.ano,
    i.ipca_pct as ibge,
    f.ipca_12m as calculado
from {{ ref('ipca_anual_ibge') }} i
left join {{ ref('fct_indicadores_mensais') }} f
    on f.mes = make_date(i.ano, 12, 1)
where f.ipca_12m is null or abs(f.ipca_12m - i.ipca_pct) > 0.02
