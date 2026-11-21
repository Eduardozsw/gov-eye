"""Linha de comando do gov-eye: `uv run goveye <comando>`."""

import argparse
import sys
from datetime import date

from . import definicoes as defs
from .config import ANO_FINAL, ANO_INICIAL


def _mes(texto: str) -> tuple[int, int]:
    ano, mes = texto.split("-")
    return int(ano), int(mes)


def _anos(texto: str) -> range:
    inicio, _, fim = texto.partition("-")
    return range(int(inicio), int(fim or inicio) + 1)


def cmd_validar(_: argparse.Namespace) -> int:
    c = defs.carregar()
    print(f"temas: {len(c.temas)}, atos: {len(c.atos)}, eventos: {len(c.eventos)}")
    print(f"ações: {len(c.acoes)}, ações excluídas: {len(c.excluidas)}, correções: {len(c.correcoes)}")
    print("Definições válidas.")
    return 0


def cmd_corrigir(args: argparse.Namespace) -> int:
    dia = date.fromisoformat(args.data) if args.data else date.today()
    defs.registrar_correcao(args.objeto, args.id, args.o_que_mudou, args.motivo, dia)
    print(f"Correção registrada em {defs.ARQUIVO_CORRECOES}. Ela aparece no site na próxima exportação.")
    return 0


def cmd_coletar_orcamento(args: argparse.Namespace) -> int:
    from .pipeline import coletar_orcamento

    coletar_orcamento(args.anos)
    return 0


def cmd_coletar_dou(args: argparse.Namespace) -> int:
    from .pipeline import coletar_dou

    coletar_dou(args.meses, manter_zip=args.manter_zip)
    return 0


def cmd_candidatos_dou(args: argparse.Namespace) -> int:
    from .coleta.dou import carregar_filtrados

    for a in carregar_filtrados():
        if args.busca and args.busca.lower() not in f"{a.identifica} {a.ementa} {a.texto}".lower():
            continue
        print(f"{a.data_publicacao}  {a.tipo:18} {a.identifica or '(sem título)'}")
        print(f"            {a.ementa[:160]}")
        print(f"            id {a.id_materia}  {a.url_pdf}")
    return 0


def cmd_conferir_trechos(_: argparse.Namespace) -> int:
    """Confere se o trecho de cada evento aparece no texto do DOU coletado para o ato (pelo SHA-256)."""
    import re

    from .coleta.dou import carregar_filtrados

    def normalizar(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip(' "')

    textos = {a.sha256_xml: normalizar(a.texto) for a in carregar_filtrados()}
    c = defs.carregar()
    falhas = 0
    for e in c.eventos:
        texto = textos.get(c.atos[e.ato_id].sha256_xml)
        if texto is None:
            situacao = "texto do ato não coletado"
        elif all(normalizar(p) in texto for p in e.trecho.split("[...]")):
            situacao = "ok"
        else:
            situacao = "TRECHO NÃO ENCONTRADO"
        falhas += situacao != "ok"
        print(f"{e.id:45} {situacao}")
    return 1 if falhas else 0


def cmd_carregar(_: argparse.Namespace) -> int:
    from .pipeline import carregar

    print(f"Banco gerado em {carregar()}")
    return 0


def cmd_site(args: argparse.Namespace) -> int:
    from .site.gerar import exportar

    print(f"Dados do site ({args.modo}) exportados para {exportar(args.modo)}")
    print("Para ver: cd web && npm run dev (ou npm run build para gerar web/out/)")
    return 0


def cmd_fase0(args: argparse.Namespace) -> int:
    from . import fase0

    sys.argv = ["fase0", *args.resto]
    fase0.main()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="goveye", description="Pipeline do gov-eye")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("validar", help="valida as definições e mostra quantos itens há").set_defaults(f=cmd_validar)

    p = sub.add_parser("corrigir", help="registra uma correção no histórico público (data/definicoes/correcoes.yaml)")
    p.add_argument("objeto", choices=defs.OBJETOS_CORRIGIVEIS)
    p.add_argument("id", help="id do ato ou evento; para ação, tema:codigo (ex.: mulheres:21GI)")
    p.add_argument("--o-que-mudou", required=True, help='ex.: "Valor corrigido de R$ 0,79 para R$ 0,7925 por litro"')
    p.add_argument("--motivo", required=True, help='ex.: "Erro de arredondamento apontado por leitor"')
    p.add_argument("--data", help="AAAA-MM-DD (padrão: hoje)")
    p.set_defaults(f=cmd_corrigir)

    p = sub.add_parser("coletar-orcamento", help="baixa SIOP, Portal da Transparência e IPCA")
    p.add_argument("--anos", type=_anos, default=range(ANO_INICIAL, ANO_FINAL + 1), help="ex.: 2018-2026")
    p.set_defaults(f=cmd_coletar_orcamento)

    p = sub.add_parser("coletar-dou", help="baixa meses do DOU (Seção 1) e filtra atos sobre combustíveis")
    p.add_argument("meses", nargs="+", type=_mes, help="AAAA-MM")
    p.add_argument("--manter-zip", action="store_true", help="não apaga o ZIP mensal (cerca de 530 MB)")
    p.set_defaults(f=cmd_coletar_dou)

    p = sub.add_parser("candidatos-dou", help="lista os atos do DOU já filtrados")
    p.add_argument("--busca", help="texto que deve aparecer no ato")
    p.set_defaults(f=cmd_candidatos_dou)

    sub.add_parser("conferir-trechos", help="confere os trechos dos eventos com o texto do DOU").set_defaults(
        f=cmd_conferir_trechos
    )

    sub.add_parser("carregar", help="monta o banco SQLite a partir das definições e das coletas").set_defaults(
        f=cmd_carregar
    )

    p = sub.add_parser("site", help="exporta os dados do site para web/ (Next.js)")
    p.add_argument("--modo", choices=("previa", "publicacao"), default="previa")
    p.set_defaults(f=cmd_site)

    p = sub.add_parser("fase0", help="verifica as fontes oficiais")
    p.add_argument("resto", nargs=argparse.REMAINDER)
    p.set_defaults(f=cmd_fase0)

    args = parser.parse_args()
    try:
        sys.exit(args.f(args))
    except (defs.ErroDefinicoes, RuntimeError) as erro:
        print(f"Erro:\n{erro}", file=sys.stderr)
        sys.exit(1)
