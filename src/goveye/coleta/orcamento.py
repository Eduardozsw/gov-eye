"""Coleta do orçamento federal: SIOP (fonte principal), Portal da Transparência (conferência) e IPCA."""

import csv
import io
import json
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import httpx

from ..config import BRUTOS, PAUSA_ENTRE_REQUISICOES

PASTA = BRUTOS / "orcamento"
SIOP_URL = "https://www1.siop.planejamento.gov.br/sparql/"
PORTAL_URL = "https://portaldatransparencia.gov.br/download-de-dados/orcamento-despesa/{ano}"
IPCA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{inicio}-{fim}"
    "/variaveis/2266?localidades=N1[all]"
)

ESTAGIOS = ("projeto_lei", "inicial", "atualizada", "empenhado", "liquidado", "pago")
ESTAGIOS_PORTAL = {
    "inicial": "ORÇAMENTO INICIAL (R$)",
    "atualizada": "ORÇAMENTO ATUALIZADO (R$)",
    "empenhado": "ORÇAMENTO EMPENHADO (R$)",
    "pago": "ORÇAMENTO REALIZADO (R$)",
}

_PREFIXOS = """
PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

CONSULTA_VALORES = _PREFIXOS + """
SELECT ?acao ?nome_acao ?programa ?nome_programa ?subfuncao
       (SUM(?pl) AS ?projeto_lei) (SUM(?ini) AS ?inicial) (SUM(?atu) AS ?atualizada)
       (SUM(?emp) AS ?empenhado) (SUM(?liq) AS ?liquidado) (SUM(?pag) AS ?pago)
WHERE {{ GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
  ?item loa:temAcao ?a . ?a loa:codigo ?acao ; rdfs:label ?nome_acao .
  FILTER(?acao IN ({codigos}))
  ?item loa:temPrograma ?p . ?p loa:codigo ?programa ; rdfs:label ?nome_programa .
  ?item loa:temSubfuncao ?sf . ?sf loa:codigo ?subfuncao .
  OPTIONAL {{ ?item loa:valorProjetoLei ?pl }}
  ?item loa:valorDotacaoInicial ?ini ; loa:valorLeiMaisCredito ?atu ;
        loa:valorEmpenhado ?emp ; loa:valorLiquidado ?liq ; loa:valorPago ?pag .
}} }}
GROUP BY ?acao ?nome_acao ?programa ?nome_programa ?subfuncao
"""

CONSULTA_CANDIDATOS = _PREFIXOS + """
SELECT ?acao ?nome_acao ?programa ?nome_programa ?subfuncao (SUM(?atu) AS ?atualizada) (SUM(?pag) AS ?pago)
WHERE {{ GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
  ?item loa:temAcao ?a . ?a loa:codigo ?acao ; rdfs:label ?nome_acao .
  ?item loa:temPrograma ?p . ?p loa:codigo ?programa ; rdfs:label ?nome_programa .
  ?item loa:temSubfuncao ?sf . ?sf loa:codigo ?subfuncao .
  ?item loa:valorLeiMaisCredito ?atu ; loa:valorPago ?pag .
  FILTER(REGEX(?nome_acao, "{padrao}", "i") || REGEX(?nome_programa, "{padrao}", "i"){filtro_subfuncao})
}} }}
GROUP BY ?acao ?nome_acao ?programa ?nome_programa ?subfuncao
ORDER BY ?acao
"""


def _sparql(cliente: httpx.Client, consulta: str) -> list[dict[str, str]]:
    resp = cliente.post(SIOP_URL, data={"query": consulta}, headers={"Accept": "text/csv"}, timeout=300)
    resp.raise_for_status()
    time.sleep(PAUSA_ENTRE_REQUISICOES)
    return list(csv.DictReader(io.StringIO(resp.text)))


def candidatos(cliente: httpx.Client, ano: int, padrao: str, subfuncoes: list[str]) -> list[dict]:
    """Ações cujo nome (ou nome do programa) casa com o padrão, ou que estão nas subfunções dadas."""
    filtro = "".join(f' || ?subfuncao = "{s}"' for s in subfuncoes)
    linhas = _sparql(cliente, CONSULTA_CANDIDATOS.format(ano=ano, padrao=padrao, filtro_subfuncao=filtro))
    return [{"ano": ano, **l, "atualizada": float(l["atualizada"]), "pago": float(l["pago"])} for l in linhas]


def valores_siop(cliente: httpx.Client, ano: int, codigos: list[str]) -> list[dict]:
    """Totais por ação e programa no ano, em todos os estágios."""
    # O Virtuoso do SIOP é antigo e não aceita VALUES; usamos FILTER IN.
    valores = ", ".join(f'"{c}"' for c in sorted(set(codigos)))
    linhas = _sparql(cliente, CONSULTA_VALORES.format(ano=ano, codigos=valores))
    return [
        {
            "ano": ano,
            "acao": l["acao"],
            "nome_acao": l["nome_acao"],
            "programa": l["programa"],
            "nome_programa": l["nome_programa"],
            "subfuncao": l["subfuncao"],
            **{e: float(l[e] or 0) for e in ESTAGIOS},
        }
        for l in linhas
    ]


def _numero(texto: str) -> float:
    return float(texto.replace(".", "").replace(",", ".")) if texto else 0.0


def valores_portal(cliente: httpx.Client, ano: int, codigos: list[str]) -> dict[str, dict[str, float]]:
    """Totais por ação e subfunção ("AÇÃO/SUBFUNÇÃO") no CSV anual do Portal da Transparência.

    O ZIP fica em cache em data/raw/orcamento/.
    """
    PASTA.mkdir(parents=True, exist_ok=True)
    zip_local = PASTA / f"portal-{ano}.zip"
    if not zip_local.exists():
        resp = cliente.get(PORTAL_URL.format(ano=ano), timeout=300)
        resp.raise_for_status()
        zip_local.write_bytes(resp.content)
        time.sleep(PAUSA_ENTRE_REQUISICOES)

    with zipfile.ZipFile(zip_local) as zf:
        texto = zf.read(zf.namelist()[0]).decode("latin-1")
    alvo = set(codigos)
    totais: dict[str, dict[str, float]] = defaultdict(lambda: dict.fromkeys(ESTAGIOS_PORTAL, 0.0))
    for linha in csv.DictReader(io.StringIO(texto), delimiter=";"):
        if linha["CÓDIGO AÇÃO"] in alvo:
            chave = f"{linha['CÓDIGO AÇÃO']}/{linha['CÓDIGO SUBFUNÇÃO']}"
            for estagio, coluna in ESTAGIOS_PORTAL.items():
                totais[chave][estagio] += _numero(linha[coluna])
    return dict(totais)


def ipca(cliente: httpx.Client, ano_inicio: int, ano_fim: int) -> dict[str, float]:
    """Número-índice mensal do IPCA, chave AAAAMM."""
    resp = cliente.get(IPCA_URL.format(inicio=f"{ano_inicio}01", fim=f"{ano_fim}12"))
    resp.raise_for_status()
    serie = resp.json()[0]["resultados"][0]["series"][0]["serie"]
    return {mes: float(v) for mes, v in serie.items() if v not in ("...", "-", "")}


def salvar(nome: str, conteudo) -> Path:
    PASTA.mkdir(parents=True, exist_ok=True)
    caminho = PASTA / nome
    caminho.write_text(json.dumps(conteudo, ensure_ascii=False, indent=1), encoding="utf-8")
    return caminho


def ler(nome: str):
    return json.loads((PASTA / nome).read_text(encoding="utf-8"))
