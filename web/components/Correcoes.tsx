import type { Correcao } from "@/lib/tipos.ts";

// Histórico público de correções de um item (princípio P7). A lista vazia também é
// informação: diz ao leitor que nada foi mudado depois de publicado.
export function Correcoes({ lista }: { lista: Correcao[] }) {
  return (
    <section aria-labelledby="t-correcoes" className="correcoes">
      <h2 id="t-correcoes">Histórico de correções</h2>
      {lista.length ? (
        <ol>
          {lista.map((c, n) => (
            <li key={n}>
              <strong>{c.data}</strong>: {c.o_que_mudou}. <span>Motivo: {c.motivo}.</span>
            </li>
          ))}
        </ol>
      ) : (
        <p>Nenhuma correção desde a publicação.</p>
      )}
    </section>
  );
}
