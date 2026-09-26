import { useState } from "react";
import { login } from "../../services/api";

function Login({ onSuccess, onPrivacy }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setErro("");
    setCarregando(true);

    try {
      await login(email, password);
      await onSuccess();
    } catch (error) {
      setErro(error.message);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="login-page">
      <section className="login-card">
        <div className="login-brand">
          <div className="login-brand-icon">▥</div>
          <div>
            <strong>EDU-<span>INFRA</span></strong>
            <small>ANALYTICS</small>
          </div>
        </div>

        <div className="login-copy">
          <h1>Acesso ao sistema</h1>
          <p>Entre com uma conta cadastrada para acessar os dados de infraestrutura.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="login-email">E-mail</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="admin@escola.edu"
            autoComplete="username"
            required
          />

          <label htmlFor="login-password">Senha</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Sua senha"
            autoComplete="current-password"
            required
          />

          {erro && <div className="error-box login-error">{erro}</div>}

          <button className="primary-button login-button" type="submit" disabled={carregando}>
            {carregando ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="login-privacy">
          Ao utilizar o sistema, consulte as informações sobre tratamento de dados na{" "}
          <button type="button" onClick={onPrivacy}>Política de Privacidade e LGPD</button>.
        </p>
      </section>
    </div>
  );
}

export default Login;
