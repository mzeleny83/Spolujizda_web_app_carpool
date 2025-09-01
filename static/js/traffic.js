// Dopravní informace jen při plánování trasy
class TrafficManager {
    constructor() {
        this.trafficLayer = null;
        this.isRoutePlanning = false;
    }

    // Zobrazí dopravní úseky pro konkrétní trasu
    showTrafficForRoutePlanning(fromLocation, toLocation) {
        if (!map) return;
        
        this.isRoutePlanning = true;
        this.trafficLayer = L.layerGroup();
        
        // Přidá dopravní úseky podle zadané trasy
        this.addTrafficSegments(fromLocation, toLocation);
        
        this.trafficLayer.addTo(map);
    }
    
    // Skryje dopravní vrstvu
    hideTrafficLayer() {
        if (this.trafficLayer) {
            map.removeLayer(this.trafficLayer);
            this.trafficLayer = null;
        }
        this.isRoutePlanning = false;
    }

    // Přidá dopravní úseky podle zadané trasy
    addTrafficSegments(fromLocation, toLocation) {
        if (!this.isRoutePlanning) return;
        
        // Získá dopravní data podle trasy
        const trafficSegments = this.getTrafficForRoute(fromLocation, toLocation);

        trafficSegments.forEach(segment => {
            const color = this.getTrafficColor(segment.type);
            const polyline = L.polyline(segment.coordinates, {
                color: color,
                weight: 8,
                opacity: 0.9
            }).bindPopup(`🚦 ${segment.name}`);
            
            this.trafficLayer.addLayer(polyline);
        });
    }
    
    // Získá dopravní data pro konkrétní trasu
    getTrafficForRoute(from, to) {
        // Simulace dopravních dat podle trasy
        const segments = [];
        
        if (from && to) {
            if (from.toLowerCase().includes('brno') && to.toLowerCase().includes('boskovice')) {
                segments.push({
                    name: 'Hustý provoz - výjezd z Brna (D1)',
                    coordinates: [
                        [49.1951, 16.6068],  // Brno
                        [49.2051, 16.6168],
                        [49.2151, 16.6268]
                    ],
                    type: 'heavy'
                });
                segments.push({
                    name: 'Nehoda - silnice I/43 směr Boskovice',
                    coordinates: [
                        [49.3500, 16.7000],
                        [49.3600, 16.7100],
                        [49.3700, 16.7200]
                    ],
                    type: 'accident'
                });
            } else if (from.toLowerCase().includes('praha')) {
                segments.push({
                    name: 'Hustý provoz - Václavské náměstí',
                    coordinates: [
                        [50.0755, 14.4378],
                        [50.0765, 14.4388],
                        [50.0775, 14.4398]
                    ],
                    type: 'heavy'
                });
            }
        }
        
        return segments;
    }

    // Vrátí barvu podle typu dopravního problému
    getTrafficColor(type) {
        switch (type) {
            case 'heavy': return '#dc3545';
            case 'medium': return '#ffc107';
            case 'accident': return '#6f42c1';
            default: return '#28a745';
        }
    }



    // Optimalizuje trasu podle dopravní situace
    async optimizeRoute(waypoints) {
        if (!waypoints || waypoints.length < 2) return waypoints;

        try {
            // Simulace optimalizace trasy
            const optimizedWaypoints = [...waypoints];
            
            // Přidá informace o času cesty
            for (let i = 0; i < optimizedWaypoints.length - 1; i++) {
                const distance = this.calculateDistance(
                    optimizedWaypoints[i].lat, optimizedWaypoints[i].lng,
                    optimizedWaypoints[i + 1].lat, optimizedWaypoints[i + 1].lng
                );
                
                // Simulace dopravní situace
                const trafficMultiplier = Math.random() * 0.5 + 1; // 1.0 - 1.5x
                const estimatedTime = Math.round((distance / 50) * 60 * trafficMultiplier); // km/h -> minuty
                
                optimizedWaypoints[i].estimatedTime = estimatedTime;
                optimizedWaypoints[i].trafficStatus = trafficMultiplier > 1.3 ? 'heavy' : 
                                                    trafficMultiplier > 1.15 ? 'medium' : 'light';
            }

            return optimizedWaypoints;
        } catch (error) {
            console.error('Chyba při optimalizaci trasy:', error);
            return waypoints;
        }
    }

    // Vypočítá vzdálenost mezi dvěma body
    calculateDistance(lat1, lng1, lat2, lng2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    // Poskytne hlasové pokyny pro navigaci
    provideVoiceGuidance(currentWaypoint, nextWaypoint) {
        if (!('speechSynthesis' in window)) return;

        const distance = this.calculateDistance(
            currentWaypoint.lat, currentWaypoint.lng,
            nextWaypoint.lat, nextWaypoint.lng
        );

        let instruction = '';
        if (distance < 0.5) {
            instruction = `Za ${Math.round(distance * 1000)} metrů pokračujte k ${nextWaypoint.name || 'dalšímu bodu'}.`;
        } else {
            instruction = `Za ${distance.toFixed(1)} kilometrů pokračujte k ${nextWaypoint.name || 'dalšímu bodu'}.`;
        }

        // Přidá informace o dopravě
        if (nextWaypoint.trafficStatus === 'heavy') {
            instruction += ' Pozor, v této oblasti je hustý provoz.';
        } else if (nextWaypoint.trafficStatus === 'medium') {
            instruction += ' V této oblasti může být mírné zpoždění.';
        }

        const utterance = new SpeechSynthesisUtterance(instruction);
        utterance.lang = 'cs-CZ';
        utterance.rate = 0.9;
        speechSynthesis.speak(utterance);
    }

    // Zobrazí alternativní trasy
    async showAlternativeRoutes(start, end) {
        const routes = [
            { name: 'Nejrychlejší trasa', time: 25, distance: 15.2, traffic: 'medium' },
            { name: 'Nejkratší trasa', time: 32, distance: 12.8, traffic: 'heavy' },
            { name: 'Bez dálnic', time: 38, distance: 18.5, traffic: 'light' }
        ];

        let html = '<h4>🛣️ Alternativní trasy:</h4>';
        routes.forEach((route, index) => {
            const trafficIcon = route.traffic === 'heavy' ? '🔴' : 
                              route.traffic === 'medium' ? '🟡' : '🟢';
            
            html += `
                <div style="padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; cursor: pointer;" 
                     onclick="selectRoute(${index})">
                    <strong>${route.name}</strong> ${trafficIcon}<br>
                    ⏱️ ${route.time} min | 📏 ${route.distance} km
                </div>
            `;
        });

        // Zobrazí v results kontejneru
        document.getElementById('results').innerHTML = html;
    }
}

// Globální instance
const trafficManager = new TrafficManager();

// Funkce pro výběr trasy
function selectRoute(routeIndex) {
    const routes = [
        'Nejrychlejší trasa vybrána. Navigace zahájena.',
        'Nejkratší trasa vybrána. Navigace zahájena.',
        'Trasa bez dálnic vybrána. Navigace zahájena.'
    ];
    
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(routes[routeIndex]);
        utterance.lang = 'cs-CZ';
        speechSynthesis.speak(utterance);
    }
    
    alert(`✅ ${routes[routeIndex]}`);
}

// Inicializace při načtení mapy
document.addEventListener('DOMContentLoaded', function() {
    // Počká na inicializaci mapy
    setTimeout(() => {
        if (typeof map !== 'undefined' && map) {
            
        }
    }, 2000);
});