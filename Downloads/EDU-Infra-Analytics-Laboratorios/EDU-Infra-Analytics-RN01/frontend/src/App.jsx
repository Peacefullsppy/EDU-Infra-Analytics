import { useState } from "react";
import Sidebar from "./components/Sidebar/Sidebar";
import Dashboard from "./pages/Dashboard/Dashboard";
import Laboratories from "./pages/Laboratories/Laboratories";
import Computers from "./pages/Computers/Computers";
import "./App.css";

function Placeholder({ title }) {
  return <div className="placeholder-panel"><h1>{title}</h1><p>Esta parte ficará para as próximas regras de negócio do projeto.</p></div>;
}

function App() {
  const [page, setPage] = useState("dashboard");
  const pages = {
    dashboard: <Dashboard />,
    laboratorios: <Laboratories />,
    computadores: <Computers />,
    indicadores: <Placeholder title="Indicadores" />,
    relatorios: <Placeholder title="Relatórios" />,
    configuracoes: <Placeholder title="Configurações" />,
  };
  return <div className="app-shell"><Sidebar page={page} onChange={setPage} /><main className="main-content">{pages[page]}</main></div>;
}

export default App;
