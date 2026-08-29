function DetectionOverlay({
  detections = [],
}) {
  if (!detections.length) {
    return null;
  }

  return (
    <div className="detection-overlay">
      {detections.map(
        (detection, index) => {
          const box = detection.bboxPct;

          if (!box) {
            return null;
          }

          const width =
            box.w * 100;

          const height =
            box.h * 100;

          const left =
            (box.x - box.w / 2) * 100;

          const top =
            (box.y - box.h / 2) * 100;

          return (
            <div
              key={index}
              className="detection-box"
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${width}%`,
                height: `${height}%`,
              }}
            >
              <div className="detection-label">
                Pothole{" "}
                {(
                  detection.confidence *
                  100
                ).toFixed(0)}
                %
              </div>
            </div>
          );
        }
      )}
    </div>
  );
}

export default DetectionOverlay;