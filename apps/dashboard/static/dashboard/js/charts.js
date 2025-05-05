/**
 * Egypt Metro Dashboard Chart Configurations
 */

// Color palette
const COLORS = {
    primary: '#3498db',
    secondary: '#2ecc71',
    warning: '#f39c12',
    danger: '#e74c3c',
    info: '#9b59b6',
    dark: '#34495e',
    light: '#ecf0f1',
    primaryLight: 'rgba(52, 152, 219, 0.2)',
    secondaryLight: 'rgba(46, 204, 113, 0.2)',
    warningLight: 'rgba(243, 156, 18, 0.2)',
    dangerLight: 'rgba(231, 76, 60, 0.2)',
    infoLight: 'rgba(155, 89, 182, 0.2)',
};

// Chart theme settings
const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                boxWidth: 12,
                usePointStyle: true,
                font: {
                    size: 12
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            padding: 10,
            bodyFont: {
                size: 13
            },
            titleFont: {
                size: 14
            }
        }
    }
};

/**
 * Create a line chart for time-series data
 */
function createLineChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            ...CHART_DEFAULTS,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.3
                }
            },
            ...options
        }
    });
}

/**
 * Create a bar chart 
 */
function createBarChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            ...CHART_DEFAULTS,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            ...options
        }
    });
}

/**
 * Create a horizontal bar chart
 */
function createHorizontalBarChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            ...CHART_DEFAULTS,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            ...options
        }
    });
}

/**
 * Create a pie chart
 */
function createPieChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'pie',
        data: data,
        options: {
            ...CHART_DEFAULTS,
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: {
                    ...CHART_DEFAULTS.plugins.legend,
                    position: 'right'
                }
            },
            ...options
        }
    });
}

/**
 * Create a doughnut chart
 */
function createDoughnutChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            ...CHART_DEFAULTS,
            cutout: '60%',
            ...options
        }
    });
}

/**
 * Format number as currency (EGP)
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-EG', {
        style: 'currency',
        currency: 'EGP',
        maximumFractionDigits: 0
    }).format(value);
}

/**
 * Format percentage
 */
function formatPercent(value) {
    return `${value.toFixed(1)}%`;
}

/**
 * Format local date
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-EG', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
