// Fonctions utilitaires pour l'application de gestion d'inventaire

// Fonction pour formater les prix
function formatPrice(price) {
    return parseFloat(price).toFixed(2) + ' €';
}

// Fonction pour formater les dates
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

// Fonction pour valider les formulaires
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    
    // Vérifier les champs requis
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Vérifier les champs numériques
    const numericFields = form.querySelectorAll('input[type="number"]');
    numericFields.forEach(field => {
        const value = parseFloat(field.value);
        const min = parseFloat(field.getAttribute('min') || '-Infinity');
        const max = parseFloat(field.getAttribute('max') || 'Infinity');
        
        if (isNaN(value) || value < min || value > max) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Initialisation des tooltips et validation des formulaires
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('fade-in');
    });

    // Dynamic stock status updates
    function updateStockStatus() {
        document.querySelectorAll('.stock-status').forEach(status => {
            const stock = parseInt(status.dataset.stock);
            const threshold = parseInt(status.dataset.threshold);
            
            status.classList.remove('stock-low', 'stock-out', 'stock-ok');
            
            if (stock === 0) {
                status.classList.add('stock-out');
                status.textContent = 'Rupture de stock';
            } else if (stock <= threshold) {
                status.classList.add('stock-low');
                status.textContent = 'Stock faible';
            } else {
                status.classList.add('stock-ok');
                status.textContent = 'En stock';
            }
        });
    }

    // Call stock status update on page load
    updateStockStatus();

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Dynamic search functionality
    const searchInput = document.querySelector('#searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const productCards = document.querySelectorAll('.product-card');
            
            productCards.forEach(card => {
                const productName = card.querySelector('.product-name').textContent.toLowerCase();
                const productRef = card.querySelector('.product-ref').textContent.toLowerCase();
                
                if (productName.includes(searchTerm) || productRef.includes(searchTerm)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        }, 300));
    }

    // Debounce function for search
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Smooth scrolling for anchor links
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

    // Add loading spinner to form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Chargement...';
                submitBtn.disabled = true;
            }
        });
    });

    // Initialize datepickers if they exist
    if (typeof flatpickr !== 'undefined') {
        flatpickr('.datepicker', {
            dateFormat: 'Y-m-d',
            locale: 'fr'
        });
    }
});