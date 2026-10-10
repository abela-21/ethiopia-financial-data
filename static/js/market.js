// Ethiopia Capital Market Platform - Market JavaScript

// Market Manager Class
class MarketManager {
    constructor() {
        this.refreshInterval = null;
        this.refreshRate = 60000; // 1 minute for market data
        this.isLoading = false;
        this.charts = new Map();
        
        this.initialize();
    }

    initialize() {
        console.log('Market Manager - Initializing...');
        
        // Load initial market data
        this.loadAllMarketData();
        
        // Set up auto-refresh
        this.startAutoRefresh();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('Market Manager - Initialized');
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.querySelector('[onclick="refreshMarketData()"]');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.loadAllMarketData(true);
        }

        // Trend period buttons
        const trendButtons = document.querySelectorAll('input[name="trendsOptions"]');
        trendButtons.forEach(button => {
            button.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.loadMarketTrends(parseInt(e.target.value));
                }
            });
        });

        // Tab switches for market leaders
        const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', () => {
                // Refresh leaders data when tab is shown
                if (button.id.includes('gainers') || button.id.includes('losers')) {
                    this.loadMarketLeaders();
                }
            });
        });

        // Page visibility for auto-refresh
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });
    }

    async loadAllMarketData(forceRefresh = false) {
        if (this.isLoading && !forceRefresh) return;
        
        this.isLoading = true;
        this.showGlobalLoading();

        try {
            await Promise.all([
                this.loadMarketSummary(forceRefresh),
                this.loadMarketLeaders(forceRefresh),
                this.loadMarketTrends(this.selectedTrendDays(), forceRefresh)
            ]);
            
            this.hideGlobalLoading();
        } catch (error) {
            console.error('Market data loading error:', error);
            this.handleMarketError(error);
        } finally {
            this.isLoading = false;
        }
    }

    selectedTrendDays() {
        const checked = document.querySelector('input[name="trendsOptions"]:checked');
        return checked ? parseInt(checked.value, 10) : 30;
    }

    async loadMarketSummary(forceRefresh = false) {
        const cacheKey = 'market_summary';
        
        if (!forceRefresh) {
            const cached = cache.get(cacheKey);
            if (cached) {
                this.updateMarketSummary(cached);
                return;
            }
        }

        try {
            const data = await api.get('/market/summary');
            cache.set(cacheKey, data);
            this.updateMarketSummary(data);
        } catch (error) {
            console.error('Market summary error:', error);
            this.showMarketSummaryError();
        }
    }

    updateMarketSummary(data) {
        const summary = data.summary || {};
        
        // Update summary cards with animation
        this.animateValueUpdate('totalCompanies', summary.total_companies || 0);
        this.animateValueUpdate('activeCompanies', summary.active_companies || 0);
        this.animateValueUpdate('marketCap', Utils.formatLargeNumber(summary.market_cap || 0));
        this.animateValueUpdate('dailyVolume', Utils.formatLargeNumber(summary.daily_volume || 0));
        
        // Update statistics
        this.animateValueUpdate('gainersCount', summary.gainers || 0);
        this.animateValueUpdate('losersCount', summary.losers || 0);
        this.animateValueUpdate('unchangedCount', summary.unchanged || 0);
        
        // Update metadata
        if (data.metadata) {
            this.updateElement('lastUpdated', data.metadata.last_updated || 'N/A');
        }

        // Update market status indicator
        this.updateMarketStatus(summary);
    }

    async loadMarketLeaders(forceRefresh = false) {
        const cacheKey = 'market_leaders';
        
        if (!forceRefresh) {
            const cached = cache.get(cacheKey);
            if (cached) {
                this.updateMarketLeaders(cached);
                return;
            }
        }

        try {
            const data = await api.get('/market/leaders');
            cache.set(cacheKey, data);
            this.updateMarketLeaders(data);
        } catch (error) {
            console.error('Market leaders error:', error);
            this.showMarketLeadersError();
        }
    }

    updateMarketLeaders(data) {
        // API rows: {ticker, name, current_price, percent_change, volume}
        const normalize = rows => (rows || []).map(row => ({
            ticker: row.ticker,
            name: row.name || '',
            price: row.current_price ?? row.price ?? 0,
            change: row.percent_change ?? row.change ?? 0,
            volume: row.volume || 0
        }));
        this.updateLeadersList('gainersContent', normalize(data.gainers));
        this.updateLeadersList('losersContent', normalize(data.losers));
    }

    updateLeadersList(containerId, companies) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (companies.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-info-circle text-muted fa-2x mb-2"></i>
                    <p class="text-muted">No data available</p>
                </div>
            `;
            return;
        }

        container.innerHTML = companies.map((company, index) => {
            const changeClass = company.change >= 0 ? 'text-success' : 'text-danger';
            const changeIcon = company.change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            const rankIcon = index === 0 ? 'fa-crown text-warning' : 'fa-circle text-muted';
            
            return `
                <div class="leader-item d-flex justify-content-between align-items-center py-3 border-bottom">
                    <div class="d-flex align-items-center">
                        <div class="rank-indicator me-3">
                            <i class="fas ${rankIcon}"></i>
                        </div>
                        <div>
                            <div class="fw-bold">${company.ticker}</div>
                            <div class="text-muted small">${Utils.truncateText(company.name, 25)}</div>
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold">${Utils.formatCurrency(company.price)}</div>
                        <div class="small ${changeClass}">
                            <i class="fas ${changeIcon} me-1"></i>
                            ${Utils.formatPercentage(Math.abs(company.change))}
                        </div>
                        <div class="text-muted small">Vol: ${Utils.formatLargeNumber(company.volume)}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async loadMarketTrends(days, forceRefresh = false) {
        const cacheKey = `market_trends_${days}`;
        
        if (!forceRefresh) {
            const cached = cache.get(cacheKey);
            if (cached) {
                this.renderTrendsChart(cached);
                return;
            }
        }

        this.showTrendsLoading();

        try {
            const data = await api.get('/market/trends', { days });
            cache.set(cacheKey, data);
            this.renderTrendsChart(data);
        } catch (error) {
            console.error('Market trends error:', error);
            this.showTrendsError();
        }
    }

    renderTrendsChart(data) {
        const trends = data.trends || [];
        
        if (trends.length === 0) {
            this.showTrendsError();
            return;
        }

        const chartData = {
            labels: trends.map(t => Utils.formatDate(t.date)),
            datasets: [
                {
                    type: 'line',
                    label: 'Market Cap (ETB)',
                    data: trends.map(t => t.market_cap),
                    borderColor: ChartConfig.colors.primary,
                    backgroundColor: chartManager.hexToRgba(ChartConfig.colors.primary, 0.1),
                    fill: true,
                    yAxisID: 'y',
                    tension: 0.2
                },
                {
                    type: 'bar',
                    label: 'Daily Volume',
                    data: trends.map(t => t.volume),
                    backgroundColor: chartManager.hexToRgba(ChartConfig.colors.success, 0.6),
                    borderColor: ChartConfig.colors.success,
                    yAxisID: 'y1',
                    barThickness: 4
                }
            ]
        };

        const options = {
            ...ChartTemplates.marketTrends.options,
            plugins: {
                ...ChartTemplates.marketTrends.options.plugins,
                tooltip: {
                    ...ChartTemplates.marketTrends.options.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label;
                            if (label.includes('Volume')) {
                                return `${label}: ${Utils.formatLargeNumber(context.parsed.y)}`;
                            }
                            return `${label}: ${Utils.formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            }
        };

        // Destroy existing chart
        if (this.charts.has('trendsChart')) {
            this.charts.get('trendsChart').destroy();
        }

        const chart = chartManager.createMixedChart('trendsChart', chartData, options);
        if (chart) {
            this.charts.set('trendsChart', chart);
        }

        this.hideTrendsLoading();
    }

    // Market status indicator
    updateMarketStatus(summary) {
        const statusContainer = document.getElementById('marketStatus');
        if (!statusContainer) return;

        const marketOpenHours = this.isMarketOpen();
        const totalVolume = summary.daily_volume || 0;
        const totalCompanies = summary.total_companies || 0;
        const activeCompanies = summary.active_companies || 0;
        
        let status, statusClass, statusIcon;
        
        if (marketOpenHours && activeCompanies > 0) {
            status = 'Market Open';
            statusClass = 'text-success';
            statusIcon = 'fa-circle';
        } else if (marketOpenHours) {
            status = 'Market Open (Low Activity)';
            statusClass = 'text-warning';
            statusIcon = 'fa-circle';
        } else {
            status = 'Market Closed';
            statusClass = 'text-danger';
            statusIcon = 'fa-circle';
        }

        statusContainer.innerHTML = `
            <div class="market-status d-flex align-items-center">
                <i class="fas ${statusIcon} ${statusClass} me-2"></i>
                <span class="${statusClass} fw-bold">${status}</span>
                <small class="text-muted ms-2">
                    (${activeCompanies}/${totalCompanies} companies trading)
                </small>
            </div>
        `;
    }

    isMarketOpen() {
        const now = new Date();
        const hour = now.getHours();
        const day = now.getDay();
        
        // Ethiopian market hours: Monday-Friday, 9 AM - 3 PM EAT
        return day >= 1 && day <= 5 && hour >= 9 && hour < 15;
    }

    // Animation and visual effects
    animateValueUpdate(elementId, newValue) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const currentValue = element.textContent;
        if (currentValue !== newValue.toString()) {
            element.classList.add('value-updating');
            setTimeout(() => {
                element.textContent = newValue;
                element.classList.remove('value-updating');
                element.classList.add('value-updated');
                setTimeout(() => element.classList.remove('value-updated'), 1000);
            }, 200);
        }
    }

    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    // Loading states
    showGlobalLoading() {
        const refreshBtn = document.querySelector('[onclick="refreshMarketData()"]');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Refreshing...';
            refreshBtn.disabled = true;
        }
    }

    hideGlobalLoading() {
        const refreshBtn = document.querySelector('[onclick="refreshMarketData()"]');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Refresh';
            refreshBtn.disabled = false;
        }
    }

    showTrendsLoading() {
        const container = document.getElementById('trendsChartContainer');
        const loading = document.getElementById('trendsLoading');
        const error = document.getElementById('trendsError');
        
        if (container) container.classList.add('d-none');
        if (error) error.classList.add('d-none');
        if (loading) loading.classList.remove('d-none');
    }

    hideTrendsLoading() {
        const container = document.getElementById('trendsChartContainer');
        const loading = document.getElementById('trendsLoading');
        const error = document.getElementById('trendsError');
        
        if (container) container.classList.remove('d-none');
        if (loading) loading.classList.add('d-none');
        if (error) error.classList.add('d-none');
    }

    // Error handling
    handleMarketError(error) {
        this.hideGlobalLoading();
        notifications.error('Failed to load market data. Please try again.');
    }

    showMarketSummaryError() {
        ['totalCompanies', 'activeCompanies', 'marketCap', 'dailyVolume'].forEach(id => {
            this.updateElement(id, 'N/A');
        });
    }

    showMarketLeadersError() {
        ['gainersContent', 'losersContent'].forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-4">
                        <i class="fas fa-exclamation-triangle text-muted fa-2x mb-2"></i>
                        <p class="text-muted">Unable to load data</p>
                        <button class="btn btn-sm btn-outline-primary" onclick="window.marketManager.loadMarketLeaders(true)">
                            <i class="fas fa-retry me-1"></i>Retry
                        </button>
                    </div>
                `;
            }
        });
    }

    showTrendsError() {
        const container = document.getElementById('trendsChartContainer');
        const loading = document.getElementById('trendsLoading');
        const error = document.getElementById('trendsError');
        
        if (container) container.classList.add('d-none');
        if (loading) loading.classList.add('d-none');
        if (error) error.classList.remove('d-none');
    }

    // Auto-refresh management
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            if (this.isMarketOpen()) {
                this.loadAllMarketData();
            }
        }, this.refreshRate);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Cleanup
    destroy() {
        this.stopAutoRefresh();
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }
}

