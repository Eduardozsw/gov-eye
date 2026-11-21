# gov-eye

Linha do tempo verificável de tributos e políticas públicas federais: o que mudou, por que mudou, quem assinou e onde está o documento oficial.

- Especificação: [docs/ESPECIFICACAO.md](docs/ESPECIFICACAO.md)
- Resultado da validação das fontes: [docs/FASE0.md](docs/FASE0.md)
- Decisões de arquitetura: [docs/adr/](docs/adr/)

## Como rodar

Requer [uv](https://docs.astral.sh/uv/).

```sh
uv run goveye validar               # confere as definições em data/definicoes
uv run goveye carregar              # monta data/goveye.sqlite a partir das definições e de data/coletas
uv run goveye site                  # exporta a prévia para web/dados/site.json
uv run goveye site --modo publicacao  # recusa se site.yaml tiver PREENCHER; esconde anos com divergência SIOP × Portal
cd web && npm install && npm run dev  # abre o site em http://localhost:3000
cd web && npm run build             # site estático em web/out/
uv run pytest                       # testes (sem rede)
```

Coleta (acessa servidores públicos; respeita uma pausa entre requisições):

```sh
uv run goveye coletar-orcamento --anos 2018-2026  # SIOP, Portal da Transparência e IPCA
uv run goveye coletar-dou 2023-01 2023-02         # ZIP mensal do DOU (~530 MB cada), guarda só os atos filtrados
uv run goveye candidatos-dou --busca gasolina     # lista os atos filtrados do DOU
uv run goveye fase0                               # verifica todas as fontes oficiais
```

## Correções

Correção de algo já publicado (fica pública na página do item e em `/correcoes/`; nada é apagado):

```sh
uv run goveye corrigir evento pis-cofins-gasolina-2023-03 --o-que-mudou "Data de efeito corrigida de 01/03 para 02/03/2023" --motivo "Aviso de leitor; conferido no DOU"
```

Cada correção é acrescentada a `data/definicoes/correcoes.yaml`. Ajustes feitos antes da primeira publicação não são correções e não precisam ser registrados.

## Estrutura

```
data/definicoes/     o que o site mostra (YAML): temas, mandatos, atos, eventos, ações, glossário, correções
data/coletas/        instantâneos processados das fontes (versionados)
data/raw/            downloads brutos (fora do git)
src/goveye/fontes/   verificação de cada fonte oficial (Fase 0)
src/goveye/coleta/   coletores: DOU e orçamento
src/goveye/definicoes.py  leitura e validação dos YAML
src/goveye/banco.py  banco SQLite (derivado, reconstruído a cada carga)
src/goveye/site/     regras de publicação, frases, gráficos SVG e exportação para o front-end
web/                 front-end em Next.js (ADR 0002)
tests/               testes com fixtures fictícias
```

## Licença

Código: [AGPL-3.0](LICENSE). Quem publicar uma versão alterada, inclusive como site, precisa abrir o código dela.
Dados publicados: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br), uso livre com crédito ao gov-eye.
