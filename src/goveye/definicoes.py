"""Leitura e validação dos arquivos de definições em data/definicoes/.

Esses arquivos dizem o que o site mostra: temas, ações do orçamento de cada tema,
atos e eventos da linha do tempo. Os coletores nunca escrevem neles.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from .config import DEFINICOES
from .modelo import (
    AcaoExcluida,
    AcaoMapeada,
    Agente,
    Ato,
    Categoria,
    Causa,
    Correcao,
    Evento,
    Indicador,
    Mandato,
    Tema,
)

ARQUIVO_CORRECOES = "correcoes.yaml"
OBJETOS_CORRIGIVEIS = ("ato", "evento", "acao")
DOMINIOS_OFICIAIS = ("https://www.in.gov.br/", "http://pesquisa.in.gov.br/", "https://www.planalto.gov.br/")
TOLERANCIA_VALOR = 1e-6


class ErroDefinicoes(ValueError):
    pass


@dataclass
class Definicoes:
    mandatos: list[Mandato]
    temas: list[Tema]
    atos: dict[str, Ato]
    eventos: list[Evento]
    acoes: list[AcaoMapeada]
    excluidas: list[AcaoExcluida]
    correcoes: list[Correcao] = field(default_factory=list)

    @property
    def indicadores(self) -> dict[str, Indicador]:
        return {i.id: i for t in self.temas for i in t.indicadores}

    def tema(self, tema_id: str) -> Tema:
        return next(t for t in self.temas if t.id == tema_id)

    def eventos_do_indicador(self, indicador_id: str) -> list[Evento]:
        return sorted((e for e in self.eventos if e.indicador_id == indicador_id), key=lambda e: e.data_efeito)

    def mandato_em(self, dia: date) -> Mandato | None:
        return next((m for m in self.mandatos if m.inicio <= dia <= m.fim), None)


def _ler(caminho: Path):
    with caminho.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _ato(d: dict) -> Ato:
    return Ato(
        id=d["id"],
        tipo=d["tipo"],
        numero=str(d["numero"]),
        ementa=d["ementa"].strip(),
        data_assinatura=d["data_assinatura"],
        data_publicacao=d["data_publicacao"],
        signatarios=[Agente(**s) for s in d.get("signatarios", [])],
        url_oficial=d["url_oficial"],
        id_materia_dou=str(d.get("id_materia_dou", "")),
        sha256_xml=d.get("sha256_xml", ""),
        vigencia_fim_prevista=d.get("vigencia_fim_prevista"),
    )


def _evento(d: dict) -> Evento:
    return Evento(
        id=d["id"],
        indicador_id=d["indicador"],
        data_efeito=d["data_efeito"],
        valor_antes=d.get("valor_antes"),
        valor_depois=float(d["valor_depois"]),
        causa=Causa(d["causa"]) if d.get("causa") else None,
        ato_id=d["ato"],
        trecho=d["trecho"].strip(),
        ato_origem_id=d.get("ato_origem"),
        nota=(d.get("nota") or "").strip(),
    )


def carregar(pasta: Path = DEFINICOES) -> Definicoes:
    mandatos = [Mandato(**m) for m in _ler(pasta / "mandatos.yaml")["mandatos"]]

    temas = []
    for t in _ler(pasta / "temas.yaml")["temas"]:
        indicadores = [Indicador(tema_id=t["id"], **i) for i in t.get("indicadores", [])]
        temas.append(Tema(t["id"], t["nome"], Categoria(t["categoria"]), t["descricao"].strip(), indicadores))

    atos: dict[str, Ato] = {}
    for arquivo in sorted((pasta / "atos").glob("*.yaml")):
        ato = _ato(_ler(arquivo))
        if ato.id in atos:
            raise ErroDefinicoes(f"Ato duplicado: {ato.id}")
        atos[ato.id] = ato

    eventos = []
    for arquivo in sorted((pasta / "eventos").glob("*.yaml")):
        eventos.extend(_evento(e) for e in _ler(arquivo)["eventos"])

    mapeamento = _ler(pasta / "acoes.yaml")
    acoes = [
        AcaoMapeada(
            tema_id=a["tema"],
            codigo=str(a["acao"]),
            justificativa=a["justificativa"].strip(),
            subfuncao=str(a["subfuncao"]) if a.get("subfuncao") else None,
            ano_inicio=a.get("ano_inicio"),
            ano_fim=a.get("ano_fim"),
        )
        for a in mapeamento["acoes"]
    ]
    excluidas = [
        AcaoExcluida(tema_id=a["tema"], codigo=str(a["acao"]), motivo=a["motivo"].strip())
        for a in mapeamento.get("excluidas", [])
    ]

    registro = _ler(pasta / ARQUIVO_CORRECOES) if (pasta / ARQUIVO_CORRECOES).exists() else {}
    correcoes = [
        Correcao(objeto=x["objeto"], objeto_id=str(x["id"]), data=x["data"],
                 o_que_mudou=(x.get("o_que_mudou") or "").strip(), motivo=(x.get("motivo") or "").strip())
        for x in registro.get("correcoes") or []
    ]
    definicoes = Definicoes(mandatos, temas, atos, eventos, acoes, excluidas, correcoes)
    validar(definicoes)
    return definicoes


def corrigiveis(c: Definicoes) -> dict[tuple[str, str], Ato | Evento | AcaoMapeada]:
    """Objetos que podem receber correção, pela chave usada em correcoes.yaml."""
    return {
        **{("ato", a.id): a for a in c.atos.values()},
        **{("evento", e.id): e for e in c.eventos},
        **{("acao", f"{a.tema_id}:{a.codigo}"): a for a in c.acoes},
    }


def registrar_correcao(objeto: str, id_: str, o_que_mudou: str, motivo: str, dia: date,
                       pasta: Path = DEFINICOES) -> None:
    """Acrescenta uma correção ao histórico público (comando `goveye corrigir`).

    Registre só o que mudou depois de publicado: ajustes antes da primeira publicação não são correções.
    """
    if objeto not in OBJETOS_CORRIGIVEIS:
        raise ErroDefinicoes(f"Objeto inválido: {objeto}")
    if (objeto, id_) not in corrigiveis(carregar(pasta)):
        raise ErroDefinicoes(f"{objeto} inexistente: {id_}")
    if not o_que_mudou.strip() or not motivo.strip():
        raise ErroDefinicoes("A correção precisa dizer o que mudou e por quê")
    caminho = pasta / ARQUIVO_CORRECOES
    if not caminho.exists():
        caminho.write_text(
            "# Histórico público de correções (princípio P7). Só acrescentar; não apagar nem editar linhas.\n"
            "correcoes:\n",
            encoding="utf-8",
        )
    item = yaml.safe_dump(
        [{"objeto": objeto, "id": id_, "data": dia, "o_que_mudou": o_que_mudou.strip(), "motivo": motivo.strip()}],
        allow_unicode=True, default_flow_style=False, sort_keys=False, width=1000,
    )
    with caminho.open("a", encoding="utf-8") as f:
        f.write("".join("  " + linha for linha in item.splitlines(keepends=True)))


def validar(c: Definicoes) -> None:
    """Regras que impedem publicar algo incoerente. Levanta ErroDefinicoes com todos os problemas."""
    erros: list[str] = []
    indicadores = c.indicadores
    temas = {t.id for t in c.temas}

    for ato in c.atos.values():
        if not ato.url_oficial.startswith(DOMINIOS_OFICIAIS):
            erros.append(f"Ato {ato.id}: link não aponta para domínio oficial ({ato.url_oficial})")
        if ato.data_publicacao < ato.data_assinatura:
            erros.append(f"Ato {ato.id}: publicado antes de assinado")

    ids_eventos = [e.id for e in c.eventos]
    for repetido in {i for i in ids_eventos if ids_eventos.count(i) > 1}:
        erros.append(f"Evento duplicado: {repetido}")

    for e in c.eventos:
        if e.indicador_id not in indicadores:
            erros.append(f"Evento {e.id}: indicador inexistente {e.indicador_id}")
        if e.ato_id not in c.atos:
            erros.append(f"Evento {e.id}: ato inexistente {e.ato_id}")
        if not e.trecho:
            erros.append(f"Evento {e.id}: sem trecho do ato que comprove o valor")
        if e.causa == Causa.EXPIRACAO_PREVISTA:
            origem = c.atos.get(e.ato_origem_id or "")
            if origem is None:
                erros.append(f"Evento {e.id}: expiração sem ato de origem")
            elif origem.vigencia_fim_prevista is None:
                erros.append(f"Evento {e.id}: ato de origem {origem.id} não tem vigência prevista")

    por_indicador = defaultdict(list)
    for e in c.eventos:
        por_indicador[e.indicador_id].append(e)
    for indicador_id, lista in por_indicador.items():
        lista.sort(key=lambda e: e.data_efeito)
        if lista[0].valor_antes is not None or lista[0].causa is not None:
            erros.append(f"{indicador_id}: o primeiro evento deve ser o valor inicial (sem valor_antes e sem causa)")
        for anterior, atual in zip(lista, lista[1:]):
            if atual.causa is None:
                erros.append(f"Evento {atual.id}: só o primeiro evento da série pode não ter causa")
            if atual.valor_antes is None or abs(atual.valor_antes - anterior.valor_depois) > TOLERANCIA_VALOR:
                erros.append(
                    f"Evento {atual.id}: valor_antes ({atual.valor_antes}) não bate com "
                    f"o valor anterior da série ({anterior.valor_depois}, evento {anterior.id})"
                )
            if atual.data_efeito == anterior.data_efeito:
                erros.append(f"Eventos {anterior.id} e {atual.id} têm a mesma data de efeito")

    for a in c.acoes:
        if a.tema_id not in temas:
            erros.append(f"Ação {a.codigo}: tema inexistente {a.tema_id}")
        if not a.justificativa:
            erros.append(f"Ação {a.codigo} ({a.tema_id}): sem justificativa")
    incluidas = {(a.tema_id, a.codigo) for a in c.acoes}
    for x in c.excluidas:
        if (x.tema_id, x.codigo) in incluidas:
            erros.append(f"Ação {x.codigo} ({x.tema_id}): aparece como incluída e excluída")
        if not x.motivo:
            erros.append(f"Ação excluída {x.codigo} ({x.tema_id}): sem motivo")

    objetos = corrigiveis(c)
    for x in c.correcoes:
        if (x.objeto, x.objeto_id) not in objetos:
            erros.append(f"Correção de {x.objeto} inexistente: {x.objeto_id}")
        if not x.o_que_mudou or not x.motivo:
            erros.append(f"Correção de {x.objeto} {x.objeto_id} em {x.data}: falta dizer o que mudou ou por quê")

    if erros:
        raise ErroDefinicoes("\n".join(erros))
