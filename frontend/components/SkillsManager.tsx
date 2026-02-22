'use client';

import React, { useState, useEffect } from 'react';
import { api, Skill } from '@/lib/api';
import { Plus, Pencil, Trash2, Star, X, Code2 } from 'lucide-react';

export default function SkillsManager() {
    const [skills, setSkills] = useState<Skill[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editing, setEditing] = useState<Skill | null>(null);
    const [form, setForm] = useState({ name: '', category: '', proficiency_level: 3 });

    const load = async () => {
        try {
            const data = await api.get<Skill[]>('/api/skills');
            setSkills(data);
        } catch { }
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const openNew = () => {
        setEditing(null);
        setForm({ name: '', category: '', proficiency_level: 3 });
        setShowForm(true);
    };

    const openEdit = (s: Skill) => {
        setEditing(s);
        setForm({ name: s.name, category: s.category || '', proficiency_level: s.proficiency_level });
        setShowForm(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const payload = { ...form, category: form.category || null };
        if (editing) {
            await api.put(`/api/skills/${editing.id}`, payload);
        } else {
            await api.post('/api/skills', payload);
        }
        setShowForm(false);
        load();
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this skill?')) return;
        await api.delete(`/api/skills/${id}`);
        load();
    };

    // Group by category
    const grouped = skills.reduce<Record<string, Skill[]>>((acc, s) => {
        const cat = s.category || 'Uncategorized';
        (acc[cat] = acc[cat] || []).push(s);
        return acc;
    }, {});

    if (loading) return <div className="flex justify-center py-10"><div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-xl font-display font-bold text-white tracking-tight">Technical Proficiency</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">{skills.length} Validated Skills</p>
                </div>
                <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm px-5 py-2.5">
                    <Plus size={16} /> Add Competency
                </button>
            </div>

            {skills.length === 0 ? (
                <div className="text-center py-20 card border-dashed border-white/5 opacity-50">
                    <Code2 size={40} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">No skill matrices detected. Initialize your profile.</p>
                </div>
            ) : (
                <div className="space-y-8">
                    {Object.entries(grouped).map(([cat, items]) => (
                        <div key={cat} className="animate-slide-up">
                            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4 ml-1">{cat}</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                {items.map(s => (
                                    <div key={s.id} className="group flex items-center justify-between px-4 py-3 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-emerald-500/20 hover:bg-white/[0.04] transition-all duration-300">
                                        <div className="flex flex-col gap-1">
                                            <span className="text-sm font-bold text-white group-hover:text-emerald-400 transition-colors">{s.name}</span>
                                            <div className="flex gap-1">
                                                {Array.from({ length: 5 }).map((_, i) => (
                                                    <Star key={i} size={10} className={i < s.proficiency_level ? 'text-emerald-400 fill-emerald-400' : 'text-slate-800'} />
                                                ))}
                                            </div>
                                        </div>
                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => openEdit(s)} className="p-2 rounded-lg hover:bg-white/5 text-slate-500 hover:text-white transition-colors"><Pencil size={14} /></button>
                                            <button onClick={() => handleDelete(s.id)} className="p-2 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"><Trash2 size={14} /></button>
                                        </div>
                                    </div>
                                ))}
                            </div>
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
                                    {editing ? 'Refine Competency' : 'New Competency'}
                                </h3>
                                <button type="button" onClick={() => setShowForm(false)} className="p-2 hover:bg-white/5 rounded-xl text-slate-500 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Skill Title</label>
                                    <input
                                        value={form.name}
                                        onChange={e => setForm({ ...form, name: e.target.value })}
                                        className="input-field"
                                        placeholder="e.g. Distributed Systems"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Domain Category</label>
                                    <input
                                        value={form.category}
                                        onChange={e => setForm({ ...form, category: e.target.value })}
                                        className="input-field"
                                        placeholder="e.g. Infrastructure"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Expertise Index (1-5)</label>
                                    <div className="flex gap-2">
                                        {[1, 2, 3, 4, 5].map(n => (
                                            <button
                                                key={n}
                                                type="button"
                                                onClick={() => setForm({ ...form, proficiency_level: n })}
                                                className={`flex-1 aspect-square rounded-xl border font-bold transition-all duration-300 ${n <= form.proficiency_level ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.15)]' : 'border-white/5 text-slate-600 hover:border-white/10'}`}
                                            >
                                                {n}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <button type="submit" className="btn-primary w-full py-3.5 text-lg">
                                {editing ? 'Confirm Changes' : 'Initialize Skill'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

