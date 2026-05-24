import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Astra — AI Startup OS",
  description: "Your AI co-founder, 24/7",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">
        <header className="border-b border-zinc-800 px-6 py-4">
          <a href="/" className="text-lg font-semibold tracking-tight text-white">
            ✦ Astra
          </a>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
