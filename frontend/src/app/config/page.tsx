'use client';

import { useState, useEffect } from 'react';
import { getConfig, updateSnifferConfig } from '@/lib/api';
import {
    Settings,
    Wifi,
    Cpu,
    Shield,
    Save,
    Loader2,
    CheckCircle,
} from 'lucide-react';

interface NidsConfig {
    sniffer: {
        interface: string;
        bpf_filter?: string;
        snap_length?: number;
        promisc?: boolean;
    };
    ml: {
        model_path: string;
        confidence_threshold: number;
    };
    ips: {
        enabled: boolean;
        auto_block: boolean;
        block_duration_minutes?: number;
    };
}

export default function ConfigPage() {
    const [config, setConfig] = useState<NidsConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Editable sniffer fields
    const [iface, setIface] = useState('');

    useEffect(() => {
        (async () => {
            try {
                const res = await getConfig();
                setConfig(res.data);
                setIface(res.data.sniffer?.interface || '');
            } catch (e) {
                console.error('Failed to load config:', e);
            }
            setLoading(false);
        })();
    }, []);

    const handleSaveSniffer = async () => {
        setSaving(true);
        try {
            await updateSnifferConfig({ interface: iface });
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (e) {
            console.error('Failed to save sniffer config:', e);
        }
        setSaving(false);
    };

    if (loading) {
        return (
            <div style={{ padding: '60px 0', textAlign: 'center', color: '#475569' }}>
                <div className="shimmer" style={{ width: 120, height: 16, borderRadius: 4, margin: '0 auto 12px' }} />
                <p style={{ fontSize: '0.85rem' }}>Loading configuration...</p>
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
                    Configuration
                </h1>
                <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: 4 }}>
                    Manage NIDS sniffer, ML engine, and IPS settings
                </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* Sniffer Config */}
                <div className="glass-card" style={{ padding: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                        <div
                            style={{
                                width: 36,
                                height: 36,
                                borderRadius: 10,
                                background: 'rgba(99,102,241,0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            <Wifi size={18} color="#818cf8" />
                        </div>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>Sniffer Engine</h3>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>
                                Network Interface
                            </label>
                            <input
                                className="input"
                                value={iface}
                                onChange={(e) => setIface(e.target.value)}
                                placeholder="e.g. eth0"
                            />
                        </div>

                        <button
                            className="btn btn-primary"
                            onClick={handleSaveSniffer}
                            disabled={saving}
                            style={{ alignSelf: 'flex-start' }}
                        >
                            {saving ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : saved ? <CheckCircle size={16} /> : <Save size={16} />}
                            {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Changes'}
                        </button>
                    </div>
                </div>

                {/* ML Config (read-only) */}
                <div className="glass-card" style={{ padding: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                        <div
                            style={{
                                width: 36,
                                height: 36,
                                borderRadius: 10,
                                background: 'rgba(139,92,246,0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            <Cpu size={18} color="#a78bfa" />
                        </div>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>ML Engine</h3>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>
                                Model Path
                            </label>
                            <input
                                className="input"
                                value={config?.ml?.model_path || '—'}
                                readOnly
                                style={{ opacity: 0.7, cursor: 'not-allowed' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>
                                Confidence Threshold
                            </label>
                            <div
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 12,
                                    padding: '10px 14px',
                                    background: '#111827',
                                    borderRadius: 8,
                                    border: '1px solid rgba(99,102,241,0.15)',
                                }}
                            >
                                <div
                                    style={{
                                        flex: 1,
                                        height: 6,
                                        borderRadius: 3,
                                        background: 'rgba(99,102,241,0.2)',
                                        position: 'relative',
                                        overflow: 'hidden',
                                    }}
                                >
                                    <div
                                        style={{
                                            height: '100%',
                                            width: `${(config?.ml?.confidence_threshold ?? 0.5) * 100}%`,
                                            borderRadius: 3,
                                            background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                                        }}
                                    />
                                </div>
                                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f1f5f9', fontFamily: 'var(--font-mono)' }}>
                                    {((config?.ml?.confidence_threshold ?? 0.5) * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* IPS Config (read-only) */}
                <div className="glass-card" style={{ padding: 24, gridColumn: 'span 2' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                        <div
                            style={{
                                width: 36,
                                height: 36,
                                borderRadius: 10,
                                background: 'rgba(16,185,129,0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            <Shield size={18} color="#34d399" />
                        </div>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>
                            Intrusion Prevention System
                        </h3>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>
                                IPS Status
                            </label>
                            <span className={`badge ${config?.ips?.enabled ? 'badge-low' : 'badge-critical'}`}>
                                {config?.ips?.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 6 }}>
                                Auto-Block
                            </label>
                            <span className={`badge ${config?.ips?.auto_block ? 'badge-low' : 'badge-high'}`}>
                                {config?.ips?.auto_block ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}
