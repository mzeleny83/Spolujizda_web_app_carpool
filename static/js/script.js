// Globální proměnné
let socket;
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

// Inicializace při načtení stránky
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeMap();
    setupEventListeners();
    initializePWA();
    checkUserLogin();
    setupFullscreenButton();
    
    // Zpoždění před vyžádáním notifikací
    setTimeout(() => {
        requestNotificationPermission();
    }, 2000);
    
    // Přizpůsobí mapu při změně velikosti okna
    window.addEventListener('resize', function() {
        if (map) {
            setTimeout(() => map.invalidateSize(), 100);
        }
        
        // Na mobilu skryj panel toggle
        const toggleBtn = document.getElementById('panelToggle');
        if (window.innerWidth <= 768) {
            toggleBtn.style.display = 'none';
        } else {
            toggleBtn.style.display = 'block';
        }
    });
});

// Nastavení fullscreen tlačítka
function setupFullscreenButton() {
    const fullscreenBtn = document.querySelector('.fullscreen-toggle');
    const mapContainer = document.querySelector('.map-container');
    
    function updateButtonPosition() {
        if (!fullscreenBtn || !mapContainer) return;
        
        const mapRect = mapContainer.getBoundingClientRect();
        
        // Pokud mapa končí nad spodem obrazovky, posun tlačítko nahoru
        let bottom = 20;
        
        if (mapRect.bottom < window.innerHeight - 20) {
            bottom = window.innerHeight - mapRect.bottom + 20;
        }
        
        fullscreenBtn.style.bottom = bottom + 'px';
    }
    
    window.addEventListener('scroll', updateButtonPosition);
    window.addEventListener('resize', updateButtonPosition);
    updateButtonPosition();
}

// Zkontroluje, zda je uživatel přihlášen
function checkUserLogin() {
    const userId = localStorage.getItem('user_id');
    const userName = localStorage.getItem('user_name');
    const userPhone = localStorage.getItem('user_phone');
    
    if (userId && userName && userPhone) {
        updateUIForLoggedInUser(userName);
    }
}

function updateUIForLoggedInUser(userName) {
    // Skryj přihlašovací tlačítka
    document.getElementById('loginButtons').style.display = 'none';
    
    // Zobraz welcome zprávu
    const welcomeMsg = document.getElementById('welcomeMessage');
    welcomeMsg.textContent = `Vítejte, ${userName}!`;
    welcomeMsg.style.display = 'block';
    
    // Zobraz tlačítko odhlášení
    document.getElementById('logoutButton').style.display = 'block';
}

function updateUIForLoggedOutUser() {
    // Zobraz přihlašovací tlačítka
    document.getElementById('loginButtons').style.display = 'block';
    
    // Skryj welcome zprávu
    document.getElementById('welcomeMessage').style.display = 'none';
    
    // Skryj tlačítko odhlášení
    document.getElementById('logoutButton').style.display = 'none';
}

// PWA inicializace
function initializePWA() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registrován:', registration);
            })
            .catch(error => {
                console.log('SW chyba:', error);
            });
    }
    
    // Install prompt
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
    });
}



// Instalace aplikace
function installApp() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('Aplikace nainstalována');
            }
            deferredPrompt = null;
        });
    }
}

// Požádá o povolení notifikací
function requestNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                console.log('Notifikace:', permission);
            }).catch(error => {
                console.error('Chyba notifikací:', error);
            });
        }
    }
}

// Pošle push notifikaci
function sendNotification(title, body) {
    if ('serviceWorker' in navigator && 'Notification' in window) {
        navigator.serviceWorker.ready.then(registration => {
            registration.showNotification(title, {
                body: body,
                icon: '/static/manifest.json',
                vibrate: [200, 100, 200]
            });
        });
    }
}

// SMS ověření
let verificationCode = null;

function sendVerificationSMS() {
    const phone = document.getElementById('regPhone').value;
    const name = document.getElementById('regName').value;
    const password = document.getElementById('regPassword').value;
    
    if (!name || !phone || !password) {
        return;
    }
    
    // Normalizuje telefonní číslo - odebere všechny mezery a speciální znaky
    let normalizedPhone = phone.replace(/[^0-9]/g, '');
    
    // Odstraní předvolbu
    if (normalizedPhone.startsWith('420')) {
        normalizedPhone = normalizedPhone.substring(3);
    }
    
    if (normalizedPhone.length !== 9) {
        alert('Zadejte platné české telefonní číslo (9 číslic)');
        return;
    }
    
    // Přímá registrace bez SMS
    fetch('/api/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: name,
            phone: normalizedPhone,
            password: password
        })
    }).then(response => response.json())
    .then(data => {
        if (data.message) {
            hideRegisterForm();
        }
    })
    .catch(error => {
        console.error('Chyba při registraci:', error);
    });
}

function verifyAndRegister() {
    // Tato funkce už není potřeba - registrace probíhá přímo
}

function showRegisterForm() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('registerSection').style.display = 'block';
    document.getElementById('loginSection2').style.display = 'none';
}

function showLoginForm() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('registerSection').style.display = 'none';
    document.getElementById('loginSection2').style.display = 'block';
}

function hideRegisterForm() {
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('registerSection').style.display = 'none';
    document.getElementById('verificationSection').style.display = 'none';
}

function backToLoginOptions() {
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('registerSection').style.display = 'none';
    document.getElementById('loginSection2').style.display = 'none';
}

function showQuickLogin() {
    document.getElementById('loginModal').style.display = 'block';
}

function showQuickRegister() {
    document.getElementById('registerModal').style.display = 'block';
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('loginRequiredMessage').style.display = 'none';
}

function closeRegisterModal() {
    document.getElementById('registerModal').style.display = 'none';
}

function showTermsModal() {
    document.getElementById('termsModal').style.display = 'block';
}

function closeTermsModal() {
    document.getElementById('termsModal').style.display = 'none';
}

function showPrivacyModal() {
    document.getElementById('privacyModal').style.display = 'block';
}

function closePrivacyModal() {
    document.getElementById('privacyModal').style.display = 'none';
}

// Validační funkce
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    field.classList.add('field-error');
    
    // Odstraň předchozí chybovou zprávu
    const existingError = field.parentNode.querySelector('.error-message');
    if (existingError) existingError.remove();
    
    // Přidej novou chybovou zprávu
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
    
    // Odstraň chybu po 5 sekundách
    setTimeout(() => {
        field.classList.remove('field-error');
        if (errorDiv.parentNode) errorDiv.remove();
    }, 5000);
}

function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    field.classList.remove('field-error');
    field.classList.add('field-success');
    
    const errorMsg = field.parentNode.querySelector('.error-message');
    if (errorMsg) errorMsg.remove();
    
    setTimeout(() => field.classList.remove('field-success'), 2000);
}

// Plánování trasy od aktuální polohy
function planRouteFromLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            // Reverse geocoding pro získání názvu místa
            try {
                const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
                const data = await response.json();
                const parts = data.display_name ? data.display_name.split(',') : [];
                const locationName = parts.length > 0 ? parts.slice(0, 3).join(', ').trim() : 'Aktuální poloha';
                
                // Vymaž předchozí trasu nejdřív
                clearRoute();
                
                // Vyplň pole "Odkud" AŽ PO vymažání
                document.getElementById('fromOffer').value = locationName;
                
                console.log(`GPS poloha: ${lat}, ${lng}, adresa: ${locationName}`);
                
                // Přidej výchozí bod
                routeWaypoints = [{ lat: lat, lng: lng, name: locationName }];
                
                // Vytvoř marker
                const marker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        html: '<div style="background: #28a745; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold;">1</div>',
                        iconSize: [25, 25],
                        iconAnchor: [12, 12]
                    }),
                    draggable: true
                }).addTo(map).bindPopup(`Start: ${locationName}`);
                
                routeMarkers = [marker];
                updateWaypointsList();
                
                // Spusť plánování
                isRoutePlanning = true;
                map.on('click', addWaypoint);
                map.setView([lat, lng], 15);
                
                
            } catch (error) {
                console.error('Reverse geocoding error:', error);
            }
        }, function(error) {
            console.error('GPS chyba:', error.message);
            document.getElementById('fromOffer').value = 'GPS nedostupné';
        }, {
            enableHighAccuracy: true,
            timeout: 30000,
            maximumAge: 0
        });
    } else {
        document.getElementById('fromOffer').value = 'GPS nepodporováno';
    }
}

// Ruční plánování trasy
function planRouteManual() {
    clearRoute();
    isRoutePlanning = true;
    map.on('click', addWaypoint);
}

function modalLoginUser() {
    const phone = document.getElementById('modalLoginPhone').value;
    const password = document.getElementById('modalLoginPassword').value;
    
    if (!phone || !password) {
        alert('Vyplňte všechna pole!');
        return;
    }
    
    // Normalizuje telefonní číslo
    let normalizedPhone = phone.replace(/[^0-9]/g, '');
    if (normalizedPhone.startsWith('420')) {
        normalizedPhone = normalizedPhone.substring(3);
    }
    const fullPhone = `+420${normalizedPhone}`;
    
    fetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: fullPhone, password: password })
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    }).then(data => {
        if (data.user_id) {
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_name', data.name);
            localStorage.setItem('user_phone', fullPhone);
            updateUIForLoggedInUser(data.name);
            closeLoginModal();
            document.getElementById('loginRequiredMessage').style.display = 'none';
        } else {
            showFieldError('modalLoginPassword', data.error || 'Nesprávné přihlašovací údaje');
        }
    })
    .catch(error => {
        console.error('Chyba při přihlášení:', error);
        showFieldError('modalLoginPassword', 'Chyba při přihlášení');
    });
}

