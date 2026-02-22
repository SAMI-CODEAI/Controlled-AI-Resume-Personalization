'use client';

import React, { useState, useEffect } from 'react';
import { api, Achievement } from '@/lib/api';
import { Plus, Pencil, Trash2, X, Trophy } from 'lucide-react';

export default function AchievementsManager() {
    const [achievements, setAchievements] = useState<Achievement[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editing, setEditing] = useState<Achievement | null>(null);
    const [form, setForm] = useState({ title: '', description: '', date: '' });

    const load = async () => {
        try { setAchievements(await api.get<Achievement[]>('/api/achievements')); } catch { }
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const openNew = () => {
        setEditing(null);
        setForm({ title: '', description: '', date: '' });
        setShowForm(true);
    };

    const openEdit = (a: Achievement) => {
        setEditing(a);
        setForm({ title: a.title, description: a.description || '', date: a.date || '' });
        setShowForm(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const payload = {
            title: form.title,
            description: form.description.trim() || null,
            date: form.date || null
        };
        try {
            if (editing) { await api.put(`/api/achievements/${editing.id}`, payload); }
            else { await api.post('/api/achievements', payload); }
            setShowForm(false);
            load();
        } catch (err: any) {
            console.error('Achievement submission failed:', err);
            alert(err.message || 'Failed to save achievement');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this achievement?')) return;
        await api.delete(`/api/achievements/${id}`);
        load();
    };

    if (loading) return <div className="flex justify-center py-10"><div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-xl font-display font-bold text-white tracking-tight">Social Proof & Accolades</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">{achievements.length} Verified Achievements</p>
                </div>
                <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm px-5 py-2.5">
                    <Plus size={16} /> Log Accolade
                </button>
            </div>

            {achievements.length === 0 ? (
                <div className="text-center py-20 card border-dashed border-white/5 opacity-50">
                    <Trophy size={40} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">No professional accolades recorded. Start your hall of fame.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {achievements.map(a => (
                        <div key={a.id} className="card group hover:border-amber-500/20 transition-all duration-300">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                                        <Trophy size={18} className="text-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.2)]" />
                                    </div>
                                    <div>
                                        <h3 className="text-base font-bold text-white group-hover:text-amber-400 transition-colors tracking-tight">{a.title}</h3>
                                        {a.date && <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">{new Date(a.date).toLocaleDateString(undefined, { year: 'numeric', month: 'short' })}</p>}
                                    </div>
                                </div>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
                                    <button onClick={() => openEdit(a)} className="p-2 rounded-lg hover:bg-white/5 text-slate-500 hover:text-white transition-colors"><Pencil size={14} /></button>
                                    <button onClick={() => handleDelete(a.id)} className="p-2 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"><Trash2 size={14} /></button>
                                </div>
                            </div>
                            {a.description && <p className="text-sm text-slate-400 leading-relaxed mt-2">{a.description}</p>}
                        </div>
                    ))}
                </div>
            )}

            {/* Modal */}
            {showForm && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
                    <div className="w-full max-w-md animate-slide-up">
                        <form onSubmit={handleSubmit} className="card border-white/10 shadow-2xl space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-2xl font-display font-bold text-white tracking-tight">
                                    {editing ? 'Refine Accolade' : 'New Accolade'}
                                </h3>
                                <button type="button" onClick={() => setShowForm(false)} className="p-2 hover:bg-white/5 rounded-xl text-slate-500 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Achievement Focus</label>
                                    <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="input-field" placeholder="e.g. Forbes 30 Under 30" required />
                                </div>

                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Evidence / Context</label>
                                    <textarea
                                        value={form.description}
                                        onChange={e => setForm({ ...form, description: e.target.value })}
                                        className="input-field min-h-[100px] py-3"
                                        placeholder="Briefly describe the significance..."
                                    />
                                </div>

                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Conferred Date</label>
                                    <input type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} className="input-field" />
                                </div>
                            </div>

                            <button type="submit" className="btn-primary w-full py-3.5 text-lg">
                                {editing ? 'Finalize Changes' : 'Commit Achievement'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

