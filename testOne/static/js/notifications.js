/**
 * Global Notification System using Toastr
 * Centralized configuration and helper functions
 */

// Global Toastr Configuration
toastr.options = {
    "closeButton": true,
    "debug": false,
    "newestOnTop": true,
    "progressBar": true,
    "positionClass": "toast-top-right",
    "preventDuplicates": true,
    "onclick": null,
    "showDuration": "300",
    "hideDuration": "1000",
    "timeOut": "4000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
};

/**
 * Show success notification
 * @param {string} message - The message to display
 * @param {string} title - Optional title (default: "Éxito")
 */
function showSuccess(message, title = "Éxito") {
    toastr.success(message, title);
}

/**
 * Show error notification
 * @param {string} message - The message to display
 * @param {string} title - Optional title (default: "Error")
 */
function showError(message, title = "Error") {
    toastr.error(message, title);
}

/**
 * Show warning notification
 * @param {string} message - The message to display
 * @param {string} title - Optional title (default: "Advertencia")
 */
function showWarning(message, title = "Advertencia") {
    toastr.warning(message, title);
}

/**
 * Show info notification
 * @param {string} message - The message to display
 * @param {string} title - Optional title (default: "Información")
 */
function showInfo(message, title = "Información") {
    toastr.info(message, title);
}

/**
 * Auto-display Django messages on page load
 * Captures messages from Django's messages framework
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get all Django message elements
    const messageElements = document.querySelectorAll('.django-message');
    
    messageElements.forEach(function(element) {
        const messageType = element.dataset.messageType;
        const messageText = element.dataset.messageText;
        
        // Map Django message levels to Toastr functions
        switch(messageType) {
            case 'success':
                showSuccess(messageText);
                break;
            case 'error':
            case 'danger':
                showError(messageText);
                break;
            case 'warning':
                showWarning(messageText);
                break;
            case 'info':
                showInfo(messageText);
                break;
            default:
                showInfo(messageText);
        }
        
        // Remove the message element from DOM after displaying
        element.remove();
    });
});

/**
 * Handle form submission success
 * Can be called after AJAX operations
 */
function handleFormSuccess(message = "Operación completada exitosamente") {
    showSuccess(message);
}

/**
 * Handle form submission error
 * Can be called after AJAX operations
 */
function handleFormError(message = "Ocurrió un error al procesar la solicitud") {
    showError(message);
}

/**
 * Confirm action with notification
 * @param {string} message - Confirmation message
 * @param {function} callback - Function to execute if confirmed
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
        return true;
    }
    return false;
}
