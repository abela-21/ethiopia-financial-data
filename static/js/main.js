// Ethiopia Capital Market Platform - Main JavaScript

// Global Configuration
const CONFIG = {
    API_BASE_URL: '/api',
    CACHE_DURATION: 300000, // 5 minutes
    DEBOUNCE_DELAY: 300,
    ANIMATION_DURATION: 300,
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000
};

// Cache Management
class SimpleCache {
    constructor() {
        this.cache = new Map();
        this.timestamps = new Map();
    }

    set(key, value, duration = CONFIG.CACHE_DURATION) {
        this.cache.set(key, value);
        this.timestamps.set(key, Date.now() + duration);
    }

    get(key) {
        const timestamp = this.timestamps.get(key);
        if (timestamp && Date.now() < timestamp) {
            return this.cache.get(key);
        }
        this.delete(key);
        return null;
    }

    delete(key) {
        this.cache.delete(key);
        this.timestamps.delete(key);
    }

    clear() {
        this.cache.clear();
        this.timestamps.clear();
    }
}

// Global cache instance
const cache = new SimpleCache();

// Utility Functions
const Utils = {
    // Debounce function for search and input handling
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle function for scroll events
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Format numbers with commas
    formatNumber(num, decimals = 0) {
        if (num === null || num === undefined || isNaN(num)) return 'N/A';
        return Number(num).toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },

    // Format currency
    formatCurrency(amount, currency = 'ETB', decimals = 2) {
        if (amount === null || amount === undefined || isNaN(amount)) return 'N/A';
        return `${this.formatNumber(amount, decimals)} ${currency}`;
    },

    // Format percentage
    formatPercentage(value, decimals = 1) {
        if (value === null || value === undefined || isNaN(value)) return 'N/A';
        const sign = value >= 0 ? '+' : '';
        return `${sign}${this.formatNumber(value, decimals)}%`;
    },

    // Format large numbers (K, M, B)
    formatLargeNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return 'N/A';
        
        const absNum = Math.abs(num);
        if (absNum >= 1e9) {
            return `${(num / 1e9).toFixed(1)}B`;
        } else if (absNum >= 1e6) {
            return `${(num / 1e6).toFixed(1)}M`;
        } else if (absNum >= 1e3) {
            return `${(num / 1e3).toFixed(1)}K`;
        }
        return this.formatNumber(num);
    },

    // Format date
    formatDate(dateString, options = {}) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                ...options
            });
        } catch (error) {
            console.error('Date formatting error:', error);
            return 'Invalid Date';
        }
    },

    // Truncate text
    truncateText(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    },

    // Get color for change values
    getChangeColor(value) {
        if (value > 0) return 'text-success';
        if (value < 0) return 'text-danger';
        return 'text-muted';
    },

    // Validate email
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Generate random ID
    generateId() {
        return Math.random().toString(36).substring(2, 15);
    }
};

