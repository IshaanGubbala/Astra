import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Geist, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import SiteNav from "./site-nav";
import StarField from "./components/StarField";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
const instrumentSerif = Instrument_Serif({ subsets: ["latin"], weight: ["400"], style: ["normal", "italic"], variable: "--font-instrument-serif" });
const jetBrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
  title: "Astra — Your AI Founding Team",
  description: "Launch and operate a company with a coordinated AI founding team.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "";
  const clarityId = process.env.NEXT_PUBLIC_CLARITY_PROJECT_ID ?? "";

  return (
    <html lang="en" className={`${geist.variable} ${instrumentSerif.variable} ${jetBrainsMono.variable} antialiased`}>
      <head>
        {posthogKey && (
          <script dangerouslySetInnerHTML={{ __html: `!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+" (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys onSessionId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);posthog.init('${posthogKey}',{api_host:'https://app.posthog.com'})` }} />
        )}
        {clarityId && (
          <script dangerouslySetInnerHTML={{ __html: `(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y)})(window,document,"clarity","script","${clarityId}");` }} />
        )}
      </head>
      <body>
        <ClerkProvider>
          <div aria-hidden="true" style={{
            position: "fixed", inset: "-10vh -10vw", zIndex: 0, pointerEvents: "none",
            background: "radial-gradient(60vw 50vh at 20% 18%, oklch(0.48 0.24 240 / 0.18), transparent 60%), radial-gradient(50vw 40vh at 85% 30%, oklch(0.55 0.22 240 / 0.14), transparent 65%), radial-gradient(70vw 60vh at 60% 90%, oklch(0.42 0.20 240 / 0.10), transparent 70%)",
            filter: "blur(40px)",
          }} />
          <StarField />
          <SiteNav />
          <main className="site-shell">{children}</main>
        </ClerkProvider>
      </body>
    </html>
  );
}
