const express = require('express');
const router = express.Router();
const { OpenAI } = require('openai');
const { protect } = require('../middleware/auth');
const Skill = require('../models/Skill');
const Experience = require('../models/Experience');
const Project = require('../models/Project');
const Achievement = require('../models/Achievement');
const ResumeTemplate = require('../models/ResumeTemplate');
const GeneratedResume = require('../models/GeneratedResume');

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: process.env.LLM_BASE_URL || undefined, // Allow bridging to Ollama if configured
});

// GET all generated resumes for a user
router.get('/', protect, async (req, res) => {
    try {
        const resumes = await GeneratedResume.find({ user_id: req.user._id }).sort({ created_at: -1 });
        res.json(resumes.map(r => ({ ...r.toObject(), id: r._id.toString() })));
    } catch (err) {
        res.status(500).json({ detail: err.message });
    }
});


// DELETE a resume
router.delete('/:id', protect, async (req, res) => {
    try {
        await GeneratedResume.findOneAndDelete({ _id: req.params.id, user_id: req.user._id });
        res.status(204).send();
    } catch (err) {
        res.status(500).json({ detail: err.message });
    }
});

// GET analysis
router.get('/:id/analysis', protect, async (req, res) => {
    try {
        const resume = await GeneratedResume.findOne({ _id: req.params.id, user_id: req.user._id });
        if (!resume || !resume.metadata_json) return res.status(404).json({ detail: 'Not found' });

        const meta = JSON.parse(resume.metadata_json);
        res.json({
            required_skill_match: meta.score_breakdown?.required_skill_match || 80,
            project_relevance: meta.score_breakdown?.project_relevance || 85,
            keyword_alignment: meta.score_breakdown?.keyword_alignment || 90,
            total_score: resume.match_score || 85,
            matched_skills: resume.matched_skills ? JSON.parse(resume.matched_skills) : [],
            missing_skills: resume.missing_skills ? JSON.parse(resume.missing_skills) : [],
            ranked_projects: meta.ranked_projects || [],
            improvement_suggestions: []
        });
    } catch (err) {
        res.status(500).json({ detail: err.message });
    }
});

// POST generate
router.post('/generate', protect, async (req, res) => {
    try {
        const { template_id, job_description } = req.body;

        // 1. Fetch template
        const template = await ResumeTemplate.findOne({ _id: template_id, user_id: req.user._id });
        if (!template) return res.status(404).json({ detail: 'Template not found' });

        // 2. Fetch user data
        const skills = await Skill.find({ user_id: req.user._id });
        const experiences = await Experience.find({ user_id: req.user._id });
        const projects = await Project.find({ user_id: req.user._id });
        const achievements = await Achievement.find({ user_id: req.user._id });

        const userData = {
            skills: skills.map(s => ({ name: s.name, level: s.proficiency_level })),
            experiences: experiences.map(e => ({ company: e.company, role: e.role, desc: e.description })),
            projects: projects.map(p => ({ title: p.title, desc: p.description, tech: p.technologies })),
            achievements: achievements.map(a => ({ title: a.title, desc: a.description }))
        };

        // 3. Extract placeholders dynamically from the template
        const placeholders = [...template.latex_content.matchAll(/%%([A-Z_]+)%%/g)].map(m => m[1]);
        const hasTags = placeholders.length > 0;
        const systemPrompt = [
            'You are a professional resume writer and career coach with a strict zero-hallucination policy.',
            '',
            '=== ABSOLUTE RULES — NEVER VIOLATE ===',
            '1. ALL facts (companies, roles, project titles, skills, dates, descriptions) MUST come',
            '   verbatim or paraphrased from the USER DATA block below.',
            '2. NEVER invent, fabricate, or infer any detail not explicitly present in USER DATA.',
            '3. The STYLE REFERENCE is a formatting guide ONLY. Ignore every name, company,',
            '   skill, technology, and personal fact in it. Use it only for bullet style and tone.',
            '4. Never write a skill, technology, company, or project not in USER DATA,',
            '   even if the STYLE REFERENCE mentions it.',
            '5. Output ONLY printable ASCII (0x20-0x7E) plus real newlines. NEVER emit Unicode',
            '   control characters (U+0000-U+001F, U+007F). Use LaTeX escape sequences for accents.',
            '',
            '=== ANALYSIS TASK ===',
            '- Identify "matched_requirements": specific skills/experiences from USER DATA that fit the STYLE REFERENCE.',
            '- Identify "missing_requirements": keys/skills present in the STYLE REFERENCE but absent in USER DATA.',
            '- Provide "improvement_suggestions": actionable tips (e.g. "Add a project involving Docker to fill this gap").',
            '',
            '=== STYLE REFERENCE (formatting guide only — ignore all content/facts) ===',
            job_description,
            '',
            '=== USER DATA (the ONLY allowed source of facts) ===',
            JSON.stringify(userData, null, 2),
            '',
            '=== OUTPUT INSTRUCTIONS ===',
            'Return a JSON object with these keys:',
            `- "sections": object with keys: ${hasTags ? placeholders.join(', ') : 'full_latex'}`,
            hasTags ? '  (Each value is a LaTeX snippet for that section)' : '  (Value is the entire re-written LaTeX document based on the template)',
            '- "analysis": { "match_score": number, "matched": string[], "missing": string[], "tips": string[] }',
            'Output valid JSON only. No markdown fences. No extra keys.',
        ].join('\n');

        let resultJson;
        try {
            const completion = await openai.chat.completions.create({
                model: process.env.LLM_MODEL || 'gpt-4o',
                messages: [{ role: 'system', content: systemPrompt }],
                response_format: { type: 'json_object' }
            });
            resultJson = JSON.parse(completion.choices[0].message.content);
        } catch (llmErr) {
            console.error(llmErr);
            return res.status(500).json({ detail: 'AI Generation failed: ' + llmErr.message });
        }

        // Sanitizer: strip control chars that break pdflatex
        // eslint-disable-next-line no-control-regex
        const sanitize = (s) => (s || '').replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');

        // 4. Fill template or use full re-write
        let finalLatex = template.latex_content;
        if (hasTags) {
            for (const key of placeholders) {
                const replacement = sanitize(resultJson.sections?.[key] || '');
                finalLatex = finalLatex.replace(new RegExp(`%%${key}%%`, 'g'), replacement);
            }
        } else {
            finalLatex = sanitize(resultJson.sections?.full_latex || template.latex_content);
        }

        // 5. Extract analysis from AI
        const analysis = resultJson.analysis || {};
        const score = analysis.match_score || 85;

        // 6. Save Generated Resume
        const resume = await GeneratedResume.create({
            user_id: req.user._id,
            template_id,
            job_description,
            latex_output: finalLatex,
            match_score: score,
            matched_skills: JSON.stringify(analysis.matched || []),
            missing_skills: JSON.stringify(analysis.missing || []),
            metadata_json: JSON.stringify({
                score_breakdown: {
                    required_skill_match: score - 5,
                    project_relevance: score,
                    keyword_alignment: score + 2,
                    total_score: score
                },
                improvement_suggestions: analysis.tips || [],
                ranked_projects: projects.slice(0, 3).map(p => ({
                    title: p.title,
                    relevance_score: score - Math.floor(Math.random() * 10),
                    matching_technologies: p.technologies ? p.technologies.split(',') : []
                }))
            }),
            version: 1
        });

        res.status(201).json({ ...resume.toObject(), id: resume._id.toString() });

    } catch (err) {
        console.error(err);
        res.status(500).json({ detail: err.message });
    }
});

module.exports = router;








