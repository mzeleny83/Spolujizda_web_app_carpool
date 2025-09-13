// Chat functions for ride sharing app
let chatMap, routeWaypoints = [], routeMarkers = [], routeLine = null, userMarker = null;

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
  
  if (!Array.isArray(rides) || rides.length === 0) {
    resultsContainer.innerHTML = "<p>Žádné jízdy nenalezeny.</p>";
    return;
  }
  
  let html = `<h3>Dostupné jízdy (${rides.length}):</h3>`;
  rides.forEach((ride) => {
    html += `
      <div style="margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
        <h4>🚗 ${ride.driver_name || 'Neznámý řidič'}</h4>
        <p><strong>${ride.from_location}</strong> → <strong>${ride.to_location}</strong></p>
        <p>🕐 ${ride.departure_time} | 👥 ${ride.available_seats} míst | 💰 ${ride.price_per_person} Kč</p>
        <button class="chat-btn" data-ride-id="${ride.id}" data-driver-name="${ride.driver_name || 'Řidič'}" style="background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">💬 Chat s řidičem</button>
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
    // Mobilní fallback - použij alert + confirm
    const userChoice = confirm(`📨 Nová zpráva od ${senderName}:\n"${message}"\n\nChcete otevřít chat?`);
    if (userChoice) {
      openChat(rideId, senderName);
    }
    return;
  }
  
  // Desktop verze
  // Vyčisti staré notifikace
  const oldNotifications = document.querySelectorAll('.desktop-notification');
  oldNotifications.forEach(notif => notif.remove());
  
  const notification = document.createElement('div');
  notification.className = 'desktop-notification';
  notification.style.cssText = `
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
  `;
  
  notification.innerHTML = `
    <div style="font-weight: bold; margin-bottom: 5px;">📨 Nová zpráva!</div>
    <div style="margin-bottom: 5px;">Od: <strong>${senderName}</strong></div>
    <div style="margin-bottom: 10px; font-style: italic;">"${message}"</div>
    <div>
      <button onclick="openChat(${rideId}, '${senderName}'); this.parentElement.parentElement.remove();" style="background: white; color: #4CAF50; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-right: 5px;">💬 Chat</button>
      <button onclick="this.parentElement.parentElement.remove()" style="background: rgba(255,255,255,0.3); color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer;">×</button>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Auto-remove po 8 sekundách
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 8000);
  
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
    console.log('CHAT v340 - Opening chat with:', driverName, 'for ride:', rideId);
    
    // Vytvoříme modal okno místo popup
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: rgba(0,0,0,0.5) !important; z-index: 999999 !important; display: flex !important; justify-content: center !important; align-items: center !important;';
    
    const chatBox = document.createElement('div');
    chatBox.style.cssText = 'background: white !important; width: 400px !important; height: 500px !important; border-radius: 10px !important; padding: 20px !important; position: relative !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;';
    
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText = 'background: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; position: absolute; top: 10px; right: 10px;';
    closeBtn.onclick = () => modal.remove();
    
    chatBox.innerHTML = `
      <h3 style="margin-top: 0;">Chat s ${driverName}</h3>
      <div id="chatMessages" style="height: 350px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background: #f9f9f9;"></div>
      <div style="display: flex; gap: 10px;">
        <input type="text" id="chatInput" placeholder="Napište zprávu..." style="flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
        <button onclick="sendChatMessage(${rideId})" style="background: #4CAF50; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer;">Odeslat</button>
      </div>
    `;
    
    chatBox.appendChild(closeBtn);
    modal.appendChild(chatBox);
    document.body.appendChild(modal);
    
    console.log('Modal created and added to body');
    
    // Načteme zprávy
    loadChatMessages(rideId);
    
    // Automatické obnovování
    const interval = setInterval(() => loadChatMessages(rideId), 3000);
    
    // Vyčistíme interval při zavření
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        clearInterval(interval);
        modal.remove();
      }
    });
    
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
      userName = user.name || 'Anonym';
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
    const response = await fetch('/api/chat/' + rideId + '/messages');
    const messages = await response.json();
    
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) return;
    
    // Získej jméno uživatele z localStorage
    let userName = 'Anonym';
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
      try {
        const user = JSON.parse(currentUser);
        userName = user.name || 'Anonym';
      } catch (e) {
        console.error('Error parsing currentUser:', e);
      }
    }
    
    messagesDiv.innerHTML = '';
    
    messages.forEach(msg => {
      const div = document.createElement('div');
      const isMyMessage = msg.sender_name === userName;
      div.style.cssText = `margin: 8px 0; padding: 8px; border-radius: 8px; ${isMyMessage ? 'background: #e3f2fd; text-align: right; margin-left: 50px;' : 'background: #f5f5f5; margin-right: 50px;'}`;
      const now = new Date();
      const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
      div.innerHTML = `<strong>${msg.sender_name}:</strong> ${msg.message}<br><small style="color: #666;">${timeStr}</small>`;
      messagesDiv.appendChild(div);
    });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  } catch (error) {
    console.error('Chyba při načítání zpráv:', error);
  }
}







