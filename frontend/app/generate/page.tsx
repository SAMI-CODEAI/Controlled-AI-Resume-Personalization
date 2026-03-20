'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api, ResumeTemplate, GeneratedResume, ChatResponse, getToken } from '@/lib/api';
import {
    Sparkles, FileText, ClipboardPaste, ChevronRight,
    CheckCircle2, TrendingUp, Send, Bot, User, Loader2,
    Download, AlertTriangle, RefreshCw, Code, Eye, XCircle
} from 'lucide-react';
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

type Step = 'jd' | 'match' | 'result';

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function GeneratePage() {
    const [step, setStep] = useState<Step>('jd');
    const [jdText, setJdText] = useState('');
    const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<string>('');
    const [generating, setGenerating] = useState(false);
    const [result, setResult] = useState<GeneratedResume | null>(null);
    const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
    const [error, setError] = useState('');

    // Insights state
    const [showInsights, setShowInsights] = useState(true);

    // Editor & PDF state
    const [latexCode, setLatexCode] = useState('');
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [compiling, setCompiling] = useState(false);
    const [compileError, setCompileError] = useState('');
    const [activePanel, setActivePanel] = useState<'code' | 'preview'>('preview');
    const compileTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const currentPdfUrlRef = useRef<string | null>(null);

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

    // Compile LaTeX to PDF
    const compilePdf = useCallback(async (code: string) => {
        if (!code.trim()) return;
        setCompiling(true);
        setCompileError('');
        try {
            const token = getToken();
            const response = await fetch(`${API_BASE}/api/v1/compile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ latex: code }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: 'Compilation failed' }));
                throw new Error(err.detail || 'Compilation failed');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            // Revoke old URL to prevent memory leaks
            if (currentPdfUrlRef.current) URL.revokeObjectURL(currentPdfUrlRef.current);
            currentPdfUrlRef.current = url;
            setPdfUrl(url);
        } catch (err: any) {
            setCompileError(err.message || 'Compilation error');
        }
        setCompiling(false);
    }, []);

    // Debounced compile on LaTeX edit
    const handleLatexChange = useCallback((code: string) => {
        setLatexCode(code);
        if (compileTimer.current) clearTimeout(compileTimer.current);
        compileTimer.current = setTimeout(() => compilePdf(code), 800);
    }, [compilePdf]);

    // Cleanup object URL on unmount
    useEffect(() => () => {
        if (currentPdfUrlRef.current) URL.revokeObjectURL(currentPdfUrlRef.current);
    }, []);

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
            setLatexCode(resume.latex_output);

            try {
                const a = await api.get<AnalysisData>(`/api/resumes/${resume.id}/analysis`);
                setAnalysis(a);
            } catch { }

            // Trigger initial compile
            compilePdf(resume.latex_output);
            setStep('result');
        } catch (err: any) {
            setError(err.message || 'Generation failed');
        }
        setGenerating(false);
    };

    const handleDownloadPdf = () => {
        if (!pdfUrl) return;
        const a = document.createElement('a');
        a.href = pdfUrl;
        a.download = 'resume.pdf';
        a.click();
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
                setLatexCode(resp.updated_latex);
                compilePdf(resp.updated_latex);
            }
        } catch (err: any) {
            setChatMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
        }
        setChatLoading(false);
    };

    const scoreColor = (score: number) => score >= 70 ? 'text-emerald-400' : score >= 40 ? 'text-amber-400' : 'text-rose-400';
    const scoreGradient = (score: number) => score >= 70 ? '#10b981' : score >= 40 ? '#facc15' : '#f43f5e';

    const steps: { key: Step; label: string }[] = [
        { key: 'jd', label: 'Analysis' },
        { key: 'match', label: 'Template' },
        { key: 'result', label: 'Export' },
    ];

    return (
        <div className="relative min-h-screen">
            <div className="bg-mesh" />

            {/* Steps + header – hide when in result view */}
            {step !== 'result' && (
                <div className="pt-32 pb-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="mb-10 text-center md:text-left">
                        <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-3 tracking-tight">Generate Resume</h1>
                        <p className="text-slate-400 max-w-2xl leading-relaxed">
                            Input target parameters. Our zero-hallucination engine will synthesize a high-integrity LaTeX resume.
                        </p>
                    </div>

                    <div className="flex items-center gap-4 mb-10 overflow-x-auto pb-2 no-scrollbar">
                        {steps.map((s, i) => (
                            <React.Fragment key={s.key}>
                                <div className={`flex items-center gap-3 px-6 py-3 rounded-2xl text-sm font-bold uppercase tracking-widest border-2 transition-all duration-500 ${step === s.key
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
                            <p className="text-sm text-slate-500 mb-6 font-medium">Paste a job description or another person's resume. The AI will adapt your data to match its format.</p>
                            <textarea
                                value={jdText}
                                onChange={e => setJdText(e.target.value)}
                                className="input-field min-h-[350px] font-mono text-sm leading-relaxed p-6"
                                placeholder="Paste job description or target resume here…"
                            />
                            <div className="flex justify-end mt-8">
                                <button onClick={() => setStep('match')} disabled={!jdText.trim()} className="btn-primary flex items-center gap-3 text-lg px-8 py-4">
                                    Select Template <ChevronRight size={20} />
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
                                    <p className="text-slate-500">No LaTeX templates detected. Initialize your registry first.</p>
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
                                    {generating ? <><Loader2 size={20} className="animate-spin" /> Synthesizing…</> : <><Sparkles size={20} /> Forge Resume</>}
                                </button>
                            </div>

                            {error && (
                                <div className="mt-6 flex items-center gap-3 px-5 py-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-400 text-sm font-medium">
                                    <AlertTriangle size={18} /> {error}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* ─── OVERLEAF-STYLE RESULT VIEW ─── */}
            {step === 'result' && result && (
                <div className="h-screen flex flex-col pt-16">
                    {/* Top bar */}
                    <div className="flex items-center justify-between px-6 py-3 glass-light border-b border-indigo-500/10 shrink-0">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => { setStep('jd'); setResult(null); setAnalysis(null); setChatMessages([]); setPdfUrl(null); }}
                                className="btn-secondary text-xs px-4 py-2"
                            >
                                ← New
                            </button>
                            <span className="text-slate-400 text-sm font-medium">
                                Resume #{result.id.slice(-6)} •{' '}
                                <span className={scoreColor(result.match_score ?? 0)}>{Math.round(result.match_score ?? 0)}% match</span>
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            {/* Mobile toggle */}
                            <div className="flex md:hidden gap-1 bg-white/5 rounded-xl p-1">
                                <button onClick={() => setActivePanel('code')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${activePanel === 'code' ? 'bg-white/10 text-white' : 'text-slate-500'}`}>
                                    <Code size={14} />
                                </button>
                                <button onClick={() => setActivePanel('preview')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${activePanel === 'preview' ? 'bg-white/10 text-white' : 'text-slate-500'}`}>
                                    <Eye size={14} />
                                </button>
                            </div>
                            <button
                                onClick={() => compilePdf(latexCode)}
                                disabled={compiling}
                                className="flex items-center gap-1.5 btn-secondary text-xs px-4 py-2"
                            >
                                <RefreshCw size={13} className={compiling ? 'animate-spin' : ''} /> Recompile
                            </button>
                            <button
                                onClick={handleDownloadPdf}
                                disabled={!pdfUrl}
                                className="flex items-center gap-1.5 btn-primary text-xs px-4 py-2"
                            >
                                <Download size={13} /> Download PDF
                            </button>
                        </div>
                    </div>

                    {/* ─── MATCHING INSIGHTS OVERLAY ─── */}
                    {showInsights && analysis && (
                        <div className="mx-6 mt-4 mb-2 animate-slide-down">
                            <div className="card-glass border-indigo-500/20 p-5 relative overflow-hidden">
                                <button
                                    onClick={() => setShowInsights(false)}
                                    className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors"
                                >
                                    <XCircle size={18} />
                                </button>

                                <div className="flex flex-col md:flex-row gap-8">
                                    {/* Left: Score Circle */}
                                    <div className="flex flex-col items-center gap-2 shrink-0">
                                        <div className="relative w-20 h-20 flex items-center justify-center">
                                            <svg className="w-full h-full transform -rotate-90">
                                                <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-white/5" />
                                                <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="4" fill="transparent" strokeDasharray={226} strokeDashoffset={226 - (226 * (analysis.total_score || 0)) / 100} className={scoreColor(analysis.total_score)} style={{ transition: 'stroke-dashoffset 1s ease-out' }} />
                                            </svg>
                                            <span className={`absolute text-xl font-display font-bold ${scoreColor(analysis.total_score)}`}>{Math.round(analysis.total_score)}%</span>
                                        </div>
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Integrity Match</span>
                                    </div>

                                    {/* Middle: Highlights & Gaps */}
                                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <div className="flex items-center gap-2 mb-3">
                                                <CheckCircle2 size={14} className="text-emerald-400" />
                                                <h4 className="text-[11px] font-bold uppercase tracking-widest text-white">Matched Highlights</h4>
                                            </div>
                                            <div className="flex flex-wrap gap-1.5">
                                                {analysis.matched_skills.map(s => (
                                                    <span key={s} className="px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 text-[10px] font-bold uppercase">{s}</span>
                                                ))}
                                                {analysis.matched_skills.length === 0 && <span className="text-slate-600 text-[10px]">No specific mapping found...</span>}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2 mb-3">
                                                <AlertTriangle size={14} className="text-rose-400" />
                                                <h4 className="text-[11px] font-bold uppercase tracking-widest text-white">Missing Requirements</h4>
                                            </div>
                                            <div className="flex flex-wrap gap-1.5">
                                                {analysis.missing_skills.map(s => (
                                                    <span key={s} className="px-2 py-0.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/10 text-[10px] font-bold uppercase">{s}</span>
                                                ))}
                                                {analysis.missing_skills.length === 0 && <span className="text-slate-600 text-[10px]">All key requirements matched!</span>}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Right: Strategy Tips */}
                                    <div className="md:w-1/3 border-l border-white/5 pl-6">
                                        <div className="flex items-center gap-2 mb-3">
                                            <TrendingUp size={14} className="text-indigo-400" />
                                            <h4 className="text-[11px] font-bold uppercase tracking-widest text-white">AI Strategy Tips</h4>
                                        </div>
                                        <ul className="space-y-2">
                                            {analysis.improvement_suggestions.map((tip, i) => (
                                                <li key={i} className="text-[11px] text-slate-400 leading-relaxed flex items-start gap-2">
                                                    <span className="w-1 h-1 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                                                    {tip}
                                                </li>
                                            ))}
                                            {analysis.improvement_suggestions.length === 0 && (
                                                <li className="text-[11px] text-slate-500 italic">Resume aligns perfectly with target profile.</li>
                                            )}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {!showInsights && analysis && (
                        <div className="px-6 py-1">
                            <button
                                onClick={() => setShowInsights(true)}
                                className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-indigo-400 hover:text-indigo-300 transition-colors"
                            >
                                <TrendingUp size={12} /> Show Matching Insights
                            </button>
                        </div>
                    )}

                    {/* Main split pane */}
                    {/* Main split pane */}
                    <div className="flex flex-1 min-h-0 overflow-hidden">

                        {/* LEFT – LaTeX Editor */}
                        <div className={`flex flex-col border-r border-white/5 ${activePanel === 'preview' ? 'hidden md:flex' : 'flex'} w-full md:w-1/2`}>
                            <div className="flex items-center gap-2 px-4 py-2 bg-slate-900/80 border-b border-white/5 text-xs text-slate-500 font-bold uppercase tracking-widest shrink-0">
                                <Code size={12} /> LaTeX Source
                            </div>
                            <div className="flex-1 min-h-0">
                                <MonacoEditor
                                    height="100%"
                                    language="latex"
                                    theme="vs-dark"
                                    value={latexCode}
                                    onChange={v => handleLatexChange(v || '')}
                                    options={{
                                        fontSize: 13,
                                        minimap: { enabled: false },
                                        wordWrap: 'on',
                                        padding: { top: 12 },
                                        scrollBeyondLastLine: false,
                                        lineNumbers: 'on',
                                        glyphMargin: false,
                                        folding: true,
                                        renderLineHighlight: 'line',
                                    }}
                                />
                            </div>
                        </div>

                        {/* RIGHT – PDF Preview + Chat */}
                        <div className={`flex flex-col ${activePanel === 'code' ? 'hidden md:flex' : 'flex'} w-full md:w-1/2`}>

                            {/* PDF Pane */}
                            <div className="flex flex-col border-b border-white/5" style={{ height: '65%' }}>
                                <div className="flex items-center gap-2 px-4 py-2 bg-slate-900/80 border-b border-white/5 text-xs text-slate-500 font-bold uppercase tracking-widest shrink-0">
                                    <Eye size={12} /> PDF Preview
                                    {compiling && <span className="ml-auto flex items-center gap-1 text-amber-400"><Loader2 size={10} className="animate-spin" /> Compiling…</span>}
                                    {!compiling && pdfUrl && <span className="ml-auto text-emerald-400">● Live</span>}
                                </div>

                                <div className="flex-1 min-h-0 relative bg-gray-100">
                                    {compileError && !compiling && (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 bg-slate-950 z-10">
                                            <AlertTriangle size={32} className="text-rose-400 mb-3" />
                                            <p className="text-rose-400 font-bold text-sm mb-2">Compilation Error</p>
                                            <pre className="text-xs text-rose-300/70 bg-rose-500/10 rounded-xl p-4 overflow-auto max-h-40 w-full">{compileError}</pre>
                                            <button onClick={() => compilePdf(latexCode)} className="mt-4 btn-secondary text-xs">
                                                <RefreshCw size={12} /> Retry
                                            </button>
                                        </div>
                                    )}
                                    {!pdfUrl && !compiling && !compileError && (
                                        <div className="absolute inset-0 flex items-center justify-center bg-slate-950">
                                            <p className="text-slate-600 text-sm">PDF will appear here after compilation</p>
                                        </div>
                                    )}
                                    {compiling && !pdfUrl && (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950 z-10">
                                            <Loader2 size={32} className="text-indigo-400 animate-spin mb-3" />
                                            <p className="text-slate-400 text-sm">Compiling LaTeX…</p>
                                        </div>
                                    )}
                                    {pdfUrl && (
                                        <iframe
                                            key={pdfUrl}
                                            src={pdfUrl}
                                            className="w-full h-full border-0"
                                            title="PDF Preview"
                                        />
                                    )}
                                </div>
                            </div>

                            {/* Chat Pane */}
                            <div className="flex flex-col flex-1 min-h-0">
                                <div className="flex items-center gap-2 px-4 py-2 bg-slate-900/80 border-b border-white/5 text-xs text-slate-500 font-bold uppercase tracking-widest shrink-0">
                                    <Bot size={12} /> Neural Nexus Chat
                                </div>
                                <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                                    {chatMessages.length === 0 && (
                                        <div className="text-center py-8 opacity-40">
                                            <Bot size={32} className="mx-auto mb-2 text-slate-600" />
                                            <p className="text-xs text-slate-500">Ask for adjustments to your resume…</p>
                                        </div>
                                    )}
                                    {chatMessages.map((msg, i) => (
                                        <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 border ${msg.role === 'user' ? 'bg-primary-500/20 border-primary-500/30' : 'bg-purple-500/20 border-purple-500/30'}`}>
                                                {msg.role === 'user' ? <User size={12} className="text-primary-400" /> : <Bot size={12} className="text-purple-400" />}
                                            </div>
                                            <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed ${msg.role === 'user' ? 'bg-primary-500/10 text-primary-50' : 'bg-white/[0.04] text-slate-300'}`}>
                                                {msg.content}
                                            </div>
                                        </div>
                                    ))}
                                    {chatLoading && <div className="flex gap-2 animate-pulse"><div className="w-7 h-7 rounded-full bg-slate-800" /><div className="px-3 py-2 rounded-xl bg-white/[0.02] text-slate-600 text-xs">Refining resume…</div></div>}
                                    <div ref={chatEndRef} />
                                </div>
                                <div className="relative px-3 py-3 border-t border-white/5 shrink-0">
                                    <input
                                        value={chatInput}
                                        onChange={e => setChatInput(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleChat()}
                                        className="input-field text-xs py-3 pr-12"
                                        placeholder="Ask for a tweak… (Enter to send)"
                                    />
                                    <button onClick={handleChat} disabled={chatLoading || !chatInput.trim()} className="absolute right-5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center hover:bg-primary-400 transition-all disabled:opacity-30">
                                        <Send size={14} className="text-slate-950" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Analysis bar at bottom (collapsed) */}
                    {analysis && (
                        <div className="flex items-center gap-6 px-6 py-2 bg-slate-900/80 border-t border-white/5 shrink-0 overflow-x-auto no-scrollbar">
                            {[
                                { label: 'Integrity', value: analysis.total_score },
                                { label: 'Domain Fit', value: analysis.required_skill_match },
                                { label: 'Experience', value: analysis.project_relevance },
                                { label: 'Semantic', value: analysis.keyword_alignment },
                            ].map(s => (
                                <div key={s.label} className="flex items-center gap-2 shrink-0">
                                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">{s.label}</span>
                                    <span className={`text-sm font-bold ${scoreColor(s.value)}`}>{Math.round(s.value)}%</span>
                                </div>
                            ))}
                            <div className="ml-auto flex flex-wrap gap-1">
                                {analysis.matched_skills.map(s => <span key={s} className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 font-bold">{s}</span>)}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
