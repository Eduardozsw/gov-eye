"""Gráficos SVG gerados no servidor: funcionam sem JavaScript e podem ser lidos por leitores de tela.

Cada gráfico vem acompanhado, na página, de uma tabela ou lista com os mesmos dados.
"""

from dataclasses import dataclass
from datetime import date
from html import escape

from .formato import data_br, moeda_curta

LARGURA = 720
MARGEM_ESQ, MARGEM_DIR, MARGEM_TOPO, MARGEM_BASE = 64, 16, 28, 32


@dataclass
class Faixa:
    """Período de um mandato, desenhado como faixa de fundo."""

    inicio: date
    fim: date
    rotulo: str


@dataclass
class Degrau:
    data: date
    valor: float
    rotulo: str  # texto do <title> do marcador
    pendente: bool = False


def _escala(d0: float, d1: float, p0: float, p1: float):
    if d1 == d0:
        return lambda v: (p0 + p1) / 2
    return lambda v: p0 + (v - d0) * (p1 - p0) / (d1 - d0)


def topo_eixo(maximo: float) -> float:
    """Arredonda o máximo para cima em um valor "redondo" (1, 2, 2,5 ou 5 vezes potência de 10)."""
    if maximo <= 0:
        return 1.0
    potencia = 1.0
    while potencia * 10 <= maximo:
        potencia *= 10
    while potencia > maximo:
        potencia /= 10
    for m in (1, 2, 2.5, 5, 10):
        if maximo <= m * potencia + 1e-12:
            return m * potencia
    return 10 * potencia


def degraus(
    pontos: list[Degrau],
    faixas: list[Faixa],
    inicio: date,
    fim: date,
    formatar,
    titulo: str,
    prazos: list[tuple[date, str]] = (),
    altura: int = 260,
) -> str:
    """Série em degraus (alíquotas): o valor vale até a próxima mudança.

    `prazos` marca, com linha tracejada, o fim de vigência previsto em atos da série (seção 8.2).
    """
    x = _escala(inicio.toordinal(), fim.toordinal(), MARGEM_ESQ, LARGURA - MARGEM_DIR)
    topo = topo_eixo(max(p.valor for p in pontos) * 1.1) if pontos else 1.0
    y = _escala(0, topo, altura - MARGEM_BASE, MARGEM_TOPO)
    partes = [
        f'<svg viewBox="0 0 {LARGURA} {altura}" class="grafico" role="img" aria-label="{escape(titulo)}">',
        f"<title>{escape(titulo)}</title>",
    ]

    for n, f in enumerate(faixas):
        a, b = max(f.inicio, inicio), min(f.fim, fim)
        if a >= b:
            continue
        xa, xb = x(a.toordinal()), x(b.toordinal())
        partes.append(
            f'<rect class="faixa faixa-{n % 2}" x="{xa:.1f}" y="{MARGEM_TOPO - 18}" '
            f'width="{xb - xa:.1f}" height="{altura - MARGEM_BASE - MARGEM_TOPO + 18}"/>'
        )
        # Faixa estreita no fim do gráfico (governo em curso): o rótulo é empurrado para dentro,
        # para não ser cortado na borda. Largura estimada de 7 px por caractere a 12 px.
        meia = len(f.rotulo) * 3.5
        centro = min(max((xa + xb) / 2, meia + 2), LARGURA - meia - 2)
        partes.append(
            f'<text class="rotulo-faixa" x="{centro:.1f}" y="{MARGEM_TOPO - 6}" '
            f'text-anchor="middle">{escape(f.rotulo)}</text>'
        )

    for i in range(5):
        v = topo * i / 4
        partes.append(
            f'<line class="grade" x1="{MARGEM_ESQ}" x2="{LARGURA - MARGEM_DIR}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
            f'<text class="eixo" x="{MARGEM_ESQ - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{escape(formatar(v))}</text>'
        )
    for ano in range(inicio.year + (inicio.month > 1 or inicio.day > 1), fim.year + 1):
        xa = x(date(ano, 1, 1).toordinal())
        partes.append(
            f'<text class="eixo" x="{xa:.1f}" y="{altura - MARGEM_BASE + 18}" text-anchor="middle">{ano}</text>'
        )

    for dia, rotulo in prazos:
        if not inicio <= dia <= fim:
            continue
        xp = x(dia.toordinal())
        partes.append(
            f'<line class="prazo" x1="{xp:.1f}" x2="{xp:.1f}" y1="{MARGEM_TOPO}" y2="{altura - MARGEM_BASE}">'
            f"<title>{escape(rotulo)}: {escape(data_br(dia))}</title></line>"
        )

    if pontos:
        caminho = []
        for atual, proximo in zip(pontos, pontos[1:] + [None]):
            ate = proximo.data if proximo else fim
            caminho.append(f"{'M' if not caminho else 'L'}{x(atual.data.toordinal()):.1f},{y(atual.valor):.1f}")
            caminho.append(f"L{x(ate.toordinal()):.1f},{y(atual.valor):.1f}")
        partes.append(f'<path class="serie" d="{" ".join(caminho)}"/>')
        for p in pontos:
            classe = "marcador pendente" if p.pendente else "marcador"
            partes.append(
                f'<circle class="{classe}" cx="{x(p.data.toordinal()):.1f}" cy="{y(p.valor):.1f}" r="5">'
                f"<title>{escape(data_br(p.data))}: {escape(p.rotulo)}</title></circle>"
            )

    partes.append("</svg>")
    return "".join(partes)


