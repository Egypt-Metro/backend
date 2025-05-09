/**
 * Egypt Metro Dashboard Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard JS loaded at:', new Date().toISOString());
    
    // Debug check to verify JS is running
    document.querySelector('body').classList.add('js-loaded');
    
    initializeFilters();
    initializeExports();
    
    // Add debug overlay
    if (document.body.classList.contains('debug-mode')) {
        addDebugOverlay();
    }
});

/**
 * Initialize dashboard filters
 */
function initializeFilters() {
    const dateRangeSelect = document.getElementById('date-range');
    const customDateInputs = document.getElementById('custom-date-inputs');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const applyFiltersBtn = document.getElementById('apply-filters');
    
    if (!dateRangeSelect) {
        console.warn('Date range select not found');
        return;
    }
    
    console.log('Initializing date filters');
    
    // Check if we have dates in URL params and set them
    const urlParams = new URLSearchParams(window.location.search);
    const rangeParam = urlParams.get('range');
    const startDateParam = urlParams.get('start_date');
    const endDateParam = urlParams.get('end_date');
    
    if (rangeParam && dateRangeSelect.querySelector(`option[value="${rangeParam}"]`)) {
        dateRangeSelect.value = rangeParam;
    }
    
    if (startDateParam && endDateParam) {
        dateRangeSelect.value = 'custom';
        if (customDateInputs) {
            customDateInputs.style.display = 'inline-flex';
        }
        if (startDateInput) {
            startDateInput.value = startDateParam;
        }
        if (endDateInput) {
            endDateInput.value = endDateParam;
        }
    }
    
    // Set current date as default for date inputs if not already set
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    if (startDateInput && !startDateInput.value) {
        startDateInput.valueAsDate = thirtyDaysAgo;
    }
    if (endDateInput && !endDateInput.value) {
        endDateInput.valueAsDate = today;
    }
    
    // Handle date range selector change
    if (dateRangeSelect) {
        dateRangeSelect.addEventListener('change', function() {
            console.log('Date range changed to', this.value);
            if (customDateInputs) {
                if (this.value === 'custom') {
                    customDateInputs.style.display = 'inline-flex';
                } else {
                    customDateInputs.style.display = 'none';
                    
                    // Set date range based on selection
                    const today = new Date();
                    let startDate = new Date(today);
                    let endDate = new Date(today);
                    
                    switch (this.value) {
                        case 'today':
                            // Both start and end are today
                            break;
                            
                        case 'yesterday':
                            startDate.setDate(today.getDate() - 1);
                            endDate = new Date(startDate);
                            break;
                            
                        case 'this_week':
                            // Start from Sunday of current week
                            startDate.setDate(today.getDate() - today.getDay());
                            break;
                            
                        case 'this_month':
                            startDate.setDate(1);
                            break;
                            
                        case 'last_month':
                            // Last day of previous month
                            endDate = new Date(today.getFullYear(), today.getMonth(), 0);
                            // First day of previous month
                            startDate = new Date(endDate.getFullYear(), endDate.getMonth(), 1);
                            break;
                            
                        case 'last_30_days':
                            startDate.setDate(today.getDate() - 30);
                            break;
                            
                        case 'last_90_days':
                            startDate.setDate(today.getDate() - 90);
                            break;
                    }
                    
                    if (startDateInput) startDateInput.valueAsDate = startDate;
                    if (endDateInput) endDateInput.valueAsDate = endDate;
                }
            }
        });
    }
    
    // Apply filters button
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            console.log('Applying filters');
            let url = new URL(window.location.href);
            
            // Get date range
            if (dateRangeSelect.value === 'custom') {
                if (startDateInput && startDateInput.value) {
                    url.searchParams.set('start_date', startDateInput.value);
                }
                if (endDateInput && endDateInput.value) {
                    url.searchParams.set('end_date', endDateInput.value);
                }
                // Remove range param when using custom dates
                url.searchParams.delete('range');
            } else {
                // Let the backend handle predefined ranges
                url.searchParams.delete('start_date');
                url.searchParams.delete('end_date');
                url.searchParams.set('range', dateRangeSelect.value);
            }
            
            // Redirect to filtered view
            console.log('Redirecting to', url.toString());
            window.location.href = url.toString();
        });
    }
}

/**
 * Initialize export buttons
 */
function initializeExports() {
    const exportButtons = document.querySelectorAll('.export-btn[data-type]');
    
    console.log(`Found ${exportButtons.length} export buttons`);
    
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const dataType = this.dataset.type;
            const exportType = this.dataset.format || 'csv';
            
            console.log(`Exporting ${dataType} as ${exportType}`);
            
            const form = document.getElementById('export-form') || createExportForm();
            
            // Set form values
            const dataTypeInput = form.querySelector('input[name="data_type"]');
            const exportTypeInput = form.querySelector('input[name="export_type"]');
            
            if (dataTypeInput) dataTypeInput.value = dataType;
            if (exportTypeInput) exportTypeInput.value = exportType;
            
            // Get current date range parameters
            const urlParams = new URLSearchParams(window.location.search);
            const startDate = urlParams.get('start_date') || document.getElementById('start-date')?.value;
            const endDate = urlParams.get('end_date') || document.getElementById('end-date')?.value;
            const range = urlParams.get('range') || document.getElementById('date-range')?.value;
            
            // Add parameters to form
            const addFormParam = (name, value) => {
                if (!value) return;
                
                let input = form.querySelector(`input[name="${name}"]`);
                if (!input) {
                    input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    form.appendChild(input);
                }
                input.value = value;
            };
            
            addFormParam('start_date', startDate);
            addFormParam('end_date', endDate);
            addFormParam('range', range);
            
            // Submit form
            console.log('Submitting export form', {
                'data_type': dataType,
                'export_type': exportType,
                'start_date': startDate,
                'end_date': endDate,
                'range': range
            });
            form.submit();
        });
    });
}

