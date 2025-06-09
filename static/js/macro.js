// Macroeconomic Indicators JavaScript
let growthChart = null;
let inflationChart = null;
let exchangeChart = null;
let tradeChart = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Macro indicators page - Initializing...');
    loadLatestIndicators();
    loadMacroCharts();
    console.log('Macro indicators page - Initialized');
});

async function loadLatestIndicators() {
    try {
        const response = await fetch('/api/macro/latest');
        const data = await response.json();
        
        if (data.indicators) {
            const indicators = data.indicators;
            document.getElementById('gdpGrowth').textContent = indicators.gdp_growth ? indicators.gdp_growth.toFixed(1) + '%' : 'N/A';
            document.getElementById('inflationRate').textContent = indicators.inflation_rate ? indicators.inflation_rate.toFixed(1) + '%' : 'N/A';
            document.getElementById('usdExchange').textContent = indicators.etb_usd ? indicators.etb_usd.toFixed(2) : 'N/A';
            document.getElementById('interestRate').textContent = indicators.interest_rate ? indicators.interest_rate.toFixed(1) + '%' : 'N/A';
        }
    } catch (error) {
        console.error('Error loading latest indicators:', error);
        // Set fallback values
        document.getElementById('gdpGrowth').textContent = 'N/A';
        document.getElementById('inflationRate').textContent = 'N/A';
        document.getElementById('usdExchange').textContent = 'N/A';
        document.getElementById('interestRate').textContent = 'N/A';
    }
}

async function loadMacroCharts() {
    try {
        const response = await fetch('/api/macro?limit=20');
        const data = await response.json();
        
        if (data.indicators && data.indicators.length > 0) {
            const indicators = data.indicators.sort((a, b) => new Date(a.date) - new Date(b.date));
            
            // Create charts
            createGrowthChart(indicators);
            createInflationChart(indicators);
            createExchangeChart(indicators);
            createTradeChart(indicators);
        } else {
            showChartErrors();
        }
    } catch (error) {
        console.error('Error loading macro charts:', error);
        showChartErrors();
    }
}

function createGrowthChart(data) {
    const ctx = document.getElementById('growthChart');
    if (!ctx) return;
    
    const labels = data.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    });
    
    const gdpData = data.map(d => d.gdp_growth || 0);
    const industrialData = data.map(d => d.industrial_production || 0);
    
    if (growthChart) {
        growthChart.destroy();
    }
    
    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'GDP Growth (%)',
                data: gdpData,
                borderColor: '#075056',
                backgroundColor: 'rgba(7, 80, 86, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }, {
                label: 'Industrial Production Index',
                data: industrialData,
                borderColor: '#FF5B04',
                backgroundColor: 'rgba(255, 91, 4, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            }
        }
    });
}

function createInflationChart(data) {
    const ctx = document.getElementById('inflationChart');
    if (!ctx) return;
    
    const labels = data.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    });
    
    const inflationData = data.map(d => d.inflation_rate || 0);
    const foodInflationData = data.map(d => d.food_inflation || 0);
    
    if (inflationChart) {
        inflationChart.destroy();
    }
    
    inflationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'General Inflation (%)',
                data: inflationData,
                borderColor: '#FF5B04',
                backgroundColor: 'rgba(255, 91, 4, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }, {
                label: 'Food Inflation (%)',
                data: foodInflationData,
                borderColor: '#F4D47C',
                backgroundColor: 'rgba(244, 212, 124, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            }
        }
    });
}

function createExchangeChart(data) {
    const ctx = document.getElementById('exchangeChart');
    if (!ctx) return;
    
    const labels = data.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    });
    
    const usdData = data.map(d => d.etb_usd || 0);
    const eurData = data.map(d => d.etb_eur || 0);
    
    if (exchangeChart) {
        exchangeChart.destroy();
    }
    
    exchangeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'ETB/USD',
                data: usdData,
                borderColor: '#075056',
                backgroundColor: 'rgba(7, 80, 86, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }, {
                label: 'ETB/EUR',
                data: eurData,
                borderColor: '#233038',
                backgroundColor: 'rgba(35, 48, 56, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            }
        }
    });
}

function createTradeChart(data) {
    const ctx = document.getElementById('tradeChart');
    if (!ctx) return;
    
    const labels = data.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    });
    
    const exportsData = data.map(d => d.exports || 0);
    const importsData = data.map(d => d.imports || 0);
    
    if (tradeChart) {
        tradeChart.destroy();
    }
    
    tradeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Exports (Billion USD)',
                data: exportsData,
                backgroundColor: '#075056',
                borderColor: '#075056',
                borderWidth: 1
            }, {
                label: 'Imports (Billion USD)',
                data: importsData,
                backgroundColor: '#FF5B04',
                borderColor: '#FF5B04',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            }
        }
    });
}

function showChartErrors() {
    // Show error states for charts
    const chartContainers = ['growthChartContainer', 'inflationChartContainer', 'exchangeChartContainer', 'tradeChartContainer'];
    const errorElements = ['growthError', 'inflationError', 'exchangeError', 'tradeError'];
    
    chartContainers.forEach((containerId, index) => {
        const container = document.getElementById(containerId);
        const errorElement = document.getElementById(errorElements[index]);
        
        if (container && errorElement) {
            container.style.display = 'none';
            errorElement.classList.remove('d-none');
        }
    });
}

async function refreshMacroData() {
    // Show loading states
    const refreshBtn = document.querySelector('[onclick="refreshMacroData()"]');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Refreshing...';
        refreshBtn.disabled = true;
    }
    
    try {
        await loadLatestIndicators();
        await loadMacroCharts();
        
        // Show success message briefly
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-check me-2"></i>Updated';
            setTimeout(() => {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Refresh';
                refreshBtn.disabled = false;
            }, 2000);
        }
    } catch (error) {
        console.error('Error refreshing macro data:', error);
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error';
            setTimeout(() => {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Refresh';
                refreshBtn.disabled = false;
            }, 2000);
        }
    }
}