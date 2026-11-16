
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000"
).replace(/\/+$/, "");

async function parseResponse(response, fallbackMessage) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || fallbackMessage);
  }

  return data;
}

export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  return parseResponse(response, "Backend health check failed.");
}

export async function getHazards() {
  const response = await fetch(`${API_BASE_URL}/api/hazards`);
  return parseResponse(response, "Could not load road hazards.");
}

export async function getReports() {
  const response = await fetch(`${API_BASE_URL}/api/reports`);
  return parseResponse(response, "Could not load authority reports.");
}

export async function createReport(report) {
  const response = await fetch(`${API_BASE_URL}/api/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(report),
  });

  return parseResponse(response, "Could not create authority report.");
}

export async function updateReportStatus(reportId, status) {
  const response = await fetch(`${API_BASE_URL}/api/reports/${reportId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report_status: status }),
  });

  return parseResponse(response, "Could not update report status.");
}

