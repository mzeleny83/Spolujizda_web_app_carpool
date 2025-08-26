// GDPR Cookie Consent
class CookieConsent {
    constructor() {
        this.init();
    }

    init() {
        if (!this.hasConsent()) {
            this.showBanner();
        }
    }

    hasConsent() {
        return localStorage.getItem('cookie_consent') === 'accepted';
    }

    showBanner() {
        const banner = document.createElement('div');
        banner.id = 'cookie-banner';
        banner.innerHTML = `
            <div style="position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 15px; z-index: 10000; text-align: center;">
                <p style="margin: 0 0 10px 0;">
                    Používáme cookies pro správné fungování aplikace. 
                    <a href="/privacy" style="color: #007bff;">Více informací</a>
                </p>
                <button onclick="cookieConsent.accept()" style="background: #007bff; color: white; border: none; padding: 8px 16px; margin: 0 5px; border-radius: 4px; cursor: pointer;">
                    Rozumím
                </button>
            </div>
        `;
        document.body.appendChild(banner);
    }

    accept() {
        localStorage.setItem('cookie_consent', 'accepted');
        localStorage.setItem('analytics_consent', 'true');
        this.hideBanner();
        this.loadAnalytics();
    }

    acceptNecessary() {
        localStorage.setItem('cookie_consent', 'accepted');
        localStorage.setItem('analytics_consent', 'false');
        this.hideBanner();
    }

    hideBanner() {
        const banner = document.getElementById('cookie-banner');
        if (banner) {
            banner.remove();
        }
    }

    loadAnalytics() {
        if (localStorage.getItem('analytics_consent') === 'true') {
            // Zde by se načetly analytické skripty
            console.log('Analytics loaded');
        }
    }
}

// Inicializace při načtení stránky
const cookieConsent = new CookieConsent();