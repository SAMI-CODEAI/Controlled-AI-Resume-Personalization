'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, setToken, clearToken, isAuthenticated, User, TokenResponse } from '@/lib/api';

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, fullName: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing token on mount
        if (isAuthenticated()) {
            api.get<User>('/api/auth/me')
                .then(setUser)
                .catch(() => {
                    clearToken();
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (email: string, password: string) => {
        const response = await api.post<TokenResponse>('/api/auth/login', { email, password });
        setToken(response.access_token);
        setUser(response.user);
    };

    const register = async (email: string, password: string, fullName: string) => {
        const response = await api.post<TokenResponse>('/api/auth/register', {
            email,
            password,
            full_name: fullName,
        });
        setToken(response.access_token);
        setUser(response.user);
    };

    const logout = () => {
        clearToken();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}
