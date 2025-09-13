self.addEventListener('push', function(event) {
  const data = event.data.json();
  console.log('Push received:', data);

  const title = data.title || 'New Message';
  const options = {
    body: data.body || 'You have a new message.',
    icon: data.icon || '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png', // Optional: for Android
    data: data.data || {} // Custom data, e.g., URL to open on click
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  console.log('Notification click received:', event.notification.data);
  event.notification.close();

  const urlToOpen = event.notification.data.url || '/';

  event.waitUntil(
    clients.openWindow(urlToOpen)
  );
});