/**
 * Create export form if not exists
 */
function createExportForm() {
    console.log('Creating export form');
    const form = document.createElement('form');
    form.id = 'export-form';
    form.method = 'post';
    form.action = window.location.pathname;
    form.style.display = 'none';
    
    // Add CSRF token
    const csrfToken = getCsrfToken();
    if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
    } else {
        console.error('CSRF token not found');
    }
    
    // Add export fields
    const dataTypeInput = document.createElement('input');
    dataTypeInput.type = 'hidden';
    dataTypeInput.name = 'data_type';
    form.appendChild(dataTypeInput);
    
    const exportTypeInput = document.createElement('input');
    exportTypeInput.type = 'hidden';
    exportTypeInput.name = 'export_type';
    form.appendChild(exportTypeInput);
    
    const exportInput = document.createElement('input');
    exportInput.type = 'hidden';
    exportInput.name = 'export';
    exportInput.value = '1';
    form.appendChild(exportInput);
    
    document.body.appendChild(form);
    return form;
}

/**
 * Get CSRF token from cookies
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    if (!cookieValue) {
        // Try to get from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            cookieValue = metaTag.getAttribute('content');
        }
    }
    
    return cookieValue;
}

/**
 * Add a debug overlay for troubleshooting
 */
function addDebugOverlay() {
    console.log('Adding debug overlay');
    const overlay = document.createElement('div');
    overlay.className = 'debug-overlay';
    overlay.style.position = 'fixed';
    overlay.style.bottom = '10px';
    overlay.style.right = '10px';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    overlay.style.color = 'white';
    overlay.style.padding = '10px';
    overlay.style.borderRadius = '4px';
    overlay.style.fontSize = '12px';
    overlay.style.zIndex = '9999';
    overlay.style.maxWidth = '400px';
    overlay.style.maxHeight = '300px';
    overlay.style.overflow = 'auto';
    
    const toggleBtn = document.createElement('button');
    toggleBtn.textContent = 'Debug Info';
    toggleBtn.style.padding = '5px 10px';
    toggleBtn.style.backgroundColor = '#4CAF50';
    toggleBtn.style.color = 'white';
    toggleBtn.style.border = 'none';
    toggleBtn.style.borderRadius = '4px';
    toggleBtn.style.cursor = 'pointer';
    
    const debugContent = document.createElement('div');
    debugContent.style.display = 'none';
    debugContent.style.marginTop = '10px';
    
    toggleBtn.addEventListener('click', function() {
        if (debugContent.style.display === 'none') {
            debugContent.style.display = 'block';
            updateDebugInfo();
        } else {
            debugContent.style.display = 'none';
        }
    });
    
    function updateDebugInfo() {
        const scriptTags = document.querySelectorAll('script');
        const styleTags = document.querySelectorAll('link[rel="stylesheet"]');
        const canvasTags = document.querySelectorAll('canvas');
        
        let info = `
            <div style="margin-bottom: 10px;"><b>Page Info:</b></div>
            <div>URL: ${window.location.href}</div>
            <div>Time: ${new Date().toLocaleTimeString()}</div>
            <div>Window Size: ${window.innerWidth}x${window.innerHeight}</div>
            <div>Chart.js: ${window.Chart ? 'Loaded' : 'Not Loaded'}</div>
            <div>Scripts: ${scriptTags.length}</div>
            <div>Stylesheets: ${styleTags.length}</div>
            <div>Canvas Elements: ${canvasTags.length}</div>
            
            <div style="margin: 10px 0;"><b>Canvas Status:</b></div>
        `;
        
        canvasTags.forEach(canvas => {
            info += `<div>${canvas.id || 'unnamed'}: ${canvas.width}x${canvas.height}</div>`;
        });
        
        debugContent.innerHTML = info;
    }
    
    overlay.appendChild(toggleBtn);
    overlay.appendChild(debugContent);
    document.body.appendChild(overlay);
}

/**
 * Process JSON data to make sure it's valid for charts
 */
function processDashboardData(jsonData, defaultValue = []) {
    try {
        // If it's already an object, return it
        if (typeof jsonData === 'object' && jsonData !== null) {
            return jsonData;
        }
        
        // If it's a string, try to parse it
        if (typeof jsonData === 'string') {
            return JSON.parse(jsonData);
        }
        
        // If it's undefined or null, return default
        return defaultValue;
    } catch (err) {
        console.error('Error processing dashboard data:', err);
        return defaultValue;
    }
}