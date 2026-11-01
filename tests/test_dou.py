import io
import zipfile

from goveye.coleta import dou

XML_ATO = """<xml><article idMateria="123" artType="Decreto numerado" pubDate="02/01/2023"
 artCategory="Atos do Poder Executivo" pdfPage="http://pesquisa.in.gov.br/x?a=1&amp;b=2"
 editionNumber="1" numberPage="3"><body>
<Identifica><![CDATA[DECRETO Nº 1, DE 1º DE JANEIRO DE 2023]]></Identifica>
<Ementa><![CDATA[Reduz as alíquotas da Contribuição para o PIS/Pasep e da Cofins sobre a gasolina.]]></Ementa>
<Texto><![CDATA[<p>Art. 1º&nbsp;Ficam reduzidas a zero as alíquotas.</p><p>Art. 2º Vigência.</p>]]></Texto>
</body></article></xml>"""

XML_OUTRO = XML_ATO.replace('artType="Decreto numerado"', 'artType="Portaria"').replace('idMateria="123"', 'idMateria="9"')


def test_ler_artigo():
    ato = dou.ler_artigo(XML_ATO.encode(), "teste.zip:1.xml")
    assert ato.id_materia == "123"
    assert ato.data_publicacao == "2023-01-02"
    assert ato.url_pdf == "http://pesquisa.in.gov.br/x?a=1&b=2"
    assert ato.texto.splitlines() == ["Art. 1º Ficam reduzidas a zero as alíquotas.", "Art. 2º Vigência."]
    assert len(ato.sha256_xml) == 64


def test_filtro_de_relevancia():
    assert dou.e_relevante(dou.ler_artigo(XML_ATO.encode(), "x"))
    assert not dou.e_relevante(dou.ler_artigo(XML_OUTRO.encode(), "x"))  # portaria não é ato normativo do filtro
    sem_combustivel = XML_ATO.replace("sobre a gasolina", "sobre receitas financeiras")
    assert not dou.e_relevante(dou.ler_artigo(sem_combustivel.encode(), "x"))


def test_formato_antigo_com_tipo_em_caixa_alta():
    antigo = XML_ATO.replace('artType="Decreto numerado"', 'artType="DECRETO"').replace('idMateria="123" ', "")
    assert dou.e_relevante(dou.ler_artigo(antigo.encode(), "x"))


def test_ler_zip_ignora_arquivos_invalidos(tmp_path):
    caminho = tmp_path / "S01012023.zip"
    with zipfile.ZipFile(caminho, "w") as zf:
        zf.writestr("1.xml", XML_ATO)
        zf.writestr("2.xml", "<quebrado")
        zf.writestr("imagem.jpg", b"\xff\xd8")
    atos = list(dou.ler_zip(caminho))
    assert [a.id_materia for a in atos] == ["123"]
