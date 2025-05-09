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
 * Validate chart data before rendering
 */
function validateChartData(data, chartType) {
    console.log(`Validating ${chartType} chart data:`, data);
    
    // Check if data exists
    if (!data) {
        console.error(`No data provided for ${chartType} chart`);
        return false;
    }
    
    // Check if datasets exist and have data
    if (!data.datasets || !Array.isArray(data.datasets) || data.datasets.length === 0) {
        console.error(`No datasets provided for ${chartType} chart`);
        return false;
    }
    
    // Check if labels exist
    if (!data.labels || !Array.isArray(data.labels) || data.labels.length === 0) {
        console.error(`No labels provided for ${chartType} chart`);
        return false;
    }
    
    // For each dataset, verify data exists
    for (let i = 0; i < data.datasets.length; i++) {
        const dataset = data.datasets[i];
        if (!dataset.data || !Array.isArray(dataset.data) || dataset.data.length === 0) {
            console.error(`Dataset ${i} has no data for ${chartType} chart`);
            return false;
        }
        
        // Check for NaN or undefined values in data
        for (let j = 0; j < dataset.data.length; j++) {
            if (dataset.data[j] === undefined || isNaN(dataset.data[j])) {
                console.error(`Dataset ${i} contains invalid data at index ${j} for ${chartType} chart`);
                dataset.data[j] = 0; // Replace with 0 to avoid errors
            }
        }
    }
    
    return true;
}

/**
 * Create a placeholder chart for when data is not available
 */
function createPlaceholderChart(ctx, chartType) {
    console.warn(`Creating placeholder for ${chartType} chart`);
    
    return new Chart(ctx, {
        type: chartType === 'horizontalBar' ? 'bar' : chartType,
        data: {
            labels: ['No Data Available'],
            datasets: [{
                label: 'No Data',
                data: [0],
                backgroundColor: COLORS.light,
                borderColor: COLORS.light,
                borderWidth: 1
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            plugins: {
                ...CHART_DEFAULTS.plugins,
                tooltip: {
                    callbacks: {
                        label: function() {
                            return 'No data available';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a line chart for time-series data
 */
function createLineChart(ctx, data, options = {}) {
    try {
        console.log('Creating line chart');
        
        // Validate the context
        if (!ctx) {
            console.error('Invalid canvas context for line chart');
            return null;
        }
        
        // Validate data
        if (!validateChartData(data, 'line')) {
            return createPlaceholderChart(ctx, 'line');
        }
        
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
    } catch (err) {
        console.error('Error creating line chart:', err);
        return createPlaceholderChart(ctx, 'line');
    }
}

/**
 * Create a bar chart 
 */
function createBarChart(ctx, data, options = {}) {
    try {
        console.log('Creating bar chart');
        
        // Validate the context
        if (!ctx) {
            console.error('Invalid canvas context for bar chart');
            return null;
        }
        
        // Validate data
        if (!validateChartData(data, 'bar')) {
            return createPlaceholderChart(ctx, 'bar');
        }
        
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
    } catch (err) {
        console.error('Error creating bar chart:', err);
        return createPlaceholderChart(ctx, 'bar');
    }
}

/**
 * Create a horizontal bar chart
 */
function createHorizontalBarChart(ctx, data, options = {}) {
    try {
        console.log('Creating horizontal bar chart');
        
        // Validate the context
        if (!ctx) {
            console.error('Invalid canvas context for horizontal bar chart');
            return null;
        }
        
        // Validate data
        if (!validateChartData(data, 'horizontalBar')) {
            return createPlaceholderChart(ctx, 'horizontalBar');
        }
        
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
    } catch (err) {
        console.error('Error creating horizontal bar chart:', err);
        return createPlaceholderChart(ctx, 'horizontalBar');
    }
}

/**
 * Create a pie chart
 */
function createPieChart(ctx, data, options = {}) {
    try {
        console.log('Creating pie chart');
        
        // Validate the context
        if (!ctx) {
            console.error('Invalid canvas context for pie chart');
            return null;
        }
        
        // Validate data
        if (!validateChartData(data, 'pie')) {
            return createPlaceholderChart(ctx, 'pie');
        }
        
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
    } catch (err) {
        console.error('Error creating pie chart:', err);
        return createPlaceholderChart(ctx, 'pie');
    }
}

/**
 * Create a doughnut chart
 */
function createDoughnutChart(ctx, data, options = {}) {
    try {
        console.log('Creating doughnut chart');
        
        // Validate the context
        if (!ctx) {
            console.error('Invalid canvas context for doughnut chart');
            return null;
        }
        
        // Validate data
        if (!validateChartData(data, 'doughnut')) {
            return createPlaceholderChart(ctx, 'doughnut');
        }
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: {
                ...CHART_DEFAULTS,
                cutout: '60%',
                ...options
            }
        });
    } catch (err) {
        console.error('Error creating doughnut chart:', err);
        return createPlaceholderChart(ctx, 'doughnut');
    }
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