// static/admin/js/user_admin.js

'use strict';

const MetroAdmin = {
    // Configuration
    config: {
        selectors: {
            form: '.user-form',
            table: '.metro-table',
            actionButton: '.action-button',
            subscriptionSelect: '#id_subscription_type',
            paymentMethod: '#id_payment_method',
            statsChart: '#userStatsChart'
        },
        endpoints: {
            users: '/admin/api/users/'
        }
    },

    // Initialization
    init() {
        this.initializeTooltips();
        this.setupFormHandlers();
        this.setupActionButtons();
        this.setupSubscriptionHandler();
        this.initializeCharts();
    },

    // Tooltip initialization
    initializeTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    },

    // Form handling
    setupFormHandlers() {
        const forms = document.querySelectorAll(this.config.selectors.form);
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit(form);
            });
        });
    },

    async handleFormSubmit(form) {
        try {
            const formData = new FormData(form);
            const response = await this.sendRequest(
                this.config.endpoints.users,
                'POST',
                formData
            );
            
            if (response.ok) {
                this.showMessage('Success!', 'success');
                window.location.reload();
            }
        } catch (error) {
            this.showMessage('Error submitting form', 'error');
            console.error('Form submission error:', error);
        }
    },

    // Action button handling
    setupActionButtons() {
        const buttons = document.querySelectorAll(this.config.selectors.actionButton);
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                const action = button.dataset.action;
                const userId = button.dataset.userId;
                this.handleAction(action, userId);
            });
        });
    },

    handleAction(action, userId) {
        switch(action) {
            case 'edit':
                window.location.href = `/admin/users/user/${userId}/change/`;
                break;
            case 'history':
                window.location.href = `/admin/users/user/${userId}/history/`;
                break;
            case 'deactivate':
                this.confirmDeactivation(userId);
                break;
            default:
                console.warn('Unknown action:', action);
        }
    },

    // Subscription handling
    setupSubscriptionHandler() {
        const select = document.querySelector(this.config.selectors.subscriptionSelect);
        if (select) {
            select.addEventListener('change', (e) => {
                this.togglePaymentMethod(e.target.value);
            });
        }
    },

    togglePaymentMethod(subscriptionType) {
        const paymentField = document.querySelector(this.config.selectors.paymentMethod)
            ?.closest('.form-group');
        
        if (paymentField) {
            paymentField.style.display = subscriptionType === 'FREE' ? 'none' : 'block';
        }
    },

    // Chart initialization
    initializeCharts() {
        const chartElement = document.querySelector(this.config.selectors.statsChart);
        if (!chartElement) return;

        new Chart(chartElement, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'User Growth',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: '#007bff',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    },

    // Utility functions
    async sendRequest(url, method, data) {
        const options = {
            method: method,
            headers: {
                'X-CSRFToken': this.getCsrfToken()
            }
        };

        if (data) {
            options.body = data instanceof FormData ? data : JSON.stringify(data);
        }

        return await fetch(url, options);
    },

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    },

    showMessage(message, type = 'info') {
        // Simple alert for now, can be enhanced with custom notification
        alert(message);
    },

    confirmDeactivation(userId) {
        if (confirm('Are you sure you want to deactivate this user?')) {
            this.deactivateUser(userId);
        }
    },

    async deactivateUser(userId) {
        try {
            const response = await this.sendRequest(
                `${this.config.endpoints.users}${userId}/deactivate/`,
                'POST'
            );
            
            if (response.ok) {
                this.showMessage('User deactivated successfully');
                window.location.reload();
            }
        } catch (error) {
            this.showMessage('Failed to deactivate user', 'error');
            console.error('Deactivation error:', error);
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    MetroAdmin.init();
});