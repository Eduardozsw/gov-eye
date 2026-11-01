import pytest

from goveye import orcamento as orc
from goveye.modelo import AcaoMapeada


def test_mapeamento_respeita_subfuncao_e_anos():
    m = AcaoMapeada("t", "AAAA", "x", subfuncao="423", ano_inicio=2020, ano_fim=2022)
    assert m.vale_em(2021, "423")
    assert not m.vale_em(2021, "122")
    assert not m.vale_em(2019, "423")
    assert not m.vale_em(2023, "423")


def test_totais_do_tema(orcamento_sintetico):
    siop, _, _ = orcamento_sintetico
    mapa = [AcaoMapeada("politica-y", "AAAA", "x", subfuncao="423")]
    totais = orc.totais_por_ano(orc.linhas_do_tema(siop, mapa, "politica-y"))
    assert totais[2022]["pago"] == 200.0  # a linha da subfunção 122 ficou fora
    assert list(totais) == [2021, 2022]


def test_correcao_pela_inflacao(orcamento_sintetico):
    _, _, ipca = orcamento_sintetico
    ref = orc.mes_referencia(ipca)
    assert ref == "202212"
    assert orc.fator_correcao(ipca, 2021, ref) == pytest.approx(1.10)
    assert orc.fator_correcao(ipca, 2022, ref) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        orc.fator_correcao(ipca, 2018, ref)


def test_conferencia_siop_portal(orcamento_sintetico):
    siop, portal, _ = orcamento_sintetico
    linhas = [l for l in siop if l["subfuncao"] == "423"]
    divergencias = orc.conferir(linhas, portal)
    assert [(d.ano, d.chave, d.estagio) for d in divergencias] == [(2022, "AAAA/423", "pago")]


def test_conferencia_tolera_centavos():
    linhas = [{"ano": 2021, "acao": "A", "subfuncao": "1", "inicial": 10.0, "atualizada": 10.0,
               "empenhado": 10.0, "pago": 10.0}]
    portal = {2021: {"A/1": {"inicial": 10.4, "atualizada": 10.0, "empenhado": 10.0, "pago": 9.7}}}
    assert orc.conferir(linhas, portal) == []
