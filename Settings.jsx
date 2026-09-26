import { useEffect, useState } from "react";
import { consultarCep, getAuditoria } from "../../services/api";

function Settings({ user, onPrivacy }) {
  const [cep, setCep] = useState("");
  const [endereco, setEndereco] = useState(null);
  const [logs, setLogs] = useState([]);
  const [erroCep, setErroCep] = useState("");
  const [erroLogs, setErroLogs] = useState("");

  useEffect(() => {
    if (user?.role !== "admin") return;

    getAuditoria(80)
      .then(setLogs)
      .catch((error) => setErroLogs(error.message));
  }, [user]);

  async function handleCep(event) {
    event.preventDefault();
    setErroCep("");
    setEndereco(null);

    try {
      const data = await consultarCep(cep);
      setEndereco(data);
    } catch (error) {
      setErroCep(error.message);
    }
  }

  return (
    <div className="settings-page">
      <header className="page-header">
        <div>
          <h1>Configurações e segurança</h1>
          <p>Integração externa, auditoria e informações de privacidade</p>
        </div>
        <button className="secondary-button" type="button" onClick={onPrivacy}>LGPD e Privacidade</button>
      </header>

      <section className="settings-grid">
        <article className="panel integration-panel">
          <h2>Integração externa — ViaCEP</h2>
          <p className="panel-description">
            Consulta um serviço externo para obter endereço a partir de um CEP. A funcionalidade é auxiliar e
            não interfere no monitoramento caso o serviço externo esteja indisponível.
          </p>

          <form className="cep-form" onSubmit={handleCep}>
            <input
              value={cep}
              onChange={(event) => setCep(event.target.value)}
              placeholder="Ex.: 01001000"
              maxLength={9}
              required
            />
            <button className="primary-button" type="submit">Consultar CEP</button>
          </form>

          {erroCep && <div className="error-box">{erroCep}</div>}

          {endereco && (
            <div className="address-result">
              <strong>{endereco.cep}</strong>
              <span>{endereco.logradouro || "Logradouro não informado"}</span>
              <span>{endereco.bairro || "Bairro não informado"}</span>
              <span>{endereco.cidade} - {endereco.uf}</span>
              {endereco.ibge && <small>Código IBGE: {endereco.ibge}</small>}
            </div>
          )}
        </article>

        <article className="panel security-summary-panel">
          <h2>Segurança da sessão</h2>
          <div className="security-list">
            <div><span>✓</span><p><strong>Autenticação JWT</strong><small>Token temporário após login.</small></p></div>
            <div><span>✓</span><p><strong>Senha com hash Argon2</strong><small>A senha original não é salva no banco.</small></p></div>
            <div><span>✓</span><p><strong>Controle por perfil</strong><small>Admin, técnico e gestor possuem permissões diferentes.</small></p></div>
            <div><span>✓</span><p><strong>Auditoria</strong><small>Ações relevantes ficam registradas no PostgreSQL.</small></p></div>
          </div>
        </article>
      </section>

      <article className="panel audit-panel">
        <div className="panel-title-row settings-audit-title">
          <div>
            <h2>Log de auditoria</h2>
            <p className="panel-description">Acessos e ações registradas nas funcionalidades implementadas.</p>
          </div>
          {user?.role !== "admin" && <span className="role-note">Disponível apenas para administrador</span>}
        </div>

        {erroLogs && <div className="error-box audit-error">{erroLogs}</div>}

        {user?.role === "admin" && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Usuário</th>
                  <th>Ação</th>
                  <th>Recurso</th>
                  <th>Método</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{new Date(log.criado_em).toLocaleString("pt-BR")}</td>
                    <td>{log.usuario || "Não identificado"}</td>
                    <td><strong>{log.acao}</strong></td>
                    <td>{log.recurso}{log.recurso_id ? ` #${log.recurso_id}` : ""}</td>
                    <td>{log.metodo || "-"}</td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr><td colSpan="5">Nenhum registro encontrado.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </div>
  );
}

export default Settings;
