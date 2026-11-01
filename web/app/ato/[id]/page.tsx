import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Selo } from "@/components/Selo.tsx";
import { ato as acharAto, site } from "@/lib/dados.ts";

type Props = { params: Promise<{ id: string }> };

export const dynamicParams = false;

export function generateStaticParams() {
  // A exportação estática exige ao menos um parâmetro; sem atos, gera só a página "não encontrado".
  return site.atos.length ? site.atos.map((a) => ({ id: a.id })) : [{ id: "nenhum" }];
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const a = acharAto((await params).id);
  return a ? { title: a.titulo, description: a.ementa } : {};
}

export default async function PaginaAto({ params }: Props) {
  const a = acharAto((await params).id);
  if (!a) notFound();
  return (
    <div className="pagina">
      <p className="migalha">Ato oficial · {a.tipo}</p>
      <h1>
        {a.titulo} <Selo pendente={a.pendente} />
      </h1>
      <p className="lede">{a.ementa}</p>
      <dl className="ficha">
        <dt>Assinatura</dt>
        <dd>{a.assinatura}</dd>
        <dt>Publicação no Diário Oficial</dt>
        <dd>{a.publicacao}</dd>
        {a.governo && (
          <>
            <dt>Governo</dt>
            <dd>{a.governo}</dd>
          </>
        )}
        {a.signatarios.length > 0 && (
          <>
            <dt>Quem assinou</dt>
            <dd>
              <ul>
                {a.signatarios.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </dd>
          </>
        )}
        {a.vigencia_fim && (
          <>
            <dt>Prazo previsto no próprio ato</dt>
            <dd>até {a.vigencia_fim}</dd>
          </>
        )}
        <dt>Fonte oficial</dt>
        <dd>
          <a href={a.url_oficial} rel="noopener">
            {a.url_oficial}
          </a>
        </dd>
        {a.sha256 && (
          <>
            <dt>SHA-256 do texto coletado</dt>
            <dd>
              <code className="hash">{a.sha256}</code>
            </dd>
          </>
        )}
      </dl>
      {a.eventos.length > 0 && (
        <>
          <h2>Mudanças ligadas a este ato</h2>
          <ul>
            {a.eventos.map((e) => (
              <li key={e.id}>
                {e.frase} <Selo pendente={e.pendente} />{" "}
                <Link href={`/tema/${e.tema_id}/#${e.id}`}>Ver na linha do tempo</Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
