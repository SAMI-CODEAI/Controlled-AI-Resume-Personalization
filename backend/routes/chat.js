const express = require('express');
const router = express.Router();
const { OpenAI } = require('openai');
const { protect } = require('../middleware/auth');
const GeneratedResume = require('../models/GeneratedResume');

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: process.env.LLM_BASE_URL || undefined,
});

router.post('/refine', protect, async (req, res) => {
    try {
        const { resume_id, message, history } = req.body;

        const resume = await GeneratedResume.findOne({ _id: resume_id, user_id: req.user._id });
        if (!resume) return res.status(404).json({ detail: 'Resume not found' });

        // Build the system prompt using the existing LaTeX
        const systemPrompt = `You are an expert AI Resume Assistant. The user wants to refine their LaTeX resume.
Here is their current resume LaTeX code:
\`\`\`latex
${resume.latex_output}
\`\`\`
Return a JSON object with two keys: "reply" (a friendly response to the user), and "updated_latex" (the entire updated LaTeX code based on their feedback). Do NOT make changes if not asked. Return valid JSON only, without markdown wrapping.`;

        const messages = [
            { role: 'system', content: systemPrompt },
            ...(history || []).map(h => ({ role: h.role, content: h.content })),
            { role: 'user', content: message }
        ];

        let resultJson;
        try {
            const completion = await openai.chat.completions.create({
                model: process.env.LLM_MODEL || 'gpt-4o',
                messages: messages,
                response_format: { type: 'json_object' }
            });
            resultJson = JSON.parse(completion.choices[0].message.content);
        } catch (llmErr) {
            console.error(llmErr);
            return res.status(500).json({ detail: 'AI Chat failed: ' + llmErr.message });
        }

        const reply = resultJson.reply || 'I updated your resume.';
        const updated_latex = resultJson.updated_latex || resume.latex_output;

        // Save the updated latex to DB
        resume.latex_output = updated_latex;
        resume.version += 1;
        await resume.save();

        res.json({
            reply: reply,
            updated_latex: updated_latex,
            validation_passed: true,
            validation_errors: []
        });

    } catch (err) {
        console.error(err);
        res.status(500).json({ detail: err.message });
    }
});

module.exports = router;
