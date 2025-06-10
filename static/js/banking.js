// Banking Sector Analysis JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize banking page
    initializeBankingFilters();
    loadBankingData();
    loadSectorOverview();
    
    // Set up event listeners
    setupEventListeners();
});

function initializeBankingFilters() {
    const filterForm = document.getElementById('banking-filters');
    if (!filterForm) return;
    
    // Add change event listeners to all filter inputs
    const filterInputs = filterForm.querySelectorAll('select, input');
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            loadBankingData();
        });
    });
}

function setupEventListeners() {
    // Export buttons
    const exportCsvBtn = document.getElementById('export-csv');
    const exportExcelBtn = document.getElementById('export-excel');
    
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => exportBankingData('csv'));
    }
    
    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', () => exportBankingData('excel'));
    }
}

async function loadBankingData() {
    const tbody = document.getElementById('banking-tbody');
    if (!tbody) return;
    
    // Show loading state
    tbody.innerHTML = `
        <tr>
            <td colspan="9" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading banks...</span>
                </div>
            </td>
        </tr>
    `;
    
    try {
        // Get filter values
        const filters = getFilterValues();
        const queryParams = new URLSearchParams(filters);
        
        const response = await fetch(`/api/banking/banks?${queryParams}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        renderBankingTable(data.data);
        updateBankingStats(data.data);
        
    } catch (error) {
        console.error('Error loading banking data:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4 text-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading banking data. Please try again.
                </td>
            </tr>
        `;
    }
}

function getFilterValues() {
    const form = document.getElementById('banking-filters');
    if (!form) return {};
    
    const formData = new FormData(form);
    const filters = {};
    
    for (let [key, value] of formData.entries()) {
        if (value.trim() !== '') {
            filters[key] = value;
        }
    }
    
    return filters;
}

function renderBankingTable(banks) {
    const tbody = document.getElementById('banking-tbody');
    if (!tbody || !banks) return;
    
    if (banks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4 text-muted">
                    <i class="fas fa-search me-2"></i>
                    No banks found matching your criteria.
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = banks.map(bank => `
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    <div>
                        <h6 class="mb-0">${escapeHtml(bank.name)}</h6>
                        <small class="text-muted">${escapeHtml(bank.license_number || '')}</small>
                    </div>
                </div>
            </td>
            <td><span class="badge bg-primary">${escapeHtml(bank.bank_type || '')}</span></td>
            <td><span class="badge bg-info">${escapeHtml(bank.ownership_type || '')}</span></td>
            <td>
                <span class="badge ${getRatingBadgeClass(bank.nbe_rating)}">
                    ${escapeHtml(bank.nbe_rating || 'N/A')}
                </span>
            </td>
            <td>${(bank.branch_count || 0).toLocaleString()}</td>
            <td>${(bank.atm_count || 0).toLocaleString()}</td>
            <td>${(bank.digital_banking_users || 0).toLocaleString()}</td>
            <td>${formatDate(bank.establishment_date)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="viewBankDetails(${bank.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${bank.website_url ? `
                        <a href="${escapeHtml(bank.website_url)}" target="_blank" class="btn btn-outline-success" title="Visit Website">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

function getRatingBadgeClass(rating) {
    if (!rating) return 'bg-secondary';
    
    switch (rating.charAt(0)) {
        case 'A': return 'bg-success';
        case 'B': return 'bg-warning';
        case 'C': return 'bg-danger';
        default: return 'bg-secondary';
    }
}

function updateBankingStats(banks) {
    // Update summary statistics
    const totalBanks = document.getElementById('total-banks');
    const totalBranches = document.getElementById('total-branches');
    const digitalUsers = document.getElementById('digital-users');
    
    if (totalBanks) totalBanks.textContent = banks.length;
    
    if (banks.length > 0) {
        const totalBranchCount = banks.reduce((sum, bank) => sum + (bank.branch_count || 0), 0);
        const totalDigitalUsers = banks.reduce((sum, bank) => sum + (bank.digital_banking_users || 0), 0);
        
        if (totalBranches) totalBranches.textContent = totalBranchCount.toLocaleString() + '+';
        if (digitalUsers) digitalUsers.textContent = (totalDigitalUsers / 1000000).toFixed(1) + 'M+';
    }
}

async function loadSectorOverview() {
    const sectorMetrics = document.getElementById('sector-metrics');
    if (!sectorMetrics) return;
    
    try {
        const response = await fetch('/api/banking/banking-sector/overview');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        renderSectorOverview(data);
        
    } catch (error) {
        console.error('Error loading sector overview:', error);
        sectorMetrics.innerHTML = `
            <div class="col-12 text-center">
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Unable to load sector overview at this time.
                </div>
            </div>
        `;
    }
}

function renderSectorOverview(data) {
    const sectorMetrics = document.getElementById('sector-metrics');
    if (!sectorMetrics || !data) return;
    
    sectorMetrics.innerHTML = `
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body text-center">
                    <h5 class="card-title text-primary">Total Assets</h5>
                    <h3 class="display-6 fw-bold">${data.sector_assets ? (data.sector_assets / 1000000000).toFixed(1) + 'B ETB' : 'N/A'}</h3>
                    <p class="text-muted mb-0">Banking Sector</p>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body text-center">
                    <h5 class="card-title text-success">Loan Portfolio</h5>
                    <h3 class="display-6 fw-bold">${data.total_loans ? (data.total_loans / 1000000000).toFixed(1) + 'B ETB' : 'N/A'}</h3>
                    <p class="text-muted mb-0">Outstanding Loans</p>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body text-center">
                    <h5 class="card-title text-warning">NPL Ratio</h5>
                    <h3 class="display-6 fw-bold">${data.avg_npl_ratio ? data.avg_npl_ratio.toFixed(1) + '%' : 'N/A'}</h3>
                    <p class="text-muted mb-0">Average</p>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body text-center">
                    <h5 class="card-title text-info">Capital Adequacy</h5>
                    <h3 class="display-6 fw-bold">${data.avg_car ? data.avg_car.toFixed(1) + '%' : 'N/A'}</h3>
                    <p class="text-muted mb-0">Average CAR</p>
                </div>
            </div>
        </div>
    `;
}

async function exportBankingData(format) {
    try {
        const filters = getFilterValues();
        const queryParams = new URLSearchParams(filters);
        queryParams.append('export', format);
        
        const response = await fetch(`/api/banking/banks?${queryParams}`);
        
        if (format === 'csv') {
            const csvData = await response.text();
            downloadFile(csvData, 'ethiopian_banks.csv', 'text/csv');
        } else if (format === 'excel') {
            const blob = await response.blob();
            downloadFile(blob, 'ethiopian_banks.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        }
        
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Error exporting data. Please try again.');
    }
}

function viewBankDetails(bankId) {
    // Navigate to bank details page or show modal
    window.location.href = `/banking/${bankId}`;
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, function(m) { return map[m]; });
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.getFullYear();
}

function downloadFile(data, filename, mimeType) {
    const blob = data instanceof Blob ? data : new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}