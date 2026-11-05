/**
 * INKSPACE Global Application Scripts
 * Manages toast dismissals, bookmark triggers, and general UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Bookmark button toggle
  const bookmarkBtn = document.getElementById('bookmarkBtn');
  if (bookmarkBtn) {
    bookmarkBtn.addEventListener('click', function () {
      const icon = this.querySelector('i');
      if (icon.classList.contains('bi-bookmark')) {
        icon.classList.replace('bi-bookmark', 'bi-bookmark-fill');
        icon.style.color = '#C65D24';
      } else {
        icon.classList.replace('bi-bookmark-fill', 'bi-bookmark');
        icon.style.color = '';
      }
    });
  }

  // Follow author button toggle
  const followBtn = document.getElementById('followAuthorBtn');
  if (followBtn) {
    followBtn.addEventListener('click', function () {
      if (this.textContent.includes('Follow')) {
        this.innerHTML = '<i class="bi bi-check2 me-1"></i> Following';
        this.className = 'btn btn-orange-secondary btn-sm rounded-pill w-100 fw-medium';
        this.style.backgroundColor = '#FFEDD5';
        this.style.color = '#C65D24';
        this.style.borderColor = '#FDBA74';
      } else {
        this.innerHTML = '<i class="bi bi-plus-lg me-1"></i> Follow';
        this.className = 'btn btn-orange-outline btn-sm rounded-pill w-100 fw-medium';
        this.style.backgroundColor = 'transparent';
        this.style.color = '#C65D24';
        this.style.borderColor = '#C65D24';
      }
    });
  }
});
