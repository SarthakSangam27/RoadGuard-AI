function ModelCard({
  title,
  tag,
  status,
  children,
}) {
  const isDanger = status === "danger";

  return (
    <div
      className={`model-card ${
        isDanger ? "model-danger" : "model-safe"
      }`}
    >
      <div className="model-card-header">
        <div>
          <h3>{title}</h3>

          <span className="model-tag">
            {tag}
          </span>
        </div>

        <span
          className={`model-status ${
            isDanger ? "danger" : "safe"
          }`}
        >
          {isDanger ? "DETECTED" : "CLEAR"}
        </span>
      </div>

      <div className="model-card-body">
        {children}
      </div>
    </div>
  );
}

export default ModelCard;