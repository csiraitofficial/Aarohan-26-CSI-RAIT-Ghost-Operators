'use client';

import { useState, useEffect } from 'react';
import {
    getBlockedIps,
    getPlaybookHistory,
    getHoneypotStats,
    blockIp,
} from '@/lib/api';
import {
    Shield,
    Ban,
    BookOpen,
    Bug,
    Plus,
    Loader2,
    X,
} from 'lucide-react';

interface BlockedIp {
    ip_address: string;
    blocked_at: string;
    duration_minutes: number;
    reason: string;
    expires_at?: string;
}

interface PlaybookEntry {
    id: string;
    name: string;
    trigger: string;
    action: string;
    executed_at: string;
    status: string;
}

export default function PreventionPage() {
    const [blockedIps, setBlockedIps] = useState<BlockedIp[]>([]);
    const [playbookHistory, setPlaybookHistory] = useState<PlaybookEntry[]>([]);
    const [honeypotStats, setHoneypotStats] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(true);
    const [showBlockModal, setShowBlockModal] = useState(false);
    const [blockForm, setBlockForm] = useState({ ip: '', duration: 60, reason: '' });
    const [blocking, setBlocking] = useState(false);

    useEffect(() => {
        (async () => {
            try {
                const [bRes, pRes, hRes] = await Promise.all([
                    getBlockedIps().catch(() => ({ data: [] })),
                    getPlaybookHistory().catch(() => ({ data: [] })),
                    getHoneypotStats().catch(() => ({ data: null })),
                ]);
                setBlockedIps(Array.isArray(bRes.data) ? bRes.data : []);
                setPlaybookHistory(Array.isArray(pRes.data) ? pRes.data : []);
                setHoneypotStats(hRes.data);
            } catch { /* ignore */ }
            setLoading(false);
        })();
    }, []);

    const handleBlock = async () => {
        setBlocking(true);
        try {
            await blockIp(blockForm.ip, blockForm.duration, blockForm.reason);
            setShowBlockModal(false);
            setBlockForm({ ip: '', duration: 60, reason: '' });
            // Refresh
            const res = await getBlockedIps().catch(() => ({ data: [] }));
            setBlockedIps(Array.isArray(res.data) ? res.data : []);
        } catch (e) {
            console.error('Block failed:', e);
        }
        setBlocking(false);
    };

    if (loading) {
        return (
            <div style={{ padding: '60px 0', textAlign: 'center', color: '#475569' }}>
                <div className="shimmer" style={{ width: 120, height: 16, borderRadius: 4, margin: '0 auto 12px' }} />
                <p style={{ fontSize: '0.85rem' }}>Loading prevention data...</p>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div>
                <h1
                    style={{
                        fontSize: '1.5rem',
                        fontWeight: 700,
                        background: 'linear-gradient(135deg, #f1f5f9, #94a3b8)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                    }}
                >
                    Prevention & Response
                </h1>
                <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: 4 }}>
                    Manage IP blocks, playbooks, and honeypot activity
                </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* Blocked IPs */}
                <div className="glass-card" style={{ padding: 24 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(244,63,94,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Ban size={18} color="#fb7185" />
                            </div>
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>Blocked IPs</h3>
                        </div>
                        <button className="btn btn-primary" style={{ padding: '6px 14px', fontSize: '0.8rem' }} onClick={() => setShowBlockModal(true)}>
                            <Plus size={14} /> Block IP
                        </button>
                    </div>

                    {blockedIps.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '30px 0', color: '#475569' }}>
                            <Shield size={32} style={{ margin: '0 auto 8px', opacity: 0.3, display: 'block' }} />
                            <p style={{ fontSize: '0.85rem' }}>No blocked IPs</p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 300, overflowY: 'auto' }}>
                            {blockedIps.map((ip, idx) => (
                                <div
                                    key={idx}
                                    style={{
                                        padding: '10px 14px',
                                        borderRadius: 8,
                                        background: 'rgba(17,24,39,0.5)',
                                        border: '1px solid rgba(99,102,241,0.08)',
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                    }}
                                >
                                    <div>
                                        <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: '#f1f5f9' }}>
                                            {ip.ip_address}
                                        </div>
                                        <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}>
                                            {ip.reason} • {ip.duration_minutes}m
                                        </div>
                                    </div>
                                    <span className="badge badge-critical">Blocked</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Honeypot Stats */}
                <div className="glass-card" style={{ padding: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                        <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(245,158,11,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Bug size={18} color="#fbbf24" />
                        </div>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>Honeypot Activity</h3>
                    </div>

                    {honeypotStats ? (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            {Object.entries(honeypotStats).map(([key, value]) => (
                                <div key={key} style={{ padding: 14, borderRadius: 8, background: 'rgba(17,24,39,0.5)', border: '1px solid rgba(99,102,241,0.08)' }}>
                                    <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 4, textTransform: 'uppercase' }}>
                                        {key.replace(/_/g, ' ')}
                                    </div>
                                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9' }}>
                                        {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '30px 0', color: '#475569' }}>
                            <Bug size={32} style={{ margin: '0 auto 8px', opacity: 0.3, display: 'block' }} />
                            <p style={{ fontSize: '0.85rem' }}>No honeypot data available</p>
                        </div>
                    )}
                </div>

                {/* Playbook History */}
                <div className="glass-card" style={{ padding: 24, gridColumn: 'span 2' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                        <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(34,211,238,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <BookOpen size={18} color="#67e8f9" />
                        </div>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>Playbook Execution History</h3>
                    </div>

                    {playbookHistory.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '30px 0', color: '#475569' }}>
                            <BookOpen size={32} style={{ margin: '0 auto 8px', opacity: 0.3, display: 'block' }} />
                            <p style={{ fontSize: '0.85rem' }}>No playbook executions recorded</p>
                        </div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table className="nids-table">
                                <thead>
                                    <tr>
                                        <th>Playbook</th>
                                        <th>Trigger</th>
                                        <th>Action</th>
                                        <th>Executed</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {playbookHistory.map((entry, idx) => (
                                        <tr key={entry.id || idx}>
                                            <td style={{ fontWeight: 500, color: '#f1f5f9' }}>{entry.name}</td>
                                            <td>{entry.trigger}</td>
                                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{entry.action}</td>
                                            <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>{entry.executed_at}</td>
                                            <td>
                                                <span className={`badge ${entry.status === 'success' ? 'badge-low' : 'badge-high'}`}>
                                                    {entry.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Block IP Modal */}
            {showBlockModal && (
                <div
                    style={{
                        position: 'fixed',
                        inset: 0,
                        background: 'rgba(0,0,0,0.6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 50,
                        backdropFilter: 'blur(4px)',
                    }}
                    onClick={() => setShowBlockModal(false)}
                >
                    <div
                        className="glass-card animate-float-up"
                        style={{ width: '100%', maxWidth: 420, padding: 28, display: 'flex', flexDirection: 'column', gap: 16 }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>Block IP Address</h3>
                            <button onClick={() => setShowBlockModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                                <X size={20} />
                            </button>
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>IP Address</label>
                            <input className="input" value={blockForm.ip} onChange={(e) => setBlockForm({ ...blockForm, ip: e.target.value })} placeholder="192.168.1.100" />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>Duration (minutes)</label>
                            <input className="input" type="number" value={blockForm.duration} onChange={(e) => setBlockForm({ ...blockForm, duration: parseInt(e.target.value) || 60 })} />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>Reason</label>
                            <input className="input" value={blockForm.reason} onChange={(e) => setBlockForm({ ...blockForm, reason: e.target.value })} placeholder="Suspicious activity" />
                        </div>
                        <button className="btn btn-danger" onClick={handleBlock} disabled={blocking} style={{ width: '100%', marginTop: 8 }}>
                            {blocking ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Ban size={16} />}
                            {blocking ? 'Blocking...' : 'Block IP'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
