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

// Fonction pour afficher une notification toast
function showToast(title, message, type = 'info') {
    const toast = document.getElementById('liveToast');
    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');
    const toastTime = document.getElementById('toastTime');

    // Set content
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    toastTime.textContent = 'À l\'instant';

    // Set toast color based on type
    toast.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    const toastHeader = toast.querySelector('.toast-header i');
    toastHeader.classList.remove('text-success', 'text-danger', 'text-warning', 'text-info');

    switch(type) {
        case 'success':
            toastHeader.classList.add('text-success');
            toastHeader.classList.remove('fa-info-circle', 'fa-exclamation-circle', 'fa-exclamation-triangle');
            toastHeader.classList.add('fa-check-circle');
            break;
        case 'danger':
            toastHeader.classList.add('text-danger');
            toastHeader.classList.remove('fa-info-circle', 'fa-check-circle', 'fa-exclamation-triangle');
            toastHeader.classList.add('fa-exclamation-circle');
            break;
        case 'warning':
            toastHeader.classList.add('text-warning');
            toastHeader.classList.remove('fa-info-circle', 'fa-check-circle', 'fa-exclamation-circle');
            toastHeader.classList.add('fa-exclamation-triangle');
            break;
        default:
            toastHeader.classList.add('text-info');
            toastHeader.classList.remove('fa-check-circle', 'fa-exclamation-circle', 'fa-exclamation-triangle');
            toastHeader.classList.add('fa-info-circle');
    }

    // Show the toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Fonction pour basculer entre le mode clair et sombre
function toggleDarkMode() {
    const htmlElement = document.documentElement;
    const isDarkMode = htmlElement.getAttribute('data-bs-theme') === 'dark';
    const newMode = isDarkMode ? 'light' : 'dark';

    // Update HTML attribute
    htmlElement.setAttribute('data-bs-theme', newMode);

    // Update button icon
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        const icon = darkModeToggle.querySelector('i');
        if (newMode === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            darkModeToggle.setAttribute('title', 'Passer en mode clair');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            darkModeToggle.setAttribute('title', 'Passer en mode sombre');
        }
    }

    // Save preference to localStorage
    localStorage.setItem('darkMode', newMode);

    // Show toast notification
    const title = newMode === 'dark' ? 'Mode sombre activé' : 'Mode clair activé';
    const message = newMode === 'dark' ? 'L\'interface est maintenant en mode sombre.' : 'L\'interface est maintenant en mode clair.';
    showToast(title, message, 'info');
}

// Initialisation des tooltips, du mode sombre et validation des formulaires
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize dark mode from saved preference
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode) {
        document.documentElement.setAttribute('data-bs-theme', savedMode);
        if (savedMode === 'dark') {
            const darkModeToggle = document.getElementById('darkModeToggle');
            if (darkModeToggle) {
                const icon = darkModeToggle.querySelector('i');
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
                darkModeToggle.setAttribute('title', 'Passer en mode clair');
            }
        }
    }

    // Add dark mode toggle event listener
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }

    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('fade-in');
    });

    // Add delete buttons to product cards
    function addDeleteButtons() {
        // Get all product cards
        const productCards = document.querySelectorAll('.product-card');

        productCards.forEach(card => {
            // Find the card footer
            const cardFooter = card.querySelector('.card-footer');
            if (!cardFooter) return;

            // Find the product ID from the update link
            const updateLink = cardFooter.querySelector('a[href*="update-stock"]');
            if (!updateLink) return;

            // Extract product ID from the href attribute
            const hrefParts = updateLink.getAttribute('href').split('/');
            const productId = hrefParts[hrefParts.length - 1];

            // Create delete form
            const deleteForm = document.createElement('form');
            deleteForm.setAttribute('action', `/products/delete/${productId}`);
            deleteForm.setAttribute('method', 'POST');
            deleteForm.classList.add('d-grid', 'mt-2');

            // Create delete button
            const deleteButton = document.createElement('button');
            deleteButton.setAttribute('type', 'submit');
            deleteButton.classList.add('btn', 'btn-outline-danger');
            deleteButton.setAttribute('onclick', "return confirm('Êtes-vous sûr de vouloir supprimer ce produit?');");
            deleteButton.innerHTML = '<i class="fas fa-trash-alt me-1"></i>Supprimer';

            // Append button to form
            deleteForm.appendChild(deleteButton);

            // Append form to card footer
            cardFooter.appendChild(deleteForm);
        });
    }

    // Call the function to add delete buttons
    addDeleteButtons();

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

            // Add stock progress bar if it doesn't exist
            const parentDiv = status.parentElement;
            if (!parentDiv.querySelector('.stock-progress')) {
                // Create progress bar container
                const progressDiv = document.createElement('div');
                progressDiv.className = 'stock-progress mt-2';

                // Create progress bar
                const progressBar = document.createElement('div');
                progressBar.className = 'stock-progress-bar';

                // Calculate percentage (max 100%)
                let percentage = (stock / (threshold * 2)) * 100;
                if (percentage > 100) percentage = 100;

                // Set progress bar width and color
                progressBar.style.width = percentage + '%';
                if (stock === 0) {
                    progressBar.classList.add('bg-danger');
                } else if (stock <= threshold) {
                    progressBar.classList.add('bg-warning');
                } else {
                    progressBar.classList.add('bg-success');
                }

                // Append progress bar to container
                progressDiv.appendChild(progressBar);

                // Append container after the status element
                parentDiv.insertBefore(progressDiv, status.nextSibling);

                // Add stock level indicator
                const stockInfo = document.createElement('small');
                stockInfo.className = 'text-muted d-block mt-1';
                stockInfo.innerHTML = `<strong>${stock}</strong>/${threshold} unités`;
                parentDiv.insertBefore(stockInfo, progressDiv.nextSibling);
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
