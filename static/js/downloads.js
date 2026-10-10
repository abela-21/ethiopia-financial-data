// Downloads page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Load companies for dropdowns
    loadCompanies();

    // "All Variables" toggles the financial variable checkboxes
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

        ['stockCompany', 'financialCompany'].forEach(id => {
            const select = document.getElementById(id);
            if (!select || !data.companies) return;
            data.companies.forEach(company => {
                select.appendChild(new Option(`${company.name} (${company.ticker})`, company.id));
            });
        });
    } catch (error) {
        console.error('Error loading companies:', error);
    }
}

// Form values as query parameters, skipping blanks (multi-selects repeat the key).
function formParams(form, skip = []) {
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form).entries()) {
        if (!skip.includes(key) && String(value).trim()) {
            params.append(key, value);
        }
    }
    return params;
}

function downloadCompanies(event) {
    event.preventDefault();
    downloadFile(`/api/download/companies?${formParams(event.target)}`, event.target);
}

function downloadMacro(event) {
    event.preventDefault();
    downloadFile(`/api/download/macro_indicators?${formParams(event.target)}`, event.target);
}

function downloadFinancials(event) {
    event.preventDefault();
    // Company is optional: blank downloads every company's financials.
    downloadFile(`/api/download/financials?${formParams(event.target)}`, event.target);
}

function downloadStocks(event) {
    event.preventDefault();
    const companyId = new FormData(event.target).get('company_id');
    if (!companyId) {
        alert('Please select a company');
        return;
    }
    downloadFile(`/api/download/stocks/${companyId}?${formParams(event.target, ['company_id'])}`, event.target);
}

async function downloadFile(url, form) {
    const button = form.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Downloading...';
    button.disabled = true;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            throw new Error(result.error || `Download failed (HTTP ${response.status})`);
        }
        const disposition = response.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
        const filename = match ? decodeURIComponent(match[1]) : 'download';

        const blob = await response.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        // Give the browser time to start the download before releasing the blob.
        setTimeout(() => URL.revokeObjectURL(link.href), 10000);
    } catch (error) {
        console.error('Download error:', error);
        alert(error.message);
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Macro variables selection helper functions
function selectAllMacroVariables() {
    const select = document.getElementById('macroVariables');
    for (let option of select.options) {
        option.selected = true;
    }
}

function clearAllMacroVariables() {
    const select = document.getElementById('macroVariables');
    for (let option of select.options) {
        option.selected = false;
    }
}
