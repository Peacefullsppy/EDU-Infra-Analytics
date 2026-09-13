import { useEffect, useMemo, useState } from "react";
import MetricCard from "../../components/MetricCard/MetricCard";
import StatusBadge from "../../components/StatusBadge/StatusBadge";
import { createLaboratorio, getLaboratorios } from "../../services/api";

function Laboratories() {
  const [laboratorios, setLaboratorios] = useState([]);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [formulario, setFormulario] = useState({ nome: "", localizacao: "", status: "ativo" });
  const [erro, setErro] = useState("");

  function carregarLaboratorios() {
    getLaboratorios()
      .then(setLaboratorios)
      .catch((error) => setErro(error.message));
  }

  useEffect(() => {
    carregarLaboratorios();
  }, []);

  const resumo = useMemo(() => {
    const equipamentos = laboratorios.reduce((total, lab) => total + lab.equipamentos, 0);
    const disponiveis = laboratorios.reduce((total, lab) => total + lab.online, 0);
    const problemas = laboratorios.reduce((total, lab) => total + lab.problemas, 0);

    return { equipamentos, disponiveis, problemas };
  }, [laboratorios]);

  const indicadores = useMemo(() => {
    const comIIE = laboratorios.filter((lab) => typeof lab.iie === "number");

    if (comIIE.length === 0) {
      return {
        melhor: "-",
        atencao: "-",
        manutencao: "-",
        media: "-",
      };
    }

    const ordenados = [...comIIE].sort((a, b) => b.iie - a.iie);
    const somaIIE = comIIE.reduce((total, lab) => total + lab.iie, 0);

    return {
      melhor: ordenados[0]?.nome ?? "-",
      atencao: ordenados.length > 2 ? ordenados[1].nome : ordenados.at(-1)?.nome ?? "-",
      manutencao: ordenados.at(-1)?.nome ?? "-",
      media: (Math.floor((somaIIE / comIIE.length) * 10) / 10).toFixed(1).replace(".", ","),
    };
  }, [laboratorios]);

  const maiorQuantidade = Math.max(...laboratorios.map((lab) => lab.equipamentos), 1);
  const percentualDisponivel = resumo.equipamentos
    ? Math.round((resumo.disponiveis / resumo.equipamentos) * 100)
    : 0;
  const percentualProblemas = resumo.equipamentos
    ? Math.round((resumo.problemas / resumo.equipamentos) * 100)
    : 0;

  async function cadastrarLaboratorio(event) {
    event.preventDefault();
    setErro("");

    try {
      await createLaboratorio(formulario);
      setFormulario({ nome: "", localizacao: "", status: "ativo" });
      setMostrarFormulario(false);
      carregarLaboratorios();
    } catch (error) {
      setErro(error.message);
    }
  }

  function statusDoLaboratorio(iie) {
    if (iie == null) return "ativo";
    if (iie >= 85) return "saudavel";
    if (iie >= 70) return "atencao";
    return "critico";
  }

  function classeIIE(iie) {
    if (iie == null) return "";
    if (iie >= 85) return "success-text";
    if (iie >= 70) return "warning-text";
    return "danger-text";
  }

  const dataAtual = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date());

  return (
    <div className="laboratories-page">
      <header className="page-header laboratories-header">
        <div>
          <h1>Laboratórios</h1>
          <p>Gerencie e acompanhe os laboratórios da instituição</p>
        </div>

        <div className="laboratories-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => setMostrarFormulario((valor) => !valor)}
          >
            + Novo laboratório
          </button>
          <div className="date-pill">▣ {dataAtual}⌄</div>
        </div>
      </header>

      {mostrarFormulario && (
        <form className="form-panel laboratory-form" onSubmit={cadastrarLaboratorio}>
          <div>
            <label htmlFor="nome-laboratorio">Nome</label>
            <input
              id="nome-laboratorio"
              value={formulario.nome}
              onChange={(event) => setFormulario({ ...formulario, nome: event.target.value })}
              placeholder="Ex.: LAB 04"
              required
            />
          </div>

          <div>
            <label htmlFor="localizacao-laboratorio">Localização</label>
            <input
              id="localizacao-laboratorio"
              value={formulario.localizacao}
              onChange={(event) => setFormulario({ ...formulario, localizacao: event.target.value })}
              placeholder="Ex.: Informática 4"
              required
            />
          </div>

          <button className="primary-button" type="submit">Salvar laboratório</button>
        </form>
      )}

      {erro && <div className="error-box">{erro}</div>}

      <section className="metrics-grid laboratories-metrics">
        <MetricCard title="Total de laboratórios" value={laboratorios.length} tone="blue" icon="▦" />
        <MetricCard title="Equipamentos" value={resumo.equipamentos} tone="blue" icon="▣" />
        <MetricCard title="Disponíveis" value={resumo.disponiveis} tone="green" icon="✓" />
        <MetricCard title="Com problemas" value={resumo.problemas} tone="red" icon="!" />
      </section>

      <section className="content-grid laboratories-main-grid">
        <article className="panel panel-large laboratory-status-panel">
          <div className="panel-title-row">
            <h2>Situação dos Laboratórios</h2>
            <button className="text-button" type="button">Ver todos ›</button>
          </div>

          <div className="table-wrap">
            <table className="laboratories-table">
              <thead>
                <tr>
                  <th>Laboratório</th>
                  <th>Equipamentos</th>
                  <th>Online</th>
                  <th>Problemas</th>
                  <th>IIE</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {laboratorios.map((lab) => (
                  <tr key={lab.id}>
                    <td>
                      <div className="laboratory-name-cell">
                        <span className="laboratory-table-icon">▦</span>
                        <span>
                          <strong>{lab.nome}</strong>
                          <small className="table-subtitle">{lab.localizacao}</small>
                        </span>
                      </div>
                    </td>
                    <td>{lab.equipamentos}</td>
                    <td className="success-text">{lab.online}</td>
                    <td className={lab.problemas > 0 ? "warning-text" : ""}>{lab.problemas}</td>
                    <td className={classeIIE(lab.iie)}>{lab.iie ?? "-"}</td>
                    <td><StatusBadge status={statusDoLaboratorio(lab.iie)} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel quick-summary-panel">
          <h2>Resumo rápido</h2>
          <div className="quick-summary">
            <div>
              <span className="summary-icon green-bg">↗</span>
              <p>Melhor desempenho<strong>{indicadores.melhor}</strong></p>
            </div>
            <div>
              <span className="summary-icon orange-bg">!</span>
              <p>Maior atenção<strong>{indicadores.atencao}</strong></p>
            </div>
            <div>
              <span className="summary-icon red-bg">⚒</span>
              <p>Prioridade de manutenção<strong>{indicadores.manutencao}</strong></p>
            </div>
            <div>
              <span className="summary-icon blue-bg">▥</span>
              <p>IIE médio institucional<strong className="summary-iie">{indicadores.media}</strong></p>
            </div>
          </div>
        </article>
      </section>

      <section className="content-grid lower-grid laboratories-lower-grid">
        <article className="panel capacity-panel">
          <div className="panel-title-row chart-heading">
            <h2>Capacidade e disponibilidade</h2>
            <div className="chart-legend-inline">
              <span><i className="legend-square blue-square" />Equipamentos totais</span>
              <span><i className="legend-square green-square" />Equipamentos online</span>
            </div>
          </div>

          <div className="bar-chart">
            <div className="bar-chart-y-axis">
              <span>{maiorQuantidade}</span>
              <span>{Math.round(maiorQuantidade / 2)}</span>
              <span>0</span>
            </div>

            <div className="bar-chart-content">
              <div className="bar-grid-line top" />
              <div className="bar-grid-line middle" />
              <div className="bar-grid-line bottom" />

              {laboratorios.map((lab) => (
                <div className="bar-group" key={lab.id}>
                  <div className="bars">
                    <div className="bar-column">
                      <span className="bar-value">{lab.equipamentos}</span>
                      <div
                        className="chart-bar total-bar"
                        style={{ height: `${Math.max((lab.equipamentos / maiorQuantidade) * 128, 8)}px` }}
                      />
                    </div>
                    <div className="bar-column">
                      <span className="bar-value">{lab.online}</span>
                      <div
                        className="chart-bar online-bar"
                        style={{ height: `${Math.max((lab.online / maiorQuantidade) * 128, 8)}px` }}
                      />
                    </div>
                  </div>
                  <strong className="bar-label">{lab.nome}</strong>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="panel distribution-panel">
          <h2>Distribuição dos equipamentos</h2>
          <div className="donut-row laboratory-donut-row">
            <div
              className="donut laboratory-donut"
              style={{
                background: `conic-gradient(
                  #2faf62 0 ${percentualDisponivel}%,
                  #ff3d3d ${percentualDisponivel}% 100%
                )`,
              }}
            />

            <div className="legend distribution-legend">
              <span><i className="dot green" /> Online <strong>{resumo.disponiveis} ({percentualDisponivel}%)</strong></span>
              <span><i className="dot red" /> Offline <strong>{resumo.problemas} ({percentualProblemas}%)</strong></span>
              <span><i className="dot gray" /> Manutenção <strong>0 (0%)</strong></span>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}

export default Laboratories;
