"use client";
import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("astra-theme");
    const isDark = stored ? stored === "dark" : true;
    setDark(isDark);
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    const val = next ? "dark" : "light";
    localStorage.setItem("astra-theme", val);
    document.documentElement.setAttribute("data-theme", val);
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      style={{
        background: "none", border: "none", cursor: "pointer",
        display: "flex", alignItems: "center", justifyContent: "center",
        width: 28, height: 28, borderRadius: 6, flexShrink: 0,
        color: "var(--text-2)", fontSize: 13, lineHeight: 1,
        transition: "color 0.15s, background 0.15s",
      }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "var(--glass-hi)"; (e.currentTarget as HTMLElement).style.color = "var(--text)"; }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "none"; (e.currentTarget as HTMLElement).style.color = "var(--text-2)"; }}
    >
      {dark ? "○" : "●"}
    </button>
  );
}
