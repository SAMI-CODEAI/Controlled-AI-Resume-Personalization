const mongoose = require('mongoose');

const generatedResumeSchema = new mongoose.Schema({
    user_id: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    template_id: { type: mongoose.Schema.Types.ObjectId, ref: 'ResumeTemplate', default: null },
    job_description: { type: String, required: true },
    latex_output: { type: String, required: true },
    pdf_path: { type: String, default: null },
    match_score: { type: Number, default: null },
    matched_skills: { type: String, default: null }, // JSON string
    missing_skills: { type: String, default: null }, // JSON string
    metadata_json: { type: String, default: null }, // Full analysis JSON
    version: { type: Number, default: 1 }
}, { timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' } });

module.exports = mongoose.model('GeneratedResume', generatedResumeSchema);
