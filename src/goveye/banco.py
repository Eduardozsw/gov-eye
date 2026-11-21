"""Banco SQLite do gov-eye, reconstruído do zero a cada carga a partir das definições e das coletas.

O banco é um produto derivado: nada é editado nele à mão. O que o site mostra
vem dos arquivos em data/definicoes/; os números, dos dados brutos em data/raw/.
"""

import sqlite3
from datetime import date
from pathlib import Path

from . import orcamento as orc
from .config import BANCO
from .definicoes import Definicoes
from .modelo import TEXTO_CAUSA

ESQUEMA = """
CREATE TABLE mandato (
    id TEXT PRIMARY KEY, presidente TEXT, nome_curto TEXT, partido_na_posse TEXT, inicio TEXT, fim TEXT
);
CREATE TABLE tema (
    id TEXT PRIMARY KEY, nome TEXT, categoria TEXT, descricao TEXT
);
CREATE TABLE indicador (
    id TEXT PRIMARY KEY, tema_id TEXT REFERENCES tema(id), nome TEXT, unidade TEXT, tipo TEXT, descricao TEXT,
    levantado_ate TEXT
);
CREATE TABLE ato (
    id TEXT PRIMARY KEY, tipo TEXT, numero TEXT, titulo TEXT, ementa TEXT,
    data_assinatura TEXT, data_publicacao TEXT, vigencia_fim_prevista TEXT,
    url_oficial TEXT, id_materia_dou TEXT, sha256_xml TEXT,
    mandato_id TEXT REFERENCES mandato(id)
);
CREATE TABLE signatario (
    ato_id TEXT REFERENCES ato(id), ordem INTEGER, nome TEXT, cargo TEXT
);
CREATE TABLE evento (
    id TEXT PRIMARY KEY, indicador_id TEXT REFERENCES indicador(id), data_efeito TEXT,
    valor_antes REAL, valor_depois REAL, causa TEXT, texto_causa TEXT,
    ato_id TEXT REFERENCES ato(id), ato_origem_id TEXT REFERENCES ato(id),
    trecho TEXT, nota TEXT, mandato_id TEXT REFERENCES mandato(id)
);
CREATE TABLE correcao (
    objeto TEXT, objeto_id TEXT, data TEXT, o_que_mudou TEXT, motivo TEXT
);
CREATE TABLE acao_mapeada (
    tema_id TEXT REFERENCES tema(id), codigo TEXT, subfuncao TEXT, ano_inicio INTEGER, ano_fim INTEGER,
    justificativa TEXT
);
CREATE TABLE acao_excluida (
    tema_id TEXT REFERENCES tema(id), codigo TEXT, motivo TEXT
);
CREATE TABLE orcamento (
    tema_id TEXT REFERENCES tema(id), ano INTEGER, acao TEXT, nome_acao TEXT,
    programa TEXT, nome_programa TEXT, subfuncao TEXT,
    projeto_lei REAL, inicial REAL, atualizada REAL, empenhado REAL, liquidado REAL, pago REAL,
    fator_ipca REAL
);
CREATE TABLE divergencia (
    tema_id TEXT, ano INTEGER, chave TEXT, estagio TEXT, siop REAL, portal REAL
);
CREATE TABLE ipca (mes TEXT PRIMARY KEY, indice REAL);
CREATE TABLE metadado (chave TEXT PRIMARY KEY, valor TEXT);
"""


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


def _mandato_id(c: Definicoes, dia: date) -> str | None:
    m = c.mandato_em(dia)
    return m.id if m else None


