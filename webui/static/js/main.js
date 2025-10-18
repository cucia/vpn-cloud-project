// VPN Cloud Project - Main JavaScript

// Logout function
async function logout() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        window.location.href = '/';
    } catch (error) {
        console.error('Logout failed:', error);
        window.location.href = '/';
    }
}

// Utility function to show messages
function showMessage(elementId, message, type = 'info') {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.className = type;
        element.classList.remove('hidden');

        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }
}

// Format bytes to human readable
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Format date
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

console.log('VPN Cloud Project initialized');
