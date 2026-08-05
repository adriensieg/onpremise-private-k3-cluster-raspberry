const CACHE = "scanning-v1";
// Service worker scope is /scanning/, so registration.scope gives us the prefix.
const ROOT = new URL(self.registration.scope).pathname.replace(/\/$/, "");
const ASSETS = [
  `${ROOT}/`,
  `${ROOT}/static/style.css`,
  `${ROOT}/static/script.js`,
  `${ROOT}/manifest.json`,
  `${ROOT}/static/icons/icon-192.png`,
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.url.includes("/api/")) {
    event.respondWith(fetch(request));
    return;
  }
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request))
  );
});
