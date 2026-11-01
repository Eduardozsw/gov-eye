from datetime import date

import pytest

from conftest import escrever_yaml
from goveye import banco
from goveye import curadoria as cur
from goveye.site import formato, svg, textos
from goveye.site.gerar import ErroPublicacao, gerar

HOJE = date(2026, 6, 30)


@pytest.fixture
def banco_teste(tmp_path, pasta_curadoria, orcamento_sintetico):
    siop, portal, ipca = orcamento_sintetico
    return banco.construir(cur.carregar(pasta_curadoria), siop, portal, ipca, tmp_path / "teste.sqlite")


def _gerar(modo, banco_teste, pasta_curadoria, tmp_path):
    return gerar(modo, banco=banco_teste, saida=tmp_path / modo, curadoria=pasta_curadoria, hoje=HOJE)


def test_previa_mostra_pendentes_com_selo(banco_teste, pasta_curadoria, tmp_path):
    saida = _gerar("previa", banco_teste, pasta_curadoria, tmp_path)
    html = (saida / "tema" / "combustiveis.html").read_text(encoding="utf-8")
    assert "PRÉVIA INTERNA" in html
    assert "pendente de revisão" in html
    assert "Prazo previsto no ato original terminou" in html
    assert 'name="robots" content="noindex' in html
    assert (saida / "ato" / "mp-teste-2.html").exists()


def test_publicacao_para_no_primeiro_evento_pendente(banco_teste, pasta_curadoria, tmp_path):
    saida = _gerar("publicacao", banco_teste, pasta_curadoria, tmp_path)
    html = (saida / "tema" / "combustiveis.html").read_text(encoding="utf-8")
    assert "PRÉVIA" not in html
    assert "pendente de revisão" not in html
    assert "R$ 0,5000" in html  # valor inicial, revisado duas vezes
    assert "Medida Provisória nº 2.000/2022" not in html  # eventos seguintes ainda pendentes
    assert "eventos seguintes ainda estão em revisão" in html
    assert not (saida / "ato" / "mp-teste-2.html").exists()


def test_publicacao_esconde_orcamento_com_mapeamento_pendente(banco_teste, pasta_curadoria, tmp_path):
    saida = _gerar("publicacao", banco_teste, pasta_curadoria, tmp_path)
    html = (saida / "tema" / "politica-y.html").read_text(encoding="utf-8")
    assert "ainda está em revisão" in html
    assert "<svg" not in html


def test_publicacao_bloqueia_ano_com_divergencia(tmp_path, pasta_curadoria, orcamento_sintetico):
    cur.registrar_revisao("acao", "politica-y:AAAA", "Curador", date(2026, 1, 1), pasta_curadoria)
    cur.registrar_revisao("acao", "politica-y:AAAA", "Curador", date(2026, 1, 2), pasta_curadoria)
    siop, portal, ipca = orcamento_sintetico
    caminho = banco.construir(cur.carregar(pasta_curadoria), siop, portal, ipca, tmp_path / "b.sqlite")
    saida = _gerar("publicacao", caminho, pasta_curadoria, tmp_path)
    html = (saida / "tema" / "politica-y.html").read_text(encoding="utf-8")
    assert "<svg" in html
    assert "2022: valores em conferência" in html  # SIOP e Portal divergem no pago de 2022
    assert "Em 2021, o orçamento autorizou" in html


def test_publicacao_recusa_campos_a_preencher(banco_teste, pasta_curadoria, tmp_path):
    (pasta_curadoria / "site.yaml").write_text("responsavel:\n  nome: PREENCHER\n", encoding="utf-8")
    with pytest.raises(ErroPublicacao):
        _gerar("publicacao", banco_teste, pasta_curadoria, tmp_path)


def test_manifesto_dos_dados(banco_teste, pasta_curadoria, tmp_path):
    import hashlib

    saida = _gerar("previa", banco_teste, pasta_curadoria, tmp_path)
    for linha in (saida / "dados" / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        soma, nome = linha.split("  ")
        assert hashlib.sha256((saida / "dados" / nome).read_bytes()).hexdigest() == soma


def test_formatos_brasileiros():
    assert formato.moeda(1234567.891) == "R$ 1.234.567,89"
    assert formato.aliquota(0.7925) == "R$ 0,7925"
    assert formato.moeda_curta(2_500_000_000) == "R$ 2,5 bi"
    assert formato.moeda_curta(12_000_000) == "R$ 12 mi"
    assert formato.data_br("2023-01-01") == "01/01/2023"
    assert formato.data_extenso("2023-03-01") == "1º de março de 2023"


def test_frase_de_expiracao_atribui_ao_ato_de_origem():
    ato = {"tipo": "Medida Provisória", "titulo": "Medida Provisória nº 2.000/2022", "data_assinatura": "2022-06-01",
           "signatarios": [{"nome": "Presidente A", "cargo": "Presidente"}]}
    evento = {"data_efeito": "2023-01-01", "causa": "EXPIRACAO_PREVISTA", "valor_antes": 0.0, "valor_depois": 0.5,
              "texto_causa": "Prazo previsto no ato original terminou"}
    frase = textos.frase_evento(evento, {"nome": "Tributo X"}, ato, None, ato, {"nome_curto": "A"}, formato.aliquota)
    assert "voltou a ser cobrado" in frase
    assert "na Medida Provisória nº 2.000/2022, assinada em 1º de junho de 2022" in frase
    assert "(governo A)" in frase
    assert "Nenhum ato novo" in frase


def test_topo_do_eixo():
    assert svg.topo_eixo(0.87) == 1.0
    assert svg.topo_eixo(0.3) == 0.5
    assert svg.topo_eixo(1.6e11) == 2e11
    assert svg.topo_eixo(0) == 1.0


def test_serie_nao_passa_da_data_de_levantamento(tmp_path, pasta_curadoria, orcamento_sintetico):
    temas = cur._ler(pasta_curadoria / "temas.yaml")
    temas["temas"][0]["indicadores"][0]["levantado_ate"] = date(2023, 6, 30)
    escrever_yaml(pasta_curadoria / "temas.yaml", temas)
    siop, portal, ipca = orcamento_sintetico
    caminho = banco.construir(cur.carregar(pasta_curadoria), siop, portal, ipca, tmp_path / "b.sqlite")
    saida = _gerar("previa", caminho, pasta_curadoria, tmp_path)
    html = (saida / "tema" / "combustiveis.html").read_text(encoding="utf-8")
    assert "Série levantada até 30/06/2023" in html
    inicio = (saida / "index.html").read_text(encoding="utf-8")
    assert "série levantada até 30/06/2023" in inicio
