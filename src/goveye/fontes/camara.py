"""Câmara dos Deputados: votações (uso previsto na Fase 3)."""

import httpx

from .base import Resultado, Status

NOME = "Câmara dos Deputados"
URL = "https://dadosabertos.camara.leg.br/api/v2/votacoes"
CAMPOS = {"id", "data", "siglaOrgao", "descricao"}


def verificar(cliente: httpx.Client) -> Resultado:
    resp = cliente.get(
        URL,
        params={"dataInicio": "2023-03-01", "dataFim": "2023-03-10", "itens": 5},
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    dados = resp.json()["dados"]
    if not dados:
        return Resultado(NOME, Status.FALHA, "Nenhuma votação retornada para março/2023")

    faltando = CAMPOS - dados[0].keys()
    detalhes = [f"{len(dados)} votações na amostra; exemplo: {dados[0]['id']} em {dados[0]['data']}"]
    if faltando:
        detalhes.append(f"Campos ausentes: {sorted(faltando)}")
        return Resultado(NOME, Status.PARCIAL, "Formato mudou", detalhes)
    return Resultado(NOME, Status.OK, "API REST pública, sem chave, JSON", detalhes)
