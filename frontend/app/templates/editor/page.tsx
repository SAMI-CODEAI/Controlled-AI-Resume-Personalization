'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api, ResumeTemplate } from '@/lib/api';
import { Save, ArrowLeft, Info } from 'lucide-react';
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

function EditorContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const templateId = searchParams.get('id');

    const [name, setName] = useState('');
    const [content, setContent] = useState('');
    const [saving, setSaving] = useState(false);
    const [loaded, setLoaded] = useState(!templateId);

    useEffect(() => {
        if (templateId) {
            api.get<ResumeTemplate>(`/api/templates/${templateId}`)
                .then(t => {
                    setName(t.name);
                    setContent(t.latex_content);
                    setLoaded(true);
                })
                .catch(() => router.push('/templates'));
        }
    }, [templateId, router]);

    const handleSave = async () => {
        if (!name.trim() || !content.trim()) return;
        setSaving(true);
        try {
            if (templateId) {
                await api.put(`/api/templates/${templateId}`, { name, latex_content: content });
            } else {
                await api.post('/api/templates', { name, latex_content: content });
            }
            router.push('/templates');
        } catch (err: any) {
            alert(err.message || 'Failed to save');
        }
        setSaving(false);
    };

    const defaultTemplate = `\\documentclass[11pt,a4paper]{article}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{enumitem}
\\usepackage{hyperref}

\\begin{document}

%% ─── HEADER ──────────────────────────────────
\\begin{center}
{\\LARGE \\textbf{Your Name}} \\\\[4pt]
your@email.com \\quad | \\quad (555) 123-4567 \\quad | \\quad linkedin.com/in/yourname
\\end{center}

\\vspace{8pt}

%% ─── SUMMARY ─────────────────────────────────
\\section*{Professional Summary}
%%SUMMARY%%

%% ─── SKILLS ──────────────────────────────────
\\section*{Skills}
%%SKILLS%%

%% ─── EXPERIENCE ──────────────────────────────
\\section*{Experience}
%%EXPERIENCE%%

%% ─── PROJECTS ────────────────────────────────
\\section*{Projects}
%%PROJECTS%%

\\end{document}
`;

    if (!loaded) {
        return (
            <div className="pt-24 flex items-center justify-center min-h-screen">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="pt-20 pb-4 h-screen flex flex-col">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 sm:px-6 lg:px-8 py-3 glass-light border-b border-indigo-500/10">
                <div className="flex items-center gap-3">
                    <button onClick={() => router.push('/templates')} className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors">
                        <ArrowLeft size={18} />
                    </button>
                    <input
                        value={name}
                        onChange={e => setName(e.target.value)}
                        className="bg-transparent border-none text-lg font-semibold text-white placeholder-gray-600 focus:outline-none w-64"
                        placeholder="Template name…"
                    />
                </div>
                <div className="flex items-center gap-2">
                    {!templateId && !content && (
                        <button
                            onClick={() => setContent(defaultTemplate)}
                            className="btn-secondary text-xs flex items-center gap-1"
                        >
                            <Info size={12} /> Load Starter Template
                        </button>
                    )}
                    <button onClick={handleSave} disabled={saving || !name.trim()} className="btn-primary flex items-center gap-1.5 text-sm">
                        <Save size={14} /> {saving ? 'Saving…' : 'Save'}
                    </button>
                </div>
            </div>

            {/* Placeholder hints */}
            <div className="px-4 sm:px-6 lg:px-8 py-2 flex gap-2 text-xs text-gray-600 overflow-x-auto">
                <span className="text-gray-500">Placeholders:</span>
                {['%%SUMMARY%%', '%%SKILLS%%', '%%EXPERIENCE%%', '%%PROJECTS%%'].map(p => (
                    <span key={p} className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 cursor-pointer hover:bg-purple-500/20 transition-colors"
                        onClick={() => setContent(prev => prev + '\n' + p)}
                    >
                        {p}
                    </span>
                ))}
            </div>

            {/* Editor */}
            <div className="flex-1 min-h-0">
                <MonacoEditor
                    height="100%"
                    language="latex"
                    theme="vs-dark"
                    value={content}
                    onChange={(v) => setContent(v || '')}
                    options={{
                        fontSize: 14,
                        minimap: { enabled: false },
                        wordWrap: 'on',
                        padding: { top: 16 },
                        scrollBeyondLastLine: false,
                        smoothScrolling: true,
                        lineNumbers: 'on',
                        glyphMargin: false,
                        folding: true,
                        renderLineHighlight: 'line',
                        contextmenu: true,
                    }}
                />
            </div>
        </div>
    );
}

export default function TemplateEditorPage() {
    return (
        <Suspense fallback={
            <div className="pt-24 flex items-center justify-center min-h-screen">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        }>
            <EditorContent />
        </Suspense>
    );
}
