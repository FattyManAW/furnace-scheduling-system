import { useEffect } from "react";

/**
 * Set document.title on mount; restore on unmount.
 * WCAG 2.1 2.4.2 — Page Titled (each page has a descriptive title)
 */
const BASE = "排爐系統 — 干式套管最佳化";

export default function usePageTitle(pageName) {
  useEffect(() => {
    const prev = document.title;
    document.title = pageName ? `${pageName} — ${BASE}` : BASE;
    return () => { document.title = prev; };
  }, [pageName]);
}