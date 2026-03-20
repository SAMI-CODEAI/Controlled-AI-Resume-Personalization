const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth');
const { execFile } = require('child_process');
const os = require('os');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

/**
 * POST /api/v1/compile
 * Accepts { latex: string }, compiles with pdflatex, returns a PDF binary.
 */
/**
 * Strip ASCII control characters that pdflatex cannot handle.
 * Keeps: \t (0x09), \n (0x0A), \r (0x0D).
 * Removes: NUL, backspace (^^H), vertical-tab, form-feed, and all other
 * C0/C1 controls and DEL that the LLM occasionally emits.
 */
function sanitizeLatex(src) {
    // eslint-disable-next-line no-control-regex
    return src.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
}

router.post('/', protect, async (req, res) => {
    const { latex } = req.body;
    if (!latex) return res.status(400).json({ detail: 'latex is required' });

    const clean = sanitizeLatex(latex);

    // Create a unique temp directory for this request
    const jobId = crypto.randomUUID();
    const tmpDir = path.join(os.tmpdir(), `resume-${jobId}`);
    const texFile = path.join(tmpDir, 'resume.tex');
    const pdfFile = path.join(tmpDir, 'resume.pdf');

    try {
        fs.mkdirSync(tmpDir, { recursive: true });
        fs.writeFileSync(texFile, clean, 'utf-8');

        await new Promise((resolve, reject) => {
            execFile(
                'pdflatex',
                [
                    '-interaction=nonstopmode',
                    '-halt-on-error',
                    '-output-directory', tmpDir,
                    texFile,
                ],
                { timeout: 30000, maxBuffer: 5 * 1024 * 1024 },
                (err, stdout, stderr) => {
                    if (err) {
                        // Extract last meaningful error line from the log
                        const logFile = path.join(tmpDir, 'resume.log');
                        let logTail = '';
                        try {
                            const log = fs.readFileSync(logFile, 'utf-8');
                            const lines = log.split('\n');
                            // Find lines starting with ! (LaTeX errors)
                            const errLines = lines.filter(l => l.startsWith('!'));
                            logTail = errLines.slice(0, 5).join('\n') || stderr.slice(-500);
                        } catch (_) {
                            logTail = stderr.slice(-500);
                        }
                        return reject(new Error(logTail || 'pdflatex compilation failed'));
                    }
                    resolve();
                }
            );
        });

        if (!fs.existsSync(pdfFile)) {
            return res.status(500).json({ detail: 'PDF was not produced' });
        }

        const pdfBuffer = fs.readFileSync(pdfFile);

        res.set('Content-Type', 'application/pdf');
        res.set('Content-Disposition', 'inline; filename="resume.pdf"');
        res.set('Content-Length', pdfBuffer.length);
        res.send(pdfBuffer);

    } catch (err) {
        console.error('[compile]', err.message);
        res.status(422).json({ detail: err.message });
    } finally {
        // Cleanup temp folder asynchronously
        fs.rm(tmpDir, { recursive: true, force: true }, () => { });
    }
});

module.exports = router;
