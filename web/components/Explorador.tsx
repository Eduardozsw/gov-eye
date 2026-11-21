"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect, useId, useMemo, useRef, useState } from "react";

import { buscar, preparar } from "@/lib/busca.ts";
import type { ItemBusca } from "@/lib/tipos.ts";

import { Olho } from "./Olho.tsx";
import { ListaResultados, useItemAtivo } from "./Resultados.tsx";

function reduzMovimento(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Escreve e apaga as frases de exemplo, uma letra por vez. Sem JavaScript (ou com
// movimento reduzido), fica parada na primeira frase.
function useDigitacao(frases: string[], ativo: boolean) {
  const [texto, setTexto] = useState(frases[0] ?? "");
  const estado = useRef({ i: 0, pos: (frases[0] ?? "").length, apagando: false });

  useEffect(() => {
    if (!ativo || frases.length === 0 || reduzMovimento()) return;
    let timer: number;
    const passo = () => {
      const e = estado.current;
      let espera: number;
      if (!e.apagando && e.pos < frases[e.i].length) {
        e.pos += 1;
        espera = 40 + Math.random() * 70;
      } else if (!e.apagando) {
        e.apagando = true;
        espera = 1900;
      } else if (e.pos > 0) {
        e.pos -= 1;
        espera = 22;
      } else {
        e.apagando = false;
        e.i = (e.i + 1) % frases.length;
        espera = 450;
      }
      setTexto(frases[e.i].slice(0, e.pos));
      timer = window.setTimeout(passo, espera);
    };
    timer = window.setTimeout(passo, 1400);
    return () => window.clearTimeout(timer);
  }, [ativo, frases]);

  return { texto, fraseAtual: () => frases[estado.current.i] ?? "" };
}

type Props = { sugestoes: string[]; indice: ItemBusca[]; children: ReactNode };

export function Explorador({ sugestoes, indice, children }: Props) {
  const router = useRouter();
  const id = useId();
  const campo = useRef<HTMLInputElement>(null);
  const [valor, setValor] = useState("");
  const [foco, setFoco] = useState(false);

  const preparado = useMemo(() => preparar(indice), [indice]);
  const resultados = useMemo(() => buscar(preparado, valor), [preparado, valor]);
  const { ativo, setAtivo, aoTeclar: navegar } = useItemAtivo(resultados.length);
  const { texto, fraseAtual } = useDigitacao(sugestoes, valor === "");
  const aberto = foco && valor.trim() !== "";
  const listaId = `${id}-resultados`;

  // Link de busca compartilhável: /?q=gasolina abre a página com os resultados.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) {
      setValor(q);
      campo.current?.focus();
    }
  }, []);

  function escolher(consulta: string) {
    setValor(consulta);
    setAtivo(-1);
    campo.current?.focus();
  }

  function aoTeclar(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      setValor("");
      setAtivo(-1);
    } else {
      navegar(e);
    }
  }

  function aoEnviar(e: React.FormEvent) {
    e.preventDefault();
    if (valor.trim() === "") {
      escolher(fraseAtual());
      return;
    }
    const alvo = resultados[ativo >= 0 ? ativo : 0];
    if (alvo) router.push(alvo.href);
  }

  return (
    <div className="heroi__conteudo">
      <Olho atento={foco || valor !== ""} />
      {children}
      <form
        className="busca"
        role="search"
        onSubmit={aoEnviar}
        onFocus={() => setFoco(true)}
        onBlur={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFoco(false);
        }}
      >
        <div className="busca__caixa">
          <div className="busca__campo">
            <svg className="busca__icone" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" strokeLinecap="round" />
            </svg>
            <div className="busca__area">
              <label htmlFor={`${id}-campo`} className="pular">
                Pesquise um imposto, programa, ato ou ano
              </label>
              <input
                ref={campo}
                id={`${id}-campo`}
                type="search"
                autoComplete="off"
                spellCheck={false}
                value={valor}
                onChange={(e) => {
                  setValor(e.target.value);
                  setAtivo(-1);
                }}
                onKeyDown={aoTeclar}
                role="combobox"
                aria-expanded={aberto}
                aria-controls={listaId}
                aria-autocomplete="list"
                aria-activedescendant={ativo >= 0 ? `${listaId}-${ativo}` : undefined}
              />
              {valor === "" && (
                <span className="busca__fantasma" aria-hidden="true">
                  <span className="busca__fantasma-texto">{texto}</span>
                  <span className="busca__cursor" />
                </span>
              )}
            </div>
            <button className="busca__botao" type="submit">
              Buscar
            </button>
          </div>

          <ListaResultados
            id={listaId}
            className="busca__resultados"
            resultados={resultados}
            ativo={ativo}
            aberto={aberto}
          />
        </div>

        <ul className="busca__sugestoes" aria-label="Exemplos de busca">
          {sugestoes.slice(0, 4).map((s) => (
            <li key={s}>
              <button type="button" onClick={() => escolher(s)}>
                {s}
              </button>
            </li>
          ))}
        </ul>
      </form>
    </div>
  );
}
