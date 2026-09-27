const labels = {
  online: "Online", saudavel: "Saudável", atencao: "Atenção", critico: "Crítico", offline: "Offline",
  ativo: "Ativo", inativo: "Inativo",
};
function StatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{labels[status] || status}</span>;
}
export default StatusBadge;
