import {
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

function ResultBanner({ detected }) {
  return (
    <div
      className={`result-banner ${
        detected ? "danger" : "safe"
      }`}
    >
      {detected ? (
        <AlertTriangle size={22} />
      ) : (
        <CheckCircle2 size={22} />
      )}

      <span>
        {detected
          ? "Pothole Detected"
          : "Road Surface Clear"}
      </span>

      <strong>
        {detected ? "ALERT" : "OK"}
      </strong>
    </div>
  );
}

export default ResultBanner;