import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar/Sidebar";
import Computers from "./pages/Computers/Computers";
import Dashboard from "./pages/Dashboard/Dashboard";
import Laboratories from "./pages/Laboratories/Laboratories";
import Login from "./pages/Login/Login";
import Privacy from "./pages/Privacy/Privacy";
import Settings from "./pages/Settings/Settings";
import { clearToken, getMe, getToken } from "./services/api";
import "./App.css";

function Placeholder({ title }) {
  return (
    <div className="placeholder-panel">
      <h1>{title}</h1>
      <p>Esta parte ficará para as próximas regras de negócio do projeto.</p>
    </div>
  );
}

function App() {
  const [page, setPage] = useState("dashboard");
  const [user, setUser] = useState(null);
  const [loadingSession, setLoadingSession] = useState(Boolean(getToken()));
  const [showPrivacy, setShowPrivacy] = useState(false);

  async function loadSession() {
    if (!getToken()) {
      setUser(null);
      setLoadingSession(false);
      return;
    }

    try {
      const data = await getMe();
      setUser(data);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoadingSession(false);
    }
  }

  useEffect(() => {
    loadSession();
  }, []);

  function logout() {
    clearToken();
    setUser(null);
    setPage("dashboard");
  }

  if (showPrivacy) {
    return <Privacy onBack={() => setShowPrivacy(false)} />;
  }

  if (loadingSession) {
    return <div className="session-loading">Validando sessão...</div>;
  }

  if (!user) {
    return <Login onSuccess={loadSession} onPrivacy={() => setShowPrivacy(true)} />;
  }

  const pages = {
    dashboard: <Dashboard />,
    laboratorios: <Laboratories />,
    computadores: <Computers />,
    indicadores: <Placeholder title="Indicadores" />,
    relatorios: <Placeholder title="Relatórios" />,
    configuracoes: <Settings user={user} onPrivacy={() => setShowPrivacy(true)} />,
  };

  return (
    <div className="app-shell">
      <Sidebar page={page} onChange={setPage} user={user} onLogout={logout} />
      <main className="main-content">{pages[page]}</main>
    </div>
  );
}

export default App;
