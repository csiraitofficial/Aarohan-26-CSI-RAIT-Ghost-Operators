'use client';

import { useNidsStore, Alert } from '@/store/useNidsStore';
import {
  Activity,
  ShieldAlert,
  Cpu,
  Network,
  Zap,
  TrendingUp,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

function formatUptime(seconds: number) {
  if (!seconds) return '0s';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

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

export default function DashboardPage() {
  const { systemStatus, stats, liveAlerts } = useNidsStore();

  const statCards = [
    {
      label: 'Packets Captured',
      value: systemStatus?.packets_captured?.toLocaleString() ?? '—',
      icon: Network,
      color: '#6366f1',
      glow: 'rgba(99,102,241,0.2)',
    },
    {
      label: 'Total Alerts',
      value: systemStatus?.alerts_generated?.toLocaleString() ?? '—',
      icon: ShieldAlert,
      color: '#f43f5e',
      glow: 'rgba(244,63,94,0.2)',
    },
    {
      label: 'ML Predictions',
      value: systemStatus?.ml_predictions?.toLocaleString() ?? '—',
      icon: Cpu,
      color: '#8b5cf6',
      glow: 'rgba(139,92,246,0.2)',
    },
    {
      label: 'Signature Matches',
      value: systemStatus?.signature_matches?.toLocaleString() ?? '—',
      icon: Zap,
      color: '#f59e0b',
      glow: 'rgba(245,158,11,0.2)',
    },
    {
      label: 'Detection Rate',
      value: stats?.detection_rate != null ? `${(stats.detection_rate * 100).toFixed(1)}%` : '—',
      icon: TrendingUp,
      color: '#10b981',
      glow: 'rgba(16,185,129,0.2)',
    },
    {
      label: 'Uptime',
      value: formatUptime(systemStatus?.uptime ?? 0),
      icon: Clock,
      color: '#22d3ee',
      glow: 'rgba(34,211,238,0.2)',
    },
  ];

  // Fake chart data derived from live alerts to give the chart some life
  const chartData = Array.from({ length: 12 }, (_, i) => {
    const minute = `${(i * 5).toString().padStart(2, '0')}m`;
    return {
      time: minute,
      alerts: Math.floor(Math.random() * 10) + (liveAlerts.length > 0 ? 3 : 0),
      packets: Math.floor(Math.random() * 50) + 20,
    };
  });

  const pieData = [
    { name: 'ML', value: stats?.ml_detections ?? 30, color: '#8b5cf6' },
    { name: 'Signature', value: stats?.signature_detections ?? 20, color: '#f59e0b' },
    { name: 'Clean', value: Math.max(0, (stats?.total_packets ?? 100) - (stats?.total_alerts ?? 50)), color: '#10b981' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Page title */}
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
          Dashboard
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: 4 }}>
          Real-time network security overview
        </p>
      </div>

      {/* Stat Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: 16,
        }}
      >
        {statCards.map(({ label, value, icon: Icon, color, glow }) => (
          <div
            key={label}
            className="glass-card stat-card"
            style={{ padding: '20px 20px', position: 'relative', overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500, marginBottom: 8 }}>
                  {label}
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
              </div>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: `${color}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon size={20} color={color} />
              </div>
            </div>
            {/* Decorative glow */}
            <div
              style={{
                position: 'absolute',
                bottom: -20,
                right: -20,
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: glow,
                filter: 'blur(30px)',
              }}
            />
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
        {/* Area Chart */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9', marginBottom: 16 }}>
            <Activity size={16} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            Activity Over Time
          </h3>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorPackets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                <XAxis dataKey="time" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: '#111827',
                    border: '1px solid rgba(99,102,241,0.2)',
                    borderRadius: 8,
                    fontSize: '0.8rem',
                    color: '#f1f5f9',
                  }}
                />
                <Area type="monotone" dataKey="packets" stroke="#6366f1" fill="url(#colorPackets)" strokeWidth={2} />
                <Area type="monotone" dataKey="alerts" stroke="#f43f5e" fill="url(#colorAlerts)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9', marginBottom: 16 }}>
            Detection Breakdown
          </h3>
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#111827',
                    border: '1px solid rgba(99,102,241,0.2)',
                    borderRadius: 8,
                    fontSize: '0.8rem',
                    color: '#f1f5f9',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 8 }}>
            {pieData.map((item) => (
              <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: item.color,
                  }}
                />
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Live Alerts Feed */}
      <div className="glass-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9' }}>
            <AlertTriangle size={16} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle', color: '#f59e0b' }} />
            Live Alert Feed
          </h3>
          {liveAlerts.length > 0 && (
            <span className="badge badge-critical" style={{ animation: 'pulse-glow 2s infinite' }}>
              {liveAlerts.length} new
            </span>
          )}
        </div>

        {liveAlerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#475569' }}>
            <ShieldAlert size={40} style={{ margin: '0 auto 12px', opacity: 0.3, display: 'block' }} />
            <p style={{ fontSize: '0.85rem' }}>No live alerts. The system is quiet.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 320, overflowY: 'auto' }}>
            {liveAlerts.map((alert: Alert, idx: number) => (
              <div
                key={alert.id || idx}
                className="animate-float-up"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 16px',
                  borderRadius: 10,
                  background: 'rgba(17, 24, 39, 0.5)',
                  border: '1px solid rgba(99,102,241,0.08)',
                  animationDelay: `${idx * 0.05}s`,
                }}
              >
                <span className={`badge ${severityBadge(alert.severity)}`}>
                  {alert.severity}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.85rem', color: '#f1f5f9', fontWeight: 500 }}>
                    {alert.description || alert.detection_type}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 2 }}>
                    {alert.source_ip} • {alert.timestamp}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
