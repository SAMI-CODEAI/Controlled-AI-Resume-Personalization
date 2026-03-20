const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const connectDB = require('./config/db');
const authRoutes = require('./routes/auth');
const resumeRoutes = require('./routes/resumes');
const chatRoutes = require('./routes/chat');
const compileRoutes = require('./routes/compile');

// Load env vars
dotenv.config();

// Connect to database
connectDB();

const app = express();

// Body parser
app.use(express.json());
// Form data parser for OAuth2 password grant form
app.use(express.urlencoded({ extended: true }));

// Enable CORS
app.use(cors());

// Mount routers
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/resumes', resumeRoutes);
app.use('/api/v1/chat', chatRoutes);
app.use('/api/v1/compile', compileRoutes);

// Generic CRUD routers for the Data Vault
const createCrudRouter = require('./routes/crudGenerator');
const Skill = require('./models/Skill');
const Experience = require('./models/Experience');
const Project = require('./models/Project');
const Achievement = require('./models/Achievement');
const ResumeTemplate = require('./models/ResumeTemplate');

app.use('/api/v1/skills', createCrudRouter(Skill));
app.use('/api/v1/experiences', createCrudRouter(Experience));
app.use('/api/v1/projects', createCrudRouter(Project));
app.use('/api/v1/achievements', createCrudRouter(Achievement));
app.use('/api/v1/templates', createCrudRouter(ResumeTemplate));

app.get('/api/v1/health', (req, res) => {
    res.json({ status: 'healthy', database: 'mongodb connected' });
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ detail: 'Server Error', message: err.message });
});

const PORT = process.env.PORT || 8000;

app.listen(PORT, console.log(`Server running on port ${PORT}`));
