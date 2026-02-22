'use client';

import React, { useState, useEffect } from 'react';
import { api, Experience } from '@/lib/api';
import { Plus, Pencil, Trash2, X, Briefcase } from 'lucide-react';

export default function ExperiencesManager() {
    const [experiences, setExperiences] = useState<Experience[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editing, setEditing] = useState<Experience | null>(null);
    const [form, setForm] = useState({
        company: '', role: '', description: '', technologies: '',
        location: '', is_current: false, start_date: '', end_date: '',
    });

    const load = async () => {
        try { setExperiences(await api.get<Experience[]>('/api/experiences')); } catch { }
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const openNew = () => {
        setEditing(null);
        setForm({ company: '', role: '', description: '', technologies: '', location: '', is_current: false, start_date: '', end_date: '' });
        setShowForm(true);
    };

    const openEdit = (e: Experience) => {
        setEditing(e);
        setForm({
            company: e.company, role: e.role, description: e.description,
            technologies: e.technologies || '', location: e.location || '',
            is_current: e.is_current, start_date: e.start_date || '', end_date: e.end_date || '',
        });
        setShowForm(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const payload = {
            ...form,
            technologies: form.technologies || null, location: form.location || null,
            start_date: form.start_date || null, end_date: form.is_current ? null : (form.end_date || null),
        };
        if (editing) { await api.put(`/api/experiences/${editing.id}`, payload); }
        else { await api.post('/api/experiences', payload); }
        setShowForm(false);
        load();
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this experience?')) return;
        await api.delete(`/api/experiences/${id}`);
        load();
    };

    if (loading) return <div className="flex justify-center py-10"><div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-xl font-display font-bold text-white tracking-tight">Professional Trajectory</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">{experiences.length} Career Nodes</p>
                </div>
                <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm px-5 py-2.5">
                    <Plus size={16} /> Log Experience
                </button>
            </div>

            {experiences.length === 0 ? (
                <div className="text-center py-20 card border-dashed border-white/5 opacity-50">
                    <Briefcase size={40} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">No professional history recorded. Initialize your career ledger.</p>
                </div>
            ) : (
                <div className="relative space-y-8 before:absolute before:inset-0 before:ml-6 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-emerald-500/20 before:via-slate-800 before:to-transparent">
                    {experiences.map((exp, i) => (
                        <div key={exp.id} className="relative pl-12 group animate-slide-up" style={{ animationDelay: `${i * 100}ms` }}>
                            {/* Dot */}
                            <div className="absolute left-0 top-1 w-12 h-12 flex items-center justify-center">
                                <div className="w-3 h-3 rounded-full bg-slate-950 border-2 border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] group-hover:scale-125 transition-transform" />
                            </div>

                            <div className="card border-white/5 group-hover:border-emerald-500/20 transition-all duration-300">
                                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                                    <div>
                                        <h3 className="text-lg font-bold text-white group-hover:text-emerald-400 transition-colors uppercase tracking-tight">{exp.role}</h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-sm font-bold text-slate-300">{exp.company}</span>
                                            {exp.location && (
                                                <>
                                                    <span className="w-1 h-1 rounded-full bg-slate-700" />
                                                    <span className="text-xs font-medium text-slate-500">{exp.location}</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-white/5 px-3 py-1 rounded-full">
                                            {exp.start_date || 'N/A'} – {exp.is_current ? <span className="text-emerald-400">Current</span> : (exp.end_date || 'N/A')}
                                        </div>
                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
                                            <button onClick={() => openEdit(exp)} className="p-2 rounded-xl hover:bg-white/5 text-slate-500 hover:text-white transition-colors"><Pencil size={14} /></button>
                                            <button onClick={() => handleDelete(exp.id)} className="p-2 rounded-xl hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"><Trash2 size={14} /></button>
                                        </div>
                                    </div>
                                </div>

                                <p className="text-sm text-slate-400 leading-relaxed mb-5">{exp.description}</p>

                                {exp.technologies && (
                                    <div className="flex flex-wrap gap-2">
                                        {exp.technologies.split(',').map((t, j) => (
                                            <span key={j} className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white/[0.03] text-slate-500 border border-white/5 uppercase tracking-tighter">
                                                {t.trim()}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Modal */}
            {showForm && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
                    <div className="w-full max-w-lg my-8 animate-slide-up">
                        <form onSubmit={handleSubmit} className="card border-white/10 shadow-2xl space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-2xl font-display font-bold text-white tracking-tight">
                                    {editing ? 'Update Record' : 'Log Tenure'}
                                </h3>
                                <button type="button" onClick={() => setShowForm(false)} className="p-2 hover:bg-white/5 rounded-xl text-slate-500 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Company/Entity</label>
                                        <input value={form.company} onChange={e => setForm({ ...form, company: e.target.value })} className="input-field" placeholder="e.g. OpenAI" required />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Official Role</label>
                                        <input value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} className="input-field" placeholder="e.g. Senior Researcher" required />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Key Contributions & Responsibilities</label>
                                    <textarea
                                        value={form.description}
                                        onChange={e => setForm({ ...form, description: e.target.value })}
                                        className="input-field min-h-[120px] py-3"
                                        placeholder="Outline high-impact achievements..."
                                        required
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Infrastructure/Stack</label>
                                        <input value={form.technologies} onChange={e => setForm({ ...form, technologies: e.target.value })} className="input-field" placeholder="K8s, Terraform..." />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Deployment Location</label>
                                        <input value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} className="input-field" placeholder="Remote / NY" />
                                    </div>
                                </div>

                                <div className="flex items-center gap-3 py-2 px-1">
                                    <div
                                        onClick={() => setForm({ ...form, is_current: !form.is_current })}
                                        className={`w-10 h-6 rounded-full transition-colors cursor-pointer relative flex items-center ${form.is_current ? 'bg-emerald-500' : 'bg-slate-800'}`}
                                    >
                                        <div className={`w-4 h-4 rounded-full bg-white transition-transform shadow-sm absolute ${form.is_current ? 'translate-x-5' : 'translate-x-1'}`} />
                                    </div>
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest cursor-pointer" onClick={() => setForm({ ...form, is_current: !form.is_current })}>
                                        Active Tenure
                                    </label>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Commencement</label>
                                        <input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} className="input-field" />
                                    </div>
                                    {!form.is_current && (
                                        <div>
                                            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Termination</label>
                                            <input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} className="input-field" />
                                        </div>
                                    )}
                                </div>
                            </div>

                            <button type="submit" className="btn-primary w-full py-3.5 text-lg">
                                {editing ? 'Finalize Changes' : 'Commit Experience'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

