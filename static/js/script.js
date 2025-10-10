// Chat functions for ride sharing app
let chatMap, routeWaypoints = [], routeMarkers = [], routeLine = null, userMarker = null;

// Function to convert VAPID public key from base64 to Uint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

async function setupPushNotifications() {
    console.log('Setting up push notifications...');
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn('Push notifications not supported by this browser.');
        return;
    }

    try {
        // Fetch VAPID public key from backend
        const response = await fetch('/api/vapid-public-key');
        const data = await response.json();
        const vapidPublicKey = data.publicKey;

        if (!vapidPublicKey || vapidPublicKey === 'BP_YOUR_PUBLIC_KEY_HERE') {
            console.warn('VAPID Public Key not configured on the server. Push notifications will not work.');
            return;
        }

        const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);

        const registration = await navigator.serviceWorker.register('/static/js/sw.js');
        console.log('Service Worker registered:', registration);

        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            console.log('Notification permission granted.');

            const subscribeOptions = {
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            };

            const pushSubscription = await registration.pushManager.subscribe(subscribeOptions);
            console.log('Push Subscription:', pushSubscription);

            // Get current user ID from localStorage
            let userId = null;
            const currentUser = localStorage.getItem('currentUser');
            if (currentUser) {
                try {
                    const user = JSON.parse(currentUser);
                    userId = user.user_id;
                } catch (e) {
                    console.error('Error parsing currentUser from localStorage:', e);
                }
            }

            if (!userId) {
                console.warn('User not logged in. Cannot save push subscription to backend.');
                return;
            }

            // Send subscription to backend
            const subscribeResponse = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId,
                    subscription: pushSubscription
                })
            });

            if (subscribeResponse.ok) {
                console.log('Push subscription sent to backend successfully.');
            } else {
                const error = await subscribeResponse.json();
                console.error('Failed to send push subscription to backend:', error);
            }

        } else {
            console.warn('Notification permission denied.');
        }
    } catch (error) {
        console.error('Error setting up push notifications:', error);
    }
}

// Call setupPushNotifications when the DOM is loaded
document.addEventListener('DOMContentLoaded', setupPushNotifications);

// Function to create test reservation for notification testing
async function createTestReservation() {
  try {
    const response = await fetch('/api/reservations/create', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        ride_id: 34,
        passenger_id: 2, // Pokus Pokus user ID
        seats_reserved: 1
      })
    });
    
    const result = await response.json();
    console.log('Test reservation created:', result);
  } catch (error) {
    console.error('Error creating test reservation:', error);
  }
}

// Missing function for showAll button
function showAll() {
  const results = document.getElementById('searchResults');
  if (results) {
    results.innerHTML = '⏳ Načítám všechny jízdy...';
    
    fetch('/api/rides/search')
      .then(response => response.json())
      .then(rides => {
        if (rides.length === 0) {
          results.innerHTML = '<div style="text-align:center;color:#666;margin:30px 0;">❌ Žádné jízdy nenalezeny</div>';
          return;
        }
        
        results.innerHTML = rides.map(ride => `
          <div class="ride">
            <h3>${ride.from_location} → ${ride.to_location}</h3>
            <div>🕐 ${ride.departure_time} | 👥 ${ride.available_seats} míst | 💰 ${ride.price_per_person} Kč</div>
            <div>🚗 ${ride.driver_name || 'Neznámý řidič'}</div>
            <div style="margin-top: 10px;">
              <button class="btn" onclick="openChat(${ride.id}, '${ride.driver_name}')" style="background: #17a2b8; padding: 5px 15px;">💬 Chat s řidičem</button>
            </div>
          </div>
        `).join('');
      })
      .catch(error => {
        results.innerHTML = '❌ Chyba: ' + error.message;
      });
  }
}

