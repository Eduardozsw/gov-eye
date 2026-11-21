"""Frases geradas por modelo fixo (seção 9 da especificação).

Os textos do site saem sempre destes modelos, preenchidos com dados do banco.
Ninguém escreve à mão a frase que explica uma mudança: assim o mesmo fato é
contado do mesmo jeito, qualquer que seja o governo.
"""

from .formato import data_extenso


def lista_nomes(nomes: list[str]) -> str:
    if not nomes:
        return ""
    if len(nomes) == 1:
        return nomes[0]
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


def nome_no_meio_da_frase(nome: str) -> str:
    """"Educação básica" vira "educação básica"; nomes próprios ("Bolsa Família", "FIES") ficam como estão."""
    if any(c.isupper() for c in nome[1:]):
        return nome
    return nome[:1].lower() + nome[1:]


def _movimento(antes: float, depois: float, fmt) -> str:
    if depois == antes:
        return f"continuou em {fmt(depois)}"
    if depois == 0:
        return f"foi zerado (era {fmt(antes)})"
    if antes == 0:
        return f"voltou a ser cobrado, em {fmt(depois)}"
    verbo = "subiu" if depois > antes else "caiu"
    return f"{verbo} de {fmt(antes)} para {fmt(depois)}"


TIPOS_FEMININOS = ("Lei", "Lei Complementar", "Medida Provisória", "Emenda Constitucional", "Portaria")


def com_artigo(preposicao: str, ato: dict) -> str:
    """'pelo Decreto nº ...', 'pela Lei nº ...', 'no Decreto', 'na Medida Provisória'."""
    feminino = ato["tipo"] in TIPOS_FEMININOS
    forma = {"por": ("pelo", "pela"), "em": ("no", "na")}[preposicao][feminino]
    return f"{forma} {ato['titulo']}"


def _assinatura(ato: dict, mandato: dict | None, preposicao: str) -> str:
    if ato["tipo"].startswith("Lei"):
        verbo = "sancionada"
    else:
        verbo = "assinada" if ato["tipo"] in TIPOS_FEMININOS else "assinado"
    texto = f"{com_artigo(preposicao, ato)}, {verbo} em {data_extenso(ato['data_assinatura'])}"
    if ato["signatarios"]:
        texto += " por " + lista_nomes([s["nome"] for s in ato["signatarios"]])
    if mandato:
        texto += f" (governo {mandato['nome_curto']})"
    return texto


def _assinatura_solta(ato: dict, mandato: dict | None) -> str:
    """Mesma informação sem preposição, para depois de dois-pontos ('Decreto nº ..., assinado em ...')."""
    texto = _assinatura(ato, mandato, "por")
    return texto.split(" ", 1)[1]


def frase_evento(evento: dict, indicador: dict, ato: dict, mandato_ato: dict | None,
                 origem: dict | None, mandato_origem: dict | None, fmt) -> str:
    quando = f"Em {data_extenso(evento['data_efeito'])}"
    if evento["causa"] is None:
        return f"{quando}, o valor em vigor era {fmt(evento['valor_depois'])}, fixado {_assinatura(ato, mandato_ato, "por")}."

    # "o valor de" evita escolher artigo por indicador ("o PIS/Cofins", "a CIDE").
    mudanca = f"{quando}, o valor de {indicador['nome']} " +_movimento(evento["valor_antes"], evento["valor_depois"], fmt)
    if evento["causa"] == "EXPIRACAO_PREVISTA" and origem:
        return (
            f"{mudanca} porque terminou o prazo já fixado {_assinatura(origem, mandato_origem, "em")}. "
            "Nenhum ato novo foi assinado para esta mudança."
        )
    return f"{mudanca}. {evento['texto_causa']}: {_assinatura_solta(ato, mandato_ato)}."


def frase_prazo(indicador: str, valor: str, fim: str, ato: dict) -> str:
    """Prazo escrito no próprio ato: vale igual para prazos já vencidos e futuros."""
    return f"O valor de {indicador} foi fixado em {valor} até {data_extenso(fim)} {com_artigo('por', ato)}."


def frase_orcamento(tema: str, ano: int, autorizado: float, pago: float, fmt_moeda) -> str:
    if autorizado <= 0:
        return f"Em {ano}, não houve valor autorizado para {tema} nas ações acompanhadas."
    proporcao = pago / autorizado
    return (
        f"Em {ano}, o orçamento autorizou {fmt_moeda(autorizado)} para {tema} e foram pagos "
        f"{fmt_moeda(pago)} ({round(proporcao * 100)}% do autorizado)."
    )
