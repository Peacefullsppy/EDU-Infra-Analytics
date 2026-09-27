import { useEffect, useState } from "react";
import { consultarCep, getAuditoria, getHealth } from "../../services/api";

function Settings({ user }) {
  const [health, setHealth] = useState(null);
  const [cep, setCep] = useState("");
  const [endereco, setEndereco] = useState(null);
  const [logs, setLogs] = useState([]);
  const [erro, setErro] = useState("");

  useEffect(() => {
    getHealth().then(setHealth).catch((error) => setErro(error.message));
    if (user?.role === "admin") {
      getAuditoria(30).then(setLogs).catch((error) => setErro(error.message));
    }
  }, [user]);

  async function pesquisarCep(event) {
    event.preventDefault();
    setErro("");
    setEndereco(null);
    try {
      const data = await consultarCep(cep);
      setEndereco(data);
      if (user?.role === "admin") {
        getAuditoria(30).then(setLogs).catch(() => {});
      }
    } catch (error) {
      setErro(error.message);
    }
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Configurações</h1>
          <p>Integrações, conexão do backend e registros de auditoria</p>
        </div>
      </header>

      {erro && <div className="error-box">{erro}</div>}

      <section className="settings-grid">
        <article className="panel">
          <h2>Status da aplicação</h2>
          <div className="status-check-row">
            <span className={`status-light ${health?.status === "ok" ? "ok" : ""}`} />
            <div>
              <strong>Backend</strong>
              <p>{health?.status === "ok" ? "API respondendo normalmente" : "Verificando..."}</p>
            </div>
          </div>
          <div className="status-check-row">
            <span className={`status-light ${health?.database === "conectado" ? "ok" : ""}`} />
            <div>
              <strong>Banco de dados</strong>
              <p>{health?.database || "Verificando conexão..."}</p>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>API externa — ViaCEP</h2>
          <p className="muted-copy">Integração complementar para consulta de endereços por CEP.</p>
          <form className="cep-form" onSubmit={pesquisarCep}>
            <input
              value={cep}
              onChange={(event) => setCep(event.target.value)}
              placeholder="Ex.: 01001000"
              maxLength={9}
              required
            />
            <button className="primary-button" type="submit">Consultar</button>
          </form>
          {endereco && (
            <div className="address-result">
              <strong>{endereco.cep}</strong>
              <span>{endereco.logradouro || "Logradouro não informado"}</span>
              <span>{endereco.bairro}</span>
              <span>{endereco.localidade} - {endereco.uf}</span>
            </div>
          )}
        </article>
      </section>

      {user?.role === "admin" ? (
        <section className="panel audit-panel">
          <div className="panel-title-row">
            <h2>Auditoria</h2>
            <span className="role-pill">Somente administrador</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Data/hora</th><th>Usuário</th><th>Ação</th><th>Entidade</th><th>IP</th></tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{new Date(log.data_hora).toLocaleString("pt-BR")}</td>
                    <td>{log.usuario}</td>
                    <td><strong>{log.acao}</strong></td>
                    <td>{log.entidade}</td>
                    <td>{log.ip || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
        <div className="business-rule-note">Os registros de auditoria são visíveis apenas para o perfil administrador.</div>
      )}
    </>
  );
}

export default Settings;
