const CACHE_NAME = 'spolujizda-v2';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/script.js',
  '/static/js/navigation.js',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

const API_CACHE = 'api-cache-v1';
const OFFLINE_DATA = 'offline-data';

// Instalace service workeru
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// Obsluha požadavků s offline podporou
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // API požadavky - cache first s fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(API_CACHE).then(cache => {
        return cache.match(request).then(cachedResponse => {
          const fetchPromise = fetch(request).then(networkResponse => {
            if (networkResponse.ok) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          }).catch(() => {
            // Offline fallback data
            if (url.pathname.includes('/search')) {
              return new Response(JSON.stringify([]), {
                headers: { 'Content-Type': 'application/json' }
              });
            }
            throw new Error('Offline - no cached data');
          });
          
          return cachedResponse || fetchPromise;
        });
      })
    );
  } else {
    // Static resources
    event.respondWith(
      caches.match(request).then(response => {
        return response || fetch(request).catch(() => {
          // Offline fallback page
          if (request.mode === 'navigate') {
            return caches.match('/');
          }
        });
      })
    );
  }
});

// Push notifikace
self.addEventListener('push', event => {
  let data = { title: 'Spolujízda', body: 'Nová jízda dostupná!' };
  
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  const options = {
    body: data.body,
    icon: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByeD0iOCIgZmlsbD0iIzY2N2VlYSIvPgo8cGF0aCBkPSJNNTIgMjBIMTJDMTAuOSAyMCAxMCAyMC45IDEwIDIyVjQyQzEwIDQzLjEgMTAuOSA0NCAxMiA0NEgxNFY0OEMxNCA0OS4xIDE0LjkgNTAgMTYgNTBIMThDMTkuMSA1MCAyMCA0OS4xIDIwIDQ4VjQ0SDQ0VjQ4QzQ0IDQ5LjEgNDQuOSA1MCA0NiA1MEg0OEM0OS4xIDUwIDUwIDQ5LjEgNTAgNDhWNDRINTJDNTMuMSA0NCA1NCA0My4xIDU0IDQyVjIyQzU0IDIwLjkgNTMuMSAyMCA1MiAyMFpNMTggMzZDMTYuOSAzNiAxNiAzNS4xIDE2IDM0QzE2IDMyLjkgMTYuOSAzMiAxOCAzMkMxOS4xIDMyIDIwIDMyLjkgMjAgMzRDMjAgMzUuMSAxOS4xIDM2IDE4IDM2Wk00NiAzNkM0NC45IDM2IDQ0IDM1LjEgNDQgMzRDNDQgMzIuOSA0NC45IDMyIDQ2IDMyQzQ3LjEgMzIgNDggMzIuOSA0OCAzNEM0OCAzNS4xIDQ3LjEgMzYgNDYgMzZaTTEyIDI4SDUyVjIySDEyVjI4WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
    badge: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTE4LjkyIDYuMDFDMTguNzIgNS40MiAxOC4xNiA1IDE3LjUgNUgxNVYzSDEzVjVIMTFWM0g5VjVINi41QzUuODQgNSA1LjI4IDUuNDIgNS4wOCA2LjAxTDMgMTJWMjBDMyAyMC41NSAzLjQ1IDIxIDQgMjFINUM1LjU1IDIxIDYgMjAuNTUgNiAyMFYxOUgxOFYyMEMxOCAyMC41NSAxOC40NSAyMSAxOSAyMUgyMEMyMC41NSAyMSAyMSAyMC41NSAyMSAyMFYxMkwxOC45MiA2LjAxWk02LjUgMTZDNS42NyAxNiA1IDE1LjMzIDUgMTQuNVM1LjY3IDEzIDYuNSAxMyA4IDEzLjY3IDggMTQuNSA3LjMzIDE2IDYuNSAxNlpNMTcuNSAxNkMxNi42NyAxNiAxNiAxNS4zMyAxNiAxNC41UzE2LjY3IDEzIDE3LjUgMTMgMTkgMTMuNjcgMTkgMTQuNSAxOC4zMyAxNiAxNy41IDE2Wk01IDExTDE5IDExTDE3LjMgN0g2LjdMNSAxMVoiIGZpbGw9IiM2NjdlZWEiLz4KPC9zdmc+',
    vibrate: [200, 100, 200],
    tag: 'spolujizda-notification',
    requireInteraction: true,
    data: data,
    actions: [
      {
        action: 'view',
        title: '👁️ Zobrazit',
      },
      {
        action: 'dismiss',
        title: '❌ Zavřít'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Spolujízda', options)
  );
});

// Klik na notifikaci
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'view' || !event.action) {
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then(clientList => {
        if (clientList.length > 0) {
          return clientList[0].focus();
        }
        return clients.openWindow('/');
      })
    );
  }
});

// Background sync pro offline akce
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      caches.open(OFFLINE_DATA).then(cache => {
        return cache.match('pending-actions').then(response => {
          if (response) {
            return response.json().then(actions => {
              return Promise.all(
                actions.map(action => 
                  fetch(action.url, action.options)
                    .then(() => console.log('Offline action synced:', action))
                    .catch(err => console.error('Sync failed:', err))
                )
              );
            });
          }
        });
      })
    );
  }
});

// Aktualizace cache
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});