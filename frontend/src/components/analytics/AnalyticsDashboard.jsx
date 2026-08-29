import { useEffect, useState } from "react";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ScanLine,
} from "lucide-react";
import "./AnalyticsDashboard.css";
const STORAGE_KEY =
  "roadguard_scan_history";

function AnalyticsDashboard() {
  const [history, setHistory] =
    useState([]);

  function loadHistory() {
    try {
      const stored =
        localStorage.getItem(
          STORAGE_KEY
        );

      if (!stored) {
        setHistory([]);
        return;
      }

      setHistory(
        JSON.parse(stored)
      );
    } catch (error) {
      console.error(
        "Unable to load analytics:",
        error
      );

      setHistory([]);
    }
  }

  useEffect(() => {
    loadHistory();

    const handleUpdate = () => {
      loadHistory();
    };

    window.addEventListener(
      "roadguard:history-updated",
      handleUpdate
    );

    return () => {
      window.removeEventListener(
        "roadguard:history-updated",
        handleUpdate
      );
    };
  }, []);

  const totalScans =
    history.length;

  const potholeScans =
    history.filter(
      (scan) =>
        scan.pothole_detected
    ).length;

  const clearScans =
    totalScans - potholeScans;

  const detectionRate =
    totalScans > 0
      ? (
          (potholeScans /
            totalScans) *
          100
        ).toFixed(1)
      : "0.0";

  const averageVggConfidence =
    totalScans > 0
      ? (
          (history.reduce(
            (sum, scan) =>
              sum +
              (scan.vgg19_confidence ||
                0),
            0
          ) /
            totalScans) *
          100
        ).toFixed(1)
      : "0.0";

  const averageYoloDetections =
    totalScans > 0
      ? (
          history.reduce(
            (sum, scan) =>
              sum +
              (scan.yolo_detections ||
                0),
            0
          ) / totalScans
        ).toFixed(1)
      : "0.0";

  return (
    <section
      className="analytics-section"
      id="analytics"
    >
      <div className="analytics-heading">
        <div className="analytics-eyebrow">
          <span />
          SCAN ANALYTICS
        </div>

        <h2>
          RoadGuard-AI
          <br />
          <span>at a glance.</span>
        </h2>

        <p>
          A live summary of the road scans
          performed in this browser.
        </p>
      </div>


      {/* TOP STATISTICS */}

      <div className="analytics-stat-grid">

        <div className="analytics-stat-card">
          <div className="analytics-stat-icon">
            <ScanLine size={21} />
          </div>

          <span>
            TOTAL SCANS
          </span>

          <strong>
            {totalScans}
          </strong>
        </div>


        <div className="analytics-stat-card danger-stat">
          <div className="analytics-stat-icon">
            <AlertTriangle size={21} />
          </div>

          <span>
            POTHOLE SCANS
          </span>

          <strong>
            {potholeScans}
          </strong>
        </div>


        <div className="analytics-stat-card safe-stat">
          <div className="analytics-stat-icon">
            <CheckCircle2 size={21} />
          </div>

          <span>
            CLEAR ROADS
          </span>

          <strong>
            {clearScans}
          </strong>
        </div>


        <div className="analytics-stat-card">
          <div className="analytics-stat-icon">
            <BarChart3 size={21} />
          </div>

          <span>
            DETECTION RATE
          </span>

          <strong>
            {detectionRate}%
          </strong>
        </div>

      </div>


      {/* ANALYTICS DETAILS */}

      <div className="analytics-details">

        {/* Detection rate */}

        <div className="analytics-panel">

          <div className="analytics-panel-header">
            <div>
              <span>
                ROAD CONDITION
              </span>

              <h3>
                Pothole Detection Rate
              </h3>
            </div>

            <strong>
              {detectionRate}%
            </strong>
          </div>

          <div className="progress-track">
            <div
              className="progress-fill"
              style={{
                width:
                  `${detectionRate}%`,
              }}
            />
          </div>

          <p>
            Percentage of completed scans
            where RoadGuard-AI detected
            pothole damage.
          </p>

        </div>


        {/* Model activity */}

        <div className="analytics-panel">

          <div className="analytics-panel-header">
            <div>
              <span>
                MODEL ACTIVITY
              </span>

              <h3>
                Detection Statistics
              </h3>
            </div>

            <Activity size={21} />
          </div>


          <div className="analytics-model-row">

            <div>
              <span>
                VGG19
              </span>

              <small>
                Average confidence
              </small>
            </div>

            <strong>
              {averageVggConfidence}%
            </strong>

          </div>


          <div className="analytics-model-row">

            <div>
              <span>
                YOLOv8
              </span>

              <small>
                Average detections / scan
              </small>
            </div>

            <strong>
              {averageYoloDetections}
            </strong>

          </div>

        </div>

      </div>


      {/* EMPTY STATE */}

      {totalScans === 0 && (
        <div className="analytics-empty">
          <BarChart3 size={25} />

          <span>
            Analytics will populate after
            your first completed scan.
          </span>
        </div>
      )}

    </section>
  );
}

export default AnalyticsDashboard;