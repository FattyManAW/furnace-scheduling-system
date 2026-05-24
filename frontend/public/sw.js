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

  // Page navigations: network-first, fallback to cached "/" or offline page
  if (e.request.mode === "navigate") {
    e.respondWith(
      fetch(e.request).catch(async () => {
        const cachedRoot = await caches.match("/");
        if (cachedRoot) return cachedRoot;
        return new Response(
          "<!DOCTYPE html><html lang=\"zh-TW\"><head><meta charset=\"UTF-8\"><title>离线模式</title></head><body style=\"display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:system-ui;background:#181b23;color:#e2e8f0;text-align:center\"><div><h1>📡</h1><p>目前为离线模式</p><p style=\"font-size:14px;opacity:.6\">请检查网络连线后重整页面</p></div></body></html>",
          { status: 503, headers: { "Content-Type": "text/html" } },
        );
      }),
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