"""Senado Federal: votações (uso previsto na Fase 3).

O serviço antigo (/plenario/lista/votacao) foi desativado em 01/02/2026;
o substituto indicado pelo próprio Senado é /dadosabertos/votacao.
"""

import httpx

from .base import Resultado, Status

NOME = "Senado Federal"
URL = "https://legis.senado.leg.br/dadosabertos/votacao"
CAMPOS = {"codigoSessaoVotacao", "dataSessao", "identificacao", "ementa"}


def verificar(cliente: httpx.Client) -> Resultado:
    resp = cliente.get(
        URL,
        params={"dataInicio": "2023-05-01", "dataFim": "2023-05-31"},
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    dados = resp.json()
    if not dados:
        return Resultado(NOME, Status.FALHA, "Nenhuma votação retornada para maio/2023")

    faltando = CAMPOS - dados[0].keys()
    detalhes = [f"{len(dados)} votações nominais em maio/2023; exemplo: {dados[0]['identificacao']}"]
    if faltando:
        detalhes.append(f"Campos ausentes: {sorted(faltando)}")
        return Resultado(NOME, Status.PARCIAL, "Formato mudou", detalhes)
    return Resultado(NOME, Status.OK, "API nova (/votacao), sem chave, JSON", detalhes)
