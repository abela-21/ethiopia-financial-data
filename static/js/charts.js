// Ethiopia Capital Market Platform - Charts JavaScript

// Chart Configuration and Utilities
const ChartConfig = {
    // Ethiopian flag colors
    colors: {
        primary: '#0d6efd',
        success: '#007a33',  // Ethiopian green
        warning: '#ffdc00',  // Ethiopian yellow
        danger: '#ef3340',   // Ethiopian red
        info: '#0dcaf0',
        secondary: '#6c757d',
        light: '#f8f9fa',
        dark: '#212529'
    },
    
    // Default chart options
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        size: 12,
                        family: 'Inter, sans-serif'
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#ffffff',
                bodyColor: '#ffffff',
                borderColor: '#0d6efd',
                borderWidth: 1,
                cornerRadius: 8,
                displayColors: true,
                mode: 'index',
                intersect: false
            }
        },
        elements: {
            line: {
                tension: 0.1,
                borderWidth: 2
            },
            point: {
                radius: 4,
                hoverRadius: 6,
                borderWidth: 2,
                backgroundColor: '#ffffff'
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)',
                    borderColor: 'rgba(0, 0, 0, 0.2)'
                },
                ticks: {
                    font: {
                        size: 11,
                        family: 'Inter, sans-serif'
                    },
                    color: '#6c757d'
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)',
                    borderColor: 'rgba(0, 0, 0, 0.2)'
                },
                ticks: {
                    font: {
                        size: 11,
                        family: 'Inter, sans-serif'
                    },
                    color: '#6c757d'
                }
            }
        }
    }
};

// Chart Manager Class
class ChartManager {
    constructor() {
        this.charts = new Map();
        this.defaultColors = Object.values(ChartConfig.colors);
    }

    // Create a line chart
    createLineChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with id '${canvasId}' not found`);
            return null;
        }

        // Destroy existing chart if it exists
        this.destroyChart(canvasId);

        const chartOptions = this.mergeOptions(ChartConfig.defaultOptions, options);
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: this.processLineData(data),
            options: chartOptions
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    // Create a bar chart
    createBarChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with id '${canvasId}' not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const chartOptions = this.mergeOptions(ChartConfig.defaultOptions, options);
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: this.processBarData(data),
            options: chartOptions
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    // Create a doughnut chart
    createDoughnutChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with id '${canvasId}' not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const defaultDoughnutOptions = {
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            cutout: '60%'
        };

        const chartOptions = this.mergeOptions(ChartConfig.defaultOptions, defaultDoughnutOptions, options);
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: this.processDoughnutData(data),
            options: chartOptions
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    // Create a mixed chart (line + bar)
    createMixedChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with id '${canvasId}' not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const chartOptions = this.mergeOptions(ChartConfig.defaultOptions, options);
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: this.processMixedData(data),
            options: chartOptions
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    // Process line chart data
    processLineData(data) {
        const datasets = data.datasets.map((dataset, index) => ({
            label: dataset.label,
            data: dataset.data,
            borderColor: dataset.borderColor || this.defaultColors[index % this.defaultColors.length],
            backgroundColor: dataset.backgroundColor || this.hexToRgba(
                dataset.borderColor || this.defaultColors[index % this.defaultColors.length], 0.1
            ),
            fill: dataset.fill !== undefined ? dataset.fill : true,
            tension: dataset.tension || 0.1,
            ...dataset
        }));

        return {
            labels: data.labels,
            datasets: datasets
        };
    }

    // Process bar chart data
    processBarData(data) {
        const datasets = data.datasets.map((dataset, index) => ({
            label: dataset.label,
            data: dataset.data,
            backgroundColor: dataset.backgroundColor || this.defaultColors[index % this.defaultColors.length],
            borderColor: dataset.borderColor || dataset.backgroundColor || this.defaultColors[index % this.defaultColors.length],
            borderWidth: dataset.borderWidth || 1,
            ...dataset
        }));

        return {
            labels: data.labels,
            datasets: datasets
        };
    }

    // Process doughnut chart data
    processDoughnutData(data) {
        return {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: data.backgroundColor || this.defaultColors,
                borderColor: data.borderColor || '#ffffff',
                borderWidth: data.borderWidth || 2,
                ...data.options
            }]
        };
    }

    // Process mixed chart data
    processMixedData(data) {
        const datasets = data.datasets.map((dataset, index) => ({
            type: dataset.type || 'bar',
            label: dataset.label,
            data: dataset.data,
            backgroundColor: dataset.backgroundColor || this.hexToRgba(
                this.defaultColors[index % this.defaultColors.length], 0.6
            ),
            borderColor: dataset.borderColor || this.defaultColors[index % this.defaultColors.length],
            borderWidth: dataset.borderWidth || 2,
            fill: dataset.fill || false,
            yAxisID: dataset.yAxisID || 'y',
            ...dataset
        }));

        return {
            labels: data.labels,
            datasets: datasets
        };
    }

    // Utility functions
    mergeOptions(...options) {
        return options.reduce((merged, option) => {
            return this.deepMerge(merged, option);
        }, {});
    }

    deepMerge(target, source) {
        const output = Object.assign({}, target);
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.deepMerge(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    }

    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }

    hexToRgba(hex, alpha = 1) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (result) {
            const r = parseInt(result[1], 16);
            const g = parseInt(result[2], 16);
            const b = parseInt(result[3], 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        return hex;
    }

    // Chart management
    destroyChart(canvasId) {
        const existingChart = this.charts.get(canvasId);
        if (existingChart) {
            existingChart.destroy();
            this.charts.delete(canvasId);
        }
    }

    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }

    getChart(canvasId) {
        return this.charts.get(canvasId);
    }

    destroyAllCharts() {
        this.charts.forEach((chart, canvasId) => {
            chart.destroy();
        });
        this.charts.clear();
    }

    // Animation helpers
    animateChart(canvasId, duration = 1000) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.options.animation = {
                duration: duration,
                easing: 'easeInOutQuart'
            };
            chart.update();
        }
    }

    // Responsive helpers
    resizeChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.resize();
        }
    }

    resizeAllCharts() {
        this.charts.forEach(chart => {
            chart.resize();
        });
    }
}

// Chart Templates for common chart types used in the platform
const ChartTemplates = {
    // Stock price chart template
    stockPrice: {
        type: 'line',
        options: {
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Price (ETB)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Price: ${Utils.formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            }
        }
    },

    // Market trends template
    marketTrends: {
        type: 'line',
        options: {
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Market Cap (ETB)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Volume'
                    },
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label;
                            if (label.includes('Volume')) {
                                return `${label}: ${Utils.formatLargeNumber(context.parsed.y)}`;
                            }
                            return `${label}: ${Utils.formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            }
        }
    },

    // Economic indicators template
    economicIndicators: {
        type: 'line',
        options: {
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${Utils.formatPercentage(context.parsed.y)}`;
                        }
                    }
                }
            }
        }
    },

    // Exchange rates template
    exchangeRates: {
        type: 'line',
        options: {
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Exchange Rate (ETB)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} ETB`;
                        }
                    }
                }
            }
        }
    },

    // Industry distribution template
    industryDistribution: {
        type: 'doughnut',
        options: {
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    }
};

