'use client';

import { create } from 'zustand';

export interface Alert {
    id: string;
    timestamp: string;
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
    detection_type: string;
    source_ip: string;
    destination_ip?: string;
    protocol?: string;
    description: string;
    confidence?: number;
    resolved?: boolean;
    notes?: string;
}

export interface SystemStatus {
    is_running: boolean;
    sniffer_active: boolean;
    ml_active: boolean;
    ips_active: boolean;
    packets_captured: number;
    flows_aggregated: number;
    alerts_generated: number;
    ml_predictions: number;
    signature_matches: number;
    uptime: number;
}

export interface Stats {
    total_packets: number;
    total_flows: number;
    total_alerts: number;
    ml_detections: number;
    signature_detections: number;
    detection_rate: number;
    average_confidence: number;
}

export interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    is_active: boolean;
}

interface NidsState {
    // Auth
    user: User | null;
    isAuthenticated: boolean;
    setUser: (user: User | null) => void;
    logout: () => void;

    // System
    systemStatus: SystemStatus | null;
    setSystemStatus: (status: SystemStatus) => void;

    // Alerts
    alerts: Alert[];
    liveAlerts: Alert[];
    addLiveAlert: (alert: Alert) => void;
    setAlerts: (alerts: Alert[]) => void;
    clearLiveAlerts: () => void;

    // Stats
    stats: Stats | null;
    setStats: (stats: Stats) => void;

    // WebSocket
    wsConnected: boolean;
    setWsConnected: (connected: boolean) => void;

    // Sidebar
    sidebarCollapsed: boolean;
    toggleSidebar: () => void;
}

export const useNidsStore = create<NidsState>((set) => ({
    // Auth
    user: null,
    isAuthenticated: false,
    setUser: (user) => set({ user, isAuthenticated: !!user }),
    logout: () => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('nids_access_token');
            localStorage.removeItem('nids_refresh_token');
        }
        set({ user: null, isAuthenticated: false });
    },

    // System
    systemStatus: null,
    setSystemStatus: (status) => set({ systemStatus: status }),

    // Alerts
    alerts: [],
    liveAlerts: [],
    addLiveAlert: (alert) =>
        set((s) => ({ liveAlerts: [alert, ...s.liveAlerts].slice(0, 50) })),
    setAlerts: (alerts) => set({ alerts }),
    clearLiveAlerts: () => set({ liveAlerts: [] }),

    // Stats
    stats: null,
    setStats: (stats) => set({ stats }),

    // WebSocket
    wsConnected: false,
    setWsConnected: (connected) => set({ wsConnected: connected }),

    // Sidebar
    sidebarCollapsed: false,
    toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
