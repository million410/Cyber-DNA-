// Legacy service helper retained for older imports; use same-origin API routing in production.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/+$/, "");

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Dashboard
export async function getDashboard() {
  return request("/dashboard/overview");
}

// Events
export async function getEvents() {
  return request("/events");
}

// Alerts
export async function getAlerts() {
  return request("/alerts");
}

export async function getAlert(id) {
  return request(`/alerts/${encodeURIComponent(id)}`);
}

// Users
export async function getUsers() {
  return request("/users");
}

// Hosts / Devices
export async function getHosts() {
  return request("/hosts");
}

// Detection rules
export async function getRules() {
  return request("/rules");
}

// Backend health check
export async function getHealth() {
  return request("/health");
}
