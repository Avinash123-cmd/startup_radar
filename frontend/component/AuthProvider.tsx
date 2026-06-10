"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { Lock, User, AlertCircle, Activity, CheckCircle2 } from "lucide-react";
import Sidebar from "./Sidebar";
import { API_BASE_URL } from "./apiHelper";

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  login: (username: string, password: string) => Promise<{ success: boolean; message?: string }>;
  signup: (username: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [authUsername, setAuthUsername] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Read session state on mount
    const saved = sessionStorage.getItem("radar_auth");
    const savedUser = sessionStorage.getItem("radar_username");
    if (saved === "true" && savedUser) {
      setIsAuthenticated(true);
      setAuthUsername(savedUser);
    }
    setLoading(false);
  }, []);

  const login = async (usernameInput: string, passwordInput: string): Promise<{ success: boolean; message?: string }> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
      });
      if (!res.ok) {
        const err = await res.json();
        return { success: false, message: err.detail || "Invalid credentials." };
      }
      const data = await res.json();
      sessionStorage.setItem("radar_auth", "true");
      sessionStorage.setItem("radar_username", data.username);
      setIsAuthenticated(true);
      setAuthUsername(data.username);
      return { success: true };
    } catch (e) {
      console.error("Login request failed", e);
      return { success: false, message: "Server connection failed." };
    }
  };

  const signup = async (usernameInput: string, passwordInput: string): Promise<{ success: boolean; message?: string }> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
      });
      if (!res.ok) {
        const err = await res.json();
        return { success: false, message: err.detail || "Registration failed." };
      }
      return { success: true };
    } catch (e) {
      console.error("Signup request failed", e);
      return { success: false, message: "Server connection failed." };
    }
  };

  const logout = () => {
    sessionStorage.removeItem("radar_auth");
    sessionStorage.removeItem("radar_username");
    setIsAuthenticated(false);
    setAuthUsername(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, username: authUsername, login, signup, logout }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export function MainLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, login, signup } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setSubmitting(true);

    if (isSignUp) {
      const result = await signup(username, password);
      if (result.success) {
        setSuccessMessage("Account created successfully! You can now sign in.");
        setIsSignUp(false);
        setPassword("");
      } else {
        setErrorMessage(result.message || "Registration failed.");
      }
    } else {
      const result = await login(username, password);
      if (!result.success) {
        setErrorMessage(result.message || "Invalid credentials.");
      }
    }
    setSubmitting(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="flex-1 w-full min-h-screen bg-zinc-950 flex items-center justify-center relative overflow-hidden px-4">
        {/* Decorative background gradients */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px]" />

        <div className="w-full max-w-md glass-card p-8 relative z-10 border border-zinc-800 bg-zinc-900/60 shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex bg-indigo-600/20 p-3 rounded-xl border border-indigo-500/30 mb-2">
              <Activity className="h-8 w-8 text-indigo-400 animate-pulse" />
            </div>
            <h2 className="text-2xl font-black text-zinc-100 tracking-tight">AI Startup Radar</h2>
            <p className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">
              {isSignUp ? "Create a New Account" : "Market Intelligence Gatekeeper"}
            </p>
          </div>

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                <input
                  type="text"
                  required
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 transition duration-200"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 transition duration-200"
                />
              </div>
            </div>

            {errorMessage && (
              <div className="flex items-center space-x-2 bg-red-950/20 border border-red-500/20 p-3 rounded-lg text-xs text-red-400 animate-shake">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {successMessage && (
              <div className="flex items-center space-x-2 bg-emerald-950/20 border border-emerald-500/20 p-3 rounded-lg text-xs text-emerald-400">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{successMessage}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-bold text-zinc-50 transition duration-200 cursor-pointer shadow-lg shadow-indigo-600/20 disabled:opacity-50"
            >
              {submitting ? "Processing..." : isSignUp ? "Create Account" : "Access Dashboard"}
            </button>
          </form>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold tracking-wider uppercase transition duration-150"
            >
              {isSignUp ? "Already have an account? Sign In" : "Don't have an account? Sign Up"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Authenticated state: sidebar and actual pages
  return (
    <div className="min-h-screen w-full flex text-zinc-100 bg-zinc-950 font-sans">
      {/* Sidebar Component */}
      <Sidebar />
      
      {/* Main Application Area */}
      <div className="flex-1 flex flex-col h-screen overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
