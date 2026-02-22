'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api, ResumeTemplate, GeneratedResume, ChatResponse, getToken } from '@/lib/api';
import {
    Sparkles, FileText, ClipboardPaste, ChevronRight,
    CheckCircle2, XCircle, TrendingUp, Send, Bot, User, Loader2,
    Download, AlertTriangle
} from 'lucide-react';

type Step = 'jd' | 'match' | 'generate' | 'result';

interface AnalysisData {
    required_skill_match: number;
    project_relevance: number;
    keyword_alignment: number;
    total_score: number;
    matched_skills: string[];
    missing_skills: string[];
    ranked_projects: { title: string; relevance_score: number; matching_technologies: string[] }[];
    improvement_suggestions: string[];
}

export default function GeneratePage() {
    const [step, setStep] = useState<Step>('jd');
    const [jdText, setJdText] = useState('');
    const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<string>('');
    const [generating, setGenerating] = useState(false);
    const [result, setResult] = useState<GeneratedResume | null>(null);
    const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
    const [error, setError] = useState('');

    // Chat state
    const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [chatLoading, setChatLoading] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        api.get<ResumeTemplate[]>('/api/templates').then(setTemplates).catch(() => { });
    }, []);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatMessages]);

    const handleGenerate = async () => {
        if (!selectedTemplate || !jdText.trim()) return;
        setGenerating(true);
        setError('');
        try {
            const resume = await api.post<GeneratedResume>('/api/resumes/generate', {
                template_id: selectedTemplate,
                job_description: jdText,
            });
            setResult(resume);

            // Fetch analysis
            try {
                const a = await api.get<AnalysisData>(`/api/resumes/${resume.id}/analysis`);
                setAnalysis(a);
            } catch { }

            setStep('result');
        } catch (err: any) {
            setError(err.message || 'Generation failed');
        }
        setGenerating(false);
    };

    const handleChat = async () => {
        if (!chatInput.trim() || !result) return;
        const userMsg = chatInput.trim();
        setChatInput('');
        setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setChatLoading(true);
        try {
            const resp = await api.post<ChatResponse>('/api/chat/refine', {
                resume_id: result.id,
                message: userMsg,
                history: chatMessages,
            });
            setChatMessages(prev => [...prev, { role: 'assistant', content: resp.reply }]);
            if (resp.updated_latex) {
                setResult({ ...result, latex_output: resp.updated_latex });
            }
            if (!resp.validation_passed && resp.validation_errors.length > 0) {
                setChatMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `⚠️ Integrity Alert: ${resp.validation_errors.join(', ')}`
                }]);
            }
        } catch (err: any) {
            setChatMessages(prev => [...prev, { role: 'assistant', content: `Neural Nexus Error: ${err.message}` }]);
        }
        setChatLoading(false);
    };

    const scoreColor = (score: number) => score >= 70 ? 'text-emerald-400' : score >= 40 ? 'text-amber-400' : 'text-rose-400';
    const scoreGradient = (score: number) => score >= 70 ? '#10b981' : score >= 40 ? '#facc15' : '#f43f5e';

    const steps: { key: Step; label: string }[] = [
        { key: 'jd', label: 'Analysis' },
        { key: 'match', label: 'Template' },
        { key: 'generate', label: 'Forge' },
        { key: 'result', label: 'Export' },
    ];

    return (
        <div className="relative min-h-screen">
            <div className="bg-mesh" />

            <div className="pt-32 pb-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="mb-12 animate-fade-in text-center md:text-left">
                    <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-3 tracking-tight">Generate Resume</h1>
                    <p className="text-slate-400 max-w-2xl leading-relaxed">
                        Input target parameters. Our zero-hallucination engine will synthesize a high-integrity LaTeX resume based on your career ledger.
                    </p>
                </div>

                {/* Extended Stepper */}
                <div className="flex items-center gap-4 mb-12 overflow-x-auto pb-4 no-scrollbar">
                    {steps.map((s, i) => (
                        <React.Fragment key={s.key}>
                            <div className={`flex items-center gap-3 px-6 py-3 rounded-2xl text-sm font-bold uppercase tracking-widest transition-all duration-500 border-2 ${step === s.key
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                : steps.indexOf(steps.find(st => st.key === step)!) > i
                                    ? 'text-emerald-500/50 border-emerald-500/20'
                                    : 'text-slate-600 border-white/5 opacity-50'
                                }`}>
                                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs border ${step === s.key ? 'border-emerald-500/50 bg-emerald-500/20' : 'border-current opacity-60'}`}>
                                    {steps.indexOf(steps.find(st => st.key === step)!) > i ? <CheckCircle2 size={16} /> : i + 1}
                                </span>
                                <span className="whitespace-nowrap">{s.label}</span>
                            </div>
                            {i < steps.length - 1 && <div className="h-px w-8 bg-white/5 hidden md:block" />}
                        </React.Fragment>
                    ))}
                </div>

                {/* Step 1: JD Input */}
                {step === 'jd' && (
                    <div className="card animate-fade-in max-w-4xl mx-auto">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center">
                                <ClipboardPaste size={20} className="text-primary-400" />
                            </div>
                            <h2 className="text-2xl font-display font-bold text-white tracking-tight">Target Parameters</h2>
                        </div>
                        <p className="text-sm text-slate-500 mb-6 font-medium">Paste the full job description or target profile requirements below.</p>
                        <textarea
                            value={jdText}
                            onChange={e => setJdText(e.target.value)}
                            className="input-field min-h-[350px] font-mono text-sm leading-relaxed p-6"
                            placeholder="e.g. Seeking a Senior Engineer with 5+ years experience in distributed systems and Rust..."
                        />
                        <div className="flex justify-end mt-8">
                            <button
                                onClick={() => setStep('match')}
                                disabled={!jdText.trim()}
                                className="btn-primary flex items-center gap-3 text-lg px-8 py-4"
                            >
                                Analyze Requirements <ChevronRight size={20} />
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 2: Template Selection */}
                {step === 'match' && (
                    <div className="card animate-fade-in max-w-4xl mx-auto">
                        <div className="flex items-center gap-3 mb-8">
                            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                                <FileText size={20} className="text-amber-400" />
                            </div>
                            <h2 className="text-2xl font-display font-bold text-white tracking-tight">Visual Framework</h2>
                        </div>

                        {templates.length === 0 ? (
                            <div className="text-center py-20 border-2 border-dashed border-white/5 rounded-3xl opacity-50">
                                <FileText size={48} className="text-slate-600 mx-auto mb-4" />
                                <p className="text-slate-500">No LaTeX templates detected. Initialize your registry.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
                                {templates.map(t => (
                                    <button
                                        key={t.id}
                                        onClick={() => setSelectedTemplate(t.id)}
                                        className={`flex items-center gap-4 text-left p-6 rounded-3xl border-2 transition-all duration-300 ${selectedTemplate === t.id
                                            ? 'border-emerald-500 bg-emerald-500/10 shadow-[0_0_30px_rgba(16,185,129,0.1)]'
                                            : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                                            }`}
                                    >
                                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${selectedTemplate === t.id ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                                            <FileText size={24} />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-white uppercase tracking-tight">{t.name}</h3>
                                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">High-Precision LaTeX</p>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}

                        <div className="flex items-center justify-between border-t border-white/5 pt-8">
                            <button onClick={() => setStep('jd')} className="btn-secondary px-8">Back</button>
                            <button
                                onClick={handleGenerate}
                                disabled={!selectedTemplate || generating}
                                className="btn-primary flex items-center gap-3 text-lg px-8 py-4"
                            >
                                {generating ? (
                                    <><Loader2 size={20} className="animate-spin" /> Synthesizing…</>
                                ) : (
                                    <><Sparkles size={20} /> Forge Resume</>
                                )}
                            </button>
                        </div>

                        {error && (
                            <div className="mt-6 flex items-center gap-3 px-5 py-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-400 text-sm font-medium animate-slide-up">
                                <AlertTriangle size={18} /> {error}
                            </div>
                        )}
                    </div>
                )}

                {/* Step 4: Result */}
                {step === 'result' && result && (
                    <div className="animate-fade-in space-y-8">
                        {/* Summary Header */}
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 card border-emerald-500/20 bg-emerald-500/[0.02]">
                            <div>
                                <h1 className="text-2xl font-display font-bold text-white tracking-tight">Resume Synthesis Complete</h1>
                                <p className="text-sm text-slate-400 mt-1">Version {result.id.slice(0, 8)} • Crafted with {selectedTemplate && templates.find(t => t.id === selectedTemplate)?.name}</p>
                            </div>
                            <div className="flex gap-3">
                                {result.pdf_path && (
                                    <a
                                        href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resumes/${result.id}/pdf?token=${getToken()}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="btn-primary flex items-center gap-3 px-6"
                                    >
                                        <Download size={18} /> Download High-End PDF
                                    </a>
                                )}
                                <button onClick={() => { setStep('jd'); setResult(null); setAnalysis(null); setChatMessages([]); }} className="btn-secondary px-6">
                                    Generate New
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Main content */}
                            <div className="lg:col-span-2 space-y-8">
                                {/* Match Score */}
                                {analysis && (
                                    <div className="card">
                                        <div className="flex items-center justify-between mb-8">
                                            <h2 className="text-xl font-display font-bold text-white mb-4 flex items-center gap-3">
                                                <TrendingUp size={22} className="text-primary-400" /> Synthesis Analysis
                                            </h2>
                                            <div className="px-4 py-1.5 rounded-full bg-slate-900 border border-white/5 text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Match Indices</div>
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
                                            {[
                                                { label: 'Integrity', value: analysis.total_score },
                                                { label: 'Domain Fit', value: analysis.required_skill_match },
                                                { label: 'Experience', value: analysis.project_relevance },
                                                { label: 'Semantic', value: analysis.keyword_alignment },
                                            ].map(s => (
                                                <div key={s.label} className="text-center group">
                                                    <div className="relative w-24 h-24 mx-auto mb-3">
                                                        <svg className="w-24 h-24 -rotate-90 group-hover:scale-110 transition-transform duration-500" viewBox="0 0 36 36">
                                                            <circle cx="18" cy="18" r="16" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1.5" />
                                                            <circle cx="18" cy="18" r="16" fill="none" stroke={scoreGradient(s.value)} strokeWidth="2.5"
                                                                strokeDasharray={`${s.value} 100`} strokeLinecap="round"
                                                                className="drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]" />
                                                        </svg>
                                                        <span className={`absolute inset-0 flex items-center justify-center text-xl font-display font-bold ${scoreColor(s.value)}`}>
                                                            {Math.round(s.value)}
                                                        </span>
                                                    </div>
                                                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{s.label}</p>
                                                </div>
                                            ))}
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-white/5">
                                            <div>
                                                <h3 className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                                    <CheckCircle2 size={12} /> Validated Alignments
                                                </h3>
                                                <div className="flex flex-wrap gap-2">
                                                    {analysis.matched_skills.map(s => (
                                                        <span key={s} className="text-[10px] font-bold px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 uppercase tracking-tight">
                                                            {s}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                            <div>
                                                <h3 className="text-[10px] font-bold text-rose-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                                    <AlertTriangle size={12} /> Optimization Gaps
                                                </h3>
                                                <div className="flex flex-wrap gap-2">
                                                    {analysis.missing_skills.map(s => (
                                                        <span key={s} className="text-[10px] font-bold px-3 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/10 uppercase tracking-tight">
                                                            {s}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* LaTeX Output */}
                                <div className="card">
                                    <div className="flex items-center justify-between mb-6">
                                        <h2 className="text-xl font-display font-bold text-white flex items-center gap-3">
                                            <FileText size={22} className="text-slate-400" /> LaTeX Buffer
                                        </h2>
                                        <div className="px-4 py-1.5 rounded-full bg-slate-900 border border-white/5 text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Source Code</div>
                                    </div>
                                    <div className="relative group">
                                        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-transparent rounded-2xl pointer-events-none" />
                                        <pre className="text-xs text-slate-400 bg-black/40 border border-white/5 rounded-2xl p-6 overflow-auto max-h-[800px] font-mono leading-relaxed whitespace-pre-wrap custom-scrollbar">
                                            {result.latex_output}
                                        </pre>
                                    </div>
                                </div>
                            </div>

                            {/* Chat Panel */}
                            <div className="lg:sticky lg:top-28 h-fit">
                                <div className="card flex flex-col h-[750px] shadow-3xl">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                                            <Bot size={22} className="text-purple-400" />
                                        </div>
                                        <h2 className="text-xl font-display font-bold text-white tracking-tight">Neural Nexus Chat</h2>
                                    </div>
                                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-6">Factual Integrity Guardrails Active</p>

                                    <div className="flex-1 overflow-y-auto space-y-6 mb-6 pr-2 custom-scrollbar">
                                        {chatMessages.length === 0 && (
                                            <div className="text-center py-20 opacity-40">
                                                <Bot size={48} className="mx-auto mb-4 text-slate-600" />
                                                <p className="text-sm font-medium text-slate-500">Ask for bullets adjustments, tone shifts, or project focuses.</p>
                                            </div>
                                        )}
                                        {chatMessages.map((msg, i) => (
                                            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border-2 ${msg.role === 'user'
                                                    ? 'bg-primary-500/20 border-primary-500/30'
                                                    : 'bg-purple-500/20 border-purple-500/30'}`}>
                                                    {msg.role === 'user' ? <User size={14} className="text-primary-400" /> : <Bot size={14} className="text-purple-400" />}
                                                </div>
                                                <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                                                    ? 'bg-primary-500/10 text-primary-50 text-right'
                                                    : msg.content.startsWith('⚠️')
                                                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold'
                                                        : 'bg-white/[0.04] text-slate-300'
                                                    }`}>
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))}
                                        {chatLoading && (
                                            <div className="flex gap-3 animate-pulse">
                                                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center">
                                                    <Loader2 size={14} className="text-slate-500 animate-spin" />
                                                </div>
                                                <div className="px-4 py-3 rounded-2xl bg-white/[0.02] text-slate-600 text-sm">
                                                    Scanning Career Ledger…
                                                </div>
                                            </div>
                                        )}
                                        <div ref={chatEndRef} />
                                    </div>

                                    <div className="relative pt-4 border-t border-white/5">
                                        <input
                                            value={chatInput}
                                            onChange={e => setChatInput(e.target.value)}
                                            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleChat()}
                                            className="input-field py-4 pr-14 text-sm bg-white/5 border-white/10"
                                            placeholder="Request a resume adjustment…"
                                        />
                                        <button
                                            onClick={handleChat}
                                            disabled={chatLoading || !chatInput.trim()}
                                            className="absolute right-2 top-[calc(1rem+0.5rem)] w-10 h-10 rounded-xl bg-primary-500 text-slate-950 flex items-center justify-center hover:bg-primary-400 transition-all disabled:opacity-30 disabled:hover:bg-primary-500"
                                        >
                                            <Send size={18} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

