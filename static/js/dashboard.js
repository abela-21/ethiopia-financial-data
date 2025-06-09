// Ethiopia Capital Market Platform - Dashboard JavaScript

// Dashboard Manager Class
class DashboardManager {
    constructor() {
        this.refreshInterval = null;
        this.refreshRate = 300000; // 5 minutes
        this.isLoading = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.initialize();
    }

    initialize() {
        console.log('Dashboard Manager - Initializing...');
        
        // Load initial data
        this.loadDashboardData();
        
        // Set up auto-refresh
        this.startAutoRefresh();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('Dashboard Manager - Initialized');
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardData(true);
            });
        }

        // Auto-refresh toggle
        const autoRefreshToggle = document.querySelector('[data-toggle="auto-refresh"]');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }

        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });
    }

    async loadDashboardData(forceRefresh = false) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            // Load market summary
            await this.loadMarketSummary(forceRefresh);
            
            // Load latest indicators
            await this.loadLatestIndicators(forceRefresh);
            
            // Load recent activities
            await this.loadRecentActivities(forceRefresh);
            
            this.retryCount = 0;
            this.hideLoadingState();
            
        } catch (error) {
            console.error('Dashboard data loading error:', error);
            this.handleLoadingError(error);
        } finally {
            this.isLoading = false;
        }
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
            console.error('Market summary loading error:', error);
            this.showMarketSummaryError();
        }
    }

    updateMarketSummary(data) {
        const summary = data.summary;
        
        // Update summary cards
        this.updateElement('totalCompanies', summary.total_companies || 0);
        this.updateElement('activeCompanies', summary.active_companies || 0);
        this.updateElement('marketCap', Utils.formatLargeNumber(summary.market_cap || 0));
        this.updateElement('dailyVolume', Utils.formatLargeNumber(summary.daily_volume || 0));
        this.updateElement('gainers', summary.gainers || 0);
        this.updateElement('losers', summary.losers || 0);
        this.updateElement('unchanged', summary.unchanged || 0);
        
        // Update last updated timestamp
        if (data.metadata && data.metadata.last_updated) {
            this.updateElement('lastUpdated', data.metadata.last_updated);
        }

        // Update market cap change indicator
        this.updateMarketCapChange(summary.market_cap_change);
    }

    async loadLatestIndicators(forceRefresh = false) {
        const cacheKey = 'latest_indicators';
        
        if (!forceRefresh) {
            const cached = cache.get(cacheKey);
            if (cached) {
                this.updateLatestIndicators(cached);
                return;
            }
        }

        try {
            const data = await api.get('/macro/latest');
            cache.set(cacheKey, data);
            this.updateLatestIndicators(data);
        } catch (error) {
            console.error('Latest indicators loading error:', error);
            this.showIndicatorsError();
        }
    }

    updateLatestIndicators(data) {
        if (!data.latest_indicators) return;

        const indicators = data.latest_indicators;
        
        // Update economic indicator cards
        this.updateElement('gdpGrowth', 
            indicators.gdp_growth ? `${indicators.gdp_growth.toFixed(1)}%` : 'N/A'
        );
        
        this.updateElement('inflationRate', 
            indicators.inflation_rate ? `${indicators.inflation_rate.toFixed(1)}%` : 'N/A'
        );
        
        this.updateElement('usdExchange', 
            indicators.etb_usd ? `${indicators.etb_usd.toFixed(2)}` : 'N/A'
        );
        
        this.updateElement('interestRate', 
            indicators.interest_rate ? `${indicators.interest_rate.toFixed(1)}%` : 'N/A'
        );

        // Update indicator changes with colors
        this.updateIndicatorChange('gdpGrowthChange', indicators.gdp_growth_change);
        this.updateIndicatorChange('inflationChange', indicators.inflation_change);
        this.updateIndicatorChange('exchangeChange', indicators.exchange_change);
        this.updateIndicatorChange('interestChange', indicators.interest_change);
    }

    async loadRecentActivities(forceRefresh = false) {
        const cacheKey = 'recent_activities';
        
        if (!forceRefresh) {
            const cached = cache.get(cacheKey);
            if (cached) {
                this.updateRecentActivities(cached);
                return;
            }
        }

        try {
            // Simulate recent activities for now
            const activities = this.generateRecentActivities();
            cache.set(cacheKey, activities);
            this.updateRecentActivities(activities);
        } catch (error) {
            console.error('Recent activities loading error:', error);
            this.showActivitiesError();
        }
    }

    generateRecentActivities() {
        // This would normally come from an API
        return [
            {
                type: 'market',
                title: 'Market Update',
                description: 'Daily trading volume reached new monthly high',
                time: '2 minutes ago',
                icon: 'chart-line',
                color: 'success'
            },
            {
                type: 'company',
                title: 'New Company Listed',
                description: 'ABC Manufacturing joined the exchange',
                time: '1 hour ago',
                icon: 'building',
                color: 'primary'
            },
            {
                type: 'macro',
                title: 'Economic Indicator Update',
                description: 'Inflation rate decreased by 0.2%',
                time: '3 hours ago',
                icon: 'globe',
                color: 'info'
            },
            {
                type: 'system',
                title: 'Data Refresh',
                description: 'Financial statements updated for Q3 2024',
                time: '6 hours ago',
                icon: 'sync-alt',
                color: 'warning'
            }
        ];
    }

    updateRecentActivities(activities) {
        const container = document.getElementById('recentActivities');
        if (!container) return;

        container.innerHTML = activities.map(activity => `
            <div class="activity-item d-flex align-items-start mb-3">
                <div class="activity-icon me-3">
                    <div class="icon-circle bg-${activity.color} text-white">
                        <i class="fas fa-${activity.icon}"></i>
                    </div>
                </div>
                <div class="activity-content flex-grow-1">
                    <h6 class="activity-title mb-1">${activity.title}</h6>
                    <p class="activity-description text-muted mb-1">${activity.description}</p>
                    <small class="activity-time text-muted">${activity.time}</small>
                </div>
            </div>
        `).join('');
    }

    // Chart creation methods
    createMarketTrendsChart() {
        const canvas = document.getElementById('marketTrendsChart');
        if (!canvas) return;

        // Sample data - in real app this would come from API
        const data = {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Market Cap',
                data: [1200, 1350, 1280, 1420, 1380, 1450],
                borderColor: ChartConfig.colors.primary,
                backgroundColor: chartManager.hexToRgba(ChartConfig.colors.primary, 0.1),
                fill: true
            }]
        };

        const options = {
            ...ChartTemplates.marketTrends.options,
            plugins: {
                legend: {
                    display: false
                }
            }
        };

        return chartManager.createLineChart('marketTrendsChart', data, options);
    }

    createSectorDistributionChart() {
        const canvas = document.getElementById('sectorDistributionChart');
        if (!canvas) return;

        // Sample data
        const data = {
            labels: ['Banking', 'Manufacturing', 'Agriculture', 'Services', 'Technology'],
            data: [35, 25, 20, 15, 5],
            backgroundColor: [
                ChartConfig.colors.primary,
                ChartConfig.colors.success,
                ChartConfig.colors.warning,
                ChartConfig.colors.info,
                ChartConfig.colors.danger
            ]
        };

        return chartManager.createDoughnutChart('sectorDistributionChart', data);
    }

    // Utility methods
    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            element.classList.add('updated');
            setTimeout(() => element.classList.remove('updated'), 1000);
        }
    }

    updateMarketCapChange(change) {
        const element = document.getElementById('marketCapChange');
        if (element && change !== undefined) {
            element.textContent = Utils.formatPercentage(change);
            element.className = `small ${Utils.getChangeColor(change)}`;
        }
    }

    updateIndicatorChange(elementId, change) {
        const element = document.getElementById(elementId);
        if (element && change !== undefined) {
            element.textContent = Utils.formatPercentage(change);
            element.className = `small ${Utils.getChangeColor(change)}`;
        }
    }

    // Loading states
    showLoadingState() {
        const refreshBtn = document.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Refreshing...';
            refreshBtn.disabled = true;
        }

        // Add loading shimmer to cards
        const summaryCards = document.querySelectorAll('.market-summary .card-body');
        summaryCards.forEach(card => card.classList.add('loading-shimmer'));
    }

    hideLoadingState() {
        const refreshBtn = document.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Refresh';
            refreshBtn.disabled = false;
        }

        // Remove loading shimmer
        const summaryCards = document.querySelectorAll('.market-summary .card-body');
        summaryCards.forEach(card => card.classList.remove('loading-shimmer'));
    }

    // Error handling
    handleLoadingError(error) {
        this.hideLoadingState();
        
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            setTimeout(() => {
                this.loadDashboardData();
            }, 2000 * this.retryCount);
        } else {
            notifications.error('Failed to load dashboard data. Please check your connection.');
        }
    }

    showMarketSummaryError() {
        const elements = ['totalCompanies', 'activeCompanies', 'marketCap', 'dailyVolume'];
        elements.forEach(id => this.updateElement(id, 'N/A'));
    }

    showIndicatorsError() {
        const elements = ['gdpGrowth', 'inflationRate', 'usdExchange', 'interestRate'];
        elements.forEach(id => this.updateElement(id, 'N/A'));
    }

    showActivitiesError() {
        const container = document.getElementById('recentActivities');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-exclamation-triangle text-muted fa-2x mb-2"></i>
                    <p class="text-muted">Unable to load recent activities</p>
                </div>
            `;
        }
    }

    // Auto-refresh management
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
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
        chartManager.destroyAllCharts();
    }
}

// Real-time updates simulation
class RealTimeUpdates {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    // Simulate real-time updates with periodic data changes
    startSimulation() {
        setInterval(() => {
            this.simulateMarketChange();
        }, 30000); // Update every 30 seconds
    }

    simulateMarketChange() {
        // Simulate small changes in market data
        const elements = {
            'totalVolume': () => Math.random() > 0.5 ? 1 : -1,
            'gainers': () => Math.floor(Math.random() * 3),
            'losers': () => Math.floor(Math.random() * 3)
        };

        Object.entries(elements).forEach(([elementId, changeFn]) => {
            const element = document.getElementById(elementId);
            if (element) {
                const currentValue = parseInt(element.textContent) || 0;
                const change = changeFn();
                const newValue = Math.max(0, currentValue + change);
                
                element.textContent = Utils.formatNumber(newValue);
                element.classList.add('flash-update');
                setTimeout(() => element.classList.remove('flash-update'), 1000);
            }
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on pages that have dashboard elements
    if (document.querySelector('.market-summary') || document.getElementById('marketTrendsChart')) {
        console.log('Initializing Dashboard Manager...');
        
        window.dashboardManager = new DashboardManager();
        window.realTimeUpdates = new RealTimeUpdates();
        
        // Start real-time updates simulation
        window.realTimeUpdates.startSimulation();
        
        // Create charts if elements exist
        setTimeout(() => {
            if (typeof chartManager !== 'undefined') {
                dashboardManager.createMarketTrendsChart();
                dashboardManager.createSectorDistributionChart();
            }
        }, 100);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboardManager) {
        window.dashboardManager.destroy();
    }
});

// CSS for flash updates
const style = document.createElement('style');
style.textContent = `
    .flash-update {
        background-color: rgba(255, 193, 7, 0.3) !important;
        transition: background-color 0.3s ease;
    }
    
    .updated {
        color: #198754 !important;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .activity-item {
        padding: 0.75rem;
        border-radius: 0.5rem;
        transition: background-color 0.2s ease;
    }
    
    .activity-item:hover {
        background-color: rgba(0, 0, 0, 0.02);
    }
    
    .activity-icon .icon-circle {
        width: 40px;
        height: 40px;
    }
    
    .activity-title {
        font-weight: 600;
        color: #212529;
    }
    
    .activity-description {
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .activity-time {
        font-size: 0.8rem;
    }
`;
document.head.appendChild(style);

// Export for global use
window.DashboardManager = DashboardManager;
window.RealTimeUpdates = RealTimeUpdates;
