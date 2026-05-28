import Link from "next/link";
import { NECESSARY_COOKIES } from "@/lib/necessary-cookies";

export default function CookiesPage() {
  return (
    <div className="site-shell" style={{ paddingTop: 64, paddingBottom: 88 }}>
      <div style={{ maxWidth: 920, margin: "0 auto", display: "grid", gap: 22 }}>
        <div style={{ display: "grid", gap: 8 }}>
          <span className="site-label">Cookies</span>
          <h1 style={{ fontSize: "clamp(32px, 5vw, 58px)", lineHeight: 1.02 }}>Necessary cookies</h1>
          <p style={{ color: "var(--fg-dim)", fontSize: 15, lineHeight: 1.7 }}>
            Astra uses only cookies needed to run the application, keep accounts secure, and remember that this notice was shown.
            We do not set advertising cookies from Astra.
          </p>
        </div>

        <div style={{ display: "grid", gap: 12 }}>
          {NECESSARY_COOKIES.map((cookie) => (
            <div
              key={cookie.name}
              style={{
                borderRadius: 28,
                border: "1px solid var(--line)",
                background: "var(--glass)",
                backdropFilter: "var(--blur)",
                WebkitBackdropFilter: "var(--blur)",
                padding: "18px 20px",
                display: "grid",
                gap: 7,
              }}
            >
              <span style={{ fontFamily: "var(--font-jetbrains-mono)", fontSize: 12, color: "var(--fg)" }}>{cookie.name}</span>
              <span style={{ color: "var(--fg-dim)", fontSize: 13, lineHeight: 1.6 }}>{cookie.purpose}</span>
              <span style={{ color: "var(--fg-mute)", fontSize: 12 }}>Duration: {cookie.duration}</span>
            </div>
          ))}
        </div>

        <Link href="/" className="site-btn site-btn-primary" style={{ width: "fit-content", padding: "0 20px" }}>
          Back to Astra
        </Link>
      </div>
    </div>
  );
}
