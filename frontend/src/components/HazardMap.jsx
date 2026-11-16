import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";

const INDIA_CENTER = [22.9734, 78.6569];

function getSeverity(value) {
  const severity = String(value || "medium").toLowerCase();
  return ["low", "medium", "high", "critical"].includes(severity) ? severity : "medium";
}

function makeHazardIcon(severity) {
  return L.divIcon({
    className: "roadguard-marker-wrapper",
    html: `<span class="roadguard-marker roadguard-marker-${getSeverity(severity)}"></span>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -12],
  });
}

function MapViewport({ points }) {
  const map = useMap();

  useEffect(() => {
    if (points.length === 1) {
      map.setView(points[0].position, 14);
    } else if (points.length > 1) {
      const bounds = L.latLngBounds(points.map((point) => point.position));
      map.fitBounds(bounds, { padding: [36, 36], maxZoom: 15 });
    } else {
      map.setView(INDIA_CENTER, 5);
    }
    const timer = window.setTimeout(() => map.invalidateSize(), 100);
    return () => window.clearTimeout(timer);
  }, [map, points]);

  return null;
}

export default function HazardMap({ hazards = [] }) {
  const points = useMemo(() => hazards.flatMap((hazard) => {
    const latitude = Number(hazard.latitude);
    const longitude = Number(hazard.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return [];
    return [{ ...hazard, position: [latitude, longitude] }];
  }), [hazards]);

  const initialCenter = points.length ? points[0].position : INDIA_CENTER;

  return (
    <div className="roadguard-map-shell">
      <div className="roadguard-map-legend" aria-label="Hazard severity legend">
        <span><i className="roadguard-legend-dot low" /> Low</span>
        <span><i className="roadguard-legend-dot medium" /> Medium</span>
        <span><i className="roadguard-legend-dot high" /> High</span>
        <span><i className="roadguard-legend-dot critical" /> Critical</span>
        <strong>{points.length} mapped hazard{points.length === 1 ? "" : "s"}</strong>
      </div>
      <MapContainer center={initialCenter} zoom={points.length ? 13 : 5} scrollWheelZoom className="roadguard-leaflet-map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapViewport points={points} />
        {points.map((hazard) => (
          <Marker key={hazard.id} position={hazard.position} icon={makeHazardIcon(hazard.severity)}>
            <Popup>
              <div className="roadguard-map-popup">
                <strong>Road hazard #{hazard.id}</strong>
                <span>Severity: {hazard.severity || "Unspecified"}</span>
                <span>Confidence: {hazard.confidence == null ? "—" : `${(Number(hazard.confidence) * 100).toFixed(1)}%`}</span>
                <span>Latitude: {hazard.position[0].toFixed(6)}</span>
                <span>Longitude: {hazard.position[1].toFixed(6)}</span>
                <span>{hazard.description || "Pothole detected"}</span>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      {points.length === 0 && <p className="roadguard-map-empty">No valid saved coordinates yet. Add a hazard with latitude and longitude to see its marker.</p>}
    </div>
  );
}