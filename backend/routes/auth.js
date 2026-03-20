const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const generateToken = (id) => {
    return jwt.sign({ sub: id }, process.env.JWT_SECRET_KEY, {
        expiresIn: `${process.env.JWT_EXPIRATION_MINUTES}m`,
    });
};

router.post('/register', async (req, res) => {
    const { email, password, full_name } = req.body;

    try {
        const userExists = await User.findOne({ email });

        if (userExists) {
            return res.status(400).json({ detail: 'User already exists' });
        }

        const salt = await bcrypt.genSalt(10);
        const hashed_password = await bcrypt.hash(password, salt);

        const user = await User.create({
            email,
            hashed_password,
            full_name,
        });

        if (user) {
            res.status(201).json({
                id: user._id,
                email: user.email,
                full_name: user.full_name,
                access_token: generateToken(user._id),
            });
        } else {
            res.status(400).json({ detail: 'Invalid user data' });
        }
    } catch (error) {
        res.status(500).json({ detail: error.message });
    }
});

router.post('/login', async (req, res) => {
    const { username, password } = req.body;

    try {
        // FastAPI OAuth2PasswordRequestForm uses 'username' field for email usually.
        const user = await User.findOne({ email: username });

        if (user && (await bcrypt.compare(password, user.hashed_password))) {
            res.json({
                access_token: generateToken(user._id),
                token_type: 'bearer',
            });
        } else {
            res.status(401).json({ detail: 'Invalid credentials' });
        }
    } catch (error) {
        res.status(500).json({ detail: error.message });
    }
});

module.exports = router;
