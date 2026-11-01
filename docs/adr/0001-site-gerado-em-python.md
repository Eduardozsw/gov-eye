# ADR 0001: Site estático gerado em Python, sem Astro

- Status: substituído em parte pelo ADR 0002 (itens 1 e 2: o site passou a ser desenhado em Next.js; os itens 3 e 4 continuam valendo)
- Data: 2026-11-01

## Contexto

A especificação (seção 10) previa Astro com uma biblioteca de gráficos leve. Depois da Fase 0, a coleta, a validação, o banco e as regras editoriais (seção 9) ficaram todos em Python. Com Astro, o projeto teria duas linguagens, dois gerenciadores de pacote e uma etapa intermediária para levar os dados do Python para o JavaScript.

## Decisão

1. **Site gerado em Python com Jinja2.** O mesmo processo que valida a curadoria gera as páginas, então uma regra (por exemplo, "série para no primeiro item não revisado") vale igual para o site, para o CSV e para o JSON.
2. **Gráficos em SVG gerados no servidor**, sem JavaScript. Funcionam em celular simples e conexão lenta (seção 8.4), aparecem quando alguém salva a página e são lidos por leitores de tela, com `<title>` e `aria-label`. Cada gráfico vem acompanhado de uma lista ou tabela com os mesmos dados. A alternância nominal/corrigido usa só CSS (botões de rádio).
3. **SQLite é produto derivado e não é versionado.** A fonte da verdade fica em arquivos legíveis no git:
   - `data/curadoria/*.yaml`: decisões editoriais (atos, eventos, mapeamento de ações, revisões);
   - `data/coletas/*.json`: instantâneos processados das fontes (pequenos), que permitem reconstruir o banco e o site sem rede;
   - `data/raw/`: downloads brutos grandes (ZIPs do DOU e do Portal), fora do git.
   O banco é reconstruído do zero a cada `goveye carregar`, então nunca diverge dos YAML.
4. **Revisões em registro próprio**, `data/curadoria/revisoes.yaml`, ao qual só se acrescentam linhas (comando `goveye revisar`). Assim a revisão não reescreve os YAML comentados e o histórico de quem revisou o quê fica num lugar só, fácil de auditar no `git log`. Revisões escritas dentro dos próprios arquivos continuam aceitas.

## Consequências

- Uma linguagem só e um comando (`uv run goveye site`) do dado ao HTML.
- A interatividade fica limitada a `<details>`, `<title>` nos pontos e CSS. Se no futuro for preciso busca no site ou gráfico com zoom, dá para acrescentar um script pequeno sem trocar o gerador.
- Os cards de compartilhamento (seção 8.3) ainda não existem. Gerar PNG no servidor exige uma dependência de renderização (por exemplo, `cairosvg` ou um navegador sem interface), a decidir.
