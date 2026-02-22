'use client';

import React, { useState, useEffect } from 'react';
import { api, GeneratedResume } from '@/lib/api';
import { Clock, Trash2, Download, Eye, FileText, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';

export default function HistoryPage() {
    const [resumes, setResumes] = useState<GeneratedResume[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const load = async () => {
        try { setResumes(await api.get<GeneratedResume[]>('/api/resumes')); } catch { }
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this resume?')) return;
        await api.delete(`/api/resumes/${id}`);
        load();
    };

    const scoreColor = (score: number) => score >= 70 ? 'text-emerald-400' : score >= 40 ? 'text-amber-400' : 'text-red-400';
    const scoreBg = (score: number) => score >= 70 ? 'bg-emerald-500/10' : score >= 40 ? 'bg-amber-500/10' : 'bg-red-500/10';

    if (loading) {
        return (
            <div className="pt-24 flex items-center justify-center min-h-screen">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="pt-24 pb-16 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Resume History</h1>
                <p className="text-gray-400">All your generated resumes, sorted by most recent.</p>
            </div>

            {resumes.length === 0 ? (
                <div className="card text-center py-16">
                    <Clock size={48} className="text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">No history yet</h3>
                    <p className="text-gray-500 text-sm mb-6">
                        Generated resumes will appear here.
                    </p>
                    <a href="/generate" className="btn-primary inline-flex items-center gap-1.5">
                        <Sparkles size={16} /> Generate Your First
                    </a>
                </div>
            ) : (
                <div className="space-y-3">
                    {resumes.map(r => {
                        const isExpanded = expandedId === r.id;
                        const matched = r.matched_skills ? JSON.parse(r.matched_skills) : [];
                        const missing = r.missing_skills ? JSON.parse(r.missing_skills) : [];

                        return (
                            <div key={r.id} className="card animate-fade-in">
                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                                        <FileText size={18} className="text-indigo-400" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-white truncate">{r.job_description.slice(0, 100)}…</p>
                                                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                                                    <span className="flex items-center gap-1"><Clock size={10} /> {new Date(r.created_at).toLocaleString()}</span>
                                                    <span>v{r.version}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 flex-shrink-0">
                                                {r.match_score !== null && (
                                                    <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${scoreColor(r.match_score)} ${scoreBg(r.match_score)}`}>
                                                        {Math.round(r.match_score)}%
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Action buttons */}
                                        <div className="flex items-center gap-2 mt-3">
                                            <button
                                                onClick={() => setExpandedId(isExpanded ? null : r.id)}
                                                className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
                                            >
                                                <Eye size={12} /> {isExpanded ? 'Hide' : 'View'} LaTeX
                                                {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                                            </button>
                                            {r.pdf_path && (
                                                <a
                                                    href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resumes/${r.id}/pdf`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                                                >
                                                    <Download size={12} /> PDF
                                                </a>
                                            )}
                                            <button
                                                onClick={() => handleDelete(r.id)}
                                                className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-400 transition-colors ml-auto"
                                            >
                                                <Trash2 size={12} /> Delete
                                            </button>
                                        </div>

                                        {/* Expanded content */}
                                        {isExpanded && (
                                            <div className="mt-4 space-y-3 animate-slide-up">
                                                {/* Skills breakdown */}
                                                {(matched.length > 0 || missing.length > 0) && (
                                                    <div className="grid grid-cols-2 gap-3">
                                                        <div>
                                                            <p className="text-xs font-semibold text-emerald-400 mb-1">Matched ({matched.length})</p>
                                                            <div className="flex flex-wrap gap-1">
                                                                {matched.map((s: string) => (
                                                                    <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300">{s}</span>
                                                                ))}
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs font-semibold text-red-400 mb-1">Missing ({missing.length})</p>
                                                            <div className="flex flex-wrap gap-1">
                                                                {missing.map((s: string) => (
                                                                    <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-300">{s}</span>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* LaTeX preview */}
                                                <pre className="text-xs text-gray-400 bg-surface-800/50 rounded-xl p-4 overflow-auto max-h-[400px] font-mono leading-relaxed whitespace-pre-wrap">
                                                    {r.latex_output}
                                                </pre>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
