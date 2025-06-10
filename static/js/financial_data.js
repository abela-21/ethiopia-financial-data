/**
 * Financial Data Download Interface
 * Handles company data loading, metrics display, and download functionality
 */

class FinancialDataManager {
    constructor() {
        this.companies = [];
        this.selectedCompanyId = null;
        this.selectedCompanyData = null;
        this.baseApiUrl = '/api/financial';
        
        this.init();
    }
    
    async init() {
        await this.loadCompanies();
        this.renderCompanies();
        this.setupEventListeners();
    }
    
    async loadCompanies() {
        try {
            const response = await fetch(`${this.baseApiUrl}/companies`);
            const data = await response.json();
            
            if (data.data) {
                this.companies = data.data;
                this.updateStats(data.metadata);
            } else {
                console.error('Failed to load companies:', data.error);
            }
        } catch (error) {
            console.error('Error loading companies:', error);
            this.showError('Failed to load company data. Please try again.');
        }
    }
    
    updateStats(metadata) {
        if (metadata) {
            document.getElementById('totalCompanies').textContent = this.companies.length;
            
            const totalMetrics = this.companies.reduce((sum, company) => 
                sum + (company.available_metrics || 0), 0);
            document.getElementById('totalMetrics').textContent = totalMetrics;
            
            if (metadata.total_market_cap) {
                const marketCapFormatted = (metadata.total_market_cap / 1000000000).toFixed(0) + 'B';
                document.querySelector('.stat-number:last-child').textContent = marketCapFormatted;
            }
        }
    }
    
    renderCompanies() {
        const grid = document.getElementById('companiesGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        this.companies.forEach(company => {
            const card = this.createCompanyCard(company);
            grid.appendChild(card);
        });
        
