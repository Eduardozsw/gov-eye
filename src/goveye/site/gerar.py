"""Exporta os dados do site para o front-end em Next.js (pasta web/).

O Python continua sendo o lugar das regras: decide o que é publicável, monta as
frases e os gráficos SVG e grava tudo, já formatado, em web/dados/site.json. O
Next.js só desenha a interface a partir desse arquivo.

Dois modos (seção 7):
- "previa": uso interno; mostra também os valores dos anos em que SIOP e Portal divergem.
- "publicacao": recusa enquanto site.yaml tiver campos a preencher, e anos com divergência
  entre SIOP e Portal ficam bloqueados.
"""

import csv
import hashlib
import io
import json
import shutil
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

from .. import orcamento as orc
from ..banco import conectar
from ..config import BANCO, DEFINICOES, WEB
from ..modelo import Causa
from . import formato, svg, textos

MODOS = ("previa", "publicacao")
MARCADOR_A_PREENCHER = "PREENCHER"
LICENCA_DADOS = "CC BY 4.0"
URL_LICENCA = "https://creativecommons.org/licenses/by/4.0/deed.pt-br"

# Frases que o campo de busca da página inicial escreve e apaga, como exemplo.
SUGESTOES_BUSCA = (
    "Quem zerou o imposto da gasolina?",
    "Quanto foi pago no Bolsa Família em 2024?",
    "Orçamento para povos indígenas",
    "Imposto sobre o diesel",
    "Minha Casa Minha Vida por ano",
    "Casa da Mulher Brasileira",
    "Medida Provisória 1.157",
    "Merenda escolar",
    "Orçamento das universidades federais",
    "Farmácia Popular",
)

# Palavras que o leitor usa e que não aparecem no texto oficial.
SINONIMOS_CATEGORIA = {
    "tributo": "imposto impostos tributo tributos aliquota taxa combustivel combustiveis preco",
    "politica": "orcamento gasto gastos verba dinheiro investimento pago programa politica publica",
}


class ErroPublicacao(RuntimeError):
    pass


def _linhas(db: sqlite3.Connection, sql: str, *args) -> list[dict]:
    return [dict(r) for r in db.execute(sql, args)]


def _config_site(pasta: Path) -> dict:
    caminho = pasta / "site.yaml"
    return yaml.safe_load(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}


def _a_preencher(valor) -> bool:
    if isinstance(valor, dict):
        return any(_a_preencher(v) for v in valor.values())
    return isinstance(valor, str) and MARCADOR_A_PREENCHER in valor


