const menu = [
  ["dashboard", "⌂", "Dashboard"],
  ["laboratorios", "▦", "Laboratórios"],
  ["computadores", "▣", "Computadores"],
  ["indicadores", "↗", "Indicadores"],
  ["relatorios", "▤", "Relatórios"],
  ["configuracoes", "⚙", "Configurações"],
];

function Sidebar({ page, onChange }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">▥</div>
        <div className="brand-title">EDU-<span>INFRA</span></div>
        <div className="brand-subtitle">ANALYTICS</div>
      </div>

      <nav className="menu">
        {menu.map(([key, icon, label]) => (
          <button key={key} className={`menu-item ${page === key ? "active" : ""}`} onClick={() => onChange(key)} type="button">
            <span className="menu-icon">{icon}</span>
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-avatar">A</div>
        <div><strong>Administrador</strong><small>MVP sem autenticação</small></div>
      </div>
    </aside>
  );
}

export default Sidebar;
