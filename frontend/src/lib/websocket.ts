export type WSCallback = (data: Record<string, unknown>) => void;

class NidsWebSocket {
    private ws: WebSocket | null = null;
    private url: string;
    private listeners: Set<WSCallback> = new Set();
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private reconnectAttempts = 0;
    private maxReconnect = 10;
    private reconnectDelay = 3000;

    constructor() {
        const base = process.env.NEXT_PUBLIC_WS_URL || 'ws://195.35.23.26:8000';
        this.url = `${base}/ws/alerts`;
    }

    connect() {
        if (this.ws?.readyState === WebSocket.OPEN) return;

        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('[WS] Connected to NIDS alerts');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.listeners.forEach((cb) => cb(data));
                } catch {
                    console.warn('[WS] Failed to parse message:', event.data);
                }
            };

            this.ws.onclose = () => {
                console.log('[WS] Disconnected');
                this.scheduleReconnect();
            };

            this.ws.onerror = (err) => {
                console.error('[WS] Error:', err);
                this.ws?.close();
            };
        } catch (err) {
            console.error('[WS] Connection failed:', err);
            this.scheduleReconnect();
        }
    }

    private scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnect) {
            console.warn('[WS] Max reconnect attempts reached');
            return;
        }
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        this.reconnectTimer = setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`[WS] Reconnecting (${this.reconnectAttempts}/${this.maxReconnect})...`);
            this.connect();
        }, this.reconnectDelay * Math.min(this.reconnectAttempts + 1, 5));
    }

    subscribe(callback: WSCallback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    disconnect() {
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        this.reconnectAttempts = this.maxReconnect; // prevent reconnection
        this.ws?.close();
        this.ws = null;
    }

    get connected() {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}

export const nidsWs = new NidsWebSocket();
