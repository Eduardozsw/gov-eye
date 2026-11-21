"use client";

import Link from "next/link";
import { useState } from "react";

import type { ItemBusca } from "@/lib/tipos.ts";

// Seta para cima e para baixo percorrem os resultados; usado pela busca da página
// inicial e pela do topo.
export function useItemAtivo(total: number) {
  const [ativo, setAtivo] = useState(-1);
  function aoTeclar(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" && total) {
      e.preventDefault();
      setAtivo((a) => (a + 1) % total);
    } else if (e.key === "ArrowUp" && total) {
      e.preventDefault();
      setAtivo((a) => (a <= 0 ? total - 1 : a - 1));
    }
  }
  return { ativo, setAtivo, aoTeclar };
}

type Props = {
  id: string;
  resultados: ItemBusca[];
  ativo: number;
  aberto: boolean;
  className: string;
  aoEscolher?: () => void;
};

export function ListaResultados({ id, resultados, ativo, aberto, className, aoEscolher }: Props) {
  return (
    <ul className={className} id={id} role="listbox" hidden={!aberto} aria-label="Resultados">
      {resultados.map((r, n) => (
        <li key={`${r.href}-${r.titulo}`} id={`${id}-${n}`} role="option" aria-selected={n === ativo}>
          <Link href={r.href} tabIndex={-1} onClick={aoEscolher}>
            <span className="busca__tipo">{r.tipo}</span>
            <span className="busca__titulo">{r.titulo}</span>
            <span className="busca__resumo">{r.resumo}</span>
          </Link>
        </li>
      ))}
      {aberto && resultados.length === 0 && (
        <li className="busca__vazio" role="option" aria-selected={false} aria-disabled="true">
          Nada encontrado. Tente o nome de um imposto, programa ou ano.
        </li>
      )}
    </ul>
  );
}
