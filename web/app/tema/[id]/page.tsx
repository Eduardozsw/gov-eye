import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Grafico, Selo } from "@/components/Selo.tsx";
import { site, tema as acharTema } from "@/lib/dados.ts";
import type { Orcamento, Serie } from "@/lib/tipos.ts";

type Props = { params: Promise<{ id: string }> };

export const dynamicParams = false;

export function generateStaticParams() {
  return site.temas.map((t) => ({ id: t.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = acharTema((await params).id);
  return t ? { title: t.nome, description: t.descricao } : {};
}

function SecaoSerie({ s }: { s: Serie }) {
  return (
    <section className="serie" id={s.id} aria-labelledby={`t-${s.id}`}>
      <h2 id={`t-${s.id}`}>{s.nome}</h2>
      {s.descricao && <p>{s.descricao}</p>}
      {s.eventos.length === 0 ? (
        <p className="aviso">Série em levantamento: nenhum valor revisado ainda.</p>
      ) : (
        <>
          {s.valor_atual && (
            <p className="serie__atual">
              Valor hoje: <strong>{s.valor_atual}</strong> por litro
            </p>
          )}
          <figure>
            <Grafico svg={s.grafico} />
            <figcaption>
              Valor em {s.unidade}. As faixas de fundo mostram cada governo. Os pontos são as mudanças, listadas abaixo.
              A linha tracejada marca o fim de um prazo que já estava escrito no ato.
            </figcaption>
          </figure>
          {s.levantado_ate && (
            <p className="aviso">
              Série levantada até {s.levantado_ate}. Mudanças posteriores ainda não foram registradas.
            </p>
          )}
          {s.interrompida && (
            <p className="aviso">
              A série continua depois do último item mostrado, mas os eventos seguintes ainda estão em revisão.
            </p>
          )}
          <ol className="linha-tempo">
            {s.eventos.map((e) => (
              <li key={e.id} id={e.id} className={`evento${e.expiracao ? " expiracao" : ""}`}>
                <p className="quando">
                  <time dateTime={e.data_iso}>{e.data}</time>
                  {e.governo && <span className="governo">governo {e.governo}</span>}
                  <span className="causa">{e.causa}</span> <Selo pendente={e.pendente} />
                </p>
                <p>{e.frase}</p>
                <details>
                  <summary>Trecho do ato</summary>
                  <blockquote>{e.trecho}</blockquote>
                  <p>
                    <Link href={`/ato/${e.ato.id}/`}>Ver {e.ato.titulo}</Link>
                    {e.origem && (
                      <>
                        {" · "}
                        <Link href={`/ato/${e.origem.id}/`}>Ver o ato que fixou o prazo ({e.origem.titulo})</Link>
                      </>
                    )}
                  </p>
                  {e.nota && <p className="nota">{e.nota}</p>}
                </details>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}

function SecaoOrcamento({ o }: { o: Orcamento }) {
  return (
    <>
      {!o.liberado ? (
        <p className="aviso">
          O mapeamento das ações orçamentárias deste tema ainda está em revisão. Os números serão publicados depois que
          cada ação incluída for conferida.
        </p>
      ) : (
        <section aria-labelledby="t-orc">
          <h2 id="t-orc">Orçamento federal por ano</h2>
          <p>
            Barra clara: valor <strong>autorizado</strong> (lei orçamentária mais créditos e cortes). Barra escura: valor{" "}
            <strong>pago</strong>. Ano com * ainda está em andamento.
          </p>
          <div className="alternador">
            <input type="radio" name="valores" id="v-corrigido" defaultChecked />
            <label htmlFor="v-corrigido">Corrigido pela inflação</label>
            <input type="radio" name="valores" id="v-nominal" />
            <label htmlFor="v-nominal">Valores da época</label>
            <figure className="g-corrigido">
              <Grafico svg={o.grafico_corrigido} />
              <figcaption>Valores corrigidos pelo IPCA até {o.ipca_referencia}.</figcaption>
            </figure>
            <figure className="g-nominal">
              <Grafico svg={o.grafico_nominal} />
              <figcaption>Valores em reais de cada ano, sem correção.</figcaption>
            </figure>
          </div>

          <ul className="frases">
            {o.frases.map((f) => (
              <li key={f.ano}>
                {f.texto} {f.divergente && <span className="selo">fontes divergem</span>}
              </li>
            ))}
          </ul>

          <div className="rolagem">
            <table>
              <caption>Orçamento por estágio, valores da época</caption>
              <thead>
                <tr>
                  <th scope="col">Ano</th>
                  {o.estagios.map((e) => (
                    <th scope="col" key={e}>
                      {e}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {o.tabela.map((l) => (
                  <tr key={l.ano}>
                    <th scope="row">{l.ano}</th>
                    {l.valores.map((v, n) => (
                      <td key={n}>{v}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section id="acoes" aria-labelledby="t-acoes">
        <h2 id="t-acoes">O que entra nesta conta</h2>
        <p>
          As ações orçamentárias abaixo foram incluídas porque o nome oficial delas se refere a este tema. Os códigos
          mudam de um plano plurianual para outro, por isso a lista tem ações antigas e novas.
        </p>
        <ul className="acoes">
          {o.acoes.map((a) => (
            <li key={`${a.codigo}-${a.subfuncao ?? ""}`}>
              <code>{a.codigo}</code>
              {a.subfuncao && ` (só subfunção ${a.subfuncao})`}: {a.justificativa} <Selo pendente={a.pendente} />
            </li>
          ))}
        </ul>
        {o.excluidas.length > 0 && (
          <>
            <h3>O que ficou de fora, e por quê</h3>
            <ul className="acoes">
              {o.excluidas.map((x) => (
                <li key={x.codigo}>
                  <code>{x.codigo}</code>: {x.motivo}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      {o.detalhe && o.detalhe.linhas.length > 0 && (
        <section aria-labelledby="t-detalhe">
          <h2 id="t-detalhe">Valor pago por ação</h2>
          <div className="rolagem">
            <table>
              <caption>Pago por ação e ano, valores da época</caption>
              <thead>
                <tr>
                  <th scope="col">Ação</th>
                  {o.detalhe.anos.map((a) => (
                    <th scope="col" key={a}>
                      {a}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {o.detalhe.linhas.map((g) => (
                  <tr key={g.acao}>
                    <th scope="row" className="quebra">
                      <code>{g.acao}</code> {g.nome}
                    </th>
                    {g.valores.map((v, n) => (
                      <td key={n}>{v}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {o.divergencias.length > 0 && (
        <section aria-labelledby="t-div">
          <h2 id="t-div">Divergências entre SIOP e Portal da Transparência (só na prévia)</h2>
          <div className="rolagem">
            <table>
              <thead>
                <tr>
                  <th scope="col">Ano</th>
                  <th scope="col">Ação/subfunção</th>
                  <th scope="col">Estágio</th>
                  <th scope="col">SIOP</th>
                  <th scope="col">Portal</th>
                </tr>
              </thead>
              <tbody>
                {o.divergencias.map((d) => (
                  <tr key={`${d.ano}-${d.chave}-${d.estagio}`}>
                    <td>{d.ano}</td>
                    <td>
                      <code>{d.chave}</code>
                    </td>
                    <td>{d.estagio}</td>
                    <td>{d.siop}</td>
                    <td>{d.portal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}

export default async function PaginaTema({ params }: Props) {
  const t = acharTema((await params).id);
  if (!t) notFound();
  return (
    <>
      <header className="cabecalho-tema">
        <div>
          <p className="migalha">
            <Link href="/#temas">Temas</Link> / {t.categoria === "tributo" ? "Impostos" : "Orçamento federal"}
          </p>
          <h1>{t.nome}</h1>
          <p className="lede">{t.descricao}</p>
        </div>
      </header>
      <div className="pagina">
        {t.series?.map((s) => <SecaoSerie key={s.id} s={s} />)}
        {t.orcamento && <SecaoOrcamento o={t.orcamento} />}
      </div>
    </>
  );
}
