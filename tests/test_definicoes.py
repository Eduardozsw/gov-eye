from datetime import date

import pytest

from conftest import escrever_yaml
from goveye import definicoes as defs


def test_carrega_fixture(pasta_definicoes):
    c = defs.carregar(pasta_definicoes)
    assert len(c.atos) == 2
    assert [e.id for e in c.eventos_do_indicador("tributo-x")] == ["tributo-x-inicial", "tributo-x-zerado", "tributo-x-volta"]
    assert c.mandato_em(date(2022, 6, 1)).id == "governo-a"
    assert c.mandato_em(date(2023, 1, 1)).id == "governo-b"
    assert len(c.excluidas) == 1


def _eventos(pasta):
    return defs._ler(pasta / "eventos" / "tributo-x.yaml")


def test_continuidade_da_serie(pasta_definicoes):
    eventos = _eventos(pasta_definicoes)
    eventos["eventos"][2]["valor_antes"] = 0.1  # não bate com o valor_depois anterior (0,0)
    escrever_yaml(pasta_definicoes / "eventos" / "tributo-x.yaml", eventos)
    with pytest.raises(defs.ErroDefinicoes, match="não bate"):
        defs.carregar(pasta_definicoes)


def test_expiracao_exige_ato_de_origem_com_vigencia(pasta_definicoes):
    eventos = _eventos(pasta_definicoes)
    eventos["eventos"][2]["ato_origem"] = "decreto-teste-1"  # não tem vigencia_fim_prevista
    escrever_yaml(pasta_definicoes / "eventos" / "tributo-x.yaml", eventos)
    with pytest.raises(defs.ErroDefinicoes, match="não tem vigência prevista"):
        defs.carregar(pasta_definicoes)


def test_primeiro_evento_e_valor_inicial(pasta_definicoes):
    eventos = _eventos(pasta_definicoes)
    eventos["eventos"][0]["causa"] = "ATO_NOVO"
    escrever_yaml(pasta_definicoes / "eventos" / "tributo-x.yaml", eventos)
    with pytest.raises(defs.ErroDefinicoes, match="valor inicial"):
        defs.carregar(pasta_definicoes)


def test_link_precisa_ser_oficial(pasta_definicoes):
    ato = defs._ler(pasta_definicoes / "atos" / "decreto-teste-1.yaml")
    ato["url_oficial"] = "https://exemplo.com/decreto"
    escrever_yaml(pasta_definicoes / "atos" / "decreto-teste-1.yaml", ato)
    with pytest.raises(defs.ErroDefinicoes, match="domínio oficial"):
        defs.carregar(pasta_definicoes)


def test_acao_nao_pode_ser_incluida_e_excluida(pasta_definicoes):
    acoes = defs._ler(pasta_definicoes / "acoes.yaml")
    acoes["excluidas"].append({"tema": "politica-y", "acao": "AAAA", "motivo": "conflito"})
    escrever_yaml(pasta_definicoes / "acoes.yaml", acoes)
    with pytest.raises(defs.ErroDefinicoes, match="incluída e excluída"):
        defs.carregar(pasta_definicoes)


def test_registro_de_correcoes(pasta_definicoes):
    defs.registrar_correcao("evento", "tributo-x-zerado", "Data de efeito corrigida de 31/05 para 01/06/2022",
                           "Leitura errada da data de publicação", date(2026, 3, 1), pasta_definicoes)
    defs.registrar_correcao("ato", "mp-teste-2", "Cargo do signatário corrigido", "Erro de digitação",
                           date(2026, 3, 2), pasta_definicoes)
    c = defs.carregar(pasta_definicoes)
    assert [(x.objeto, x.objeto_id, x.data) for x in c.correcoes] == [
        ("evento", "tributo-x-zerado", date(2026, 3, 1)),
        ("ato", "mp-teste-2", date(2026, 3, 2)),
    ]
    assert c.correcoes[0].motivo == "Leitura errada da data de publicação"


def test_correcao_exige_objeto_existente_e_motivo(pasta_definicoes):
    with pytest.raises(defs.ErroDefinicoes):
        defs.registrar_correcao("evento", "nao-existe", "x", "y", date(2026, 3, 1), pasta_definicoes)
    with pytest.raises(defs.ErroDefinicoes):
        defs.registrar_correcao("evento", "tributo-x-zerado", "x", " ", date(2026, 3, 1), pasta_definicoes)
    (pasta_definicoes / "correcoes.yaml").write_text(
        "correcoes:\n  - {objeto: evento, id: sumiu, data: 2026-03-01, o_que_mudou: x, motivo: y}\n", encoding="utf-8"
    )
    with pytest.raises(defs.ErroDefinicoes, match="sumiu"):
        defs.carregar(pasta_definicoes)
