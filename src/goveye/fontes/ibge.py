"""IBGE: IPCA (número-índice), usado para corrigir valores pela inflação."""

import httpx

from .base import Resultado, Status

NOME = "IBGE (IPCA)"
URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{periodos}"
    "/variaveis/2266?localidades=N1[all]"
)

# Valor publicado pelo IBGE, conferido manualmente.
REFERENCIA = ("202401", 6801.72)


def verificar(cliente: httpx.Client) -> Resultado:
    resp = cliente.get(URL.format(periodos="201801-202612"))
    resp.raise_for_status()
    serie = resp.json()[0]["resultados"][0]["series"][0]["serie"]

    periodo, esperado = REFERENCIA
    obtido = float(serie[periodo])
    meses = sorted(p for p, v in serie.items() if v not in ("...", "-"))
    detalhes = [
        f"{len(meses)} meses disponíveis, de {meses[0]} a {meses[-1]}",
        f"Referência {periodo}: esperado {esperado}, obtido {obtido}",
    ]
    if abs(obtido - esperado) > 0.01:
        return Resultado(NOME, Status.FALHA, "Valor de referência não confere", detalhes)
    return Resultado(NOME, Status.OK, "API pública, sem chave, JSON", detalhes)
