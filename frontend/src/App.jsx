import { useEffect, useRef, useState } from "react";



import {



  Activity,



  AlertTriangle,



  ArrowUpRight,



  Bell,



  Camera,



  CheckCircle2,



  ChevronDown,



  CircleHelp,



  FileText,



  Gauge,



  LayoutDashboard,



  MapPin,



  Menu,



  ScanSearch,



  Settings,



  ShieldCheck,



  Upload,



  X,



} from "lucide-react";



import "./App.css";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents, useMap } from "react-leaflet";



import {



  getHazards,



  getReports,



  createReport,



  updateReportStatus,



} from "./services/api";



const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000").replace(/\/+$/, "");



let scanAudioContext;



function playScanSound(type) {



  try {



    const AudioContextClass = window.AudioContext || window.webkitAudioContext;



    if (!AudioContextClass) return;



    if (!scanAudioContext) scanAudioContext = new AudioContextClass();



    const ctx = scanAudioContext;



    if (ctx.state === "suspended") ctx.resume().catch(() => {});



    const tones = type === "start"



      ? [{ frequency: 880, delay: 0, duration: 0.09 }]



      : [



          { frequency: 523.25, delay: 0, duration: 0.13 },



          { frequency: 783.99, delay: 0.16, duration: 0.18 },



        ];



    tones.forEach(({ frequency, delay, duration }) => {



      const oscillator = ctx.createOscillator();



      const gain = ctx.createGain();



      const startTime = ctx.currentTime + delay;



      const endTime = startTime + duration;



      oscillator.type = "sine";



      oscillator.frequency.setValueAtTime(frequency, startTime);



      gain.gain.setValueAtTime(0.0001, startTime);



      gain.gain.exponentialRampToValueAtTime(0.16, startTime + 0.015);



      gain.gain.exponentialRampToValueAtTime(0.0001, endTime);



      oscillator.connect(gain);



      gain.connect(ctx.destination);



      oscillator.start(startTime);



      oscillator.stop(endTime);



    });



  } catch (error) {



    console.warn("Scan sound unavailable:", error);



  }



}