@dataclass
class Barra:
    ano: int
    autorizado: float
    pago: float
    em_andamento: bool = False
    bloqueado: bool = False


def barras(dados: list[Barra], titulo: str, altura: int = 280) -> str:
    """Barras por ano: autorizado (fundo) e pago (frente)."""
    topo = topo_eixo(max([max(b.autorizado, b.pago) for b in dados] + [0]) * 1.05)
    y = _escala(0, topo, altura - MARGEM_BASE, MARGEM_TOPO)
    largura_util = LARGURA - MARGEM_ESQ - MARGEM_DIR
    passo = largura_util / max(len(dados), 1)
    partes = [
        f'<svg viewBox="0 0 {LARGURA} {altura}" class="grafico" role="img" aria-label="{escape(titulo)}">',
        f"<title>{escape(titulo)}</title>",
    ]
    for i in range(5):
        v = topo * i / 4
        partes.append(
            f'<line class="grade" x1="{MARGEM_ESQ}" x2="{LARGURA - MARGEM_DIR}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
            f'<text class="eixo" x="{MARGEM_ESQ - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{escape(moeda_curta(v))}</text>'
        )
    for n, b in enumerate(dados):
        x0 = MARGEM_ESQ + n * passo + passo * 0.15
        w = passo * 0.7
        rotulo = f"{b.ano}{'*' if b.em_andamento else ''}"
        partes.append(
            f'<text class="eixo" x="{x0 + w / 2:.1f}" y="{altura - MARGEM_BASE + 18}" text-anchor="middle">{rotulo}</text>'
        )
        if b.bloqueado:
            partes.append(
                f'<text class="bloqueado" x="{x0 + w / 2:.1f}" y="{altura - MARGEM_BASE - 8}" '
                f'text-anchor="middle">em conferência</text>'
            )
            continue
        dica = f"{b.ano}: autorizado {moeda_curta(b.autorizado)}, pago {moeda_curta(b.pago)}"
        partes.append(
            f'<g><title>{escape(dica)}</title>'
            f'<rect class="autorizado" x="{x0:.1f}" y="{y(b.autorizado):.1f}" width="{w:.1f}" '
            f'height="{y(0) - y(b.autorizado):.1f}"/>'
            f'<rect class="pago{" andamento" if b.em_andamento else ""}" x="{x0 + w * 0.2:.1f}" y="{y(b.pago):.1f}" '
            f'width="{w * 0.6:.1f}" height="{y(0) - y(b.pago):.1f}"/></g>'
        )
    partes.append("</svg>")
    return "".join(partes)
