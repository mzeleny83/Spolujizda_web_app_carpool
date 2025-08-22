(function() {
// Integrace pokročilého vyhledávání do webové aplikace
class SearchIntegration {
    constructor() {
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
        
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'search-results-container';
        resultsContainer.style.display = 'none';
        wrapper.appendChild(resultsContainer);
        
        let debounceTimer;
        
        field.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                if (e.target.value.trim().length > 0) {
                    this.performSearch(e.target.value, searchType, resultsContainer, field);
                } else {
                    resultsContainer.style.display = 'none';
                }
            }, 300);
        });
        
        field.addEventListener('focus', () => {
            if (field.value.trim() === '') {
                this.showSuggestions(resultsContainer, searchType, field);
            }
        });
        
        field.addEventListener('blur', (e) => {
            setTimeout(() => {
                resultsContainer.style.display = 'none';
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

            const response = await fetch(`/api/rides/search?from=${query}`);
            
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
        
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\\]/g, '\\$&')})`, 'gi');
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
const searchStyles = `
<style>
.advanced-search-wrapper {
    position: relative;
    width: 100%;
}

.search-results-container {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    max-height: 300px;
    overflow-y: auto;
    z-index: 1000;
    margin-top: 4px;
}

.search-result-item {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.2s;
}

.search-result-item:hover {
    background-color: #f8f9fa;
}

.search-result-item:last-child {
    border-bottom: none;
}

.search-result-icon {
    font-size: 18px;
    margin-right: 12px;
    width: 20px;
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
    font-size: 12px;
    color: #666;
    margin-top: 2px;
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

if (!document.querySelector('#search-integration-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'search-integration-styles';
    styleElement.innerHTML = searchStyles;
    document.head.appendChild(styleElement);
}

document.addEventListener('DOMContentLoaded', () => {
    window.searchIntegration = new SearchIntegration();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchIntegration;
}
})();