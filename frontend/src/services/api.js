// frontend/src/services/api.js

const API_BASE = "http://127.0.0.1:8000";

// ==============================
// Internal Fetch Helper
// ==============================

async function apiFetch(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000); // 15s timeout

  try {
    const res = await fetch(`${API_BASE}${url}`, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      signal: controller.signal,
      ...options,
    });

    clearTimeout(timeout);

    if (!res.ok) {
      const errText = await res.text().catch(() => null);
      throw new Error(
        `Request failed: ${res.status} ${res.statusText}${
          errText ? " - " + errText : ""
        }`
      );
    }

    // Handle empty response
    if (res.status === 204) return null;

    return await res.json();
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("Request timeout. Server took too long to respond.");
    }
    throw err;
  }
}

// ==============================
// Crisis APIs
// ==============================

/**
 * Submit new crisis to backend
 */
export async function submitCrisis(text, approved = false) {
  return apiFetch("/crisis_command", {
    method: "POST",
    body: JSON.stringify({
      crises: [text],
      approved,
    }),
  });
}

/**
 * Check crisis approval/execution status
 */
export async function getCrisisStatus(crisisId) {
  return apiFetch(`/crisis_status/${crisisId}`, {
    method: "GET",
  });
}

/**
 * Fetch full crisis report (timeline + metadata)
 */
export async function getCrisisReport(crisisId) {
  return apiFetch(`/crisis_report/${crisisId}`, {
    method: "GET",
  });
}

/**
 * Fetch all reports
 */
export async function getAllReports() {
  return apiFetch("/all_reports", {
    method: "GET",
  });
}

/**
 * Generate download link for PDF report
 */
export function getReportDownloadUrl(crisisId) {
  return `${API_BASE}/download_report/${crisisId}`;
}