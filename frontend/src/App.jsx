import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar/Sidebar";
import Computers from "./pages/Computers/Computers";
import Dashboard from "./pages/Dashboard/Dashboard";
import Indicators from "./pages/Indicators/Indicators";
import Laboratories from "./pages/Laboratories/Laboratories";
import Login from "./pages/Login/Login";
import Privacy from "./pages/Privacy/Privacy";
import Reports from "./pages/Reports/Reports";
import Settings from "./pages/Settings/Settings";
import { clearSession, getMe, getSavedUser } from "./services/api";
import "./App.css";

function App() {
  const [page, setPage] = useState("dashboard");
  const [user, setUser] = useState(getSavedUser());
  const [checkingSession, setCheckingSession] = useState(Boolean(user));

  useEffect(() => {
    const savedUser = getSavedUser();
    if (!savedUser) {
      setCheckingSession(false);
      return;
    }

    getMe()
      .then((currentUser) => setUser(currentUser))
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setCheckingSession(false));
  }, []); // valida somente ao abrir a aplicação

  function logout() {
    clearSession();
    setUser(null);
    setPage("dashboard");
  }

  if (checkingSession) {
    return <div className="full-page-loading">Validando sessão...</div>;
  }

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  const pages = {
    dashboard: <Dashboard />,
    laboratorios: <Laboratories />,
    computadores: <Computers />,
    indicadores: <Indicators />,
    relatorios: <Reports />,
    configuracoes: <Settings user={user} />,
    privacidade: <Privacy />,
  };

  return (
    <div className="app-shell">
      <Sidebar page={page} onChange={setPage} user={user} onLogout={logout} />
      <main className="main-content">{pages[page]}</main>
    </div>
  );
}

export default App;
