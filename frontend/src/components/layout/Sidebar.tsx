'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    ShieldAlert,
    Settings,
    Shield,
    Activity,
    ChevronLeft,
    ChevronRight,
    Wifi,
    WifiOff,
} from 'lucide-react';
import { useNidsStore } from '@/store/useNidsStore';

const navItems = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/alerts', label: 'Alerts', icon: ShieldAlert },
    { href: '/prevention', label: 'Prevention', icon: Shield },
    { href: '/config', label: 'Configuration', icon: Settings },
];

export default function Sidebar() {
    const pathname = usePathname();
    const { sidebarCollapsed, toggleSidebar, wsConnected } = useNidsStore();

    return (
        <aside
            style={{
                width: sidebarCollapsed ? 72 : 260,
                minHeight: '100vh',
                position: 'fixed',
                top: 0,
                left: 0,
                zIndex: 40,
                display: 'flex',
                flexDirection: 'column',
                background: 'rgba(10, 14, 26, 0.95)',
                borderRight: '1px solid rgba(99, 102, 241, 0.1)',
                transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                backdropFilter: 'blur(16px)',
            }}
        >
            {/* Logo */}
            <div
                style={{
                    height: 64,
                    display: 'flex',
                    alignItems: 'center',
                    padding: sidebarCollapsed ? '0 16px' : '0 20px',
                    gap: 12,
                    borderBottom: '1px solid rgba(99, 102, 241, 0.1)',
                }}
            >
                <div
                    style={{
                        width: 36,
                        height: 36,
                        borderRadius: 10,
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                    }}
                >
                    <Activity size={20} color="#fff" />
                </div>
                {!sidebarCollapsed && (
                    <div style={{ overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f1f5f9' }}>
                            Ghost NIDS
                        </div>
                        <div style={{ fontSize: '0.7rem', color: '#64748b' }}>v2.0.0</div>
                    </div>
                )}
            </div>

            {/* Navigation */}
            <nav style={{ flex: 1, padding: '16px 8px', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {navItems.map(({ href, label, icon: Icon }) => {
                    const active = pathname === href;
                    return (
                        <Link
                            key={href}
                            href={href}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                padding: sidebarCollapsed ? '12px 16px' : '10px 16px',
                                borderRadius: 10,
                                textDecoration: 'none',
                                color: active ? '#f1f5f9' : '#94a3b8',
                                background: active ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                                fontWeight: active ? 600 : 400,
                                fontSize: '0.875rem',
                                transition: 'all 0.2s ease',
                                position: 'relative',
                            }}
                            title={label}
                        >
                            <Icon size={20} style={{ flexShrink: 0, color: active ? '#818cf8' : '#64748b' }} />
                            {!sidebarCollapsed && <span>{label}</span>}
                            {active && (
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: 0,
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        width: 3,
                                        height: 20,
                                        borderRadius: 4,
                                        background: '#6366f1',
                                    }}
                                />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Bottom section */}
            <div style={{ padding: '12px 8px', borderTop: '1px solid rgba(99, 102, 241, 0.1)' }}>
                {/* WS Status */}
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '8px 16px',
                        fontSize: '0.75rem',
                        color: wsConnected ? '#34d399' : '#f87171',
                    }}
                >
                    {wsConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
                    {!sidebarCollapsed && (
                        <span>{wsConnected ? 'Live Connected' : 'Disconnected'}</span>
                    )}
                </div>

                {/* Collapse toggle */}
                <button
                    onClick={toggleSidebar}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                        gap: 8,
                        width: '100%',
                        padding: '10px 16px',
                        borderRadius: 10,
                        border: 'none',
                        background: 'transparent',
                        color: '#94a3b8',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                        transition: 'all 0.2s ease',
                    }}
                >
                    {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    {!sidebarCollapsed && <span>Collapse</span>}
                </button>
            </div>
        </aside>
    );
}
