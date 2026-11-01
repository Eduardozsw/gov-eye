"""Etapas do pipeline (seção 7): coleta, carga no banco e geração do site."""

from pathlib import Path

from . import banco
from . import curadoria as cur
from .coleta import dou, orcamento
from .config import ANO_FINAL, ANO_INICIAL
from .fontes.base import novo_cliente


def coletar_orcamento(anos: range = range(ANO_INICIAL, ANO_FINAL + 1)) -> None:
    """Baixa SIOP, Portal da Transparência e IPCA para as ações do mapeamento."""
    c = cur.carregar()
    codigos = sorted({a.codigo for a in c.acoes})
    with novo_cliente() as cliente:
        siop, portal = [], {}
        for ano in anos:
            print(f"SIOP {ano}...", flush=True)
            siop.extend(orcamento.valores_siop(cliente, ano, codigos))
            print(f"Portal da Transparência {ano}...", flush=True)
            portal[ano] = orcamento.valores_portal(cliente, ano, codigos)
        print("IPCA...", flush=True)
        ipca = orcamento.ipca(cliente, anos.start, anos.stop - 1)

    orcamento.salvar("siop.json", siop)
    orcamento.salvar("portal.json", {str(k): v for k, v in portal.items()})
    orcamento.salvar("ipca.json", ipca)
    print(f"{len(siop)} linhas do SIOP, {len(ipca)} meses de IPCA")


def coletar_dou(meses: list[tuple[int, int]], manter_zip: bool = False) -> None:
    with novo_cliente() as cliente:
        for ano, mes in meses:
            caminho = dou.coletar_mes(cliente, ano, mes, manter_zip=manter_zip)
            total = sum(1 for _ in caminho.open(encoding="utf-8"))
            print(f"{ano}-{mes:02d}: {total} atos candidatos em {caminho}", flush=True)


def carregar() -> Path:
    """Monta o banco SQLite a partir da curadoria e das coletas já feitas."""
    c = cur.carregar()
    portal = {int(ano): v for ano, v in orcamento.ler("portal.json").items()}
    return banco.construir(c, orcamento.ler("siop.json"), portal, orcamento.ler("ipca.json"))