function modalRegisterUser() {
    const phone = document.getElementById('modalRegPhone').value;
    const name = document.getElementById('modalRegName').value;
    const email = document.getElementById('modalRegEmail').value;
    const password = document.getElementById('modalRegPassword').value;
    const passwordConfirm = document.getElementById('modalRegPasswordConfirm').value;
    
    const agreeTerms = document.getElementById('modalRegTerms').checked;
    const agreePrivacy = document.getElementById('modalRegPrivacy').checked;
    const agreeAge = document.getElementById('modalRegAge').checked;
    
    // Validace polí s vizualizací
    let hasError = false;
    
    if (!name) {
        showFieldError('modalRegName', 'Jméno je povinné');
        hasError = true;
    }
    if (!phone) {
        showFieldError('modalRegPhone', 'Telefon je povinný');
        hasError = true;
    }
    if (!password) {
        showFieldError('modalRegPassword', 'Heslo je povinné');
        hasError = true;
    }
    if (!passwordConfirm) {
        showFieldError('modalRegPasswordConfirm', 'Potvrzení hesla je povinné');
        hasError = true;
    }
    
    if (hasError) return;
    
    if (!agreeTerms) {
        showFieldError('modalRegTerms', 'Musíte souhlasit s podmínkami');
        hasError = true;
    }
    if (!agreePrivacy) {
        showFieldError('modalRegPrivacy', 'Musíte souhlasit se zpracováním údajů');
        hasError = true;
    }
    if (!agreeAge) {
        showFieldError('modalRegAge', 'Musíte potvrdit věk 18+');
        hasError = true;
    }
    
    if (hasError) return;
    
    if (password !== passwordConfirm) {
        alert('Hesla se neshodují!');
        return;
    }
    
    let normalizedPhone = phone.replace(/[^0-9]/g, '');
    if (normalizedPhone.startsWith('420')) {
        normalizedPhone = normalizedPhone.substring(3);
    }
    
    if (normalizedPhone.length !== 9) {
        alert('Zadejte platné české telefonní číslo (9 číslic)');
        return;
    }
    
    fetch('/api/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: name,
            phone: `+420${normalizedPhone}`,
            email: email,
            password: password,
            password_confirm: passwordConfirm
        })
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    }).then(data => {
        if (data.message) {
            closeRegisterModal();
            showQuickLogin();
        }
    })
    .catch(error => {
        console.error('Chyba při registraci:', error);
    });
}

function loginUser() {
    const phone = document.getElementById('loginPhone').value;
    const password = document.getElementById('loginPassword').value;
    
    fetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: phone, password: password })
    }).then(response => response.json())
    .then(data => {
        if (data.user_id) {
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_name', data.name);
            localStorage.setItem('user_phone', phone);
            showUserProfile(data.name, phone);
        }
    });
}

function showUserProfile(name, phone) {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('loginSection2').style.display = 'none';
    document.getElementById('userProfile').style.display = 'block';
    document.getElementById('userNameProfile').textContent = `Jméno: ${name}`;
    document.getElementById('userPhoneProfile').textContent = `Telefon: ${phone}`;
    
    // Načte skutečné hodnocení
    const userId = localStorage.getItem('user_id');
    if (userId) {
        fetch(`/api/users/${userId}/stats`)
        .then(response => response.json())
        .then(data => {
            // Simulace hodnocení - v reálu by se načetlo z databáze
            document.getElementById('userRatingProfile').textContent = `Hodnocení: ⭐️⭐️⭐️⭐️⭐️ (5.0)`;
        })
        .catch(() => {
            document.getElementById('userRatingProfile').textContent = `Hodnocení: Nový uživatel`;
        });
    }
}

function logoutUser() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_phone');
    updateUIForLoggedOutUser();
}

function updateInstallButton() {
    const installBtn = document.getElementById('installAppBtn');
    const installStatus = document.getElementById('installStatus');
    
    if (deferredPrompt) {
        installBtn.style.display = 'block';
        installStatus.textContent = 'Aplikace je připravena k instalaci';
    } else {
        installBtn.style.display = 'none';
        installStatus.textContent = 'Aplikace je již nainstalována nebo není podporována';
    }
}

function enableNotifications() {
    requestNotificationPermission();
    setTimeout(updateNotificationStatus, 1000);
}

function updateNotificationStatus() {
    const status = document.getElementById('notificationStatus');
    if ('Notification' in window) {
        if (Notification.permission === 'granted') {
            status.textContent = 'Stav notifikací: ✅ Povoleny';
        } else if (Notification.permission === 'denied') {
            status.textContent = 'Stav notifikací: ❌ Zakázány';
        } else {
            status.textContent = 'Stav notifikací: ⏳ Čeká na povolení';
        }
    } else {
        status.textContent = 'Stav notifikací: Nepodporovány';
    }
}

// Inicializace SocketIO
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        document.getElementById('connectionStatus').textContent = 'Připojeno';
        document.getElementById('connectionStatus').className = 'connected';
    });
    
    socket.on('disconnect', function() {
        document.getElementById('connectionStatus').textContent = 'Odpojeno';
        document.getElementById('connectionStatus').className = 'disconnected';
    });
    
    socket.on('location_updated', function(data) {
        updateUserMarker(data.user_id, data.lat, data.lng);
    });
    
    // Chat event listenery
    socket.on('user_joined', (data) => {
        addChatMessage('Systém', data.message, data.timestamp, true);
    });
    
    socket.on('user_left', (data) => {
        addChatMessage('Systém', data.message, data.timestamp, true);
    });
    
    socket.on('new_chat_message', (data) => {
        addChatMessage(data.user_name, data.message, data.timestamp);
    });
    
    socket.on('live_location_update', (data) => {
        addChatMessage('Poloha', `📍 ${data.user_name} sdílí svou polohu: ${data.lat.toFixed(4)}, ${data.lng.toFixed(4)}`, data.timestamp, true);
        
        if (map && typeof L !== 'undefined') {
            const marker = L.marker([data.lat, data.lng], {
                icon: L.divIcon({
                    html: `<div style="background: #28a745; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-size: 12px;">📍</div>`,
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                })
            }).addTo(map).bindPopup(`📍 ${data.user_name} - ${new Date(data.timestamp).toLocaleTimeString('cs-CZ')}`);
            
            setTimeout(() => {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            }, 300000);
        }
    });
    
    socket.on('direct_message_received', (data) => {
        if (currentDirectChat === data.from_user) {
            addChatMessage(data.from_user, data.message, data.timestamp);
        } else {
            sendNotification(`Nová zpráva od ${data.from_user}`, data.message);
        }
    });
    
    socket.on('user_location_response', (data) => {
        if (data.lat && data.lng) {
            map.setView([data.lat, data.lng], 15);
            
            const tempMarker = L.marker([data.lat, data.lng], {
                icon: L.divIcon({
                    html: `<div style="background: #ffc107; color: black; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold;">📍</div>`,
                    iconSize: [25, 25],
                    iconAnchor: [12, 12]
                })
            }).addTo(map).bindPopup(`📍 Poloha uživatele ${data.user_name}`);
            
            setTimeout(() => {
                if (map.hasLayer(tempMarker)) {
                    map.removeLayer(tempMarker);
                }
            }, 30000);
            
            alert(`📍 Poloha uživatele ${data.user_name} zobrazena na mapě`);
        } else {
            alert(`⚠️ Uživatel ${data.user_name} nesdilí svou polohu`);
        }
    });
}

// Inicializace mapy s Leaflet (OpenStreetMap)
function initializeMap() {
    const mapContainer = document.getElementById('map');
    
    try {
        // Inicializace Leaflet mapy
        map = L.map('map', {
            zoomControl: true,
            scrollWheelZoom: true,
            doubleClickZoom: true,
            touchZoom: true,
            dragging: true,
            zoomSnap: 0.25,
            zoomDelta: 0.25,
            wheelPxPerZoomLevel: 120
        }).setView([50.0755, 14.4378], 13);
        
        // Vrstvy map
        const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        });
        
        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles © Esri',
            maxZoom: 19
        });
        
        const terrainLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap',
            maxZoom: 17
        });
        
        // Přidá výchozí vrstvu
        osmLayer.addTo(map);
        
        // Ovládání vrstev
        const baseLayers = {
            '🗺️ Mapa': osmLayer,
            '🛰️ Satelit': satelliteLayer,
            '🏔️ Terén': terrainLayer
        };
        
        L.control.layers(baseLayers).addTo(map);
        
        console.log('Mapa úspěšně inicializována');
    } catch (error) {
        console.error('Chyba při inicializaci mapy:', error);
    }
}

// Nastavení event listenerů
function setupEventListeners() {
    document.getElementById('rideOfferForm').addEventListener('submit', function(e) {
        e.preventDefault();
        offerRide();
    });
    
    document.getElementById('rideSearchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        searchRides();
    });
    
    document.getElementById('recurringRideForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createRecurringRide();
    });
}

// Toggle sledování polohy
function toggleTracking() {
    if (!checkLoginRequired()) return;
    
    if (isTracking) {
        stopTracking();
    } else {
        startTracking();
    }
}