// API Helper Class
class APIClient {
    constructor(baseURL = CONFIG.API_BASE_URL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${url}`, error);
            throw error;
        }
    }

    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url);
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Global API client
const api = new APIClient();

// Loading Manager
class LoadingManager {
    constructor() {
        this.loadingElements = new Set();
    }

    show(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('loading-shimmer');
            this.loadingElements.add(elementId);
        }
    }

    hide(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('loading-shimmer');
            this.loadingElements.delete(elementId);
        }
    }

    showSpinner(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="text-muted mt-2">${message}</p>
                </div>
            `;
        }
    }

    showError(containerId, message = 'Data temporarily unavailable', details = null) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="alert alert-warning border-0 shadow-sm" role="alert">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-info-circle text-warning me-3"></i>
                        <div>
                            <h6 class="alert-heading mb-1">Information Notice</h6>
                            <p class="mb-0">${message}</p>
                            ${details ? `<small class="text-muted">${details}</small>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }
    }

    hideAll() {
        this.loadingElements.forEach(elementId => this.hide(elementId));
        this.loadingElements.clear();
    }
}

// Global loading manager
const loadingManager = new LoadingManager();

// Notification System
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        this.container.appendChild(notification);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }

        return notification;
    }

    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'danger', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

// Global notification manager
const notifications = new NotificationManager();

// Search Functionality
class SearchManager {
    constructor() {
        this.initializeSearch();
    }

    initializeSearch() {
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            this.setupSearchInput(searchInput);
        }
    }

    setupSearchInput(input) {
        const debouncedSearch = Utils.debounce(this.performSearch.bind(this), CONFIG.DEBOUNCE_DELAY);
        
        input.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                debouncedSearch(query);
            } else {
                this.hideSearchResults();
            }
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target)) {
                this.hideSearchResults();
            }
        });
    }

    async performSearch(query) {
        try {
            const cacheKey = `search_${query}`;
            let results = cache.get(cacheKey);

            if (!results) {
                results = await api.get('/search/companies', { q: query, limit: 5 });
                cache.set(cacheKey, results);
            }

            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
            this.hideSearchResults();
        }
    }

    displaySearchResults(results) {
        const searchContainer = document.querySelector('.search-container');
        if (!searchContainer) return;

        let resultsContainer = searchContainer.querySelector('.search-results');
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.className = 'search-results';
            searchContainer.appendChild(resultsContainer);
        }

        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="search-result-item text-muted">
                    <i class="fas fa-search me-2"></i>No results found
                </div>
            `;
        } else {
            resultsContainer.innerHTML = results.map(company => `
                <div class="search-result-item" onclick="window.location.href='/companies/${company.id}'">
                    <div class="fw-bold">${company.name}</div>
                    <div class="small text-muted">${company.ticker} • ${company.industry}</div>
                </div>
            `).join('');
        }

        resultsContainer.style.display = 'block';
    }

    hideSearchResults() {
        const resultsContainer = document.querySelector('.search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }
}

// Form Validation
class FormValidator {
    constructor() {
        this.initializeForms();
    }

    initializeForms() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => this.setupFormValidation(form));
    }

    setupFormValidation(form) {
        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    this.validateField(input);
                }
            });
        });
    }

    validateForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (required && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Type-specific validation
        if (value && isValid) {
            switch (type) {
                case 'email':
                    if (!Utils.isValidEmail(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid email address';
                    }
                    break;
                case 'password':
                    if (value.length < 6) {
                        isValid = false;
                        errorMessage = 'Password must be at least 6 characters long';
                    }
                    break;
                case 'number':
                    if (isNaN(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid number';
                    }
                    break;
            }
        }

        // Custom validation
        const customValidator = field.getAttribute('data-validator');
        if (customValidator && window[customValidator]) {
            const customResult = window[customValidator](value);
            if (!customResult.valid) {
                isValid = false;
                errorMessage = customResult.message;
            }
        }

        // Update field state
        this.updateFieldState(field, isValid, errorMessage);
        return isValid;
    }

    updateFieldState(field, isValid, errorMessage) {
        const feedbackElement = field.parentNode.querySelector('.invalid-feedback') || 
                               field.parentNode.querySelector('.error-message');

        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            if (feedbackElement) {
                feedbackElement.style.display = 'none';
            }
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            if (feedbackElement) {
                feedbackElement.textContent = errorMessage;
                feedbackElement.style.display = 'block';
            }
        }
    }
}

// Back to Top Button
class BackToTopButton {
    constructor() {
        this.button = document.getElementById('backToTop');
        if (this.button) {
            this.initialize();
        }
    }

    initialize() {
        // Show/hide button based on scroll position
        const toggleButton = Utils.throttle(() => {
            if (window.pageYOffset > 300) {
                this.button.style.display = 'flex';
            } else {
                this.button.style.display = 'none';
            }
        }, 100);

        window.addEventListener('scroll', toggleButton);

        // Smooth scroll to top
        this.button.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Ethiopia Capital Market Platform - Initializing...');

    // Initialize components
    new SearchManager();
    new FormValidator();
    new BackToTopButton();

    // Initialize Bootstrap tooltips and popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            if (alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    console.log('Ethiopia Capital Market Platform - Initialized successfully');
});

// Export utilities for global use
window.Utils = Utils;
window.api = api;
window.cache = cache;
window.notifications = notifications;
window.loadingManager = loadingManager;

// Handle global errors
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    notifications.error('An unexpected error occurred. Please try again.');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    notifications.error('A network error occurred. Please check your connection.');
});
