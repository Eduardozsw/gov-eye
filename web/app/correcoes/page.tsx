import type { Metadata } from "next";
import Link from "next/link";

import { contato, site } from "@/lib/dados.ts";

export const metadata: Metadata = {
  title: "Correções",
  description: "Tudo o que foi corrigido no gov-eye depois de publicado, com data e motivo.",
};

export default function Correcoes() {
  const email = contato();
  return (
    <div className="pagina">
      <h1>Correções</h1>
      <p className="lede">
        Quando um dado publicado está errado, ele é corrigido às claras: a correção fica registrada aqui e na página do
        item, com data e motivo. Nada é apagado em silêncio.
      </p>
      {site.correcoes.length ? (
        <ol className="lista-correcoes">
          {site.correcoes.map((c, n) => (
            <li key={n}>
              <p className="lista-correcoes__quando">
                <strong>{c.data}</strong> · <Link href={c.href}>{c.titulo}</Link>
              </p>
              <p>
                {c.o_que_mudou}. Motivo: {c.motivo}.
              </p>
            </li>
          ))}
        </ol>
      ) : (
        <p>Nenhuma correção registrada até {site.gerado_em}.</p>
      )}
      <h2>Como avisar um erro</h2>
      <p>
        {email ? (
          <>
            Escreva para <a href={`mailto:${email}`}>{email}</a> com o link da página e, se tiver, o link do documento
            oficial com a informação correta.
          </>
        ) : (
          <>
            Veja o contato na página <Link href="/quem-faz/">Quem faz</Link>.
          </>
        )}{" "}
        Os dados de todas as correções também estão em <Link href="/dados/">Dados abertos</Link> (arquivo correcoes.csv).
      </p>
    </div>
  );
}
