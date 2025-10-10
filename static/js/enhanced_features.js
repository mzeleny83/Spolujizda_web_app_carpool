// Enhanced Features for Spolujizda App

// Voice Messages
class VoiceMessage {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.sendVoiceMessage(audioBlob);
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            return true;
        } catch (error) {
            console.error('Error starting recording:', error);
            return false;
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    async sendVoiceMessage(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice-message.wav');
        formData.append('ride_id', currentChatRide);
        formData.append('sender_id', currentUser.user_id);
        formData.append('sender_name', currentUser.name);
        formData.append('message_type', 'voice');

        try {
            const response = await fetch('/api/chat/send-voice', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                loadChatMessages();
            }
        } catch (error) {
            console.error('Error sending voice message:', error);
        }
    }
}

// Real-time Location Tracking
class LocationTracker {
    constructor() {
        this.watchId = null;
        this.currentPosition = null;
    }

    startTracking() {
        if (!navigator.geolocation) {
            console.error('Geolocation not supported');
            return false;
        }

        this.watchId = navigator.geolocation.watchPosition(
            (position) => {
                this.currentPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    timestamp: Date.now()
                };
                this.updateLocationOnServer();
            },
            (error) => {
                console.error('Location error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );

        return true;
    }

    stopTracking() {
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
    }

    async updateLocationOnServer() {
        if (!currentUser || !this.currentPosition) return;

        try {
            await fetch('/api/users/location', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: currentUser.user_id,
                    latitude: this.currentPosition.lat,
                    longitude: this.currentPosition.lng
                })
            });
        } catch (error) {
            console.error('Error updating location:', error);
        }
    }
}

// Push Notifications
class PushNotifications {
    constructor() {
        this.registration = null;
    }

    async initialize() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.log('Push notifications not supported');
            return false;
        }

        try {
            this.registration = await navigator.serviceWorker.register('/sw.js');
            console.log('Service Worker registered');
            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }

    async requestPermission() {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    async subscribe() {
        if (!this.registration) return false;

        try {
            const response = await fetch('/api/vapid-public-key');
            const { publicKey } = await response.json();

            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(publicKey)
            });

            await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: currentUser.user_id,
                    subscription: subscription
                })
            });

            return true;
        } catch (error) {
            console.error('Push subscription failed:', error);
            return false;
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
}

// Offline Support
class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.pendingRequests = [];
        this.setupEventListeners();
    }

    setupEventListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.processPendingRequests();
            showNotification('Připojení obnoveno', 'success');
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            showNotification('Offline režim', 'error');
        });
    }

    async makeRequest(url, options = {}) {
        if (this.isOnline) {
            try {
                return await fetch(url, options);
            } catch (error) {
                this.addToPendingRequests(url, options);
                throw error;
            }
        } else {
            this.addToPendingRequests(url, options);
            throw new Error('Offline - request queued');
        }
    }

    addToPendingRequests(url, options) {
        this.pendingRequests.push({ url, options, timestamp: Date.now() });
        localStorage.setItem('pendingRequests', JSON.stringify(this.pendingRequests));
    }

    async processPendingRequests() {
        const stored = localStorage.getItem('pendingRequests');
        if (stored) {
            this.pendingRequests = JSON.parse(stored);
        }

        for (const request of this.pendingRequests) {
            try {
                await fetch(request.url, request.options);
            } catch (error) {
                console.error('Failed to process pending request:', error);
            }
        }

        this.pendingRequests = [];
        localStorage.removeItem('pendingRequests');
    }
}

// Advanced Search Filters
class AdvancedSearch {
    constructor() {
        this.filters = {
            priceRange: { min: 0, max: 1000 },
            timeRange: { start: '00:00', end: '23:59' },
            rating: 0,
            verified: false,
            recurring: false,
            smoking: null,
            pets: null,
            carType: '',
            maxDetour: 10
        };
    }

    applyFilters(rides) {
        return rides.filter(ride => {
            // Price filter
            if (ride.price < this.filters.priceRange.min || ride.price > this.filters.priceRange.max) {
                return false;
            }

            // Time filter
            const rideTime = new Date(ride.departure_time).toTimeString().slice(0, 5);
            if (rideTime < this.filters.timeRange.start || rideTime > this.filters.timeRange.end) {
                return false;
            }

            // Rating filter
            if (ride.driver_rating < this.filters.rating) {
                return false;
            }

            // Verification filter
            if (this.filters.verified && !ride.driver_verified) {
                return false;
            }

            // Smoking filter
            if (this.filters.smoking !== null && ride.smoking_allowed !== this.filters.smoking) {
                return false;
            }

            // Pets filter
            if (this.filters.pets !== null && ride.pets_allowed !== this.filters.pets) {
                return false;
            }

            return true;
        });
    }

    saveFilters() {
        localStorage.setItem('searchFilters', JSON.stringify(this.filters));
    }

    loadFilters() {
        const saved = localStorage.getItem('searchFilters');
        if (saved) {
            this.filters = { ...this.filters, ...JSON.parse(saved) };
        }
    }
}

// Payment Integration
class PaymentManager {
    constructor() {
        this.stripe = null;
        this.elements = null;
        this.card = null;
    }

