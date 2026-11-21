"use client";

import Link from "next/link";
import { type ReactNode, useEffect, useId, useState } from "react";

// Sem JavaScript, ou em navegador sem a API de popover, o termo é um link para o glossário.
// Com ela, tocar no termo abre um balão com a definição, sem sair da página.
export function TermoBalao({ id, termo, definicao, children }: { id: string; termo: string; definicao: string; children: ReactNode }) {
  const balao = useId();
  const [comBalao, setComBalao] = useState(false);

  useEffect(() => {
    setComBalao(Object.prototype.hasOwnProperty.call(HTMLElement.prototype, "popover"));
  }, []);

  if (!comBalao) {
    return (
      <Link className="termo" href={`/glossario/#${id}`}>
        {children}
      </Link>
    );
  }
  return (
    <>
      <button type="button" className="termo" popoverTarget={balao} aria-haspopup="dialog">
        {children}
      </button>
      <span popover="auto" id={balao} className="termo__balao" role="dialog" aria-label={termo}>
        <strong>{termo}</strong>
        <span>{definicao}</span>
        <span className="termo__acoes">
          <Link href={`/glossario/#${id}`}>Ver no glossário</Link>
          <button type="button" popoverTarget={balao} popoverTargetAction="hide">
            Fechar
          </button>
        </span>
      </span>
    </>
  );
}