// Initialize market manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on market page
    if (document.getElementById('marketSummary') || document.getElementById('trendsChart')) {
        console.log('Initializing Market Manager...');
        window.marketManager = new MarketManager();
    }
});

// Global functions for backward compatibility
window.refreshMarketData = function() {
    if (window.marketManager) {
        window.marketManager.loadAllMarketData(true);
    }
};

window.loadMarketSummary = async function() {
    if (window.marketManager) {
        await window.marketManager.loadMarketSummary(true);
    }
};

window.loadMarketLeaders = async function() {
    if (window.marketManager) {
        await window.marketManager.loadMarketLeaders(true);
    }
};

window.loadMarketTrends = async function(days) {
    if (window.marketManager) {
        await window.marketManager.loadMarketTrends(days, true);
    }
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.marketManager) {
        window.marketManager.destroy();
    }
});

// CSS for market animations
const style = document.createElement('style');
style.textContent = `
    .value-updating {
        opacity: 0.5;
        transform: scale(0.95);
        transition: all 0.2s ease;
    }
    
    .value-updated {
        color: #198754 !important;
        font-weight: 700;
        transform: scale(1.05);
        transition: all 0.3s ease;
    }
    
    .leader-item {
        transition: background-color 0.2s ease;
    }
    
    .leader-item:hover {
        background-color: rgba(13, 110, 253, 0.05);
        cursor: pointer;
    }
    
    .rank-indicator {
        width: 24px;
        text-align: center;
    }
    
    .market-status {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background-color: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
`;
document.head.appendChild(style);

// Export for global use
window.MarketManager = MarketManager;
