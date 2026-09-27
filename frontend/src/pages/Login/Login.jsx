import { useState } from "react";
import { login, saveSession } from "../../services/api";

function Login({ onLogin }) {
  const [email, setEmail] = useState("admin@escola.edu");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setErro("");
    setCarregando(true);

    try {
      const data = await login(email, password);
      saveSession(data);
      onLogin(data.user);
    } catch (error) {
      setErro(error.message);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="brand-icon large">▥</div>
          <div>
            <div className="brand-title dark">EDU-<span>INFRA</span></div>
            <div className="brand-subtitle dark">ANALYTICS</div>
          </div>
        </div>

        <div className="login-copy">
          <h1>Acesso ao sistema</h1>
          <p>Entre para acompanhar laboratórios, computadores, indicadores e auditoria.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            E-mail
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@escola.edu"
              required
            />
          </label>

          <label>
            Senha
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Digite sua senha"
              required
            />
          </label>

          {erro && <div className="error-box">{erro}</div>}

          <button className="primary-button login-button" disabled={carregando} type="submit">
            {carregando ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <small className="login-help">
          O usuário administrador é criado pelo comando <code>python -m app.seed</code>.
        </small>
      </div>
    </div>
  );
}

export default Login;
