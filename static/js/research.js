// Research Documents JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize research page
    initializeResearchFilters();
    loadResearchDocuments();
    loadDocumentCategories();
    
    // Set up event listeners
    setupEventListeners();
});

function initializeResearchFilters() {
    const filterForm = document.getElementById('research-filters');
    if (!filterForm) return;
    
    // Add change event listeners to all filter inputs
    const filterInputs = filterForm.querySelectorAll('select, input');
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            loadResearchDocuments();
        });
        
        // For search input, add debounce
        if (input.type === 'text') {
            let timeout;
            input.addEventListener('input', function() {
                clearTimeout(timeout);
                timeout = setTimeout(() => loadResearchDocuments(), 500);
            });
        }
    });
}

function setupEventListeners() {
    // View toggle buttons
    const gridViewBtn = document.getElementById('grid-view');
    const listViewBtn = document.getElementById('list-view');
    
    if (gridViewBtn && listViewBtn) {
        gridViewBtn.addEventListener('click', () => setViewMode('grid'));
        listViewBtn.addEventListener('click', () => setViewMode('list'));
    }
    
    // Category cards
    const categoryCards = document.querySelectorAll('.category-card');
    categoryCards.forEach(card => {
        card.addEventListener('click', function() {
            const category = this.dataset.category;
            filterByCategory(category);
        });
    });
}

function setViewMode(mode) {
    const gridBtn = document.getElementById('grid-view');
    const listBtn = document.getElementById('list-view');
    
    if (mode === 'grid') {
        gridBtn.classList.add('active');
        listBtn.classList.remove('active');
    } else {
        listBtn.classList.add('active');
        gridBtn.classList.remove('active');
    }
    
    // Store preference
    localStorage.setItem('research-view-mode', mode);
    
    // Re-render with new view mode
    loadResearchDocuments();
}

function filterByCategory(category) {
    const documentTypeSelect = document.getElementById('documentType');
    if (documentTypeSelect) {
        documentTypeSelect.value = category;
        loadResearchDocuments();
    }
}

async function loadResearchDocuments() {
    const researchGrid = document.getElementById('research-grid');
    if (!researchGrid) return;
    
    // Show loading state
    researchGrid.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading research documents...</span>
            </div>
        </div>
    `;
    
    try {
        // Get filter values
        const filters = getFilterValues();
        const queryParams = new URLSearchParams(filters);
        
        const response = await fetch(`/api/research/documents?${queryParams}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const viewMode = localStorage.getItem('research-view-mode') || 'grid';
        renderResearchDocuments(data.data, viewMode);
        renderPagination(data.pagination);
        
    } catch (error) {
        console.error('Error loading research documents:', error);
        researchGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading research documents. Please try again.
                </div>
            </div>
        `;
    }
}

function getFilterValues() {
    const form = document.getElementById('research-filters');
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

function renderResearchDocuments(documents, viewMode = 'grid') {
    const researchGrid = document.getElementById('research-grid');
    if (!researchGrid || !documents) return;
    
    if (documents.length === 0) {
        researchGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="text-muted">
                    <i class="fas fa-search fa-3x mb-3"></i>
                    <h5>No documents found</h5>
                    <p>Try adjusting your search criteria or filters.</p>
                </div>
            </div>
        `;
        return;
    }
    
    if (viewMode === 'list') {
        renderListView(documents);
    } else {
        renderGridView(documents);
    }
}

