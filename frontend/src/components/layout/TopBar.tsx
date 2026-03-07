'use client';

import { useNidsStore } from '@/store/useNidsStore';
import {
    Power,
    PowerOff,
    LogOut,
    Bell,
    User,
} from 'lucide-react';
import { startNids, stopNids } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function TopBar() {
    const { user, logout, systemStatus, liveAlerts } = useNidsStore();
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    const isRunning = systemStatus?.is_running ?? false;

    const handleToggle = async () => {
        setLoading(true);
        try {
            if (isRunning) {
                await stopNids();
            } else {
                await startNids();
            }
        } catch (e) {
            console.error('Toggle NIDS failed:', e);
        }
        setLoading(false);
    };

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    return (
        <header
            style={{
                height: 64,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 24px',
                background: 'rgba(10, 14, 26, 0.8)',
                borderBottom: '1px solid rgba(99, 102, 241, 0.1)',
                backdropFilter: 'blur(16px)',
                position: 'sticky',
                top: 0,
                zIndex: 30,
            }}
        >
            {/* Left: System Status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <button
                    className="btn"
                    onClick={handleToggle}
                    disabled={loading}
                    style={{
                        background: isRunning
                            ? 'rgba(244, 63, 94, 0.15)'
                            : 'rgba(16, 185, 129, 0.15)',
                        color: isRunning ? '#fb7185' : '#34d399',
                        border: `1px solid ${isRunning ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                        padding: '8px 16px',
                        fontSize: '0.8rem',
                    }}
                >
                    {isRunning ? <PowerOff size={16} /> : <Power size={16} />}
                    {loading ? 'Processing...' : isRunning ? 'Stop NIDS' : 'Start NIDS'}
                </button>

                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        fontSize: '0.8rem',
                        color: isRunning ? '#34d399' : '#f87171',
                    }}
                >
                    <div
                        style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: isRunning ? '#10b981' : '#f43f5e',
                            boxShadow: isRunning ? '0 0 8px rgba(16, 185, 129, 0.5)' : '0 0 8px rgba(244, 63, 94, 0.5)',
                        }}
                    />
                    {isRunning ? 'System Active' : 'System Stopped'}
                </div>
            </div>

            {/* Right: Alerts + User */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                {/* Live alert badge */}
                <div style={{ position: 'relative', cursor: 'pointer' }} onClick={() => router.push('/alerts')}>
                    <Bell size={20} color="#94a3b8" />
                    {liveAlerts.length > 0 && (
                        <span
                            style={{
                                position: 'absolute',
                                top: -6,
                                right: -8,
                                background: '#f43f5e',
                                color: '#fff',
                                fontSize: '0.65rem',
                                fontWeight: 700,
                                width: 18,
                                height: 18,
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            {liveAlerts.length > 9 ? '9+' : liveAlerts.length}
                        </span>
                    )}
                </div>

                {/* User */}
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '6px 12px',
                        borderRadius: 10,
                        background: 'rgba(99, 102, 241, 0.08)',
                        border: '1px solid rgba(99, 102, 241, 0.12)',
                    }}
                >
                    <div
                        style={{
                            width: 30,
                            height: 30,
                            borderRadius: '50%',
                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}
                    >
                        <User size={14} color="#fff" />
                    </div>
                    <div>
                        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f1f5f9' }}>
                            {user?.username || 'Admin'}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: '#64748b', textTransform: 'uppercase' }}>
                            {user?.role || 'admin'}
                        </div>
                    </div>
                </div>

                <button
                    onClick={handleLogout}
                    title="Logout"
                    style={{
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: '#94a3b8',
                        padding: 6,
                        borderRadius: 8,
                        display: 'flex',
                    }}
                >
                    <LogOut size={18} />
                </button>
            </div>
        </header>
    );
}
