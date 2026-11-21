import type { Metadata } from "next";

import { site } from "@/lib/dados.ts";

export const metadata: Metadata = {
  title: "Glossário",
  description: "Termos de orçamento, impostos e atos oficiais explicados em linguagem simples.",
};

export default function Glossario() {
  return (
    <div className="pagina">
      <h1>Glossário</h1>
      <p className="lede">Os termos técnicos que aparecem no site, em linguagem simples.</p>
      <dl className="glossario">
        {site.glossario.map((t) => (
          <div key={t.id} id={t.id}>
            <dt>{t.termo}</dt>
            <dd>{t.definicao}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
