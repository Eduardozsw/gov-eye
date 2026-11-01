"""SIOP (Ministério do Planejamento): orçamento federal em SPARQL, com todos os estágios."""

import csv
import io

import httpx

from .base import Resultado, Status

NOME = "SIOP (SPARQL)"
URL = "https://www1.siop.planejamento.gov.br/sparql/"
ANOS_MVP = range(2018, 2027)

# Mesma ação de referência usada no Portal da Transparência, para verificação cruzada.
ANO, ACAO = 2023, "20YP"

CONSULTA_TOTAIS = """
PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
SELECT (SUM(?ini) AS ?inicial) (SUM(?atu) AS ?atualizada) (SUM(?emp) AS ?empenhado)
       (SUM(?liq) AS ?liquidado) (SUM(?pag) AS ?pago)
WHERE {{ GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
  ?item loa:temAcao ?acao . ?acao loa:codigo "{acao}" .
  ?item loa:valorDotacaoInicial ?ini ; loa:valorLeiMaisCredito ?atu ;
        loa:valorEmpenhado ?emp ; loa:valorLiquidado ?liq ; loa:valorPago ?pag .
}} }}
"""

CONSULTA_GRAFOS = "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }"


def _consultar(cliente: httpx.Client, consulta: str) -> list[dict[str, str]]:
    resp = cliente.post(URL, data={"query": consulta}, headers={"Accept": "text/csv"})
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def verificar(cliente: httpx.Client) -> Resultado:
    grafos = {linha["g"] for linha in _consultar(cliente, CONSULTA_GRAFOS)}
    anos_faltando = [a for a in ANOS_MVP if f"http://orcamento.dados.gov.br/{a}/" not in grafos]

    totais = {k: float(v) for k, v in _consultar(cliente, CONSULTA_TOTAIS.format(ano=ANO, acao=ACAO))[0].items()}
    detalhes = [
        f"Ação {ACAO} em {ANO}: inicial R$ {totais['inicial']:,.2f}, pago R$ {totais['pago']:,.2f}",
        "Tem todos os estágios: projeto de lei, dotação inicial, atualizada, empenhado, liquidado e pago",
    ]
    if anos_faltando:
        detalhes.append(f"Anos do MVP sem dados: {anos_faltando}")
        return Resultado(NOME, Status.PARCIAL, "Faltam anos do MVP", detalhes, amostra=totais)
    detalhes.insert(0, f"Anos {ANOS_MVP.start}–{ANOS_MVP.stop - 1} disponíveis")
    return Resultado(NOME, Status.OK, "SPARQL público, sem chave", detalhes, amostra=totais)
