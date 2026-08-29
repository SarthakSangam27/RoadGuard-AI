import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Trash2,
} from "lucide-react";

const STORAGE_KEY = "roadguard_scan_history";

function ScanHistory() {
  const [history, setHistory] = useState([]);

  function loadHistory() {
    try {
      const stored = localStorage.getItem(
        STORAGE_KEY
      );

      if (!stored) {
        setHistory([]);
        return;
      }

      setHistory(JSON.parse(stored));
    } catch (error) {
      console.error(
        "Unable to load scan history:",
        error
      );

      setHistory([]);
    }
  }

  useEffect(() => {
    loadHistory();

    const handleHistoryUpdate = () => {
      loadHistory();
    };

    window.addEventListener(
      "roadguard:history-updated",
      handleHistoryUpdate
    );

    return () => {
      window.removeEventListener(
        "roadguard:history-updated",
        handleHistoryUpdate
      );
    };
  }, []);

  function clearHistory() {
    const confirmed = window.confirm(
      "Clear all RoadGuard-AI scan history?"
    );

    if (!confirmed) {
      return;
    }

    localStorage.removeItem(STORAGE_KEY);

    setHistory([]);
  }

  return (
    <section
      className="history-section"
      id="history"
    >
      <div className="history-heading">
        <div className="history-eyebrow">
          <span />
          SCAN HISTORY
        </div>

        <div className="history-title-row">
          <div>
            <h2>
              Previous road scans.
            </h2>

            <p>
              Review recent RoadGuard-AI
              detection results from this browser.
            </p>
          </div>

          {history.length > 0 && (
            <button
              className="clear-history-button"
              onClick={clearHistory}
            >
              <Trash2 size={15} />
              Clear History
            </button>
          )}
        </div>
      </div>

      {history.length === 0 ? (
        <div className="history-empty">
          <Clock3 size={30} />

          <h3>
            No scans yet
          </h3>

          <p>
            Completed scans will appear here
            automatically.
          </p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((scan) => {
            const detected =
              scan.pothole_detected;

            return (
              <div
                className="history-card"
                key={scan.id}
              >
                <div className="history-card-main">
                  <div
                    className={`history-result-icon ${
                      detected
                        ? "history-danger"
                        : "history-safe"
                    }`}
                  >
                    {detected ? (
                      <AlertTriangle
                        size={20}
                      />
                    ) : (
                      <CheckCircle2
                        size={20}
                      />
                    )}
                  </div>

                  <div className="history-file">
                    <h3>
                      {scan.file_name}
                    </h3>

                    <span>
                      {new Date(
                        scan.timestamp
                      ).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="history-stats">
                  <div>
                    <span>
                      RESULT
                    </span>

                    <strong
                      className={
                        detected
                          ? "history-text-danger"
                          : "history-text-safe"
                      }
                    >
                      {detected
                        ? "POTHOLE"
                        : "CLEAR"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      VGG19
                    </span>

                    <strong>
                      {scan.vgg19_confidence
                        ? `${(
                            scan.vgg19_confidence *
                            100
                          ).toFixed(1)}%`
                        : "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      YOLOv8
                    </span>

                    <strong>
                      {scan.yolo_detections}
                    </strong>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default ScanHistory;