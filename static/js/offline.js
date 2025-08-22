// Offline režim pro základní funkce
class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineData = {
            rides: [],
            messages: [],
            locations: {}
        };
        this.init();
    }

    init() {
        // Poslouchá změny připojení
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Načte offline data z localStorage
        this.loadOfflineData();
        
        // Zobrazí status připojení
        this.updateConnectionStatus();
    }

    handleOnline() {
        this.isOnline = true;
        this.updateConnectionStatus();
        this.syncOfflineData();
        this.showNotification('✅ Připojení obnoveno', 'Synchronizuji offline data...');
    }

    handleOffline() {
        this.isOnline = false;
        this.updateConnectionStatus();
        this.showNotification('⚠️ Offline režim', 'Některé funkce jsou omezené');
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = this.isOnline ? 'Připojeno' : 'Offline režim';
            statusElement.className = this.isOnline ? 'connected' : 'disconnected';
        }
    }

    // Uloží data pro offline použití
    saveOfflineData(key, data) {
        this.offlineData[key] = data;
        localStorage.setItem('spolujizda_offline', JSON.stringify(this.offlineData));
    }

    // Načte offline data
    loadOfflineData() {
        const saved = localStorage.getItem('spolujizda_offline');
        if (saved) {
            try {
                this.offlineData = JSON.parse(saved);
            } catch (e) {
                console.error('Chyba při načítání offline dat:', e);
            }
        }
    }

    // Synchronizuje offline data při obnovení připojení
    async syncOfflineData() {
        const pendingActions = this.getPendingActions();
        
        for (const action of pendingActions) {
            try {
                await fetch(action.url, action.options);
                console.log('Offline akce synchronizována:', action);
            } catch (error) {
                console.error('Chyba při synchronizaci:', error);
            }
        }
        
        // Vymaže synchronizované akce
        this.clearPendingActions();
    }

    // Přidá akci do fronty pro offline synchronizaci
    addPendingAction(url, options) {
        const actions = this.getPendingActions();
        actions.push({
            url,
            options,
            timestamp: Date.now()
        });
        localStorage.setItem('pending_actions', JSON.stringify(actions));
    }

    getPendingActions() {
        const saved = localStorage.getItem('pending_actions');
        return saved ? JSON.parse(saved) : [];
    }

    clearPendingActions() {
        localStorage.removeItem('pending_actions');
    }

    // Offline vyhledávání jízd
    searchRidesOffline(from, to) {
        const cachedRides = this.offlineData.rides || [];
        
        // Jednoduché filtrování podle textu
        const results = cachedRides.filter(ride => 
            ride.from_location.toLowerCase().includes(from.toLowerCase()) ||
            ride.to_location.toLowerCase().includes(to.toLowerCase())
        );

        return results;
    }

    // Offline nabídka jízdy
    offerRideOffline(rideData) {
        // Uloží do offline fronty
        this.addPendingAction('/api/rides/offer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rideData)
        });

        // Přidá do lokálních dat pro okamžité zobrazení
        const localRide = {
            ...rideData,
            id: Date.now(),
            driver_name: 'Vy (čeká na synchronizaci)',
            offline: true
        };
        
        this.offlineData.rides.push(localRide);
        this.saveOfflineData('rides', this.offlineData.rides);

        return localRide;
    }

    // Offline zprávy
    sendMessageOffline(messageData) {
        this.addPendingAction('/api/messages/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(messageData)
        });

        // Uloží lokálně
        const localMessage = {
            ...messageData,
            id: Date.now(),
            timestamp: new Date().toISOString(),
            offline: true
        };

        if (!this.offlineData.messages) {
            this.offlineData.messages = [];
        }
        this.offlineData.messages.push(localMessage);
        this.saveOfflineData('messages', this.offlineData.messages);

        return localMessage;
    }

    // Offline mapa - základní funkcionalita
    initOfflineMap() {
        if (!this.isOnline && typeof L !== 'undefined') {
            // Přepne na offline tile layer (pokud je dostupný)
            const offlineLayer = L.tileLayer('', {
                attribution: 'Offline režim - omezená funkcionalita'
            });
            
            if (map && map.hasLayer) {
                // Odebere online vrstvy
                map.eachLayer(layer => {
                    if (layer instanceof L.TileLayer) {
                        map.removeLayer(layer);
                    }
                });
                
                // Přidá offline vrstvu
                offlineLayer.addTo(map);
            }
        }
    }

    // Zobrazí notifikaci
    showNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body });
        } else {
            // Fallback - zobrazí alert
            console.log(`${title}: ${body}`);
        }
    }

    // Exportuje data pro backup
    exportData() {
        const exportData = {
            rides: this.offlineData.rides,
            messages: this.offlineData.messages,
            userStats: localStorage.getItem('user_stats'),
            timestamp: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `spolujizda_backup_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // Importuje data ze zálohy
    importData(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const importedData = JSON.parse(e.target.result);
                
                // Sloučí s existujícími daty
                this.offlineData.rides = [...(this.offlineData.rides || []), ...(importedData.rides || [])];
                this.offlineData.messages = [...(this.offlineData.messages || []), ...(importedData.messages || [])];
                
                this.saveOfflineData('rides', this.offlineData.rides);
                this.saveOfflineData('messages', this.offlineData.messages);
                
                if (importedData.userStats) {
                    localStorage.setItem('user_stats', importedData.userStats);
                }
                
                alert('✅ Data úspěšně importována!');
            } catch (error) {
                alert('❌ Chyba při importu dat: ' + error.message);
            }
        };
        reader.readAsText(file);
    }

    // Vymaže offline data
    clearOfflineData() {
        if (confirm('Opravdu chcete vymazat všechna offline data?')) {
            this.offlineData = { rides: [], messages: [], locations: {} };
            localStorage.removeItem('spolujizda_offline');
            localStorage.removeItem('pending_actions');
            alert('✅ Offline data vymazána');
        }
    }
}

// Globální instance
const offlineManager = new OfflineManager();

// Rozšíření existujících funkcí pro offline podporu
const originalSearchRides = window.searchRides;
window.searchRides = async function() {
    if (!offlineManager.isOnline) {
        const from = document.getElementById('fromSearch').value;
        const to = document.getElementById('toSearch').value;
        const results = offlineManager.searchRidesOffline(from, to);
        
        const resultsContainer = document.getElementById('results');
        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>📱 Offline režim - žádné uložené jízdy nenalezeny.</p>';
        } else {
            let html = '<h3>📱 Offline výsledky:</h3>';
            results.forEach(ride => {
                html += `
                    <div class="ride-item" style="border-left-color: #ffc107;">
                        <h4>🚗 ${ride.driver_name} ${ride.offline ? '(offline)' : ''}</h4>
                        <p><strong>Trasa:</strong> ${ride.from_location} → ${ride.to_location}</p>
                        <p><strong>Cena:</strong> ${ride.price_per_person} Kč</p>
                        <p style="color: #ffc107;"><small>⚠️ Offline data - může být zastaralé</small></p>
                    </div>
                `;
            });
            resultsContainer.innerHTML = html;
        }
        return;
    }
    
    // Online režim
    return originalSearchRides.apply(this, arguments);
};

const originalOfferRide = window.offerRide;
window.offerRide = async function() {
    if (!offlineManager.isOnline) {
        const formData = {
            from_location: document.getElementById('fromOffer').value,
            to_location: document.getElementById('toOffer').value,
            departure_time: document.getElementById('departureOffer').value,
            available_seats: parseInt(document.getElementById('seatsOffer').value),
            price_per_person: parseInt(document.getElementById('priceOffer').value),
            route_waypoints: routeWaypoints
        };
        
        const ride = offlineManager.offerRideOffline(formData);
        alert('📱 Jízda uložena offline - bude synchronizována při obnovení připojení');
        document.getElementById('rideOfferForm').reset();
        clearRoute();
        return;
    }
    
    // Online režim
    return originalOfferRide.apply(this, arguments);
};

// Přidá offline funkce do nastavení
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        const settingsForm = document.getElementById('settingsForm');
        if (settingsForm) {
            const offlineSection = document.createElement('div');
            offlineSection.innerHTML = `
                <hr style="margin: 20px 0;">
                <h3>📱 Offline režim</h3>
                <p>Stav: <span id="offlineStatus">${offlineManager.isOnline ? 'Online' : 'Offline'}</span></p>
                <button onclick="offlineManager.exportData()">💾 Exportovat data</button>
                <input type="file" id="importFile" accept=".json" style="display: none;" onchange="offlineManager.importData(this.files[0])">
                <button onclick="document.getElementById('importFile').click()">📂 Importovat data</button>
                <button onclick="offlineManager.clearOfflineData()" style="background: #dc3545;">🗑️ Vymazat offline data</button>
            `;
            settingsForm.appendChild(offlineSection);
        }
    }, 1000);
});