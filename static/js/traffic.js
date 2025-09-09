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
        
        // Získá dopravní data podle zadané trasy
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
        // TODO: Implement with a real traffic data provider
        return [];
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
        // TODO: Implement with a real traffic data provider
        return waypoints;
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
            instruction = `Za ${(distance || 0).toFixed(1)} kilometrů pokračujte k ${nextWaypoint.name || 'dalšímu bodu'}.`;
        }

        const utterance = new SpeechSynthesisUtterance(instruction);
        utterance.lang = 'cs-CZ';
        utterance.rate = 0.9;
        speechSynthesis.speak(utterance);
    }

    // Zobrazí alternativní trasy
    async showAlternativeRoutes(start, end) {
        // TODO: Implement with a real traffic data provider
        document.getElementById('results').innerHTML = '';
    }
}

// Globální instance
const trafficManager = new TrafficManager();

// Inicializace při načtení mapy
document.addEventListener('DOMContentLoaded', function() {
    // Počká na inicializaci mapy
    setTimeout(() => {
        if (typeof map !== 'undefined' && map) {
            // trafficManager.addTrafficLayer(); // Removed non-existent function call
        }
    }, 2000);
});
