// Jednoduchá oprava GPS funkce
function showMyLocationFixed() {
    console.log('GPS test started');
    
    // Kontrola HTTPS
    if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
        alert('GPS vyžaduje HTTPS! Přesměrovávám na zabezpečenou verzi...');
        window.location.href = 'https://' + location.host + location.pathname;
        return;
    }
    
    if (!navigator.geolocation) {
        alert('GPS není podporováno v tomto prohlížeči');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            console.log('GPS nalezeno:', lat, lng);
            alert(`GPS poloha nalezena!\nLat: ${lat}\nLng: ${lng}`);
            
            // Pokud existuje mapa, vycentruj ji
            if (window.searchMap) {
                window.searchMap.setView([lat, lng], 13);
                
                // Přidej marker
                if (window.myLocationMarker) {
                    window.searchMap.removeLayer(window.myLocationMarker);
                }
                
                window.myLocationMarker = L.marker([lat, lng]).addTo(window.searchMap);
                window.myLocationMarker.bindPopup('📍 Vaše poloha').openPopup();
            }
        },
        function(error) {
            console.error('GPS chyba:', error);
            alert('GPS chyba: ' + error.message);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}