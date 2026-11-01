from datetime import date

import pytest

from conftest import escrever_yaml
from goveye import curadoria as cur
from goveye.modelo import Revisao, StatusRevisao, publicavel, status_revisao


def test_carrega_fixture(pasta_curadoria):
    c = cur.carregar(pasta_curadoria)
    assert len(c.atos) == 2
    assert [e.id for e in c.eventos_do_indicador("tributo-x")] == ["tributo-x-inicial", "tributo-x-zerado", "tributo-x-volta"]
    assert c.mandato_em(date(2022, 6, 1)).id == "governo-a"
    assert c.mandato_em(date(2023, 1, 1)).id == "governo-b"
    assert len(c.excluidas) == 1


def _eventos(pasta):
    return cur._ler(pasta / "eventos" / "tributo-x.yaml")


def test_continuidade_da_serie(pasta_curadoria):
    eventos = _eventos(pasta_curadoria)
    eventos["eventos"][2]["valor_antes"] = 0.1  # não bate com o valor_depois anterior (0,0)
    escrever_yaml(pasta_curadoria / "eventos" / "tributo-x.yaml", eventos)
    with pytest.raises(cur.ErroCuradoria, match="não bate"):
        cur.carregar(pasta_curadoria)


def test_expiracao_exige_ato_de_origem_com_vigencia(pasta_curadoria):
    eventos = _eventos(pasta_curadoria)
    eventos["eventos"][2]["ato_origem"] = "decreto-teste-1"  # não tem vigencia_fim_prevista
    escrever_yaml(pasta_curadoria / "eventos" / "tributo-x.yaml", eventos)
    with pytest.raises(cur.ErroCuradoria, match="não tem vigência prevista"):
        cur.carregar(pasta_curadoria)


def test_primeiro_evento_e_valor_inicial(pasta_curadoria):
    eventos = _eventos(pasta_curadoria)
    eventos["eventos"][0]["causa"] = "ATO_NOVO"
    escrever_yaml(pasta_curadoria / "eventos" / "tributo-x.yaml", eventos)
    with pytest.raises(cur.ErroCuradoria, match="valor inicial"):
        cur.carregar(pasta_curadoria)


def test_link_precisa_ser_oficial(pasta_curadoria):
    ato = cur._ler(pasta_curadoria / "atos" / "decreto-teste-1.yaml")
    ato["url_oficial"] = "https://exemplo.com/decreto"
    escrever_yaml(pasta_curadoria / "atos" / "decreto-teste-1.yaml", ato)
    with pytest.raises(cur.ErroCuradoria, match="domínio oficial"):
        cur.carregar(pasta_curadoria)


def test_acao_nao_pode_ser_incluida_e_excluida(pasta_curadoria):
    acoes = cur._ler(pasta_curadoria / "acoes.yaml")
    acoes["excluidas"].append({"tema": "politica-y", "acao": "AAAA", "motivo": "conflito"})
    escrever_yaml(pasta_curadoria / "acoes.yaml", acoes)
    with pytest.raises(cur.ErroCuradoria, match="incluída e excluída"):
        cur.carregar(pasta_curadoria)


def test_protocolo_de_revisao():
    d1, d2 = date(2026, 1, 1), date(2026, 1, 2)
    assert status_revisao([]) == StatusRevisao.PENDENTE
    assert status_revisao([Revisao("A", d1)]) == StatusRevisao.PRIMEIRA_PASSAGEM
    assert status_revisao([Revisao("A", d1), Revisao("A", d1)]) == StatusRevisao.PRIMEIRA_PASSAGEM
    assert status_revisao([Revisao("A", d1), Revisao("A", d2)]) == StatusRevisao.REVISAO_INDIVIDUAL
    assert status_revisao([Revisao("A", d1), Revisao("B", d1)]) == StatusRevisao.REVISADO
    assert not publicavel(StatusRevisao.PRIMEIRA_PASSAGEM)
    assert publicavel(StatusRevisao.REVISAO_INDIVIDUAL)


def test_registro_de_revisoes(pasta_curadoria):
    cur.registrar_revisao("acao", "politica-y:AAAA", "Curador", date(2026, 2, 1), pasta_curadoria)
    cur.registrar_revisao("acao", "politica-y:AAAA", "Curador", date(2026, 2, 3), pasta_curadoria)
    c = cur.carregar(pasta_curadoria)
    assert status_revisao(c.acoes[0].revisoes) == StatusRevisao.REVISAO_INDIVIDUAL


def test_registro_recusa_objeto_inexistente(pasta_curadoria):
    with pytest.raises(cur.ErroCuradoria, match="inexistente"):
        cur.registrar_revisao("ato", "nao-existe", "Curador", date(2026, 2, 1), pasta_curadoria)
