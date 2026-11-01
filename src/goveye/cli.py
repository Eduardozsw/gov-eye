"""Linha de comando do gov-eye: `uv run goveye <comando>`."""

import argparse
import sys
from collections import Counter
from datetime import date

from . import curadoria as cur
from .config import ANO_FINAL, ANO_INICIAL
from .modelo import status_revisao


def _mes(texto: str) -> tuple[int, int]:
    ano, mes = texto.split("-")
    return int(ano), int(mes)


def _anos(texto: str) -> range:
    inicio, _, fim = texto.partition("-")
    return range(int(inicio), int(fim or inicio) + 1)


def cmd_validar(_: argparse.Namespace) -> int:
    c = cur.carregar()
    status = Counter()
    for nome, itens in (("atos", c.atos.values()), ("eventos", c.eventos), ("ações", c.acoes)):
        contagem = Counter(status_revisao(i.revisoes).value for i in itens)
        status.update(contagem)
        resumo = ", ".join(f"{n} {s}" for s, n in sorted(contagem.items())) or "nenhum"
        print(f"{nome}: {resumo}")
    print(f"ações excluídas: {len(c.excluidas)}")
    print("Curadoria válida.")
    return 0


def cmd_pendentes(_: argparse.Namespace) -> int:
    c = cur.carregar()
    for chave, obj in cur.revisaveis(c).items():
        s = status_revisao(obj.revisoes)
        if s.value in ("pendente", "primeira passagem"):
            print(f"{chave[0]:7} {chave[1]:45} {s.value}")
    return 0


def cmd_revisar(args: argparse.Namespace) -> int:
    dia = date.fromisoformat(args.data) if args.data else date.today()
    cur.registrar_revisao(args.objeto, args.id, args.revisor, dia)
    obj = cur.revisaveis(cur.carregar())[(args.objeto, args.id)]
    print(f"Revisão registrada. Status de {args.objeto} {args.id}: {status_revisao(obj.revisoes).value}")
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


def cmd_carregar(_: argparse.Namespace) -> int:
    from .pipeline import carregar

    print(f"Banco gerado em {carregar()}")
    return 0


def cmd_site(args: argparse.Namespace) -> int:
    from .site.gerar import gerar

    print(f"Site ({args.modo}) gerado em {gerar(args.modo)}")
    return 0


def cmd_fase0(args: argparse.Namespace) -> int:
    from . import fase0

    sys.argv = ["fase0", *args.resto]
    fase0.main()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="goveye", description="Pipeline do gov-eye")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("validar", help="valida a curadoria e mostra o status de revisão").set_defaults(f=cmd_validar)
    sub.add_parser("pendentes", help="lista os itens que ainda precisam de revisão").set_defaults(f=cmd_pendentes)

    p = sub.add_parser("revisar", help="registra uma revisão do curador em data/curadoria/revisoes.yaml")
    p.add_argument("objeto", choices=cur.OBJETOS_REVISAVEIS)
    p.add_argument("id", help="id do ato ou evento; para ação, tema:codigo (ex.: mulheres:21GI)")
    p.add_argument("--revisor", required=True, help="nome de quem revisou")
    p.add_argument("--data", help="AAAA-MM-DD (padrão: hoje)")
    p.set_defaults(f=cmd_revisar)

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

    sub.add_parser("carregar", help="monta o banco SQLite a partir da curadoria e das coletas").set_defaults(
        f=cmd_carregar
    )

    p = sub.add_parser("site", help="gera o site estático em site/")
    p.add_argument("--modo", choices=("previa", "publicacao"), default="previa")
    p.set_defaults(f=cmd_site)

    p = sub.add_parser("fase0", help="verifica as fontes oficiais")
    p.add_argument("resto", nargs=argparse.REMAINDER)
    p.set_defaults(f=cmd_fase0)

    args = parser.parse_args()
    try:
        sys.exit(args.f(args))
    except (cur.ErroCuradoria, RuntimeError) as erro:
        print(f"Erro:\n{erro}", file=sys.stderr)
        sys.exit(1)
