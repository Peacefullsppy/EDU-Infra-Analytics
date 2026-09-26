import { useEffect, useMemo, useState } from "react";
import MetricCard from "../../components/MetricCard/MetricCard";
import StatusBadge from "../../components/StatusBadge/StatusBadge";
import { createComputador, getAlertas, getComputadores, getLaboratorios } from "../../services/api";

function Computers() {
  const [computadores, setComputadores] = useState([]);
  const [laboratorios, setLaboratorios] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [busca, setBusca] = useState("");
  const [laboratorioFiltro, setLaboratorioFiltro] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("");
  const [erro, setErro] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [form, setForm] = useState({ hostname: "", ip: "", laboratorio_id: "", status: "online", cpu: 0, ram: 0, disco: 0 });

  const carregar = async () => {
    try {
      const [pcs, labs, alerts] = await Promise.all([getComputadores(), getLaboratorios(), getAlertas()]);
      setComputadores(pcs); setLaboratorios(labs); setAlertas(alerts.slice(0, 4));
    } catch (error) { setErro(error.message); }
  };

  useEffect(() => { carregar(); }, []);

  const resumo = useMemo(() => {
    const offline = computadores.filter((pc) => pc.status === "offline").length;
    const atencao = computadores.filter((pc) => ["atencao", "critico"].includes(pc.status)).length;
    return { total: computadores.length, online: computadores.length - offline, offline, atencao };
  }, [computadores]);

  const laboratoriosPorId = useMemo(() => Object.fromEntries(laboratorios.map((lab) => [lab.id, lab])), [laboratorios]);
  const filtrados = computadores.filter((pc) => {
    const buscaOk = pc.hostname.toLowerCase().includes(busca.toLowerCase());
    const labOk = !laboratorioFiltro || pc.laboratorio_id === Number(laboratorioFiltro);
    const statusOk = !statusFiltro || pc.status === statusFiltro;
    return buscaOk && labOk && statusOk;
  });

  async function handleSubmit(event) {
    event.preventDefault(); setErro(""); setMensagem("");
    try {
      const payload = {
        ...form,
        laboratorio_id: Number(form.laboratorio_id),
        cpu: form.status === "offline" ? null : Number(form.cpu),
        ram: form.status === "offline" ? null : Number(form.ram),
        disco: form.status === "offline" ? null : Number(form.disco),
      };
      await createComputador(payload);
      setMensagem("Computador cadastrado com sucesso e vinculado ao laboratório.");
      setShowForm(false);
      setForm({ hostname: "", ip: "", laboratorio_id: "", status: "online", cpu: 0, ram: 0, disco: 0 });
      carregar();
    } catch (error) { setErro(error.message); }
  }

  return (
    <>
      <header className="page-header">
        <div><h1>Computadores</h1><p>Monitore os equipamentos cadastrados nos laboratórios</p></div>
        <button className="primary-button" onClick={() => setShowForm((value) => !value)} type="button">+ Cadastrar computador</button>
      </header>

      {showForm && (
        <form className="form-panel computer-form" onSubmit={handleSubmit}>
          <div><label>Hostname</label><input value={form.hostname} onChange={(e) => setForm({ ...form, hostname: e.target.value })} placeholder="Ex.: LAB01-PC21" required /></div>
          <div><label>IP</label><input value={form.ip} onChange={(e) => setForm({ ...form, ip: e.target.value })} placeholder="Ex.: 192.168.1.121" required /></div>
          <div><label>Laboratório</label><select value={form.laboratorio_id} onChange={(e) => setForm({ ...form, laboratorio_id: e.target.value })} required>
            <option value="">Selecione</option>{laboratorios.map((lab) => <option key={lab.id} value={lab.id}>{lab.nome} - {lab.localizacao}</option>)}
          </select></div>
          <div><label>Status</label><select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="online">Online</option><option value="atencao">Atenção</option><option value="critico">Crítico</option><option value="offline">Offline</option>
          </select></div>
          <button className="primary-button" type="submit">Salvar computador</button>
        </form>
      )}

      {erro && <div className="error-box">{erro}</div>}
      {mensagem && <div className="success-box">{mensagem}</div>}
      <div className="business-rule-note"><strong>RN01 ativa:</strong> o backend só aceita o cadastro se o laboratório informado existir.</div>

      <section className="metrics-grid">
        <MetricCard title="Total de equipamentos" value={resumo.total} tone="blue" icon="▣" />
        <MetricCard title="Online" value={resumo.online} tone="green" icon="✓" />
        <MetricCard title="Offline" value={resumo.offline} tone="red" icon="⏻" />
        <MetricCard title="Em atenção" value={resumo.atencao} tone="orange" icon="!" />
      </section>

      <section className="content-grid computers-grid">
        <article className="panel panel-large">
          <h2>Equipamentos monitorados</h2>
          <div className="filters">
            <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="⌕  Pesquisar equipamento..." />
            <select value={laboratorioFiltro} onChange={(e) => setLaboratorioFiltro(e.target.value)}><option value="">Todos os laboratórios</option>{laboratorios.map((lab) => <option key={lab.id} value={lab.id}>{lab.nome}</option>)}</select>
            <select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)}><option value="">Todos os status</option><option value="online">Online</option><option value="atencao">Atenção</option><option value="critico">Crítico</option><option value="offline">Offline</option></select>
          </div>
          <div className="table-wrap"><table>
            <thead><tr><th>Computador</th><th>Laboratório</th><th>Status</th><th>CPU</th><th>RAM</th><th>Disco</th><th>Última coleta</th></tr></thead>
            <tbody>{filtrados.slice(0, 12).map((pc) => <tr key={pc.id}>
              <td><strong>{pc.hostname}</strong></td><td>{laboratoriosPorId[pc.laboratorio_id]?.nome || "-"}</td><td><StatusBadge status={pc.status} /></td>
              <td>{pc.cpu ?? "--"}{pc.cpu != null ? "%" : ""}</td><td>{pc.ram ?? "--"}{pc.ram != null ? "%" : ""}</td><td>{pc.disco ?? "--"}{pc.disco != null ? "%" : ""}</td><td>{pc.ultima_coleta}</td>
            </tr>)}</tbody>
          </table></div>
        </article>

        <article className="panel">
          <h2>Alertas recentes</h2>
          <div className="alert-list">{alertas.map((alerta, index) => <div className="alert-item" key={`${alerta.computador}-${index}`}>
            <div className={`alert-symbol alert-${alerta.tipo}`}>!</div><div className="alert-copy"><strong>{alerta.computador}</strong><span>{alerta.mensagem}</span></div><small>{alerta.hora}</small>
          </div>)}</div>
        </article>
      </section>
    </>
  );
}

export default Computers;
