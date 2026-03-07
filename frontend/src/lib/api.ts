import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://195.35.23.26:8000';

const api = axios.create({
    baseURL: `${API_BASE}/api/v1`,
    headers: { 'Content-Type': 'application/json' },
    timeout: 15000,
});

const authApi = axios.create({
    baseURL: `${API_BASE}/auth`,
    headers: { 'Content-Type': 'application/json' },
    timeout: 15000,
});

// Inject JWT token into requests
api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('nids_access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('nids_access_token');
                localStorage.removeItem('nids_refresh_token');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// ── Auth ──
export const login = (username: string, password: string) =>
    authApi.post('/login', { username, password });

export const register = (username: string, email: string, password: string, role: string = 'viewer') =>
    authApi.post('/register', { username, email, password, role });

export const getMe = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('nids_access_token') : null;
    return authApi.get('/me', { headers: { Authorization: `Bearer ${token}` } });
};

// ── System Control ──
export const getSystemStatus = () => api.get('/status');
export const startNids = (config?: Record<string, unknown>) => api.post('/start', config ? { config } : undefined);
export const stopNids = () => api.post('/stop');

// ── Alerts ──
export interface AlertFilters {
    limit?: number;
    page?: number;
    severity?: string;
    detection_type?: string;
    source_ip?: string;
    resolved?: boolean;
}
export const getAlerts = (filters: AlertFilters = {}) =>
    api.get('/alerts', { params: filters });
export const getAlertDetail = (id: string) => api.get(`/alerts/${id}`);
export const resolveAlert = (id: string, notes: string = '') =>
    api.post(`/alerts/${id}/resolve`, null, { params: { notes } });
export const exportAlerts = (format: string = 'json') =>
    api.get('/alerts/export', { params: { format }, responseType: 'blob' });

// ── Traffic ──
export const getPackets = (limit: number = 100) =>
    api.get('/packets', { params: { limit } });
export const getStats = () => api.get('/stats');

// ── IPS / Prevention ──
export const blockIp = (ip_address: string, duration_minutes: number, reason: string) =>
    api.post('/ips/block', { ip_address, duration_minutes, reason });
export const getBlockedIps = () => api.get('/ips/blocked-ips');
export const getPlaybookHistory = () => api.get('/prevention/playbook-history');
export const getHoneypotStats = () => api.get('/prevention/honeypot-stats');

// ── Intelligence ──
export const getUebaStats = () => api.get('/intelligence/ueba-stats');
export const getAiTriageHistory = () => api.get('/intelligence/ai-triage-history');
export const getPredictiveInsight = () => api.get('/intelligence/predictive-insight');

// ── Config ──
export const getConfig = () => api.get('/config');
export const updateSnifferConfig = (config: Record<string, unknown>) =>
    api.post('/config/sniffer', config);

// ── Health ──
export const getHealth = () => api.get('/health');

export default api;
