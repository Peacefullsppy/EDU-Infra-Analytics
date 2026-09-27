import { useEffect, useState } from "react";
import MetricCard from "../../components/MetricCard/MetricCard";
import { getIndicadores } from "../../services/api";

function Indicators() {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    getIndicadores().then(setDados).catch((error) => setErro(error.message));
  }, []);

  if (erro) return <div className="error-box">{erro}</div>;
  if (!dados) return <div className="loading">Carregando indicadores...</div>;

  return (
    <>
      <header className="page-header"><div><h1>Indicadores</h1><p>Resumo dos indicadores atuais da infraestrutura</p></div></header>
      <section className="metrics-grid two-metrics">
        <MetricCard title="IIE médio" value={`${dados.iie_medio} / 100`} tone="blue" icon="★" />
        <MetricCard title="Disponibilidade" value={`${dados.disponibilidade_percentual}%`} tone="green" icon="✓" />
      </section>
      <article className="panel">
        <h2>IIE por laboratório</h2>
        <div className="indicator-list">
          {dados.laboratorios.map((lab) => (
            <div className="indicator-row" key={lab.id}>
              <strong>{lab.nome}</strong>
              <div className="indicator-track"><span style={{ width: `${lab.iie || 0}%` }} /></div>
              <b>{lab.iie ?? "-"}</b>
            </div>
          ))}
        </div>
      </article>
    </>
  );
}

export default Indicators;
