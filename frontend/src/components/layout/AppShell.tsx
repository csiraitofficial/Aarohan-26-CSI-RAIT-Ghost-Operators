'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';
import TopBar from '@/components/layout/TopBar';
import { useNidsStore } from '@/store/useNidsStore';
import { getSystemStatus, getStats, getMe } from '@/lib/api';
import { nidsWs } from '@/lib/websocket';

export default function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const router = useRouter();
    const {
        sidebarCollapsed,
        setUser,
        setSystemStatus,
        setStats,
        addLiveAlert,
        setWsConnected,
        isAuthenticated,
    } = useNidsStore();

    const isLoginPage = pathname === '/login';

    // Check auth on mount
    useEffect(() => {
        if (isLoginPage) return;
        const token = localStorage.getItem('nids_access_token');
        if (!token) {
            router.push('/login');
            return;
        }
        // Try to fetch user
        getMe()
            .then((res) => setUser(res.data))
            .catch(() => {
                // Token invalid
                router.push('/login');
            });
    }, [isLoginPage, isAuthenticated]);

    // Poll system status and stats
    useEffect(() => {
        if (isLoginPage) return;
        const poll = async () => {
            try {
                const [statusRes, statsRes] = await Promise.all([
                    getSystemStatus().catch(() => null),
                    getStats().catch(() => null),
                ]);
                if (statusRes) setSystemStatus(statusRes.data);
                if (statsRes) setStats(statsRes.data);
            } catch { /* ignore */ }
        };
        poll();
        const interval = setInterval(poll, 5000);
        return () => clearInterval(interval);
    }, [isLoginPage, isAuthenticated]);

    // WebSocket
    useEffect(() => {
        if (isLoginPage || !isAuthenticated) return;

        nidsWs.connect();
        const unsub = nidsWs.subscribe((data) => {
            addLiveAlert(data as never);
        });
        const checkInterval = setInterval(() => {
            setWsConnected(nidsWs.connected);
        }, 2000);
        return () => {
            unsub();
            clearInterval(checkInterval);
            nidsWs.disconnect();
        };
    }, [isLoginPage, isAuthenticated]);

    if (isLoginPage) {
        return <>{children}</>;
    }

    return (
        <div style={{ display: 'flex', minHeight: '100vh' }}>
            <Sidebar />
            <div
                style={{
                    flex: 1,
                    marginLeft: sidebarCollapsed ? 72 : 260,
                    transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <TopBar />
                <main style={{ flex: 1, padding: 24 }}>{children}</main>
            </div>
        </div>
    );
}
