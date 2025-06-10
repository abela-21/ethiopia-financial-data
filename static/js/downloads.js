// Downloads page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Load companies for dropdowns
    loadCompanies();
    
    // Handle variable selection for financial data
    const varAllCheckbox = document.getElementById('var_all');
    if (varAllCheckbox) {
        varAllCheckbox.addEventListener('change', function() {
            const financialCheckboxes = document.querySelectorAll('#financialsForm input[type="checkbox"]:not(#var_all)');
            financialCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
});

async function loadCompanies() {
    try {
        const response = await fetch('/api/companies?per_page=1000');
        const data = await response.json();
        
        const stockCompanySelect = document.getElementById('stockCompany');
        const financialCompanySelect = document.getElementById('financialCompany');
        
        if (stockCompanySelect && data.companies) {
            data.companies.forEach(company => {
                const option = document.createElement('option');
                option.value = company.id;
                option.textContent = `${company.name} (${company.ticker})`;
                stockCompanySelect.appendChild(option);
            });
        }
        
        if (financialCompanySelect && data.companies) {
            data.companies.forEach(company => {
                const option = document.createElement('option');
                option.value = company.id;
                option.textContent = `${company.name} (${company.ticker})`;
                financialCompanySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading companies:', error);
    }
}

function downloadCompanies(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    for (const [key, value] of formData.entries()) {
        if (value) params.append(key, value);
    }
    
    const url = `/api/download/companies?${params.toString()}`;
    downloadFile(url, 'companies');
}

function downloadMacro(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    // Handle basic form fields
    for (const [key, value] of formData.entries()) {
        if (value && key !== 'variables') {
            params.append(key, value);
        }
    }
    
    // Handle variable selection from multi-select dropdown
    const variableSelect = document.getElementById('macroVariables');
    const selectedVariables = Array.from(variableSelect.selectedOptions)
        .map(option => option.value)
        .filter(value => value !== ''); // Remove empty "All Variables" option
    
    if (selectedVariables.length > 0) {
        params.append('variables', selectedVariables.join(','));
    }
    
    const url = `/api/download/macro_indicators?${params.toString()}`;
    downloadFile(url, 'macro_indicators');
}

function downloadFinancials(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    // Handle basic form fields
    for (const [key, value] of formData.entries()) {
        if (value && key !== 'variables') {
            params.append(key, value);
        }
    }
    
    // Handle variable selection
    const selectedVariables = [];
    const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked:not(#var_all)');
    checkboxes.forEach(checkbox => {
        selectedVariables.push(checkbox.value);
    });
    
    if (selectedVariables.length > 0 && !selectedVariables.includes('all')) {
        params.append('variables', selectedVariables.join(','));
    }
    
    const url = `/api/download/financials?${params.toString()}`;
    downloadFile(url, 'financials');
}

function downloadStocks(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    for (const [key, value] of formData.entries()) {
        if (value) {
            // Map form field names to API parameter names
            if (key === 'start_date') {
                params.append('date_from', value);
            } else if (key === 'end_date') {
                params.append('date_to', value);
            } else {
                params.append(key, value);
            }
        }
    }
    
    const url = `/api/download/stocks?${params.toString()}`;
    downloadFile(url, 'stocks');
}

// Helper function to handle file downloads properly
function downloadFile(url, dataType) {
    // Show loading indicator
    const button = event.target.querySelector('button[type="submit"]') || event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Downloading...';
    button.disabled = true;
    
    // Create a temporary link element to trigger download
    const link = document.createElement('a');
    link.href = url;
    link.style.display = 'none';
    document.body.appendChild(link);
    
    // Handle the download
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Extract filename from response headers
            const contentDisposition = response.headers.get('content-disposition');
            let filename = `${dataType}.csv`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match) {
                    filename = match[1].replace(/['"]/g, '');
                }
            }
            
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            // Create object URL and trigger download
            const downloadUrl = window.URL.createObjectURL(blob);
            link.href = downloadUrl;
            link.download = filename;
            link.click();
            
            // Cleanup
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(link);
        })
        .catch(error => {
            console.error('Download error:', error);
            alert('Download failed. Please try again.');
        })
        .finally(() => {
            // Reset button
            button.innerHTML = originalText;
            button.disabled = false;
        });
}