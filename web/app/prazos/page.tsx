import type { Metadata } from "next";
import Link from "next/link";

import { site } from "@/lib/dados.ts";
import type { Prazo } from "@/lib/tipos.ts";

export const metadata: Metadata = {
  title: "Prazos escritos nos atos",
  description:
    "Reduções de imposto que já nasceram com data para acabar: o que vence em breve e o que aconteceu quando cada prazo terminou.",
};

function CartaoPrazo({ p }: { p: Prazo }) {
  return (
    <li className={`prazo${p.futuro ? " prazo--futuro" : ""}`}>
      <p className="prazo__data">
        <time dateTime={p.data_iso}>{p.data}</time>
        <span>{p.futuro ? "vence" : "venceu"}</span>
      </p>
      <h3>
        <Link href={`/ato/${p.ato.id}/`}>{p.ato.titulo}</Link>
      </h3>
      {p.itens.map((i) => (
        <div key={i.evento_id} className="prazo__item">
          <p>
            {i.frase} <Link href={`/mudanca/${i.evento_id}/`}>Ver a mudança</Link>
          </p>
          {i.depois ? (
            <p className="prazo__depois">
              <strong>Depois:</strong> {i.depois.frase}{" "}
              <Link href={`/mudanca/${i.depois.id}/`}>Ver</Link>
            </p>
          ) : i.levantado_ate ? (
            <p className="prazo__depois">
              A série foi levantada até {i.levantado_ate}. O que aconteceu depois do prazo ainda não foi registrado.
            </p>
          ) : (
            p.futuro && (
              <p className="prazo__depois">
                Se nenhum novo ato for publicado até lá, essa regra deixa de valer nessa data.
              </p>
            )
          )}
        </div>
      ))}
    </li>
  );
}

export default function Prazos() {
  const futuros = site.prazos.filter((p) => p.futuro);
  const vencidos = site.prazos.filter((p) => !p.futuro);
  return (
    <div className="pagina">
      <h1>Prazos escritos nos atos</h1>
      <p className="lede">
        Muitas reduções de imposto já nascem com data para acabar. Quando o prazo termina, o valor volta sem que ninguém
        assine nada novo, e a mudança costuma ser atribuída a quem está no governo naquele dia. Aqui estão as datas que
        já constam nos próprios atos.
      </p>

      <section aria-labelledby="t-futuros">
        <h2 id="t-futuros">Próximos prazos</h2>
        {futuros.length ? (
          <ol className="prazos">
            {futuros.map((p) => (
              <CartaoPrazo key={p.ato.id} p={p} />
            ))}
          </ol>
        ) : (
          <p>Nenhum dos atos acompanhados tem prazo a vencer a partir de {site.gerado_em}.</p>
        )}
      </section>

      {vencidos.length > 0 && (
        <section aria-labelledby="t-vencidos">
          <h2 id="t-vencidos">Prazos que já venceram, e o que veio depois</h2>
          <ol className="prazos">
            {vencidos.map((p) => (
              <CartaoPrazo key={p.ato.id} p={p} />
            ))}
          </ol>
        </section>
      )}

      <p className="nota">
        O prazo mostrado é o que está escrito no ato. Quando um mesmo ato fixa prazos diferentes para produtos diferentes,
        vale o registrado na página de cada ato. <Link href="/metodologia/">Veja como verificamos</Link>.
      </p>
    </div>
  );
}
