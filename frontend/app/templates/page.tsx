'use client';

import React, { useState, useEffect } from 'react';
import { api, ResumeTemplate } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Plus, Trash2, FileText, Edit, Clock, Hash } from 'lucide-react';

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    const load = async () => {
        try { setTemplates(await api.get<ResumeTemplate[]>('/api/templates')); } catch { }
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this template?')) return;
        await api.delete(`/api/templates/${id}`);
        load();
    };

    const getPlaceholders = (t: ResumeTemplate) => {
        const matches = t.latex_content.match(/%%[A-Z_]+%%/g);
        return matches ? [...new Set(matches)] : [];
    };

    if (loading) {
        return (
            <div className="pt-24 flex items-center justify-center min-h-screen">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="pt-24 pb-16 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">LaTeX Templates</h1>
                    <p className="text-gray-400">Manage your resume templates with %%PLACEHOLDER%% markers.</p>
                </div>
                <button
                    onClick={() => router.push('/templates/editor')}
                    className="btn-primary flex items-center gap-1.5"
                >
                    <Plus size={16} /> New Template
                </button>
            </div>

            {templates.length === 0 ? (
                <div className="card text-center py-16">
                    <FileText size={48} className="text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">No templates yet</h3>
                    <p className="text-gray-500 text-sm mb-6 max-w-md mx-auto">
                        Create a LaTeX template with placeholders like %%SKILLS%%, %%SUMMARY%%, %%PROJECTS%%, and %%EXPERIENCE%%. The AI will fill these in.
                    </p>
                    <button onClick={() => router.push('/templates/editor')} className="btn-primary">
                        Create Your First Template
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {templates.map(t => {
                        const placeholders = getPlaceholders(t);
                        return (
                            <div key={t.id} className="card group">
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                                            <FileText size={18} className="text-indigo-400" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-white">{t.name}</h3>
                                            <p className="text-xs text-gray-500 flex items-center gap-1">
                                                <Clock size={10} /> {new Date(t.created_at).toLocaleDateString()}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex gap-1">
                                        <button
                                            onClick={() => router.push(`/templates/editor?id=${t.id}`)}
                                            className="p-1.5 rounded-lg hover:bg-indigo-500/10 text-gray-500 hover:text-indigo-400 transition-colors"
                                        >
                                            <Edit size={14} />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(t.id)}
                                            className="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-500 hover:text-red-400 transition-colors"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>

                                {/* Preview snippet */}
                                <pre className="text-xs text-gray-500 bg-surface-800/30 rounded-lg p-3 mb-3 overflow-hidden max-h-24 leading-relaxed font-mono">
                                    {t.latex_content.slice(0, 200)}…
                                </pre>

                                {/* Placeholders */}
                                {placeholders.length > 0 && (
                                    <div className="flex flex-wrap gap-1">
                                        {placeholders.map(p => (
                                            <span key={p} className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 flex items-center gap-1">
                                                <Hash size={8} />{p.replace(/%%/g, '')}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
