'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';
import { useNidsStore } from '@/store/useNidsStore';
import { ShieldCheck, Eye, EyeOff, Loader2 } from 'lucide-react';

export default function LoginPage() {
    const router = useRouter();
    const { setUser } = useNidsStore();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await login(username, password);
            const { access_token, refresh_token } = res.data;
            localStorage.setItem('nids_access_token', access_token);
            localStorage.setItem('nids_refresh_token', refresh_token);
            // Set a minimal user object; AppShell will fetch full user via /me
            setUser({ id: '', username, email: '', role: 'admin', is_active: true });
            router.push('/');
        } catch {
            setError('Invalid credentials. Please try again.');
        }
        setLoading(false);
    };

    return (
        <div
            style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'radial-gradient(ellipse at top, #0f172a 0%, #0a0e1a 50%, #050810 100%)',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Animated background orbs */}
            <div
                style={{
                    position: 'absolute',
                    width: 400,
                    height: 400,
                    borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)',
                    top: '-10%',
                    right: '-5%',
                    filter: 'blur(60px)',
                    animation: 'pulse-glow 4s ease-in-out infinite',
                }}
            />
            <div
                style={{
                    position: 'absolute',
                    width: 300,
                    height: 300,
                    borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(34,211,238,0.1) 0%, transparent 70%)',
                    bottom: '-5%',
                    left: '-3%',
                    filter: 'blur(60px)',
                    animation: 'pulse-glow 5s ease-in-out infinite',
                }}
            />

            <form
                onSubmit={handleLogin}
                className="glass-card animate-float-up"
                style={{
                    width: '100%',
                    maxWidth: 420,
                    padding: '40px 36px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 24,
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: 8 }}>
                    <div
                        style={{
                            width: 56,
                            height: 56,
                            borderRadius: 16,
                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            margin: '0 auto 16px',
                            boxShadow: '0 0 30px rgba(99, 102, 241, 0.3)',
                        }}
                    >
                        <ShieldCheck size={28} color="#fff" />
                    </div>
                    <h1
                        style={{
                            fontSize: '1.5rem',
                            fontWeight: 800,
                            background: 'linear-gradient(135deg, #f1f5f9, #94a3b8)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            marginBottom: 4,
                        }}
                    >
                        Ghost Operators NIDS
                    </h1>
                    <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
                        Network Intrusion Detection System
                    </p>
                </div>

                {/* Error */}
                {error && (
                    <div
                        style={{
                            background: 'rgba(244, 63, 94, 0.1)',
                            border: '1px solid rgba(244, 63, 94, 0.3)',
                            borderRadius: 8,
                            padding: '10px 14px',
                            color: '#fb7185',
                            fontSize: '0.85rem',
                        }}
                    >
                        {error}
                    </div>
                )}

                {/* Username */}
                <div>
                    <label
                        style={{
                            display: 'block',
                            fontSize: '0.8rem',
                            fontWeight: 500,
                            color: '#94a3b8',
                            marginBottom: 6,
                        }}
                    >
                        Username
                    </label>
                    <input
                        className="input"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter your username"
                        required
                        autoFocus
                    />
                </div>

                {/* Password */}
                <div>
                    <label
                        style={{
                            display: 'block',
                            fontSize: '0.8rem',
                            fontWeight: 500,
                            color: '#94a3b8',
                            marginBottom: 6,
                        }}
                    >
                        Password
                    </label>
                    <div style={{ position: 'relative' }}>
                        <input
                            className="input"
                            type={showPassword ? 'text' : 'password'}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                            style={{ paddingRight: 42 }}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            style={{
                                position: 'absolute',
                                right: 12,
                                top: '50%',
                                transform: 'translateY(-50%)',
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                color: '#64748b',
                                display: 'flex',
                            }}
                        >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>
                </div>

                {/* Submit */}
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '12px 20px',
                        fontSize: '0.9rem',
                        marginTop: 8,
                    }}
                >
                    {loading ? (
                        <>
                            <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                            Authenticating...
                        </>
                    ) : (
                        'Sign In'
                    )}
                </button>

                <p style={{ textAlign: 'center', fontSize: '0.75rem', color: '#475569' }}>
                    Secured by Ghost Operators • v2.0.0
                </p>
            </form>

            {/* Spin keyframes for the loader */}
            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}
