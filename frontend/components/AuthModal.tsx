"use client";

import { useState } from "react";
import { login, register, type User } from "../lib/api";
import { useAuthStore } from "../lib/store";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { setAuth } = useAuthStore();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (mode === "login") {
        const { token, user } = await login(email, password);
        localStorage.setItem("token", token);
        setAuth(token, user);
        onClose();
      } else {
        await register(email, name, password, companyName || undefined);
        // Auto-login after registration
        const { token, user } = await login(email, password);
        localStorage.setItem("token", token);
        setAuth(token, user);
        onClose();
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          (mode === "login" ? "Invalid credentials" : "Registration failed")
      );
    } finally {
      setIsLoading(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-brand-primary">
            {mode === "login" ? "Sign In" : "Create Account"}
          </h2>
          <button
            onClick={onClose}
            className="text-brand-muted hover:text-brand-primary"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <>
              <div>
                <label className="text-xs font-semibold uppercase text-brand-muted">
                  Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-brand-muted">
                  Company Name (optional)
                </label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                />
              </div>
            </>
          )}

          <div>
            <label className="text-xs font-semibold uppercase text-brand-muted">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold uppercase text-brand-muted">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
              required
              minLength={6}
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-md bg-brand-accent px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500 disabled:opacity-50"
          >
            {isLoading
              ? "Please wait..."
              : mode === "login"
              ? "Sign In"
              : "Create Account"}
          </button>
        </form>

        <div className="mt-4 text-center text-sm">
          {mode === "login" ? (
            <p>
              Don't have an account?{" "}
              <button
                onClick={() => setMode("register")}
                className="text-brand-accent hover:underline"
              >
                Create one
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{" "}
              <button
                onClick={() => setMode("login")}
                className="text-brand-accent hover:underline"
              >
                Sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
