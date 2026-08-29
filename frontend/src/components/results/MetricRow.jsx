function MetricRow({
  label,
  value,
  highlight = false,
}) {
  return (
    <div className="metric-row">
      <span>{label}</span>

      <strong
        className={
          highlight
            ? "metric-highlight"
            : ""
        }
      >
        {value}
      </strong>
    </div>
  );
}

export default MetricRow;