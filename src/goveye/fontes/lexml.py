"""LexML: identificadores URN e metadados de normas."""

import httpx

from .base import Resultado, Status

NOME = "LexML (SRU)"
URL = "https://www.lexml.gov.br/busca/SRU"


def verificar(cliente: httpx.Client) -> Resultado:
    resp = cliente.get(
        URL,
        params={
            "operation": "searchRetrieve",
            "version": "1.1",
            "query": 'urn="urn:lex:br:federal:lei:2023-06-19;14601"',
            "maximumRecords": 1,
        },
    )
    if "Verificação de segurança" in resp.text:
        return Resultado(
            NOME,
            Status.BLOQUEADO,
            "Devolve página anti-robô em vez de XML",
            ["Dispensável no MVP: a URN pode ser montada a partir do tipo, data e número do ato"],
        )
    resp.raise_for_status()
    if "searchRetrieveResponse" not in resp.text:
        return Resultado(NOME, Status.FALHA, "Resposta não é SRU", [resp.text[:200]])
    return Resultado(NOME, Status.OK, "SRU respondeu com XML")