// Začít sledování polohy a vycentrování
function startTracking() {
    const userId = localStorage.getItem('user_id');
    const userName = localStorage.getItem('user_name');
    
    if (!userId || !userName) {
        return;
    }
    
    currentUserId = userName;
    
    if (navigator.geolocation) {
        // Nejdříve získá přesnou polohu
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                // Kontrola přesnosti před využitím
                const accuracy = position.coords.accuracy;
                console.log(`GPS přesnost: ${accuracy}m na pozici ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
                
                // Použije pozici i při nižší přesnosti
                
                // Vycentruje mapu jen při prvním spuštění
                map.setView([lat, lng], 16);
                updateOwnLocation(lat, lng);
                
                // Spustí kontinuelní sledování
                watchId = navigator.geolocation.watchPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        
                        socket.emit('update_location', {
                            user_id: currentUserId,
                            lat: lat,
                            lng: lng
                        });
                        
                        // Kontrola přesnosti GPS
                        const accuracy = position.coords.accuracy;
                        console.log(`GPS aktualizace: přesnost ${accuracy}m`);
                        
                        // Kontrola rozumné vzdálenosti od poslední pozice
                        if (userMarker) {
                            const lastPos = userMarker.getLatLng();
                            const distance = map.distance([lat, lng], [lastPos.lat, lastPos.lng]);
                            
                            // Pokud je vzdálenost větší než 10km za 30s, pravděpodobně chyba
                            if (distance > 10000) {
                                console.warn(`Podezrělý skok v pozici: ${distance}m - ignoruji`);
                                return;
                            }
                        }
                        
                        updateOwnLocation(lat, lng);
                        
                        // Necentruj mapu automaticky - nech uživatele prohlížet
                        
                        document.getElementById('coordsText').textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                        document.getElementById('gpsCoords').style.display = 'block';
                    },
                    function(error) {
                        console.error('Chyba při sledování:', error);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
                
                isTracking = true;
                const btn = document.getElementById('trackingBtn');
                btn.innerHTML = '⏹️ Zastavit sledování';
                btn.title = 'Zastaví sledování GPS polohy';
            },
            function(error) {
                console.error('Chyba při získávání polohy:', error);
                document.getElementById('gpsCoords').style.display = 'none';
            },
            {
                enableHighAccuracy: false,
                timeout: 15000,
                maximumAge: 300000
            }
        );
    }
}

// Zastavit sledování polohy
function stopTracking() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
    document.getElementById('gpsCoords').style.display = 'none';
    isTracking = false;
    
    // Změní tlačítko zpět
    const btn = document.getElementById('trackingBtn');
    btn.innerHTML = '📍 Najít mě a sledovat';
    btn.title = 'Spustí sledování vaší GPS polohy a vycentruje mapu na vaši pozici';
}

// Přepínání levého panelu
function togglePanel() {
    const leftColumn = document.querySelector('.left-column');
    const toggleBtn = document.getElementById('panelToggle');
    
    // Na mobilu nepoužívat toggle
    if (window.innerWidth <= 768) {
        return;
    }
    
    // Pokud je fullscreen aktivní, zruš ho a zobraz menu
    if (isFullscreen) {
        const mapContainer = document.querySelector('.map-container');
        const fullscreenToggleBtn = document.querySelector('.fullscreen-toggle');
        
        mapContainer.classList.remove('map-fullscreen');
        fullscreenToggleBtn.innerHTML = '⛶';
        fullscreenToggleBtn.title = 'Celá obrazovka';
        isFullscreen = false;
        wasMenuHiddenBeforeFullscreen = false; // Reset stavu
        
        leftColumn.classList.remove('hidden');
        toggleBtn.innerHTML = '◀';
        toggleBtn.title = 'Skrýt menu';
    } else {
        // Normální toggle - přepínání mezi zobrazením a skrytím
        if (leftColumn.classList.contains('hidden')) {
            leftColumn.classList.remove('hidden');
            toggleBtn.innerHTML = '◀';
            toggleBtn.title = 'Skrýt menu';
        } else {
            leftColumn.classList.add('hidden');
            toggleBtn.innerHTML = '▶';
            toggleBtn.title = 'Zobrazit menu';
        }
    }
    
    // Přizpůsobí velikost mapy
    setTimeout(() => {
        if (map) {
            map.invalidateSize();
        }
    }, 300);
}

// Fullscreen mapa
let isFullscreen = false;
let wasMenuHiddenBeforeFullscreen = false;

function toggleFullscreen() {
    const mapContainer = document.querySelector('.map-container');
    const toggleBtn = document.querySelector('.fullscreen-toggle');
    const leftColumn = document.querySelector('.left-column');
    const panelToggleBtn = document.getElementById('panelToggle');
    
    if (!isFullscreen) {
        // Zapamatuj si stav menu před fullscreen
        wasMenuHiddenBeforeFullscreen = leftColumn.classList.contains('hidden');
        
        mapContainer.classList.add('map-fullscreen');
        toggleBtn.innerHTML = '✖';
        toggleBtn.title = 'Zavřít fullscreen';
        toggleBtn.style.display = 'block';
        isFullscreen = true;
        
        // Při fullscreen vždy skryj menu a nastav správnou ikonu
        leftColumn.classList.add('hidden');
        panelToggleBtn.innerHTML = '☰';
        panelToggleBtn.title = 'Zobrazit menu';
    } else {
        mapContainer.classList.remove('map-fullscreen');
        toggleBtn.innerHTML = '⛶';
        toggleBtn.title = 'Celá obrazovka';
        isFullscreen = false;
        
        // Obnov stav menu podle toho, jak bylo před fullscreen
        if (!wasMenuHiddenBeforeFullscreen) {
            leftColumn.classList.remove('hidden');
            panelToggleBtn.innerHTML = '◀';
            panelToggleBtn.title = 'Skrýt menu';
        }
    }
    
    // Přizpůsobí velikost mapy
    setTimeout(() => {
        if (map) {
            map.invalidateSize();
        }
    }, 300);
}

// ESC klávesa pro zavření fullscreen
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isFullscreen) {
        toggleFullscreen();
    }
});

// Aktualizovat vlastní pozici na mapě
function updateOwnLocation(lat, lng) {
    if (map && typeof L !== 'undefined') {
        if (userMarker) {
            userMarker.setLatLng([lat, lng]);
        } else {
            const userIcon = L.divIcon({
                html: '<div style="background: #4285f4; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
                iconSize: [26, 26],
                iconAnchor: [13, 13],
                className: 'user-marker'
            });
            
            const userName = localStorage.getItem('user_name') || 'Vy';
            const popupContent = `
                <div style="text-align: center; min-width: 150px;">
                    <h4>📍 ${userName}</h4>
                    <p>Vaše aktuální poloha</p>
                    <button onclick="openDirectChat('${userName}')" style="background: #667eea; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin: 2px;">💬 Můj chat</button>
                </div>
            `;
            
            userMarker = L.marker([lat, lng], { icon: userIcon })
                .addTo(map)
                .bindPopup(popupContent);
        }
    }
}

// Aktualizovat marker jiného uživatele
function updateUserMarker(userId, lat, lng) {
    if (map && typeof L !== 'undefined') {
        if (userMarkers[userId]) {
            userMarkers[userId].setLatLng([lat, lng]);
        } else {
            const otherUserIcon = L.divIcon({
                html: '<div style="background: #ea4335; width: 18px; height: 18px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 10px;">🚗</div>',
                iconSize: [22, 22],
                iconAnchor: [11, 11],
                className: 'other-user-marker'
            });
            
            const popupContent = `
                <div style="text-align: center; min-width: 150px;">
                    <h4>🚗 ${userId}</h4>
                    <button onclick="openDirectChat('${userId}')" style="background: #667eea; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin: 5px;">💬 Chat</button>
                    <button onclick="getUserLocation('${userId}')" style="background: #28a745; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin: 5px;">📍 Poloha</button>
                </div>
            `;
            
            userMarkers[userId] = L.marker([lat, lng], { icon: otherUserIcon })
                .addTo(map)
                .bindPopup(popupContent);
        }
    }
}

// Toggle funkce pro formuláře
function toggleOfferForm() {
    if (!checkLoginRequired()) return;
    
    const form = document.getElementById('offerForm');
    if (form.style.display === 'block') {
        form.style.display = 'none';
    } else {
        hideAllForms();
        form.style.display = 'block';
    }
}

function toggleSearchForm() {
    const form = document.getElementById('searchForm');
    if (form.style.display === 'block') {
        form.style.display = 'none';
        document.getElementById('results').innerHTML = '';
    } else {
        hideAllForms();
        form.style.display = 'block';
        updateSliderBackground('searchRange', 10, 1, 100);
        showAllRides();
    }
}

function toggleActiveRides() {
    const form = document.getElementById('activeRides');
    if (form.style.display === 'block') {
        form.style.display = 'none';
    } else {
        hideAllForms();
        form.style.display = 'block';
    }
}

function toggleSettings() {
    const form = document.getElementById('settingsForm');
    if (form.style.display === 'block') {
        form.style.display = 'none';
    } else {
        hideAllForms();
        form.style.display = 'block';
        updateInstallButton();
        updateNotificationStatus();
        loadUserStats();
    }
}

function toggleUserSearch() {
    const form = document.getElementById('userSearchForm');
    if (form.style.display === 'block') {
        form.style.display = 'none';
    } else {
        hideAllForms();
        form.style.display = 'block';
    }
}

function toggleRecurringForm() {
    if (!checkLoginRequired()) return;
    
    const form = document.getElementById('recurringForm');
    if (form.style.display === 'block') {
        form.style.display = 'none';
    } else {
        hideAllForms();
        form.style.display = 'block';
        loadRecurringRides();
    }
}

// Staré funkce pro zpětnou kompatibilitu
function showOfferForm() { toggleOfferForm(); }
function showSearchForm() { toggleSearchForm(); }
function showActiveRides() { toggleActiveRides(); }
function showSettings() { toggleSettings(); }
function showRecurringForm() { toggleRecurringForm(); }

// Skrýt všechny formuláře
function hideAllForms() {
    document.getElementById('offerForm').style.display = 'none';
    document.getElementById('searchForm').style.display = 'none';
    document.getElementById('userSearchForm').style.display = 'none';
    document.getElementById('recurringForm').style.display = 'none';
    document.getElementById('activeRides').style.display = 'none';
    document.getElementById('settingsForm').style.display = 'none';
    document.getElementById('results').innerHTML = '';
}

// Plánování trasy
function planRoute() {
    if (!map) {
        alert('Mapa není dostupná');
        return;
    }
    
    // Získá zadané lokace z formuláře
    const fromLocation = document.getElementById('fromOffer').value;
    const toLocation = document.getElementById('toOffer').value;
    
    if (!fromLocation || !toLocation) {
        alert('Nejdříve zadejte odkud a kam jedete!');
        return;
    }
    
    // Vymazání předchozích tras a markerů
    clearRoute();
    
    isRoutePlanning = true;
    
    alert('🗺️ Klikejte na mapu pro přidání zastávek na trase!');
    
    map.on('click', addWaypoint);
}

async function addWaypoint(e) {
    if (!isRoutePlanning) return;
    
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    // Získá název místa
    let locationName = `Zastávka ${routeWaypoints.length + 1}`;
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
        const data = await response.json();
        if (data && data.display_name) {
            const parts = data.display_name.split(',');
            // Vezme první 3 části (ulice, číslo, město)
            locationName = parts.slice(0, 3).join(', ').trim();
        }
    } catch (error) {
        console.error('Reverse geocoding error:', error);
    }
    
    // Přidá nový waypoint
    routeWaypoints.push({ lat: lat, lng: lng, name: locationName });
    
    // Vyplň pole v menu
    if (routeWaypoints.length === 1) {
        document.getElementById('fromOffer').value = locationName;
    } else if (routeWaypoints.length === 2) {
        document.getElementById('toOffer').value = locationName;
    }
    
    // Vymazání všech předchozích markerů
    routeMarkers.forEach(marker => {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        }
    });
    routeMarkers = [];
    
    // Vytvoření nových markerů pro celou trasu
    routeWaypoints.forEach((wp, index) => {
        const marker = L.marker([wp.lat, wp.lng], {
            icon: L.divIcon({
                html: `<div style="background: #ff6b35; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold;">${index + 1}</div>`,
                iconSize: [25, 25],
                iconAnchor: [12, 12]
            }),
            draggable: true
        }).addTo(map);
        
        // Přidání event listeneru pro přetahování
        marker.on('dragend', async function(e) {
            const newPos = e.target.getLatLng();
            routeWaypoints[index].lat = newPos.lat;
            routeWaypoints[index].lng = newPos.lng;
            
            // Získá nový název místa
            try {
                const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${newPos.lat}&lon=${newPos.lng}`);
                const data = await response.json();
                if (data && data.display_name) {
                    const parts = data.display_name.split(',');
                    routeWaypoints[index].name = parts.slice(0, 3).join(', ').trim();
                    
                    // Aktualizuj pole v menu
                    if (index === 0) {
                        document.getElementById('fromOffer').value = routeWaypoints[index].name;
                    } else if (index === 1) {
                        document.getElementById('toOffer').value = routeWaypoints[index].name;
                    }
                }
            } catch (error) {
                console.error('Reverse geocoding error:', error);
                routeWaypoints[index].name = `Zastávka ${index + 1}`;
            }
            
            updateWaypointsList();
            drawRoute();
        });
        
        // Mazání bodu - dvojité poklepní (mobil) a pravé tlačítko (PC)
        marker.on('dblclick', function(e) {
            e.originalEvent.stopPropagation();
            removeWaypointByIndex(index);
        });
        
        marker.on('contextmenu', function(e) {
            e.originalEvent.preventDefault();
            removeWaypointByIndex(index);
        });
        
        routeMarkers.push(marker);
    });
    
    updateWaypointsList();
    drawRoute();
}

