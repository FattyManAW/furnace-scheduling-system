/**
 * Animation utilities — scroll reveal + number counter
 * Zero-dependency. Hooks into CSS classes in index.css.
 */
export function initScrollReveal() {
  if (typeof window === "undefined" || !window.IntersectionObserver) return;
  const observer = new IntersectionObserver(
    (entries) => entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("visible"); observer.unobserve(e.target); }
    }),
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" },
  );
  document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
  return () => observer.disconnect();
}

export function animateNumber(el, target, duration = 800) {
  if (!el) return;
  const start = performance.now();
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    const eased = 1 - (1 - p) ** 2;
    el.textContent = Math.round(target * eased).toLocaleString();
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}