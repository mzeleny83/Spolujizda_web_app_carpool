// Push notifikace pro nové jízdy a rezervace

class NotificationManager {
    constructor() {
        this.permission = Notification.permission;
        this.init();
    }

    async init() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.ready;
                this.registration = registration;
            } catch (error) {
                console.error('Service Worker chyba:', error);
            }
        }
    }

    async requestPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.permission = permission;
            return permission === 'granted';
        }
        return false;
    }

    showNotification(title, options = {}) {
        if (this.permission !== 'granted') {
            console.log('Notifikace nejsou povoleny');
            return;
        }

        const defaultOptions = {
            icon: '/static/icon-192.png',
            badge: '/static/icon-72.png',
            vibrate: [200, 100, 200],
            requireInteraction: true,
            actions: [
                {
                    action: 'view',
                    title: 'Zobrazit',
                    icon: '/static/icon-view.png'
                },
                {
                    action: 'dismiss',
                    title: 'Zavřít',
                    icon: '/static/icon-close.png'
                }
            ]
        };

        const finalOptions = { ...defaultOptions, ...options };

        if (this.registration) {
            this.registration.showNotification(title, finalOptions);
        } else {
            new Notification(title, finalOptions);
        }
    }

    // Notifikace pro nové jízdy
    notifyNewRide(ride) {
        this.showNotification('🚗 Nová jízda k dispozici!', {
            body: `${ride.from_location} → ${ride.to_location}\nCena: ${ride.price_per_person} Kč`,
            tag: 'new-ride',
            data: { rideId: ride.id, type: 'new-ride' }
        });
    }

    // Notifikace pro potvrzení rezervace
    notifyReservationConfirmed(ride, driverName) {
        this.showNotification('✅ Rezervace potvrzena!', {
            body: `${driverName} potvrdil vaši rezervaci na jízdu ${ride.from_location} → ${ride.to_location}`,
            tag: 'reservation-confirmed',
            data: { rideId: ride.id, type: 'reservation' }
        });
    }

    // Notifikace pro novou zprávu
    notifyNewMessage(senderName, message) {
        this.showNotification(`💬 Zpráva od ${senderName}`, {
            body: message.length > 100 ? message.substring(0, 100) + '...' : message,
            tag: 'new-message',
            data: { sender: senderName, type: 'message' }
        });
    }

    // Notifikace pro změnu jízdy
    notifyRideUpdate(ride, changeType) {
        const messages = {
            'time_changed': 'Čas odjezdu byl změněn',
            'cancelled': 'Jízda byla zrušena',
            'seats_changed': 'Počet míst byl změněn'
        };

        this.showNotification('⚠️ Změna jízdy', {
            body: `${ride.from_location} → ${ride.to_location}\n${messages[changeType] || 'Jízda byla aktualizována'}`,
            tag: 'ride-update',
            data: { rideId: ride.id, type: 'update', changeType }
        });
    }
}

// Globální instance
const notificationManager = new NotificationManager();

// Export pro použití v jiných souborech
window.notificationManager = notificationManager;