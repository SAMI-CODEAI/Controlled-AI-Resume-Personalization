'use client';

import React, { useState } from 'react';
import { Code2, FolderKanban, Briefcase, Trophy } from 'lucide-react';
import SkillsManager from '@/components/SkillsManager';
import ProjectsManager from '@/components/ProjectsManager';
import ExperiencesManager from '@/components/ExperiencesManager';
import AchievementsManager from '@/components/AchievementsManager';

const tabs = [
    { key: 'skills', label: 'Skills', icon: Code2 },
    { key: 'projects', label: 'Projects', icon: FolderKanban },
    { key: 'experiences', label: 'Experience', icon: Briefcase },
    { key: 'achievements', label: 'Achievements', icon: Trophy },
] as const;

type TabKey = typeof tabs[number]['key'];

export default function ProfilePage() {
    const [active, setActive] = useState<TabKey>('skills');

    return (
        <div className="relative min-h-screen">
            <div className="bg-mesh" />

            <div className="pt-32 pb-16 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="mb-12 animate-fade-in text-center md:text-left">
                    <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-3 tracking-tight">Career Architecture</h1>
                    <p className="text-slate-400 max-w-2xl leading-relaxed">
                        Curate your professional ledger. This data powers the zero-hallucination engine to craft your high-integrity resumes.
                    </p>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-12 overflow-x-auto pb-4 no-scrollbar border-b border-white/5">
                    {tabs.map(({ key, label, icon: Icon }) => (
                        <button
                            key={key}
                            onClick={() => setActive(key)}
                            className={`flex items-center gap-2.5 px-6 py-3 rounded-2xl text-sm font-bold uppercase tracking-widest transition-all duration-300 whitespace-nowrap ${active === key
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.1)]'
                                : 'text-slate-500 hover:text-slate-300 hover:bg-white/5 border border-transparent'
                                }`}
                        >
                            <Icon size={16} />
                            {label}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="animate-fade-in min-h-[400px]">
                    {active === 'skills' && <SkillsManager />}
                    {active === 'projects' && <ProjectsManager />}
                    {active === 'experiences' && <ExperiencesManager />}
                    {active === 'achievements' && <AchievementsManager />}
                </div>
            </div>
        </div>
    );
}

