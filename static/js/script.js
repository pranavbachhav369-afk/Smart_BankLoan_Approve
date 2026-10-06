// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('shadow');
    } else {
        navbar.classList.remove('shadow');
    }
});

// Add fade-in animation to elements
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card, .step-card, .stat-item').forEach(el => {
    observer.observe(el);
});

// Form validation helper
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        if (input.hasAttribute('required') && !input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
        
        // Email validation
        if (input.type === 'email' && input.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                isValid = false;
                input.classList.add('is-invalid');
            }
        }
        
        // Number validation
        if (input.type === 'number' && input.value) {
            const min = parseFloat(input.getAttribute('min'));
            const max = parseFloat(input.getAttribute('max'));
            const value = parseFloat(input.value);
            
            if (min !== undefined && value < min) {
                isValid = false;
                input.classList.add('is-invalid');
            }
            if (max !== undefined && value > max) {
                isValid = false;
                input.classList.add('is-invalid');
            }
        }
    });
    
    return isValid;
}

// Add input event listeners for real-time validation
document.querySelectorAll('input, select, textarea').forEach(input => {
    input.addEventListener('input', function() {
        this.classList.remove('is-invalid');
    });
});

// Loading state helper
function setLoading(button, isLoading, originalText) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = originalText || button.dataset.originalText || button.innerHTML;
    }
}

// Toast notification helper
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    toastContainer.appendChild(toast);
    document.body.appendChild(toastContainer);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toastContainer.remove();
    });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Prevent form resubmission on page refresh
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

// Add active class to current page in navbar
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// Handle browser back button
window.addEventListener('popstate', function() {
    // Reset any forms if needed
    document.querySelectorAll('form').forEach(form => {
        form.reset();
        form.classList.remove('was-validated');
    });
});

// Console welcome message
console.log('%c LoanPredict ', 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-size: 20px; font-weight: bold; padding: 10px; border-radius: 5px;');
console.log('%c AI-Powered Loan Approval Prediction System ', 'color: #667eea; font-size: 14px;');

// ==========================================================================
// Relative Time Calculation & Live Activity Feed System
// ==========================================================================
function formatRelativeTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    const now = new Date();
    const diffSeconds = Math.floor((now - date) / 1000);

    if (diffSeconds < 15) return 'Just now';
    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 30) return `${diffDays}d ago`;
    const diffMonths = Math.floor(diffDays / 30);
    if (diffMonths < 12) return `${diffMonths}mo ago`;
    return `${Math.floor(diffMonths / 12)}y ago`;
}

function updateRelativeTimePills() {
    document.querySelectorAll('.time-ago-pill[data-timestamp]').forEach(pill => {
        const ts = pill.getAttribute('data-timestamp');
        if (ts) {
            const rel = formatRelativeTime(ts);
            if (rel) {
                pill.textContent = rel;
            }
        }
    });
}

function updateDashboardData() {
    const feedContainer = document.getElementById('activityFeedContainer');
    if (!feedContainer) return;

    fetch('/api/user-recent-activity')
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                // Update Top 4 KPI Cards
                const kpiTotal = document.getElementById('kpiTotalPredictions');
                const kpiApproved = document.getElementById('kpiApprovedCount');
                const kpiRejected = document.getElementById('kpiRejectedCount');
                const kpiRate = document.getElementById('kpiApprovalRate');

                if (kpiTotal) kpiTotal.textContent = data.user_predictions_count;
                if (kpiApproved) kpiApproved.textContent = data.user_approved_count;
                if (kpiRejected) kpiRejected.textContent = data.user_rejected_count;
                if (kpiRate) kpiRate.textContent = `${data.user_approval_rate}%`;

                // Update Feed List
                if (data.activities && data.activities.length > 0) {
                    let html = '';
                    data.activities.forEach(pred => {
                        const isApproved = pred.prediction_result === 'Approved';
                        const itemClass = isApproved ? 'approved-item' : 'rejected-item';
                        const statusClass = isApproved ? 'approved' : 'rejected';
                        const iconClass = isApproved ? 'bi-check-lg' : 'bi-x-lg';
                        const amountStr = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(pred.loan_amount);
                        const totalIncomeStr = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(pred.applicant_income + pred.coapplicant_income);
                        const probStr = pred.probability ? (pred.probability * 100).toFixed(1) : '75.0';
                        const creditBadge = pred.credit_history === 1 ? 
                            '<i class="bi bi-shield-check text-success me-1"></i><span class="text-success fw-semibold">Good Credit</span>' : 
                            '<i class="bi bi-shield-exclamation text-danger me-1"></i><span class="text-danger fw-semibold">Poor Credit</span>';
                        const relTime = formatRelativeTime(pred.created_at);

                        html += `
                        <div class="activity-item ${itemClass}">
                            <div class="d-flex align-items-center gap-3">
                                <div class="activity-status-icon ${statusClass}">
                                    <i class="bi ${iconClass}"></i>
                                </div>
                                <div>
                                    <div class="d-flex align-items-center gap-2 mb-1">
                                        <span class="fw-bold text-white" style="font-size: 0.9rem;">Prediction #PRED-${pred.id}</span>
                                        <span class="activity-badge ${statusClass}">${pred.prediction_result}</span>
                                    </div>
                                    <div class="d-flex flex-wrap align-items-center gap-3" style="font-size: 0.78rem; color: var(--text-secondary);">
                                        <span><i class="bi bi-cash-stack me-1"></i><strong>₹${amountStr}</strong> Loan</span>
                                        <span><i class="bi bi-calendar3 me-1"></i>${parseInt(pred.loan_amount_term)} Days</span>
                                        <span><i class="bi bi-wallet2 me-1"></i>Income: ₹${totalIncomeStr}</span>
                                        <span>${creditBadge}</span>
                                        <span><i class="bi bi-cpu me-1"></i>AI Confidence: <strong>${probStr}%</strong></span>
                                    </div>
                                </div>
                            </div>
                            <div class="text-end ms-3 flex-shrink-0">
                                <span class="badge bg-dark text-info border border-info border-opacity-25 px-2.5 py-1 mb-1 time-ago-pill" data-timestamp="${pred.created_at}" style="font-size: 0.725rem; font-weight: 500;">
                                    ${relTime}
                                </span>
                                <div style="font-size: 0.7rem; color: var(--text-muted);">
                                    ${pred.created_at_formatted}
                                </div>
                            </div>
                        </div>`;
                    });
                    feedContainer.innerHTML = html;
                }
            }
        })
        .catch(err => console.debug('Live feed update notice:', err));
}

document.addEventListener('DOMContentLoaded', function() {
    updateRelativeTimePills();
    setInterval(updateRelativeTimePills, 15000);

    if (document.getElementById('activityFeedContainer')) {
        setInterval(updateDashboardData, 15000);
    }
});

