/**
 * Egypt Metro Dashboard Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    initializeExports();
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
    
    if (!dateRangeSelect) return;
    
    // Set current date as default for date inputs
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    if (startDateInput) startDateInput.valueAsDate = thirtyDaysAgo;
    if (endDateInput) endDateInput.valueAsDate = today;
    
    // Handle date range selector change
    dateRangeSelect.addEventListener('change', function() {
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
    
    // Apply filters button
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            let url = new URL(window.location.href);
            
            // Get date range
            if (dateRangeSelect.value === 'custom') {
                if (startDateInput && startDateInput.value) {
                    url.searchParams.set('start_date', startDateInput.value);
                }
                if (endDateInput && endDateInput.value) {
                    url.searchParams.set('end_date', endDateInput.value);
                }
            } else {
                // Let the backend handle predefined ranges
                url.searchParams.delete('start_date');
                url.searchParams.delete('end_date');
                url.searchParams.set('range', dateRangeSelect.value);
            }
            
            // Redirect to filtered view
            window.location.href = url.toString();
        });
    }
}

/**
 * Initialize export buttons
 */
function initializeExports() {
    const exportButtons = document.querySelectorAll('.export-btn[data-type]');
    
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const dataType = this.dataset.type;
            const exportType = this.dataset.format || 'csv';
            const form = document.getElementById('export-form') || createExportForm();
            
            // Set form values
            const dataTypeInput = form.querySelector('input[name="data_type"]');
            const exportTypeInput = form.querySelector('input[name="export_type"]');
            
            dataTypeInput.value = dataType;
            exportTypeInput.value = exportType;
            
            // Add date filters if present
            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');
            
            if (startDateInput && startDateInput.value) {
                let formStartDate = form.querySelector('input[name="start_date"]');
                if (!formStartDate) {
                    formStartDate = document.createElement('input');
                    formStartDate.type = 'hidden';
                    formStartDate.name = 'start_date';
                    form.appendChild(formStartDate);
                }
                formStartDate.value = startDateInput.value;
            }
            
            if (endDateInput && endDateInput.value) {
                let formEndDate = form.querySelector('input[name="end_date"]');
                if (!formEndDate) {
                    formEndDate = document.createElement('input');
                    formEndDate.type = 'hidden';
                    formEndDate.name = 'end_date';
                    form.appendChild(formEndDate);
                }
                formEndDate.value = endDateInput.value;
            }
            
            // Submit form
            form.submit();
        });
    });
}

/**
 * Create export form if not exists
 */
function createExportForm() {
    const form = document.createElement('form');
    form.id = 'export-form';
    form.method = 'post';
    form.style.display = 'none';
    
    // Add CSRF token
    const csrfToken = getCsrfToken();
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);
    
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
    
    return cookieValue;
}