    async initialize() {
        if (typeof Stripe === 'undefined') {
            console.error('Stripe not loaded');
            return false;
        }

        try {
            const response = await fetch('/api/stripe-public-key');
            const { publicKey } = await response.json();
            
            this.stripe = Stripe(publicKey);
            this.elements = this.stripe.elements();
            
            this.card = this.elements.create('card');
            return true;
        } catch (error) {
            console.error('Stripe initialization failed:', error);
            return false;
        }
    }

    mountCard(elementId) {
        if (this.card) {
            this.card.mount(`#${elementId}`);
        }
    }

    async processPayment(bookingId, amount) {
        try {
            const response = await fetch('/api/payments/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ booking_id: bookingId, amount })
            });

            const { client_secret } = await response.json();

            const result = await this.stripe.confirmCardPayment(client_secret, {
                payment_method: {
                    card: this.card,
                    billing_details: {
                        name: currentUser.name
                    }
                }
            });

            if (result.error) {
                throw new Error(result.error.message);
            }

            return result.paymentIntent;
        } catch (error) {
            console.error('Payment failed:', error);
            throw error;
        }
    }
}

// Rating System
class RatingSystem {
    constructor() {
        this.currentRating = 0;
    }

    createRatingWidget(containerId, callback) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        for (let i = 1; i <= 5; i++) {
            const star = document.createElement('span');
            star.innerHTML = '☆';
            star.className = 'rating-star';
            star.style.cursor = 'pointer';
            star.style.fontSize = '24px';
            star.style.color = '#ddd';
            
            star.addEventListener('click', () => {
                this.currentRating = i;
                this.updateStars(container);
                if (callback) callback(i);
            });

            star.addEventListener('mouseover', () => {
                this.highlightStars(container, i);
            });

            container.appendChild(star);
        }

        container.addEventListener('mouseleave', () => {
            this.updateStars(container);
        });
    }

    highlightStars(container, rating) {
        const stars = container.querySelectorAll('.rating-star');
        stars.forEach((star, index) => {
            star.innerHTML = index < rating ? '★' : '☆';
            star.style.color = index < rating ? '#ff9800' : '#ddd';
        });
    }

    updateStars(container) {
        this.highlightStars(container, this.currentRating);
    }

    async submitRating(rideId, ratedUserId, rating, comment) {
        try {
            const response = await fetch('/api/ratings/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ride_id: rideId,
                    rater_id: currentUser.user_id,
                    rated_id: ratedUserId,
                    rating: rating,
                    comment: comment
                })
            });

            return response.ok;
        } catch (error) {
            console.error('Rating submission failed:', error);
            return false;
        }
    }
}

// Initialize enhanced features
const voiceMessage = new VoiceMessage();
const locationTracker = new LocationTracker();
const pushNotifications = new PushNotifications();
const offlineManager = new OfflineManager();
const advancedSearch = new AdvancedSearch();
const paymentManager = new PaymentManager();
const ratingSystem = new RatingSystem();

// Enhanced chat functions
function addVoiceMessageButton() {
    const chatInput = document.querySelector('.chat-input');
    if (!chatInput || chatInput.querySelector('.voice-btn')) return;

    const voiceBtn = document.createElement('button');
    voiceBtn.className = 'btn btn-secondary voice-btn';
    voiceBtn.innerHTML = '🎤';
    voiceBtn.style.marginLeft = '5px';
    
    voiceBtn.addEventListener('mousedown', () => {
        voiceMessage.startRecording();
        voiceBtn.innerHTML = '⏹️';
        voiceBtn.style.background = '#f44336';
    });

    voiceBtn.addEventListener('mouseup', () => {
        voiceMessage.stopRecording();
        voiceBtn.innerHTML = '🎤';
        voiceBtn.style.background = '#6c757d';
    });

    chatInput.appendChild(voiceBtn);
}

// Enhanced location sharing
function shareLocation() {
    if (locationTracker.currentPosition) {
        const message = `📍 Moje poloha: https://maps.google.com/?q=${locationTracker.currentPosition.lat},${locationTracker.currentPosition.lng}`;
        document.getElementById('chat-input').value = message;
        sendMessage();
    } else {
        showNotification('Poloha není dostupná', 'error');
    }
}

// Auto-translate messages
async function translateMessage(message, targetLang = 'cs') {
    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: message, target: targetLang })
        });
        
        const result = await response.json();
        return result.translatedText || message;
    } catch (error) {
        console.error('Translation failed:', error);
        return message;
    }
}

// Initialize enhanced features when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load saved search filters
    advancedSearch.loadFilters();
    
    // Initialize push notifications
    pushNotifications.initialize().then(success => {
        if (success) {
            pushNotifications.requestPermission();
        }
    });
    
    // Initialize payment system
    paymentManager.initialize();
    
    // Start location tracking if user is logged in
    if (currentUser) {
        locationTracker.startTracking();
    }
});

// Export functions for global use
window.enhancedFeatures = {
    voiceMessage,
    locationTracker,
    pushNotifications,
    offlineManager,
    advancedSearch,
    paymentManager,
    ratingSystem,
    addVoiceMessageButton,
    shareLocation,
    translateMessage
};