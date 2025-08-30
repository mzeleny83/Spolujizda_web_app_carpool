// Navigační funkce
let navigationActive = false;
let currentRoute = null;

// Spustí navigaci
function startNavigation(waypoints) {
    if (!waypoints || waypoints.length < 2) {
        alert('Nedostatek bodů pro navigaci');
        return;
    }
    
    navigationActive = true;
    currentRoute = waypoints;
    
    // Vytvoří navigační panel
    createNavigationPanel();
    
    // Spustí sledování pozice pro navigaci
    if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition(
            updateNavigationPosition,
            handleNavigationError,
            { enableHighAccuracy: true, timeout: 5000, maximumAge: 1000 }
        );
    }
    
    alert('🧭 Navigace spuštěna!');
}

// Vytvoří navigační panel
function createNavigationPanel() {
    const navPanel = document.createElement('div');
    navPanel.id = 'navigationPanel';
    navPanel.style.cssText = `
        position: fixed;
        top: 20px;
        left: 20px;
        right: 20px;
        background: rgba(0,0,0,0.9);
        color: white;
        padding: 15px;
        border-radius: 10px;
        z-index: 1000;
        font-size: 16px;
        text-align: center;
    `;
    
    navPanel.innerHTML = `
        <div id="navInstruction">🧭 Navigace se načítá...</div>
        <div id="navDistance" style="font-size: 14px; margin-top: 5px;"></div>
        <button onclick="stopNavigation()" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 5px; margin-top: 10px;">Ukončit navigaci</button>
    `;
    
    document.body.appendChild(navPanel);
}

// Aktualizuje pozici během navigace
function updateNavigationPosition(position) {
    if (!navigationActive || !currentRoute) return;
    
    const userLat = position.coords.latitude;
    const userLng = position.coords.longitude;
    
    // Najde nejbližší bod na trase
    let nearestPoint = null;
    let minDistance = Infinity;
    let nextWaypointIndex = 0;
    
    currentRoute.forEach((waypoint, index) => {
        const distance = calculateDistance(userLat, userLng, waypoint.lat, waypoint.lng);
        if (distance < minDistance) {
            minDistance = distance;
            nearestPoint = waypoint;
            nextWaypointIndex = index + 1;
        }
    });
    
    // Aktualizuje navigační instrukce
    updateNavigationInstructions(userLat, userLng, nextWaypointIndex);
}

// Aktualizuje navigační instrukce
function updateNavigationInstructions(userLat, userLng, nextWaypointIndex) {
    const navInstruction = document.getElementById('navInstruction');
    const navDistance = document.getElementById('navDistance');
    
    if (nextWaypointIndex >= currentRoute.length) {
        navInstruction.textContent = '🎉 Cíl dosažen!';
        navDistance.textContent = '';
        setTimeout(stopNavigation, 3000);
        return;
    }
    
    const nextWaypoint = currentRoute[nextWaypointIndex];
    const distance = calculateDistance(userLat, userLng, nextWaypoint.lat, nextWaypoint.lng);
    const bearing = calculateBearing(userLat, userLng, nextWaypoint.lat, nextWaypoint.lng);
    
    // Směrové instrukce
    let direction = '';
    if (bearing >= 337.5 || bearing < 22.5) direction = '⬆️ Pokračujte rovně';
    else if (bearing >= 22.5 && bearing < 67.5) direction = '↗️ Odbočte vpravo';
    else if (bearing >= 67.5 && bearing < 112.5) direction = '➡️ Odbočte doprava';
    else if (bearing >= 112.5 && bearing < 157.5) direction = '↘️ Odbočte vpravo';
    else if (bearing >= 157.5 && bearing < 202.5) direction = '⬇️ Otočte se';
    else if (bearing >= 202.5 && bearing < 247.5) direction = '↙️ Odbočte vlevo';
    else if (bearing >= 247.5 && bearing < 292.5) direction = '⬅️ Odbočte doleva';
    else direction = '↖️ Odbočte vlevo';
    
    navInstruction.textContent = direction;
    navDistance.textContent = `${Math.round(distance * 1000)}m do ${nextWaypoint.name || 'dalšího bodu'}`;
    
    // Hlasové instrukce (pokud je podporováno)
    if (distance < 0.05 && 'speechSynthesis' in window) { // 50m
        const utterance = new SpeechSynthesisUtterance(`Za 50 metrů ${direction.replace(/[⬆️↗️➡️↘️⬇️↙️⬅️↖️]/g, '')}`);
        utterance.lang = 'cs-CZ';
        speechSynthesis.speak(utterance);
    }
}

// Vypočítá směr (bearing) mezi dvěma body
function calculateBearing(lat1, lng1, lat2, lng2) {
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const lat1Rad = lat1 * Math.PI / 180;
    const lat2Rad = lat2 * Math.PI / 180;
    
    const y = Math.sin(dLng) * Math.cos(lat2Rad);
    const x = Math.cos(lat1Rad) * Math.sin(lat2Rad) - Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLng);
    
    let bearing = Math.atan2(y, x) * 180 / Math.PI;
    return (bearing + 360) % 360;
}

// Ukončí navigaci
function stopNavigation() {
    navigationActive = false;
    currentRoute = null;
    
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
    
    const navPanel = document.getElementById('navigationPanel');
    if (navPanel) {
        navPanel.remove();
    }
    
    alert('🛑 Navigace ukončena');
}

// Chyba navigace
function handleNavigationError(error) {
    console.error('Navigační chyba:', error);
    document.getElementById('navInstruction').textContent = '❌ Chyba GPS';
}