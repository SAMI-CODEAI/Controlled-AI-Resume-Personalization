# Controlled AI Resume Personalization Platform

[![GitHub Release](https://img.shields.io/github/v/release/SAMI-CODEAI/Controlled-AI-Resume-Personalization?style=flat-square)](https://github.com/SAMI-CODEAI/Controlled-AI-Resume-Personalization)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Powered by OpenAI](https://img.shields.io/badge/Powered%20by-OpenAI-412991?style=flat-square&logo=openai)](https://openai.com/)

A production-ready, full-stack ecosystem designed to generate high-fidelity, job-specific resumes through **Controlled AI Personalization**. By bridging the gap between structured career data and generative AI, the platform ensures professional excellence without compromising integrity.

---

## 🏗️ System Architecture

The platform utilizes a modern, decoupled architecture designed for high throughput and modularity.

```mermaid
graph TD
    User((User))
    
    subgraph "Frontend (Next.js 14)"
        UI[React UI / Tailwind]
        Draft[Interactive LaTeX Editor]
        Viewer[Live PDF Preview]
    end
    
    subgraph "Backend Layer (FastAPI)"
        API[REST API Endpoints]
        Auth[JWT Authentication]
        logic[Business & Matching Logic]
    end
    
    subgraph "Service Layer"
        AI[AI Matching & Personalization]
        LaTeX[LaTeX Rendering Engine]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL / SQLite)]
    end
    
    User --> UI
    UI --> API
    API --> Auth
    API --> logic
    logic --> DB
    logic --> AI
    logic --> LaTeX
    AI --> OpenAI(OpenAI SDK)
```

---

## ⚡ Core Workflow: The "Controlled" Approach

Unlike typical LLM wrappers, this platform employs a multi-stage pipeline to ensure every word in your resume is backed by verified data.

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant A as AI Service
    participant L as LaTeX Engine

    U->>F: Upload Job Description & Select Template
    F->>B: Trigger Resume Generation
    B->>B: Retrieve Career Data Vault
    B->>A: Match JD vs. Verified Experiences
    Note over A: Intelligent Filtering & Hallucination Guard
    A-->>B: Return Personalized Content
    B->>L: Inject Content into LaTeX Template
    L-->>B: Compile PDF
    B-->>F: Stream PDF Data
    F->>U: Display Live Preview & Editor
```

---

## 🛡️ Hallucination Prevention & Integrity

> [!IMPORTANT]
> **Integrity Guarantee**: Our platform uses a **Closed-Loop Verification** system. The AI is only permitted to rephrase and emphasize *existing* data points. It is strictly prohibited from introducing generic skills or fabricated roles, even if they match the job description.

| Mechanical Layer | Description | Purpose |
| :--- | :--- | :--- |
| **Data Vaulting** | All career history is stored in a structured, immutable format. | Source of Truth |
| **Semantic Matching** | Vector-based analysis ensures AI only picks relevant *existing* skills. | Relevance Filtering |
| **Prompt Constraining** | Strict system prompts enforce "No New Facts" policy. | Hallucination Guard |
| **Comparison Layer** | (Post-process) Cross-checks generated text against original data. | Final Validation |

---

## 🛠️ Technology Stack & Rationale

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14 (App Router)** | Performance (RSC), seamless hydration, and robust SEO capabilities. |
| **Styling** | **Tailwind CSS** | Design consistency and the ability to implement complex themes like the "Anti-Gravity" aesthetic. |
| **Backend** | **FastAPI** | Asynchronous execution for high-concurrency LLM calls and PDF rendering. |
| **Database** | **PostgreSQL** | Relational integrity for complex career data (Work Experience → Achievements). |
| **AI Client** | **OpenAI GPT-4o** | State-of-the-art reasoning for precise semantic matching and professional writing. |
| **Editing** | **Monaco Editor** | The industry standard for syntax highlighting (LaTeX) and a premium developer feel. |

---

## ✨ Features Spotlight

### 📊 Career Data Vault
Store your work history, projects, and skills twice. Verify them once. Reuse them infinitely for different job targets.

### 🎨 Premium Aesthetics
Designed with a "Floating/Anti-Gravity" medical aesthetic. Smooth transitions, glassmorphism, and subtle micro-animations provide an elite user experience.

### ✍️ Integrated LaTeX Studio
Advanced users can take full control. Edit the raw LaTeX source with real-time PDF synchronization.

---

## 🚀 Getting Started

### 1. Environment Configuration
Create a `.env` file in the root using the provided template:
```bash
cp .env.example .env
```

### 2. Launch with Docker
```bash
docker-compose up --build
```

### 3. Access the Platform
- **Frontend**: `http://localhost:3000`
- **Interactive API Docs**: `http://localhost:8000/docs`

---
> [!TIP]
> To run without Docker, ensure you have a local LaTeX distribution installed (e.g., TeX Live or MiKTeX) for resume rendering.

Developed with precision by the **Controlled AI Team**.