function App() {



  const [activePage, setActivePage] = useState("Overview");



  const [image, setImage] = useState(null);



  const [backendStatus, setBackendStatus] = useState("Checking");



  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);



  const [scanResult, setScanResult] = useState(null);



  const [scanning, setScanning] = useState(false);



  const [scanError, setScanError] = useState("");



  const [latitude, setLatitude] = useState("");



  const [longitude, setLongitude] = useState("");



  const [saveMessage, setSaveMessage] = useState("");



  const [savingHazards, setSavingHazards] = useState(false);



  const [imagesScanned, setImagesScanned] = useState(0);



  const inputRef = useRef(null);



  const [hazards, setHazards] = useState([]);



  const [reports, setReports] = useState([]);



  const [roadDataLoading, setRoadDataLoading] = useState(true);



  const [roadDataError, setRoadDataError] = useState("");



  const [reportHazardId, setReportHazardId] = useState("");



  const [authorityName, setAuthorityName] = useState("");



  const [reportDescription, setReportDescription] = useState("");



  const [reportSubmitting, setReportSubmitting] = useState(false);



  const [reportMessage, setReportMessage] = useState("");



  async function refreshRoadData() {



    setRoadDataLoading(true);



    setRoadDataError("");



    try {



      const [hazardData, reportData] = await Promise.all([getHazards(), getReports()]);



      setHazards(hazardData.hazards || []);



      setReports(reportData.reports || []);



    } catch (error) {



      setRoadDataError(error.message || "Could not load road data.");



    } finally {



      setRoadDataLoading(false);



    }



  }



  async function handleCreateReport(event) {



    event.preventDefault();



    setReportMessage("");



    if (!reportHazardId || !authorityName.trim() || !reportDescription.trim()) {



      setReportMessage("Please complete all report fields.");



      return;



    }



    setReportSubmitting(true);



    try {



      await createReport({ hazard_id: Number(reportHazardId), authority_name: authorityName.trim(), report_description: reportDescription.trim() });



      setReportMessage("Report created successfully.");



      setReportHazardId("");



      setAuthorityName("");



      setReportDescription("");



      await refreshRoadData();



    } catch (error) {



      setReportMessage(error.message || "Could not create report.");



    } finally {



      setReportSubmitting(false);



    }



  }



  async function handleReportStatusChange(reportId, status) {



    setReportMessage("");



    try {



      await updateReportStatus(reportId, status);



      await refreshRoadData();



      setReportMessage("Report status updated.");



    } catch (error) {



      setReportMessage(error.message || "Could not update report status.");



    }



  }



  useEffect(() => {



    refreshRoadData();



  }, []);



  useEffect(() => {



    let active = true;



    async function checkBackend() {



      try {



        const response = await fetch(`${API_BASE_URL}/api/health`);



        if (!response.ok) throw new Error("Backend unavailable");



        if (active) setBackendStatus("Connected");



      } catch {



        if (active) setBackendStatus("Offline");



      }



    }



    checkBackend();



    const intervalId = window.setInterval(checkBackend, 15000);



    return () => {



      active = false;



      window.clearInterval(intervalId);



    };



  }, []);



  useEffect(() => {



    return () => {



      if (image?.url) URL.revokeObjectURL(image.url);



    };



  }, [image]);



  function handleImageChange(event) {



    const file = event.target.files?.[0];



    if (!file) return;



    if (!file.type.startsWith("image/")) {



      setScanError("Please select a valid image file.");



      event.target.value = "";



      return;



    }



    if (file.size > 8 * 1024 * 1024) {



      setScanError("Please select an image smaller than 8 MB.");



      event.target.value = "";



      return;



    }



    setScanError("");



    setScanResult(null);



    const previewUrl = URL.createObjectURL(file);



    setImage({ file, url: previewUrl });



  }



  function clearImage() {



    setImage(null);



    setScanResult(null);



    setScanError("");



    if (inputRef.current) inputRef.current.value = "";



  }



  async function saveDetectionsToDatabase(detections) {



    if (!detections.length) {



      setSaveMessage("No potholes detected; nothing to save.");



      return;



    }



    const lat = Number(latitude);



    const lon = Number(longitude);



    if (latitude.trim() === "" || longitude.trim() === "" || !Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {



      setSaveMessage("Scan completed, but enter valid latitude and longitude to save detections.");



      return;



    }



    setSavingHazards(true);



    setSaveMessage("");



    try {



      const results = await Promise.all(detections.map(async (detection) => {



        const confidence = Number(detection.confidence);



        if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {



          throw new Error("A detection has an invalid confidence value; nothing was saved.");



        }



        const response = await fetch(`${API_BASE_URL}/api/hazards`, {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify({



            latitude: lat,



            longitude: lon,



            severity: "medium",



            confidence,



            description: `${detection.class || "Pothole"} detected by AI model`,



          }),



        });



        const result = await response.json().catch(() => ({}));



        if (!response.ok) throw new Error(result.error || "Could not save a detection to the database.");



        return result;



      }));



      await refreshRoadData();



      setSaveMessage(`${results.length} detection(s) saved successfully.`);



    } catch (error) {



      setSaveMessage(error.message || "Failed to save detections.");



    } finally {



      setSavingHazards(false);



    }



  }



  async function handleScan() {



    if (!image?.file) {



      setScanError("Please choose a road image first.");



      return;



    }



    if (backendStatus !== "Connected") {



      setScanError("The detection API is offline. Start the Flask backend and try again.");



      return;



    }



    playScanSound("start");



    setScanning(true);



    setScanError("");



    setScanResult(null);



    try {



      const formData = new FormData();



      formData.append("image", image.file);



      const response = await fetch(`${API_BASE_URL}/api/scan`, {



        method: "POST",



        body: formData,



      });



      const data = await response.json().catch(() => ({}));



      if (!response.ok) {



        throw new Error(data.error || `Image scan failed (HTTP ${response.status}).`);



      }



      // Current Flask dual-model response: { vgg19, yolov8, processing_time_sec }

      // Keep compatibility with the older YOLO-only response shape as well.

      const yolo = data.yolov8 || {};

      const vgg = data.vgg19 || {};

      const detections = Array.isArray(data.detections)

        ? data.detections

        : Array.isArray(yolo.detections)

          ? yolo.detections

          : [];

      const detectionCount = Number.isFinite(Number(data.detection_count))

        ? Number(data.detection_count)

        : Number(yolo.num_detections ?? detections.length);



      if (!data.success && !data.yolov8 && !Array.isArray(data.detections)) {

        throw new Error("The API response did not contain YOLOv8/VGG19 results.");

      }

      if (!Number.isFinite(detectionCount)) {

        throw new Error("The API returned an invalid detection count.");

      }



      const normalizedResult = {

        ...data,

        detections,

        detection_count: detectionCount,

        vgg19: vgg,

        yolov8: {

          ...yolo,

          num_detections: detectionCount,

          highest_confidence: Number(yolo.highest_confidence ?? (detections.length

            ? Math.max(...detections.map((item) => Number(item.confidence) || 0))

            : 0)),

        },

      };



      setScanResult(normalizedResult);

      setImagesScanned((count) => count + 1);

      playScanSound("complete");

      await saveDetectionsToDatabase(detections);



    } catch (error) {



      setScanError(error.message || "Unable to scan this image. Check the Flask terminal.");



    } finally {



      setScanning(false);



    }



  }



  const navigation = [



    { name: "Overview", icon: LayoutDashboard },



    { name: "Detect Damage", icon: ScanSearch },



    { name: "Road Intelligence", icon: MapPin },



    { name: "Reports", icon: FileText },



  ];



  function selectPage(name) {



    setActivePage(name);



    setMobileMenuOpen(false);



    if (name === "Detect Damage") {



      window.setTimeout(() => {



        document



          .getElementById("image-upload")



          ?.scrollIntoView({ behavior: "smooth", block: "center" });



      }, 50);



    }



  }



  const totalDetections = scanResult?.detection_count ?? 0;



  return (



    <div className="app-shell">



      {mobileMenuOpen && (



        <button



          className="mobile-backdrop"



          aria-label="Close navigation"



          onClick={() => setMobileMenuOpen(false)}



        />



      )}



      <aside className={`sidebar ${mobileMenuOpen ? "sidebar-open" : ""}`}>



        <div className="brand">



          <div className="brand-icon">



            <ShieldCheck size={24} />



          </div>



          <div>



            <h2>



              RoadGuard<span>-AI</span>



            </h2>



            <p>ROAD INTELLIGENCE</p>



          </div>



          <button



            className="icon-button mobile-close"



            aria-label="Close menu"



            onClick={() => setMobileMenuOpen(false)}



          >



            <X size={19} />



          </button>



        </div>



        <div className="workspace-label">WORKSPACE</div>



        <nav className="navigation">



          {navigation.map(({ name, icon: Icon }) => (



            <button



              key={name}



              className={`nav-item ${activePage === name ? "nav-active" : ""}`}



              onClick={() => selectPage(name)}



            >



              <Icon size={19} />



              <span>{name}</span>



            </button>



          ))}



        </nav>



        <div className="sidebar-bottom">



          <div className="sidebar-status">



            <div className="status-icon">



              <Activity size={19} />



            </div>



            <div>



              <strong>System status</strong>



              <p>



                <span



                  className={`status-dot ${



                    backendStatus === "Connected"



                      ? "dot-green"



                      : backendStatus === "Offline"



                        ? "dot-red"



                        : ""



                  }`}



                />



                {backendStatus === "Connected"



                  ? "API connected"



                  : backendStatus === "Offline"



                    ? "API offline"



                    : "Checking API"}



              </p>



            </div>



          </div>



          <button className="nav-item utility-item" onClick={() => selectPage("Settings")}>



            <Settings size={19} />



            <span>Settings</span>



          </button>



          <button className="nav-item utility-item" onClick={() => selectPage("Help")}>



            <CircleHelp size={19} />



            <span>Help & information</span>



          </button>



          <div className="sidebar-footer">



            <span className="footer-pulse" />



            Software-only AI platform



          </div>



        </div>



      </aside>



      <main className="main-content">



        <header className="topbar">



          <div className="topbar-left">



            <button



              className="icon-button menu-toggle"



              aria-label="Open navigation"



              onClick={() => setMobileMenuOpen(true)}



            >



              <Menu size={21} />



            </button>



            <div>



              <p className="breadcrumb">Workspace / {activePage}</p>



              <h1>{activePage}</h1>



            </div>



          </div>



          <div className="topbar-actions">



            <span className="environment-label">



              <span className={`status-dot ${backendStatus === "Connected" ? "dot-green" : ""}`} />



              Development



            </span>



            <button className="icon-button" aria-label="Notifications">



              <Bell size={19} />



            </button>



            <div className="user-avatar">RG</div>



            <ChevronDown size={15} className="chevron" />



          </div>



        </header>



        <div className="page-content">



          {activePage === "Overview" || activePage === "Detect Damage" ? (



            <>



              <section className="welcome-row">



                <div>



                  <div className="eyebrow">



                    <span className="eyebrow-line" />



                    INTELLIGENT ROAD MONITORING



                  </div>



                  <h2>



                    Building safer roads,



                    <br />



                    <span>one detection at a time.</span>



                  </h2>



                  <p className="welcome-description">



                    Detect road damage, preserve hazard locations and build predictive road intelligence.



                  </p>



                </div>



                <div className="welcome-decoration">



                  <div className="decoration-ring ring-one" />



                  <div className="decoration-ring ring-two" />



                  <div className="decoration-center">



                    <ShieldCheck size={36} />



                  </div>



                  <span className="decoration-node node-one" />



                  <span className="decoration-node node-two" />



                  <span className="decoration-node node-three" />



                </div>



              </section>



              <section className="stats-grid">



                <StatCard



                  label="Images scanned"



                  value={String(imagesScanned)}



                  description="Successful scans this session"



                  icon={Camera}



                  color="blue"



                />



                <StatCard



                  label="Latest detections"



                  value={scanResult ? String(totalDetections) : "—"}



                  description={scanResult ? "From latest scan" : "Run a scan to see results"}



                  icon={ScanSearch}



                  color="purple"



                />



                <StatCard



                  label="Saved road hazards"



                  value={roadDataLoading ? "…" : String(hazards.length)}



                  description="Records loaded from database"



                  icon={MapPin}



                  color="orange"



                />



                <StatCard



                  label="Reports submitted"



                  value={roadDataLoading ? "…" : String(reports.filter((report) => report.report_status === "submitted").length)}



                  description="Reports marked as submitted"



                  icon={FileText}



                  color="green"



                />



              </section>



              <section className="content-grid">



                <div className="panel upload-panel" id="image-upload">



                  <div className="panel-heading">



                    <div>



                      <div className="section-kicker">COMPUTER VISION</div>



                      <h3>Road damage detection</h3>



                      <p>Upload a road image and run the trained pothole model.</p>



                    </div>



                    <div className="heading-icon">



                      <ScanSearch size={21} />



                    </div>



                  </div>



                  <div className={`upload-zone ${image ? "has-image" : ""}`}>



                    {image ? (



                      <div className="image-preview">



                        <img src={image.url} alt="Selected road for inspection" />



                        <button



                          className="remove-image"



                          aria-label="Remove selected image"



                          onClick={clearImage}



                          disabled={scanning}



                        >



                          <X size={17} />



                        </button>



                        <div className="image-file-label">



                          <CheckCircle2 size={16} />



                          Image selected



                        </div>



                      </div>



                    ) : (



                      <>



                        <div className="upload-icon">



                          <Upload size={25} />



                        </div>



                        <h4>Upload your road image</h4>



                        <p>Select an image from your computer to inspect it for potholes.</p>



                        <button className="primary-button" onClick={() => inputRef.current?.click()}>



                          <Upload size={17} />



                          Choose image



                        </button>



                        <span className="upload-hint">JPG, PNG or WEBP · Maximum 8 MB</span>



                      </>



                    )}



                    <input



                      ref={inputRef}



                      type="file"



                      accept="image/jpeg,image/png,image/webp"



                      hidden



                      onChange={handleImageChange}



                    />



                  </div>



                  {image && (



                    <div className="selected-file">



                      <div className="file-details">



                        <Camera size={18} />



                        <div>



                          <strong>{image.file.name}</strong>



                          <span>{(image.file.size / (1024 * 1024)).toFixed(2)} MB</span>



                        </div>



                      </div>



                      <button className="secondary-button" onClick={clearImage} disabled={scanning}>



                        Remove image



                      </button>



                    </div>



                  )}



                  <div className="report-form scan-location-form">



                    <label htmlFor="scan-latitude">Image location — latitude</label>



                    <input id="scan-latitude" type="number" step="any" min="-90" max="90" placeholder="e.g. 22.5726" value={latitude} onChange={(event) => setLatitude(event.target.value)} />



                    <label htmlFor="scan-longitude">Image location — longitude</label>



                    <input id="scan-longitude" type="number" step="any" min="-180" max="180" placeholder="e.g. 88.3639" value={longitude} onChange={(event) => setLongitude(event.target.value)} />



                  </div>



                  <div className="scan-controls">



                    <button



                      className="primary-button"



                      onClick={handleScan}



                      disabled={!image || scanning || backendStatus !== "Connected"}



                    >



                      <ScanSearch size={17} />



                      {scanning ? "Scanning road..." : "Detect road damage"}



                    </button>



                    {scanning && (



                      <p className="scan-progress" role="status">



                        The AI model is analysing your image. Please wait.



                      </p>



                    )}



                    {scanError && (



                      <p className="scan-error" role="alert">



                        {scanError}



                      </p>



                    )}



                    {backendStatus === "Offline" && (



                      <p className="scan-error">



                        Flask API is offline. Start the backend on port 5000, then retry.



                      </p>



                    )}



                    {saveMessage && (



                      <p className={saveMessage.includes("successfully") ? "report-message" : "scan-error"} role="status">



                        {saveMessage}



                      </p>



                    )}



                    {savingHazards && (



                      <p className="scan-progress" role="status">Saving detections to the database...</p>



                    )}



                  </div>



                  {scanResult && (



                    <div className="scan-results" aria-live="polite">



                      <div className="scan-results-heading">



                        <div>



                          <div className="section-kicker">MODEL OUTPUT</div>



                          <h3>Detection results</h3>



                        </div>



                        <span className="scan-count">



                          {scanResult.detection_count} detected



                        </span>



                      </div>



                      <div className="scan-summary-grid">



                        <div>



                          <span>Detections</span>



                          <strong>{scanResult.detection_count}</strong>



                        </div>



                        <div>



                          <span>Image dimensions</span>



                          <strong>



                            {scanResult.image_width} × {scanResult.image_height}



                          </strong>



                        </div>



                      </div>



                      {scanResult.annotated_image && (



                        <img



                          className="scan-result-image"



                          src={scanResult.annotated_image}



                          alt="AI pothole detections shown on the road image"



                        />



                      )}



                      {scanResult.detections.length > 0 ? (



                        <div className="detection-list">



                          <h4>Detected regions</h4>



                          {scanResult.detections.map((detection, index) => (



                            <div className="detection-row" key={`${index}-${detection.class}`}>



                              <div>



                                <strong>



                                  {detection.class || "Road damage"} {index + 1}



                                </strong>



                                <span>



                                  Confidence: {(Number(detection.confidence) * 100).toFixed(1)}%



                                </span>



                              </div>



                              <span className="detection-confidence">



                                {(Number(detection.confidence) * 100).toFixed(1)}%



                              </span>



                            </div>



                          ))}



                        </div>



                      ) : (



                        <p className="scan-no-detections">



                          No potholes were detected in this image. This does not guarantee the road is damage-free.



                        </p>



                      )}



                      <p className="scan-disclaimer">



                        Confidence is the model's score, not a guarantee that every detection is correct.



                        This model currently detects potholes; crack detection is not yet integrated.



                      </p>



                    </div>



                  )}



                  {scanResult && scanResult.vgg19 && scanResult.yolov8 && (

                    <ModelComparisonPanel result={scanResult} />

                  )}



                  <div className="model-notice">



                    <div className="notice-icon">



                      <Activity size={18} />



                    </div>



                    <div>



                      <strong>



                        {backendStatus === "Connected"



                          ? "Pothole detection API connected"



                          : "Waiting for detection API"}



                      </strong>



                      <p>



                        {backendStatus === "Connected"



                          ? "Your selected image is sent to the trained YOLO model when you click Detect road damage."



                          : "Keep the Flask backend running to enable real image inference."}



                      </p>



                    </div>



                  </div>



                </div>



                <div className="panel intelligence-panel">



                  <div className="panel-heading">



                    <div>



                      <div className="section-kicker">SYSTEM OVERVIEW</div>



                      <h3>Road intelligence</h3>



                      <p>Platform modules and their current status.</p>



                    </div>



                    <div className="heading-icon">



                      <Gauge size={21} />



                    </div>



                  </div>



                  <div className="module-list">



                    <ModuleRow



                      icon={Activity}



                      title="Backend API"



                      subtitle="Flask service"



                      status={backendStatus}



                      online={backendStatus === "Connected"}



                    />



                    <ModuleRow



                      icon={ScanSearch}



                      title="Pothole detection"



                      subtitle="Fine-tuned YOLO model"



                      status={backendStatus === "Connected" ? "Ready to scan" : "Offline"}



                      online={backendStatus === "Connected"}



                    />



                    <ModuleRow

                      icon={MapPin}

                      title="Geospatial memory"

                      subtitle="PostgreSQL hazard database"

                      status={

                        roadDataLoading

                          ? "Checking..."

                          : roadDataError

                            ? "Unavailable"

                            : "API connected"

                      }

                      online={!roadDataLoading && !roadDataError}

                    />



                    <ModuleRow

                      icon={FileText}

                      title="Authority reporting"

                      subtitle="Internal report workflow"

                      status={

                        roadDataLoading

                          ? "Checking..."

                          : roadDataError

                            ? "Unavailable"

                            : "API connected"

                      }

                      online={!roadDataLoading && !roadDataError}

                    />



                  </div>



                  <div className="progress-footer">



                    <div className="progress-copy">



                      <span>Development progress</span>



                      <strong>Detection, hazard and report APIs</strong>



                    </div>



                    <div className="progress-track">



                      <div className="progress-fill" />



                    </div>



                    <p>

                      {roadDataLoading

                        ? "Checking database and reporting services..."

                        : roadDataError

                          ? "Database or reporting service needs attention. Check the backend connection."

                          : "Hazard database and internal authority report APIs are connected."}

                    </p>



                  </div>



                </div>



              </section>



              <section className="panel hazards-panel">



                <div className="panel-heading hazards-heading">



                  <div>



                    <div className="section-kicker">ROAD MEMORY</div>



                    <h3>Recent road hazards</h3>



                    <p>Recent hazard records loaded from the backend database.</p>



                  </div>



                  <button className="secondary-button" onClick={() => selectPage("Road Intelligence")}>



                    View road intelligence <ArrowUpRight size={16} />



                  </button>



                </div>



                <div className="table-scroll">



                  <table>



                    <thead>



                      <tr>



                        <th>REPORT ID</th>



                        <th>DEFECT TYPE</th>



                        <th>LOCATION</th>



                        <th>SEVERITY</th>



                        <th>RECORD STATUS</th>



                      </tr>



                    </thead>



                    <tbody>



                      {!roadDataLoading && hazards.length === 0 && (



                        <tr><td colSpan={5}>No saved hazards yet.</td></tr>



                      )}



                      {hazards.slice(0, 5).map((hazard) => (



                        <tr key={hazard.id}>



                          <td className="report-id">{hazard.id}</td>



                          <td>Road hazard</td>



                          <td>{Number(hazard.latitude).toFixed(5)}, {Number(hazard.longitude).toFixed(5)}</td>



                          <td><span className={`severity severity-${String(hazard.severity || "medium").toLowerCase()}`}><span />{hazard.severity || "Unspecified"}</span></td>



                          <td><span className="sample-tag">Database record</span></td>



                        </tr>



                      ))}



                    </tbody>



                  </table>



                </div>



                <div className="sample-disclaimer">



                  <AlertTriangle size={15} />



                  Showing saved database records. Confirm test records before treating them as real hazards.



                </div>



              </section>



              <footer className="page-footer">



                <span><ShieldCheck size={15} /> RoadGuard-AI</span>



                <span>AI-assisted road safety · Development build</span>



              </footer>



            </>



          ) : activePage === "Road Intelligence" ? (



            <RoadIntelligencePage hazards={hazards} loading={roadDataLoading} error={roadDataError} onRefresh={refreshRoadData} setLatitude={setLatitude} setLongitude={setLongitude} onUseCoordinates={() => selectPage("Detect Damage")} />



          ) : activePage === "Reports" ? (



            <ReportsPage



              hazards={hazards} reports={reports} loading={roadDataLoading} error={roadDataError}



              reportHazardId={reportHazardId} setReportHazardId={setReportHazardId}



              authorityName={authorityName} setAuthorityName={setAuthorityName}



              reportDescription={reportDescription} setReportDescription={setReportDescription}



              reportSubmitting={reportSubmitting} reportMessage={reportMessage}



              onCreateReport={handleCreateReport} onStatusChange={handleReportStatusChange} onRefresh={refreshRoadData}



            />



          ) : (



            <PlaceholderPage page={activePage} onBack={() => selectPage("Overview")} />



          )}



        </div>



      </main>



    </div>



  );



}



