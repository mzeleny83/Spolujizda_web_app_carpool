document.addEventListener('DOMContentLoaded', function() {

// Globální proměnné
let map;
let userMarker;
let userMarkers = {};
let watchId;
let currentUserId;
let isTracking = false;
let routeWaypoints = [];
let routeMarkers = [];
let routeLine = null;
let isRoutePlanning = false;
let deferredPrompt;
window.rideMarkers = [];

// Inicializace při načtení stránky
initializeMap();
setupEventListeners();
initializePWA();
checkUserLogin();

setTimeout(() => {
  requestNotificationPermission();
}, 2000);

window.addEventListener("resize", function () {
  if (map) {
    setTimeout(() => map.invalidateSize(), 100);
  }
  
  const toggleBtn = document.getElementById("panelToggle");
  if (window.innerWidth <= 768) {
    toggleBtn.style.display = "none";
  } else {
    toggleBtn.style.display = "block";
  }
});

// Zkontroluje, zda je uživatel přihlášen
function checkUserLogin() {
  const userId = localStorage.getItem("user_id");
  const userName = localStorage.getItem("user_name");
  const userPhone = localStorage.getItem("user_phone");

  if (userId && userName && userPhone) {
    // User is logged in, update UI
    const userNameInput = document.getElementById("userName");
    if (userNameInput) {
        userNameInput.value = userName;
    }
  }
}

// PWA inicializace
function initializePWA() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .register("/static/sw.js")
      .catch((error) => {
        console.error("SW chyba:", error);
      });
  }

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
  });
}

function installApp() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      deferredPrompt = null;
    });
  }
}

function requestNotificationPermission() {
  if ("Notification" in window) {
    if (Notification.permission === "default") {
      Notification.requestPermission()
        .catch((error) => {
          console.error("Chyba notifikací:", error);
        });
    }
  }
}

// Inicializace mapy s Leaflet (OpenStreetMap)
function initializeMap() {
  try {
    map = L.map("map", {
      zoomControl: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      touchZoom: true,
      dragging: true,
      zoomSnap: 0.25,
      zoomDelta: 0.25,
      wheelPxPerZoomLevel: 120,
    }).setView([50.0755, 14.4378], 13);

    const osmLayer = L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
      }
    );

    osmLayer.addTo(map);

  } catch (error) {
    console.error("Chyba při inicializaci mapy:", error);
  }
}

// Nastavení event listenerů
function setupEventListeners() {
  const rideOfferForm = document.getElementById("rideOfferForm");
  if (rideOfferForm) {
      rideOfferForm.addEventListener("submit", function (e) {
        e.preventDefault();
        offerRide();
      });
  }

  const rideSearchForm = document.getElementById("rideSearchForm");
  if (rideSearchForm) {
      rideSearchForm.addEventListener("submit", function (e) {
        e.preventDefault();
        searchRides();
      });
  }
}

function startTracking() {
  const userName = document.getElementById("userName").value;
  if (!userName) {
      alert("Zadejte prosím své jméno.");
      return;
  }
  localStorage.setItem("user_name", userName);


  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        
        map.setView([lat, lng], 16);
        updateOwnLocation(lat, lng);

        watchId = navigator.geolocation.watchPosition(
          function (position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const accuracy = position.coords.accuracy;

            updateOwnLocation(lat, lng);

            document.getElementById("locationStatus").textContent = 
              `GPS: Aktivní (${(lat || 0).toFixed(6)}, ${(lng || 0).toFixed(6)}) ±${(accuracy || 0).toFixed(0)}m`;
          },
          function (error) {
            console.error("Chyba při sledování:", error);
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0,
          }
        );

        isTracking = true;
        document.getElementById("locationStatus").textContent = "GPS: Aktivní";

      },
      function (error) {
        console.error("Chyba při získávání polohy:", error);
        document.getElementById("locationStatus").textContent =
          "GPS: Chyba - zkontrolujte povolení lokalizace";
      },
      {
        enableHighAccuracy: false,
        timeout: 15000,
        maximumAge: 300000,
      }
    );
  }
}

