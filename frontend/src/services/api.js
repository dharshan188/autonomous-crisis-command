// frontend/src/services/api.js

const API_BASE = "http://127.0.0.1:8000";

/**
 * Submit new crisis to backend
 */
export async function submitCrisis(text, approved = false) {
  const body = {
    crises: [text],
    approved: approved,
  };

  const res = await fetch(`${API_BASE}/crisis_command`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => null);
    throw new Error(
      `Request failed: ${res.status} ${res.statusText}${
        errText ? " - " + errText : ""
      }`
    );
  }

  return await res.json();
}

/**
 * Check crisis approval/execution status
 */
export async function getCrisisStatus(crisisId) {
  const res = await fetch(`${API_BASE}/crisis_status/${crisisId}`, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch crisis status");
  }

  return await res.json();
}