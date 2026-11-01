"""Gera o site estático a partir do banco SQLite.

Dois modos (seção 7):
- "previa": mostra tudo, com selo nos itens ainda não revisados. Uso interno do curador.
- "publicacao": só itens publicáveis. Séries de alíquotas param no primeiro evento não
  publicável; o orçamento de um tema só aparece quando todo o mapeamento dele foi revisado,
  e anos com divergência entre SIOP e Portal ficam bloqueados.
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
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .. import orcamento as orc
from ..banco import conectar
from ..config import BANCO, CURADORIA, SITE_SAIDA
from ..modelo import StatusRevisao, publicavel
from . import formato, svg, textos

AQUI = Path(__file__).parent
MODOS = ("previa", "publicacao")
MARCADOR_A_PREENCHER = "PREENCHER"
LICENCA_DADOS = "CC BY-NC 4.0"
URL_LICENCA = "https://creativecommons.org/licenses/by-nc/4.0/deed.pt-br"


class ErroPublicacao(RuntimeError):
    pass


def _publicavel(status: str) -> bool:
    return publicavel(StatusRevisao(status))


def _linhas(db: sqlite3.Connection, sql: str, *args) -> list[dict]:
    return [dict(r) for r in db.execute(sql, args)]


def _ambiente() -> Environment:
    env = Environment(
        loader=FileSystemLoader(AQUI / "modelos"),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(
        data=formato.data_br,
        data_extenso=formato.data_extenso,
        moeda=formato.moeda,
        moeda_curta=formato.moeda_curta,
        aliquota=formato.aliquota,
        percentual=formato.percentual,
    )
    return env


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
            a["pendente"] = not _publicavel(a["status_revisao"])

        self.eventos = self._eventos_visiveis(_linhas(db, "SELECT * FROM evento ORDER BY indicador_id, data_efeito"))
        self.acoes = _linhas(db, "SELECT * FROM acao_mapeada ORDER BY tema_id, codigo")
        for a in self.acoes:
            a["pendente"] = not _publicavel(a["status_revisao"])
        self.excluidas = _linhas(db, "SELECT * FROM acao_excluida ORDER BY tema_id, codigo")
        self.orcamento = _linhas(db, "SELECT * FROM orcamento ORDER BY tema_id, ano, acao")
        self.divergencias = _linhas(db, "SELECT * FROM divergencia ORDER BY tema_id, ano, chave, estagio")

    # ------------------------------------------------------------------ alíquotas

    def _eventos_visiveis(self, eventos: list[dict]) -> list[dict]:
        visiveis = []
        interrompido = set()
        for e in eventos:
            ato = self.atos[e["ato_id"]]
            e["pendente"] = not _publicavel(e["status_revisao"]) or ato["pendente"]
            if self.previa:
                visiveis.append(e)
            elif e["indicador_id"] not in interrompido:
                # Na publicação a série para no primeiro item não revisado: mostrar eventos
                # posteriores pularia uma mudança e quebraria a continuidade.
                if e["pendente"]:
                    interrompido.add(e["indicador_id"])
                else:
                    visiveis.append(e)
        self.series_interrompidas = interrompido
        return visiveis

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
                       f"{formato.aliquota(e['valor_depois'])} ({e['texto_causa'].lower()})", e["pendente"])
            for e in eventos
        ]
        atos_da_serie = {e["ato_id"]: e["ato"] for e in eventos}
        prazos = [
            (date.fromisoformat(a["vigencia_fim_prevista"]), f"Prazo previsto no {a['titulo']}")
            for a in atos_da_serie.values() if a["vigencia_fim_prevista"]
        ]
        grafico = (
            svg.degraus(pontos, faixas, inicio, self.hoje, formato.aliquota,
                        f"{indicador['nome']}: valor por litro ao longo do tempo", prazos)
            if eventos else ""
        )
        return {
            "indicador": indicador,
            "eventos": eventos,
            "grafico": grafico,
            "interrompida": indicador["id"] in self.series_interrompidas,
            "valor_atual": eventos[-1]["valor_depois"] if eventos else None,
        }

    # ------------------------------------------------------------------ orçamento

    def orcamento_do_tema(self, tema: dict) -> dict:
        acoes = [a for a in self.acoes if a["tema_id"] == tema["id"]]
        liberado = self.previa or (acoes and not any(a["pendente"] for a in acoes))
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
                    tema["nome"].lower(), ano, v["atualizada"], v["pago"], formato.moeda_curta
                ),
            })

        def grafico(chave: str, rotulo: str) -> str:
            return svg.barras(
                [svg.Barra(a["ano"], a[chave]["atualizada"], a[chave]["pago"], a["em_andamento"], a["bloqueado"])
                 for a in anos],
                f"Orçamento de {tema['nome']} por ano, {rotulo}: autorizado e pago",
            )

        return {
            "liberado": liberado,
            "acoes": acoes,
            "excluidas": [x for x in self.excluidas if x["tema_id"] == tema["id"]],
            "anos": anos,
            "divergencias": [d for d in self.divergencias if d["tema_id"] == tema["id"]],
            "grafico_nominal": grafico("nominal", "em valores da época") if anos and liberado else "",
            "grafico_corrigido": grafico("corrigido", "corrigido pela inflação") if anos and liberado else "",
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
    temas_liberados = {t["id"] for t in m.temas if m.orcamento_do_tema(t)["liberado"]}
    orcamento = [l for l in m.orcamento if l["tema_id"] in temas_liberados]
    acoes = [a for a in m.acoes if m.previa or a["tema_id"] in temas_liberados]

    arquivos = {
        "eventos.csv": _csv(eventos, ["id", "indicador_id", "data_efeito", "valor_antes", "valor_depois", "causa",
                                      "texto_causa", "ato_id", "ato_origem_id", "mandato_id", "trecho", "nota",
                                      "status_revisao"]),
        "atos.csv": _csv(atos, ["id", "tipo", "numero", "titulo", "ementa", "data_assinatura", "data_publicacao",
                                "vigencia_fim_prevista", "signatarios", "url_oficial", "id_materia_dou",
                                "sha256_xml", "mandato_id", "status_revisao"]),
        "orcamento.csv": _csv(orcamento, ["tema_id", "ano", "acao", "nome_acao", "programa", "nome_programa",
                                          "subfuncao", *orc.ESTAGIOS, "fator_ipca"]),
        "acoes-mapeadas.csv": _csv(acoes, ["tema_id", "codigo", "subfuncao", "ano_inicio", "ano_fim",
                                           "justificativa", "status_revisao"]),
        "acoes-excluidas.csv": _csv(m.excluidas, ["tema_id", "codigo", "motivo"]),
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


# ---------------------------------------------------------------------- geração

def gerar(modo: str, banco: Path = BANCO, saida: Path = SITE_SAIDA, curadoria: Path = CURADORIA,
          hoje: date | None = None) -> Path:
    config = _config_site(curadoria)
    if modo == "publicacao" and _a_preencher(config):
        raise ErroPublicacao(f"Preencha os campos marcados com {MARCADOR_A_PREENCHER} em {curadoria / 'site.yaml'}")

    db = conectar(banco)
    m = Montagem(db, modo, hoje or date.today())
    db.close()

    if saida.exists():
        shutil.rmtree(saida)
    (saida / "tema").mkdir(parents=True)
    (saida / "ato").mkdir()
    shutil.copy(AQUI / "estatico" / "estilo.css", saida / "estilo.css")

    env = _ambiente()
    comum = {
        "modo": modo,
        "previa": m.previa,
        "config": config,
        "temas": m.temas,
        "gerado_em": m.hoje,
        "licenca": LICENCA_DADOS,
        "url_licenca": URL_LICENCA,
    }

    def escrever(caminho: str, modelo: str, **contexto) -> None:
        raiz = "../" * caminho.count("/")
        html = env.get_template(modelo).render(**comum, raiz=raiz, **contexto)
        (saida / caminho).write_text(html, encoding="utf-8")

    resumo_temas = []
    for tema in m.temas:
        if tema["categoria"] == "tributo":
            series = [m.serie(i) for i in m.indicadores if i["tema_id"] == tema["id"]]
            escrever(f"tema/{tema['id']}.html", "tema_tributo.html", tema=tema, series=series)
            resumo_temas.append({"tema": tema, "series": series})
        else:
            dados = m.orcamento_do_tema(tema)
            escrever(f"tema/{tema['id']}.html", "tema_politica.html", tema=tema, orcamento=dados,
                     ipca_referencia=m.ipca_referencia, nomes_estagios=orc.NOMES_ESTAGIOS,
                     estagios=orc.ESTAGIOS)
            resumo_temas.append({"tema": tema, "orcamento": dados})

    for ato in m.atos_visiveis():
        eventos = [e for e in m.eventos if ato["id"] in (e["ato_id"], e["ato_origem_id"])]
        escrever(f"ato/{ato['id']}.html", "ato.html", ato=ato, eventos=eventos,
                 mandato=m.mandato_por_id(ato["mandato_id"]), indicadores={i["id"]: i for i in m.indicadores})

    manifesto = _dados_abertos(m, saida / "dados")
    escrever("index.html", "inicio.html", resumo=resumo_temas, mandatos=m.mandatos)
    escrever("metodologia.html", "metodologia.html", excluidas=m.excluidas, acoes=m.acoes,
             ipca_referencia=m.ipca_referencia, nomes_estagios=orc.NOMES_ESTAGIOS,
             tolerancia=orc.TOLERANCIA_CONFERENCIA)
    escrever("quem-faz.html", "quem_faz.html")
    escrever("dados.html", "dados.html", manifesto=manifesto)
    escrever("404.html", "404.html")
    return saida
