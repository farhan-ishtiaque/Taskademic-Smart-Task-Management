// Main JavaScript for Taskademic

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CSRF token for API calls
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Set up CSRF token for all API requests
    if (csrfToken) {
        fetch = new Proxy(fetch, {
            apply: function(target, thisArg, argumentsList) {
                const [url, options = {}] = argumentsList;
                
                // Add CSRF token to POST, PUT, PATCH, DELETE requests
                if (options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase())) {
                    options.headers = {
                        ...options.headers,
                        'X-CSRFToken': csrfToken
                    };
                }
                
                return target.apply(thisArg, [url, options]);
            }
        });
    }
    
    // Initialize notifications
    initializeNotifications();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize auto-save functionality
    initializeAutoSave();
});

// Notification system
function initializeNotifications() {
    window.showNotification = function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg max-w-sm transition-all duration-300 transform translate-x-full`;
        
        const typeClasses = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-white',
            info: 'bg-blue-500 text-white'
        };
        
        notification.classList.add(...typeClasses[type].split(' '));
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    ×
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    };
}

// Tooltip system
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg pointer-events-none';
            tooltip.textContent = tooltipText;
            tooltip.id = 'tooltip';
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = document.getElementById('tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
}

// Auto-save functionality for forms
function initializeAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-autosave]');
    
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        let saveTimeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    saveFormData(form);
                }, 2000); // Save 2 seconds after last input
            });
        });
    });
}

function saveFormData(form) {
    const formData = new FormData(form);
    const saveUrl = form.getAttribute('data-autosave');
    
    if (saveUrl) {
        fetch(saveUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Auto-saved', 'success');
            }
        })
        .catch(error => {
            console.error('Auto-save error:', error);
        });
    }
}

// Task management utilities
window.TaskUtils = {
    // Format date for display
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    // Format datetime for display
    formatDateTime(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Get priority class for styling
    getPriorityClass(priority) {
        const classes = {
            low: 'bg-green-100 text-green-800',
            medium: 'bg-yellow-100 text-yellow-800',
            high: 'bg-orange-100 text-orange-800',
            urgent: 'bg-red-100 text-red-800'
        };
        return classes[priority] || classes.medium;
    },
    
    // Get status class for styling
    getStatusClass(status) {
        const classes = {
            todo: 'bg-gray-100 text-gray-800',
            in_progress: 'bg-blue-100 text-blue-800',
            review: 'bg-yellow-100 text-yellow-800',
            done: 'bg-green-100 text-green-800'
        };
        return classes[status] || classes.todo;
    },
    
    // Check if task is overdue
    isOverdue(dueDate, status) {
        if (!dueDate || status === 'done') return false;
        return new Date(dueDate) < new Date();
    }
};

// API utilities
window.API = {
    // Base API request function
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            showNotification('An error occurred. Please try again.', 'error');
            throw error;
        }
    },
    
    // Task API methods
    tasks: {
        async getAll() {
            return API.request('/tasks/api/tasks/');
        },
        
        async get(id) {
            return API.request(`/tasks/api/tasks/${id}/`);
        },
        
        async create(taskData) {
            return API.request('/tasks/api/tasks/', {
                method: 'POST',
                body: JSON.stringify(taskData)
            });
        },
        
        async update(id, taskData) {
            return API.request(`/tasks/api/tasks/${id}/`, {
                method: 'PATCH',
                body: JSON.stringify(taskData)
            });
        },
        
        async delete(id) {
            return API.request(`/tasks/api/tasks/${id}/`, {
                method: 'DELETE'
            });
        },
        
        async getKanbanData() {
            return API.request('/tasks/api/tasks/kanban_data/');
        },
        
        async getStats() {
            return API.request('/tasks/api/tasks/stats/');
        }
    }
};

// Loading state management
window.LoadingManager = {
    show(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.classList.add('opacity-50', 'pointer-events-none');
            
            // Add spinner if not already present
            if (!element.querySelector('.spinner')) {
                const spinner = document.createElement('div');
                spinner.className = 'spinner absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2';
                element.style.position = 'relative';
                element.appendChild(spinner);
            }
        }
    },
    
    hide(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.classList.remove('opacity-50', 'pointer-events-none');
            
            // Remove spinner
            const spinner = element.querySelector('.spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TaskUtils, API, LoadingManager };
}
