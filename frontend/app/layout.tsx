import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "3D Print Portal",
  description: "Customer and admin portal for on-demand 3D printing",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-100">
        <div className="mx-auto max-w-6xl px-6 py-10">
          <header className="mb-10 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-brand-primary">NovaPrint</h1>
              <p className="text-sm text-brand-muted">
                Upload, quote, and manage 3D printed parts in minutes.
              </p>
            </div>
            <nav className="flex gap-4 text-sm font-medium text-brand-primary">
              <a href="#customer" className="hover:text-brand-accent">
                Customer Portal
              </a>
              <a href="#admin" className="hover:text-brand-accent">
                Admin Portal
              </a>
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
