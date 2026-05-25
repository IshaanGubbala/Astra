"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

function NavLink({
  href,
  children,
  className = "",
}: {
  href: string;
  children: ReactNode;
  className?: string;
}) {
  const pathname = usePathname();
  const isActive =
    href === "/" ? pathname === "/" : href.startsWith("/") ? pathname === href.split("#")[0] : false;

  return (
    <Link href={href} className={`${className} ${isActive ? "active" : ""}`.trim()}>
      {children}
    </Link>
  );
}

export default function SiteNav() {
  return (
    <header className="site-nav">
      <Link href="/" className="site-brand" aria-label="Astra home">
        <span className="site-brand-mark" aria-hidden="true" />
        <span style={{ letterSpacing: "0.18em", fontSize: 13, textTransform: "uppercase" }}>
          Astra
        </span>
      </Link>

      <nav className="site-nav-links" aria-label="Primary">
        <NavLink href="/">Home</NavLink>
        <NavLink href="/dashboard">Dashboard</NavLink>
        <NavLink href="/setup">Setup</NavLink>
        <NavLink href="/" className="site-btn site-btn-primary">
          New goal <span aria-hidden="true">→</span>
        </NavLink>
      </nav>
    </header>
  );
}