function updateWaypointsList() {
    const container = document.getElementById('routeWaypoints');
    let html = '<h4>Trasa:</h4>';
    
    routeWaypoints.forEach((wp, index) => {
        html += `<div style="margin: 5px 0; padding: 5px; background: #f0f0f0; border-radius: 5px;">
            ${index + 1}. ${wp.name} 
            <button type="button" onclick="removeWaypoint(${index})" style="background: #dc3545; color: white; border: none; padding: 2px 8px; border-radius: 3px; margin-left: 10px;" title="Odebere tuto zastávku z naplánované trasy">X</button>
        </div>`;
    });
    
    // Tlačítko dokončit plánování se už nepoužívá - sloučeno s nabídnout jízdu
    
    container.innerHTML = html;
}

function removeWaypoint(index) {
    routeWaypoints.splice(index, 1);
    
    if (routeMarkers[index]) {
        map.removeLayer(routeMarkers[index]);
        routeMarkers.splice(index, 1);
    }
    
    // Pokud nejsou žádné body, vymazání trasy
    if (routeWaypoints.length === 0) {
        clearRoute();
        return;
    }
    
    updateWaypointsList();
    drawRoute();
}

// Nová funkce pro mazání bodu a překresleni celé trasy
function removeWaypointByIndex(index) {
    routeWaypoints.splice(index, 1);
    
    // Pokud nejsou žádné body, vymazání celé trasy
    if (routeWaypoints.length === 0) {
        clearRoute();
        return;
    }
    
    redrawAllWaypoints();
}

// Najde nejbližší segment trasy pro vložení nového bodu
function findNearestSegment(clickPoint, waypoints) {
    let minDistance = Infinity;
    let nearestIndex = 0;
    
    for (let i = 0; i < waypoints.length - 1; i++) {
        const segmentStart = L.latLng(waypoints[i].lat, waypoints[i].lng);
        const segmentEnd = L.latLng(waypoints[i + 1].lat, waypoints[i + 1].lng);
        
        const segmentCenter = L.latLng(
            (segmentStart.lat + segmentEnd.lat) / 2,
            (segmentStart.lng + segmentEnd.lng) / 2
        );
        
        const distance = clickPoint.distanceTo(segmentCenter);
        
        if (distance < minDistance) {
            minDistance = distance;
            nearestIndex = i;
        }
    }
    
    return nearestIndex;
}

// Překreslí všechny waypointy s novým číslovaním
function redrawAllWaypoints() {
    routeMarkers.forEach(marker => {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        }
    });
    routeMarkers = [];
    
    routeWaypoints.forEach((wp, index) => {
        const marker = L.marker([wp.lat, wp.lng], {
            icon: L.divIcon({
                html: `<div style="background: #ff6b35; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold;">${index + 1}</div>`,
                iconSize: [25, 25],
                iconAnchor: [12, 12]
            }),
            draggable: true
        }).addTo(map);
        
        marker.on('dragend', function(e) {
            const newPos = e.target.getLatLng();
            routeWaypoints[index].lat = newPos.lat;
            routeWaypoints[index].lng = newPos.lng;
            routeWaypoints[index].name = `Zastávka ${index + 1}`;
            updateWaypointsList();
            drawRoute();
        });
        
        marker.on('dblclick', function(e) {
            e.originalEvent.stopPropagation();
            removeWaypointByIndex(index);
        });
        
        marker.on('contextmenu', function(e) {
            e.originalEvent.preventDefault();
            removeWaypointByIndex(index);
        });
        
        routeMarkers.push(marker);
    });
    
    updateWaypointsList();
    drawRoute();
}

async function drawRoute() {
    // Vymazání předchozí trasy
    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }
    
    if (routeWaypoints.length > 1) {
        // Použije OSRM API pro routing podle silnic
        try {
            const coords = routeWaypoints.map(wp => `${wp.lng},${wp.lat}`).join(';');
            const response = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
            const data = await response.json();
            
            if (data.routes && data.routes[0]) {
                const route = data.routes[0].geometry.coordinates;
                const latlngs = route.map(coord => [coord[1], coord[0]]);
                routeLine = L.polyline(latlngs, { 
                    color: '#007bff', 
                    weight: 4,
                    opacity: 0.8
                }).addTo(map);
                
                // Přidání možnosti přetahování trasy
                routeLine.on('click', function(e) {
                    if (!isRoutePlanning) return;
                    
                    const clickedPoint = e.latlng;
                    
                    // Najdi nejbližší segment trasy
                    let insertIndex = findNearestSegment(clickedPoint, routeWaypoints);
                    
                    // Vlož nový waypoint na kliknuté místo
                    routeWaypoints.splice(insertIndex + 1, 0, {
                        lat: clickedPoint.lat,
                        lng: clickedPoint.lng,
                        name: `Zastávka ${insertIndex + 2}`
                    });
                    
                    // Překresleni celé trasy
                    redrawAllWaypoints();
                });
            }
        } catch (error) {
            console.error('OSRM routing failed:', error);
            // Fallback - přímá čára mezi body
            const latlngs = routeWaypoints.map(wp => [wp.lat, wp.lng]);
            routeLine = L.polyline(latlngs, { 
                color: '#dc3545', 
                weight: 3,
                dashArray: '5, 10',
                opacity: 0.7
            }).addTo(map);
        }
    }
}

