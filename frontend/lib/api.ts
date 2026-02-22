/**
 * Centralized API client with JWT auth headers.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiError {
    detail: string;
}

export function getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
}

export function setToken(token: string): void {
    localStorage.setItem('auth_token', token);
}

export function clearToken(): void {
    localStorage.removeItem('auth_token');
}

export function isAuthenticated(): boolean {
    return !!getToken();
}

async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getToken();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
        return undefined as unknown as T;
    }

    return response.json();
}

export const api = {
    get: <T>(endpoint: string) => request<T>(endpoint),

    post: <T>(endpoint: string, data?: unknown) =>
        request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),

    put: <T>(endpoint: string, data?: unknown) =>
        request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),

    delete: <T>(endpoint: string) =>
        request<T>(endpoint, { method: 'DELETE' }),
};

// ─── Type Definitions ──────────────────────────────────────────

export interface User {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    created_at: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface Skill {
    id: string;
    name: string;
    category: string | null;
    proficiency_level: number;
    created_at: string;
}

export interface Project {
    id: string;
    title: string;
    description: string;
    technologies: string | null;
    impact: string | null;
    domain: string | null;
    url: string | null;
    start_date: string | null;
    end_date: string | null;
    created_at: string;
}

export interface Experience {
    id: string;
    company: string;
    role: string;
    description: string;
    technologies: string | null;
    location: string | null;
    is_current: boolean;
    start_date: string | null;
    end_date: string | null;
    created_at: string;
}

export interface Achievement {
    id: string;
    title: string;
    description: string | null;
    date: string | null;
    created_at: string;
}

export interface ResumeTemplate {
    id: string;
    name: string;
    latex_content: string;
    placeholders: string | null;
    created_at: string;
    updated_at: string;
}

export interface GeneratedResume {
    id: string;
    template_id: string | null;
    job_description: string;
    latex_output: string;
    pdf_path: string | null;
    match_score: number | null;
    matched_skills: string | null;
    missing_skills: string | null;
    metadata_json: string | null;
    version: number;
    created_at: string;
}

export interface MatchScoreBreakdown {
    required_skill_match: number;
    project_relevance: number;
    keyword_alignment: number;
    total_score: number;
    matched_skills: string[];
    missing_skills: string[];
    ranked_projects: {
        project_id: string;
        title: string;
        relevance_score: number;
        matching_technologies: string[];
    }[];
    improvement_suggestions: string[];
}

export interface ChatResponse {
    reply: string;
    updated_latex: string | null;
    validation_passed: boolean;
    validation_errors: string[];
}
