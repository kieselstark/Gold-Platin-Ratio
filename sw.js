const CACHE_NAME = 'gold-silver-ratio-v1';
const API_URL = 'https://api.gold-silver-ratio.com/latest'; // Beispiel-API

// Statische Ressourcen cachen
const urlsToCache = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

// Installationsphase
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

// Cache-Bereinigung alter Versionen
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) return caches.delete(cache);
        })
      );
    })
  );
});

// Fetch-Strategie: Stale-While-Revalidate für API + Cache-Fallback
self.addEventListener('fetch', (event) => {
  // API-Anfragen
  if (event.request.url.includes(API_URL)) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cached) => {
          const fetchPromise = fetch(event.request).then((response) => {
            cache.put(event.request, response.clone()); // Cache updaten
            return response;
          }).catch(() => {
            // Offline-Fallback
            return cached || new Response(JSON.stringify({
              ratio: "16.5",
              lastUpdated: "(Offline-Daten)"
            }), { headers: { 'Content-Type': 'application/json' }});
          });
          return cached || fetchPromise;
        });
      })
    );
  }
  // Statische Dateien
  else {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
