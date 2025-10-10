// Service Worker for Spolujizda Enhanced

const CACHE_NAME = 'spolujizda-v1';
const urlsToCache = [
    '/',
    '/static/js/enhanced_features.js',
    '/static/css/enhanced_styles.css',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch event
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            })
    );
});

// Push event
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'Nová zpráva!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Otevřít chat',
                icon: '/static/icons/checkmark.png'
            },
            {
                action: 'close',
                title: 'Zavřít',
                icon: '/static/icons/xmark.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Spolujízda', options)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'explore') {
        // Open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'close') {
        // Just close the notification
        event.notification.close();
    } else {
        // Default action - open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Background sync
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Sync pending messages, location updates, etc.
    try {
        const pendingRequests = await getStoredRequests();
        for (const request of pendingRequests) {
            await fetch(request.url, request.options);
        }
        await clearStoredRequests();
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

async function getStoredRequests() {
    // Get requests from IndexedDB or localStorage
    return JSON.parse(localStorage.getItem('pendingRequests') || '[]');
}

async function clearStoredRequests() {
    localStorage.removeItem('pendingRequests');
}