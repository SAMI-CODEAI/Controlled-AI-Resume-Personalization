const express = require('express');
const { protect } = require('../middleware/auth');

const createCrudRouter = (Model) => {
    const router = express.Router();

    router.use(protect);

    router.get('/', async (req, res) => {
        try {
            const items = await Model.find({ user_id: req.user._id });
            // Map _id and created_at
            res.json(items.map(i => ({ ...i.toObject(), id: i._id.toString() })));
        } catch (err) {
            res.status(500).json({ detail: err.message });
        }
    });

    router.post('/', async (req, res) => {
        try {
            const item = await Model.create({ ...req.body, user_id: req.user._id });
            res.status(201).json({ ...item.toObject(), id: item._id.toString() });
        } catch (err) {
            res.status(400).json({ detail: err.message });
        }
    });

    router.put('/:id', async (req, res) => {
        try {
            const item = await Model.findOneAndUpdate(
                { _id: req.params.id, user_id: req.user._id },
                req.body,
                { new: true, runValidators: true }
            );
            if (!item) return res.status(404).json({ detail: 'Item not found' });
            res.json({ ...item.toObject(), id: item._id.toString() });
        } catch (err) {
            res.status(400).json({ detail: err.message });
        }
    });

    router.delete('/:id', async (req, res) => {
        try {
            const item = await Model.findOneAndDelete({ _id: req.params.id, user_id: req.user._id });
            if (!item) return res.status(404).json({ detail: 'Item not found' });
            res.status(204).send();
        } catch (err) {
            res.status(400).json({ detail: err.message });
        }
    });

    return router;
};

module.exports = createCrudRouter;
