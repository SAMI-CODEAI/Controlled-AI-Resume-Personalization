import React from 'react';
import Link from 'next/link';
import { Sparkles, Zap, ShieldCheck, Target, MessageSquare, History, ChevronRight } from 'lucide-react';

export default function LandingPage() {
    const features = [
        {
            title: 'Zero Hallucination',
            desc: 'Strict profile-matching technology ensures every claim in your resume is backed by your actual experience.',
            icon: ShieldCheck,
            color: 'text-emerald-400',
            bg: 'bg-emerald-500/10'
        },
        {
            title: 'LaTeX Precision',
            desc: 'Industry-standard LaTeX templates provide perfect formatting and maximum ATS compatibility.',
            icon: Zap,
            color: 'text-amber-400',
            bg: 'bg-amber-500/10'
        },
        {
            title: 'Real-time Matching',
            desc: 'Get an instant match score for every job description, highlighting missing skills and project relevance.',
            icon: Target,
            color: 'text-blue-400',
            bg: 'bg-blue-500/10'
        },
        {
            title: 'AI Revision Chat',
            desc: 'Iterative refinement: chat with the AI to tweak bullet points while maintaining factual integrity.',
            icon: MessageSquare,
            color: 'text-purple-400',
            bg: 'bg-purple-500/10'
        },
        {
            title: 'Version Control',
            desc: 'Built-in versioning allows you to track iterations and roll back to previous resume drafts instantly.',
            icon: History,
            color: 'text-pink-400',
            bg: 'bg-pink-500/10'
        },
        {
            title: 'Structured Career',
            desc: 'A central source of truth for your skills, projects, and experiences to power all your documents.',
            icon: Sparkles,
            color: 'text-primary-400',
            bg: 'bg-primary-500/10'
        }
    ];

    return (
        <div className="relative min-h-screen overflow-hidden">
            <div className="bg-mesh" />

            {/* Hero */}
            <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs font-semibold mb-8 animate-fade-in">
                    <Sparkles size={14} /> The Future of Resume Personalization
                </div>

                <h1 className="text-5xl md:text-7xl lg:text-8xl font-display font-bold leading-tight mb-8 tracking-tight">
                    Craft Resumes with <br />
                    <span className="gradient-text">Absolute Integrity</span>
                </h1>

                <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12 leading-relaxed">
                    The only AI resume builder that cross-references your career data to prevent hallucinations, while delivering high-end LaTeX exports.
                </p>

                <div className="flex flex-col sm:flex-row gap-4">
                    <Link href="/register" className="btn-primary flex items-center gap-2 text-lg px-8 py-3.5">
                        Start Building <ChevronRight size={20} />
                    </Link>
                    <Link href="/login" className="btn-secondary flex items-center gap-2 text-lg px-8 py-3.5">
                        Sign In
                    </Link>
                </div>

                {/* Floating visual element */}
                <div className="mt-20 w-full max-w-5xl h-[300px] md:h-[500px] relative rounded-3xl overflow-hidden glass border border-white/5 shadow-2xl animate-float">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-transparent to-amber-500/5" />
                    <div className="flex items-center justify-center h-full text-slate-600 font-mono text-xs md:text-sm p-4 text-left pointer-events-none opacity-40">
                        <pre className="max-w-full overflow-hidden">
                            {`\\documentclass[11pt]{resume}
\\usepackage{emerald}
\\begin{document}
  \\section{Experience}
  \\resumeItem{Developed AI-powered platform using Next.js and FastAPI...}
  \\resumeItem{Implemented 100% factual career matching algorithm...}
\\end{document}`}
                        </pre>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/5">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">Precision Engineering</h2>
                    <p className="text-slate-400">Advanced features built for the modern professional.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((f, i) => (
                        <div key={i} className="card group">
                            <div className={`w-12 h-12 rounded-2xl ${f.bg} flex items-center justify-center mb-6 transition-transform group-hover:scale-110 duration-500`}>
                                <f.icon className={f.color} size={24} />
                            </div>
                            <h3 className="text-xl font-bold mb-3 group-hover:text-primary-400 transition-colors">{f.title}</h3>
                            <p className="text-slate-500 leading-relaxed">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-white/5 text-center text-slate-600 text-sm">
                <p>&copy; {new Date().getFullYear()} ResumeAI. Built for high-stakes professionals.</p>
            </footer>
        </div>
    );
}

