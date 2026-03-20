const mongoose = require('mongoose');

const resumeTemplateSchema = new mongoose.Schema({
    user_id: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    name: { type: String, required: true },
    latex_content: { type: String, required: true },
    placeholders: { type: String, default: null } // JSON string or Mixed type
}, { timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' } });

module.exports = mongoose.model('ResumeTemplate', resumeTemplateSchema);
