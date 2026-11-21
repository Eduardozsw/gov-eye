import type { Metadata } from "next";
import Link from "next/link";

import { site } from "@/lib/dados.ts";

export const metadata: Metadata = { title: "Como verificamos" };

export default function Metodologia() {
  const m = site.metodologia;
  return (
    <div className="pagina">
      <h1>Como verificamos</h1>

      <h2>Fontes</h2>
      <ul>
        <li>
          <strong>Atos oficiais</strong>: texto publicado no Diário Oficial da União (Imprensa Nacional). Cada mudança
          cita o trecho exato do ato.
        </li>
        <li>
          <strong>Orçamento</strong>: Sistema Integrado de Planejamento e Orçamento (SIOP), conferido com o Portal da
          Transparência. Se as duas fontes diferem em mais de {m.tolerancia} num ano, o valor daquele ano só é publicado
          depois que a diferença for explicada.
        </li>
        <li>
          <strong>Inflação</strong>: IPCA do IBGE. Cada ano é corrigido pelo índice de dezembro (ou do último mês
          disponível, no ano em andamento) até {m.ipca_referencia}.
        </li>
      </ul>

      <h2>Por que um valor mudou</h2>
      <p>Toda mudança recebe uma causa, tirada sempre da mesma lista, qualquer que seja o governo:</p>
      <dl className="causas">
        <dt>Alterado por novo ato</dt>
        <dd>Um decreto, medida provisória ou lei novo mudou o valor.</dd>
        <dt>Prazo previsto no ato original terminou</dt>
        <dd>
          O valor voltou sozinho, porque o ato que o reduziu já tinha data para acabar. A mudança é atribuída ao governo
          que assinou esse ato, não a quem estava no poder no dia.
        </dd>
        <dt>Prazo estendido</dt>
        <dd>Um ato novo prorrogou uma redução que ia acabar.</dd>
        <dt>Ato anterior revogado</dt>
        <dd>Um ato derrubou outro.</dd>
        <dt>Determinado pela Justiça</dt>
        <dd>Uma decisão judicial mudou o valor.</dd>
        <dt>Lei aprovada pelo Congresso</dt>
        <dd>A mudança foi decidida em lei, não em decreto.</dd>
        <dt>Regra de reajuste já existente</dt>
        <dd>Reajuste automático previsto em regra anterior.</dd>
      </dl>

      <h2>Orçamento: os estágios</h2>
      <ol>
        {m.estagios.map((e) => (
          <li key={e}>{e}</li>
        ))}
      </ol>
      <p>
        Autorizado não é gasto. O valor <strong>pago</strong> é o dinheiro que efetivamente saiu do caixa no ano.
        Pagamentos de dívidas de anos anteriores (restos a pagar) não entram.
      </p>

      <h2>Conferência</h2>
      <p>
        Os valores do orçamento vêm do SIOP e são comparados automaticamente com o Portal da Transparência. Quando as
        duas fontes divergem, o ano fica &ldquo;em conferência&rdquo; e o valor não é mostrado.
      </p>
      <p>
        As mudanças de alíquota são extraídas do texto do Diário Oficial de forma automatizada. Cada uma traz o trecho do
        ato que comprova o valor e o link para o documento oficial, para que qualquer pessoa possa conferir. A escolha
        das ações orçamentárias de cada tema segue o critério acima e está justificada ação por ação.
      </p>
      <p>
        Esses itens não passam por revisão humana individual antes de ir ao ar. Se encontrar um erro, use o link
        &ldquo;Reportar erro&rdquo; da página: a correção é feita e fica registrada.
      </p>

      <h2>Correções</h2>
      <p>
        Erros encontrados depois da publicação são corrigidos às claras: cada correção fica registrada com data, o que
        mudou e o motivo, na página do item e na lista de <Link href="/correcoes/">correções</Link>. Os termos técnicos
        estão explicados no <Link href="/glossario/">glossário</Link>.
      </p>

      <h2>Ações orçamentárias excluídas</h2>
      <p>Ações que parecem do tema, mas ficaram de fora:</p>
      <div className="rolagem">
        <table>
          <thead>
            <tr>
              <th scope="col">Tema</th>
              <th scope="col">Ação</th>
              <th scope="col">Motivo</th>
            </tr>
          </thead>
          <tbody>
            {m.excluidas.map((x) => (
              <tr key={`${x.tema}-${x.codigo}`}>
                <td>{x.tema}</td>
                <td>
                  <code>{x.codigo}</code>
                </td>
                <td className="quebra">{x.motivo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Limites</h2>
      <ul>
        <li>Só tributos e orçamento federais. ICMS e programas estaduais ficam fora.</li>
        <li>
          Programas financiados por fundos fora do orçamento (como o FGTS no Minha Casa Minha Vida) não aparecem nos
          números.
        </li>
        <li>Salários e custeio administrativo genérico dos ministérios não são atribuídos a nenhum tema.</li>
      </ul>
    </div>
  );
}
