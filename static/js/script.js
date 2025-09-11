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
    updateUIForLoggedInUser(userName);
  }
}

function updateUIForLoggedInUser(userName) {
  document.getElementById("loginButtons").style.display = "none";
  const welcomeMsg = document.getElementById("welcomeMessage");
  welcomeMsg.textContent = `Vítejte, ${userName}!`;
  welcomeMsg.style.display = "block";
  document.getElementById("logoutButton").style.display = "block";
}

function updateUIForLoggedOutUser() {
  document.getElementById("loginButtons").style.display = "block";
  document.getElementById("welcomeMessage").style.display = "none";
  document.getElementById("logoutButton").style.display = "none";
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

function sendNotification(title, body) {
  if ("serviceWorker" in navigator && "Notification" in window) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.showNotification(title, {
        body: body,
        icon: "/static/images/app_icon.png",
        vibrate: [200, 100, 200],
      });
    });
  }
}

function normalizePhoneNumber(phone) {
  let normalizedPhone = phone.replace(/[^0-9]/g, "");
  if (normalizedPhone.startsWith("420")) {
    normalizedPhone = normalizedPhone.substring(3);
  }
  return normalizedPhone;
}

function modalLoginUser() {
  const phone = document.getElementById("modalLoginPhone").value;
  const password = document.getElementById("modalLoginPassword").value;

  if (!phone || !password) {
    alert("Vyplňte všechna pole!");
    return;
  }

  const fullPhone = `+420${normalizePhoneNumber(phone)}`;

  fetch("/api/users/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone: fullPhone, password: password }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.user_id) {
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("user_name", data.name);
        localStorage.setItem("user_phone", fullPhone);
        updateUIForLoggedInUser(data.name);
        closeLoginModal();
        document.getElementById("loginRequiredMessage").style.display = "none";
      } else {
        alert(data.error || "Nesprávné přihlašovací údaje");
      }
    })
    .catch((error) => {
      console.error("Chyba při přihlášení:", error);
      alert("Chyba při přihlášení");
    });
}

function modalRegisterUser() {
  const phone = document.getElementById("modalRegPhone").value;
  const name = document.getElementById("modalRegName").value;
  const email = document.getElementById("modalRegEmail").value;
  const password = document.getElementById("modalRegPassword").value;
  const passwordConfirm = document.getElementById("modalRegPasswordConfirm").value;

  if (!name || !phone || !password || !passwordConfirm) {
    alert("Vyplňte všechna pole!");
    return;
  }

  if (password !== passwordConfirm) {
    alert("Hesla se neshodují!");
    return;
  }

  const normalizedPhone = normalizePhoneNumber(phone);

  if (normalizedPhone.length !== 9) {
    alert("Zadejte platné české telefonní číslo (9 číslic)");
    return;
  }

  fetch("/api/users/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: name,
      phone: `+420${normalizedPhone}`,
      email: email,
      password: password,
      password_confirm: passwordConfirm,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.message) {
        closeRegisterModal();
        showQuickLogin();
      }
    })
    .catch((error) => {
      console.error("Chyba při registraci:", error);
    });
}

function logoutUser() {
  localStorage.removeItem("user_id");
  localStorage.removeItem("user_name");
  localStorage.removeItem("user_phone");
  updateUIForLoggedOutUser();
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
  document.getElementById("rideOfferForm").addEventListener("submit", function (e) {
    e.preventDefault();
    offerRide();
  });

  document.getElementById("rideSearchForm").addEventListener("submit", function (e) {
    e.preventDefault();
    searchRides();
  });

  document.getElementById("showQuickLoginBtn").addEventListener("click", showQuickLogin);
  document.getElementById("showQuickRegisterBtn").addEventListener("click", showQuickRegister);
  document.getElementById("trackingBtn").addEventListener("click", toggleTracking);
  document.getElementById("toggleOfferFormBtn").addEventListener("click", toggleOfferForm);
  document.getElementById("toggleSearchFormBtn").addEventListener("click", toggleSearchForm);
  document.getElementById("logoutButton").addEventListener("click", logoutUser);
  document.getElementById("modalLoginUserBtn").addEventListener("click", modalLoginUser);
  document.getElementById("modalRegisterUserBtn").addEventListener("click", modalRegisterUser);
  document.getElementById("closeLoginModalBtn").addEventListener("click", closeLoginModal);
  document.getElementById("closeRegisterModalBtn").addEventListener("click", closeRegisterModal);
  document.getElementById("showAllRidesBtn").addEventListener("click", showAllRides);
}

function showQuickLogin() {
  document.getElementById("loginModal").style.display = "block";
}

function showQuickRegister() {
  document.getElementById("registerModal").style.display = "block";
}

function closeLoginModal() {
  document.getElementById("loginModal").style.display = "none";
  document.getElementById("loginRequiredMessage").style.display = "none";
}

function closeRegisterModal() {
  document.getElementById("registerModal").style.display = "none";
}

function toggleTracking() {
  if (!checkLoginRequired()) return;

  if (isTracking) {
    stopTracking();
  } else {
    startTracking();
  }
}

function startTracking() {
  const userId = localStorage.getItem("user_id");
  const userName = localStorage.getItem("user_name");

  if (!userId || !userName) {
    return;
  }

  currentUserId = userId;

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const accuracy = position.coords.accuracy;
        
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
        const btn = document.getElementById("trackingBtn");
        btn.innerHTML = "⏹️ Zastavit sledování";
        btn.title = "Zastaví sledování GPS polohy";
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

  const btn = document.getElementById("trackingBtn");
  btn.innerHTML = "📍 Najít mě a sledovat";
  btn.title = "Spustí sledování vaší GPS polohy a vycentruje mapu na vaši pozici";
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

function toggleOfferForm() {
  if (!checkLoginRequired()) return;

  const form = document.getElementById("offerForm");
  if (form.style.display === "block") {
    form.style.display = "none";
  } else {
    hideAllForms();
    form.style.display = "block";
  }
}

function toggleSearchForm() {
  const form = document.getElementById("searchForm");
  if (form.style.display === "block") {
    form.style.display = "none";
    document.getElementById("results").innerHTML = "";
  } else {
    hideAllForms();
    form.style.display = "block";
    showAllRides();
  }
}

function hideAllForms() {
  document.getElementById("offerForm").style.display = "none";
  document.getElementById("searchForm").style.display = "none";
  document.getElementById("results").innerHTML = "";
}

function checkLoginRequired() {
  const userId = localStorage.getItem("user_id");
  if (!userId) {
    showLoginRequired();
    return false;
  }
  return true;
}

function showLoginRequired() {
  document.getElementById("loginRequiredMessage").style.display = "block";
  showQuickLogin();
}

async function offerRide() {
  const userId = localStorage.getItem("user_id");
  if (!userId) {
    alert("Musíte se přihlásit pro nabízení jízd");
    return;
  }

  const formData = {
    user_id: parseInt(userId),
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

async function showAllRides() {
  try {
    const response = await fetch("/api/rides/all");
    if (!response.ok) {
      alert("Chyba serveru: " + response.status);
      return;
    }
    const rides = await response.json();
    displayAllRides(rides);
  } catch (error) {
    alert("Chyba při načítání jízd: " + error.message);
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
      </div>
    `;
  });
  resultsContainer.innerHTML = html;
}

async function searchRides() {
  const from = document.getElementById("fromSearch").value;
  const to = document.getElementById("toSearch").value;

  try {
    const userId = localStorage.getItem("user_id") || "0";
    let url = `/api/rides/search-text?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&user_id=${userId}`;

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

});