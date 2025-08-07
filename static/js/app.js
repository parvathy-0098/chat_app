// Newsletter Publisher Assistant - JavaScript Utilities

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize Feather Icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Auto-dismiss alerts after 10 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 10000);
    });
}

// File Upload Utilities
function validateFileUpload(fileInput) {
    const file = fileInput.files[0];
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedTypes = ['audio/', 'video/'];
    
    if (!file) {
        showNotification('Please select a file to upload.', 'warning');
        return false;
    }
    
    if (file.size > maxSize) {
        showNotification('File size must be less than 100MB. Please choose a smaller file.', 'danger');
        fileInput.value = '';
        return false;
    }
    
    const isValidType = allowedTypes.some(type => file.type.startsWith(type));
    if (!isValidType) {
        showNotification('Please select an audio or video file.', 'danger');
        fileInput.value = '';
        return false;
    }
    
    return true;
}

// Notification System
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 300px;
        max-width: 500px;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i data-feather="${getIconForType(type)}" class="me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close ms-2" onclick="this.closest('.alert').remove()"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Replace feather icons in the notification
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Auto remove
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }
    
    return notification;
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'alert-triangle',
        'warning': 'alert-circle',
        'info': 'info',
        'primary': 'bell'
    };
    return icons[type] || 'info';
}

// Copy to Clipboard Utilities
async function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    try {
        await navigator.clipboard.writeText(text);
        showNotification(successMessage, 'success', 3000);
        return true;
    } catch (err) {
        console.error('Failed to copy to clipboard:', err);
        
        // Fallback method
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            textArea.remove();
            showNotification(successMessage, 'success', 3000);
            return true;
        } catch (err) {
            textArea.remove();
            showNotification('Failed to copy to clipboard', 'danger');
            return false;
        }
    }
}

// Language Detection and Management
function updateLanguageInfo(languageCode) {
    const languageNames = {
        'auto': 'Auto-detect',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'no': 'Norwegian',
        'da': 'Danish',
        'fi': 'Finnish',
        'pl': 'Polish',
        'tr': 'Turkish'
    };
    
    return languageNames[languageCode] || languageCode.toUpperCase();
}

// Progress Tracking
function createProgressBar(container, initialProgress = 0) {
    const progressBar = document.createElement('div');
    progressBar.className = 'progress';
    progressBar.innerHTML = `
        <div class="progress-bar progress-bar-striped progress-bar-animated" 
             role="progressbar" 
             style="width: ${initialProgress}%"
             aria-valuenow="${initialProgress}" 
             aria-valuemin="0" 
             aria-valuemax="100">
        </div>
    `;
    
    container.appendChild(progressBar);
    
    return {
        element: progressBar,
        update: function(progress) {
            const bar = progressBar.querySelector('.progress-bar');
            bar.style.width = progress + '%';
            bar.setAttribute('aria-valuenow', progress);
        },
        complete: function() {
            const bar = progressBar.querySelector('.progress-bar');
            bar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            bar.classList.add('bg-success');
            this.update(100);
        },
        error: function() {
            const bar = progressBar.querySelector('.progress-bar');
            bar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            bar.classList.add('bg-danger');
        }
    };
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

function timeAgo(date) {
    const now = new Date();
    const secondsPast = (now.getTime() - date.getTime()) / 1000;
    
    if (secondsPast < 60) {
        return 'just now';
    }
    if (secondsPast < 3600) {
        return Math.floor(secondsPast / 60) + ' minutes ago';
    }
    if (secondsPast <= 86400) {
        return Math.floor(secondsPast / 3600) + ' hours ago';
    }
    if (secondsPast <= 2592000) {
        return Math.floor(secondsPast / 86400) + ' days ago';
    }
    if (secondsPast <= 31536000) {
        return Math.floor(secondsPast / 2592000) + ' months ago';
    }
    
    return Math.floor(secondsPast / 31536000) + ' years ago';
}

// Form Enhancement
function enhanceFormValidation() {
    const forms = document.querySelectorAll('form[data-validate="true"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Check required fields
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
            
            // Check file upload if present
            const fileInput = form.querySelector('input[type="file"]');
            if (fileInput && fileInput.hasAttribute('required')) {
                if (!validateFileUpload(fileInput)) {
                    isValid = false;
                }
            }
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields correctly.', 'danger');
            }
        });
    });
}

// Initialize form validation when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    enhanceFormValidation();
});

// Export functions for use in other scripts
window.AppUtils = {
    showNotification,
    copyToClipboard,
    validateFileUpload,
    formatFileSize,
    formatDuration,
    timeAgo,
    updateLanguageInfo,
    createProgressBar
};
