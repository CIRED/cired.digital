// ==========================================
// ==========================================

const PROFILE_STORAGE_KEY = 'user-profile';
const PROFILE_ONBOARDED_KEY = 'profile-onboarded';

const onboardingModal = document.getElementById('onboarding-modal');
const profilePanel = document.getElementById('profile-panel');
const profileBtn = document.getElementById('profile-btn');
const profileCloseBtn = document.getElementById('profile-close-btn');
const skipProfileBtn = document.getElementById('skip-profile');
const submitProfileBtn = document.getElementById('submit-profile');
const saveProfileBtn = document.getElementById('save-profile');
const clearProfileBtn = document.getElementById('clear-profile');

const defaultProfile = {
    name: '',
    email: '',
    role: '',
    usage: '',
    organization: '',
    createdAt: null,
    updatedAt: null
};

// ==========================================
// ==========================================

function getProfile() {
    try {
        const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
        return stored ? { ...defaultProfile, ...JSON.parse(stored) } : { ...defaultProfile };
    } catch (error) {
        debugLog('Error loading profile', error);
        return { ...defaultProfile };
    }
}

function saveProfile(profileData) {
    try {
        const profile = {
            ...profileData,
            updatedAt: new Date().toISOString()
        };
        if (!profile.createdAt) {
            profile.createdAt = profile.updatedAt;
        }
        localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
        debugLog('Profile saved', profile);
        
        monitor(MonitorEventType.USER_PROFILE, {
            action: 'profile_updated',
            profile: sanitizeProfileForAnalytics(profile)
        });
        
        return profile;
    } catch (error) {
        debugLog('Error saving profile', error);
        return null;
    }
}

function clearProfile() {
    try {
        localStorage.removeItem(PROFILE_STORAGE_KEY);
        localStorage.removeItem(PROFILE_ONBOARDED_KEY);
        debugLog('Profile cleared');
        
        monitor(MonitorEventType.USER_PROFILE, {
            action: 'profile_cleared'
        });
        
        return true;
    } catch (error) {
        debugLog('Error clearing profile', error);
        return false;
    }
}

function sanitizeProfileForAnalytics(profile) {
    return {
        role: profile.role,
        usage: profile.usage,
        organization: profile.organization,
        hasName: !!profile.name,
        hasEmail: !!profile.email,
        createdAt: profile.createdAt,
        updatedAt: profile.updatedAt
    };
}

function isOnboarded() {
    return localStorage.getItem(PROFILE_ONBOARDED_KEY) === 'true';
}

function setOnboarded() {
    localStorage.setItem(PROFILE_ONBOARDED_KEY, 'true');
}

// ==========================================
// ==========================================

function showOnboardingModal() {
    if (onboardingModal) {
        onboardingModal.classList.remove('hidden');
        const firstInput = onboardingModal.querySelector('input, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

function hideOnboardingModal() {
    if (onboardingModal) {
        onboardingModal.classList.add('hidden');
    }
}

function showProfilePanel() {
    if (profilePanel) {
        profilePanel.classList.remove('hidden');
        loadProfileIntoForm();
    }
}

function hideProfilePanel() {
    if (profilePanel) {
        profilePanel.classList.add('hidden');
    }
}

function loadProfileIntoForm() {
    const profile = getProfile();
    
    const editForm = document.getElementById('profile-edit-form');
    if (editForm) {
        editForm.querySelector('#edit-profile-name').value = profile.name || '';
        editForm.querySelector('#edit-profile-email').value = profile.email || '';
        editForm.querySelector('#edit-profile-role').value = profile.role || '';
        editForm.querySelector('#edit-profile-usage').value = profile.usage || '';
        editForm.querySelector('#edit-profile-organization').value = profile.organization || '';
    }
}

function collectFormData(formPrefix = 'profile-') {
    return {
        name: document.getElementById(formPrefix + 'name')?.value || '',
        email: document.getElementById(formPrefix + 'email')?.value || '',
        role: document.getElementById(formPrefix + 'role')?.value || '',
        usage: document.getElementById(formPrefix + 'usage')?.value || '',
        organization: document.getElementById(formPrefix + 'organization')?.value || ''
    };
}

// ==========================================
// ==========================================

function handleSkipProfile() {
    hideOnboardingModal();
    setOnboarded();
    
    monitor(MonitorEventType.USER_PROFILE, {
        action: 'onboarding_skipped'
    });
}

function handleSubmitProfile() {
    const profileData = collectFormData();
    const savedProfile = saveProfile(profileData);
    
    if (savedProfile) {
        hideOnboardingModal();
        setOnboarded();
        
        monitor(MonitorEventType.USER_PROFILE, {
            action: 'onboarding_completed',
            profile: sanitizeProfileForAnalytics(savedProfile)
        });
    }
}

function handleSaveProfile() {
    const profileData = collectFormData('edit-profile-');
    const savedProfile = saveProfile(profileData);
    
    if (savedProfile) {
        const saveBtn = document.getElementById('save-profile');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Sauvegardé !';
        saveBtn.style.backgroundColor = '#059669';
        
        setTimeout(() => {
            saveBtn.textContent = originalText;
            saveBtn.style.backgroundColor = '';
        }, 2000);
    }
}

function handleClearProfile() {
    if (confirm('Êtes-vous sûr de vouloir effacer votre profil ? Cette action est irréversible.')) {
        if (clearProfile()) {
            hideProfilePanel();
            alert('Profil effacé avec succès.');
        }
    }
}

// ==========================================
// ==========================================

function handleModalKeydown(event) {
    if (event.key === 'Escape') {
        hideOnboardingModal();
        hideProfilePanel();
    }
    
    if (event.key === 'Tab') {
        const modal = event.target.closest('.modal-overlay, #profile-panel');
        if (modal) {
            const focusableElements = modal.querySelectorAll(
                'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            if (event.shiftKey && event.target === firstElement) {
                event.preventDefault();
                lastElement.focus();
            } else if (!event.shiftKey && event.target === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        }
    }
}

// ==========================================
// INITIALIZATION
// ==========================================

function initializeProfile() {
    debugLog('Initializing profile system');
    
    if (!isOnboarded()) {
        setTimeout(showOnboardingModal, 1000);
    }
    
    if (profileBtn) {
        profileBtn.addEventListener('click', showProfilePanel);
    }
    
    if (profileCloseBtn) {
        profileCloseBtn.addEventListener('click', hideProfilePanel);
    }
    
    if (skipProfileBtn) {
        skipProfileBtn.addEventListener('click', handleSkipProfile);
    }
    
    if (submitProfileBtn) {
        submitProfileBtn.addEventListener('click', handleSubmitProfile);
    }
    
    if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', handleSaveProfile);
    }
    
    if (clearProfileBtn) {
        clearProfileBtn.addEventListener('click', handleClearProfile);
    }
    
    document.addEventListener('keydown', handleModalKeydown);
    
    if (onboardingModal) {
        onboardingModal.addEventListener('click', (event) => {
            if (event.target === onboardingModal) {
                hideOnboardingModal();
            }
        });
    }
    
    debugLog('Profile system initialized');
}

// ==========================================
// ==========================================

function getProfileForSession() {
    const profile = getProfile();
    return sanitizeProfileForAnalytics(profile);
}

window.getProfileForSession = getProfileForSession;
