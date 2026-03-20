const mongoose = require('mongoose');

const experienceSchema = new mongoose.Schema({
    user_id: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    company: { type: String, required: true },
    role: { type: String, required: true },
    description: { type: String, required: true },
    technologies: { type: String, default: null },
    location: { type: String, default: null },
    is_current: { type: Boolean, default: false },
    start_date: { type: Date, default: null },
    end_date: { type: Date, default: null },
}, { timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' } });

module.exports = mongoose.model('Experience', experienceSchema);
