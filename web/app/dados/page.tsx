import type { Metadata } from "next";

import { site } from "@/lib/dados.ts";

export const metadata: Metadata = { title: "Dados abertos" };

export default function Dados() {
  return (
    <div className="pagina">
      <h1>Dados abertos</h1>
      <p>
        Todos os dados do site podem ser baixados. Licença{" "}
        <a href={site.url_licenca} rel="license">
          {site.licenca}
        </a>
        : uso livre com crédito ao gov-eye e sem fins comerciais. Imprensa e agências de checagem podem pedir
        autorização gratuita para outros usos.
      </p>
      <div className="rolagem">
        <table>
          <thead>
            <tr>
              <th scope="col">Arquivo</th>
              <th scope="col">Tamanho</th>
              <th scope="col">SHA-256</th>
            </tr>
          </thead>
          <tbody>
            {site.manifesto.map((a) => (
              <tr key={a.nome}>
                <td>
                  <a href={`/dados/${a.nome}`} download>
                    {a.nome}
                  </a>
                </td>
                <td>{a.kb.toLocaleString("pt-BR")} KB</td>
                <td className="quebra">
                  <code className="hash">{a.sha256}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        Lista das impressões digitais: <a href="/dados/SHA256SUMS.txt">SHA256SUMS.txt</a>. Para conferir no computador:{" "}
        <code>sha256sum -c SHA256SUMS.txt</code>.
      </p>
    </div>
  );
}
