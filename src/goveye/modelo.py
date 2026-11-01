"""Modelo de dados do gov-eye (seção 5 da especificação)."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class Categoria(StrEnum):
    TRIBUTO = "tributo"
    POLITICA = "politica"


class Causa(StrEnum):
    """Por que um valor mudou (tabela 5.3 da especificação)."""

    ATO_NOVO = "ATO_NOVO"
    EXPIRACAO_PREVISTA = "EXPIRACAO_PREVISTA"
    PRORROGACAO = "PRORROGACAO"
    REVOGACAO = "REVOGACAO"
    DECISAO_JUDICIAL = "DECISAO_JUDICIAL"
    LEI_CONGRESSO = "LEI_CONGRESSO"
    REAJUSTE_AUTOMATICO = "REAJUSTE_AUTOMATICO"


TEXTO_CAUSA = {
    Causa.ATO_NOVO: "Alterado por novo ato",
    Causa.EXPIRACAO_PREVISTA: "Prazo previsto no ato original terminou",
    Causa.PRORROGACAO: "Prazo estendido",
    Causa.REVOGACAO: "Ato anterior revogado",
    Causa.DECISAO_JUDICIAL: "Determinado pela Justiça",
    Causa.LEI_CONGRESSO: "Lei aprovada pelo Congresso",
    Causa.REAJUSTE_AUTOMATICO: "Regra de reajuste já existente",
}


class StatusRevisao(StrEnum):
    PENDENTE = "pendente"
    PRIMEIRA_PASSAGEM = "primeira passagem"
    REVISAO_INDIVIDUAL = "revisão individual"
    REVISADO = "revisado"


@dataclass(frozen=True)
class Revisao:
    revisor: str
    data: date


def status_revisao(revisoes: list[Revisao]) -> StatusRevisao:
    """Aplica o protocolo da seção 7: duas passagens em dias diferentes, ou dois revisores."""
    if not revisoes:
        return StatusRevisao.PENDENTE
    if len({r.revisor for r in revisoes}) >= 2:
        return StatusRevisao.REVISADO
    if len({r.data for r in revisoes}) >= 2:
        return StatusRevisao.REVISAO_INDIVIDUAL
    return StatusRevisao.PRIMEIRA_PASSAGEM


def publicavel(status: StatusRevisao) -> bool:
    return status in (StatusRevisao.REVISAO_INDIVIDUAL, StatusRevisao.REVISADO)


@dataclass
class Mandato:
    id: str
    presidente: str
    partido_na_posse: str
    inicio: date
    fim: date


@dataclass
class Indicador:
    id: str
    tema_id: str
    nome: str
    unidade: str
    tipo: str  # "aliquota" ou "orcamento"
    descricao: str = ""


@dataclass
class Tema:
    id: str
    nome: str
    categoria: Categoria
    descricao: str
    indicadores: list[Indicador] = field(default_factory=list)


@dataclass
class Agente:
    nome: str
    cargo: str


@dataclass
class Ato:
    id: str
    tipo: str
    numero: str
    ementa: str
    data_assinatura: date
    data_publicacao: date
    signatarios: list[Agente]
    url_oficial: str
    id_materia_dou: str = ""
    sha256_xml: str = ""
    vigencia_fim_prevista: date | None = None
    revisoes: list[Revisao] = field(default_factory=list)

    @property
    def titulo(self) -> str:
        return f"{self.tipo} nº {self.numero}"


@dataclass
class Evento:
    """Mudança de valor de um indicador tributário."""

    id: str
    indicador_id: str
    data_efeito: date
    valor_antes: float | None  # None no valor inicial da série
    valor_depois: float
    causa: Causa | None  # None no valor inicial da série
    ato_id: str
    trecho: str  # citação literal do ato que comprova o valor
    ato_origem_id: str | None = None  # em expirações, o ato que fixou o prazo
    nota: str = ""
    revisoes: list[Revisao] = field(default_factory=list)


@dataclass
class AcaoMapeada:
    """Ligação entre uma ação orçamentária e um tema (seção 5.4)."""

    tema_id: str
    codigo: str
    justificativa: str
    # Restringe a ação a uma subfunção, para ações genéricas usadas por vários públicos
    # (ex.: 21C0, enfrentamento da covid, só na subfunção 423, assistência aos povos indígenas).
    subfuncao: str | None = None
    ano_inicio: int | None = None
    ano_fim: int | None = None
    revisoes: list[Revisao] = field(default_factory=list)

    def vale_em(self, ano: int, subfuncao: str) -> bool:
        return (
            (self.ano_inicio is None or ano >= self.ano_inicio)
            and (self.ano_fim is None or ano <= self.ano_fim)
            and (self.subfuncao is None or subfuncao == self.subfuncao)
        )


@dataclass
class AcaoExcluida:
    """Ação candidata que o curador decidiu não incluir, com o motivo (publicado na metodologia)."""

    tema_id: str
    codigo: str
    motivo: str
