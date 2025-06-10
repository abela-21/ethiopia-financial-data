class DashboardManager {
    constructor() {
        this.init();
    }

    init() {
        this.loadDashboardStats();
        this.loadWatchlists();
        this.loadRecentActivity();
        this.loadDownloadHistory();
        this.loadSavedSearches();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Create watchlist modal
        document.getElementById('saveWatchlist')?.addEventListener('click', () => {
            this.createWatchlist();
        });

        // Update watchlist modal
        document.getElementById('updateWatchlist')?.addEventListener('click', () => {
            this.updateWatchlist();
        });

        // Delete watchlist
        document.getElementById('deleteWatchlist')?.addEventListener('click', () => {
            this.deleteWatchlist();
        });

        // View toggle buttons
        document.getElementById('gridViewBtn')?.addEventListener('click', () => {
            this.setWatchlistView('grid');
        });

        document.getElementById('listViewBtn')?.addEventListener('click', () => {
            this.setWatchlistView('list');
        });

        // Alert category navigation
        document.querySelectorAll('#alertCategories .list-group-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadAlerts(item.dataset.category);
            });
        });

        // Preferences button
        document.getElementById('preferencesBtn')?.addEventListener('click', () => {
            this.showPreferences();
        });
    }

    async loadDashboardStats() {
        try {
            const response = await fetch('/api/dashboard/stats');
            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                document.getElementById('watchlistCount').textContent = data.watchlist_count;
                document.getElementById('companiesCount').textContent = data.companies_count;
                document.getElementById('downloadsCount').textContent = data.downloads_count;
                document.getElementById('alertsCount').textContent = data.alerts_count;
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }

    async loadWatchlists() {
        try {
            const response = await fetch('/api/dashboard/watchlists');
            const result = await response.json();

            if (result.status === 'success') {
                this.renderWatchlists(result.data);
            }
        } catch (error) {
            console.error('Error loading watchlists:', error);
        }
    }

    renderWatchlists(watchlists) {
        const container = document.getElementById('watchlistsContainer');
        
        if (watchlists.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-eye fa-3x text-muted mb-3"></i>
                    <h6 class="text-muted">No watchlists yet</h6>
                    <p class="text-muted">Create your first watchlist to start tracking companies</p>
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createWatchlistModal">
                        <i class="fas fa-plus me-1"></i>Create Watchlist
                    </button>
                </div>
            `;
            return;
        }

        const view = localStorage.getItem('watchlistView') || 'grid';
        
        if (view === 'grid') {
            this.renderGridView(watchlists, container);
        } else {
            this.renderListView(watchlists, container);
        }
    }

    renderGridView(watchlists, container) {
        const html = `
            <div class="row">
                ${watchlists.map(watchlist => `
                    <div class="col-md-6 col-lg-4 mb-4">
                        <div class="card h-100 ${watchlist.is_default ? 'border-primary' : ''}">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="card-title mb-0">
                                        ${watchlist.name}
                                        ${watchlist.is_default ? '<span class="badge bg-primary ms-1">Default</span>' : ''}
                                        ${watchlist.is_public ? '<span class="badge bg-success ms-1">Public</span>' : ''}
                                    </h6>
                                    <div class="dropdown">
                                        <button class="btn btn-sm btn-outline-secondary" data-bs-toggle="dropdown">
                                            <i class="fas fa-ellipsis-v"></i>
                                        </button>
                                        <ul class="dropdown-menu">
                                            <li><a class="dropdown-item" href="#" onclick="dashboard.editWatchlist(${watchlist.id})">
                                                <i class="fas fa-edit me-2"></i>Edit
                                            </a></li>
                                            <li><a class="dropdown-item" href="#" onclick="dashboard.viewWatchlist(${watchlist.id})">
                                                <i class="fas fa-eye me-2"></i>View Companies
                                            </a></li>
                                            <li><hr class="dropdown-divider"></li>
                                            <li><a class="dropdown-item text-danger" href="#" onclick="dashboard.confirmDeleteWatchlist(${watchlist.id})">
                                                <i class="fas fa-trash me-2"></i>Delete
                                            </a></li>
                                        </ul>
                                    </div>
                                </div>
                                <p class="card-text text-muted small">${watchlist.description || 'No description'}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <small class="text-muted">
                                        <i class="fas fa-building me-1"></i>${watchlist.companies_count} companies
                                    </small>
                                    <small class="text-muted">
                                        Created ${new Date(watchlist.created_at).toLocaleDateString()}
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        container.innerHTML = html;
    }

    renderListView(watchlists, container) {
        const html = `
            <div class="list-group">
                ${watchlists.map(watchlist => `
                    <div class="list-group-item">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">
                                ${watchlist.name}
                                ${watchlist.is_default ? '<span class="badge bg-primary ms-2">Default</span>' : ''}
                                ${watchlist.is_public ? '<span class="badge bg-success ms-2">Public</span>' : ''}
                            </h6>
                            <div class="dropdown">
                                <button class="btn btn-sm btn-outline-secondary" data-bs-toggle="dropdown">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <ul class="dropdown-menu">
                                    <li><a class="dropdown-item" href="#" onclick="dashboard.editWatchlist(${watchlist.id})">
                                        <i class="fas fa-edit me-2"></i>Edit
                                    </a></li>
                                    <li><a class="dropdown-item" href="#" onclick="dashboard.viewWatchlist(${watchlist.id})">
                                        <i class="fas fa-eye me-2"></i>View Companies
                                    </a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="#" onclick="dashboard.confirmDeleteWatchlist(${watchlist.id})">
                                        <i class="fas fa-trash me-2"></i>Delete
                                    </a></li>
                                </ul>
                            </div>
                        </div>
                        <p class="mb-1">${watchlist.description || 'No description'}</p>
                        <small class="text-muted">
                            <i class="fas fa-building me-1"></i>${watchlist.companies_count} companies • 
                            Created ${new Date(watchlist.created_at).toLocaleDateString()}
                        </small>
                    </div>
                `).join('')}
            </div>
        `;
        container.innerHTML = html;
    }

    setWatchlistView(view) {
        localStorage.setItem('watchlistView', view);
        
        // Update button states
        document.querySelectorAll('#gridViewBtn, #listViewBtn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(view + 'ViewBtn').classList.add('active');
        
        // Reload watchlists with new view
        this.loadWatchlists();
    }

    async createWatchlist() {
        const name = document.getElementById('watchlistName').value.trim();
        const description = document.getElementById('watchlistDescription').value.trim();
        const isPublic = document.getElementById('isPublic').checked;
        const isDefault = document.getElementById('isDefault').checked;

        if (!name) {
            alert('Please enter a watchlist name');
            return;
        }

        try {
            const response = await fetch('/api/dashboard/watchlists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    description,
                    is_public: isPublic,
                    is_default: isDefault
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                // Close modal
                bootstrap.Modal.getInstance(document.getElementById('createWatchlistModal')).hide();
                
                // Reset form
                document.getElementById('createWatchlistForm').reset();
                
                // Reload data
                this.loadWatchlists();
                this.loadDashboardStats();
                
                // Show success message
                this.showNotification('Watchlist created successfully!', 'success');
            } else {
                alert(result.message || 'Failed to create watchlist');
            }
        } catch (error) {
            console.error('Error creating watchlist:', error);
            alert('Failed to create watchlist');
        }
    }

    async editWatchlist(watchlistId) {
        try {
            const response = await fetch(`/api/dashboard/watchlists/${watchlistId}/companies`);
            const result = await response.json();

            if (result.status === 'success') {
                const watchlist = result.data.watchlist;
                
                // Populate edit form
                document.getElementById('editWatchlistId').value = watchlistId;
                document.getElementById('editWatchlistName').value = watchlist.name;
                document.getElementById('editWatchlistDescription').value = watchlist.description || '';
                
                // Load companies in watchlist
                this.renderWatchlistCompanies(result.data.companies);
                
                // Show modal
                new bootstrap.Modal(document.getElementById('editWatchlistModal')).show();
            }
        } catch (error) {
            console.error('Error loading watchlist:', error);
        }
    }

    renderWatchlistCompanies(companies) {
        const container = document.getElementById('watchlistCompanies');
        
        if (companies.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No companies in this watchlist</p>';
            return;
        }

        const html = companies.map(company => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <strong>${company.name}</strong> (${company.ticker})
                    <br>
                    <small class="text-muted">${company.sector}</small>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="dashboard.removeFromWatchlist(${company.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }

    async loadRecentActivity() {
        try {
            const response = await fetch('/api/dashboard/recent-activity');
            const result = await response.json();

            if (result.status === 'success') {
                this.renderRecentActivity(result.data);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    renderRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="text-center py-3"><p class="text-muted">No recent activity</p></div>';
            return;
        }

        const html = activities.map(activity => `
            <div class="d-flex align-items-start mb-3">
                <div class="flex-shrink-0">
                    <i class="fas fa-${this.getActivityIcon(activity.type)} text-primary"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <p class="mb-1">${activity.description}</p>
                    <small class="text-muted">${new Date(activity.timestamp).toLocaleString()}</small>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }

    getActivityIcon(type) {
        const icons = {
            'download': 'download',
            'watchlist_addition': 'eye',
            'search': 'search',
            'alert': 'bell'
        };
        return icons[type] || 'circle';
    }

    async loadDownloadHistory() {
        try {
            const response = await fetch('/api/dashboard/download-history?per_page=5');
            const result = await response.json();

            if (result.status === 'success') {
                this.renderDownloadHistory(result.data.downloads);
            }
        } catch (error) {
            console.error('Error loading download history:', error);
        }
    }

    renderDownloadHistory(downloads) {
        const container = document.getElementById('downloadHistory');
        
        if (downloads.length === 0) {
            container.innerHTML = '<div class="text-center py-3"><small class="text-muted">No downloads yet</small></div>';
            return;
        }

        const html = downloads.map(download => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <small class="fw-bold">${download.resource_name}</small>
                    <br>
                    <small class="text-muted">${download.file_format.toUpperCase()} • ${this.formatFileSize(download.file_size)}</small>
                </div>
                <small class="text-muted">${new Date(download.downloaded_at).toLocaleDateString()}</small>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }

    async loadSavedSearches() {
        try {
            const response = await fetch('/api/dashboard/saved-searches');
            const result = await response.json();

            if (result.status === 'success') {
                this.renderSavedSearches(result.data.slice(0, 5)); // Show only recent 5
            }
        } catch (error) {
            console.error('Error loading saved searches:', error);
        }
    }

    renderSavedSearches(searches) {
        const container = document.getElementById('savedSearches');
        
        if (searches.length === 0) {
            container.innerHTML = '<div class="text-center py-3"><small class="text-muted">No saved searches</small></div>';
            return;
        }

        const html = searches.map(search => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <small class="fw-bold">${search.name}</small>
                    <br>
                    <small class="text-muted">${search.results_count} results</small>
                </div>
                <div class="text-end">
                    ${search.alert_enabled ? '<i class="fas fa-bell text-warning"></i>' : ''}
                    <br>
                    <small class="text-muted">${new Date(search.updated_at).toLocaleDateString()}</small>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }

    async loadAlerts(category = 'price') {
        try {
            const response = await fetch(`/api/dashboard/alerts?type=${category}`);
            const result = await response.json();

            if (result.status === 'success') {
                this.renderAlerts(result.data);
            }

            // Update active category
            document.querySelectorAll('#alertCategories .list-group-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`#alertCategories [data-category="${category}"]`).classList.add('active');
        } catch (error) {
            console.error('Error loading alerts:', error);
        }
    }

    renderAlerts(alerts) {
        const container = document.getElementById('alertsList');
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="text-center py-3"><p class="text-muted">No alerts in this category</p></div>';
            return;
        }

        const html = alerts.map(alert => `
            <div class="card mb-2">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${alert.title}</h6>
                            <p class="mb-1 text-muted small">${alert.message}</p>
                            <small class="text-muted">
                                ${alert.frequency} • ${alert.delivery_method} • 
                                Created ${new Date(alert.created_at).toLocaleDateString()}
                            </small>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" ${alert.is_active ? 'checked' : ''} 
                                   onchange="dashboard.toggleAlert(${alert.id}, this.checked)">
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }

    formatFileSize(bytes) {
        if (!bytes) return 'Unknown';
        
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    showNotification(message, type = 'info') {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    async toggleAlert(alertId, isActive) {
        try {
            const response = await fetch(`/api/dashboard/alerts/${alertId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ is_active: isActive })
            });

            const result = await response.json();
            if (result.status === 'success') {
                this.loadDashboardStats(); // Refresh alert count
            }
        } catch (error) {
            console.error('Error toggling alert:', error);
        }
    }

    confirmDeleteWatchlist(watchlistId) {
        if (confirm('Are you sure you want to delete this watchlist? This action cannot be undone.')) {
            this.deleteWatchlistById(watchlistId);
        }
    }

    async deleteWatchlistById(watchlistId) {
        try {
            const response = await fetch(`/api/dashboard/watchlists/${watchlistId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.status === 'success') {
                this.loadWatchlists();
                this.loadDashboardStats();
                this.showNotification('Watchlist deleted successfully!', 'success');
            } else {
                alert(result.message || 'Failed to delete watchlist');
            }
        } catch (error) {
            console.error('Error deleting watchlist:', error);
            alert('Failed to delete watchlist');
        }
    }

    showPreferences() {
        // Navigate to preferences page or show preferences modal
        window.location.href = '/settings';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});