function finishRoutePlanning() {
    isRoutePlanning = false;
    map.off('click', addWaypoint);
}

// Nabídnout jízdu
async function offerRide() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        showFieldError('fromOffer', 'Musíte se přihlásit pro nabízení jízd');
        return;
    }
    
    // Automaticky ukončí plánování pokud probíhá
    if (isRoutePlanning) {
        finishRoutePlanning();
    }
    
    const formData = {
        user_id: parseInt(userId),
        from_location: document.getElementById('fromOffer').value,
        to_location: document.getElementById('toOffer').value,
        departure_time: document.getElementById('departureOffer').value,
        available_seats: parseInt(document.getElementById('seatsOffer').value),
        price_per_person: parseInt(document.getElementById('priceOffer').value),
        route_waypoints: routeWaypoints
    };
    
    try {
        const response = await fetch('/api/rides/offer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Zobrazí úspěch bez alertu
            const submitBtn = document.querySelector('#rideOfferForm button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = '✅ Jízda nabídnuta!';
            submitBtn.style.background = '#28a745';
            setTimeout(() => {
                submitBtn.textContent = originalText;
                submitBtn.style.background = '';
            }, 3000);
            
            sendNotification('Nová jízda!', 'Vaše jízda byla úspěšně nabídnuta');
            
            // Uloží data jízdy pro možnost úprav
            const rideData = {
                from_location: document.getElementById('fromOffer').value,
                to_location: document.getElementById('toOffer').value,
                departure_time: document.getElementById('departureOffer').value,
                available_seats: document.getElementById('seatsOffer').value,
                price_per_person: document.getElementById('priceOffer').value,
                route_waypoints: routeWaypoints
            };
            localStorage.setItem('last_offered_ride', JSON.stringify(rideData));
            
            // Zobrazí možnost úprav
            document.getElementById('editRideOption').style.display = 'block';
            
            document.getElementById('rideOfferForm').reset();
            clearRoute();
        } else {
            showFieldError('fromOffer', 'Chyba: ' + result.error);
        }
    } catch (error) {
        showFieldError('fromOffer', 'Chyba při odesílání: ' + error.message);
    }
}

// Aktualizace hodnoty rozsahu
function updateRangeValue(value) {
    document.getElementById('rangeValue').textContent = value;
    updateSliderBackground('searchRange', value, 1, 100);
}

// Aktualizace hodnoty hodnocení
function updateRatingValue(value) {
    const rating = parseFloat(value);
    document.getElementById('ratingValue').textContent = rating === 0 ? '0' : rating.toFixed(1);
    updateSliderBackground('minRating', value, 0, 5);
}

// Kontrola přihlášení
function checkLoginRequired() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        showLoginRequired();
        return false;
    }
    return true;
}

// Zobrazí přihlášení s informativní zprávou
function showLoginRequired() {
    document.getElementById('loginRequiredMessage').style.display = 'block';
    showQuickLogin();
}

// Přepíná viditelnost hesla
function togglePasswordVisibility(inputId, button) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        button.textContent = '👁️';
    } else {
        input.type = 'password';
        button.textContent = '👁️';
    }
}

// Aktualizuje pozadí posuvníku s modrou čárou
function updateSliderBackground(sliderId, value, min, max) {
    const slider = document.getElementById(sliderId);
    const percentage = ((value - min) / (max - min)) * 100;
    slider.style.background = `linear-gradient(to right, #667eea 0%, #667eea ${percentage}%, #ddd ${percentage}%, #ddd 100%)`;
}

