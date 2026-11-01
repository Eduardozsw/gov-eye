# ADR 0002: Front-end em Next.js, regras e dados em Python

- Status: proposto (aguardando aprovação do responsável)
- Data: 2026-11-01
- Substitui em parte: ADR 0001 (itens 1 e 2; os itens 3 e 4 continuam valendo)

## Contexto

O responsável pediu um site com identidade visual própria: um olho animado que se move de um lado a outro, como quem procura algo, e uma caixa de busca no centro da tela com exemplos de perguntas que se escrevem e se apagam. Pediu também Next.js, padrão de mercado. O gerador em Jinja2 (ADR 0001) não tinha busca nem componentes interativos.

## Decisão

1. **Python continua sendo o lugar das regras.** A classe `Montagem` (`src/goveye/site/gerar.py`) decide o que é publicável em cada modo, monta as frases por modelo fixo (seção 9) e desenha os gráficos SVG. `uv run goveye site --modo <modo>` grava tudo, já formatado, em `web/dados/site.json`, e os dados abertos em `web/public/dados/`. Os dois são gerados e ficam fora do git.
2. **Next.js só desenha a interface** (`web/`, App Router, TypeScript). Lê o `site.json` no build e não recalcula valores. Assim uma regra como "a série para no primeiro item não revisado" continua com um único dono, coberto pelos testes em Python.
3. **Exportação estática** (`output: "export"`). O resultado em `web/out/` é HTML puro e pode ser hospedado em qualquer servidor de arquivos (Cloudflare Pages, por exemplo), sem servidor Node em produção.
4. **Busca no navegador.** O índice (`busca` no `site.json`) traz temas, séries, mudanças, anos de orçamento, ações e atos, com o texto onde procurar. A busca (`web/lib/busca.ts`) ignora acentos, aceita plural e entende palavras do leitor que não aparecem no texto oficial ("zerou", "imposto", "gastou"). Um teste garante que cada frase de exemplo da página inicial tem resultado. `/?q=termo` abre a página já com os resultados, para compartilhar uma busca.
5. **Animação acessível.** O olho e o texto que se escreve são feitos em SVG e CSS, sem biblioteca. Com "reduzir movimento" ligado no sistema, ficam parados. Ao focar a busca, o olho para e olha para a caixa.
6. **Paleta neutra** (índigo e turquesa), sem vermelho nem verde-amarelo, que no Brasil são lidos como cores de partido ou de campo político.

## Consequências

- Duas linguagens e dois gerenciadores de pacote (uv e npm). O CI roda os dois.
- O site depende de JavaScript para a busca e a animação; o resto (textos, gráficos, linha do tempo, alternância nominal/corrigido) funciona sem ele, porque as páginas são pré-renderizadas.
- As fontes (Inter e Space Grotesk) são baixadas do Google Fonts no build e servidas pelo próprio site; o build precisa de rede.
- Os cards de compartilhamento (seção 8.3) continuam pendentes. Com Next.js, a rota `opengraph-image` gera PNG no build, sem dependência nova; fica para a próxima etapa.