class Montagem:
    """Lê o banco uma vez e aplica as regras do modo escolhido."""

    def __init__(self, db: sqlite3.Connection, modo: str, hoje: date):
        if modo not in MODOS:
            raise ValueError(f"Modo inválido: {modo}")
        self.modo = modo
        self.previa = modo == "previa"
        self.hoje = hoje
        self.mandatos = _linhas(db, "SELECT * FROM mandato ORDER BY inicio")
        self.temas = _linhas(db, "SELECT * FROM tema ORDER BY categoria DESC, rowid")
        self.indicadores = _linhas(db, "SELECT * FROM indicador ORDER BY rowid")
        self.ipca_referencia = db.execute("SELECT valor FROM metadado WHERE chave = 'ipca_referencia'").fetchone()[0]

        self.atos = {a["id"]: a for a in _linhas(db, "SELECT * FROM ato")}
        for a in self.atos.values():
            a["signatarios"] = _linhas(db, "SELECT nome, cargo FROM signatario WHERE ato_id = ? ORDER BY ordem", a["id"])

        self.eventos = _linhas(db, "SELECT * FROM evento ORDER BY indicador_id, data_efeito")
        self.acoes = _linhas(db, "SELECT * FROM acao_mapeada ORDER BY tema_id, codigo")
        self.excluidas = _linhas(db, "SELECT * FROM acao_excluida ORDER BY tema_id, codigo")
        self.orcamento = _linhas(db, "SELECT * FROM orcamento ORDER BY tema_id, ano, acao")
        self.divergencias = _linhas(db, "SELECT * FROM divergencia ORDER BY tema_id, ano, chave, estagio")
        self.correcoes = _linhas(db, "SELECT * FROM correcao ORDER BY data DESC, rowid DESC")

    def correcoes_de(self, objeto: str, objeto_id: str) -> list[dict]:
        return [
            {"data": formato.data_br(x["data"]), "o_que_mudou": x["o_que_mudou"], "motivo": x["motivo"]}
            for x in self.correcoes if (x["objeto"], x["objeto_id"]) == (objeto, objeto_id)
        ]

    # ------------------------------------------------------------------ alíquotas

    def mandato_por_id(self, mandato_id: str | None) -> dict | None:
        return next((m for m in self.mandatos if m["id"] == mandato_id), None)

    def serie(self, indicador: dict) -> dict:
        eventos = [e for e in self.eventos if e["indicador_id"] == indicador["id"]]
        for e in eventos:
            ato = self.atos[e["ato_id"]]
            origem = self.atos.get(e["ato_origem_id"] or "")
            e["ato"] = ato
            e["origem"] = origem
            e["mandato"] = self.mandato_por_id(e["mandato_id"])
            e["frase"] = textos.frase_evento(
                e, indicador, ato, self.mandato_por_id(ato["mandato_id"]),
                origem, self.mandato_por_id(origem["mandato_id"]) if origem else None, formato.aliquota,
            )
        inicio = date(min([date.fromisoformat(m["inicio"]).year for m in self.mandatos] or [self.hoje.year]), 1, 1)
        faixas = [
            svg.Faixa(date.fromisoformat(m["inicio"]), date.fromisoformat(m["fim"]),
                      f"{m['nome_curto']} ({m['partido_na_posse']})")
            for m in self.mandatos
        ]
        pontos = [
            svg.Degrau(date.fromisoformat(e["data_efeito"]), e["valor_depois"],
                       f"{formato.aliquota(e['valor_depois'])} ({e['texto_causa'].lower()})")
            for e in eventos
        ]
        atos_da_serie = {e["ato_id"]: e["ato"] for e in eventos}
        prazos = [
            (date.fromisoformat(a["vigencia_fim_prevista"]), f"Prazo previsto no {a['titulo']}")
            for a in atos_da_serie.values() if a["vigencia_fim_prevista"]
        ]
        fim = min(self.hoje, date.fromisoformat(indicador["levantado_ate"])) if indicador["levantado_ate"] else self.hoje
        grafico = (
            svg.degraus(pontos, faixas, inicio, fim, formato.aliquota,
                        f"{indicador['nome']}: valor por litro ao longo do tempo", prazos)
            if eventos else ""
        )
        return {
            "indicador": indicador,
            "eventos": eventos,
            "grafico": grafico,
            "levantado_ate": fim if fim < self.hoje else None,
            # Sem levantamento até hoje, não dá para afirmar qual é o valor atual.
            "valor_atual": eventos[-1]["valor_depois"] if eventos and fim >= self.hoje else None,
        }

    # ------------------------------------------------------------------ orçamento

    def orcamento_do_tema(self, tema: dict) -> dict:
        acoes = [a for a in self.acoes if a["tema_id"] == tema["id"]]
        linhas = [l for l in self.orcamento if l["tema_id"] == tema["id"]]
        anos_divergentes = {d["ano"] for d in self.divergencias if d["tema_id"] == tema["id"]}

        por_ano: dict[int, dict] = defaultdict(lambda: {e: 0.0 for e in orc.ESTAGIOS} | {"fator_ipca": 1.0})
        for l in linhas:
            for e in orc.ESTAGIOS:
                por_ano[l["ano"]][e] += l[e]
            por_ano[l["ano"]]["fator_ipca"] = l["fator_ipca"]

        anos = []
        for ano, v in sorted(por_ano.items()):
            bloqueado = ano in anos_divergentes and not self.previa
            anos.append({
                "ano": ano,
                "em_andamento": ano >= self.hoje.year,
                "divergente": ano in anos_divergentes,
                "bloqueado": bloqueado,
                "nominal": {e: v[e] for e in orc.ESTAGIOS},
                "corrigido": {e: v[e] * v["fator_ipca"] for e in orc.ESTAGIOS},
                "frase": textos.frase_orcamento(
                    textos.nome_no_meio_da_frase(tema["nome"]), ano, v["atualizada"], v["pago"], formato.moeda_curta
                ),
            })

        def grafico(chave: str, rotulo: str) -> str:
            return svg.barras(
                [svg.Barra(a["ano"], a[chave]["atualizada"], a[chave]["pago"], a["em_andamento"], a["bloqueado"])
                 for a in anos],
                f"Orçamento de {tema['nome']} por ano, {rotulo}: autorizado e pago",
            )

        return {
            "acoes": acoes,
            "excluidas": [x for x in self.excluidas if x["tema_id"] == tema["id"]],
            "anos": anos,
            "divergencias": [d for d in self.divergencias if d["tema_id"] == tema["id"]],
            "grafico_nominal": grafico("nominal", "em valores da época") if anos else "",
            "grafico_corrigido": grafico("corrigido", "corrigido pela inflação") if anos else "",
            "mini": svg.mini_barras(
                [svg.Barra(a["ano"], a["corrigido"]["atualizada"], a["corrigido"]["pago"], a["em_andamento"],
                           a["bloqueado"]) for a in anos],
                f"Valor pago por ano em {tema['nome']}, de {anos[0]['ano']} a {anos[-1]['ano']}, "
                "corrigido pela inflação",
            ) if anos else "",
            "detalhe": self._detalhe_por_acao(linhas, acoes),
        }

    @staticmethod
    def _detalhe_por_acao(linhas: list[dict], acoes: list[dict]) -> list[dict]:
        justificativas = {a["codigo"]: a for a in acoes}
        grupos: dict[str, dict] = {}
        for l in linhas:
            g = grupos.setdefault(l["acao"], {"acao": l["acao"], "nome": l["nome_acao"], "anos": {},
                                              "mapeamento": justificativas.get(l["acao"])})
            ano = g["anos"].setdefault(l["ano"], {"atualizada": 0.0, "pago": 0.0})
            ano["atualizada"] += l["atualizada"]
            ano["pago"] += l["pago"]
        return sorted(grupos.values(), key=lambda g: -sum(a["pago"] for a in g["anos"].values()))

    # ------------------------------------------------------------------ atos

    def atos_visiveis(self) -> list[dict]:
        usados = {e["ato_id"] for e in self.eventos} | {e["ato_origem_id"] for e in self.eventos if e["ato_origem_id"]}
        return sorted((self.atos[i] for i in usados), key=lambda a: a["data_assinatura"])


