# gov-eye

Linha do tempo verificável de tributos e políticas públicas federais: o que mudou, por que mudou, quem assinou e onde está o documento oficial.

- Especificação: [docs/ESPECIFICACAO.md](docs/ESPECIFICACAO.md)
- Resultado da validação das fontes: [docs/FASE0.md](docs/FASE0.md)
- Decisões de arquitetura: [docs/adr/](docs/adr/)

## Como rodar

Requer [uv](https://docs.astral.sh/uv/).

```sh
uv run goveye validar               # confere a curadoria e mostra quantos itens faltam revisar
uv run goveye carregar              # monta data/goveye.sqlite a partir da curadoria e de data/coletas
uv run goveye site                  # gera a prévia em site/ (com itens pendentes marcados)
uv run goveye site --modo publicacao  # só itens revisados; recusa se site.yaml tiver PREENCHER
uv run pytest                       # testes (sem rede)
```

Coleta (acessa servidores públicos; respeita uma pausa entre requisições):

```sh
uv run goveye coletar-orcamento --anos 2018-2026  # SIOP, Portal da Transparência e IPCA
uv run goveye coletar-dou 2023-01 2023-02         # ZIP mensal do DOU (~530 MB cada), guarda só os atos filtrados
uv run goveye candidatos-dou --busca gasolina     # lista os atos filtrados para o curador
uv run goveye fase0                               # verifica todas as fontes oficiais
```

## Revisão (só o curador)

Nada vai ao ar sem duas revisões em dias diferentes (ou dois revisores).

```sh
uv run goveye pendentes
uv run goveye revisar acao mulheres:21GI --revisor "Seu Nome"
uv run goveye revisar evento pis-cofins-gasolina-2023-03 --revisor "Seu Nome"
uv run goveye revisar ato mp-1157-2023 --revisor "Seu Nome"
```

Cada revisão é acrescentada a `data/curadoria/revisoes.yaml`.

## Estrutura

```
data/curadoria/      fonte da verdade editorial (YAML): temas, mandatos, atos, eventos, ações, revisões
data/coletas/        instantâneos processados das fontes (versionados)
data/raw/            downloads brutos (fora do git)
src/goveye/fontes/   verificação de cada fonte oficial (Fase 0)
src/goveye/coleta/   coletores: DOU e orçamento
src/goveye/curadoria.py  leitura e validação dos YAML
src/goveye/banco.py  banco SQLite (derivado, reconstruído a cada carga)
src/goveye/site/     gerador do site estático (Jinja2 + SVG)
tests/               testes com fixtures fictícias
```

## Licença

Código: todos os direitos reservados. Dados publicados: CC BY-NC 4.0.
