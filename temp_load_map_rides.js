let rideMarkers = []; // To store markers for rides on the map

        async function loadMapRides() {
            if (!map) {
                initRealMap(); // Ensure map is initialized
            }

            // Clear existing ride markers
            rideMarkers.forEach(marker => {
                map.removeLayer(marker);
            });
            rideMarkers = [];

            const mapRidesList = document.getElementById('mapRidesList');
            mapRidesList.innerHTML = '⏳ Načítám jízdy na mapu...';

            try {
                const response = await fetch('/api/rides/search'); // Fetch all rides
                const rides = await response.json();

                if (rides.length === 0) {
                    mapRidesList.innerHTML = '<div style="text-align:center;color:#666;margin:30px 0;">❌ Žádné jízdy nenalezeny pro zobrazení na mapě</div>';
                    return;
                }

                let bounds = L.latLngBounds(); // To fit all markers on the map

                rides.forEach(ride => {
                    // Assuming ride.from_location and ride.to_location can be geocoded
                    // For now, we'll use dummy coordinates or skip if not available
                    // In a real app, you'd use a geocoding service to get lat/lng from location names

                    // Example: If ride object contains lat/lng for from and to locations
                    if (ride.from_lat && ride.from_lng) {
                        const fromLatLng = [ride.from_lat, ride.from_lng];
                        const fromMarker = L.marker(fromLatLng, {
                            icon: L.divIcon({
                                html: '<div style="background: #4caf50; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">START</div>',
                                iconSize: [25, 25],
                                iconAnchor: [12, 12]
                            })
                        }).addTo(map);
                        fromMarker.bindPopup(`<b>${ride.from_location}</b><br>Odkud`);
                        rideMarkers.push(fromMarker);
                        bounds.extend(fromLatLng);
                    }

                    if (ride.to_lat && ride.to_lng) {
                        const toLatLng = [ride.to_lat, ride.to_lng];
                        const toMarker = L.marker(toLatLng, {
                            icon: L.divIcon({
                                html: '<div style="background: #f44336; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">CÍL</div>',
                                iconSize: [25, 25],
                                iconAnchor: [12, 12]
                            })
                        }).addTo(map);
                        toMarker.bindPopup(`<b>${ride.to_location}</b><br>Kam`);
                        rideMarkers.push(toMarker);
                        bounds.extend(toLatLng);
                    }

                    // Display ride details in the list
                    mapRidesList.innerHTML += `
                        <div class="ride">
                            <h3>${ride.from_location} → ${ride.to_location}</h3>
                            <div>🕐 ${ride.departure_time} | 👥 ${ride.available_seats} míst | 💰 ${ride.price_per_person} Kč</div>
                            <div>🚗 ${ride.driver_name || 'Neznámý řidič'}</div>
                            <div style="margin-top: 10px;">
                                <button class="btn" onclick="openChat('passenger', ${ride.id}, '${ride.driver_name}')" style="background: #17a2b8; padding: 5px 15px;">💬 Chat s řidičem</button>
                            </div>
                        </div>
                    `;
                });

                if (bounds.isValid()) {
                    map.fitBounds(bounds); // Adjust map view to fit all markers
                }

            } catch (error) {
                mapRidesList.innerHTML = '❌ Chyba při načítání jízd na mapu: ' + error.message;
            }
        }