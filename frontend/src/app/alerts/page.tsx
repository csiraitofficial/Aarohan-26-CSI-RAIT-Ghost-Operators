'use client';

import { useState, useEffect, useCallback } from 'react';
import { getAlerts, resolveAlert, exportAlerts, AlertFilters } from '@/lib/api';
import { useNidsStore, Alert } from '@/store/useNidsStore';
import {
    ShieldAlert,
    Search,
    Filter,
    CheckCircle,
    Download,
    ChevronLeft,
    ChevronRight,
    X,
} from 'lucide-react';

function severityBadge(severity: string) {
    const map: Record<string, string> = {
        critical: 'badge-critical',
        high: 'badge-high',
        medium: 'badge-medium',
        low: 'badge-low',
        info: 'badge-info',
    };
    return map[severity] || 'badge-info';
}

export default function AlertsPage() {
    const { setAlerts, alerts } = useNidsStore();
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [filters, setFilters] = useState<AlertFilters>({ limit: 20, page: 1 });
    const [filterSeverity, setFilterSeverity] = useState('');
    const [filterIp, setFilterIp] = useState('');
    const [showFilters, setShowFilters] = useState(false);
    const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

    const fetchAlerts = useCallback(async () => {
        setLoading(true);
        try {
            const params: AlertFilters = { limit: 20, page };
            if (filterSeverity) params.severity = filterSeverity;
            if (filterIp) params.source_ip = filterIp;
            const res = await getAlerts(params);
            setAlerts(res.data.alerts);
            setTotalCount(res.data.total_count);
        } catch (e) {
            console.error('Failed to fetch alerts:', e);
        }
        setLoading(false);
    }, [page, filterSeverity, filterIp, setAlerts]);

    useEffect(() => {
        fetchAlerts();
    }, [fetchAlerts]);

    const handleResolve = async (id: string) => {
        try {
            await resolveAlert(id);
            fetchAlerts();
            setSelectedAlert(null);
        } catch (e) {
            console.error('Failed to resolve:', e);
        }
    };

    const handleExport = async () => {
        try {
            const res = await exportAlerts('json');
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const a = document.createElement('a');
            a.href = url;
            a.download = 'nids_alerts.json';
            a.click();
        } catch (e) {
            console.error('Export failed:', e);
        }
    };

    const totalPages = Math.ceil(totalCount / 20);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
                        Alerts
                    </h1>
                    <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: 4 }}>
                        {totalCount} total alerts detected
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-ghost" onClick={() => setShowFilters(!showFilters)}>
                        <Filter size={16} />
                        Filters
                    </button>
                    <button className="btn btn-ghost" onClick={handleExport}>
                        <Download size={16} />
                        Export
                    </button>
                </div>
            </div>

            {/* Filter Bar */}
            {showFilters && (
                <div
                    className="glass-card animate-float-up"
                    style={{ padding: 16, display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}
                >
                    <div style={{ flex: 1, minWidth: 160 }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>
                            Severity
                        </label>
                        <select
                            className="input"
                            value={filterSeverity}
                            onChange={(e) => { setFilterSeverity(e.target.value); setPage(1); }}
                            style={{ appearance: 'none' }}
                        >
                            <option value="">All</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                            <option value="info">Info</option>
                        </select>
                    </div>
                    <div style={{ flex: 1, minWidth: 200 }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>
                            Source IP
                        </label>
                        <div style={{ position: 'relative' }}>
                            <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
                            <input
                                className="input"
                                placeholder="Filter by IP"
                                value={filterIp}
                                onChange={(e) => { setFilterIp(e.target.value); setPage(1); }}
                                style={{ paddingLeft: 34 }}
                            />
                        </div>
                    </div>
                    <button
                        className="btn btn-ghost"
                        onClick={() => { setFilterSeverity(''); setFilterIp(''); setPage(1); }}
                        style={{ padding: '10px 12px' }}
                    >
                        <X size={14} /> Clear
                    </button>
                </div>
            )}

            {/* Table */}
            <div className="glass-card" style={{ overflow: 'hidden' }}>
                {loading ? (
                    <div style={{ padding: '60px 0', textAlign: 'center', color: '#475569' }}>
                        <div className="shimmer" style={{ width: 120, height: 16, borderRadius: 4, margin: '0 auto 12px' }} />
                        <p style={{ fontSize: '0.85rem' }}>Loading alerts...</p>
                    </div>
                ) : alerts.length === 0 ? (
                    <div style={{ padding: '60px 0', textAlign: 'center', color: '#475569' }}>
                        <ShieldAlert size={40} style={{ margin: '0 auto 12px', opacity: 0.3, display: 'block' }} />
                        <p style={{ fontSize: '0.85rem' }}>No alerts found.</p>
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table className="nids-table">
                            <thead>
                                <tr>
                                    <th>Severity</th>
                                    <th>Type</th>
                                    <th>Source IP</th>
                                    <th>Description</th>
                                    <th>Timestamp</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {alerts.map((alert: Alert, idx: number) => (
                                    <tr
                                        key={alert.id || idx}
                                        onClick={() => setSelectedAlert(alert)}
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <td>
                                            <span className={`badge ${severityBadge(alert.severity)}`}>
                                                {alert.severity}
                                            </span>
                                        </td>
                                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                                            {alert.detection_type}
                                        </td>
                                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                                            {alert.source_ip}
                                        </td>
                                        <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {alert.description}
                                        </td>
                                        <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                                            {alert.timestamp}
                                        </td>
                                        <td>
                                            {alert.resolved ? (
                                                <span className="badge badge-low">Resolved</span>
                                            ) : (
                                                <span className="badge badge-high">Open</span>
                                            )}
                                        </td>
                                        <td>
                                            {!alert.resolved && (
                                                <button
                                                    className="btn btn-ghost"
                                                    style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleResolve(alert.id);
                                                    }}
                                                >
                                                    <CheckCircle size={14} />
                                                    Resolve
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: 12,
                            padding: '16px 0',
                            borderTop: '1px solid rgba(99,102,241,0.08)',
                        }}
                    >
                        <button
                            className="btn btn-ghost"
                            disabled={page <= 1}
                            onClick={() => setPage((p) => p - 1)}
                            style={{ padding: '6px 10px' }}
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                            Page {page} of {totalPages}
                        </span>
                        <button
                            className="btn btn-ghost"
                            disabled={page >= totalPages}
                            onClick={() => setPage((p) => p + 1)}
                            style={{ padding: '6px 10px' }}
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                )}
            </div>

            {/* Alert Detail Modal */}
            {selectedAlert && (
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
                    onClick={() => setSelectedAlert(null)}
                >
                    <div
                        className="glass-card animate-float-up"
                        style={{
                            width: '100%',
                            maxWidth: 520,
                            padding: 28,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 16,
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9' }}>Alert Detail</h3>
                            <button
                                onClick={() => setSelectedAlert(null)}
                                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            <div>
                                <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>SEVERITY</div>
                                <span className={`badge ${severityBadge(selectedAlert.severity)}`}>
                                    {selectedAlert.severity}
                                </span>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>DETECTION TYPE</div>
                                <div style={{ fontSize: '0.85rem', color: '#f1f5f9', fontFamily: 'var(--font-mono)' }}>
                                    {selectedAlert.detection_type}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>SOURCE IP</div>
                                <div style={{ fontSize: '0.85rem', color: '#f1f5f9', fontFamily: 'var(--font-mono)' }}>
                                    {selectedAlert.source_ip}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>DEST IP</div>
                                <div style={{ fontSize: '0.85rem', color: '#f1f5f9', fontFamily: 'var(--font-mono)' }}>
                                    {selectedAlert.destination_ip || '—'}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>PROTOCOL</div>
                                <div style={{ fontSize: '0.85rem', color: '#f1f5f9' }}>
                                    {selectedAlert.protocol || '—'}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>CONFIDENCE</div>
                                <div style={{ fontSize: '0.85rem', color: '#f1f5f9' }}>
                                    {selectedAlert.confidence != null ? `${(selectedAlert.confidence * 100).toFixed(1)}%` : '—'}
                                </div>
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>DESCRIPTION</div>
                            <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{selectedAlert.description}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>TIMESTAMP</div>
                            <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{selectedAlert.timestamp}</div>
                        </div>
                        {!selectedAlert.resolved && (
                            <button
                                className="btn btn-primary"
                                style={{ width: '100%', marginTop: 8 }}
                                onClick={() => handleResolve(selectedAlert.id)}
                            >
                                <CheckCircle size={16} />
                                Resolve Alert
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
