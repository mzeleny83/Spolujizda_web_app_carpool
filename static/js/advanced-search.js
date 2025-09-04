(function() {
// Pokročilý vyhledávací systém inspirovaný Waze
class AdvancedSearch {
    constructor() {
        this.searchCache = new Map();
        this.userLocation = null;
        this.searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        this.popularDestinations = [];
        this.debounceTimer = null;
        this.currentSearchId = 0;
        
        this.initializeGeolocation();
        this.loadPopularDestinations();
    }

    // Inicializace geolokace
    async initializeGeolocation() {
        if (navigator.geolocation) {
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 300000
                    });
                });
                
                this.userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };
                
                console.log('Geolokace získána:', this.userLocation);
            } catch (error) {
                console.warn('Geolokace nedostupná:', error);
            }
        }
    }

    // Načtení populárních destinací
    async loadPopularDestinations() {
        try {
            const response = await fetch('/api/search/popular');
            if (response.ok) {
                this.popularDestinations = await response.json();
            }
        } catch (error) {
            console.warn('Nepodařilo se načíst populární destinace:', error);
        }
    }

    // Hlavní vyhledávací funkce s debouncing
    search(query, inputElement, resultsContainer, options = {}) {
        clearTimeout(this.debounceTimer);
        
        const searchId = ++this.currentSearchId;
        
        this.debounceTimer = setTimeout(async () => {
            if (searchId !== this.currentSearchId) return; // Zrušeno novějším hledáním
            
            await this.performSearch(query, inputElement, resultsContainer, options);
        }, options.debounceMs || 300);
    }

    // Provedení vyhledávání
    async performSearch(query, inputElement, resultsContainer, options = {}) {
        const trimmedQuery = query.trim();
        
        if (trimmedQuery.length < 2) {
            this.showSuggestions(inputElement, resultsContainer, options);
            return;
        }

        // Kontrola cache
        const cacheKey = `${trimmedQuery}_${this.userLocation?.lat}_${this.userLocation?.lng}`;
        if (this.searchCache.has(cacheKey)) {
            this.displayResults(this.searchCache.get(cacheKey), resultsContainer, options);
            return;
        }

        try {
            resultsContainer.innerHTML = '<div class="search-loading">🔍 Hledám...</div>';
            
            const results = await this.performMultiSearch(trimmedQuery, options);
            
            // Uložení do cache
            this.searchCache.set(cacheKey, results);
            
            this.displayResults(results, resultsContainer, options);
            
        } catch (error) {
            console.error('Chyba při vyhledávání:', error);
            resultsContainer.innerHTML = '<div class="search-error">❌ Chyba při vyhledávání</div>';
        }
    }

    // Multi-source vyhledávání
    async performMultiSearch(query, options) {
        const searches = [];
        
        // 1. Vyhledávání míst
        searches.push(this.searchPlaces(query));
        
        // 2. Vyhledávání jízd
        if (options.includeRides !== false) {
            searches.push(this.searchRides(query));
        }
        
        // 3. Vyhledávání uživatelů
        if (options.includeUsers !== false) {
            searches.push(this.searchUsers(query));
        }
        
        // 4. Fuzzy matching v historii
        searches.push(this.searchHistory.filter(item => 
            this.fuzzyMatch(query, item.text)
        ).map(item => ({...item, type: 'history'})));

        const results = await Promise.all(searches);
        
        return this.mergeAndRankResults(results.flat(), query);
    }

    // Vyhledávání míst pomocí Google Places API
    async searchPlaces(query) {
        if (!window.google?.maps?.places) {
            return this.searchPlacesLocal(query);
        }

        return new Promise((resolve) => {
            const service = new google.maps.places.AutocompleteService();
            
            const request = {
                input: query,
                location: this.userLocation ? 
                    new google.maps.LatLng(this.userLocation.lat, this.userLocation.lng) : null,
                radius: 50000, // 50km
                language: 'cs',
                componentRestrictions: { country: 'cz' }
            };

            service.getPlacePredictions(request, (predictions, status) => {
                if (status === google.maps.places.PlacesServiceStatus.OK && predictions) {
                    const results = predictions.map(prediction => ({
                        id: prediction.place_id,
                        text: prediction.description,
                        type: 'place',
                        icon: '📍',
                        distance: this.calculateDistance(prediction),
                        confidence: this.calculateConfidence(query, prediction.description)
                    }));
                    resolve(results);
                } else {
                    resolve([]);
                }
            });
        });
    }

    // Lokální vyhledávání míst (fallback)
    async searchPlacesLocal(query) {
        const czechCities = [
            'Praha', 'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Olomouc', 'Ústí nad Labem',
            'České Budějovice', 'Hradec Králové', 'Pardubice', 'Zlín', 'Havířov',
            'Kladno', 'Most', 'Opava', 'Frýdek-Místek', 'Karviná', 'Jihlava'
        ];

        return czechCities
            .filter(city => this.fuzzyMatch(query, city))
            .map(city => ({
                id: city.toLowerCase(),
                text: city,
                type: 'place',
                icon: '🏙️',
                confidence: this.calculateTextConfidence(query, city)
            }));
    }

    // Vyhledávání jízd
    async searchRides(query) {
        try {
            const params = new URLSearchParams({
                q: query,
                lat: this.userLocation?.lat || 0,
                lng: this.userLocation?.lng || 0,
                limit: 10,
                timestamp: new Date().getTime()
            });

            const response = await fetch(`/api/rides/search-text?${params}`);
            if (!response.ok) return [];

            const rides = await response.json();
            
            return rides.map(ride => ({
                id: `ride_${ride.id}`,
                text: `${ride.from_location} → ${ride.to_location}`,
                subtitle: `${ride.departure_time} • ${ride.driver_name} • ${ride.price_per_person} Kč`,
                type: 'ride',
                icon: '🚗',
                data: ride,
                confidence: this.calculateTextConfidence(query, `${ride.from_location} ${ride.to_location}`)
            }));
        } catch (error) {
            console.error('Chyba při hledání jízd:', error);
            return [];
        }
    }

    // Vyhledávání uživatelů
    async searchUsers(query) {
        try {
            const response = await fetch('/api/users/search-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            if (!response.ok) return [];

            const users = await response.json();
            
            return users.map(user => ({
                id: `user_${user.id}`,
                text: user.name,
                subtitle: `⭐ ${user.rating.toFixed(1)} • ${user.phone}`,
                type: 'user',
                icon: '👤',
                data: user,
                confidence: this.calculateTextConfidence(query, user.name)
            }));
        } catch (error) {
            console.error('Chyba při hledání uživatelů:', error);
            return [];
        }
    }

    // Fuzzy matching algoritmus
    fuzzyMatch(query, text, threshold = 0.6) {
        const similarity = this.calculateSimilarity(query.toLowerCase(), text.toLowerCase());
        return similarity >= threshold;
    }

    // Výpočet podobnosti řetězců (Levenshtein distance)
    calculateSimilarity(str1, str2) {
        const matrix = [];
        const len1 = str1.length;
        const len2 = str2.length;

        for (let i = 0; i <= len2; i++) {
            matrix[i] = [i];
        }

        for (let j = 0; j <= len1; j++) {
            matrix[0][j] = j;
        }

        for (let i = 1; i <= len2; i++) {
            for (let j = 1; j <= len1; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }

        const maxLen = Math.max(len1, len2);
        return maxLen === 0 ? 1 : (maxLen - matrix[len2][len1]) / maxLen;
    }

    // Výpočet textové confidence
    calculateTextConfidence(query, text) {
        const similarity = this.calculateSimilarity(query.toLowerCase(), text.toLowerCase());
        const startsWithBonus = text.toLowerCase().startsWith(query.toLowerCase()) ? 0.2 : 0;
        const containsBonus = text.toLowerCase().includes(query.toLowerCase()) ? 0.1 : 0;
        
        return Math.min(1, similarity + startsWithBonus + containsBonus);
    }

    // Sloučení a seřazení výsledků
    mergeAndRankResults(results, query) {
        // Odstranění duplicit
        const uniqueResults = results.filter((result, index, self) => 
            index === self.findIndex(r => r.id === result.id)
        );

        // Seřazení podle confidence a typu
        return uniqueResults.sort((a, b) => {
            // Priorita podle typu
            const typeOrder = { history: 0, place: 1, ride: 2, user: 3 };
            const typeDiff = (typeOrder[a.type] || 99) - (typeOrder[b.type] || 99);
            
            if (typeDiff !== 0) return typeDiff;
            
            // Seřazení podle confidence
            return (b.confidence || 0) - (a.confidence || 0);
        }).slice(0, 10); // Maximálně 10 výsledků
    }

    // Zobrazení návrhů (když není zadán dotaz)
    showSuggestions(inputElement, resultsContainer, options) {
        const suggestions = [];
        
        // Historie hledání
        suggestions.push(...this.searchHistory.slice(0, 3).map(item => ({
            ...item,
            type: 'history',
            icon: '🕒'
        })));
        
        // Populární destinace
        suggestions.push(...this.popularDestinations.slice(0, 3).map(dest => ({
            id: dest.id,
            text: dest.name,
            type: 'popular',
            icon: '🔥'
        })));
        
        // Rychlé akce
        if (this.userLocation) {
            suggestions.push({
                id: 'current_location',
                text: 'Moje poloha',
                type: 'location',
                icon: '📍'
            });
        }

        this.displayResults(suggestions, resultsContainer, options);
    }

    // Zobrazení výsledků
    displayResults(results, container, options) {
        if (results.length === 0) {
            container.innerHTML = '<div class="search-no-results">🔍 Žádné výsledky</div>';
            return;
        }

        const html = results.map(result => `
            <div class="search-result" data-id="${result.id}" data-type="${result.type}">
                <div class="search-result-icon">${result.icon}</div>
                <div class="search-result-content">
                    <div class="search-result-text">${this.highlightQuery(result.text, options.query || '')}</div>
                    ${result.subtitle ? `<div class="search-result-subtitle">${result.subtitle}</div>` : ''}
                </div>
                ${result.distance ? `<div class="search-result-distance">${result.distance}</div>` : ''}
            </div>
        `).join('');

        container.innerHTML = html;

        // Přidání event listenerů
        container.querySelectorAll('.search-result').forEach(element => {
            element.addEventListener('click', () => {
                const result = results.find(r => r.id === element.dataset.id);
                this.selectResult(result, options);
            });
        });
    }

    // Zvýraznění hledaného textu
    highlightQuery(text, query) {
        if (!query || query.length < 2) return text;
        
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    // Výběr výsledku
    selectResult(result, options) {
        // Uložení do historie
        this.addToHistory(result);
        
        // Callback
        if (options.onSelect) {
            options.onSelect(result);
        }
        
        // Výchozí akce podle typu
        switch (result.type) {
            case 'place':
                this.selectPlace(result);
                break;
            case 'ride':
                this.selectRide(result);
                break;
            case 'user':
                this.selectUser(result);
                break;
            case 'location':
                this.selectCurrentLocation();
                break;
        }
    }

    // Výběr místa
    selectPlace(result) {
        console.log('Vybráno místo:', result);
        // Implementace podle potřeby
    }

    // Výběr jízdy
    selectRide(result) {
        console.log('Vybrána jízda:', result);
        if (result.data) {
            window.location.href = `/ride/${result.data.id}`;
        }
    }

    // Výběr uživatele
    selectUser(result) {
        console.log('Vybrán uživatel:', result);
        if (result.data) {
            window.location.href = `/user/${result.data.id}`;
        }
    }

    // Výběr současné polohy
    selectCurrentLocation() {
        if (this.userLocation) {
            console.log('Vybrána současná poloha:', this.userLocation);
        }
    }

    // Přidání do historie
    addToHistory(result) {
        const historyItem = {
            id: result.id,
            text: result.text,
            type: result.type,
            timestamp: Date.now()
        };

        // Odstranění duplicit
        this.searchHistory = this.searchHistory.filter(item => item.id !== result.id);
        
        // Přidání na začátek
        this.searchHistory.unshift(historyItem);
        
        // Omezení na 20 položek
        this.searchHistory = this.searchHistory.slice(0, 20);
        
        // Uložení do localStorage
        localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
    }

    // Výpočet vzdálenosti (zjednodušený)
    calculateDistance(prediction) {
        if (!this.userLocation) return null;
        
        // Toto by mělo být implementováno s skutečnými souřadnicemi
        return Math.floor(Math.random() * 50) + ' km';
    }
}

// Globální instance
window.advancedSearch = new AdvancedSearch();

// CSS styly
const advancedSearchStyles = `
<style>
.search-container {
    position: relative;
    width: 100%;
}

.search-input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s;
}

.search-input:focus {
    outline: none;
    border-color: #007bff;
}

.search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    max-height: 400px;
    overflow-y: auto;
    z-index: 1000;
}

.search-result {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.2s;
}

.search-result:hover {
    background-color: #f8f9fa;
}

.search-result:last-child {
    border-bottom: none;
}

.search-result-icon {
    font-size: 20px;
    margin-right: 12px;
    width: 24px;
    text-align: center;
}

.search-result-content {
    flex: 1;
}

.search-result-text {
    font-weight: 500;
    color: #333;
}

.search-result-subtitle {
    font-size: 14px;
    color: #666;
    margin-top: 2px;
}

.search-result-distance {
    font-size: 12px;
    color: #999;
}

.search-loading, .search-error, .search-no-results {
    padding: 16px;
    text-align: center;
    color: #666;
}

.search-error {
    color: #dc3545;
}

mark {
    background-color: #fff3cd;
    padding: 0 2px;
    border-radius: 2px;
}
</style>
`;

// Přidání stylů do hlavy dokumentu
if (!document.querySelector('#advanced-search-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'advanced-search-styles';
    styleElement.innerHTML = advancedSearchStyles;
    document.head.appendChild(styleElement);
}
})();