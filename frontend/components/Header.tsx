"use client";

import { useState } from "react";
import { useAuthStore } from "../lib/store";
import { AuthModal } from "./AuthModal";

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const [showAuthModal, setShowAuthModal] = useState(false);

  function handleLogout() {
    localStorage.removeItem("token");
    logout();
  }

  return (
    <>
      <header className="mb-10 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-brand-primary">NovaPrint</h1>
          <p className="text-sm text-brand-muted">
            Upload, quote, and manage 3D printed parts in minutes.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <nav className="flex gap-4 text-sm font-medium text-brand-primary">
            <a href="#customer" className="hover:text-brand-accent">
              Customer Portal
            </a>
            {user?.role === "admin" && (
              <a href="#admin" className="hover:text-brand-accent">
                Admin Portal
              </a>
            )}
          </nav>
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-brand-muted">
                {user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-brand-primary hover:border-brand-accent"
              >
                Sign out
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="rounded-md bg-brand-accent px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
            >
              Sign in
            </button>
          )}
        </div>
      </header>
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </>
  );
}