// Automatické hledání všech jízd kolem uživatele
async function autoSearchAllRides() {
    const resultsDiv = document.getElementById('results');
    if (!resultsDiv) return;
    
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        showAllRides();
        return;
    }
    
    if (!navigator.geolocation) {
        resultsDiv.innerHTML = '<p>GPS není podporováno.</p>';
        return;
    }
    
    resultsDiv.innerHTML = '<p>Získávám vaši polohu...</p>';
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            const accuracy = position.coords.accuracy;
            
            console.log(`GPS: ${latitude}, ${longitude}, přesnost: ±${accuracy}m`);
            resultsDiv.innerHTML = '<h3>Nalezené jízdy:</h3><p>Hledám...</p>';
            
            map.setView([latitude, longitude], 12);
            
            try {
                const userId = localStorage.getItem('user_id') || '0';
                const searchRange = document.getElementById('searchRange').value;
                const minRating = 0;
                
                let foundRides = [];
                const maxRange = parseInt(searchRange);
                const steps = [5, 15, maxRange]; // Rychlejší kroky
                
                for (let step of steps) {
                    if (step > maxRange) step = maxRange;
                    
                    try {
                        const response = await fetch(`/api/rides/search?from=&to=&lat=${latitude}&lng=${longitude}&user_id=${userId}&range=${step}&include_own=true`);
                        
                        if (!response.ok) {
                            console.error(`HTTP chyba: ${response.status}`);
                            continue;
                        }
                        
                        const rides = await response.json();
                        
                        if (rides && Array.isArray(rides) && rides.length > 0) {
                            rides.forEach(ride => {
                                if (!foundRides.find(r => r.id === ride.id)) {
                                    foundRides.push(ride);
                                }
                            });
                            
                            // Zobraz okamžitě každou nalezenou jízdu
                            displayAllRides(foundRides);
                            addRideMarkersToMap(foundRides);
                            
                            // Ukončí hledání po prvních nalezených jízdách
                            if (foundRides.length >= 5) {
                                break;
                            }
                        }
                    } catch (error) {
                        console.error(`Chyba při hledání v okruhu ${step} km:`, error);
                    }
                    
                    if (step >= maxRange) break;
                    // Krátká pauza jen pokud není dost jízd
                    if (foundRides.length < 3) {
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                }
                
                if (foundRides.length === 0) {
                    resultsDiv.innerHTML = '<p>Ve vašem okolí nejsou žádné dostupné jízdy.</p>';
                }
            } catch (error) {
                console.error('Chyba při hledání jízd:', error);
                resultsDiv.innerHTML = `<p>Chyba při načítání jízd: ${error.message}</p>`;
            }
        },
        (error) => {
            console.error('GPS chyba:', error.message);
            resultsDiv.innerHTML = 'Nepodařilo se získat polohu: ' + error.message;
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Zobrazí všechny jízdy bez GPS
async function showAllRides() {
    const resultsDiv = document.getElementById('results');
    if (!resultsDiv) return;
    
    resultsDiv.innerHTML = '<h3>Všechny dostupné jízdy:</h3><p>Načítám...</p>';
    
    try {
        const userId = localStorage.getItem('user_id') || '0';
        const response = await fetch(`/api/rides/search?from=&to=&lat=0&lng=0&user_id=${userId}&range=1000&include_own=true`);
        
        if (!response.ok) {
            throw new Error(`HTTP chyba: ${response.status}`);
        }
        
        const rides = await response.json();
        displayAllRides(rides);
        addRideMarkersToMap(rides);
        
    } catch (error) {
        console.error('Chyba při načítání jízd:', error);
        resultsDiv.innerHTML = `<p>Chyba při načítání jízd: ${error.message}</p>`;
    }
}

// Zobrazí všechny jízdy v okolí
function displayAllRides(rides) {
    const resultsContainer = document.getElementById('results');
    
    if (!Array.isArray(rides)) {
        resultsContainer.innerHTML = '<p>Chyba: Neplatná data z serveru</p>';
        return;
    }
    
    if (rides.length === 0) {
        resultsContainer.innerHTML = '<p>Ve vašem okolí nejsou žádné dostupné jízdy.</p>';
        return;
    }
    
    let html = `<h3>Dostupné jízdy ve vašem okolí (${rides.length}):</h3>`;
    rides.forEach(ride => {
        const distanceText = ride.distance > 0 ? ` - ${ride.distance} km` : '';
        const ratingStars = '⭐'.repeat(Math.floor(ride.driver_rating));
        
        // Určení barvy a textu podle typu jízdy
        let backgroundColor = '#f9f9f9';
        let borderColor = '#ddd';
        let statusText = '';
        let buttons = `
            <button onclick="showRideRoute(${ride.id}, ${JSON.stringify(ride.route_waypoints).replace(/"/g, '&quot;')})" style="background: #28a745; color: white; padding: 3px 8px; border: none; border-radius: 3px; font-size: 10px;">Trasa</button>
            <button onclick="reserveSeat(${ride.id}, '${ride.driver_name}')" style="background: #007bff; color: white; padding: 3px 8px; border: none; border-radius: 3px; font-size: 10px;">Rezervovat</button>
        `;
        
        if (ride.is_own) {
            backgroundColor = '#d4edda';
            borderColor = '#28a745';
            statusText = '<span style="color: #28a745; font-weight: bold; font-size: 11px;">✓ Vaše jízda</span>';
            buttons = `<button onclick="showRideRoute(${ride.id}, ${JSON.stringify(ride.route_waypoints).replace(/"/g, '&quot;')})" style="background: #28a745; color: white; padding: 3px 8px; border: none; border-radius: 3px; font-size: 10px;">Trasa</button>`;
        } else if (ride.is_reserved) {
            backgroundColor = '#cce7ff';
            borderColor = '#007bff';
            statusText = '<span style="color: #007bff; font-weight: bold; font-size: 11px;">✓ Jedu s touto jízdou</span>';
            buttons = `<button onclick="showRideRoute(${ride.id}, ${JSON.stringify(ride.route_waypoints).replace(/"/g, '&quot;')})" style="background: #007bff; color: white; padding: 3px 8px; border: none; border-radius: 3px; font-size: 10px;">Trasa</button>`;
        }
        
        html += `
            <div class="ride-item" style="margin-bottom: 8px; padding: 8px; border: 1px solid ${borderColor}; border-radius: 5px; background: ${backgroundColor};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 5px 0; font-size: 14px;">🚗 ${ride.driver_name} ${ratingStars}</h4>
                        <p style="margin: 0; font-size: 12px;"><strong>${ride.from_location}</strong> → <strong>${ride.to_location}</strong>${distanceText}</p>
                        <p style="margin: 2px 0 0 0; font-size: 11px; color: #666;">Místa: ${ride.available_seats} | Cena: ${ride.price_per_person} Kč ${statusText}</p>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        ${buttons}
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

// Hledat jízdy s filtry
async function searchRides() {
    const from = document.getElementById('fromSearch').value;
    const to = document.getElementById('toSearch').value;
    const maxPrice = document.getElementById('maxPrice').value;
    const minRating = 0;
    
    let userLat = 0, userLng = 0;
    if (navigator.geolocation) {
        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject);
            });
            userLat = position.coords.latitude;
            userLng = position.coords.longitude;
        } catch (e) {
            console.log('GPS nedostupné');
        }
    }
    
    try {
        const userId = localStorage.getItem('user_id') || '0';
        let url = `/api/rides/search?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&lat=${userLat}&lng=${userLng}&user_id=${userId}&include_own=true`;
        if (maxPrice) url += `&max_price=${maxPrice}`;
        // Hodnocení odstraňeno z filtrace
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        const rides = await response.json();
        
        const resultsContainer = document.getElementById('results');
        
        if (!rides || rides.length === 0) {
            resultsContainer.innerHTML = '<p>Žádné jízdy nebyly nalezeny.</p>';
            return;
        }
        
        let html = '<h3>Nalezené jízdy (seřazeno podle vzdálenosti):</h3>';
        rides.forEach(ride => {
            const distanceText = ride.distance > 0 ? `<p><strong>Vzdálenost:</strong> ${ride.distance} km</p>` : '';
            const waypointsText = ride.route_waypoints && ride.route_waypoints.length > 0 ? 
                `<p><strong>Zastávky:</strong> ${ride.route_waypoints.length} zastávek na trase</p>` : '';
            const ratingStars = '⭐'.repeat(Math.floor(ride.driver_rating));
            
            html += `
                <div class="ride-item">
                    <h4>🚗 ${ride.driver_name} <span class="ride-rating">${ratingStars} (${ride.driver_rating.toFixed(1)})</span></h4>
                    <p><strong>Trasa:</strong> ${ride.from_location} → ${ride.to_location}</p>
                    <p><strong>Odjezd:</strong> ${new Date(ride.departure_time).toLocaleString('cs-CZ')}</p>
                    <p><strong>Volná místa:</strong> ${ride.available_seats}</p>
                    <p><strong>Cena:</strong> ${ride.price_per_person} Kč</p>
                    ${distanceText}
                    ${waypointsText}
                    <button onclick="showRideRoute(${ride.id}, ${JSON.stringify(ride.route_waypoints).replace(/"/g, '&quot;')})" title="Zobrazí kompletní trasu jízdy s všemi zastávkami na mapě">Zobrazit trasu</button>
                    <button onclick="startNavigation(${JSON.stringify(ride.route_waypoints).replace(/"/g, '&quot;')})" title="Spustí hlasovou navigaci s dopravními informacemi a alternativními trasami">🧭 Navigovat</button>
                    <button onclick="reserveSeat(${ride.id}, '${ride.driver_name}')" title="Vytvoří rezervaci místa v této jízdě - čeká na potvrzení řidiče">Rezervovat místo</button>
                    <button onclick="contactDriver('${ride.driver_name}', ${ride.id})" title="Odešle přímou zprávu řidiči této jízdy">Kontaktovat řidiče</button>
                    <button onclick="openChatModal(${ride.id}, '${ride.driver_name}')" title="Otevře real-time chat pro tuto konkrétní jízdu">💬 Chat</button>
                    <button onclick="openRatingModal(${ride.user_id}, '${ride.driver_name}', ${ride.id})" title="Ohodnotí řidiče hvězdičkami a napíše komentář">⭐ Ohodnotit</button>
                    <button onclick="blockUser(${ride.user_id}, '${ride.driver_name}')" style="background: #dc3545;" title="Zablokuje tohoto uživatele - už se vám nebude zobrazovat">🚫 Blokovat</button>
                </div>
            `;
        });
        
        resultsContainer.innerHTML = html;
        
        // Přidá markery jízd na mapu
        addRideMarkersToMap(rides);
    } catch (error) {
        alert('Chyba při hledání: ' + error.message);
    }
}

// Přidá markery jízd na mapu
function addRideMarkersToMap(rides) {
    // Vymaže předchozí markery jízd
    if (window.rideMarkers) {
        window.rideMarkers.forEach(marker => {
            if (map.hasLayer(marker)) {
                map.removeLayer(marker);
            }
        });
    }
    window.rideMarkers = [];
    
    rides.forEach(ride => {
        // Použije první waypoint nebo výchozí pozici
        let lat = 50.0755; // Praha default
        let lng = 14.4378;
        
        if (ride.route_waypoints && ride.route_waypoints.length > 0) {
            lat = ride.route_waypoints[0].lat;
            lng = ride.route_waypoints[0].lng;
        }
        
        const rideIcon = L.divIcon({
            html: `<div style="background: #28a745; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">🚗</div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            className: 'ride-marker'
        });
        
        const ratingStars = '⭐'.repeat(Math.floor(ride.driver_rating));
        
        const popupContent = `
            <div style="text-align: center; min-width: 200px;">
                <h4>🚗 ${ride.driver_name}</h4>
                <p><strong>Trasa:</strong> ${ride.from_location} → ${ride.to_location}</p>
                <p><strong>Cena:</strong> ${ride.price_per_person} Kč</p>
                <p><strong>Místa:</strong> ${ride.available_seats}</p>
                <p>${ratingStars} (${ride.driver_rating.toFixed(1)})</p>
                <div style="margin-top: 10px;">
                    <button onclick="openDirectChat('${ride.driver_name}')" style="background: #667eea; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin: 2px;">💬 Chat</button>
                    <button onclick="reserveSeat(${ride.id}, '${ride.driver_name}')" style="background: #28a745; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin: 2px;">Rezervovat</button>
                </div>
            </div>
        `;
        
        const marker = L.marker([lat, lng], { icon: rideIcon })
            .addTo(map)
            .bindPopup(popupContent);
        
        window.rideMarkers.push(marker);
    });
}

// Kontaktovat řidiče
function contactDriver(driverName, rideId) {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        alert('⚠️ Musíte se přihlásit pro kontaktování!');
        showSettings();
        return;
    }
    
    const message = prompt(`Napište zprávu pro řidiče ${driverName}:`);
    if (message) {
        fetch('/api/messages/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ride_id: rideId,
                sender_id: parseInt(userId),
                message: message
            })
        }).then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('✅ Zpráva odeslána!');
            } else {
                alert('❌ Chyba: ' + data.error);
            }
        });
    }
}

// Rezervovat místo
function reserveSeat(rideId, driverName) {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        alert('⚠️ Musíte se přihlásit pro rezervaci!');
        showSettings();
        return;
    }
    
    const seats = prompt('Kolik míst chcete rezervovat?', '1');
    if (seats && parseInt(seats) > 0) {
        fetch('/api/reservations/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ride_id: rideId,
                passenger_id: parseInt(userId),
                seats_reserved: parseInt(seats)
            })
        }).then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(`✅ Rezervace vytvořena! Čeká na potvrzení od ${driverName}`);
                sendNotification('Rezervace vytvořena!', `Místo rezervováno u ${driverName}`);
                searchRides();
            } else {
                alert('❌ Chyba: ' + data.error);
            }
        });
    }
}

// Vymaže markery jízd z mapy
function clearRideMarkers() {
    if (window.rideMarkers) {
        window.rideMarkers.forEach(marker => {
            if (map.hasLayer(marker)) {
                map.removeLayer(marker);
            }
        });
        window.rideMarkers = [];
    }
}

// Zabrání mazání polí při updateRoutePreview
let preventFieldClearing = false;

// Vycentrovat mapu na uživatele
function centerOnUser() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                map.setView([lat, lng], 15);
                
                if (userMarker) {
                    userMarker.setLatLng([lat, lng]);
                } else {
                    const userIcon = L.divIcon({
                        html: '<div style="background: #4285f4; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
                        iconSize: [26, 26],
                        iconAnchor: [13, 13]
                    });
                    userMarker = L.marker([lat, lng], { icon: userIcon }).addTo(map).bindPopup('Vaše poloha 📍');
                }
            },
            function(error) {
                alert('GPS chyba: ' + error.message + '. Zkontrolujte povolení lokalizace v prohlížeči.');
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
    } else {
        alert('GPS není podporováno vaším prohlížečem.');
    }
}

