import type { ReactNode } from "react";

import { termo } from "@/lib/dados.ts";

import { TermoBalao } from "./TermoBalao.tsx";

// Termo técnico com explicação do glossário. Sem o termo no glossário, mostra só o texto.
export function Termo({ id, children }: { id: string; children: ReactNode }) {
  const t = termo(id);
  if (!t) return <>{children}</>;
  return (
    <TermoBalao id={t.id} termo={t.termo} definicao={t.definicao}>
      {children}
    </TermoBalao>
  );
}