function stopTracking() {
  if (watchId) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }
  document.getElementById("locationStatus").textContent = "GPS: Neaktivní";
  isTracking = false;
}

function updateOwnLocation(lat, lng) {
  if (map && typeof L !== "undefined") {
    if (userMarker) {
      userMarker.setLatLng([lat, lng]);
    } else {
      const userIcon = L.divIcon({
        html: '<div style="background: #4285f4; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
        iconSize: [26, 26],
        iconAnchor: [13, 13],
        className: "user-marker",
      });

      const userName = localStorage.getItem("user_name") || "Vy";
      const popupContent = `
        <div style="text-align: center; min-width: 150px;">
          <h4>📍 ${userName}</h4>
          <p>Vaše aktuální poloha</p>
        </div>
      `;

      userMarker = L.marker([lat, lng], { icon: userIcon })
        .addTo(map)
        .bindPopup(popupContent);
    }
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
        <button onclick="openChat(${ride.id}, '${ride.driver_name || 'Řidič'}')" style="background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">💬 Chat s řidičem</button>
      </div>
    `;
  });
  resultsContainer.innerHTML = html;
}

function clearRoute() {
  routeWaypoints = [];
  if (routeMarkers) {
    routeMarkers.forEach(marker => {
      if (map.hasLayer(marker)) {
        map.removeLayer(marker);
      }
    });
    routeMarkers = [];
  }
  if (routeLine) {
    if (map.hasLayer(routeLine)) {
      map.removeLayer(routeLine);
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
  console.log('Opening chat with:', driverName, 'for ride:', rideId);
  
  const chatWindow = window.open('', 'chat', 'width=400,height=600,scrollbars=yes,resizable=yes');
  
  if (!chatWindow) {
    alert('Popup okno bylo blokováno prohlížečem. Povolte popup okna pro tuto stránku.');
    return;
  }
  
  chatWindow.document.write(`
    <html>
    <head>
      <title>Chat s ${driverName}</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 10px; }
        #messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        #messageInput { width: 70%; padding: 5px; }
        #sendBtn { width: 25%; padding: 5px; }
        .message { margin: 5px 0; padding: 5px; border-radius: 5px; }
        .my-message { background: #e3f2fd; text-align: right; }
        .other-message { background: #f5f5f5; }
      </style>
    </head>
    <body>
      <h3>Chat s ${driverName}</h3>
      <div id="messages"></div>
      <input type="text" id="messageInput" placeholder="Napište zprávu..." onkeypress="if(event.key==='Enter') sendMessage()">
      <button id="sendBtn" onclick="sendMessage()">Odeslat</button>
      
      <script>
        const rideId = ${rideId};
        const userName = localStorage.getItem('user_name') || 'Anonym';
        
        async function sendMessage() {
          const input = document.getElementById('messageInput');
          const message = input.value.trim();
          if (!message) return;
          
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
              loadMessages();
            }
          } catch (error) {
            console.error('Chyba při odesílání:', error);
          }
        }
        
        async function loadMessages() {
          try {
            const response = await fetch('/api/chat/' + rideId + '/messages');
            const messages = await response.json();
            
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = '';
            
            messages.forEach(msg => {
              const div = document.createElement('div');
              div.className = 'message ' + (msg.sender_name === userName ? 'my-message' : 'other-message');
              div.innerHTML = '<strong>' + msg.sender_name + ':</strong> ' + msg.message + '<br><small>' + new Date(msg.timestamp).toLocaleString() + '</small>';
              messagesDiv.appendChild(div);
            });
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
          } catch (error) {
            console.error('Chyba při načítání zpráv:', error);
          }
        }
        
        loadMessages();
        setInterval(loadMessages, 3000);
      </script>
    </body>
    </html>
  `);
  
  chatWindow.document.close();
}
