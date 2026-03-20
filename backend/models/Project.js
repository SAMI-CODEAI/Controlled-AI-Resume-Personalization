const mongoose = require('mongoose');

const projectSchema = new mongoose.Schema({
    user_id: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    title: { type: String, required: true },
    description: { type: String, required: true },
    technologies: { type: String, default: null },
    impact: { type: String, default: null },
    domain: { type: String, default: null },
    url: { type: String, default: null },
    start_date: { type: Date, default: null },
    end_date: { type: Date, default: null },
}, { timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' } });

module.exports = mongoose.model('Project', projectSchema);
