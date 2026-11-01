"""Portal da Transparência (CGU): orçamento da despesa e API de dados."""

import csv
import io
import os
import zipfile

import httpx

from .base import Resultado, Status

ARQUIVO_URL = "https://portaldatransparencia.gov.br/download-de-dados/orcamento-despesa/{ano}"
API_URL = "https://api.portaldatransparencia.gov.br/api-de-dados/orgaos-siafi"
VARIAVEL_CHAVE = "PORTAL_TRANSPARENCIA_API_KEY"

# Ação de referência: 20YP, Promoção, Proteção e Recuperação da Saúde Indígena.
ANO, ACAO = 2023, "20YP"
COLUNAS = {
    "inicial": "ORÇAMENTO INICIAL (R$)",
    "atualizada": "ORÇAMENTO ATUALIZADO (R$)",
    "empenhado": "ORÇAMENTO EMPENHADO (R$)",
    "pago": "ORÇAMENTO REALIZADO (R$)",
}


def _numero(texto: str) -> float:
    return float(texto.replace(".", "").replace(",", "."))


def verificar_arquivos(cliente: httpx.Client) -> Resultado:
    nome = "Portal da Transparência (arquivos)"
    resp = cliente.get(ARQUIVO_URL.format(ano=ANO))
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        conteudo = zf.read(zf.namelist()[0]).decode("latin-1")
    leitor = csv.DictReader(io.StringIO(conteudo), delimiter=";")

    faltando = set(COLUNAS.values()) - set(leitor.fieldnames or [])
    if faltando:
        return Resultado(nome, Status.FALHA, "Colunas esperadas ausentes", [str(sorted(faltando))])

    totais = dict.fromkeys(COLUNAS, 0.0)
    linhas = 0
    for linha in leitor:
        linhas += 1
        if linha["CÓDIGO AÇÃO"] == ACAO:
            for chave, coluna in COLUNAS.items():
                totais[chave] += _numero(linha[coluna])

    return Resultado(
        nome,
        Status.OK,
        "CSV anual por ação, sem chave, mas sem o estágio 'liquidado'",
        [
            f"{len(resp.content) // 1024} KB compactado, {linhas} linhas em {ANO}",
            f"Ação {ACAO} em {ANO}: pago R$ {totais['pago']:,.2f}",
            "A coluna 'realizado' corresponde ao valor pago (conferido contra o SIOP)",
        ],
        amostra={"acao": ACAO, "ano": ANO, **totais},
    )


def verificar_api(cliente: httpx.Client) -> Resultado:
    nome = "Portal da Transparência (API)"
    chave = os.environ.get(VARIAVEL_CHAVE)
    if not chave:
        return Resultado(
            nome,
            Status.PENDENTE,
            "Exige chave gratuita",
            [
                "Cadastro: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email",
                f"Depois, defina {VARIAVEL_CHAVE} no arquivo .env",
            ],
        )
    resp = cliente.get(API_URL, params={"pagina": 1}, headers={"chave-api-dados": chave})
    if resp.status_code == 401:
        return Resultado(nome, Status.FALHA, "Chave recusada pela API")
    resp.raise_for_status()
    return Resultado(nome, Status.OK, "Chave aceita", [f"{len(resp.json())} órgãos na primeira página"])