        this.renderCompanyCheckboxes();
    }
    
    createCompanyCard(company) {
        const col = document.createElement('div');
        col.className = 'col-lg-4 col-md-6 mb-4';
        
        const sectorColors = {
            'Banking': '#28a745',
            'Telecommunications': '#007bff',
            'Transportation': '#17a2b8',
            'Consumer Goods': '#ffc107',
            'Materials': '#6c757d'
        };
        
        const sectorColor = sectorColors[company.sector] || '#6c757d';
        
        col.innerHTML = `
            <div class="card company-card h-100" style="border-left: 4px solid ${sectorColor};">
                <div class="card-body position-relative">
                    <span class="sector-badge">${company.sector}</span>
                    <h5 class="card-title fw-bold mb-2">${company.name}</h5>
                    <p class="card-text text-muted mb-3">${company.ticker_symbol} • ${company.industry}</p>
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted d-block">Market Cap</small>
                            <strong>${company.market_cap_formatted || 'N/A'}</strong>
                        </div>
                        <div class="col-6">
                            <small class="text-muted d-block">Headquarters</small>
                            <strong>${company.headquarters || 'N/A'}</strong>
                        </div>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted d-block">Available Metrics</small>
                            <span class="badge bg-primary">${company.available_metrics || 0}</span>
                        </div>
                        <div class="col-6">
                            <small class="text-muted d-block">Employees</small>
                            <strong>${company.employee_count ? company.employee_count.toLocaleString() : 'N/A'}</strong>
                        </div>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary" onclick="financialDataManager.viewCompanyDetails(${company.id})">
                            <i class="bi bi-eye me-2"></i>View Details
                        </button>
                        <button class="btn btn-outline-secondary" onclick="financialDataManager.downloadSingleCompany(${company.id})">
                            <i class="bi bi-download me-2"></i>Download Data
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return col;
    }
    
    renderCompanyCheckboxes() {
        const container = document.getElementById('companyCheckboxes');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.companies.forEach(company => {
            const col = document.createElement('div');
            col.className = 'col-md-6 mb-2';
            
            col.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${company.id}" 
                           id="company${company.id}" checked>
                    <label class="form-check-label" for="company${company.id}">
                        ${company.name} (${company.ticker_symbol})
                    </label>
                </div>
            `;
            
            container.appendChild(col);
        });
    }
    
    async viewCompanyDetails(companyId) {
        this.selectedCompanyId = companyId;
        const company = this.companies.find(c => c.id === companyId);
        
        if (!company) {
            this.showError('Company not found');
            return;
        }
        
        try {
            // Load company financial metrics
            const response = await fetch(`${this.baseApiUrl}/companies/${companyId}/metrics`);
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            this.selectedCompanyData = data;
            this.renderCompanyModal(company, data);
            
            const modal = new bootstrap.Modal(document.getElementById('companyModal'));
            modal.show();
            
        } catch (error) {
            console.error('Error loading company details:', error);
            this.showError('Failed to load company details');
        }
    }
    
    renderCompanyModal(company, financialData) {
        const title = document.getElementById('companyModalTitle');
        const details = document.getElementById('companyDetails');
        const metrics = document.getElementById('financialMetrics');
        
        title.textContent = `${company.name} (${company.ticker_symbol})`;
        
        // Company details
        details.innerHTML = `
            <div class="mb-3">
                <strong>Sector:</strong> ${company.sector}<br>
                <strong>Industry:</strong> ${company.industry}<br>
                <strong>Market Cap:</strong> ${company.market_cap_formatted}<br>
                <strong>Employees:</strong> ${company.employee_count?.toLocaleString() || 'N/A'}<br>
                <strong>Fiscal Year End:</strong> ${company.fiscal_year_end || 'N/A'}<br>
                <strong>Website:</strong> ${company.website_url ? 
                    `<a href="${company.website_url}" target="_blank">${company.website_url}</a>` : 'N/A'}
            </div>
            ${company.description ? `<p class="text-muted small">${company.description}</p>` : ''}
        `;
        
        // Financial metrics
        if (financialData.data && financialData.data.length > 0) {
            const groupedMetrics = this.groupMetricsByType(financialData.data);
            
            let metricsHtml = '';
            Object.keys(groupedMetrics).forEach(category => {
                metricsHtml += `
                    <div class="metric-category mb-4">
                        <h6 class="fw-bold text-primary mb-3">${category}</h6>
                        <div class="row">
                `;
                
                groupedMetrics[category].forEach(metric => {
                    metricsHtml += `
                        <div class="col-md-6 mb-3">
                            <div class="financial-metric">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="fw-semibold">${this.formatMetricName(metric.metric_name)}</span>
                                    <span class="text-muted small">${metric.reporting_period}</span>
                                </div>
                                <div class="metric-value h5 mb-1 text-success">
                                    ${metric.metric_value_formatted} ${metric.metric_unit}
                                </div>
                                <small class="text-muted">
                                    Source: ${metric.data_source}
                                    ${metric.is_audited ? ' • Audited' : ''}
                                </small>
                            </div>
                        </div>
                    `;
                });
                
                metricsHtml += `
                        </div>
                    </div>
                `;
            });
            
            metrics.innerHTML = metricsHtml;
        } else {
            metrics.innerHTML = '<p class="text-muted">No financial metrics available for this company.</p>';
        }
    }
    
    groupMetricsByType(metrics) {
        const groups = {
            'Financial Performance': [],
            'Balance Sheet': [],
            'Operational Metrics': [],
            'Banking Specific': [],
            'Performance Ratios': []
        };
        
        metrics.forEach(metric => {
            const name = metric.metric_name.toLowerCase();
            
            if (name.includes('revenue') || name.includes('income') || name.includes('profit') || name.includes('earnings')) {
                groups['Financial Performance'].push(metric);
            } else if (name.includes('assets') || name.includes('liabilities') || name.includes('equity') || name.includes('deposits')) {
                groups['Balance Sheet'].push(metric);
            } else if (name.includes('subscribers') || name.includes('coverage') || name.includes('arpu') || name.includes('ebitda')) {
                groups['Operational Metrics'].push(metric);
            } else if (name.includes('npl') || name.includes('capital_adequacy') || name.includes('loans') || name.includes('advances')) {
                groups['Banking Specific'].push(metric);
            } else if (name.includes('ratio') || name.includes('return_on')) {
                groups['Performance Ratios'].push(metric);
            } else {
                groups['Financial Performance'].push(metric);
            }
        });
        
        // Remove empty groups
        Object.keys(groups).forEach(key => {
            if (groups[key].length === 0) {
                delete groups[key];
            }
        });
        
        return groups;
    }
    
    formatMetricName(name) {
        return name.replace(/_/g, ' ')
                   .replace(/\b\w/g, l => l.toUpperCase())
                   .replace(/Npl/g, 'NPL')
                   .replace(/Car/g, 'CAR')
                   .replace(/Roa/g, 'ROA')
                   .replace(/Roe/g, 'ROE')
                   .replace(/Arpu/g, 'ARPU')
                   .replace(/Ebitda/g, 'EBITDA');
    }
    
    async downloadSingleCompany(companyId) {
        const company = this.companies.find(c => c.id === companyId);
        
        if (!company) {
            this.showError('Company not found');
            return;
        }
        
        try {
            const downloadData = {
                company_ids: [companyId],
                metric_names: [],
                fiscal_years: [],
                format: 'excel'
            };
            
            const response = await fetch(`${this.baseApiUrl}/download/metrics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(downloadData)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `${company.ticker_symbol}_financial_data_${new Date().toISOString().split('T')[0]}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showSuccess(`Downloaded financial data for ${company.name}`);
            } else {
                const errorData = await response.json();
                this.showError(errorData.error || 'Download failed');
            }
            
        } catch (error) {
            console.error('Download error:', error);
            this.showError('Failed to download data');
        }
    }
    
    async downloadCompanyData() {
        if (!this.selectedCompanyId) {
            this.showError('No company selected');
            return;
        }
        
        await this.downloadSingleCompany(this.selectedCompanyId);
        
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('companyModal'));
        if (modal) {
            modal.hide();
        }
    }
    
    async downloadBulkData() {
        const selectedCompanies = this.getSelectedCompanies();
        const selectedMetrics = this.getSelectedMetrics();
        const format = document.querySelector('input[name="format"]:checked').value;
        
        if (selectedCompanies.length === 0) {
            this.showError('Please select at least one company');
            return;
        }
        
        try {
            const downloadData = {
                company_ids: selectedCompanies,
                metric_names: selectedMetrics,
                fiscal_years: [],
                format: format
            };
            
            const response = await fetch(`${this.baseApiUrl}/download/metrics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(downloadData)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                
                const extension = format === 'excel' ? 'xlsx' : 'csv';
                a.download = `ethiopian_financial_data_${new Date().toISOString().split('T')[0]}.${extension}`;
                
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showSuccess(`Downloaded financial data for ${selectedCompanies.length} companies`);
            } else {
                const errorData = await response.json();
                this.showError(errorData.error || 'Download failed');
            }
            
        } catch (error) {
            console.error('Bulk download error:', error);
            this.showError('Failed to download bulk data');
        }
    }
    
    getSelectedCompanies() {
        const checkboxes = document.querySelectorAll('#companyCheckboxes input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.value));
    }
    
    getSelectedMetrics() {
        const metricCheckboxes = document.querySelectorAll('input[id^="metric"]:checked');
        const selectedTypes = Array.from(metricCheckboxes).map(cb => cb.value);
        
        // Map metric types to actual metric names
        const metricMapping = {
            'revenue': ['total_revenue', 'net_income', 'gross_profit', 'operating_income'],
            'assets': ['total_assets', 'current_assets', 'shareholders_equity', 'deposits'],
            'ratios': ['return_on_assets', 'return_on_equity', 'capital_adequacy_ratio', 'npl_ratio'],
            'banking': ['deposits', 'loans_and_advances', 'net_interest_income', 'loan_loss_provisions'],
            'telecom': ['mobile_subscribers', 'internet_subscribers', 'arpu', 'network_coverage']
        };
        
        let allMetrics = [];
        selectedTypes.forEach(type => {
            if (metricMapping[type]) {
                allMetrics = allMetrics.concat(metricMapping[type]);
            }
        });
        
        return [...new Set(allMetrics)]; // Remove duplicates
    }
    
    setupEventListeners() {
        // Scroll to section functionality
        window.scrollToSection = (sectionId) => {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        };
        
        // Global download functions
        window.downloadCompanyData = () => this.downloadCompanyData();
        window.downloadBulkData = () => this.downloadBulkData();
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
    }
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.financialDataManager = new FinancialDataManager();
});