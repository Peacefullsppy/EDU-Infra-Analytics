import { useEffect, useState } from "react";
import MetricCard from "../../components/MetricCard/MetricCard";
import { getRelatorioResumo } from "../../services/api";

function Reports() {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    getRelatorioResumo().then(setDados).catch((error) => setErro(error.message));
  }, []);

  if (erro) return <div className="error-box">{erro}</div>;
  if (!dados) return <div className="loading">Carregando relatório...</div>;

  return (
    <>
      <header className="page-header"><div><h1>Relatórios</h1><p>Resumo operacional da infraestrutura cadastrada</p></div></header>
      <section className="metrics-grid">
        <MetricCard title="Laboratórios" value={dados.laboratorios} tone="blue" icon="▦" />
        <MetricCard title="Computadores" value={dados.computadores.total} tone="blue" icon="▣" />
        <MetricCard title="Online" value={dados.computadores.online} tone="green" icon="✓" />
        <MetricCard title="Em atenção" value={dados.computadores.atencao} tone="orange" icon="!" />
      </section>
      <article className="panel report-note">
        <h2>Resumo</h2>
        <p>{dados.observacao}</p>
        <p>Esta etapa mantém o relatório simples e preparado para evolução posterior para exportação em PDF/CSV e histórico de métricas.</p>
      </article>
    </>
  );
}

export default Reports;
