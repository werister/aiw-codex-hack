import type { Metadata } from "next";
import { Inter_Tight } from "next/font/google";
import "./globals.css";

// Closest free match to FraAlliance's Söhne (web/DESIGN.md).
const brand = Inter_Tight({
  variable: "--font-brand",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Lift-off · Frankfurt Runway Outlook",
  description:
    "48 h hourly forecast of the Frankfurt Airport operating direction and runway 18.",
};

// Tower mode is saved per device; ?tower=1 or ?tower=0 overrides it. Runs before first paint.
const THEME_SCRIPT = `(function(){try{var q=new URLSearchParams(location.search).get("tower");var t=q==null?localStorage.getItem("theme"):q==="1"?"tower":"light";if(t)document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" data-theme="light" className={`${brand.variable} h-full antialiased`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
