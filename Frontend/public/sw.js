// Minimal service worker for Chrome PWA installability.
//
// Deliberately network-only: it never writes to the Cache Storage API and does
// not cache authentication, API, purchase, inventory, reporting, customer, or
// any other sensitive/network data.

self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('fetch', (event) => {
  // Relay every request straight to the network; no caching of any kind.
  event.respondWith(fetch(event.request))
})
