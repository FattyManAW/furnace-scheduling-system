/**
 * Service Worker — cache-first for static assets
 * Network-first for page navigations.
 * Offline fallback for all other requests.
 */
const CACHE = "furnace-v2.0.0";
const STATIC = [
  "/",
  "/manifest.json",
  "/favicon.svg",
  "/robots.txt",
  "/sitemap.xml",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(STATIC)).catch(() => {}),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  // Only handle GET
  if (e.request.method !== "GET") return;

  // Static assets: cache-first
  if (
    e.request.url.match(/\.(js|css|png|svg|ico|woff2?|json|xml|txt)$/) ||
    STATIC.includes(new URL(e.request.url).pathname)
  ) {
    e.respondWith(
      caches.match(e.request).then((cached) => cached || fetch(e.request).then((r) => {
        const clone = r.clone();
        caches.open(CACHE).then((c) => c.put(e.request, clone));
        return r;
      }).catch(() => cached)),
    );
    return;
  }

  // Page navigations: network-first, fallback to index
  if (e.request.mode === "navigate") {
    e.respondWith(
      fetch(e.request).catch(() =>
        caches.match("/").then((r) => r || Response.redirect("/", 302)),
      ),
    );
    return;
  }

  // Everything else: network-first
  e.respondWith(
    fetch(e.request).catch(() =>
      caches.match(e.request).then((r) => r || new Response("offline", { status: 503 })),
    ),
  );
});