// static/admin/js/user_admin.js
'use strict';

const MetroUserAdmin = {
    init() {
        this.initializeComponents();
        this.setupEventListeners();
    },

    initializeComponents() {
        // Initialize any third-party components
        this.initializeCharts();
        this.initializeDataTables();
    },

    setupEventListeners() {
        // Setup action buttons
        document.querySelectorAll('.user-action-btn').forEach(button => {
            button.addEventListener('click', this.handleUserAction.bind(this));
        });
    },

    handleUserAction(event) {
        const button = event.currentTarget;
        const action = button.dataset.action;
        const userId = button.dataset.userId;

        switch (action) {
            case 'deactivate':
                this.confirmUserDeactivation(userId);
                break;
            case 'upgrade':
                this.handleSubscriptionUpgrade(userId);
                break;
            default:
                console.warn('Unknown action:', action);
        }
    },

    confirmUserDeactivation(userId) {
        if (confirm('Are you sure you want to deactivate this user?')) {
            this.deactivateUser(userId);
        }
    },

    async deactivateUser(userId) {
        try {
            const response = await fetch(`/admin/api/users/${userId}/deactivate/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                },
            });

            if (response.ok) {
                window.location.reload();
            } else {
                throw new Error('Failed to deactivate user');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to deactivate user. Please try again.');
        }
    },

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    },

    initializeCharts() {
        const statsChart = document.getElementById('userStatsChart');
        if (!statsChart) return;

        // Initialize Chart.js
        new Chart(statsChart, {
            type: 'line',
            data: this.getChartData(),
            options: this.getChartOptions()
        });
    },

    getChartData() {
        // Return chart data configuration
        return {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'User Growth',
                data: [12, 19, 3, 5, 2, 3],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        };
    },

    getChartOptions() {
        // Return chart options configuration
        return {
            responsive: true,
            maintainAspectRatio: false
        };
    },

    initializeDataTables() {
        // Initialize DataTables if available
        if ($.fn.DataTable) {
            $('.metro-table').DataTable({
                responsive: true,
                pageLength: 25
            });
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    MetroUserAdmin.init();
});
