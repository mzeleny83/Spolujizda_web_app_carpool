(function() {
// Integrace pokročilého vyhledávání do webové aplikace
class SearchIntegration {
    constructor() {
        this.resultsContainer = document.getElementById('results'); // Get the existing results div
        this.initializeSearchFields();
        this.setupEventListeners();
    }

    initializeSearchFields() {
        this.searchFields = document.querySelectorAll('[data-search-type]');
        
        this.searchFields.forEach(field => {
            this.enhanceSearchField(field);
        });
    }

    enhanceSearchField(field) {
        const searchType = field.dataset.searchType;
        const wrapper = document.createElement('div');
        wrapper.className = 'advanced-search-wrapper';
        
        field.parentNode.insertBefore(wrapper, field);
        wrapper.appendChild(field);
        
        // Removed: Creation of new resultsContainer
        // resultsContainer.style.display = 'none'; // This line is no longer needed here
        // wrapper.appendChild(resultsContainer); // This line is no longer needed here
        
        let debounceTimer;
        
        field.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                if (e.target.value.trim().length > 0) {
                    this.performSearch(e.target.value, searchType, this.resultsContainer, field); // Pass this.resultsContainer
                } else {
                    this.resultsContainer.style.display = 'none'; // Hide the results container
                }
            }, 300);
        });
        
        field.addEventListener('focus', () => {
            if (field.value.trim() === '') {
                this.showSuggestions(this.resultsContainer, searchType, field); // Pass this.resultsContainer
            }
        });
        
        field.addEventListener('blur', (e) => {
            setTimeout(() => {
                this.resultsContainer.style.display = 'none'; // Hide the results container
            }, 200);
        });
    }

    async performSearch(query, searchType, container, field) {
        if (query.trim().length < 2) {
            this.showSuggestions(container, searchType, field);
            return;
        }

        try {
            container.innerHTML = '<div class="search-loading">🔍 Hledám...</div>';
            container.style.display = 'block';

            const params = new URLSearchParams({
                q: query,
                limit: 8
            });

            if (searchType === 'places') {
                params.append('places', 'true');
                params.append('rides', 'false');
                params.append('users', 'false');
            }

            const response = await fetch(`/api/search/unified?${params}`);
            
            if (!response.ok) {
                throw new Error('Chyba při vyhledávání');
            }

            const results = await response.json();
            this.displayResults(results, container, field, query);

        } catch (error) {
            console.error('Chyba při vyhledávání:', error);
            container.innerHTML = '<div class="search-error">❌ Chyba při vyhledávání</div>';
        }
    }

    async showSuggestions(container, searchType, field) {
        try {
            const response = await fetch('/api/search/popular?limit=5');
            const suggestions = await response.json();
            
            const quickActions = [];
            
            if (searchType === 'places') {
                quickActions.push({
                    id: 'current_location',
                    text: 'Moje poloha',
                    icon: '📍',
                    type: 'location'
                });
            }

            const allSuggestions = [...quickActions, ...suggestions];
            this.displayResults(allSuggestions, container, field, '');
            container.style.display = 'block';

        } catch (error) {
            console.error('Chyba při načítání návrhů:', error);
        }
    }

    displayResults(results, container, field, query) {
        if (results.length === 0) {
            container.innerHTML = '<div class="search-no-results">🔍 Žádné výsledky</div>';
            return;
        }

        const html = results.map(result => `
            <div class="search-result-item" data-id="${result.id}" data-type="${result.type}">
                <div class="search-result-icon">${result.icon}</div>
                <div class="search-result-content">
                    <div class="search-result-text">${this.highlightQuery(result.text, query)}</div>
                    ${result.subtitle ? `<div class="search-result-subtitle">${result.subtitle}</div>` : ''}
                </div>
            </div>
        `).join('');

        container.innerHTML = html;

        container.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const result = results.find(r => r.id === item.dataset.id);
                this.selectResult(result, field, container);
            });
        });
    }

    highlightQuery(text, query) {
        if (!query || query.length < 2) return text;
        
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    selectResult(result, field, container) {
        // Nastaví hodnotu bez spuštění dalších událostí
        field.value = result.text;
        container.style.display = 'none';
        
        // Označí pole jako vyplněné uživatelem
        field.setAttribute('data-user-filled', 'true');
        
        field.dispatchEvent(new CustomEvent('searchResultSelected', {
            detail: { result, field }
        }));
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const firstSearchField = document.querySelector('[data-search-type]');
                if (firstSearchField) {
                    firstSearchField.focus();
                }
            }
        });
    }
}

// CSS styly
const integrationSearchStyles = `
`;

if (!document.querySelector('#search-integration-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'search-integration-styles';
    styleElement.innerHTML = integrationSearchStyles;
    document.head.appendChild(styleElement);
}

document.addEventListener('DOMContentLoaded', () => {
    window.searchIntegration = new SearchIntegration();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchIntegration;
}
})();