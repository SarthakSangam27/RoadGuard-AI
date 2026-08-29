import {
  useEffect,
  useState,
} from "react";

import UploadDropzone from "../components/upload/UploadDropzone";
import ImagePreview from "../components/upload/ImagePreview";
import SampleImages from "../components/upload/SampleImages";

import ScanButton from "../components/scanner/ScanButton";

import ResultBanner from "../components/results/ResultBanner";
import ModelCard from "../components/results/ModelCard";
import MetricRow from "../components/results/MetricRow";

import { analyzeImage } from "../services/scanService";


const STORAGE_KEY =
  "roadguard_scan_history";


function Dashboard() {
  const [file, setFile] =
    useState(null);

  const [scanning, setScanning] =
    useState(false);

  const [result, setResult] =
    useState(null);

  const [error, setError] =
    useState("");


  /*
  |--------------------------------------------------------------------------
  | SAVE COMPLETED SCAN TO LOCAL STORAGE
  |--------------------------------------------------------------------------
  */

  useEffect(() => {
    if (!result || !file) {
      return;
    }

    try {
      const stored =
        localStorage.getItem(
          STORAGE_KEY
        );

      const history = stored
        ? JSON.parse(stored)
        : [];

      const historyItem = {
        id: Date.now(),

        file_name: file.name,

        timestamp:
          new Date().toISOString(),

        pothole_detected:
          result.pothole_detected,

        vgg19_confidence:
          result.vgg19?.confidence || 0,

        yolo_detections:
          result.yolov8?.num_detections || 0,
      };

      const updatedHistory = [
        historyItem,
        ...history,
      ].slice(0, 20);

      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(
          updatedHistory
        )
      );

      window.dispatchEvent(
        new Event(
          "roadguard:history-updated"
        )
      );

    } catch (error) {
      console.error(
        "Unable to save scan history:",
        error
      );
    }
  }, [result, file]);


  /*
  |--------------------------------------------------------------------------
  | FILE SELECTION
  |--------------------------------------------------------------------------
  */

  function handleFile(selectedFile) {
    if (!selectedFile) {
      return;
    }

    setFile(selectedFile);

    setResult(null);

    setError("");
  }


  /*
  |--------------------------------------------------------------------------
  | RUN DETECTION
  |--------------------------------------------------------------------------
  */

  async function handleDetection() {
    if (!file || scanning) {
      return;
    }

    try {
      setScanning(true);

      setResult(null);

      setError("");

      const detectionResult =
        await analyzeImage(file);

      setResult(
        detectionResult
      );

    } catch (error) {
      console.error(
        "Detection failed:",
        error
      );

      setError(
        error.message ||
          "Unable to analyze the image."
      );

    } finally {
      setScanning(false);
    }
  }


  /*
  |--------------------------------------------------------------------------
  | RESET
  |--------------------------------------------------------------------------
  */

  function handleReset() {
    setFile(null);

    setResult(null);

    setError("");

    setScanning(false);
  }


  /*
  |--------------------------------------------------------------------------
  | YOLO HIGHEST CONFIDENCE
  |--------------------------------------------------------------------------
  */

  function getHighestYoloConfidence() {
    const detections =
      result?.yolov8?.detections || [];

    if (detections.length === 0) {
      return "0.0%";
    }

    const highestConfidence =
      Math.max(
        ...detections.map(
          (item) =>
            item.confidence || 0
        )
      );

    return `${(
      highestConfidence * 100
    ).toFixed(1)}%`;
  }


  /*
  |--------------------------------------------------------------------------
  | RENDER
  |--------------------------------------------------------------------------
  */

  return (
    <main
      className="dashboard"
      id="scan"
    >

      {/* =====================================================
          UPLOAD STATE
      ====================================================== */}

      {!file && (
        <>
          <UploadDropzone
            onFile={handleFile}
          />

          <SampleImages
            onSelect={handleFile}
          />
        </>
      )}


      {/* =====================================================
          IMAGE PREVIEW + SCAN
      ====================================================== */}

      {file && (
        <>
          <ImagePreview
            file={file}
            scanning={scanning}
            detections={
              result?.yolov8
                ?.detections || []
            }
          />

          <div className="scan-actions">

            <ScanButton
              disabled={scanning}
              scanning={scanning}
              onClick={
                handleDetection
              }
            />

            <button
              type="button"
              className="reset-button"
              onClick={
                handleReset
              }
              disabled={scanning}
            >
              Reset
            </button>

          </div>
        </>
      )}


      {/* =====================================================
          ERROR STATE
      ====================================================== */}

      {error && (
        <div className="scan-error">

          <div className="scan-error-icon">
            !
          </div>

          <div className="scan-error-content">

            <strong>
              Detection failed
            </strong>

            <span>
              {error}
            </span>

          </div>

          <button
            type="button"
            onClick={
              handleDetection
            }
            disabled={scanning}
            className="retry-button"
          >
            Retry
          </button>

        </div>
      )}


      {/* =====================================================
          RESULTS
      ====================================================== */}

      {result && (
        <section
          className="results-section"
        >

          {/* =================================================
              FINAL VERDICT
          ================================================== */}

          <ResultBanner
            detected={
              result.pothole_detected
            }
          />


          {/* =================================================
              MODEL RESULTS
          ================================================== */}

          <div className="model-grid">

            {/* ===============================================
                VGG19
            ================================================ */}

            <ModelCard
              title="VGG19"
              tag="CLASSIFIER"
              status={
                result.vgg19?.label ===
                "pothole"
                  ? "danger"
                  : "safe"
              }
            >

              <MetricRow
                label="Prediction"
                value={
                  result.vgg19?.label ||
                  "unknown"
                }
                highlight
              />

              <MetricRow
                label="Confidence"
                value={
                  result.vgg19
                    ?.confidence != null
                    ? `${(
                        result.vgg19
                          .confidence *
                        100
                      ).toFixed(1)}%`
                    : "0.0%"
                }
              />

              <MetricRow
                label="Task"
                value="Binary Classification"
              />

            </ModelCard>


            {/* ===============================================
                YOLOv8
            ================================================ */}

            <ModelCard
              title="YOLOv8"
              tag="DETECTOR"
              status={
                (result.yolov8
                  ?.num_detections || 0) >
                0
                  ? "danger"
                  : "safe"
              }
            >

              <MetricRow
                label="Potholes"
                value={
                  result.yolov8
                    ?.num_detections ||
                  0
                }
                highlight
              />

              <MetricRow
                label="Highest Confidence"
                value={
                  getHighestYoloConfidence()
                }
              />

              <MetricRow
                label="Processing Time"
                value={
                  result.processing_time_sec !=
                  null
                    ? `${result.processing_time_sec}s`
                    : "—"
                }
              />

            </ModelCard>

          </div>


          {/* =================================================
              DETECTION SUMMARY
          ================================================== */}

          <div
            className="detection-summary"
          >

            <div className="summary-title">
              Detection Summary
            </div>

            <div className="summary-grid">

              {/* OBJECTS DETECTED */}

              <div className="summary-item">

                <span>
                  Objects Detected
                </span>

                <strong>
                  {
                    result.yolov8
                      ?.num_detections ||
                    0
                  }
                </strong>

              </div>


              {/* CLASSIFIER CONFIDENCE */}

              <div className="summary-item">

                <span>
                  Classifier Confidence
                </span>

                <strong>
                  {result.vgg19
                    ?.confidence != null
                    ? `${(
                        result.vgg19
                          .confidence *
                        100
                      ).toFixed(1)}%`
                    : "0.0%"}
                </strong>

              </div>


              {/* DETECTOR CONFIDENCE */}

              <div className="summary-item">

                <span>
                  Detector Confidence
                </span>

                <strong>
                  {
                    getHighestYoloConfidence()
                  }
                </strong>

              </div>


              {/* PROCESSING TIME */}

              <div className="summary-item">

                <span>
                  Processing Time
                </span>

                <strong>
                  {
                    result.processing_time_sec !=
                    null
                      ? `${result.processing_time_sec}s`
                      : "—"
                  }
                </strong>

              </div>

            </div>

          </div>

        </section>
      )}

    </main>
  );
}


export default Dashboard;