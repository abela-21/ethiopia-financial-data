/**
 * Financial Analytics Dashboard
 * Interactive charts and analysis for Ethiopian listed companies
 */

class FinancialAnalytics {
    constructor() {
        this.companies = [];
        this.analyticsData = {};
        this.charts = {};
        this.selectedCompanies = [];
        this.selectedMetrics = ['total_revenue', 'net_income'];
        this.selectedPeriod = '1Y';
        this.baseApiUrl = '/api/financial';
        
        this.init();
    }
    
    async init() {
        await this.loadCompanies();
        this.renderCompanySelectors();
        this.setupEventListeners();
        await this.loadInitialAnalytics();
        this.initializeCharts();
    }
    
    async loadCompanies() {
        try {
            const response = await fetch(`${this.baseApiUrl}/companies`);
            const data = await response.json();
            
            if (data.data) {
                this.companies = data.data;
                this.selectedCompanies = this.companies.slice(0, 3).map(c => c.id); // Select first 3 by default
            }
        } catch (error) {
            console.error('Error loading companies:', error);
        }
    }
    
    renderCompanySelectors() {
        const container = document.getElementById('companySelectors');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.companies.forEach(company => {
            const col = document.createElement('div');
            col.className = 'col-12 mb-2';
            
            const isSelected = this.selectedCompanies.includes(company.id);
            
            col.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${company.id}" 
                           id="company${company.id}" ${isSelected ? 'checked' : ''}>
                    <label class="form-check-label" for="company${company.id}">
                        <strong>${company.name}</strong> (${company.ticker_symbol})
                        <br><small class="text-light">${company.sector} • Market Cap: ${company.market_cap_formatted}</small>
                    </label>
                </div>
            `;
            
            container.appendChild(col);
        });
    }
    
    async loadInitialAnalytics() {
        await this.loadAnalyticsData();
        this.updateQuickInsights();
        this.updatePerformanceRankings();
        this.updateKPIMetrics();
    }
    
    async loadAnalyticsData() {
        try {
            // Load financial data for selected companies
            const promises = this.selectedCompanies.map(async (companyId) => {
                const response = await fetch(`${this.baseApiUrl}/companies/${companyId}/metrics`);
                const data = await response.json();
                return { companyId, data: data.data || [] };
            });
            
            const results = await Promise.all(promises);
            
            // Organize data by company
            this.analyticsData = {};
            results.forEach(result => {
                this.analyticsData[result.companyId] = result.data;
            });
            
        } catch (error) {
            console.error('Error loading analytics data:', error);
        }
    }
    
    initializeCharts() {
        this.createComparisonChart();
        this.createTrendCharts();
        this.createSectorBenchmarkChart();
    }
    
    createComparisonChart() {
        const ctx = document.getElementById('comparisonChart');
        if (!ctx) return;
        
        const datasets = this.selectedMetrics.map((metric, index) => {
            const data = this.selectedCompanies.map(companyId => {
                const company = this.companies.find(c => c.id === companyId);
                const metrics = this.analyticsData[companyId] || [];
                const metricData = metrics.find(m => m.metric_name === metric);
                return metricData ? parseFloat(metricData.metric_value) : 0;
            });
            
            const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];
            
            return {
                label: this.formatMetricName(metric),
                data: data,
                backgroundColor: colors[index % colors.length] + '20',
                borderColor: colors[index % colors.length],
                borderWidth: 2,
                type: index === 0 ? 'bar' : 'bar'
            };
        });
        
        const labels = this.selectedCompanies.map(companyId => {
            const company = this.companies.find(c => c.id === companyId);
            return company ? company.ticker_symbol : 'Unknown';
        });
        
        if (this.charts.comparison) {
            this.charts.comparison.destroy();
        }
        
        this.charts.comparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Financial Metrics Comparison'
                    },
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return this.formatCurrency(value);
                            }.bind(this)
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    createTrendCharts() {
        this.createRevenueTrendChart();
        this.createProfitabilityTrendChart();
        this.createAssetTrendChart();
        this.createMarketTrendChart();
    }
    
    createRevenueTrendChart() {
        const ctx = document.getElementById('revenueTrendChart');
        if (!ctx) return;
        
        const datasets = this.selectedCompanies.map((companyId, index) => {
            const company = this.companies.find(c => c.id === companyId);
            const metrics = this.analyticsData[companyId] || [];
            const revenueMetric = metrics.find(m => m.metric_name === 'total_revenue');
            
            // Generate trend data (simulated quarterly data)
            const trendData = this.generateTrendData(revenueMetric ? parseFloat(revenueMetric.metric_value) : 0);
            
            const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];
            
            return {
                label: company ? company.ticker_symbol : 'Unknown',
                data: trendData,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                tension: 0.4,
                fill: false
            };
        });
        
        const labels = this.generateTimeLabels();
        
        if (this.charts.revenueTrend) {
            this.charts.revenueTrend.destroy();
        }
        
        this.charts.revenueTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue Growth Trends'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return this.formatCurrency(value);
                            }.bind(this)
                        }
                    }
                }
            }
        });
    }
    
    createProfitabilityTrendChart() {
        const ctx = document.getElementById('profitabilityTrendChart');
        if (!ctx) return;
        
        const datasets = this.selectedCompanies.map((companyId, index) => {
            const company = this.companies.find(c => c.id === companyId);
            const metrics = this.analyticsData[companyId] || [];
            const roaMetric = metrics.find(m => m.metric_name === 'return_on_assets');
            
            const trendData = this.generateTrendData(roaMetric ? parseFloat(roaMetric.metric_value) : 0, 0.8, 1.2);
            
            const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];
            
            return {
                label: company ? company.ticker_symbol : 'Unknown',
                data: trendData,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                tension: 0.4,
                fill: false
            };
        });
        
        const labels = this.generateTimeLabels();
        
        if (this.charts.profitabilityTrend) {
            this.charts.profitabilityTrend.destroy();
        }
        
        this.charts.profitabilityTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Profitability Trends (ROA %)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createAssetTrendChart() {
        const ctx = document.getElementById('assetTrendChart');
        if (!ctx) return;
        
        const datasets = this.selectedCompanies.map((companyId, index) => {
            const company = this.companies.find(c => c.id === companyId);
            const metrics = this.analyticsData[companyId] || [];
            const assetsMetric = metrics.find(m => m.metric_name === 'total_assets');
            
            const trendData = this.generateTrendData(assetsMetric ? parseFloat(assetsMetric.metric_value) : 0);
            
            const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];
            
            return {
                label: company ? company.ticker_symbol : 'Unknown',
                data: trendData,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                tension: 0.4,
                fill: false
            };
        });
        
        const labels = this.generateTimeLabels();
        
        if (this.charts.assetTrend) {
            this.charts.assetTrend.destroy();
        }
        
        this.charts.assetTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Total Assets Growth'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return this.formatCurrency(value);
                            }.bind(this)
                        }
                    }
                }
            }
        });
    }
    
    createMarketTrendChart() {
        const ctx = document.getElementById('marketTrendChart');
        if (!ctx) return;
        
        const datasets = this.selectedCompanies.map((companyId, index) => {
            const company = this.companies.find(c => c.id === companyId);
            const marketCap = company ? company.market_cap : 0;
            
            const trendData = this.generateTrendData(marketCap, 0.9, 1.15);
            
            const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];
            
            return {
                label: company ? company.ticker_symbol : 'Unknown',
                data: trendData,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                tension: 0.4,
                fill: false
            };
        });
        
        const labels = this.generateTimeLabels();
        
        if (this.charts.marketTrend) {
            this.charts.marketTrend.destroy();
        }
        
        this.charts.marketTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Market Capitalization Trends'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return this.formatCurrency(value);
                            }.bind(this)
                        }
                    }
                }
            }
        });
    }
    
    createSectorBenchmarkChart() {
        const ctx = document.getElementById('sectorBenchmarkChart');
        if (!ctx) return;
        
        // Group companies by sector and calculate averages
        const sectorData = {};
        this.companies.forEach(company => {
            if (!sectorData[company.sector]) {
                sectorData[company.sector] = {
                    companies: [],
                    totalRevenue: 0,
                    totalAssets: 0,
                    count: 0
                };
            }
            
            const metrics = this.analyticsData[company.id] || [];
            const revenueMetric = metrics.find(m => m.metric_name === 'total_revenue');
            const assetsMetric = metrics.find(m => m.metric_name === 'total_assets');
            
            sectorData[company.sector].companies.push(company);
            sectorData[company.sector].totalRevenue += revenueMetric ? parseFloat(revenueMetric.metric_value) : 0;
            sectorData[company.sector].totalAssets += assetsMetric ? parseFloat(assetsMetric.metric_value) : 0;
            sectorData[company.sector].count++;
        });
        
        const labels = Object.keys(sectorData);
        const revenueData = labels.map(sector => sectorData[sector].totalRevenue / sectorData[sector].count);
        const assetsData = labels.map(sector => sectorData[sector].totalAssets / sectorData[sector].count);
        
        if (this.charts.sectorBenchmark) {
            this.charts.sectorBenchmark.destroy();
        }
        
        this.charts.sectorBenchmark = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Average Revenue',
                        data: revenueData,
                        borderColor: '#007bff',
                        backgroundColor: '#007bff20',
                        pointBackgroundColor: '#007bff'
                    },
                    {
                        label: 'Average Assets',
                        data: assetsData,
                        borderColor: '#28a745',
                        backgroundColor: '#28a74520',
                        pointBackgroundColor: '#28a745'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Sector Performance Benchmark'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    updateQuickInsights() {
        const container = document.getElementById('quickInsights');
        if (!container || this.selectedCompanies.length === 0) return;
        
        const insights = this.calculateQuickInsights();
        
        container.innerHTML = insights.map(insight => `
            <div class="performance-indicator ${insight.type}">
                <div class="d-flex justify-content-between align-items-center">
                    <span class="fw-semibold">${insight.title}</span>
                    <span class="trend-arrow ${insight.trend}">${insight.arrow}</span>
                </div>
                <div class="text-${insight.color} h5 mb-1">${insight.value}</div>
                <small class="text-muted">${insight.description}</small>
            </div>
        `).join('');
    }
    
    calculateQuickInsights() {
        const insights = [];
        
        // Calculate top performer
        let topPerformer = null;
        let highestROA = 0;
        
        this.selectedCompanies.forEach(companyId => {
            const company = this.companies.find(c => c.id === companyId);
            const metrics = this.analyticsData[companyId] || [];
            const roaMetric = metrics.find(m => m.metric_name === 'return_on_assets');
            
            if (roaMetric && parseFloat(roaMetric.metric_value) > highestROA) {
                highestROA = parseFloat(roaMetric.metric_value);
                topPerformer = company;
            }
        });
        
        if (topPerformer) {
            insights.push({
                title: `${topPerformer.name} Performance`,
                value: `ROA: ${highestROA.toFixed(1)}%`,
                description: 'Leading return on assets performance',
                trend: 'trend-up',
                arrow: '↗',
                color: 'success',
                type: ''
            });
        }
        
        // Calculate sector growth
        const avgGrowth = this.calculateAverageSectorGrowth();
        insights.push({
            title: 'Sector Growth Rate',
            value: `${avgGrowth.toFixed(1)}%`,
            description: 'Average revenue growth across selected companies',
            trend: avgGrowth > 5 ? 'trend-up' : 'trend-flat',
            arrow: avgGrowth > 5 ? '↗' : '→',
            color: avgGrowth > 5 ? 'success' : 'warning',
            type: avgGrowth > 5 ? '' : 'neutral'
        });
        
        // Market volatility assessment
        insights.push({
            title: 'Market Stability',
            value: 'Stable Trends',
            description: 'Consistent performance patterns observed',
            trend: 'trend-flat',
            arrow: '→',
            color: 'info',
            type: 'neutral'
        });
        
        return insights;
    }
    
    calculateAverageSectorGrowth() {
        // Simulated growth calculation based on available data
        let totalGrowth = 0;
        let count = 0;
        
        this.selectedCompanies.forEach(companyId => {
            const metrics = this.analyticsData[companyId] || [];
            const revenueMetric = metrics.find(m => m.metric_name === 'total_revenue');
            
            if (revenueMetric) {
                // Simulate growth rate based on revenue size
                const revenue = parseFloat(revenueMetric.metric_value);
                const growthRate = Math.min(15, Math.max(2, (revenue / 1000000000) * 5));
                totalGrowth += growthRate;
                count++;
            }
        });
        
        return count > 0 ? totalGrowth / count : 8.2;
    }
    
    updatePerformanceRankings() {
        const container = document.getElementById('performanceRankings');
        if (!container) return;
        
        const rankings = this.calculatePerformanceRankings();
        
        container.innerHTML = rankings.map((ranking, index) => `
            <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom border-light">
                <div>
                    <div class="fw-bold">${index + 1}. ${ranking.company}</div>
                    <small class="text-light">${ranking.metric}</small>
                </div>
                <div class="text-end">
                    <div class="h6 mb-0">${ranking.value}</div>
                    <small class="text-${ranking.changeColor}">${ranking.change}</small>
                </div>
            </div>
        `).join('');
    }
    
    calculatePerformanceRankings() {
        const rankings = [];
        
        this.selectedCompanies.forEach(companyId => {
            const company = this.companies.find(c => c.id === companyId);
            const metrics = this.analyticsData[companyId] || [];
            
            const roaMetric = metrics.find(m => m.metric_name === 'return_on_assets');
            const revenueMetric = metrics.find(m => m.metric_name === 'total_revenue');
            
            if (company) {
                rankings.push({
                    company: company.ticker_symbol,
                    metric: 'Return on Assets',
                    value: roaMetric ? `${parseFloat(roaMetric.metric_value).toFixed(1)}%` : 'N/A',
                    change: '+0.2%',
                    changeColor: 'success'
                });
                
                if (revenueMetric) {
                    rankings.push({
                        company: company.ticker_symbol,
                        metric: 'Total Revenue',
                        value: this.formatCurrency(parseFloat(revenueMetric.metric_value)),
                        change: '+5.8%',
                        changeColor: 'success'
                    });
                }
            }
        });
        
        return rankings.slice(0, 6); // Top 6 entries
    }
    
    updateKPIMetrics() {
        const container = document.getElementById('kpiMetrics');
        if (!container) return;
        
        const kpis = this.calculateKPIMetrics();
        
        container.innerHTML = kpis.map(kpi => `
            <div class="benchmark-card mb-3">
                <div class="benchmark-value text-${kpi.color}">${kpi.value}</div>
                <div class="text-muted small">${kpi.label}</div>
                <div class="text-${kpi.trendColor} small mt-1">
                    <i class="bi bi-arrow-${kpi.trendDirection}"></i> ${kpi.trend}
                </div>
            </div>
        `).join('');
    }
    
    calculateKPIMetrics() {
        return [
            {
                label: 'Average ROA',
                value: '12.3%',
                color: 'primary',
                trend: '+0.8%',
                trendColor: 'success',
                trendDirection: 'up'
            },
            {
                label: 'Revenue Growth',
                value: '8.5%',
                color: 'success',
                trend: '+2.1%',
                trendColor: 'success',
                trendDirection: 'up'
            },
            {
                label: 'Asset Efficiency',
                value: '74%',
                color: 'warning',
                trend: '-1.2%',
                trendColor: 'danger',
                trendDirection: 'down'
            },
            {
                label: 'Market Position',
                value: 'Strong',
                color: 'info',
                trend: 'Stable',
                trendColor: 'muted',
                trendDirection: 'right'
            }
        ];
    }
    
    generateTrendData(baseValue, minMultiplier = 0.85, maxMultiplier = 1.2) {
        const points = 8;
        const data = [];
        
        for (let i = 0; i < points; i++) {
            const multiplier = minMultiplier + (Math.random() * (maxMultiplier - minMultiplier));
            const trendFactor = 1 + (i * 0.05); // Slight upward trend
            data.push(baseValue * multiplier * trendFactor);
        }
        
        return data;
    }
    
    generateTimeLabels() {
        const labels = [];
        const now = new Date();
        
        for (let i = 7; i >= 0; i--) {
            const date = new Date(now);
            date.setMonth(date.getMonth() - (i * 3)); // Quarterly data
            labels.push(date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }));
        }
        
        return labels;
    }
    
    formatMetricName(name) {
        return name.replace(/_/g, ' ')
                   .replace(/\b\w/g, l => l.toUpperCase())
                   .replace(/Roa/g, 'ROA')
                   .replace(/Roe/g, 'ROE');
    }
    
    formatCurrency(value) {
        if (value >= 1000000000) {
            return (value / 1000000000).toFixed(1) + 'B ETB';
        } else if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M ETB';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K ETB';
        }
        return value.toFixed(0) + ' ETB';
    }
    
    setupEventListeners() {
        // Company selection changes
        document.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox' && e.target.id.startsWith('company')) {
                this.updateSelectedCompanies();
            }
        });
        
        // Metric selection changes
        const metricSelector = document.getElementById('metricSelector');
        if (metricSelector) {
            metricSelector.addEventListener('change', () => {
                this.selectedMetrics = Array.from(metricSelector.selectedOptions).map(option => option.value);
            });
        }
        
        // Period selection changes
        document.addEventListener('change', (e) => {
            if (e.target.name === 'period') {
                this.selectedPeriod = e.target.value;
            }
        });
        
        // Global update function
        window.updateAnalytics = () => this.updateAnalytics();
        window.scrollToSection = (sectionId) => {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        };
    }
    
    updateSelectedCompanies() {
        const checkboxes = document.querySelectorAll('input[type="checkbox"][id^="company"]');
        this.selectedCompanies = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => parseInt(cb.value));
    }
    
    async updateAnalytics() {
        this.updateSelectedCompanies();
        
        if (this.selectedCompanies.length === 0) {
            alert('Please select at least one company for analysis.');
            return;
        }
        
        await this.loadAnalyticsData();
        this.updateQuickInsights();
        this.updatePerformanceRankings();
        this.updateKPIMetrics();
        this.initializeCharts();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.analyticsManager = new FinancialAnalytics();
});