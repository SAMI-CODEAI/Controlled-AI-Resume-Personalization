'use client';

import React, { useEffect } from 'react';
import './globals.css';
import { AuthProvider, useAuth } from '@/lib/auth';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutDashboard, User, FileText, Sparkles, Clock, LogOut, Menu, X
} from 'lucide-react';

function Navigation() {
    const { user, loading, logout } = useAuth();
    const pathname = usePathname();
    const router = useRouter();
    const [mobileOpen, setMobileOpen] = React.useState(false);

    const isPublic = ['/', '/login', '/register'].includes(pathname);

    useEffect(() => {
        if (!loading && !user && !isPublic) {
            router.push('/login');
        }
    }, [loading, user, isPublic, router]);

    if (isPublic || loading) return null;
    if (!user) return null;

    const links = [
        { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { href: '/profile', label: 'Profile', icon: User },
        { href: '/templates', label: 'Templates', icon: FileText },
        { href: '/generate', label: 'Generate', icon: Sparkles },
        { href: '/history', label: 'History', icon: Clock },
    ];

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-20">
                    <Link href="/dashboard" className="flex items-center gap-2 group">
                        <div className="w-10 h-10 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400 font-bold text-lg group-hover:scale-110 group-hover:bg-primary-500/20 transition-all duration-500">
                            R
                        </div>
                        <span className="text-xl font-display font-bold tracking-tight text-white hidden sm:block">
                            Resume<span className="text-primary-400">AI</span>
                        </span>
                    </Link>

                    {/* Desktop links */}
                    <div className="hidden md:flex items-center gap-1">
                        {links.map(({ href, label, icon: Icon }) => (
                            <Link
                                key={href}
                                href={href}
                                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${pathname === href
                                    ? 'bg-primary-500/10 text-primary-400 border border-primary-400/20'
                                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                <Icon size={16} />
                                {label}
                            </Link>
                        ))}
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden lg:flex flex-col items-end">
                            <span className="text-xs font-semibold text-white truncate max-w-[150px]">{user.full_name}</span>
                            <span className="text-[10px] text-slate-500 uppercase tracking-widest">Logged In</span>
                        </div>
                        <button
                            onClick={() => { logout(); router.push('/login'); }}
                            className="p-2.5 text-slate-400 hover:text-red-400 rounded-xl hover:bg-red-500/10 transition-all duration-300"
                            title="Logout"
                        >
                            <LogOut size={18} />
                        </button>
                        <button
                            className="md:hidden p-2 text-slate-400 hover:text-white bg-white/5 rounded-lg transition-colors"
                            onClick={() => setMobileOpen(!mobileOpen)}
                        >
                            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
                        </button>
                    </div>
                </div>

                {/* Mobile menu */}
                {mobileOpen && (
                    <div className="md:hidden pb-6 pt-2 animate-slide-up space-y-2">
                        {links.map(({ href, label, icon: Icon }) => (
                            <Link
                                key={href}
                                href={href}
                                onClick={() => setMobileOpen(false)}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${pathname === href
                                    ? 'bg-primary-500/10 text-primary-400 border border-primary-400/20'
                                    : 'text-slate-400 hover:text-white bg-white/5'
                                    }`}
                            >
                                <Icon size={18} />
                                {label}
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </nav>
    );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className="dark">
            <head>
                <title>ResumeAI — Absolute Integrity AI Resume Builder</title>
                <meta name="description" content="Generate job-specific resumes with zero hallucinations using high-end LaTeX templates." />
            </head>
            <body className="min-h-screen bg-slate-950 text-white font-sans antialiased">
                <div className="bg-mesh" />
                <AuthProvider>
                    <Navigation />
                    <main className="pt-20">{children}</main>
                </AuthProvider>
            </body>
        </html>
    );
}