// Financial Chart Helpers
const FinancialCharts = {
    // Create a financial ratios comparison chart
    createRatiosChart(canvasId, data) {
        const chartData = {
            labels: data.ratios,
            datasets: [{
                label: 'Company Ratios',
                data: data.values,
                backgroundColor: ChartConfig.colors.primary,
                borderColor: ChartConfig.colors.primary,
                borderWidth: 2
            }]
        };

        const options = {
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.parsed.x.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Ratio Value'
                    }
                }
            }
        };

        return chartManager.createBarChart(canvasId, chartData, options);
    },

    // Create a revenue vs profit chart
    createRevenueProfitChart(canvasId, data) {
        const chartData = {
            labels: data.periods,
            datasets: [
                {
                    type: 'bar',
                    label: 'Revenue',
                    data: data.revenue,
                    backgroundColor: ChartConfig.colors.primary,
                    yAxisID: 'y'
                },
                {
                    type: 'line',
                    label: 'Net Profit',
                    data: data.profit,
                    borderColor: ChartConfig.colors.success,
                    backgroundColor: chartManager.hexToRgba(ChartConfig.colors.success, 0.1),
                    yAxisID: 'y'
                }
            ]
        };

        const options = {
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Amount (ETB)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${Utils.formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            }
        };

        return chartManager.createMixedChart(canvasId, chartData, options);
    }
};

// Global chart manager instance
const chartManager = new ChartManager();

// Auto-resize charts on window resize
window.addEventListener('resize', Utils.throttle(() => {
    chartManager.resizeAllCharts();
}, 250));

// Cleanup charts when navigating away
window.addEventListener('beforeunload', () => {
    chartManager.destroyAllCharts();
});

// Export for global use
window.ChartManager = ChartManager;
window.chartManager = chartManager;
window.ChartConfig = ChartConfig;
window.ChartTemplates = ChartTemplates;
window.FinancialCharts = FinancialCharts;
