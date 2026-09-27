const menu = [
  ["dashboard", "⌂", "Dashboard"],
  ["laboratorios", "▦", "Laboratórios"],
  ["computadores", "▣", "Computadores"],
  ["indicadores", "↗", "Indicadores"],
  ["relatorios", "▤", "Relatórios"],
  ["configuracoes", "⚙", "Configurações"],
  ["privacidade", "◈", "Privacidade"],
];

function Sidebar({ page, onChange, user, onLogout }) {
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

      <div className="sidebar-footer authenticated-footer">
        <div className="user-avatar">{user?.name?.charAt(0)?.toUpperCase() || "U"}</div>
        <div className="sidebar-user-copy">
          <strong>{user?.name || "Usuário"}</strong>
          <small>{user?.role || "perfil"}</small>
        </div>
        <button className="logout-button" onClick={onLogout} type="button">Sair</button>
      </div>
    </aside>
  );
}

export default Sidebar;
