"""Caminhos e parâmetros compartilhados."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DADOS = RAIZ / "data"
BRUTOS = DADOS / "raw"
# Resultados processados das coletas (pequenos, versionados): permitem refazer o site sem rede.
COLETAS = DADOS / "coletas"
DEFINICOES = DADOS / "definicoes"
BANCO = DADOS / "goveye.sqlite"
# Front-end em Next.js; recebe web/dados/site.json e os dados abertos em web/public/dados/.
WEB = RAIZ / "web"

ANO_INICIAL = 2018
ANO_FINAL = 2026

# Intervalo entre requisições à mesma fonte, para não sobrecarregar servidores públicos.
PAUSA_ENTRE_REQUISICOES = 2.0
