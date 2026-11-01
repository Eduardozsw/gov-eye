"""Formatação no padrão brasileiro (datas, moeda, alíquotas)."""

from datetime import date

MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def _milhar(numero: str) -> str:
    """Troca separadores do formato inglês (1,234.56) pelo brasileiro (1.234,56)."""
    return numero.replace(",", "_").replace(".", ",").replace("_", ".")


def data_br(d: date | str | None) -> str:
    if d is None:
        return ""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return d.strftime("%d/%m/%Y")


def data_extenso(d: date | str) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    dia = "1º" if d.day == 1 else str(d.day)
    return f"{dia} de {MESES[d.month - 1]} de {d.year}"


def moeda(valor: float, casas: int = 2) -> str:
    return "R$ " + _milhar(f"{valor:,.{casas}f}")


def aliquota(valor: float) -> str:
    """Alíquota por litro, com 4 casas (os decretos fixam valores como R$ 0,7925)."""
    return moeda(valor, 4)


def moeda_curta(valor: float) -> str:
    for limite, sufixo in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
        if abs(valor) >= limite:
            texto = f"{valor / limite:,.1f}".rstrip("0").rstrip(".")
            return f"R$ {_milhar(texto)} {sufixo}"
    return moeda(valor, 0)


def percentual(fracao: float) -> str:
    return _milhar(f"{fracao * 100:,.1f}") + "%"
