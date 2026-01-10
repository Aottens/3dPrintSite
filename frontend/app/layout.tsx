import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../styles/globals.css";
import { Header } from "../components/Header";

export const metadata: Metadata = {
  title: "NovaPrint - 3D Print Portal",
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
          <Header />
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
