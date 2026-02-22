'use client';

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { LogIn, Mail, Lock, AlertCircle, ChevronRight } from 'lucide-react';


export default function LoginPage() {
    const { login } = useAuth();
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(email, password);
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center px-4 relative">
            <div className="bg-mesh" />

            <div className="w-full max-w-md animate-fade-in relative z-10">
                <div className="text-center mb-10">
                    <div className="w-16 h-16 rounded-2xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-primary-500/10">
                        <LogIn className="text-primary-400" size={28} />
                    </div>
                    <h1 className="text-4xl font-display font-bold text-white tracking-tight">Professional Portal</h1>
                    <p className="text-slate-500 mt-2 font-medium">Securely access your career intelligence</p>
                </div>

                <form onSubmit={handleSubmit} className="card space-y-6">
                    {error && (
                        <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm animate-shake">
                            <AlertCircle size={18} />
                            <span>{error}</span>
                        </div>
                    )}

                    <div className="space-y-2">
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Account Entity</label>
                        <div className="relative group">
                            <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary-400 transition-colors" />
                            <input
                                type="email"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                className="input-field pl-12"
                                placeholder="name@domain.com"
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Access Credential</label>
                        <div className="relative group">
                            <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary-400 transition-colors" />
                            <input
                                type="password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                className="input-field pl-12"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 text-lg group">
                        {loading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                                Authenticating…
                            </span>
                        ) : (
                            <span className="flex items-center justify-center gap-2">
                                Establish Connection <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                            </span>
                        )}
                    </button>

                    <p className="text-center text-sm text-slate-500">
                        New professional?{' '}
                        <Link href="/register" className="text-primary-400 hover:text-primary-300 font-semibold underline-offset-4 hover:underline transition-all">
                            Initialize Account
                        </Link>
                    </p>
                </form>
            </div>
        </div>
    );
}

