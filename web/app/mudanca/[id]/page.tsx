import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Compartilhar } from "@/components/Compartilhar.tsx";
import { Correcoes } from "@/components/Correcoes.tsx";
import { ReportarErro } from "@/components/ReportarErro.tsx";
import { Termo } from "@/components/Termo.tsx";
import { ato as acharAto, contato, mudanca, mudancas } from "@/lib/dados.ts";

// Página própria de cada mudança: é o link que circula no WhatsApp, com o card gerado
// em card.png/route.tsx.

const CARD_ALT = "Card da mudança: valor antes e depois, causa e ato oficial";

type Props = { params: Promise<{ id: string }> };

export const dynamicParams = false;

export function generateStaticParams() {
  // A exportação estática exige ao menos um parâmetro; sem mudanças, gera só a página "não encontrado".
  const todas = mudancas();
  return todas.length ? todas.map((m) => ({ id: m.evento.id })) : [{ id: "nenhuma" }];
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const m = mudanca((await params).id);
  if (!m) return {};
  const titulo = `${m.serie.nome}: ${m.evento.valor_antes ? `${m.evento.valor_antes} → ` : ""}${m.evento.valor} por litro`;
  return {
    title: titulo,
    description: m.evento.frase,
    openGraph: {
      title: titulo,
      description: m.evento.frase,
      type: "article",
      images: [{ url: `/mudanca/${m.evento.id}/card.png`, width: 1200, height: 630, alt: CARD_ALT }],
    },
    twitter: { card: "summary_large_image" },
  };
}

export default async function PaginaMudanca({ params }: Props) {
  const m = mudanca((await params).id);
  if (!m) notFound();
  const { tema, serie, evento: e } = m;
  const ato = acharAto(e.ato.id);
  const texto = `${serie.nome}, ${e.data}: ${e.valor_antes ? `${e.valor_antes} → ` : ""}${e.valor} por litro. Causa: ${e.causa}. Fonte: ${e.ato.titulo}.`;

  return (
    <div className="pagina">
      <p className="migalha">
        <Link href="/#temas">Temas</Link> / <Link href={`/tema/${tema.id}/`}>{tema.nome}</Link> /{" "}
        <Link href={`/tema/${tema.id}/#${serie.id}`}>{serie.nome}</Link>
      </p>
      <h1>{serie.nome}</h1>

      <p className="mudanca__valores" aria-label={e.valor_antes ? `De ${e.valor_antes} para ${e.valor} por litro` : undefined}>
        {e.valor_antes && (
          <>
            <span className="mudanca__antes">{e.valor_antes}</span>
            <span className="mudanca__seta" aria-hidden="true">
              →
            </span>
          </>
        )}
        <strong>{e.valor}</strong>
        <small>por litro</small>
      </p>

      <p className="quando">
        <time dateTime={e.data_iso}>{e.data}</time>
        {e.governo && <span className="governo">governo {e.governo}</span>}
        <span className={`causa${e.expiracao ? " causa--expiracao" : ""}`}>{e.causa}</span>{" "}
      </p>

      <p className="lede">{e.frase}</p>

      <Compartilhar texto={texto} caminho={`/mudanca/${e.id}/`} />

      <h2>O que diz o ato</h2>
      <blockquote>{e.trecho}</blockquote>
      {e.nota && <p className="nota">{e.nota}</p>}

      <dl className="ficha">
        <dt>Ato que causou a mudança</dt>
        <dd>
          <Link href={`/ato/${e.ato.id}/`}>{e.ato.titulo}</Link>
        </dd>
        {e.origem && (
          <>
            <dt>Ato que já previa o prazo</dt>
            <dd>
              <Link href={`/ato/${e.origem.id}/`}>{e.origem.titulo}</Link>
            </dd>
          </>
        )}
        {ato && (
          <>
            <dt>Documento oficial</dt>
            <dd>
              <a href={ato.url_oficial} rel="noopener">
                Abrir no Diário Oficial da União
              </a>{" "}
              (<Termo id="diario-oficial">o que é</Termo>)
            </dd>
          </>
        )}
      </dl>

      <p>
        <Link href={`/tema/${tema.id}/#${e.id}`}>Ver esta mudança na linha do tempo completa</Link>
      </p>

      <Correcoes lista={e.correcoes} />
      <ReportarErro contato={contato()} assunto={`${serie.nome}, ${e.data}`} caminho={`/mudanca/${e.id}/`} />
    </div>
  );
}
