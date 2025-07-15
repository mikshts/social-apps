document.addEventListener('DOMContentLoaded', () => {
  // Image Upload Preview
  const imgInput = document.getElementById('id_profileimg');
  const imageContainer = document.querySelector('.image-upload-container');
  
  if (imgInput && imageContainer) {
    // Click on container triggers file input
    imageContainer.addEventListener('click', () => imgInput.click());
    
    imgInput.addEventListener('change', function(e) {
      if (this.files && this.files[0]) {
        const file = this.files[0];
        
        // Client-side validation
        if (file.size > 5 * 1024 * 1024) {
          alert('File size exceeds 5MB limit');
          return;
        }
        
        if (!file.type.match('image.*')) {
          alert('Please select an image file');
          return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
          // Update existing image or create new one
          const existingImg = document.getElementById('current-profile-img');
          const placeholder = document.getElementById('no-image-placeholder');
          
          if (existingImg) {
            existingImg.src = e.target.result;
          } else if (placeholder) {
            placeholder.innerHTML = `
              <img src="${e.target.result}" 
                   alt="Profile Preview" 
                   class="preview-img"
                   id="current-profile-img">
              <div class="image-overlay">
                <span>Click to change</span>
              </div>
            `;
          }
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Bio Character Counter
  const bioTextarea = document.getElementById('id_bio');
  if (bioTextarea) {
    const counter = document.getElementById('bio-count');
    
    const updateCounter = () => {
      const length = bioTextarea.value.length;
      counter.textContent = length;
      counter.style.color = length > 900 ? '#e74c3c' : 
                           length > 800 ? '#f39c12' : '#27ae60';
    };
    
    // Initialize and update on input
    updateCounter();
    bioTextarea.addEventListener('input', updateCounter);
  }

  // Form Submission Loading State
  const form = document.getElementById('profile-form');
  if (form) {
    form.addEventListener('submit', () => {
      const saveBtn = document.getElementById('save-btn');
      if (saveBtn) {
        const btnText = saveBtn.querySelector('.btn-text');
        const spinner = saveBtn.querySelector('.loading-spinner');
        
        saveBtn.disabled = true;
        btnText.textContent = 'Saving...';
        spinner.style.display = 'inline-block';
      }
    });
  }
});

// Modal Functions
function openMyCustomModal(modalId) {
  document.getElementById(modalId).style.display = 'flex';
}

function closeMyCustomModal(modalId) {
  document.getElementById(modalId).style.display = 'none';
}

function openDeactivateAccountModal() {
  const periodSelect = document.getElementById('deactivation_period');
  const display = document.getElementById('deactivationDaysDisplay');
  const hiddenInput = document.getElementById('modalDeactivationPeriod');
  
  if (periodSelect && display && hiddenInput) {
    const days = periodSelect.value;
    display.textContent = `${days} days`;
    hiddenInput.value = days;
    openMyCustomModal('deactivateAccountModal');
  }
}

// Reset Form Function
function resetForm() {
  if (confirm('Reset all changes?')) {
    const form = document.getElementById('profile-form');
    if (form) {
      form.reset();
      
      // Reset bio counter
      const bio = document.getElementById('id_bio');
      const counter = document.getElementById('bio-count');
      if (bio && counter) {
        counter.textContent = bio.value.length;
        counter.style.color = '#27ae60';
      }
      
      // Reset profile image
      const originalImg = document.getElementById('current-profile-img');
      if (originalImg && originalImg.dataset.originalSrc) {
        originalImg.src = originalImg.dataset.originalSrc;
      }
    }
  }
}

// Close modals when clicking outside
window.addEventListener('click', (event) => {
  ['deactivateAccountModal', 'deleteAccountModal', 'logoutAccountModal'].forEach(modalId => {
    const modal = document.getElementById(modalId);
    if (modal && event.target === modal) {
      closeMyCustomModal(modalId);
    }
  });
});