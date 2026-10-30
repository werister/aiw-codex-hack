"use client";

import { useSyncExternalStore } from "react";

function subscribeTheme(cb: () => void) {
  const mo = new MutationObserver(cb);
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => mo.disconnect();
}

const isTower = () => document.documentElement.dataset.theme === "tower";

// True while tower mode is on; false on the server.
export function useTower() {
  return useSyncExternalStore(subscribeTheme, isTower, () => false);
}

// Light is the brand; tower mode is the dim-room variant. Saved per device.
export function ThemeToggle() {
  const tower = useSyncExternalStore(subscribeTheme, isTower, () => false);
  const toggle = () => {
    const next = tower ? "light" : "tower";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {}
  };
  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={tower}
      aria-label={tower ? "Light mode" : "Tower mode"}
      className="pill-btn border border-line text-ink [--btn-ring:var(--line)]"
    >
      <svg viewBox="0 0 16 16" className="size-4" fill="none" aria-hidden>
        {tower ? (
          <>
            <circle cx="8" cy="8" r="3" stroke="currentColor" />
            <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6 13 13M3 13l1.4-1.4M11.6 4.4 13 3" stroke="currentColor" />
          </>
        ) : (
          <path d="M13.5 9.5A5.5 5.5 0 0 1 6.5 2.5a5.5 5.5 0 1 0 7 7Z" stroke="currentColor" strokeLinejoin="round" />
        )}
      </svg>
      <span className="hidden sm:inline">{tower ? "Light mode" : "Tower mode"}</span>
    </button>
  );
}
