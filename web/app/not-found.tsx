import Link from "next/link";

export default function NaoEncontrada() {
  return (
    <div className="pagina">
      <h1>Página não encontrada</h1>
      <p>
        <Link href="/">Voltar ao início</Link>
      </p>
    </div>
  );
}