// Zobrazit všechny uživatele na mapě
function showAllUsers() {
    if (!map || typeof L === 'undefined') return;
    
    const group = new L.featureGroup();
    let hasMarkers = false;
    
    if (userMarker) {
        group.addLayer(userMarker);
        hasMarkers = true;
    }
    
    Object.values(userMarkers).forEach(marker => {
        group.addLayer(marker);
        hasMarkers = true;
    });
    
    if (hasMarkers) {
        map.fitBounds(group.getBounds(), { padding: [20, 20] });
    }
}

// Zobrazit trasu jízdy
function showRideRoute(rideId, waypoints) {
    if (!map || !waypoints || waypoints.length === 0) {
        return;
    }
    
    clearRoute();
    
    waypoints.forEach((wp, index) => {
        const marker = L.marker([wp.lat, wp.lng], {
            icon: L.divIcon({
                html: `<div style="background: #28a745; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold;">${index + 1}</div>`,
                iconSize: [25, 25],
                iconAnchor: [12, 12]
            })
        }).addTo(map).bindPopup(wp.name || `Zastávka ${index + 1}`);
        
        routeMarkers.push(marker);
    });
    
    if (waypoints.length > 1) {
        drawRouteForWaypoints(waypoints, '#28a745');
    }
    
}

async function drawRouteForWaypoints(waypoints, color) {
    try {
        const coords = waypoints.map(wp => `${wp.lng},${wp.lat}`).join(';');
        const response = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
        const data = await response.json();
        
        if (data.routes && data.routes[0]) {
            const route = data.routes[0].geometry.coordinates;
            const latlngs = route.map(coord => [coord[1], coord[0]]);
            routeLine = L.polyline(latlngs, { 
                color: color, 
                weight: 4,
                opacity: 0.8
            }).addTo(map);
            
            map.fitBounds(routeLine.getBounds(), { padding: [20, 20] });
        }
    } catch (error) {
        console.error('OSRM routing failed:', error);
    }
}

// Vyčistí trasu
function clearRoute() {
    // Vymazání všech markerů
    routeMarkers.forEach(marker => {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        }
    });
    routeMarkers = [];
    
    // Vymazání všech modrých čar
    if (routeLine && map.hasLayer(routeLine)) {
        map.removeLayer(routeLine);
        routeLine = null;
    }
    
    // Vymazání waypointů a seznamu
    routeWaypoints = [];
    document.getElementById('routeWaypoints').innerHTML = '';
    
    // Vymazání polí v menu (jen pokud není zabráněno)
    if (!preventFieldClearing) {
        document.getElementById('fromOffer').value = '';
        document.getElementById('toOffer').value = '';
    }
    
    isRoutePlanning = false;
    map.off('click', addWaypoint);
    
    console.log('Trasa vymazána - markery:', routeMarkers.length, 'waypoints:', routeWaypoints.length, 'routeLine:', routeLine);
}

// Aktualizuje náhled trasy při zadání lokací
async function updateRoutePreview() {
    const fromLocation = document.getElementById('fromOffer').value.trim();
    const toLocation = document.getElementById('toOffer').value.trim();
    
    if (!fromLocation || !toLocation) {
        clearRoute();
        return;
    }
    
    try {
        // Geocoding - převede názvy míst na souřadnice
        const fromCoords = await geocodeLocation(fromLocation);
        const toCoords = await geocodeLocation(toLocation);
        
        if (fromCoords && toCoords) {
            // Vymaže předchozí trasu ale zachová pole
            preventFieldClearing = true;
            clearRoute();
            preventFieldClearing = false;
            
            // Obnov pole
            document.getElementById('fromOffer').value = fromLocation;
            document.getElementById('toOffer').value = toLocation;
            
            // Přidá počáteční a koncový bod
            routeWaypoints = [
                { lat: fromCoords.lat, lng: fromCoords.lng, name: fromLocation },
                { lat: toCoords.lat, lng: toCoords.lng, name: toLocation }
            ];
            
            // Vytvoří markery
            const startMarker = L.marker([fromCoords.lat, fromCoords.lng], {
                icon: L.divIcon({
                    html: '<div style="background: #28a745; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold;">A</div>',
                    iconSize: [25, 25],
                    iconAnchor: [12, 12]
                })
            }).addTo(map).bindPopup(`Start: ${fromLocation}`);
            
            const endMarker = L.marker([toCoords.lat, toCoords.lng], {
                icon: L.divIcon({
                    html: '<div style="background: #dc3545; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold;">B</div>',
                    iconSize: [25, 25],
                    iconAnchor: [12, 12]
                })
            }).addTo(map).bindPopup(`Cíl: ${toLocation}`);
            
            routeMarkers = [startMarker, endMarker];
            
            // Nakreslí trasu
            await drawRoute();
            
            // Vycentruje mapu na trasu
            const group = new L.featureGroup(routeMarkers);
            map.fitBounds(group.getBounds(), { padding: [20, 20] });
            
            // Umožní přesouvání markerů
            makeMarkersDraggable();
        }
    } catch (error) {
        console.error('Chyba při aktualizaci trasy:', error);
    }
}

// Geocoding - převede název místa na souřadnice
async function geocodeLocation(locationName) {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationName)}&countrycodes=cz&limit=1`);
        const data = await response.json();
        
        if (data && data.length > 0) {
            return {
                lat: parseFloat(data[0].lat),
                lng: parseFloat(data[0].lon)
            };
        }
        return null;
    } catch (error) {
        console.error('Geocoding chyba:', error);
        return null;
    }
}

// Umožní přesouvání markerů
function makeMarkersDraggable() {
    routeMarkers.forEach((marker, index) => {
        marker.dragging.enable();
        
        marker.on('dragend', async function(e) {
            const newPos = e.target.getLatLng();
            routeWaypoints[index].lat = newPos.lat;
            routeWaypoints[index].lng = newPos.lng;
            
            // Aktualizuje trasu při přesunutí
            await drawRoute();
            
            // Aktualizuje název lokace
            try {
                const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${newPos.lat}&lon=${newPos.lng}`);
                const data = await response.json();
                if (data && data.display_name) {
                    const shortName = data.display_name.split(',')[0];
                    routeWaypoints[index].name = shortName;
                    marker.bindPopup(`${index === 0 ? 'Start' : 'Cíl'}: ${shortName}`);
                    
                    // Aktualizuje input pole
                    if (index === 0) {
                        document.getElementById('fromOffer').value = shortName;
                    } else {
                        document.getElementById('toOffer').value = shortName;
                    }
                }
            } catch (error) {
                console.error('Reverse geocoding chyba:', error);
            }
        });
    });
}

// Hodnocení uživatelů
let currentRatingData = {};

function openRatingModal(userId, userName, rideId) {
    currentRatingData = { userId, userName, rideId };
    document.getElementById('ratingUserName').textContent = `Hodnotit uživatele: ${userName}`;
    document.getElementById('ratingModal').style.display = 'block';
    
    // Reset stars
    document.querySelectorAll('.star').forEach(star => {
        star.classList.remove('active');
        star.onclick = () => selectRating(star.dataset.rating);
    });
}

function selectRating(rating) {
    currentRatingData.rating = parseFloat(rating);
    document.querySelectorAll('.star').forEach((star, index) => {
        const starRating = parseFloat(star.dataset.rating);
        star.classList.toggle('active', starRating <= rating);
    });
}

function submitRating() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        alert('⚠️ Musíte se přihlásit pro hodnocení!');
        closeRatingModal();
        showSettings();
        return;
    }
    
    if (!currentRatingData.rating) {
        alert('Vyberte hodnocení!');
        return;
    }
    
    const comment = document.getElementById('ratingComment').value;
    
    fetch('/api/ratings/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ride_id: currentRatingData.rideId,
            rater_id: parseInt(userId),
            rated_id: currentRatingData.userId,
            rating: currentRatingData.rating,
            comment: comment
        })
    }).then(response => response.json())
    .then(data => {
        if (data.message) {
            alert('✅ Hodnocení odesláno!');
            closeRatingModal();
        } else {
            alert('❌ Chyba: ' + data.error);
        }
    });
}

function closeRatingModal() {
    document.getElementById('ratingModal').style.display = 'none';
    document.getElementById('ratingComment').value = '';
    currentRatingData = {};
}

// Blokování uživatelů
function blockUser(userId, userName) {
    const currentUserId = localStorage.getItem('user_id');
    if (!currentUserId) {
        alert('⚠️ Musíte se přihlásit pro blokování!');
        showSettings();
        return;
    }
    
    const reason = prompt(`Proč chcete blokovat uživatele ${userName}?`);
    if (reason) {
        fetch('/api/users/block', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                blocker_id: parseInt(currentUserId),
                blocked_id: userId,
                reason: reason
            })
        }).then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(`✅ Uživatel ${userName} byl zablokován`);
                searchRides(); // Refresh results
            } else {
                alert('❌ Chyba: ' + data.error);
            }
        });
    }
}

