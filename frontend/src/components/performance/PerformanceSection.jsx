import React from "react";

function Metric({
  icon,
  label,
  value,
}) {
  return (
    <div className="performance-metric">
      <div className="performance-metric-left">
        <span className="performance-metric-icon">
          {icon}
        </span>

        <span className="performance-metric-label">
          {label}
        </span>
      </div>

      <strong className="performance-metric-value">
        {value}
      </strong>
    </div>
  );
}

function PerformanceCard({
  title,
  tag,
  icon,
  description,
  metrics,
}) {
  return (
    <div className="performance-card">

      {/* HEADER */}
      <div className="performance-card-header">

        <div className="performance-card-title">

          <h2>
            {title}
          </h2>

          <span className="performance-card-tag">
            {tag}
          </span>

        </div>

        <div className="performance-card-icon">
          {icon}
        </div>

      </div>


      {/* DESCRIPTION */}
      <div className="performance-card-body">

        <p className="performance-description">
          {description}
        </p>


        {/* METRICS */}
        <div className="performance-metrics">

          {metrics.map(
            (metric, index) => (
              <Metric
                key={index}
                icon={metric.icon}
                label={metric.label}
                value={metric.value}
              />
            )
          )}

        </div>

      </div>

    </div>
  );
}


function PerformanceSection() {

  /*
   * These are the metrics from the current
   * training/demo setup.
   *
   * VGG19:
   * Epoch 1 output:
   * accuracy  = 0.7887
   * precision = 0.7887
   * recall    = 0.7331
   *
   * F1 is calculated from precision and recall.
   *
   * YOLOv8:
   * The actual inference time from your test image
   * was approximately 232.6 ms.
   *
   * mAP50 / precision / recall will be displayed
   * as "Pending" until the YOLO validation metrics
   * are available.
   */

  const vggPrecision = 0.7887;
  const vggRecall = 0.7331;

  const vggF1 =
    (2 *
      vggPrecision *
      vggRecall) /
    (vggPrecision + vggRecall);


  const vggMetrics = [
    {
      label: "Accuracy",
      value: "78.87%",
      icon: "◎",
    },

    {
      label: "Precision",
      value: "78.87%",
      icon: "⊕",
    },

    {
      label: "Recall",
      value: "73.31%",
      icon: "◔",
    },

    {
      label: "F1 Score",
      value:
        `${(vggF1 * 100).toFixed(2)}%`,
      icon: "♧",
    },
  ];


  const yoloMetrics = [
    {
      label: "mAP50",
      value: "48.23%",
      icon: "◎",
    },

    {
      label: "Precision",
      value: "51.46%",
      icon: "⊕",
    },

    {
      label: "Recall",
      value: "48.19%",
      icon: "◔",
    },

    {
      label: "Inference",
      value: "232.6 ms",
      icon: "◷",
    },
  ];


  return (
    <section
      className="performance-section"
      id="performance"
    >

      <div className="performance-grid">

        {/* =================================================
            VGG19
        ================================================= */}

        <PerformanceCard
          title="VGG19"
          tag="CLASSIFIER"
          icon="🧠"
          description="Determines whether a road image contains pothole damage."
          metrics={vggMetrics}
        />


        {/* =================================================
            YOLOv8
        ================================================= */}

        <PerformanceCard
          title="YOLOv8"
          tag="DETECTOR"
          icon="⊙"
          description="Locates individual potholes and provides confidence scores and bounding boxes."
          metrics={yoloMetrics}
        />

      </div>

    </section>
  );
}


export default PerformanceSection;