function GraphBar({ label, value, max = 100, valueLabel, tone = "blue" }) {
  const numeric = Number(value);
  const width = Number.isFinite(numeric) && max > 0
    ? Math.max(0, Math.min(100, (numeric / max) * 100))
    : 0;

  return (
    <div className="graph-bar-row">
      <div className="graph-bar-heading">
        <span>{label}</span>
        <strong>{valueLabel}</strong>
      </div>
      <div className="graph-bar-track" role="img" aria-label={`${label}: ${valueLabel}`}>
        <span className={`graph-bar-fill graph-${tone}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function ModelComparisonPanel({ result }) {
  const vgg = result.vgg19 || {};
  const yolo = result.yolov8 || {};
  const yoloConfidence = Number(yolo.highest_confidence);
  const vggConfidence = Number(vgg.confidence);
  const yoloTime = Number(yolo.inference_time_ms);
  const vggTime = Number(vgg.inference_time_ms);
  const totalTime = Number(result.processing_time_sec);
  const yoloCount = Number(yolo.num_detections ?? result.detection_count ?? 0);
  const maxTime = Math.max(
    Number.isFinite(yoloTime) ? yoloTime : 0,
    Number.isFinite(vggTime) ? vggTime : 0,
    1
  );

  return (
    <section className="model-comparison panel" aria-live="polite">
      <div className="panel-heading">
        <div>
          <div className="section-kicker">PER-SCAN MODEL BENCHMARK</div>
          <h3>YOLOv8 vs VGG19</h3>
          <p>Both models processed the same uploaded image. Compare their outputs below.</p>
        </div>
        <span className="scan-count">Live scan comparison</span>
      </div>

      <div className="comparison-model-grid">
        <article className="comparison-model-card">
          <h4>YOLOv8 <span>Object detector</span></h4>
          <div className="comparison-big-value">{yoloCount}</div>
          <p>pothole regions detected</p>
          <div className="comparison-verdict">
            {yoloCount > 0 ? "Pothole region(s) found" : "No pothole boxes returned"}
          </div>
        </article>

        <article className="comparison-model-card">
          <h4>VGG19 <span>Binary classifier</span></h4>
          <div className="comparison-big-value comparison-label">{vgg.label || "No result"}</div>
          <p>image-level classification</p>
          <div className="comparison-verdict">
            {vgg.label === "pothole"
              ? "Classified as pothole"
              : vgg.label === "no_pothole"
                ? "Classified as background"
                : "Classification unavailable"}
          </div>
        </article>
      </div>

      <div className="comparison-charts-grid">
        <article className="comparison-chart-card">
          <div className="chart-title-row">
            <div>
              <h4>Model confidence</h4>
              <p>Reported confidence for this image</p>
            </div>
            <span className="chart-unit">%</span>
          </div>
          {Number.isFinite(yoloConfidence) && (
            <GraphBar
              label="YOLOv8 detection"
              value={yoloConfidence * 100}
              valueLabel={`${(yoloConfidence * 100).toFixed(1)}%`}
              tone="blue"
            />
          )}
          {Number.isFinite(vggConfidence) && (
            <GraphBar
              label={`VGG19 (${vgg.label || "classification"})`}
              value={vggConfidence * 100}
              valueLabel={`${(vggConfidence * 100).toFixed(1)}%`}
              tone="purple"
            />
          )}
          <p className="chart-footnote">
            These confidence scores describe different model outputs; they are not accuracy scores.
          </p>
        </article>

        <article className="comparison-chart-card">
          <div className="chart-title-row">
            <div>
              <h4>Inference time</h4>
              <p>Time spent by each model on this scan</p>
            </div>
            <span className="chart-unit">ms</span>
          </div>
          {Number.isFinite(yoloTime) && (
            <GraphBar
              label="YOLOv8"
              value={yoloTime}
              max={maxTime}
              valueLabel={`${yoloTime.toFixed(1)} ms`}
              tone="blue"
            />
          )}
          {Number.isFinite(vggTime) && (
            <GraphBar
              label="VGG19"
              value={vggTime}
              max={maxTime}
              valueLabel={`${vggTime.toFixed(1)} ms`}
              tone="purple"
            />
          )}
          <p className="chart-footnote">
            Lower inference time means faster per-image processing on this machine.
          </p>
        </article>
      </div>

      <div className="comparison-summary-grid">
        <div><span>Combined processing time</span><strong>{Number.isFinite(totalTime) ? `${totalTime.toFixed(2)} s` : "Not reported"}</strong></div>
        <div><span>YOLOv8 detections</span><strong>{yoloCount}</strong></div>
        <div><span>VGG19 decision</span><strong>{vgg.label || "Not reported"}</strong></div>
      </div>
      <p className="comparison-note">
        Single-image confidence and latency are not dataset accuracy. Precision, recall, F1-score and mAP must be calculated from a labelled evaluation set.
      </p>
    </section>
  );
}


function StatCard({ label, value, description, icon: Icon, color }) {



  return (



    <article className="stat-card">



      <div className={`stat-icon stat-${color}`}><Icon size={20} /></div>



      <p className="stat-label">{label}</p>



      <div className="stat-value">{value}</div>



      <p className="stat-description">{description}</p>



    </article>



  );



}



function ModuleRow({ icon: Icon, title, subtitle, status, online = false }) {



  return (



    <div className="module-row">



      <div className="module-icon"><Icon size={18} /></div>



      <div className="module-copy">



        <strong>{title}</strong>



        <span>{subtitle}</span>



      </div>



      <span className={`module-status ${online ? "module-online" : ""}`}>



        {online && <CheckCircle2 size={13} />}



        {status}



      </span>



    </div>



  );



}



function MapSizeFix() {
  const map = useMap();

  useEffect(() => {
    const refreshSize = () => map.invalidateSize({ pan: false });
    const firstFrame = window.requestAnimationFrame(refreshSize);
    const secondTimer = window.setTimeout(refreshSize, 300);
    window.addEventListener("resize", refreshSize);

    return () => {
      window.cancelAnimationFrame(firstFrame);
      window.clearTimeout(secondTimer);
      window.removeEventListener("resize", refreshSize);
    };
  }, [map]);

  return null;
}

function MapClickHandler({ onSelect }) {
  useMapEvents({
    click(event) {
      onSelect(event.latlng);
    },
  });
  return null;
}

function RoadIntelligencePage({
  hazards,
  loading,
  error,
  onRefresh,
  setLatitude,
  setLongitude,
  onUseCoordinates,
}) {
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [tileError, setTileError] = useState(false);
  const [tileReloadKey, setTileReloadKey] = useState(0);

  const validHazards = hazards.filter((hazard) => {
    const lat = Number(hazard.latitude);
    const lng = Number(hazard.longitude);
    return Number.isFinite(lat) && Number.isFinite(lng)
      && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
  });

  const mapCenter = validHazards.length
    ? [Number(validHazards[0].latitude), Number(validHazards[0].longitude)]
    : [22.9734, 78.6569];

  function selectMapPoint(latlng) {
    setSelectedPoint(latlng);
    setLatitude(latlng.lat.toFixed(6));
    setLongitude(latlng.lng.toFixed(6));
  }

  function retryMapTiles() {
    setTileError(false);
    setTileReloadKey((value) => value + 1);
  }

  return (
    <div className="road-data-stack">
      <section className="panel road-data-panel">
        <div className="panel-heading">
          <div>
            <div className="section-kicker">OPENSTREETMAP · LEAFLET</div>
            <h3>Road hazard map</h3>
            <p>Click anywhere on the map to choose coordinates for a new scan or hazard report.</p>
          </div>
          <span className="scan-count">OpenStreetMap</span>
        </div>

        <div className="map-instructions">
          <MapPin size={16} />
          <span>Click the map to select a location. Existing database hazards appear as markers.</span>
        </div>

        <div className="roadguard-map" style={{ height: 460, minHeight: 460, width: "100%", position: "relative" }}>
          <MapContainer
            key="roadguard-openstreetmap-map"
            center={mapCenter}
            zoom={validHazards.length ? 11 : 5}
            scrollWheelZoom={true}
            preferCanvas={true}
            style={{ height: "460px", minHeight: "460px", width: "100%" }}
          >
            <MapSizeFix />
            <TileLayer
              key={tileReloadKey}
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
              eventHandlers={{
                tileerror: () => setTileError(true),
                tileload: () => setTileError(false),
              }}
            />
            <MapClickHandler onSelect={selectMapPoint} />

            {validHazards.map((hazard) => (
              <CircleMarker
                key={hazard.id}
                center={[Number(hazard.latitude), Number(hazard.longitude)]}
                radius={8}
                pathOptions={{
                  color: "#ffffff",
                  weight: 2,
                  fillColor: "#dc4b58",
                  fillOpacity: 0.9,
                }}
              >
                <Popup>
                  <strong>Hazard #{hazard.id}</strong><br />
                  Severity: {hazard.severity || "Unspecified"}<br />
                  Confidence: {hazard.confidence == null
                    ? "—"
                    : `${(Number(hazard.confidence) * 100).toFixed(1)}%`}<br />
                  {hazard.description || "Pothole report"}
                </Popup>
              </CircleMarker>
            ))}

            {selectedPoint && (
              <CircleMarker
                center={[selectedPoint.lat, selectedPoint.lng]}
                radius={9}
                pathOptions={{
                  color: "#ffffff",
                  weight: 2,
                  fillColor: "#3157d5",
                  fillOpacity: 1,
                }}
              >
                <Popup>Selected location for your next scan</Popup>
              </CircleMarker>
            )}
          </MapContainer>

          {tileError && (
            <div
              className="map-tile-warning"
              role="status"
              style={{
                position: "absolute", zIndex: 1000, left: 12, right: 12, bottom: 12,
                display: "grid", gap: 8, padding: 12, borderRadius: 10,
                background: "rgba(255,255,255,0.96)", border: "1px solid #e5a1a1",
                color: "#7f1d1d", boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
              }}
            >
              <strong>Map tiles could not be loaded.</strong>
              <span>Check your internet connection or whether your network blocks tile.openstreetmap.org.</span>
              <button type="button" className="secondary-button" onClick={retryMapTiles}>Retry map tiles</button>
            </div>
          )}
        </div>

        <div className="map-selection-footer">
          <div>
            <strong>{selectedPoint ? "Selected coordinates" : "No location selected yet"}</strong>
            <span>
              {selectedPoint
                ? `${selectedPoint.lat.toFixed(6)}, ${selectedPoint.lng.toFixed(6)}`
                : "Select a point on the map to populate latitude and longitude."}
            </span>
          </div>
          <button
            className="primary-button"
            type="button"
            onClick={onUseCoordinates}
            disabled={!selectedPoint}
          >
            Use for scan
          </button>
        </div>
        <p className="road-data-note">
          Map tiles are provided by OpenStreetMap. An internet connection is required to load the map.
          {loading ? " Loading saved hazard markers…" : ` ${validHazards.length} saved hazard marker(s) available.`}
        </p>
        {error && <p className="scan-error">Hazard data could not be loaded: {error}</p>}
        <div className="map-actions-row" style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap", marginTop: 12 }}>
          <button className="secondary-button" type="button" onClick={onRefresh} disabled={loading}>
            {loading ? "Refreshing hazards…" : "Refresh hazard markers"}
          </button>
          <a href="https://www.openstreetmap.org" target="_blank" rel="noreferrer">Open OpenStreetMap</a>
        </div>
      </section>

      <section className="panel road-data-panel">
        <div className="panel-heading">
          <div>
            <div className="section-kicker">GEOSPATIAL DATABASE</div>
            <h3>Saved road hazards</h3>
            <p>Hazard records retrieved from the backend database.</p>
          </div>
          <button className="secondary-button" onClick={onRefresh} disabled={loading}>Refresh</button>
        </div>
        {loading && <p>Loading hazards…</p>}
        {error && <p className="scan-error">{error}</p>}
        {!loading && !error && hazards.length === 0 && <p>No saved hazards found. Save a hazard in the database first.</p>}
        {!loading && hazards.length > 0 && (
          <div className="table-wrap">
            <table className="road-data-table">
              <thead><tr><th>ID</th><th>Severity</th><th>Confidence</th><th>Latitude</th><th>Longitude</th><th>Description</th><th>Created</th></tr></thead>
              <tbody>{hazards.map((hazard) => (
                <tr key={hazard.id}>
                  <td>{hazard.id}</td>
                  <td>{hazard.severity || "—"}</td>
                  <td>{hazard.confidence == null ? "—" : `${(Number(hazard.confidence) * 100).toFixed(1)}%`}</td>
                  <td>{Number(hazard.latitude).toFixed(5)}</td>
                  <td>{Number(hazard.longitude).toFixed(5)}</td>
                  <td>{hazard.description || "—"}</td>
                  <td>{hazard.created_at ? new Date(hazard.created_at).toLocaleString() : "—"}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
        <p className="road-data-note">Verify that each record represents a real road hazard. Test records should not be treated as verified detections.</p>
      </section>
    </div>
  );
}

function ReportsPage({ hazards, reports, loading, error, reportHazardId, setReportHazardId, authorityName, setAuthorityName, reportDescription, setReportDescription, reportSubmitting, reportMessage, onCreateReport, onStatusChange, onRefresh }) {



  const statuses = ["pending", "submitted", "in_progress", "resolved", "rejected"];



  return (



    <div className="road-data-stack">



      <section className="panel road-data-panel">



        <div className="panel-heading"><div><div className="section-kicker">REPORT MANAGEMENT</div><h3>Create an authority report</h3><p>Link a saved hazard to an internal report record.</p></div></div>



        <form className="report-form" onSubmit={onCreateReport}>



          <label htmlFor="report-hazard">Saved hazard</label>



          <select id="report-hazard" value={reportHazardId} onChange={(event) => setReportHazardId(event.target.value)} required>



            <option value="">Choose a hazard</option>



            {hazards.map((hazard) => <option key={hazard.id} value={hazard.id}>Hazard #{hazard.id} — {hazard.severity || "Unspecified severity"}</option>)}



          </select>



          <label htmlFor="authority-name">Authority / department name</label>



          <input id="authority-name" value={authorityName} onChange={(event) => setAuthorityName(event.target.value)} placeholder="e.g. Municipal road maintenance department" required />



          <label htmlFor="report-description">Report description</label>



          <textarea id="report-description" value={reportDescription} onChange={(event) => setReportDescription(event.target.value)} placeholder="Describe the road hazard and required action" rows={4} required />



          <button className="primary-button" type="submit" disabled={reportSubmitting || hazards.length === 0}>{reportSubmitting ? "Creating report…" : "Create report"}</button>



          {reportMessage && <p role="status" className="report-message">{reportMessage}</p>}



        </form>



      </section>



      <section className="panel road-data-panel">



        <div className="panel-heading"><div><div className="section-kicker">REPORT TRACKING</div><h3>Authority reports</h3><p>Review saved reports and update their status.</p></div><button className="secondary-button" onClick={onRefresh} disabled={loading}>Refresh</button></div>



        {loading && <p>Loading reports…</p>}



        {error && <p className="scan-error">{error}</p>}



        {!loading && !error && reports.length === 0 && <p>No reports found. Create a report using a saved hazard above.</p>}



        {!loading && reports.length > 0 && (



          <div className="table-wrap"><table className="road-data-table reports-table">



            <thead><tr><th>Report ID</th><th>Hazard ID</th><th>Authority</th><th>Description</th><th>Status</th><th>Update status</th></tr></thead>



            <tbody>{reports.map((report) => <tr key={report.id}>



              <td>{report.id}</td><td>{report.hazard_id}</td><td>{report.authority_name || "—"}</td><td>{report.report_description || "—"}</td>



              <td>{report.report_status || "pending"}</td>



              <td><select aria-label={`Status for report ${report.id}`} value={report.report_status || "pending"} onChange={(event) => onStatusChange(report.id, event.target.value)}>{statuses.map((status) => <option key={status} value={status}>{status.replace("_", " ")}</option>)}</select></td>



            </tr>)}</tbody>



          </table></div>



        )}



        <p className="road-data-note">Status changes are stored in RoadGuard-AI. This interface does not itself send reports to an external government authority.</p>



      </section>



    </div>



  );



}



function PlaceholderPage({ page, onBack }) {



  const descriptions = {



    "Road Intelligence":



      "Saved road hazards are loaded from the geospatial database. Route-aware warnings are not implemented yet.",



    Reports:



      "Create and track internal road maintenance reports. External authority delivery is not configured.",



    Settings:



      "Application configuration and service settings will be added as the platform develops.",



    Help:



      "The pothole detection API, geospatial hazard database and internal report workflow are connected through the backend APIs.",



  };



  return (



    <section className="placeholder-page panel">



      <div className="placeholder-icon">



        {page === "Road Intelligence" ? (



          <MapPin size={32} />



        ) : page === "Reports" ? (



          <FileText size={32} />



        ) : page === "Settings" ? (



          <Settings size={32} />



        ) : (



          <CircleHelp size={32} />



        )}



      </div>



      <div className="section-kicker">ROADGUARD-AI MODULE</div>



      <h2>{page}</h2>



      <p>{descriptions[page] || "This module is planned for a future phase."}</p>



      <button className="primary-button" onClick={onBack}>Return to overview</button>



    </section>



  );



}



export default App;