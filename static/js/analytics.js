/**
 * Complete Analytics Dashboard JavaScript
 * Handles all interactive charts, data fetching, and user interactions
 */

class AnalyticsDashboard {
    constructor() {
        this.selectedCompanies = [];
        this.currentMetrics = ['revenue', 'net_income', 'total_assets'];
        this.currentPeriod = '1Y';
        this.charts = {};
        this.companies = [];
        
        this.init();
    }

    async init() {
        try {
            await this.loadCompanies();
            await this.loadDashboardStats();
            this.setupEventListeners();
            this.renderCompanySelectors();
            
            // Auto-select first 3 companies and generate initial analytics
            if (this.companies.length >= 3) {
                this.selectedCompanies = [this.companies[0].id, this.companies[1].id, this.companies[2].id];
                
                // Check the first 3 company checkboxes
                this.selectedCompanies.forEach(companyId => {
                    const checkbox = document.getElementById(`company_${companyId}`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
                
                // Generate initial analytics with the selected companies
                await this.updateAnalytics();
            }
            
            console.log('Analytics Dashboard initialized successfully');
        } catch (error) {
            console.error('Failed to initialize analytics dashboard:', error);
            this.showError('Failed to load analytics dashboard');
        }
    }

    async loadCompanies() {
        try {
            const response = await fetch('/api/analytics/companies');
            const data = await response.json();
            
            if (data.success) {
                this.companies = data.companies;
                console.log(`Loaded ${this.companies.length} companies`);
            } else {
                throw new Error(data.error || 'Failed to load companies');
            }
        } catch (error) {
            console.error('Error loading companies:', error);
            throw error;
        }
    }

    async loadDashboardStats() {
        try {
            const response = await fetch('/api/analytics/dashboard-stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateDashboardStats(data.stats);
            } else {
                console.warn('Failed to load dashboard stats:', data.error);
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }

    updateDashboardStats(stats) {
        // Update ROA display
        const roaElement = document.querySelector('.roa-display');
        if (roaElement) {
            roaElement.innerHTML = `
                <div style="color: white; font-size: 3rem; font-weight: 700; margin-bottom: 0.5rem;">
                    ${stats.avg_roa}% <span style="color: white; font-size: 1.5rem; margin-left: 0.5rem;">↗</span>
                </div>
                <div style="color: white; font-weight: 500; margin-bottom: 1rem;">ROA: ${stats.avg_roa}%</div>
                <p class="mt-2 mb-0" style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Average return on assets</p>
            `;
        }

        // Update company count in insights
        const insightsElement = document.querySelector('.analytics-preview');
        if (insightsElement) {
            insightsElement.innerHTML = `
                <h6 class="fw-bold mb-3">Quick Insights</h6>
                <div class="d-flex justify-content-between mb-2">
                    <span class="fw-semibold">Active Companies</span>
                    <span class="text-primary">${stats.total_companies}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="fw-semibold">Financial Records</span>
                    <span class="text-success">${stats.total_records}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="fw-semibold">Market Volatility</span>
                    <span class="text-warning">${stats.market_volatility}</span>
                </div>
                <small class="text-muted">Last updated: ${stats.last_updated}</small>
            `;
        }
    }

    renderCompanySelectors() {
        const container = document.getElementById('companySelectors');
        if (!container || this.companies.length === 0) return;

        container.innerHTML = '';

        // Group companies by industry for better organization
        const companiesByIndustry = {};
        this.companies.forEach(company => {
            const industry = company.industry || 'Other';
            if (!companiesByIndustry[industry]) {
                companiesByIndustry[industry] = [];
            }
            companiesByIndustry[industry].push(company);
        });

        // Create checkboxes for each company
        Object.keys(companiesByIndustry).forEach(industry => {
            const industryDiv = document.createElement('div');
            industryDiv.className = 'col-12 mb-3';
            
            const industryHeader = document.createElement('h6');
            industryHeader.textContent = industry;
            industryHeader.className = 'text-white mb-2';
            industryDiv.appendChild(industryHeader);

            companiesByIndustry[industry].forEach(company => {
                const checkboxDiv = document.createElement('div');
                checkboxDiv.className = 'form-check mb-1';
                
                checkboxDiv.innerHTML = `
                    <input class="form-check-input company-checkbox" type="checkbox" 
                           value="${company.id}" id="company_${company.id}">
                    <label class="form-check-label text-white-50" for="company_${company.id}">
                        ${company.name} (${company.symbol})
                    </label>
                `;
                
                industryDiv.appendChild(checkboxDiv);
            });

            container.appendChild(industryDiv);
        });

        // Add event listeners to checkboxes
        const checkboxes = container.querySelectorAll('.company-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.handleCompanySelection(e);
            });
        });
    }

    handleCompanySelection(event) {
        const companyId = parseInt(event.target.value);
        
        if (event.target.checked) {
            if (!this.selectedCompanies.includes(companyId)) {
                this.selectedCompanies.push(companyId);
            }
        } else {
            this.selectedCompanies = this.selectedCompanies.filter(id => id !== companyId);
        }

        console.log('Selected companies:', this.selectedCompanies);
    }

    setupEventListeners() {
        // Period selector
        const periodInputs = document.querySelectorAll('input[name="period"]');
        periodInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.currentPeriod = e.target.value;
                console.log('Period changed to:', this.currentPeriod);
            });
        });

        // Metric selector
        const metricSelector = document.getElementById('metricSelector');
        if (metricSelector) {
            metricSelector.addEventListener('change', (e) => {
                this.currentMetrics = Array.from(e.target.selectedOptions).map(option => option.value);
                console.log('Metrics changed to:', this.currentMetrics);
            });
        }

        // Generate analytics button
        const generateBtn = document.querySelector('button[onclick="updateAnalytics()"]');
        if (generateBtn) {
            generateBtn.removeAttribute('onclick');
            generateBtn.addEventListener('click', () => {
                this.updateAnalytics();
            });
        }
    }

    async updateAnalytics() {
        if (this.selectedCompanies.length === 0) {
            this.showError('Please select at least one company');
            return;
        }

        try {
            this.showLoading(true);
            
            // Load financial metrics
            await this.loadFinancialMetrics();
            
            // Generate comparison if multiple companies selected
            if (this.selectedCompanies.length >= 2) {
                await this.generateComparison();
            }
            
            // Generate trend analysis for first selected company
            if (this.selectedCompanies.length >= 1) {
                await this.generateTrendAnalysis(this.selectedCompanies[0]);
            }
            
            this.showLoading(false);
            this.showSuccess('Analytics updated successfully');
            
        } catch (error) {
            console.error('Error updating analytics:', error);
            this.showError('Failed to update analytics');
            this.showLoading(false);
        }
    }

    async loadFinancialMetrics() {
        try {
            const response = await fetch('/api/analytics/metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_ids: this.selectedCompanies,
                    metrics: this.currentMetrics,
                    period: this.currentPeriod
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.renderMetricsChart(data.data);
            } else {
                throw new Error(data.error || 'Failed to load financial metrics');
            }
        } catch (error) {
            console.error('Error loading financial metrics:', error);
            throw error;
        }
    }

    async generateComparison() {
        try {
            const response = await fetch('/api/analytics/comparison', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_ids: this.selectedCompanies
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.renderComparisonChart(data.comparison);
            } else {
                throw new Error(data.error || 'Failed to generate comparison');
            }
        } catch (error) {
            console.error('Error generating comparison:', error);
            throw error;
        }
    }

    async generateTrendAnalysis(companyId) {
        try {
            const response = await fetch('/api/analytics/trends', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_id: companyId,
                    metric: 'total_revenue'
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.renderTrendChart(data.trends);
            } else {
                throw new Error(data.error || 'Failed to generate trend analysis');
            }
        } catch (error) {
            console.error('Error generating trend analysis:', error);
            throw error;
        }
    }

    renderMetricsChart(metricsData) {
        const canvas = document.getElementById('comparisonChart');
        if (!canvas) {
            console.error('Canvas element comparisonChart not found');
            return;
        }

        console.log('Rendering metrics chart with data:', metricsData);

        // Destroy existing chart
        if (this.charts.comparison) {
            this.charts.comparison.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        // Set canvas background to white
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Prepare data for chart
        const companies = Object.keys(metricsData);
        const datasets = [];
        
        // Create dataset for each metric
        this.currentMetrics.forEach((metric, index) => {
            const data = companies.map(company => {
                const latestPeriod = Object.keys(metricsData[company].metrics)[0];
                return metricsData[company].metrics[latestPeriod] ? 
                       metricsData[company].metrics[latestPeriod][metric] / 1000000 : 0; // Convert to millions
            });

            datasets.push({
                label: this.formatMetricName(metric),
                data: data,
                backgroundColor: this.getChartColor(index, 0.6),
                borderColor: this.getChartColor(index, 1),
                borderWidth: 2
            });
        });

        this.charts.comparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: companies.map(name => name.split(' ')[0]), // Shorten company names
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                backgroundColor: 'white',
                plugins: {
                    title: {
                        display: true,
                        text: 'Financial Metrics Comparison (Millions ETB)',
                        color: '#075056',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#075056'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Amount (Millions ETB)',
                            color: '#075056'
                        },
                        ticks: {
                            color: '#075056',
                            callback: function(value) {
                                return value.toLocaleString() + 'M';
                            }
                        },
                        grid: {
                            color: 'rgba(7, 80, 86, 0.1)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Companies',
                            color: '#075056'
                        },
                        ticks: {
                            color: '#075056'
                        },
                        grid: {
                            color: 'rgba(7, 80, 86, 0.1)'
                        }
                    }
                }
            }
        });
        
        console.log('Chart created successfully:', this.charts.comparison);
    }

    renderComparisonChart(comparisonData) {
        const canvas = document.getElementById('sectorChart');
        if (!canvas) return;

        // Destroy existing chart
        if (this.charts.sector) {
            this.charts.sector.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.sector = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Revenue', 'Net Income', 'Total Assets', 'ROA', 'ROE'],
                datasets: comparisonData.map((company, index) => ({
                    label: company.name,
                    data: [
                        company.total_revenue / 1000000, // Convert to millions
                        company.net_income / 1000000,
                        company.total_assets / 1000000,
                        company.roa,
                        company.roe
                    ],
                    backgroundColor: this.getChartColor(index, 0.2),
                    borderColor: this.getChartColor(index, 1),
                    borderWidth: 2
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Company Performance Comparison'
                    }
                }
            }
        });
    }

    renderTrendChart(trendData) {
        const canvas = document.getElementById('trendChart');
        if (!canvas) return;

        // Destroy existing chart
        if (this.charts.trend) {
            this.charts.trend.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendData.map(point => point.period),
                datasets: [{
                    label: 'Revenue (Millions ETB)',
                    data: trendData.map(point => point.total_revenue / 1000000),
                    backgroundColor: 'rgba(7, 80, 86, 0.1)',
                    borderColor: '#075056',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#075056',
                    pointBorderColor: '#075056',
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue Trend Analysis',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Revenue (Millions ETB)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + 'M';
                            }
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Period'
                        }
                    }
                }
            }
        });
    }

    getChartColor(index, alpha = 1) {
        const colors = [
            `rgba(7, 80, 86, ${alpha})`,      // Midnight Green
            `rgba(255, 91, 4, ${alpha})`,     // Orange Pantone
            `rgba(244, 212, 124, ${alpha})`,  // Sand Yellow
            `rgba(35, 48, 56, ${alpha})`,     // Gunmetal
            `rgba(211, 219, 221, ${alpha})`,  // Light Silver
            `rgba(253, 246, 227, ${alpha})`   // Ivory Cream
        ];
        return colors[index % colors.length];
    }

    formatMetricName(metric) {
        const names = {
            'revenue': 'Revenue',
            'total_revenue': 'Total Revenue',
            'net_income': 'Net Income',
            'total_assets': 'Total Assets',
            'return_on_assets': 'Return on Assets (%)',
            'return_on_equity': 'Return on Equity (%)',
            'market_cap': 'Market Capitalization'
        };
        return names[metric] || metric.replace('_', ' ').toUpperCase();
    }

    showLoading(show) {
        const button = document.querySelector('button[onclick="updateAnalytics()"]') || 
                      document.querySelector('.btn[onclick="updateAnalytics()"]');
        
        if (button) {
            if (show) {
                button.disabled = true;
                button.innerHTML = '<i class="spinner-border spinner-border-sm me-2"></i>Generating...';
            } else {
                button.disabled = false;
                button.innerHTML = '<i class="bi bi-graph-up-arrow me-2"></i>Generate Analytics';
            }
        }

        // Show loading on chart containers
        const chartContainers = [
            document.getElementById('comparisonChart'),
            document.getElementById('sectorChart'),
            document.getElementById('trendChart')
        ];

        chartContainers.forEach(canvas => {
            if (canvas) {
                const container = canvas.closest('.chart-container');
                if (container) {
                    if (show) {
                        container.style.opacity = '0.5';
                    } else {
                        container.style.opacity = '1';
                    }
                }
            }
        });
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Scroll functions for navigation
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.analyticsManager = new AnalyticsDashboard();
});

// Legacy function for backward compatibility
function updateAnalytics() {
    if (window.analyticsManager) {
        window.analyticsManager.updateAnalytics();
    }
}