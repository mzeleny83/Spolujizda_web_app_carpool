// Upravení poslední nabídnuté jízdy
function editLastRide() {
    const lastRideData = localStorage.getItem('last_offered_ride');
    
    if (!lastRideData) {
        alert('Není k dispozici žádná jízda k úpravě');
        return;
    }
    
    try {
        const rideData = JSON.parse(lastRideData);
        
        // Otevře formulář pro nabídnutí jízdy
        if (document.getElementById('offerForm').style.display === 'none') {
            toggleOfferForm();
        }
        
        // Vyplňuje formulář uloženými daty
        document.getElementById('fromOffer').value = rideData.from_location || '';
        document.getElementById('toOffer').value = rideData.to_location || '';
        document.getElementById('departureOffer').value = rideData.departure_time || '';
        document.getElementById('seatsOffer').value = rideData.available_seats || '';
        document.getElementById('priceOffer').value = rideData.price_per_person || '';
        
        // Obnoví trasu pokud existuje
        if (rideData.route_waypoints && rideData.route_waypoints.length > 0) {
            routeWaypoints = rideData.route_waypoints;
            redrawAllWaypoints();
        }
        
        alert('✏️ Formulář byl vyplněn daty z poslední jízdy. Můžete provést úpravy a znovu nabídnout.');
        
    } catch (error) {
        alert('Chyba při načítání dat jízdy');
        console.error('Error parsing ride data:', error);
    }
}