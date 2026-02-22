'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import { api, Skill, Project, Experience, Achievement, ResumeTemplate, GeneratedResume } from '@/lib/api';
import Link from 'next/link';
import {
    Zap, Code2, Briefcase, Trophy, FileText, Sparkles,
    TrendingUp, Plus, ArrowRight
} from 'lucide-react';

interface DashboardStats {
    skills: number;
    projects: number;
    experiences: number;
    achievements: number;
    templates: number;
    resumes: number;
}

export default function DashboardPage() {
    const { user } = useAuth();
    const [stats, setStats] = useState<DashboardStats>({ skills: 0, projects: 0, experiences: 0, achievements: 0, templates: 0, resumes: 0 });
    const [recentResumes, setRecentResumes] = useState<GeneratedResume[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const [skills, projects, experiences, achievements, templates, resumes] = await Promise.all([
                    api.get<Skill[]>('/api/skills'),
                    api.get<Project[]>('/api/projects'),
                    api.get<Experience[]>('/api/experiences'),
                    api.get<Achievement[]>('/api/achievements'),
                    api.get<ResumeTemplate[]>('/api/templates'),
                    api.get<GeneratedResume[]>('/api/resumes'),
                ]);
                setStats({
                    skills: skills.length,
                    projects: projects.length,
                    experiences: experiences.length,
                    achievements: achievements.length,
                    templates: templates.length,
                    resumes: resumes.length,
                });
                setRecentResumes(resumes.slice(0, 5));
            } catch { }
            setLoading(false);
        }
        load();
    }, []);

    const statCards = [
        { label: 'Verified Skills', value: stats.skills, icon: Code2, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
        { label: 'Key Projects', value: stats.projects, icon: Zap, color: 'text-amber-400', bg: 'bg-amber-500/10' },
        { label: 'Work History', value: stats.experiences, icon: Briefcase, color: 'text-blue-400', bg: 'bg-blue-500/10' },
        { label: 'Social Proof', value: stats.achievements, icon: Trophy, color: 'text-purple-400', bg: 'bg-purple-500/10' },
        { label: 'LaTeX Assets', value: stats.templates, icon: FileText, color: 'text-pink-400', bg: 'bg-pink-500/10' },
        { label: 'Generated', value: stats.resumes, icon: Sparkles, color: 'text-primary-400', bg: 'bg-primary-500/10' },
    ];

    if (loading) {
        return (
            <div className="pt-32 flex items-center justify-center min-h-screen">
                <div className="w-10 h-10 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                <div>
                    <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-3">
                        Welcome back, <span className="gradient-text">{user?.full_name?.split(' ')[0]}</span>
                    </h1>
                    <p className="text-slate-500 font-medium">Your career intelligence dashboard is ready.</p>
                </div>
                <Link href="/generate" className="btn-primary flex items-center gap-2 px-8 py-3.5">
                    Generate Resume <ArrowRight size={18} />
                </Link>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-6 gap-6 mb-12">
                {statCards.map(({ label, value, icon: Icon, color, bg }) => (
                    <div key={label} className="card group hover:translate-y-[-4px] cursor-default">
                        <div className={`w-12 h-12 rounded-2xl ${bg} flex items-center justify-center mb-4 transition-transform group-hover:scale-110 duration-500`}>
                            <Icon size={20} className={color} />
                        </div>
                        <p className="text-3xl font-display font-bold text-white mb-1 tracking-tight">{value}</p>
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</p>
                    </div>
                ))}
            </div>

            {/* Quick Actions & Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Secondary Actions */}
                <div className="lg:col-span-1 space-y-6">
                    <h2 className="text-sm font-bold text-slate-400 uppercase tracking-[0.2em] mb-4">Intelligence Management</h2>

                    <Link href="/profile" className="card flex items-center gap-5 group border-white/5 hover:border-emerald-500/20">
                        <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center shrink-0 group-hover:bg-emerald-500/20 transition-colors">
                            <Plus size={22} className="text-emerald-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-bold text-white text-lg">Career Data</p>
                            <p className="text-xs text-slate-500">Update verified experience</p>
                        </div>
                        <ArrowRight size={18} className="text-slate-700 group-hover:text-emerald-400 transition-all group-hover:translate-x-1" />
                    </Link>

                    <Link href="/templates" className="card flex items-center gap-5 group border-white/5 hover:border-amber-500/20">
                        <div className="w-14 h-14 rounded-2xl bg-amber-500/10 flex items-center justify-center shrink-0 group-hover:bg-amber-500/20 transition-colors">
                            <FileText size={22} className="text-amber-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-bold text-white text-lg">LaTeX Themes</p>
                            <p className="text-xs text-slate-500">Manage visual templates</p>
                        </div>
                        <ArrowRight size={18} className="text-slate-700 group-hover:text-amber-400 transition-all group-hover:translate-x-1" />
                    </Link>
                </div>

                {/* Recent Resumes */}
                <div className="lg:col-span-2">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-sm font-bold text-slate-400 uppercase tracking-[0.2em]">Recent Generation Activity</h2>
                        {recentResumes.length > 0 && (
                            <Link href="/history" className="text-xs font-bold text-primary-400 hover:text-white transition-colors uppercase tracking-widest">
                                Comprehensive History →
                            </Link>
                        )}
                    </div>

                    <div className="card border-white/5 p-4 min-h-[300px]">
                        {recentResumes.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full py-20 opacity-50">
                                <Sparkles size={40} className="text-slate-600 mb-4" />
                                <p className="text-slate-500 text-sm font-medium">No resume artifacts synthesized yet.</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {recentResumes.map(r => (
                                    <div key={r.id} className="flex items-center justify-between p-4 rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all duration-300 group">
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-bold text-white truncate group-hover:text-primary-400 transition-colors">
                                                {r.job_description.slice(0, 70)}…
                                            </p>
                                            <div className="flex items-center gap-3 mt-1.5">
                                                <span className="text-[10px] font-bold text-slate-500 bg-white/5 px-2 py-0.5 rounded-full">v{r.version}</span>
                                                <span className="text-[10px] font-medium text-slate-600">{new Date(r.created_at).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                        {r.match_score !== null && (
                                            <div className="ml-6 flex flex-col items-center">
                                                <div className="text-lg font-display font-bold text-white">{Math.round(r.match_score)}%</div>
                                                <div className="text-[10px] font-bold text-slate-600 uppercase">Match</div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

