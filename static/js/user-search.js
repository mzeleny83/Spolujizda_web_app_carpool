(function() {
// Hledání uživatelů a GPS navigace

let navigationActive = false;
let navigationInterval = null;
let targetUser = null;

// Hledání uživatele
async function searchUser() {
    const input = document.getElementById('userSearchInput').value.trim();
    const results = document.getElementById('userSearchResults');
    
    if (!input) {
        results.innerHTML = '<p>Zadejte email nebo telefon</p>';
        return;
    }
    
    results.innerHTML = '<p>Hledám uživatele...</p>';
    
    try {
        const response = await fetch('/api/users/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: input })
        });
        
        if (!response.ok) {
            throw new Error('Uživatel nenalezen');
        }
        
        const user = await response.json();
        displayFoundUser(user);
        
    } catch (error) {
        results.innerHTML = `<p>Uživatel nenalezen: ${error.message}</p>`;
    }
}

// Zobrazení nalezeného uživatele
function displayFoundUser(user) {
    const results = document.getElementById('userSearchResults');
    
    results.innerHTML = `
        <div style="padding: 10px; background: #f0f8ff; border-radius: 8px; margin: 10px 0;">
            <h4>👤 ${user.name}</h4>
            <p>📞 ${user.phone}</p>
            <p>⭐ Hodnocení: ${(user.rating || 0).toFixed(1)}</p>
            <button onclick="showUserOnMap('${user.name}')" style="background: #28a745; color: white; padding: 8px 15px; border: none; border-radius: 5px; margin: 5px;">📍 Zobrazit na mapě</button>
            <button onclick="startNavigationToUser('${user.name}')" style="background: #007bff; color: white; padding: 8px 15px; border: none; border-radius: 5px; margin: 5px;">🧭 Navigovat</button>
        </div>
    `;
}

// Zobrazení uživatele na mapě
function showUserOnMap(userName) {
    socket.emit('request_user_location', {
        target_user: userName,
        requester: localStorage.getItem('user_name') || 'Neznámý'
    });
}

// Spuštění navigace k uživateli
function startNavigationToUser(userName) {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        alert('Přihlaste se pro navigaci');
        return;
    }
    
    if (!navigator.geolocation) {
        alert('GPS není podporováno');
        return;
    }
    
    targetUser = userName;
    navigationActive = true;
    
    // Požádá o polohu cílového uživatele
    socket.emit('request_user_location', {
        target_user: userName,
        requester: localStorage.getItem('user_name') || 'Neznámý'
    });
    
    // Spustí kontinuální navigaci
    startGPSNavigation();
    
    // Hlasové oznámení
    speak(`Navigace k uživateli ${userName} zahájena`);
}

// GPS navigace s kompasem
function startGPSNavigation() {
    if (!navigationActive) return;
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const myLat = position.coords.latitude;
            const myLng = position.coords.longitude;
            const heading = position.coords.heading || 0;
            
            // Rotace mapy podle směru pohybu
            if (heading !== null) {
                map.setBearing(heading);
            }
            
            // Vycentrování na moji polohu
            map.setView([myLat, myLng], 18);
            
            // Aktualizace každé 2 sekundy
            setTimeout(() => {
                if (navigationActive) {
                    startGPSNavigation();
                }
            }, 2000);
        },
        (error) => {
            console.error('GPS chyba:', error);
        },
        {
            enableHighAccuracy: true,
            timeout: 5000,
            maximumAge: 0
        }
    );
}

// Zastavení navigace
function stopNavigation() {
    navigationActive = false;
    targetUser = null;
    
    if (navigationInterval) {
        clearInterval(navigationInterval);
        navigationInterval = null;
    }
    
    // Reset mapy
    map.setBearing(0);
    
    // Zastavení hlasu
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
    }
    
    speak('Navigace ukončena');
}

// Hlasové pokyny
function speak(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'cs-CZ';
        utterance.rate = 0.9;
        speechSynthesis.speak(utterance);
    }
}

// Výpočet vzdálenosti a směru
function calculateBearing(lat1, lng1, lat2, lng2) {
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const lat1Rad = lat1 * Math.PI / 180;
    const lat2Rad = lat2 * Math.PI / 180;
    
    const y = Math.sin(dLng) * Math.cos(lat2Rad);
    const x = Math.cos(lat1Rad) * Math.sin(lat2Rad) - Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLng);
    
    const bearing = Math.atan2(y, x) * 180 / Math.PI;
    return (bearing + 360) % 360;
}

function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371000; // metry
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}
})();