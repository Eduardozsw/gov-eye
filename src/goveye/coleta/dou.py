"""Coletor do Diário Oficial da União (Seção 1).

Baixa o ZIP mensal da Imprensa Nacional, filtra os atos que interessam ao
gov-eye e guarda só esses atos em JSON Lines. O ZIP é apagado depois, a menos
que `manter_zip` seja verdadeiro, porque cada mês tem centenas de megabytes.
"""

import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from html import unescape
from pathlib import Path

import httpx

from ..config import BRUTOS, PAUSA_ENTRE_REQUISICOES

LISTAGEM_URL = "https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados"
PASTA = BRUTOS / "dou"
MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

TIPOS_NORMATIVOS = {"Lei", "Lei Complementar", "Medida Provisória", "Decreto", "Decreto numerado"}
RE_TRIBUTO = re.compile(r"PIS|Cofins|CIDE|Contribui[çc][ãa]o de Interven[çc][ãa]o no Dom[íi]nio Econ[ôo]mico", re.I)
RE_COMBUSTIVEL = re.compile(r"gasolina|diesel|combust[íi]ve|[áa]lcool|etanol|g[áa]s liquefeito|querosene", re.I)


@dataclass
class AtoDOU:
    id_materia: str
    tipo: str
    identifica: str
    ementa: str
    orgao: str
    data_publicacao: str  # AAAA-MM-DD
    edicao: str
    pagina: str
    url_pdf: str
    texto: str
    arquivo_origem: str
    sha256_xml: str


def texto_simples(html: str) -> str:
    sem_tags = re.sub(r"<(br|/p|/tr|/li)[^>]*>", "\n", html, flags=re.I)
    sem_tags = re.sub(r"<[^>]+>", " ", sem_tags)
    linhas = (re.sub(r"[ \t\xa0]+", " ", l).strip() for l in unescape(sem_tags).splitlines())
    return "\n".join(l for l in linhas if l)


def _data_iso(data_br: str) -> str:
    dia, mes, ano = data_br.split("/")
    return f"{ano}-{mes}-{dia}"


def ler_artigo(conteudo: bytes, arquivo_origem: str) -> AtoDOU | None:
    raiz = ET.fromstring(conteudo)
    artigo = raiz if raiz.tag == "article" else raiz.find("article")
    if artigo is None:
        return None
    corpo = artigo.find("body")

    def campo(nome: str) -> str:
        return ((corpo.findtext(nome) if corpo is not None else "") or "").strip()

    return AtoDOU(
        id_materia=artigo.get("idMateria", ""),
        tipo=artigo.get("artType", ""),
        identifica=campo("Identifica"),
        ementa=campo("Ementa"),
        orgao=artigo.get("artCategory", ""),
        data_publicacao=_data_iso(artigo.get("pubDate", "01/01/1900")),
        edicao=artigo.get("editionNumber", ""),
        pagina=artigo.get("numberPage", ""),
        url_pdf=unescape(artigo.get("pdfPage", "")),
        texto=texto_simples(campo("Texto")),
        arquivo_origem=arquivo_origem,
        sha256_xml=hashlib.sha256(conteudo).hexdigest(),
    )


def e_relevante(ato: AtoDOU) -> bool:
    """Atos normativos que tratam de tributos federais sobre combustíveis."""
    if ato.tipo not in TIPOS_NORMATIVOS:
        return False
    alvo = f"{ato.ementa}\n{ato.texto}"
    return bool(RE_TRIBUTO.search(alvo) and RE_COMBUSTIVEL.search(alvo))


def ler_zip(caminho: Path) -> Iterator[AtoDOU]:
    with zipfile.ZipFile(caminho) as zf:
        for nome in zf.namelist():
            if not nome.endswith(".xml"):
                continue
            try:
                ato = ler_artigo(zf.read(nome), f"{caminho.name}:{nome}")
            except ET.ParseError:
                continue
            if ato:
                yield ato


def links_do_mes(cliente: httpx.Client, ano: int, mes: int) -> list[str]:
    resp = cliente.get(LISTAGEM_URL, params={"ano": ano, "mes": MESES[mes - 1]})
    resp.raise_for_status()
    prefixo = f"S01{mes:02d}{ano}"
    links = (l.replace("&amp;", "&") for l in re.findall(r'href="([^"]+)"', resp.text))
    return sorted({l for l in links if f"/{prefixo}" in l and ".zip" in l})


def _baixar(cliente: httpx.Client, url: str, destino: Path) -> None:
    temporario = destino.with_suffix(".parcial")
    with cliente.stream("GET", url) as resp, temporario.open("wb") as arquivo:
        resp.raise_for_status()
        for bloco in resp.iter_bytes(2**20):
            arquivo.write(bloco)
    temporario.replace(destino)


def coletar_mes(cliente: httpx.Client, ano: int, mes: int, manter_zip: bool = False) -> Path:
    """Gera data/raw/dou/filtrados/AAAA-MM.jsonl com os atos relevantes do mês."""
    saida = PASTA / "filtrados" / f"{ano}-{mes:02d}.jsonl"
    if saida.exists():
        return saida
    saida.parent.mkdir(parents=True, exist_ok=True)

    links = links_do_mes(cliente, ano, mes)
    if not links:
        raise RuntimeError(f"Nenhum arquivo da Seção 1 listado para {mes:02d}/{ano}")

    relevantes: list[AtoDOU] = []
    for url in links:
        nome = re.search(r"/(S01\d{6}[^/]*?\.zip)", url).group(1)
        caminho = PASTA / nome
        baixado_agora = not caminho.exists()
        if baixado_agora:
            _baixar(cliente, url, caminho)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
        relevantes.extend(a for a in ler_zip(caminho) if e_relevante(a))
        if baixado_agora and not manter_zip:
            caminho.unlink()

    with saida.open("w", encoding="utf-8") as f:
        for ato in sorted(relevantes, key=lambda a: (a.data_publicacao, a.identifica)):
            f.write(json.dumps(asdict(ato), ensure_ascii=False) + "\n")
    return saida


def carregar_filtrados() -> list[AtoDOU]:
    atos = []
    for arquivo in sorted((PASTA / "filtrados").glob("*.jsonl")):
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            atos.append(AtoDOU(**json.loads(linha)))
    return atos