def construir(
    c: Definicoes,
    linhas_siop: list[dict],
    portal: dict[int, dict[str, dict[str, float]]],
    ipca: dict[str, float],
    caminho: Path = BANCO,
) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    temporario.unlink(missing_ok=True)
    db = sqlite3.connect(temporario)
    db.executescript(ESQUEMA)

    db.executemany(
        "INSERT INTO mandato VALUES (?, ?, ?, ?, ?, ?)",
        [(m.id, m.presidente, m.nome_curto, m.partido_na_posse, _iso(m.inicio), _iso(m.fim)) for m in c.mandatos],
    )
    for t in c.temas:
        db.execute("INSERT INTO tema VALUES (?, ?, ?, ?)", (t.id, t.nome, t.categoria.value, t.descricao))
        db.executemany(
            "INSERT INTO indicador VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(i.id, t.id, i.nome, i.unidade, i.tipo, i.descricao, _iso(i.levantado_ate)) for i in t.indicadores],
        )

    for a in c.atos.values():
        db.execute(
            "INSERT INTO ato VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                a.id, a.tipo, a.numero, a.titulo, a.ementa, _iso(a.data_assinatura), _iso(a.data_publicacao),
                _iso(a.vigencia_fim_prevista), a.url_oficial, a.id_materia_dou, a.sha256_xml,
                _mandato_id(c, a.data_assinatura),
            ),
        )
        db.executemany(
            "INSERT INTO signatario VALUES (?, ?, ?, ?)",
            [(a.id, n, s.nome, s.cargo) for n, s in enumerate(a.signatarios)],
        )

    for e in c.eventos:
        db.execute(
            "INSERT INTO evento VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                e.id, e.indicador_id, _iso(e.data_efeito), e.valor_antes, e.valor_depois,
                e.causa.value if e.causa else None, TEXTO_CAUSA[e.causa] if e.causa else "Valor inicial da série",
                e.ato_id, e.ato_origem_id, e.trecho, e.nota, _mandato_id(c, e.data_efeito),
            ),
        )

    db.executemany(
        "INSERT INTO acao_mapeada VALUES (?, ?, ?, ?, ?, ?)",
        [(m.tema_id, m.codigo, m.subfuncao, m.ano_inicio, m.ano_fim, m.justificativa) for m in c.acoes],
    )
    db.executemany(
        "INSERT INTO correcao VALUES (?, ?, ?, ?, ?)",
        [(x.objeto, x.objeto_id, _iso(x.data), x.o_que_mudou, x.motivo) for x in c.correcoes],
    )
    db.executemany(
        "INSERT INTO acao_excluida VALUES (?, ?, ?)", [(x.tema_id, x.codigo, x.motivo) for x in c.excluidas]
    )

    referencia = orc.mes_referencia(ipca)
    db.executemany("INSERT INTO ipca VALUES (?, ?)", sorted(ipca.items()))
    for t in c.temas:
        linhas = orc.linhas_do_tema(linhas_siop, c.acoes, t.id)
        db.executemany(
            "INSERT INTO orcamento VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    t.id, l["ano"], l["acao"], l["nome_acao"], l["programa"], l["nome_programa"], l["subfuncao"],
                    *(l[e] for e in orc.ESTAGIOS), orc.fator_correcao(ipca, l["ano"], referencia),
                )
                for l in linhas
            ],
        )
        do_tema = [m for m in c.acoes if m.tema_id == t.id]
        portal_do_tema = {
            ano: {
                chave: v
                for chave, v in por_chave.items()
                if orc.mapeamento_aplicavel(
                    {"ano": ano, "acao": chave.split("/")[0], "subfuncao": chave.split("/")[1]}, do_tema
                )
            }
            for ano, por_chave in portal.items()
        }
        db.executemany(
            "INSERT INTO divergencia VALUES (?, ?, ?, ?, ?, ?)",
            [(t.id, d.ano, d.chave, d.estagio, d.siop, d.portal) for d in orc.conferir(linhas, portal_do_tema)],
        )

    db.executemany(
        "INSERT INTO metadado VALUES (?, ?)",
        [("ipca_referencia", referencia), ("construido_em", date.today().isoformat())],
    )
    db.commit()
    db.close()
    temporario.replace(caminho)
    return caminho


def conectar(caminho: Path = BANCO) -> sqlite3.Connection:
    db = sqlite3.connect(caminho)
    db.row_factory = sqlite3.Row
    return db