function updateUserLocation(lat, lng) {
  if (chatMap && userMarker) {
    chatMap.removeLayer(userMarker);
  }
  
  if (chatMap) {
    const userName = localStorage.getItem('user_name') || 'Vy';
    const userIcon = L.divIcon({
      html: '<div style="background: #007bff; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">👤</div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
    
    const popupContent = `
      <div style="text-align: center; min-width: 150px;">
        <h4>📍 ${userName}</h4>
        <p>Vaše aktuální poloha</p>
      </div>
    `;

    userMarker = L.marker([lat, lng], { icon: userIcon })
      .addTo(chatMap)
      .bindPopup(popupContent);
  }
}

async function offerRide() {
  const userName = localStorage.getItem("user_name");
  if (!userName) {
    alert("Musíte zadat své jméno pro nabízení jízd");
    return;
  }

  const formData = {
    user_name: userName,
    from_location: document.getElementById("fromOffer").value,
    to_location: document.getElementById("toOffer").value,
    departure_time: document.getElementById("departureOffer").value,
    available_seats: parseInt(document.getElementById("seatsOffer").value),
    price_per_person: parseInt(document.getElementById("priceOffer").value),
    route_waypoints: routeWaypoints,
  };

  try {
    const response = await fetch("/api/rides/offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });

    const result = await response.json();

    if (response.ok) {
      alert("Jízda byla úspěšně nabídnuta!");
      document.getElementById("rideOfferForm").reset();
      clearRoute();
    } else {
      alert("Chyba: " + result.error);
    }
  } catch (error) {
    alert("Chyba při odesílání: " + error.message);
  }
}

async function searchRides() {
  const from = document.getElementById("fromSearch").value;
  const to = document.getElementById("toSearch").value;

  try {
    let url = `/api/rides/search-text?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    const rides = await response.json();

    displayAllRides(rides);
  } catch (error) {
    alert("Chyba při hledání: " + error.message);
  }
}

function displayAllRides(rides) {
  const resultsContainer = document.getElementById("results");
  
  // Ensure rides is an array before proceeding
  if (!Array.isArray(rides) || rides.length === 0) {
    resultsContainer.innerHTML = "<p>Žádné jízdy nenalezeny.</p>";
    return;
  }
  
  let html = `<h3>Dostupné jízdy (${rides.length}):</h3>`;
  rides.forEach((ride) => {
    // Use nullish coalescing operator (??) for better handling of null/undefined
    const driverName = ride.driver_name ?? 'Neznámý řidič';
    const fromLocation = ride.from_location ?? 'Neznámé';
    const toLocation = ride.to_location ?? 'Neznámé';
    const departureTime = ride.departure_time ?? 'Neznámý čas';
    const availableSeats = ride.available_seats ?? 'N/A';
    const pricePerPerson = ride.price_per_person ?? 'N/A';

    // Escape single quotes in driverName for the onclick attribute
    const escapedDriverName = driverName.replace(/'/g, "'");

    html += `
      <div style="margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
        <h4>🚗 ${fromLocation} → ${toLocation}</h4>
        <div>🕐 ${departureTime} | 👥 ${availableSeats} míst | 💰 ${pricePerPerson} Kč</div>
        <div>🚗 ${driverName}</div>
        <div style="margin-top: 10px;">
          <button class="chat-btn" data-ride-id="${ride.id}" data-driver-name="${driverName}" onclick="openChat(parseInt(${ride.id}), '${escapedDriverName}'); this.remove();" style="background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">💬 Chat s řidičem</button>
        </div>
      </div>
    `;
  });
  resultsContainer.innerHTML = html;
  
  // Add event listeners to chat buttons
  document.querySelectorAll('.chat-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const rideId = this.getAttribute('data-ride-id');
      const driverName = this.getAttribute('data-driver-name');
      openChat(rideId, driverName);
    });
  });
}

function clearRoute() {
  routeWaypoints = [];
  if (routeMarkers) {
    routeMarkers.forEach(marker => {
      if (chatMap.hasLayer(marker)) {
        chatMap.removeLayer(marker);
      }
    });
    routeMarkers = [];
  }
  if (routeLine) {
    if (chatMap.hasLayer(routeLine)) {
      chatMap.removeLayer(routeLine);
    }
    routeLine = null;
  }
  document.getElementById('fromOffer').value = '';
  document.getElementById('toOffer').value = '';
}

// Placeholder functions for index_fixed.html
function togglePanel() { console.log('togglePanel called'); }
function showOfferForm() { 
    document.getElementById('offerForm').style.display = 'block';
    document.getElementById('searchForm').style.display = 'none';
}
function showSearchForm() {
    document.getElementById('searchForm').style.display = 'block';
    document.getElementById('offerForm').style.display = 'none';
}
function showRecurringForm() { console.log('showRecurringForm called'); }
function showActiveRides() { console.log('showActiveRides called'); }
function showSettings() { console.log('showSettings called'); }

// NOTIFIKAČNÍ SYSTÉM v361 - OPRAVENO ZOBRAZOVÁNÍ
console.log('SCRIPT v361 - Loading fixed notification system');

// Track shown notifications
let shownNotifications = new Set();
let notificationInterval = null;

function startNotificationCheck() {
  console.log('NOTIF v361 - Starting notification check');
  if (notificationInterval) {
    clearInterval(notificationInterval);
  }
  checkForNotifications();
  notificationInterval = setInterval(checkForNotifications, 10000);
}

function stopNotificationCheck() {
  console.log('NOTIF v361 - Stopping notification check');
  if (notificationInterval) {
    clearInterval(notificationInterval);
    notificationInterval = null;
  }
}

async function checkForNotifications() {
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    console.log('NOTIF v361 - No current user');
    return;
  }
  
  try {
    const user = JSON.parse(currentUser);
    const url = `/api/notifications/v361/${encodeURIComponent(user.name)}`;
    console.log('NOTIF v361 - Checking notifications for:', user.name, 'URL:', url);
    
    const response = await fetch(url);
    if (!response.ok) {
      console.error('NOTIF v361 - API error:', response.status, response.statusText);
      return;
    }
    
    const notifications = await response.json();
    console.log('NOTIF v361 - Got', notifications.length, 'notifications:', notifications);
    
    if (notifications.length > 0) {
      let newCount = 0;
      notifications.forEach(notification => {
        const notifId = `${notification.ride_id}-${notification.sender_name}-${notification.created_at}`;
        console.log('NOTIF v361 - Checking notification ID:', notifId);
        console.log('NOTIF v361 - Already shown?', shownNotifications.has(notifId));
        console.log('NOTIF v361 - Shown notifications cache:', Array.from(shownNotifications));
        
        if (!shownNotifications.has(notifId)) {
          console.log('NOTIF v361 - NEW notification:', notification.sender_name, notification.message);
          showFloatingNotification(notification.sender_name, notification.message, notification.ride_id);
          shownNotifications.add(notifId);
          newCount++;
        } else {
          console.log('NOTIF v361 - SKIPPING already shown notification:', notification.sender_name);
        }
      });
      
      if (newCount > 0) {
        console.log(`NOTIF v361 - Showed ${newCount} new notifications`);
      } else {
        console.log('NOTIF v361 - No new notifications to show');
      }
    }
  } catch (error) {
    console.error('NOTIF v361 - Error:', error);
  }
}

// Debug funkce pro vyčištění cache
function clearNotificationCache() {
  shownNotifications.clear();
  console.log('NOTIF CACHE CLEARED');
}

// Vyvolání: clearNotificationCache() v konzoli
window.clearNotificationCache = clearNotificationCache;

// Test mobilní notifikace
window.testMobileNotification = function() {
  console.log('TESTING MOBILE NOTIFICATION');
  showFloatingNotification('Test User', 'Testovací mobilní notifikace', 1);
};

// Debug mobilní detekce
window.checkMobile = function() {
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
  console.log('Mobile check:', {
    userAgent: navigator.userAgent,
    width: window.innerWidth,
    isMobile: isMobile
  });
  alert(`Mobile: ${isMobile}\nWidth: ${window.innerWidth}\nUA: ${navigator.userAgent}`);
};

function showFloatingNotification(senderName, message, rideId) {
  console.log('NOTIFICATION v385 - Showing notification:', senderName, message, rideId);
  
  // Detekce mobilního zařízení
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
  console.log('MOBILE DETECTED:', isMobile, 'UserAgent:', navigator.userAgent, 'Width:', window.innerWidth);
  
  // Na mobilních zařízeních použij jednodušší přístup
  if (isMobile) {
    console.log(`MOBILE NOTIFICATION: New message from ${senderName}: "${message}"`);
    // Directly open chat on mobile for testing purposes
    openChat('notification', rideId, senderName);
    return;
  }
  
  // Desktop verze
  // Vyčisti staré notifikace
  const oldNotifications = document.querySelectorAll('.desktop-notification');
  oldNotifications.forEach(notif => notif.remove());
  
  const notification = document.createElement('div');
  notification.className = 'desktop-notification';
  notification.style.cssText = '
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    z-index: 999999 !important;
    background: #4CAF50 !important;
    color: white !important;
    padding: 15px !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    font-family: Arial, sans-serif !important;
    max-width: 300px !important;
    pointer-events: auto !important;
  ';
  
  notification.innerHTML = '
    <div style="font-weight: bold; margin-bottom: 5px;">📨 Nová zpráva!</div>
    <div style="margin-bottom: 5px;">Od: <strong>${senderName}</strong></div>
    <div style="margin-bottom: 10px; font-style: italic;">"${message}"</div>
    <div>
      <button onclick="openChat(parseInt(${rideId}), \'${senderName.replace(/\'/g, "'" )}\'); this.parentElement.parentElement.remove();" style="background: white; color: #4CAF50; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-right: 5px;">💬 Chat</button>
      <button onclick="this.parentElement.parentElement.remove()" style="background: rgba(255,255,255,0.3); color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer;">×</button>
    </div>
  ';
  
  document.body.appendChild(notification);
  
  
  
  console.log('NOTIFICATION v385 - rideId for onclick:', rideId, 'senderName for onclick:', senderName);
  console.log('NOTIFICATION v385 - Added to DOM');
}



// Dummy funkce pro kompatibilitu
function updateRoutePreview() { console.log('updateRoutePreview called'); }
function planRoute() { console.log('planRoute called'); }
function toggleFullscreen() { console.log('toggleFullscreen called'); }
function centerOnUser() { console.log('centerOnUser called'); }
function showAllUsers() { console.log('showAllUsers called'); }
function clearRideMarkers() { console.log('clearRideMarkers called'); }
function stopVoiceGuidance() { console.log('stopVoiceGuidance called'); }

// Chat funkce
function openChat(rideId, driverName) {
  try {
    console.log('CHAT v390 - Opening chat with:', driverName, 'for ride:', rideId);
    
    // Detekce mobilního zařízení
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
    
    // Vytvoříme modal okno místo popup
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: rgba(0,0,0,0.5) !important; z-index: 999999 !important;';
    
    const chatBox = document.createElement('div');
    // Jednotný styl pro mobil i desktop - centrované okno
    chatBox.style.cssText = `position: absolute !important; top: 20px !important; left: 20px !important; right: auto !important; bottom: auto !important; background: white !important; width: ${isMobile ? '90vw' : '400px'} !important; height: ${isMobile ? '80vh' : '500px'} !important; border-radius: 10px !important; padding: 20px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;`;
    
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText = 'background: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; position: absolute; top: 10px; right: 10px;';
    closeBtn.onclick = () => modal.remove();
    
    const messagesHeight = isMobile ? 'calc(100% - 120px)' : '350px';
    
    // Ensure driverName is a string before using it in the template literal
    const displayDriverName = driverName ?? 'Neznámý';

    chatBox.innerHTML = `
      <h3 style=\"margin-top: 0; font-size: ${isMobile ? '18px' : '20px'};\">Chat s ${displayDriverName}</h3>
      <div id=\"chatMessages\" style=\"height: ${messagesHeight}; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background: #f9f9f9;\"></div>
      <div style=\"display: flex; gap: 10px;\">
        <input type=\"text\" id=\"chatInput\" placeholder=\"Napište zprávu...\" style=\"flex: 1; padding: ${isMobile ? '12px' : '8px'}; border: 1px solid #ccc; border-radius: 4px; font-size: ${isMobile ? '16px' : '14px'};\">
        <button onclick=\"sendChatMessage(${rideId})\" style=\"background: #4CAF50; color: white; border: none; padding: ${isMobile ? '12px 20px' : '8px 15px'}; border-radius: 4px; cursor: pointer; font-size: ${isMobile ? '16px' : '14px'};\">Odeslat</button>
      </div>
    `;
    
    chatBox.appendChild(closeBtn);
    modal.appendChild(chatBox);
    document.body.appendChild(modal);
    
    console.log('Modal created and added to body');
    
    // Načteme zprávy
    loadChatMessages(rideId);
    
    // Automatické obnovování
    const intervalId = setInterval(() => loadChatMessages(rideId), 3000); // Store the interval ID
    
    // Vyčistíme interval při zavření
    modal.addEventListener('click', (e) => {
      if (e.target === modal || e.target === closeBtn) { // Also clear if closeBtn is clicked
        clearInterval(intervalId); // Clear the specific interval
        modal.remove();
      }
    });
    closeBtn.onclick = () => { // Modify closeBtn.onclick to also clear interval
        clearInterval(intervalId);
        modal.remove();
    };
    
  } catch (error) {
    console.error('Error opening chat:', error);
    alert('Chyba při otevírání chatu: ' + error.message);
  }
}

async function sendChatMessage(rideId) {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;
  
  // Získej jméno uživatele z localStorage
  let userName = 'Anonym';
  const currentUser = localStorage.getItem('currentUser');
  if (currentUser) {
    try {
      const user = JSON.parse(currentUser);
      userName = user.name ?? 'Anonym'; // Use nullish coalescing
    } catch (e) {
      console.error('Error parsing currentUser:', e);
    }
  }
  
  try {
    console.log('CHAT v357 - Sending message:', message, 'to ride:', rideId);
    const response = await fetch('/api/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ride_id: rideId,
        sender_name: userName,
        message: message
      })
    });
    
    if (response.ok) {
      input.value = '';
      loadChatMessages(rideId);
      console.log('CHAT v357 - Message sent successfully');
      
      // Okamžitě zkontroluj notifikace pro ostatní uživatele
      setTimeout(() => {
        console.log('CHAT v357 - Triggering notification check after message send');
        // Toto spustí kontrolu notifikací pro všechny uživatele
      }, 1000);
    } else {
      const error = await response.json();
      console.error('Chyba při odesílání:', error);
      alert('Chyba při odesílání zprávy: ' + (error.error || 'Neznámá chyba'));
    }
  } catch (error) {
    console.error('Chyba při odesílání:', error);
    alert('Chyba při odesílání zprávy: ' + error.message);
  }
}

async function loadChatMessages(rideId) {
  try {
    const parsedRideId = parseInt(rideId, 10); // Ensure rideId is an integer
    if (isNaN(parsedRideId)) {
      console.error('Invalid rideId:', rideId);
      return;
    }
    const response = await fetch('/api/chat/' + parsedRideId + '/messages');
    const messages = await response.json();
    
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) return;
    
    // Získej jméno uživatele z localStorage
    let userName = 'Anonym';
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
      try {
        const user = JSON.parse(currentUser);
        userName = user.name ?? 'Anonym'; // Use nullish coalescing
      } catch (e) {
        console.error('Error parsing currentUser:', e);
      }
    }
    
    messagesDiv.innerHTML = '';
    
    messages.forEach(msg => {
      const div = document.createElement('div');
      const isMyMessage = msg.sender_name === userName;
      div.style.cssText = `margin: 8px 0; padding: 8px; border-radius: 8px; ${isMyMessage ? 'background: #f5f5f5; text-align: left;' : 'background: #e3f2fd; text-align: left;'}`;
      const now = new Date();
      const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
      div.innerHTML = `<strong>${msg.sender_name ?? 'Neznámý'}:</strong> ${msg.message ?? 'Prázdná zpráva'}<br><small style="color: #666;">${timeStr}</small>`;
      messagesDiv.appendChild(div);
    });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  } catch (error) {
    console.error('Chyba při načítání zpráv:', error);
  }
}



// v391 message alignment fix

// GPS Location function
function showMyLocation() {
    if (!navigator.geolocation) {
        alert('GPS není podporováno');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            // Vyplň GPS souřadnice do formuláře
            const fromInput = document.querySelector('input[placeholder*="odkud"], input[placeholder*="Odkud"]');
            if (fromInput) {
                fromInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            }
            
            alert(`GPS: ${lat.toFixed(6)}, ${lng.toFixed(6)}\nSouřadnice vyplněny do formuláře`);
        },
        function(error) {
            alert('GPS chyba: ' + error.message);
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
}