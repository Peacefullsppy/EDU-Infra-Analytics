import { useEffect, useState } from "react";
import MetricCard from "../../components/MetricCard/MetricCard";
import StatusBadge from "../../components/StatusBadge/StatusBadge";
import { getAlertas, getDashboard, getLaboratorios } from "../../services/api";

function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [laboratorios, setLaboratorios] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [erro, setErro] = useState("");

  useEffect(() => {
    Promise.all([getDashboard(), getLaboratorios(), getAlertas()])
      .then(([dashboardData, labsData, alertasData]) => {
        setDashboard(dashboardData);
        setLaboratorios(labsData);
        setAlertas(alertasData.slice(0, 4));
      })
      .catch((error) => setErro(error.message));
  }, []);

  if (erro) return <div className="error-box">{erro}</div>;
  if (!dashboard) return <div className="loading">Carregando dashboard...</div>;

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Visão geral da infraestrutura tecnológica</p>
        </div>
        <div className="date-pill">▣ 20 de agosto de 2026⌄</div>
      </header>

      <section className="metrics-grid">
        <MetricCard title="IIE Geral" value={`${dashboard.iie_geral} / 100`} subtitle="ADEQUADO" tone="green" icon="★" />
        <MetricCard title="Computadores Online" value={dashboard.computadores.online} subtitle={`de ${dashboard.computadores.total} equipamentos`} tone="blue" icon="▣" />
        <MetricCard title="Computadores Offline" value={dashboard.computadores.offline} subtitle={`${Math.round((dashboard.computadores.offline / dashboard.computadores.total) * 100)}% da infraestrutura`} tone="red" icon="×" />
        <MetricCard title="Alertas" value={dashboard.alertas} subtitle="equipamentos em atenção" tone="orange" icon="!" />
      </section>

      <section className="content-grid">
        <article className="panel panel-large">
          <h2>Situação dos Laboratórios</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Laboratório</th><th>Equipamentos</th><th>Online</th><th>Problemas</th><th>IIE</th><th>Status</th></tr></thead>
              <tbody>
                {laboratorios.map((lab) => {
                  const status = lab.iie >= 85 ? "online" : lab.iie >= 70 ? "atencao" : "critico";
                  return (
                    <tr key={lab.id}>
                      <td><strong>{lab.nome}</strong><small className="table-subtitle">{lab.localizacao}</small></td>
                      <td>{lab.equipamentos}</td>
                      <td className="success-text">{lab.online}</td>
                      <td className={lab.problemas > 0 ? "warning-text" : ""}>{lab.problemas}</td>
                      <td className={lab.iie >= 85 ? "success-text" : lab.iie >= 70 ? "warning-text" : "danger-text"}>{lab.iie ?? "-"}</td>
                      <td><StatusBadge status={status} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel">
          <h2>Alertas recentes</h2>
          <div className="alert-list">
            {alertas.map((alerta, index) => (
              <div className="alert-item" key={`${alerta.computador}-${index}`}>
                <div className={`alert-symbol alert-${alerta.tipo}`}>!</div>
                <div className="alert-copy"><strong>{alerta.computador}</strong><span>{alerta.mensagem}</span></div>
                <small>{alerta.hora}</small>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="content-grid lower-grid">
        <article className="panel panel-large">
          <h2>Desempenho da Infraestrutura</h2>
          <div className="fake-chart">
            <div className="chart-line blue-line">●────●───●────●────●──●────●</div>
            <div className="chart-line purple-line">●───●────●──●────●────●───●</div>
            <div className="chart-line green-line">●────●──●────●───●────●────●</div>
          </div>
        </article>

        <article className="panel donut-panel">
          <h2>Distribuição dos equipamentos</h2>
          <div className="donut-row">
            <div className="donut" style={{ background: `conic-gradient(#2faf62 0 ${(dashboard.computadores.online / dashboard.computadores.total) * 100}%, #ff3d3d 0 100%)` }} />
            <div className="legend">
              <span><i className="dot green" /> Online <strong>{dashboard.computadores.online}</strong></span>
              <span><i className="dot red" /> Offline <strong>{dashboard.computadores.offline}</strong></span>
            </div>
          </div>
        </article>
      </section>
    </>
  );
}

export default Dashboard;