function renderGridView(documents) {
    const researchGrid = document.getElementById('research-grid');
    
    researchGrid.innerHTML = documents.map(doc => `
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card h-100 shadow-sm border-0 document-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <span class="badge bg-primary">${formatDocumentType(doc.document_type)}</span>
                        <span class="badge bg-secondary">${formatEntityType(doc.entity_type)}</span>
                    </div>
                    
                    <h5 class="card-title">${escapeHtml(doc.title)}</h5>
                    <p class="card-text text-muted">${escapeHtml(doc.summary || '').substring(0, 150)}${doc.summary && doc.summary.length > 150 ? '...' : ''}</p>
                    
                    <div class="document-meta mb-3">
                        <small class="text-muted">
                            <i class="fas fa-calendar me-1"></i>
                            ${formatDate(doc.publication_date)}
                        </small>
                        <br>
                        <small class="text-muted">
                            <i class="fas fa-download me-1"></i>
                            ${(doc.download_count || 0).toLocaleString()} downloads
                        </small>
                        <br>
                        <small class="text-muted">
                            <i class="fas fa-file me-1"></i>
                            ${formatFileSize(doc.file_size)}
                        </small>
                    </div>
                    
                    ${doc.keywords && doc.keywords.length > 0 ? `
                        <div class="keywords mb-3">
                            ${doc.keywords.slice(0, 3).map(keyword => 
                                `<span class="badge bg-light text-dark me-1">${escapeHtml(keyword)}</span>`
                            ).join('')}
                        </div>
                    ` : ''}
                </div>
                
                <div class="card-footer bg-transparent">
                    <div class="d-flex justify-content-between">
                        <button class="btn btn-outline-primary btn-sm" onclick="viewDocumentDetails(${doc.id})">
                            <i class="fas fa-eye me-1"></i>Details
                        </button>
                        <a href="${escapeHtml(doc.file_url)}" target="_blank" class="btn btn-primary btn-sm" onclick="trackDownload(${doc.id})">
                            <i class="fas fa-download me-1"></i>Download
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function renderListView(documents) {
    const researchGrid = document.getElementById('research-grid');
    
    researchGrid.innerHTML = `
        <div class="col-12">
            <div class="list-group">
                ${documents.map(doc => `
                    <div class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <div class="flex-grow-1">
                                <div class="d-flex align-items-center mb-2">
                                    <h5 class="mb-1 me-3">${escapeHtml(doc.title)}</h5>
                                    <span class="badge bg-primary me-2">${formatDocumentType(doc.document_type)}</span>
                                    <span class="badge bg-secondary">${formatEntityType(doc.entity_type)}</span>
                                </div>
                                <p class="mb-2 text-muted">${escapeHtml(doc.summary || '').substring(0, 200)}${doc.summary && doc.summary.length > 200 ? '...' : ''}</p>
                                <div class="d-flex align-items-center text-muted">
                                    <small class="me-3">
                                        <i class="fas fa-calendar me-1"></i>
                                        ${formatDate(doc.publication_date)}
                                    </small>
                                    <small class="me-3">
                                        <i class="fas fa-download me-1"></i>
                                        ${(doc.download_count || 0).toLocaleString()}
                                    </small>
                                    <small>
                                        <i class="fas fa-file me-1"></i>
                                        ${formatFileSize(doc.file_size)}
                                    </small>
                                </div>
                            </div>
                            <div class="flex-shrink-0 ms-3">
                                <div class="btn-group-vertical">
                                    <button class="btn btn-outline-primary btn-sm" onclick="viewDocumentDetails(${doc.id})">
                                        <i class="fas fa-eye"></i> Details
                                    </button>
                                    <a href="${escapeHtml(doc.file_url)}" target="_blank" class="btn btn-primary btn-sm" onclick="trackDownload(${doc.id})">
                                        <i class="fas fa-download"></i> Download
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function renderPagination(pagination) {
    const paginationElement = document.getElementById('research-pagination');
    if (!paginationElement || !pagination) return;
    
    if (pagination.pages <= 1) {
        paginationElement.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    if (pagination.page > 1) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadPage(${pagination.page - 1})">Previous</a>
            </li>
        `;
    }
    
    // Page numbers
    for (let i = Math.max(1, pagination.page - 2); i <= Math.min(pagination.pages, pagination.page + 2); i++) {
        paginationHTML += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadPage(${i})">${i}</a>
            </li>
        `;
    }
    
    // Next button
    if (pagination.page < pagination.pages) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadPage(${pagination.page + 1})">Next</a>
            </li>
        `;
    }
    
    paginationElement.innerHTML = paginationHTML;
}

async function loadDocumentCategories() {
    try {
        const response = await fetch('/api/research/document-types');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        updateCategoryCounts(data);
        
    } catch (error) {
        console.error('Error loading document categories:', error);
    }
}

function updateCategoryCounts(categoryData) {
    // Update category badges with actual counts
    const annualCount = document.getElementById('annual-count');
    const sectorCount = document.getElementById('sector-count');
    const outlookCount = document.getElementById('outlook-count');
    const quarterlyCount = document.getElementById('quarterly-count');
    
    if (annualCount) annualCount.textContent = categoryData.annual_report || 0;
    if (sectorCount) sectorCount.textContent = categoryData.sector_analysis || 0;
    if (outlookCount) outlookCount.textContent = categoryData.economic_outlook || 0;
    if (quarterlyCount) quarterlyCount.textContent = categoryData.quarterly_report || 0;
}

function loadPage(page) {
    // Add page parameter to current filters and reload
    const filters = getFilterValues();
    filters.page = page;
    
    const queryParams = new URLSearchParams(filters);
    const url = new URL(window.location);
    url.search = queryParams.toString();
    window.history.pushState({}, '', url);
    
    loadResearchDocuments();
}

function viewDocumentDetails(documentId) {
    // Show document details modal or navigate to detail page
    window.location.href = `/research/documents/${documentId}`;
}

function trackDownload(documentId) {
    // Track download analytics
    fetch(`/api/research/documents/${documentId}/download`, {
        method: 'POST'
    }).catch(error => {
        console.error('Error tracking download:', error);
    });
}

// Utility functions
function formatDocumentType(type) {
    const typeMap = {
        'annual_report': 'Annual Report',
        'quarterly_report': 'Quarterly Report',
        'sector_analysis': 'Sector Analysis',
        'economic_outlook': 'Economic Outlook',
        'strategic_document': 'Strategic Document',
        'governance_report': 'Governance Report'
    };
    return typeMap[type] || type;
}

function formatEntityType(type) {
    const typeMap = {
        'bank': 'Bank',
        'nbe': 'NBE',
        'government': 'Government',
        'international': 'International'
    };
    return typeMap[type] || type;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatFileSize(bytes) {
    if (!bytes) return 'N/A';
    
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

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