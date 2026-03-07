// Helper to determine backend base URL dynamically
const getBackendUrl = (port: number, path: string) => {
  if (typeof window === 'undefined') return `http://localhost:${port}${path}`;
  const host = window.location.hostname;
  return `http://${host}:${port}${path}`;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_NIDS_API_URL || getBackendUrl(8000, "/api/v1");
const AUTH_BASE_URL = process.env.NEXT_PUBLIC_NIDS_AUTH_URL || getBackendUrl(8000, "/auth");
const API_KEY = process.env.NEXT_PUBLIC_NIDS_API_KEY || "nids-dev-api-key-12345678901234567890123456789012";

// Helper function to get auth headers
function getAuthHeaders() {
  // In a real app, we would get the token from localStorage/session
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

  return {
    "Authorization": token ? `Bearer ${token}` : `Bearer ${API_KEY}`,
    "Content-Type": "application/json",
  };
}

// Authentication
export async function login(username: string, password: string) {
  const res = await fetch(`${AUTH_BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(error.detail || "Login failed");
  }
  const data = await res.json();
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', data.access_token);
  }
  return data;
}

export async function getCurrentUser() {
  const res = await fetch(`${AUTH_BASE_URL}/me`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch user info");
  return res.json();
}

// Alerts
export async function fetchAlerts(limit = 50, page = 1) {
  const res = await fetch(`${API_BASE_URL}/alerts?limit=${limit}&page=${page}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function fetchAlertDetails(alertId: string) {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch alert details");
  return res.json();
}

export async function fetchPackets(limit = 100) {
  const res = await fetch(`${API_BASE_URL}/packets?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch packets");
  return res.json();
}

export async function fetchSystemStatus() {
  const res = await fetch(`${API_BASE_URL}/status`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch system status");
  return res.json();
}

export async function startSniffer(config?: any) {
  const res = await fetch(`${API_BASE_URL}/start`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ config }),
  });
  if (!res.ok) throw new Error("Failed to start sniffer");
  return res.json();
}

export async function stopSniffer() {
  const res = await fetch(`${API_BASE_URL}/stop`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error("Failed to stop sniffer");
  return res.json();
}

export async function resolveAlert(alertId: string, notes = "") {
  // Backend uses 'notes' as a query param or request body? 
  // Checking routes.py: resolve_alert(alert_id: str, notes: str = "", ...)
  // It's a path param or query param? Actually it's a regular arg, FastAPI defaults to query if not in path.
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}/resolve?notes=${encodeURIComponent(notes)}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to resolve alert");
  return res.json();
}

// export async function deleteAlert(alertId: string) { ... } // Not implemented on backend

// export async function clearAlerts(olderThanDays?: number) { ... } // Not implemented on backend

export async function fetchStats() {
  const res = await fetch(`${API_BASE_URL}/stats`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

// export async function fetchCorrelation() { ... } // Not implemented on backend

// export async function fetchSignatureRules() { ... } // Not implemented on backend

export async function updateSnifferConfig(config: any) {
  const res = await fetch(`${API_BASE_URL}/config/sniffer`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Failed to update sniffer config");
  return res.json();
}

// export async function updateMLConfig(config: any) { ... } // Not implemented on backend

// IPS Management
export async function fetchBlockedIPs() {
  const res = await fetch(`${API_BASE_URL}/ips/blocked-ips`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch blocked IPs");
  return res.json();
}

export async function blockIP(ipAddress: string, duration = 60, reason = "Manual block") {
  const res = await fetch(`${API_BASE_URL}/ips/block`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      ip_address: ipAddress,
      duration_minutes: duration,
      reason: reason
    }),
  });
  if (!res.ok) throw new Error("Failed to block IP");
  return res.json();
}

export async function fetchBlockchainStatus() {
  const res = await fetch(`${API_BASE_URL}/blockchain/status`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch blockchain status");
  return res.json();
}
