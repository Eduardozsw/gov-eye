import Link from "next/link";

import { Explorador } from "@/components/Explorador.tsx";
import { site } from "@/lib/dados.ts";
import type { Tema } from "@/lib/tipos.ts";

function ResumoTema({ tema }: { tema: Tema }) {
  if (tema.series) {
    return (
      <ul className="valores">
        {tema.series.map((s) => (
          <li key={s.id}>
            <span>{s.nome}</span>
            {s.valor_atual ? (
              <strong>{s.valor_atual}/L</strong>
            ) : s.eventos.length ? (
              <em>até {s.levantado_ate}</em>
            ) : (
              <em>em levantamento</em>
            )}
          </li>
        ))}
      </ul>
    );
  }
  const o = tema.orcamento;
  if (o?.destaque) {
    return (
      <>
        <div className="cartao__numero">{o.destaque.pago}</div>
        <p>pagos em {o.destaque.ano}, em valores da época</p>
        {o.mini && (
          <figure className="cartao__mini">
            <div dangerouslySetInnerHTML={{ __html: o.mini }} />
            <figcaption>Pago por ano, {o.anos_mini}, corrigido pela inflação</figcaption>
          </figure>
        )}
      </>
    );
  }
  return <p>Valores do orçamento ainda não coletados.</p>;
}

export default function Inicio() {
  const proximo = site.prazos.find((p) => p.futuro);
  return (
    <>
      <section className="heroi" aria-labelledby="titulo-inicio">
        <Explorador sugestoes={site.sugestoes} indice={site.busca}>
          <p className="heroi__sobretitulo">Dados oficiais do governo federal</p>
          <h1 id="titulo-inicio">
            Quem mudou o quê, <em>e quando</em>
          </h1>
          <p className="heroi__lede">
            Imposto zerado, imposto de volta, programa ampliado, programa cortado. Cada mudança aparece ligada ao ato
            oficial que a causou, com data, quem assinou e em qual governo.
          </p>
        </Explorador>
        <a className="heroi__rolar" href="#temas">
          Ver os temas ↓
        </a>
      </section>

      <div className="pagina pagina--ampla">
        <section id="temas" aria-labelledby="t-temas">
          <div className="secao-titulo">
            <h2 id="t-temas">Temas</h2>
          </div>
          <ul className="cartoes">
            {site.temas.map((t) => (
              <li key={t.id} className="cartao">
                <span className="cartao__rotulo">{t.categoria === "tributo" ? "Impostos" : "Orçamento federal"}</span>
                <h3>
                  <Link href={`/tema/${t.id}/`}>{t.nome}</Link>
                </h3>
                <ResumoTema tema={t} />
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="t-prazos" className="chamada-prazos">
          <h2 id="t-prazos">Prazos escritos nos atos</h2>
          {proximo ? (
            <p>
              Próximo prazo: <strong>{proximo.data}</strong> ({proximo.ato.titulo}).
            </p>
          ) : (
            <p>Reduções de imposto que já nasceram com data para acabar, e o que aconteceu quando cada uma venceu.</p>
          )}
          <p>
            <Link href="/prazos/">Ver todos os prazos</Link>
          </p>
        </section>

        <section aria-labelledby="t-como">
          <h2 id="t-como">Como cada número chega aqui</h2>
          <ol className="passos">
            <li>
              <strong>Ato oficial</strong>
              <span>O texto vem do Diário Oficial da União e o orçamento, do SIOP e do Portal da Transparência.</span>
            </li>
            <li>
              <strong>Conferência automática</strong>
              <span>Cada valor traz o trecho do ato que o comprova, e o orçamento é comparado entre duas fontes oficiais.</span>
            </li>
            <li>
              <strong>Mesma regra para todos</strong>
              <span>A frase que explica cada mudança sai de um modelo fixo, qualquer que seja o governo.</span>
            </li>
          </ol>
          <p>
            Às vezes um imposto volta a subir sem que ninguém assine nada: o prazo da redução já estava escrito no ato
            do governo anterior. Isso também aparece. <Link href="/metodologia/">Veja como verificamos</Link>.
          </p>
        </section>

        <section aria-labelledby="t-mandatos">
          <h2 id="t-mandatos">Governos cobertos</h2>
          <ul className="mandatos">
            {site.mandatos.map((m) => (
              <li key={m.id}>
                <strong>
                  {m.presidente} ({m.partido} na posse)
                </strong>
                <span>
                  {m.inicio} a {m.fim}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
