function MetricCard({ title, value, subtitle, tone = "blue", icon = "●" }) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <div>
        <p className="metric-title">{title}</p>
        <strong className="metric-value">{value}</strong>
        {subtitle && <p className="metric-subtitle">{subtitle}</p>}
      </div>
      <div className="metric-icon">{icon}</div>
    </article>
  );
}
export default MetricCard;
