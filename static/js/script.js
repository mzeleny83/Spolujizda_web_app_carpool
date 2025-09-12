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
    } else {
      const error = await response.json();
      console.error('Chyba při odesílání:', error);
    }
  } catch (error) {
    console.error('Chyba při odesílání:', error);
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
      let timeStr = 'Neznámý čas';
      if (msg.created_at) {
        console.log('Raw date from server:', msg.created_at, typeof msg.created_at);
        try {
          const date = new Date(msg.created_at);
          console.log('Parsed date:', date, 'isValid:', !isNaN(date.getTime()));
          if (!isNaN(date.getTime())) {
            timeStr = date.toLocaleString();
          } else {
            console.error('Invalid date:', msg.created_at);
          }
        } catch (e) {
          console.error('Error parsing date:', msg.created_at, e);
        }
      }
      div.innerHTML = `<strong>${msg.sender_name}:</strong> ${msg.message}<br><small style="color: #666;">${timeStr}</small>`;
      messagesDiv.appendChild(div);
    });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  } catch (error) {
    console.error('Chyba při načítání zpráv:', error);
  }
}

function testNotificationDisplay() {
  console.log('TEST - Forcing notification display');
  alert('TEST NOTIFIKACE: Toto je testovací notifikace!');
  showFloatingNotification('Test Uživatel', 'Testovací zpráva pro ověření funkčnosti notifikací', 123);
  
  // Test notifikačního systému
  const currentUser = localStorage.getItem('currentUser');
  if (currentUser) {
    console.log('Current user found, testing notification check...');
    checkForNotifications();
  } else {
    alert('Není přihlášený uživatel!');
  }
}

function showFloatingNotification(senderName, message, rideId) {
  console.log('NOTIFICATION v350 - Showing notification:', senderName, message, rideId);
  
  const notification = document.createElement('div');
  notification.innerHTML = `
    <div style="background: #4CAF50; color: white; padding: 15px; border-radius: 8px; margin: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-family: Arial, sans-serif;">
      <div style="font-weight: bold; margin-bottom: 5px;">📨 Nová zpráva!</div>
      <div style="margin-bottom: 5px;">Od: <strong>${senderName}</strong></div>
      <div style="margin-bottom: 10px; font-style: italic;">"${message}"</div>
      <button onclick="openChat(${rideId}, '${senderName}'); this.parentElement.parentElement.remove();" style="background: white; color: #4CAF50; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;">💬 Otevřít chat</button>
      <button onclick="this.parentElement.parentElement.remove()" style="background: rgba(255,255,255,0.3); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin-left: 5px;">×</button>
    </div>
  `;
  
  notification.style.position = 'fixed';
  notification.style.top = '20px';
  notification.style.right = '20px';
  notification.style.zIndex = '999999';
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    if (document.body.contains(notification)) {
      notification.remove();
    }
  }, 8000);
}

async function checkForNotifications() {
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    console.log('NOTIF v348 - No current user');
    return;
  }
  
  try {
    const user = JSON.parse(currentUser);
    const url = `/api/notifications/${encodeURIComponent(user.name)}`;
    console.log('NOTIF v348 - Checking notifications for:', user.name, 'URL:', url);
    
    const response = await fetch(url);
    const notifications = await response.json();
    console.log('NOTIF v348 - Notifications response:', notifications);
    
    if (notifications.length > 0) {
      // Zobraz všechny notifikace bez sledování
      notifications.forEach(notification => {
        console.log('NOTIF v348 - Showing notification:', notification);
        showFloatingNotification(notification.sender_name, notification.message, notification.ride_id);
      });
    } else {
      console.log('NOTIF v348 - No notifications found');
    }
  } catch (error) {
    console.error('NOTIF v348 - Notification check error:', error);
  }
}