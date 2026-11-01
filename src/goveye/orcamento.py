"""Regras de cálculo do orçamento por tema: filtro pelo mapeamento, totais, inflação e conferência."""

from collections import defaultdict
from dataclasses import dataclass

from .modelo import AcaoMapeada

ESTAGIOS = ("projeto_lei", "inicial", "atualizada", "empenhado", "liquidado", "pago")
ESTAGIOS_CONFERIDOS = ("inicial", "atualizada", "empenhado", "pago")
NOMES_ESTAGIOS = {
    "projeto_lei": "Proposto pelo Executivo",
    "inicial": "Aprovado na lei orçamentária",
    "atualizada": "Autorizado (após créditos e cortes)",
    "empenhado": "Empenhado (comprometido)",
    "liquidado": "Liquidado (entregue)",
    "pago": "Pago",
}
# Diferença máxima aceita entre SIOP e Portal da Transparência, em reais.
TOLERANCIA_CONFERENCIA = 1.0


@dataclass(frozen=True)
class Divergencia:
    ano: int
    chave: str  # "AÇÃO/SUBFUNÇÃO"
    estagio: str
    siop: float
    portal: float


def mapeamento_aplicavel(linha: dict, mapeamento: list[AcaoMapeada]) -> AcaoMapeada | None:
    return next(
        (m for m in mapeamento if m.codigo == linha["acao"] and m.vale_em(linha["ano"], linha["subfuncao"])),
        None,
    )


def linhas_do_tema(linhas_siop: list[dict], mapeamento: list[AcaoMapeada], tema_id: str) -> list[dict]:
    do_tema = [m for m in mapeamento if m.tema_id == tema_id]
    return [l for l in linhas_siop if mapeamento_aplicavel(l, do_tema)]


def totais_por_ano(linhas: list[dict]) -> dict[int, dict[str, float]]:
    totais: dict[int, dict[str, float]] = defaultdict(lambda: dict.fromkeys(ESTAGIOS, 0.0))
    for l in linhas:
        for e in ESTAGIOS:
            totais[l["ano"]][e] += l[e]
    return dict(sorted(totais.items()))


def mes_referencia(ipca: dict[str, float]) -> str:
    return max(ipca)


def fator_correcao(ipca: dict[str, float], ano: int, referencia: str) -> float:
    """Multiplicador que leva valores de um ano a preços do mês de referência.

    Usa o índice de dezembro do ano (ou o último mês disponível, no ano em andamento).
    """
    meses_do_ano = sorted(m for m in ipca if m.startswith(str(ano)))
    if not meses_do_ano:
        raise ValueError(f"IPCA sem dados para {ano}")
    return ipca[referencia] / ipca[meses_do_ano[-1]]


def conferir(linhas_siop: list[dict], portal_por_ano: dict[int, dict[str, dict[str, float]]]) -> list[Divergencia]:
    """Compara SIOP e Portal da Transparência por ação e subfunção, nos estágios que os dois publicam."""
    siop: dict[tuple[int, str], dict[str, float]] = defaultdict(lambda: dict.fromkeys(ESTAGIOS_CONFERIDOS, 0.0))
    for l in linhas_siop:
        for e in ESTAGIOS_CONFERIDOS:
            siop[(l["ano"], f"{l['acao']}/{l['subfuncao']}")][e] += l[e]

    divergencias = []
    chaves = set(siop) | {(ano, k) for ano, d in portal_por_ano.items() for k in d}
    for ano, chave in sorted(chaves):
        if ano not in portal_por_ano:
            continue
        a = siop.get((ano, chave), dict.fromkeys(ESTAGIOS_CONFERIDOS, 0.0))
        b = portal_por_ano[ano].get(chave, dict.fromkeys(ESTAGIOS_CONFERIDOS, 0.0))
        for e in ESTAGIOS_CONFERIDOS:
            if abs(a[e] - b[e]) > TOLERANCIA_CONFERENCIA:
                divergencias.append(Divergencia(ano, chave, e, a[e], b[e]))
    return divergencias