// Statistiky uživatele
function loadUserStats() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        document.getElementById('totalRides').textContent = 'Celkem jízd: Přihlaste se';
        document.getElementById('co2Saved').textContent = 'Ušetřeno CO2: Přihlaste se';
        document.getElementById('moneySaved').textContent = 'Ušetřeno peněz: Přihlaste se';
        return;
    }
    
    fetch(`/api/users/${userId}/stats`)
    .then(response => response.json())
    .then(data => {
        document.getElementById('totalRides').textContent = `Celkem jízd: ${data.total_rides}`;
        document.getElementById('co2Saved').textContent = `Ušetřeno CO2: ${data.co2_saved.toFixed(1)} kg`;
        document.getElementById('moneySaved').textContent = `Ušetřeno peněz: ${data.money_saved} Kč`;
    })
    .catch(error => {
        console.error('Chyba při načítání statistik:', error);
    });
}

// Hlasová navigace s dopravními informacemi
async function startNavigation(waypoints) {
    if (!waypoints || waypoints.length === 0) {
        alert('Trasa není dostupná');
        return;
    }
    
    // Optimalizuje trasu podle dopravní situace
    const optimizedWaypoints = await trafficManager.optimizeRoute(waypoints);
    
    if ('speechSynthesis' in window) {
        let totalTime = optimizedWaypoints.reduce((sum, wp) => sum + (wp.estimatedTime || 0), 0);
        const utterance = new SpeechSynthesisUtterance(
            `Navigace zahájena. Trasa má ${optimizedWaypoints.length} zastávek. Odhadovaný čas cesty je ${totalTime} minut. První cíl je ${optimizedWaypoints[0].name || 'neznámé místo'}.`
        );
        utterance.lang = 'cs-CZ';
        speechSynthesis.speak(utterance);
    }
    
    // Zobrazí alternativní trasy
    if (optimizedWaypoints.length >= 2) {
        await trafficManager.showAlternativeRoutes(optimizedWaypoints[0], optimizedWaypoints[optimizedWaypoints.length - 1]);
    }
    
    // Otevře Google Maps s navigací
    const firstWaypoint = optimizedWaypoints[0];
    const url = `https://www.google.com/maps/dir/?api=1&destination=${firstWaypoint.lat},${firstWaypoint.lng}&travelmode=driving`;
    window.open(url, '_blank');
    
    // Spustí hlasové pokyny
    startVoiceGuidance(optimizedWaypoints);
}

// Hlasové pokyny během jízdy
function startVoiceGuidance(waypoints) {
    let currentIndex = 0;
    
    const guidanceInterval = setInterval(() => {
        if (currentIndex >= waypoints.length - 1) {
            clearInterval(guidanceInterval);
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance('Dorazili jste do cíle. Navigace ukončena.');
                utterance.lang = 'cs-CZ';
                speechSynthesis.speak(utterance);
            }
            return;
        }
        
        trafficManager.provideVoiceGuidance(waypoints[currentIndex], waypoints[currentIndex + 1]);
        currentIndex++;
    }, 30000); // Pokyny každých 30 sekund
    
    // Uloží interval pro možnost zastavení
    window.currentGuidance = guidanceInterval;
}

// Zastaví hlasové pokyny
function stopVoiceGuidance() {
    if (window.currentGuidance) {
        clearInterval(window.currentGuidance);
        window.currentGuidance = null;
    }
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
    }
}

// Real-time chat
let currentChatRide = null;
let currentDirectChat = null;

function openChatModal(rideId, driverName) {
    currentChatRide = rideId;
    document.getElementById('chatTitle').textContent = `💬 Chat - jízda s ${driverName}`;
    document.getElementById('chatMessages').innerHTML = '';
    document.getElementById('chatModal').style.display = 'block';
    
    // Připoj se k chat room
    socket.emit('join_ride_chat', {
        ride_id: rideId,
        user_name: document.getElementById('userName').value || 'Neznámý uživatel'
    });
}

function closeChatModal() {
    if (currentChatRide) {
        socket.emit('leave_ride_chat', {
            ride_id: currentChatRide,
            user_name: document.getElementById('userName').value || 'Neznámý uživatel'
        });
        currentChatRide = null;
    } else if (currentDirectChat) {
        socket.emit('leave_direct_chat', {
            target_user: currentDirectChat,
            user_name: document.getElementById('userName').value || 'Neznámý uživatel'
        });
        currentDirectChat = null;
    }
    document.getElementById('chatModal').style.display = 'none';
}

function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (message) {
        if (currentChatRide) {
            socket.emit('send_chat_message', {
                ride_id: currentChatRide,
                user_name: document.getElementById('userName').value || 'Neznámý uživatel',
                message: message
            });
        } else if (currentDirectChat) {
            sendDirectMessage();
            return;
        }
        input.value = '';
    }
}

function shareLocation() {
    if (!currentChatRide) return;
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            socket.emit('share_live_location', {
                ride_id: currentChatRide,
                user_name: document.getElementById('userName').value || 'Neznámý uživatel',
                lat: position.coords.latitude,
                lng: position.coords.longitude
            });
        });
    }
}

function addChatMessage(userName, message, timestamp, isSystem = false) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `margin: 5px 0; padding: 8px; border-radius: 8px; ${isSystem ? 'background: #e9ecef; font-style: italic;' : 'background: white; border-left: 3px solid #667eea;'}`;
    
    const time = new Date(timestamp).toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
    messageDiv.innerHTML = `<strong>${userName}</strong> <small>(${time})</small><br>${message}`;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Socket event listenery jsou nyní inicializovány v initializeSocket()

// Přímý chat s uživatelem
function openDirectChat(userId) {
    currentDirectChat = userId;
    document.getElementById('chatTitle').textContent = `💬 Přímý chat s ${userId}`;
    document.getElementById('chatMessages').innerHTML = '';
    document.getElementById('chatModal').style.display = 'block';
    
    // Připoj se k přímému chatu
    socket.emit('join_direct_chat', {
        target_user: userId,
        user_name: document.getElementById('userName').value || 'Neznámý uživatel'
    });
}

function sendDirectMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (message && currentDirectChat) {
        socket.emit('send_direct_message', {
            target_user: currentDirectChat,
            user_name: document.getElementById('userName').value || 'Neznámý uživatel',
            message: message
        });
        input.value = '';
    }
}

function getUserLocation(userId) {
    socket.emit('request_user_location', {
        target_user: userId,
        requester: document.getElementById('userName').value || 'Neznámý uživatel'
    });
}

// Pravidelné jízdy
async function createRecurringRide() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        alert('⚠️ Musíte se přihlásit pro vytváření pravidelných jízd!');
        showSettings();
        return;
    }
    
    const selectedDays = Array.from(document.querySelectorAll('#recurringForm input[type="checkbox"]:checked'))
        .map(cb => cb.value);
    
    if (selectedDays.length === 0) {
        alert('Vyberte alespoň jeden den v týdnu!');
        return;
    }
    
    const formData = {
        user_id: parseInt(userId),
        from_location: document.getElementById('fromRecurring').value,
        to_location: document.getElementById('toRecurring').value,
        departure_time: document.getElementById('timeRecurring').value,
        days_of_week: selectedDays,
        available_seats: parseInt(document.getElementById('seatsRecurring').value),
        price_per_person: parseInt(document.getElementById('priceRecurring').value)
    };
    
    try {
        const response = await fetch('/api/rides/recurring', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('✅ Pravidelná jízda vytvořena!');
            document.getElementById('recurringRideForm').reset();
            loadRecurringRides();
        } else {
            alert('❌ Chyba: ' + result.error);
        }
    } catch (error) {
        alert('❌ Chyba při vytváření: ' + error.message);
    }
}

function copyCoords() {
    const coords = document.getElementById('coordsText').textContent;
    navigator.clipboard.writeText(coords).then(() => {
        const btn = event.target;
        btn.textContent = '✓';
        setTimeout(() => btn.textContent = '⧉', 1000);
    });
}

async function loadRecurringRides() {
    try {
        const userId = localStorage.getItem('user_id') || '0';
        const response = await fetch(`/api/rides/recurring?user_id=${userId}`);
        const rides = await response.json();
        
        const container = document.getElementById('recurringRidesList');
        
        if (rides.length === 0) {
            container.innerHTML = '<p>Zatím žádné pravidelné jízdy.</p>';
            return;
        }
        
        let html = '<h3>🔁 Dostupné pravidelné jízdy:</h3>';
        rides.forEach(ride => {
            const daysNames = {
                '0': 'Ne', '1': 'Po', '2': 'Út', '3': 'St', 
                '4': 'Čt', '5': 'Pá', '6': 'So'
            };
            const daysText = ride.days_of_week.map(day => daysNames[day]).join(', ');
            
            html += `
                <div class="ride-item">
                    <h4>🚗 ${ride.driver_name}</h4>
                    <p><strong>Trasa:</strong> ${ride.from_location} → ${ride.to_location}</p>
                    <p><strong>Čas:</strong> ${ride.departure_time}</p>
                    <p><strong>Dny:</strong> ${daysText}</p>
                    <p><strong>Volná místa:</strong> ${ride.available_seats}</p>
                    <p><strong>Cena:</strong> ${ride.price_per_person} Kč</p>
                    <button onclick="contactDriver('${ride.driver_name}', ${ride.id})" title="Odešle zprávu řidiči této pravidelné jízdy">Kontaktovat řidiče</button>
                </div>
            `;
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Chyba při načítání pravidelných jízd:', error);
    }
}