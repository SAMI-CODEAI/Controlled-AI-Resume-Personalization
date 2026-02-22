'use client';

import React, { useState, useEffect } from 'react';
import { api, Project } from '@/lib/api';
import { Plus, Pencil, Trash2, X, FolderKanban, ExternalLink } from 'lucide-react';

export default function ProjectsManager() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editing, setEditing] = useState<Project | null>(null);
    const [form, setForm] = useState({ title: '', description: '', technologies: '', impact: '', domain: '', url: '', start_date: '', end_date: '' });

    const load = async () => {
        try { setProjects(await api.get<Project[]>('/api/projects')); } catch { }
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const openNew = () => {
        setEditing(null);
        setForm({ title: '', description: '', technologies: '', impact: '', domain: '', url: '', start_date: '', end_date: '' });
        setShowForm(true);
    };

    const openEdit = (p: Project) => {
        setEditing(p);
        setForm({
            title: p.title, description: p.description, technologies: p.technologies || '',
            impact: p.impact || '', domain: p.domain || '', url: p.url || '',
            start_date: p.start_date || '', end_date: p.end_date || '',
        });
        setShowForm(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const payload = {
            ...form,
            technologies: form.technologies || null, impact: form.impact || null,
            domain: form.domain || null, url: form.url || null,
            start_date: form.start_date || null, end_date: form.end_date || null,
        };
        if (editing) { await api.put(`/api/projects/${editing.id}`, payload); }
        else { await api.post('/api/projects', payload); }
        setShowForm(false);
        load();
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this project?')) return;
        await api.delete(`/api/projects/${id}`);
        load();
    };

    if (loading) return <div className="flex justify-center py-10"><div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-xl font-display font-bold text-white tracking-tight">Portfolio & Lab Work</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">{projects.length} Verified Projects</p>
                </div>
                <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm px-5 py-2.5">
                    <Plus size={16} /> Deploy Project
                </button>
            </div>

            {projects.length === 0 ? (
                <div className="text-center py-20 card border-dashed border-white/5 opacity-50">
                    <FolderKanban size={40} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">No project artifacts discovered. Start your build history.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {projects.map(p => (
                        <div key={p.id} className="card group hover:border-emerald-500/20 transition-all duration-300">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-lg font-bold text-white group-hover:text-emerald-400 transition-colors uppercase tracking-tight">{p.title}</h3>
                                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">{p.domain || 'General Domain'}</p>
                                </div>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
                                    <button onClick={() => openEdit(p)} className="p-2 rounded-xl hover:bg-white/5 text-slate-500 hover:text-white transition-colors"><Pencil size={14} /></button>
                                    <button onClick={() => handleDelete(p.id)} className="p-2 rounded-xl hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"><Trash2 size={14} /></button>
                                </div>
                            </div>

                            <p className="text-sm text-slate-400 line-clamp-3 mb-5 leading-relaxed">{p.description}</p>

                            {p.technologies && (
                                <div className="flex flex-wrap gap-2 mb-6">
                                    {p.technologies.split(',').map((t, i) => (
                                        <span key={i} className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 uppercase tracking-tighter">
                                            {t.trim()}
                                        </span>
                                    ))}
                                </div>
                            )}

                            <div className="flex items-center justify-between pt-4 border-t border-white/5">
                                <div className="flex items-center gap-2 text-[10px] font-bold text-slate-600 uppercase tracking-widest">
                                    {p.start_date && (
                                        <span>{new Date(p.start_date).getFullYear()} – {p.end_date ? new Date(p.end_date).getFullYear() : 'Now'}</span>
                                    )}
                                </div>
                                {p.url && (
                                    <a href={p.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-xs font-bold text-primary-400 hover:text-white transition-colors">
                                        <ExternalLink size={12} /> Live Source
                                    </a>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {showForm && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
                    <div className="w-full max-w-lg my-8 animate-slide-up">
                        <form onSubmit={handleSubmit} className="card border-white/10 shadow-2xl space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-2xl font-display font-bold text-white tracking-tight">
                                    {editing ? 'Project Refactor' : 'Project Initiation'}
                                </h3>
                                <button type="button" onClick={() => setShowForm(false)} className="p-2 hover:bg-white/5 rounded-xl text-slate-500 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Project Identifier</label>
                                    <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="input-field" placeholder="e.g. Neural Nexus Engine" required />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Industrial Domain</label>
                                        <input value={form.domain} onChange={e => setForm({ ...form, domain: e.target.value })} className="input-field" placeholder="e.g. FinTech" />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Live URL</label>
                                        <input value={form.url} onChange={e => setForm({ ...form, url: e.target.value })} className="input-field" placeholder="https://..." />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Core Architecture Description</label>
                                    <textarea
                                        value={form.description}
                                        onChange={e => setForm({ ...form, description: e.target.value })}
                                        className="input-field min-h-[100px] py-3"
                                        placeholder="Describe the technical implementation..."
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Technology Stack (Comma separated)</label>
                                    <input value={form.technologies} onChange={e => setForm({ ...form, technologies: e.target.value })} className="input-field" placeholder="React, Rust, PostgreSQL" />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Timeline Start</label>
                                        <input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} className="input-field" />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Timeline End</label>
                                        <input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} className="input-field" placeholder="Leave blank for Now" />
                                    </div>
                                </div>
                            </div>

                            <button type="submit" className="btn-primary w-full py-3.5 text-lg">
                                {editing ? 'Finalize Changes' : 'Commit Project'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

