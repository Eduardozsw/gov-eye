"""Diário Oficial da União: arquivos mensais em XML publicados pela Imprensa Nacional.

Os arquivos são grandes (a Seção 1 de janeiro/2023 tem ~530 MB) e o servidor
recusa downloads parciais (HTTP Range), então a verificação rápida só confere
o início do arquivo. A verificação completa baixa o mês inteiro e procura um
ato conhecido.
"""

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import httpx

from .base import Resultado, Status

NOME = "Diário Oficial da União"
LISTAGEM_URL = "https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados"
PASTA_BRUTOS = Path("data/raw/dou")

# Ato de referência: MP 1.157/2023, que prorrogou a redução de PIS/Cofins sobre combustíveis.
ANO, MES, NOME_MES = 2023, 1, "Janeiro"
REFERENCIA_TIPO, REFERENCIA_NUMERO = "Medida Provisória", "1.157"


def _link_secao1(cliente: httpx.Client) -> str | None:
    resp = cliente.get(LISTAGEM_URL, params={"ano": ANO, "mes": NOME_MES})
    resp.raise_for_status()
    arquivo = f"S01{MES:02d}{ANO}.zip"
    links = re.findall(r'href="([^"]+)"', resp.text)
    return next((l.replace("&amp;", "&") for l in links if arquivo in l), None)


def _procurar_referencia(caminho: Path) -> tuple[int, dict[str, str] | None]:
    with zipfile.ZipFile(caminho) as zf:
        xmls = [n for n in zf.namelist() if n.endswith(".xml")]
        for nome in xmls:
            artigo = ET.fromstring(zf.read(nome)).find("article")
            if artigo is None or artigo.get("artType") != REFERENCIA_TIPO:
                continue
            identifica = (artigo.findtext("body/Identifica") or "").strip()
            if REFERENCIA_NUMERO in identifica:
                return len(xmls), {
                    "identifica": identifica,
                    "data": artigo.get("pubDate", ""),
                    "ementa": (artigo.findtext("body/Ementa") or "").strip(),
                    "pdf": artigo.get("pdfPage", ""),
                }
    return len(xmls), None


def verificar(cliente: httpx.Client, completo: bool = False) -> Resultado:
    link = _link_secao1(cliente)
    if not link:
        return Resultado(NOME, Status.FALHA, f"Link da Seção 1 de {NOME_MES}/{ANO} não encontrado na listagem")

    if not completo:
        with cliente.stream("GET", link) as resp:
            resp.raise_for_status()
            inicio = next(resp.iter_bytes(4), b"")
            tamanho = int(resp.headers.get("content-length", 0))
        if not inicio.startswith(b"PK"):
            return Resultado(NOME, Status.FALHA, "Arquivo não é ZIP")
        return Resultado(
            NOME,
            Status.OK,
            "ZIP mensal acessível (verificação rápida)",
            [
                f"Seção 1 de {NOME_MES}/{ANO}: {tamanho / 2**20:,.0f} MB",
                "Rode com --dou-completo para baixar o mês e localizar a MP 1.157/2023",
            ],
        )

    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_BRUTOS / f"S01{MES:02d}{ANO}.zip"
    if not caminho.exists():
        temporario = caminho.with_suffix(".parcial")
        with cliente.stream("GET", link) as resp, temporario.open("wb") as destino:
            resp.raise_for_status()
            for bloco in resp.iter_bytes(2**20):
                destino.write(bloco)
        temporario.rename(caminho)

    total, achado = _procurar_referencia(caminho)
    if not achado:
        return Resultado(NOME, Status.FALHA, f"MP {REFERENCIA_NUMERO} não encontrada em {total} atos")
    return Resultado(
        NOME,
        Status.OK,
        "XML estruturado com tipo, órgão, ementa e texto de cada ato",
        [
            f"{total} atos na Seção 1 de {NOME_MES}/{ANO}",
            f"Encontrado: {achado['identifica']} (publicado em {achado['data']})",
            f"Ementa: {achado['ementa'][:160]}…",
        ],
        amostra=achado,
    )
