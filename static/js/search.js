/**
 * Advanced Search & Filtering JavaScript
 * Handles complex company search with multiple filter criteria
 */

class AdvancedSearch {
    constructor() {
        this.searchResults = [];
        this.currentPage = 1;
        this.pageSize = 10;
        this.selectedCompanies = new Set();
        this.savedSearches = JSON.parse(localStorage.getItem('savedSearches') || '[]');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSavedSearches();
        this.setupMultiSelect();
        this.initializeDateRanges();
    }

    setupEventListeners() {
        // Search form submission
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });

        // Real-time search on input
        document.getElementById('searchQuery').addEventListener('input', 
            this.debounce(() => this.performSearch(), 500)
        );

        // Filter changes
        ['sectorFilter', 'marketCapMin', 'marketCapMax', 'roaMin', 'roaMax', 
         'revenueMin', 'revenueMax', 'assetMin', 'assetMax', 'dateFrom', 'dateTo',
         'topPerformers', 'growthCompanies', 'undervaluedCompanies'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.performSearch());
            }
        });

        // Market cap range slider
        document.getElementById('marketCapRange').addEventListener('input', (e) => {
            this.updateMarketCapRange(e.target.value);
        });

        // View toggles
        document.getElementById('gridView').addEventListener('click', () => this.toggleView('grid'));
        document.getElementById('listView').addEventListener('click', () => this.toggleView('list'));

        // Sort change
        document.getElementById('sortBy').addEventListener('change', () => this.sortResults());

        // Custom metric rules
        document.getElementById('addMetricRule').addEventListener('click', () => this.addMetricRule());

        // Clear filters
        document.getElementById('clearFilters').addEventListener('click', () => this.clearAllFilters());

        // Save search
        document.getElementById('saveSearch').addEventListener('click', () => this.showSaveSearchModal());
        document.getElementById('confirmSaveSearch').addEventListener('click', () => this.saveCurrentSearch());

        // Bulk actions
        document.getElementById('addToWatchlist').addEventListener('click', () => this.addSelectedToWatchlist());
        document.getElementById('compareSelected').addEventListener('click', () => this.compareSelected());
        document.getElementById('exportSelected').addEventListener('click', () => this.exportSelected());
    }

    setupMultiSelect() {
        // Initialize multi-select for sectors
        const sectorSelect = document.getElementById('sectorFilter');
        if (sectorSelect) {
            // Simple multi-select handling
            sectorSelect.addEventListener('change', () => {
                this.performSearch();
            });
        }
    }

    initializeDateRanges() {
        const today = new Date();
        const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
        
        document.getElementById('dateFrom').value = oneYearAgo.toISOString().split('T')[0];
        document.getElementById('dateTo').value = today.toISOString().split('T')[0];
    }

    updateMarketCapRange(value) {
        const maxValue = 50000000000;
        const percentage = (value / maxValue) * 100;
        
        // Update visual feedback
        const slider = document.getElementById('marketCapRange');
        slider.style.background = `linear-gradient(to right, #007bff 0%, #007bff ${percentage}%, #ddd ${percentage}%, #ddd 100%)`;
        
        // Update min/max inputs if they're empty
        if (!document.getElementById('marketCapMax').value) {
            document.getElementById('marketCapMax').value = value;
        }
    }

    async performSearch() {
        const filters = this.collectFilters();
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/search/companies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filters)
            });

            if (!response.ok) {
                throw new Error('Search failed');
            }

            const data = await response.json();
            this.searchResults = data.companies || [];
            this.displayResults();
            this.updateSearchStats(data);

        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    collectFilters() {
        const filters = {
            query: document.getElementById('searchQuery').value.trim(),
            sectors: this.getSelectedSectors(),
            market_cap: {
                min: this.parseNumber(document.getElementById('marketCapMin').value),
                max: this.parseNumber(document.getElementById('marketCapMax').value)
            },
            metrics: {
                roa: {
                    min: this.parseNumber(document.getElementById('roaMin').value),
                    max: this.parseNumber(document.getElementById('roaMax').value)
                },
                revenue: {
                    min: this.parseNumber(document.getElementById('revenueMin').value),
                    max: this.parseNumber(document.getElementById('revenueMax').value)
                },
                assets: {
                    min: this.parseNumber(document.getElementById('assetMin').value),
                    max: this.parseNumber(document.getElementById('assetMax').value)
                }
            },
            date_range: {
                from: document.getElementById('dateFrom').value,
                to: document.getElementById('dateTo').value
            },
            performance_filters: {
                top_performers: document.getElementById('topPerformers').checked,
                growth_companies: document.getElementById('growthCompanies').checked,
                undervalued: document.getElementById('undervaluedCompanies').checked
            },
            custom_metrics: this.collectCustomMetrics(),
            page: this.currentPage,
            page_size: this.pageSize,
            sort_by: document.getElementById('sortBy').value
        };

        return filters;
    }

    getSelectedSectors() {
        const sectorSelect = document.getElementById('sectorFilter');
        const selected = [];
        for (let option of sectorSelect.selectedOptions) {
            if (option.value) {
                selected.push(option.value);
            }
        }
        return selected;
    }

    collectCustomMetrics() {
        const rules = [];
        const metricRules = document.querySelectorAll('#customMetrics .metric-rule');
        
        metricRules.forEach(rule => {
            const metricName = rule.querySelector('select[name="metricName[]"]').value;
            const operator = rule.querySelector('select[name="operator[]"]').value;
            const value = rule.querySelector('input[name="value[]"]').value;
            
            if (metricName && operator && value) {
                rules.push({
                    metric: metricName,
                    operator: operator,
                    value: parseFloat(value)
                });
            }
        });
        
        return rules;
    }

    parseNumber(value) {
        return value && value.trim() ? parseFloat(value) : null;
    }

    displayResults() {
        const container = document.getElementById('searchResults');
        const viewMode = document.querySelector('#listView.active') ? 'list' : 'grid';
        
        if (this.searchResults.length === 0) {
            container.innerHTML = this.getNoResultsHTML();
            return;
        }

        if (viewMode === 'grid') {
            container.innerHTML = this.renderGridView();
        } else {
            container.innerHTML = this.renderListView();
        }

        this.setupResultInteractions();
        this.updatePagination();
    }

    renderListView() {
        return `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>
                                <input type="checkbox" id="selectAll" class="form-check-input">
                            </th>
                            <th>Company</th>
                            <th>Sector</th>
                            <th>Market Cap</th>
                            <th>Revenue</th>
                            <th>Assets</th>
                            <th>Performance</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.searchResults.map(company => this.renderCompanyRow(company)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderCompanyRow(company) {
        const isSelected = this.selectedCompanies.has(company.id);
        const performanceClass = this.getPerformanceClass(company.performance_score);
        
        return `
            <tr class="${isSelected ? 'table-primary' : ''}">
                <td>
                    <input type="checkbox" class="form-check-input company-select" 
                           value="${company.id}" ${isSelected ? 'checked' : ''}>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="company-logo me-2">
                            <i class="fas fa-building text-primary"></i>
                        </div>
                        <div>
                            <div class="fw-bold">${company.name}</div>
                            <small class="text-muted">${company.ticker_symbol}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge bg-secondary">${company.sector}</span>
                </td>
                <td>${this.formatCurrency(company.market_cap)}</td>
                <td>${this.formatCurrency(company.total_revenue)}</td>
                <td>${this.formatCurrency(company.total_assets)}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="progress me-2" style="width: 60px; height: 8px;">
                            <div class="progress-bar ${performanceClass}" 
                                 style="width: ${company.performance_score}%"></div>
                        </div>
                        <small>${company.performance_score}%</small>
                    </div>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary view-company" 
                                data-company-id="${company.id}">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-success add-to-watchlist" 
                                data-company-id="${company.id}">
                            <i class="fas fa-star"></i>
                        </button>
                        <button class="btn btn-outline-info download-data" 
                                data-company-id="${company.id}">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    renderGridView() {
        return `
            <div class="row">
                ${this.searchResults.map(company => this.renderCompanyCard(company)).join('')}
            </div>
        `;
    }

    renderCompanyCard(company) {
        const isSelected = this.selectedCompanies.has(company.id);
        const performanceClass = this.getPerformanceClass(company.performance_score);
        
        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card h-100 ${isSelected ? 'border-primary bg-light' : ''}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input company-select" 
                                   value="${company.id}" ${isSelected ? 'checked' : ''}>
                        </div>
                        <span class="badge bg-secondary">${company.sector}</span>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title">${company.name}</h6>
                        <p class="card-text text-muted small">${company.ticker_symbol}</p>
                        
                        <div class="row text-center mb-3">
                            <div class="col-4">
                                <div class="small text-muted">Market Cap</div>
                                <div class="fw-bold small">${this.formatCurrency(company.market_cap, true)}</div>
                            </div>
                            <div class="col-4">
                                <div class="small text-muted">Revenue</div>
                                <div class="fw-bold small">${this.formatCurrency(company.total_revenue, true)}</div>
                            </div>
                            <div class="col-4">
                                <div class="small text-muted">Performance</div>
                                <div class="fw-bold small ${performanceClass.replace('bg-', 'text-')}">${company.performance_score}%</div>
                            </div>
                        </div>
                        
                        <div class="progress mb-2" style="height: 6px;">
                            <div class="progress-bar ${performanceClass}" 
                                 style="width: ${company.performance_score}%"></div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="btn-group w-100">
                            <button class="btn btn-sm btn-outline-primary view-company" 
                                    data-company-id="${company.id}">
                                View
                            </button>
                            <button class="btn btn-sm btn-outline-success add-to-watchlist" 
                                    data-company-id="${company.id}">
                                Watch
                            </button>
                            <button class="btn btn-sm btn-outline-info download-data" 
                                    data-company-id="${company.id}">
                                Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    setupResultInteractions() {
        // Select all checkbox
        const selectAll = document.getElementById('selectAll');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll('.company-select');
                checkboxes.forEach(cb => {
                    cb.checked = e.target.checked;
                    if (e.target.checked) {
                        this.selectedCompanies.add(parseInt(cb.value));
                    } else {
                        this.selectedCompanies.delete(parseInt(cb.value));
                    }
                });
                this.updateBulkActions();
            });
        }

        // Individual company selection
        document.querySelectorAll('.company-select').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const companyId = parseInt(e.target.value);
                if (e.target.checked) {
                    this.selectedCompanies.add(companyId);
                } else {
                    this.selectedCompanies.delete(companyId);
                }
                this.updateBulkActions();
            });
        });

        // Company actions
        document.querySelectorAll('.view-company').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const companyId = e.target.closest('button').dataset.companyId;
                this.viewCompany(companyId);
            });
        });

        document.querySelectorAll('.add-to-watchlist').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const companyId = e.target.closest('button').dataset.companyId;
                this.addToWatchlist(companyId);
            });
        });

        document.querySelectorAll('.download-data').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const companyId = e.target.closest('button').dataset.companyId;
                this.downloadCompanyData(companyId);
            });
        });
    }

    updateBulkActions() {
        const selectedCount = this.selectedCompanies.size;
        document.getElementById('selectedCount').textContent = 
            `${selectedCount} companies selected`;
        
        const bulkActions = document.getElementById('bulkActions');
        if (selectedCount > 0) {
            bulkActions.style.display = 'block';
        } else {
            bulkActions.style.display = 'none';
        }
    }

    getPerformanceClass(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-info';
        if (score >= 40) return 'bg-warning';
        return 'bg-danger';
    }

    formatCurrency(amount, short = false) {
        if (!amount) return 'N/A';
        
        if (short) {
            if (amount >= 1000000000) {
                return `${(amount / 1000000000).toFixed(1)}B ETB`;
            } else if (amount >= 1000000) {
                return `${(amount / 1000000).toFixed(1)}M ETB`;
            } else if (amount >= 1000) {
                return `${(amount / 1000).toFixed(1)}K ETB`;
            }
        }
        
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'ETB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    addMetricRule() {
        const container = document.getElementById('customMetrics');
        const ruleHTML = `
            <div class="metric-rule mb-2">
                <select class="form-select form-select-sm mb-1" name="metricName[]">
                    <option value="">Select Metric</option>
                    <option value="total_revenue">Total Revenue</option>
                    <option value="net_income">Net Income</option>
                    <option value="total_assets">Total Assets</option>
                    <option value="return_on_assets">Return on Assets</option>
                    <option value="return_on_equity">Return on Equity</option>
                    <option value="debt_to_equity">Debt to Equity</option>
                </select>
                <div class="row">
                    <div class="col-4">
                        <select class="form-select form-select-sm" name="operator[]">
                            <option value="gt">></option>
                            <option value="lt"><</option>
                            <option value="eq">=</option>
                            <option value="gte">>=</option>
                            <option value="lte"><=</option>
                        </select>
                    </div>
                    <div class="col-6">
                        <input type="number" class="form-control form-control-sm" 
                               name="value[]" placeholder="Value" step="0.01">
                    </div>
                    <div class="col-2">
                        <button type="button" class="btn btn-sm btn-outline-danger remove-rule">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', ruleHTML);
        
        // Add remove functionality
        const newRule = container.lastElementChild;
        newRule.querySelector('.remove-rule').addEventListener('click', () => {
            newRule.remove();
            this.performSearch();
        });
    }

    clearAllFilters() {
        document.getElementById('searchForm').reset();
        this.selectedCompanies.clear();
        document.getElementById('customMetrics').innerHTML = `
            <div class="metric-rule mb-2">
                <select class="form-select form-select-sm mb-1" name="metricName[]">
                    <option value="">Select Metric</option>
                    <option value="total_revenue">Total Revenue</option>
                    <option value="net_income">Net Income</option>
                    <option value="total_assets">Total Assets</option>
                    <option value="return_on_assets">Return on Assets</option>
                    <option value="return_on_equity">Return on Equity</option>
                    <option value="debt_to_equity">Debt to Equity</option>
                </select>
                <div class="row">
                    <div class="col-4">
                        <select class="form-select form-select-sm" name="operator[]">
                            <option value="gt">></option>
                            <option value="lt"><</option>
                            <option value="eq">=</option>
                            <option value="gte">>=</option>
                            <option value="lte"><=</option>
                        </select>
                    </div>
                    <div class="col-8">
                        <input type="number" class="form-control form-control-sm" 
                               name="value[]" placeholder="Value" step="0.01">
                    </div>
                </div>
            </div>
        `;
        this.initializeDateRanges();
        this.searchResults = [];
        this.displayResults();
    }

    showSaveSearchModal() {
        const modal = new bootstrap.Modal(document.getElementById('saveSearchModal'));
        modal.show();
    }

    saveCurrentSearch() {
        const name = document.getElementById('searchName').value.trim();
        const description = document.getElementById('searchDescription').value.trim();
        const enableAlerts = document.getElementById('enableAlerts').checked;
        
        if (!name) {
            alert('Please enter a name for the search.');
            return;
        }
        
        const search = {
            id: Date.now(),
            name: name,
            description: description,
            filters: this.collectFilters(),
            enableAlerts: enableAlerts,
            createdAt: new Date().toISOString()
        };
        
        this.savedSearches.push(search);
        localStorage.setItem('savedSearches', JSON.stringify(this.savedSearches));
        
        this.loadSavedSearches();
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('saveSearchModal'));
        modal.hide();
        
        document.getElementById('saveSearchForm').reset();
    }

    loadSavedSearches() {
        const container = document.getElementById('savedSearches');
        
        if (this.savedSearches.length === 0) {
            container.innerHTML = '<small class="text-muted">No saved searches yet</small>';
            return;
        }
        
        container.innerHTML = this.savedSearches.map(search => `
            <div class="saved-search-item mb-2 p-2 border rounded">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="fw-bold small">${search.name}</div>
                        ${search.description ? `<div class="text-muted small">${search.description}</div>` : ''}
                        <div class="text-muted small">
                            <i class="fas fa-clock me-1"></i>
                            ${new Date(search.createdAt).toLocaleDateString()}
                        </div>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary load-search" 
                                data-search-id="${search.id}">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-outline-danger delete-search" 
                                data-search-id="${search.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Add event listeners
        container.querySelectorAll('.load-search').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const searchId = parseInt(e.target.closest('button').dataset.searchId);
                this.loadSavedSearch(searchId);
            });
        });
        
        container.querySelectorAll('.delete-search').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const searchId = parseInt(e.target.closest('button').dataset.searchId);
                this.deleteSavedSearch(searchId);
            });
        });
    }

    loadSavedSearch(searchId) {
        const search = this.savedSearches.find(s => s.id === searchId);
        if (!search) return;
        
        const filters = search.filters;
        
        // Populate form fields
        document.getElementById('searchQuery').value = filters.query || '';
        
        // Set selected sectors
        const sectorSelect = document.getElementById('sectorFilter');
        Array.from(sectorSelect.options).forEach(option => {
            option.selected = filters.sectors.includes(option.value);
        });
        
        // Set numeric ranges
        if (filters.market_cap.min) document.getElementById('marketCapMin').value = filters.market_cap.min;
        if (filters.market_cap.max) document.getElementById('marketCapMax').value = filters.market_cap.max;
        
        if (filters.metrics.roa.min) document.getElementById('roaMin').value = filters.metrics.roa.min;
        if (filters.metrics.roa.max) document.getElementById('roaMax').value = filters.metrics.roa.max;
        
        // Set performance filters
        document.getElementById('topPerformers').checked = filters.performance_filters.top_performers;
        document.getElementById('growthCompanies').checked = filters.performance_filters.growth_companies;
        document.getElementById('undervaluedCompanies').checked = filters.performance_filters.undervalued;
        
        // Execute search
        this.performSearch();
    }

    deleteSavedSearch(searchId) {
        if (confirm('Are you sure you want to delete this saved search?')) {
            this.savedSearches = this.savedSearches.filter(s => s.id !== searchId);
            localStorage.setItem('savedSearches', JSON.stringify(this.savedSearches));
            this.loadSavedSearches();
        }
    }

    toggleView(view) {
        const gridBtn = document.getElementById('gridView');
        const listBtn = document.getElementById('listView');
        
        if (view === 'grid') {
            gridBtn.classList.add('active');
            listBtn.classList.remove('active');
        } else {
            listBtn.classList.add('active');
            gridBtn.classList.remove('active');
        }
        
        this.displayResults();
    }

    sortResults() {
        const sortBy = document.getElementById('sortBy').value;
        
        this.searchResults.sort((a, b) => {
            switch (sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'market_cap':
                    return (b.market_cap || 0) - (a.market_cap || 0);
                case 'revenue':
                    return (b.total_revenue || 0) - (a.total_revenue || 0);
                case 'assets':
                    return (b.total_assets || 0) - (a.total_assets || 0);
                case 'performance':
                    return (b.performance_score || 0) - (a.performance_score || 0);
                default:
                    return 0;
            }
        });
        
        this.displayResults();
    }

    updateSearchStats(data) {
        const stats = document.getElementById('searchStats');
        const total = data.total || this.searchResults.length;
        const executionTime = data.execution_time || 0;
        
        stats.innerHTML = `
            <i class="fas fa-info-circle me-1"></i>
            Found ${total} companies in ${executionTime}ms
        `;
    }

    updatePagination() {
        // Pagination implementation would go here
        // For now, we'll show all results
    }

    showLoading() {
        document.getElementById('searchLoading').style.display = 'block';
        document.getElementById('searchResults').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('searchLoading').style.display = 'none';
        document.getElementById('searchResults').style.display = 'block';
    }

    showError(message) {
        const container = document.getElementById('searchResults');
        container.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <h6>Search Error</h6>
                <p>${message}</p>
                <button class="btn btn-outline-danger" onclick="location.reload()">
                    <i class="fas fa-redo me-1"></i>Refresh Page
                </button>
            </div>
        `;
    }

    getNoResultsHTML() {
        return `
            <div class="text-center py-5">
                <i class="fas fa-search-minus fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No companies found</h5>
                <p class="text-muted">Try adjusting your search filters or criteria.</p>
                <button class="btn btn-outline-primary" id="clearFiltersBtn">
                    <i class="fas fa-eraser me-1"></i>Clear All Filters
                </button>
            </div>
        `;
    }

    // Utility functions
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
    }

    // Action methods
    viewCompany(companyId) {
        window.location.href = `/companies/${companyId}`;
    }

    async addToWatchlist(companyId) {
        try {
            const response = await fetch('/api/watchlist/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_id: companyId })
            });
            
            if (response.ok) {
                this.showToast('Company added to watchlist', 'success');
            }
        } catch (error) {
            this.showToast('Failed to add to watchlist', 'error');
        }
    }

    downloadCompanyData(companyId) {
        window.location.href = `/api/financial/companies/${companyId}/download`;
    }

    addSelectedToWatchlist() {
        this.selectedCompanies.forEach(companyId => {
            this.addToWatchlist(companyId);
        });
    }

    compareSelected() {
        const selectedIds = Array.from(this.selectedCompanies);
        if (selectedIds.length < 2) {
            alert('Please select at least 2 companies to compare.');
            return;
        }
        
        const params = selectedIds.map(id => `company_ids=${id}`).join('&');
        window.location.href = `/analytics?${params}`;
    }

    exportSelected() {
        const selectedIds = Array.from(this.selectedCompanies);
        if (selectedIds.length === 0) {
            alert('Please select companies to export.');
            return;
        }
        
        const params = selectedIds.map(id => `company_ids=${id}`).join('&');
        window.location.href = `/api/financial/companies/export?${params}`;
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : 'success'} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize search when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AdvancedSearch();
});