# ---------------------------------------------------------------------- dados abertos

def _csv(linhas: list[dict], colunas: list[str]) -> bytes:
    saida = io.StringIO()
    w = csv.DictWriter(saida, fieldnames=colunas, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(linhas)
    # BOM para o Excel reconhecer UTF-8 ao abrir o arquivo com dois cliques.
    return ("﻿" + saida.getvalue()).encode("utf-8")


def _dados_abertos(m: Montagem, pasta: Path) -> list[dict]:
    pasta.mkdir(parents=True, exist_ok=True)
    eventos = [{k: v for k, v in e.items() if k not in ("ato", "origem", "mandato")} for e in m.eventos]
    atos = [{**a, "signatarios": "; ".join(f"{s['nome']} ({s['cargo']})" for s in a["signatarios"])}
            for a in m.atos_visiveis()]
    orcamento = m.orcamento
    acoes = m.acoes
    no_ar = ({("evento", e["id"]) for e in eventos} | {("ato", a["id"]) for a in atos}
             | {("acao", f"{a['tema_id']}:{a['codigo']}") for a in acoes})
    correcoes = [x for x in m.correcoes if (x["objeto"], x["objeto_id"]) in no_ar]

    arquivos = {
        "eventos.csv": _csv(eventos, ["id", "indicador_id", "data_efeito", "valor_antes", "valor_depois", "causa",
                                      "texto_causa", "ato_id", "ato_origem_id", "mandato_id", "trecho", "nota"]),
        "atos.csv": _csv(atos, ["id", "tipo", "numero", "titulo", "ementa", "data_assinatura", "data_publicacao",
                                "vigencia_fim_prevista", "signatarios", "url_oficial", "id_materia_dou",
                                "sha256_xml", "mandato_id"]),
        "orcamento.csv": _csv(orcamento, ["tema_id", "ano", "acao", "nome_acao", "programa", "nome_programa",
                                          "subfuncao", *orc.ESTAGIOS, "fator_ipca"]),
        "acoes-mapeadas.csv": _csv(acoes, ["tema_id", "codigo", "subfuncao", "ano_inicio", "ano_fim",
                                           "justificativa"]),
        "acoes-excluidas.csv": _csv(m.excluidas, ["tema_id", "codigo", "motivo"]),
        "correcoes.csv": _csv(correcoes, ["data", "objeto", "objeto_id", "o_que_mudou", "motivo"]),
        "mandatos.csv": _csv(m.mandatos, ["id", "presidente", "nome_curto", "partido_na_posse", "inicio", "fim"]),
    }
    arquivos["goveye.json"] = json.dumps(
        {
            "licenca": LICENCA_DADOS,
            "modo": m.modo,
            "ipca_referencia": m.ipca_referencia,
            "mandatos": m.mandatos,
            "temas": m.temas,
            "indicadores": m.indicadores,
            "atos": m.atos_visiveis(),
            "eventos": eventos,
            "acoes_mapeadas": acoes,
            "acoes_excluidas": m.excluidas,
            "orcamento": orcamento,
            "correcoes": correcoes,
        },
        ensure_ascii=False,
        indent=1,
    ).encode("utf-8")

    for nome, conteudo in arquivos.items():
        (pasta / nome).write_bytes(conteudo)
    manifesto = [{"nome": n, "sha256": hashlib.sha256(c).hexdigest(), "bytes": len(c)} for n, c in arquivos.items()]
    (pasta / "SHA256SUMS.txt").write_text(
        "".join(f"{a['sha256']}  {a['nome']}\n" for a in manifesto), encoding="utf-8"
    )
    return manifesto




# ---------------------------------------------------------------------- exportação

def _ref_ato(ato: dict | None) -> dict | None:
    return {"id": ato["id"], "titulo": ato["titulo"]} if ato else None


def _mes_referencia(aaaamm: str) -> str:
    return f"{aaaamm[4:]}/{aaaamm[:4]}"


def _serie_web(m: Montagem, indicador: dict) -> dict:
    s = m.serie(indicador)
    return {
        "id": indicador["id"],
        "nome": indicador["nome"],
        "descricao": indicador["descricao"],
        "unidade": indicador["unidade"],
        "grafico": s["grafico"],
        "levantado_ate": formato.data_br(s["levantado_ate"]) if s["levantado_ate"] else None,
        "valor_atual": formato.aliquota(s["valor_atual"]) if s["valor_atual"] is not None else None,
        "eventos": [
            {
                "id": e["id"],
                "data_iso": e["data_efeito"],
                "data": formato.data_br(e["data_efeito"]),
                "governo": e["mandato"]["nome_curto"] if e["mandato"] else None,
                "causa": e["texto_causa"],
                "expiracao": e["causa"] == Causa.EXPIRACAO_PREVISTA.name,
                "frase": e["frase"],
                "valor": formato.aliquota(e["valor_depois"]),
                "valor_antes": formato.aliquota(e["valor_antes"]) if e["valor_antes"] is not None else None,
                "trecho": e["trecho"],
                "nota": e["nota"] or None,
                "ato": _ref_ato(e["ato"]),
                "origem": _ref_ato(e["origem"]),
                "correcoes": m.correcoes_de("evento", e["id"]),
            }
            for e in reversed(s["eventos"])
        ],
    }


def _orcamento_web(m: Montagem, tema: dict) -> dict:
    o = m.orcamento_do_tema(tema)
    anos = o["anos"]
    tem_dados = bool(anos)
    fechados = [a for a in anos if not a["em_andamento"] and not a["bloqueado"]]

    def valor(a: dict, estagio: str) -> str:
        return "—" if a["bloqueado"] else formato.moeda_curta(a["nominal"][estagio])

    def pago_da_acao(g: dict, a: dict) -> str:
        if a["bloqueado"]:
            return "—"
        return formato.moeda_curta(g["anos"][a["ano"]]["pago"]) if a["ano"] in g["anos"] else ""

    return {
        "tem_dados": tem_dados,
        "destaque": (
            {"ano": fechados[-1]["ano"], "pago": formato.moeda_curta(fechados[-1]["nominal"]["pago"])}
            if fechados else None
        ),
        "ipca_referencia": _mes_referencia(m.ipca_referencia),
        "grafico_nominal": o["grafico_nominal"],
        "grafico_corrigido": o["grafico_corrigido"],
        "mini": o["mini"],
        "anos_mini": f"{anos[0]['ano']}–{anos[-1]['ano']}" if anos else None,
        "frases": [
            {
                "ano": a["ano"],
                "texto": (
                    f"{a['ano']}: valores em conferência (as fontes oficiais divergem)."
                    if a["bloqueado"]
                    else a["frase"] + (" Ano em andamento." if a["em_andamento"] else "")
                ),
                "divergente": a["divergente"] and not a["bloqueado"],
            }
            for a in reversed(anos)
        ],
        "estagios": [orc.NOMES_ESTAGIOS[e] for e in orc.ESTAGIOS],
        "tabela": [
            {"ano": f"{a['ano']}{'*' if a['em_andamento'] else ''}", "valores": [valor(a, e) for e in orc.ESTAGIOS]}
            for a in anos
        ],
        "acoes": [
            {"codigo": a["codigo"], "subfuncao": a["subfuncao"], "justificativa": a["justificativa"]}
            for a in o["acoes"]
        ],
        "excluidas": [{"codigo": x["codigo"], "motivo": x["motivo"]} for x in o["excluidas"]],
        "detalhe": {
            "anos": [a["ano"] for a in anos],
            "linhas": [
                {"acao": g["acao"], "nome": g["nome"], "valores": [pago_da_acao(g, a) for a in anos]}
                for g in o["detalhe"]
            ],
        } if tem_dados else None,
        "divergencias": [
            {"ano": d["ano"], "chave": d["chave"], "estagio": d["estagio"],
             "siop": formato.moeda(d["siop"]), "portal": formato.moeda(d["portal"])}
            for d in o["divergencias"]
        ] if m.previa else [],
    }


def _atos_web(m: Montagem) -> list[dict]:
    indicadores = {i["id"]: i for i in m.indicadores}
    saida = []
    for ato in m.atos_visiveis():
        mandato = m.mandato_por_id(ato["mandato_id"])
        eventos = [e for e in m.eventos if ato["id"] in (e["ato_id"], e["ato_origem_id"])]
        saida.append({
            "id": ato["id"],
            "titulo": ato["titulo"],
            "tipo": ato["tipo"],
            "ementa": ato["ementa"],
            "assinatura": formato.data_extenso(ato["data_assinatura"]),
            "publicacao": formato.data_extenso(ato["data_publicacao"]),
            "governo": f"{mandato['presidente']} ({mandato['partido_na_posse']} na posse)" if mandato else None,
            "signatarios": [f"{s['nome']}, {s['cargo']}" for s in ato["signatarios"]],
            "vigencia_fim": (
                formato.data_extenso(ato["vigencia_fim_prevista"]) if ato["vigencia_fim_prevista"] else None
            ),
            "url_oficial": ato["url_oficial"],
            "sha256": ato["sha256_xml"] or None,
            "correcoes": m.correcoes_de("ato", ato["id"]),
            "eventos": [
                {
                    "id": e["id"],
                    "frase": e["frase"],
                    "indicador": indicadores[e["indicador_id"]]["nome"],
                    "tema_id": indicadores[e["indicador_id"]]["tema_id"],
                }
                for e in eventos
            ],
        })
    return saida


def _prazos_web(m: Montagem) -> list[dict]:
    """Atos com data para acabar: os que ainda vão vencer primeiro, depois os já vencidos.

    Para cada série afetada, mostra o que veio em seguida. Assim o leitor vê, antes da
    data, que a regra já nasceu com prazo, e depois dela, o que de fato aconteceu.
    """
    indicadores = {i["id"]: i for i in m.indicadores}
    futuros, vencidos = [], []
    for ato in m.atos_visiveis():
        if not ato["vigencia_fim_prevista"]:
            continue
        fim = date.fromisoformat(ato["vigencia_fim_prevista"])
        # O último evento do ato em cada série é o valor que valia até o prazo.
        do_ato = {e["indicador_id"]: e for e in m.eventos
                  if e["ato_id"] == ato["id"] and e["causa"] != Causa.EXPIRACAO_PREVISTA.name}
        itens = []
        for indicador_id, e in do_ato.items():
            ind = indicadores[indicador_id]
            depois = next((x for x in m.eventos
                           if x["indicador_id"] == indicador_id and x["data_efeito"] > e["data_efeito"]), None)
            levantado = date.fromisoformat(ind["levantado_ate"]) if ind["levantado_ate"] else None
            itens.append({
                "indicador": ind["nome"],
                "tema_id": ind["tema_id"],
                "evento_id": e["id"],
                "frase": textos.frase_prazo(ind["nome"], formato.aliquota(e["valor_depois"]), ato["vigencia_fim_prevista"],
                                            ato),
                "depois": (
                    {"id": depois["id"], "data": formato.data_br(depois["data_efeito"]), "frase": depois["frase"]}
                    if depois else None
                ),
                # Sem evento seguinte numa série que não chega até hoje, não dá para dizer o que houve.
                "levantado_ate": (
                    formato.data_br(levantado) if not depois and levantado and levantado < m.hoje else None
                ),
            })
        if not itens:
            continue
        prazo = {
            "ato": _ref_ato(ato),
            "data": formato.data_extenso(fim),
            "data_iso": fim.isoformat(),
            "futuro": fim >= m.hoje,
            "itens": itens,
        }
        (futuros if prazo["futuro"] else vencidos).append(prazo)
    return sorted(futuros, key=lambda p: p["data_iso"]) + sorted(vencidos, key=lambda p: p["data_iso"], reverse=True)


def _correcoes_web(m: Montagem, temas: list[dict], atos: list[dict]) -> list[dict]:
    """Histórico geral de correções, só dos itens que estão no ar (com link para cada um)."""
    destinos = {("ato", a["id"]): (a["titulo"], f"/ato/{a['id']}/") for a in atos}
    for t in temas:
        for s in t.get("series", []):
            for e in s["eventos"]:
                destinos[("evento", e["id"])] = (f"{s['nome']}, {e['data']}", f"/mudanca/{e['id']}/")
        o = t.get("orcamento")
        if o:
            for a in o["acoes"]:
                destinos[("acao", f"{t['id']}:{a['codigo']}")] = (f"Ação {a['codigo']} em {t['nome']}",
                                                                  f"/tema/{t['id']}/#acoes")
    saida = []
    for x in m.correcoes:
        destino = destinos.get((x["objeto"], x["objeto_id"]))
        if destino:
            saida.append({"data": formato.data_br(x["data"]), "titulo": destino[0], "href": destino[1],
                          "o_que_mudou": x["o_que_mudou"], "motivo": x["motivo"]})
    return saida


def _glossario(definicoes: Path) -> list[dict]:
    caminho = definicoes / "glossario.yaml"
    termos = (yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}).get("termos", []) if caminho.exists() else []
    ids = [t.get("id") for t in termos]
    problemas = [f"termo repetido: {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    problemas += [f"termo incompleto: {t}" for t in termos if not (t.get("id") and t.get("termo") and t.get("definicao"))]
    if problemas:
        raise ErroPublicacao(f"Glossário ({caminho}): " + "; ".join(problemas))
    return [{"id": t["id"], "termo": t["termo"], "definicao": " ".join(t["definicao"].split())} for t in termos]


def _busca(temas: list[dict], atos: list[dict]) -> list[dict]:
    """Índice da caixa de busca: cada item traz o texto onde procurar e o link de destino."""
    itens = []

    def item(tipo: str, titulo: str, resumo: str, href: str, *texto: str) -> None:
        itens.append({"tipo": tipo, "titulo": titulo, "resumo": resumo, "href": href,
                      "texto": " ".join(x for x in (titulo, resumo, *texto) if x)})

    for t in temas:
        extra = SINONIMOS_CATEGORIA[t["categoria"]]
        base = f"/tema/{t['id']}/"
        item("Tema", t["nome"], t["descricao"], base, extra)
        for s in t.get("series", []):
            item("Imposto", s["nome"], s["descricao"], f"{base}#{s['id']}", t["nome"], extra)
            for e in s["eventos"]:
                item("Mudança", f"{s['nome']}, {e['data']}", e["frase"], f"/mudanca/{e['id']}/",
                     e["causa"], e["governo"] or "", extra)
        o = t.get("orcamento")
        if o:
            for f in o["frases"]:
                item("Orçamento", f"{t['nome']} em {f['ano']}", f["texto"], base, extra)
            for a in o["acoes"]:
                item("Ação do orçamento", f"{a['codigo']} · {t['nome']}", a["justificativa"], f"{base}#acoes", extra)
    for a in atos:
        item("Ato oficial", a["titulo"], a["ementa"], f"/ato/{a['id']}/", a["governo"] or "")
    return itens


def exportar(modo: str, banco: Path = BANCO, saida: Path = WEB, definicoes: Path = DEFINICOES,
             hoje: date | None = None) -> Path:
    """Grava saida/dados/site.json e os dados abertos em saida/public/dados/."""
    config = _config_site(definicoes)
    if modo == "publicacao" and _a_preencher(config):
        raise ErroPublicacao(f"Preencha os campos marcados com {MARCADOR_A_PREENCHER} em {definicoes / 'site.yaml'}")

    db = conectar(banco)
    m = Montagem(db, modo, hoje or date.today())
    db.close()

    pasta_abertos = saida / "public" / "dados"
    if pasta_abertos.exists():
        shutil.rmtree(pasta_abertos)
    manifesto = _dados_abertos(m, pasta_abertos)

    temas = []
    for tema in m.temas:
        t = {"id": tema["id"], "nome": tema["nome"], "categoria": tema["categoria"],
             "descricao": " ".join(tema["descricao"].split())}
        if tema["categoria"] == "tributo":
            t["series"] = [_serie_web(m, i) for i in m.indicadores if i["tema_id"] == tema["id"]]
        else:
            t["orcamento"] = _orcamento_web(m, tema)
        temas.append(t)
    atos = _atos_web(m)

    dados = {
        "modo": modo,
        "previa": m.previa,
        "gerado_em": formato.data_br(m.hoje),
        "licenca": LICENCA_DADOS,
        "url_licenca": URL_LICENCA,
        "config": {"responsavel": config.get("responsavel", {}), "endereco_site": config.get("endereco_site")},
        "mandatos": [
            {"id": x["id"], "presidente": x["presidente"], "nome_curto": x["nome_curto"],
             "partido": x["partido_na_posse"], "inicio": formato.data_br(x["inicio"]),
             "fim": formato.data_br(x["fim"])}
            for x in m.mandatos
        ],
        "temas": temas,
        "atos": atos,
        "prazos": _prazos_web(m),
        "correcoes": _correcoes_web(m, temas, atos),
        "glossario": _glossario(definicoes),
        "metodologia": {
            "tolerancia": formato.moeda(orc.TOLERANCIA_CONFERENCIA),
            "ipca_referencia": _mes_referencia(m.ipca_referencia),
            "estagios": [orc.NOMES_ESTAGIOS[e] for e in orc.ESTAGIOS],
            "excluidas": [{"tema": x["tema_id"], "codigo": x["codigo"], "motivo": x["motivo"]} for x in m.excluidas],
        },
        "manifesto": [{"nome": a["nome"], "kb": round(a["bytes"] / 1024, 1), "sha256": a["sha256"]} for a in manifesto],
        "busca": _busca(temas, atos),
        "sugestoes": list(SUGESTOES_BUSCA),
    }
    destino = saida / "dados" / "site.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino
