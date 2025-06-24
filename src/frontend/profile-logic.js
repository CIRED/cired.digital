// ==========================================
// ==========================================

const PROFILE_STORAGE_KEY = 'user-profile';

const profilePanel = document.getElementById('profile-panel');
const profileBtn = document.getElementById('profile-btn');
const profileCloseBtn = document.getElementById('profile-close-btn');
const saveProfileBtn = document.getElementById('save-profile');
const clearProfileBtn = document.getElementById('clear-profile');

const defaultProfile = {
    name: '',
    role: '',
    usage: '',
    organization: '',
    createdAt: null,
    updatedAt: null
};

// ==========================================
// ==========================================


function getProfileForSession() {
    const profile = getProfile();
    return sanitizeProfileForAnalytics(profile);
}

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
        createdAt: profile.createdAt,
        updatedAt: profile.updatedAt
    };
}


function showProfilePanel() {
    if (profilePanel) {
        loadProfileIntoForm();
        profilePanel.hidden = false;
    }
}

function hideProfilePanel() {
    if (profilePanel) {
        profilePanel.hidden = true;
    }
}

function loadProfileIntoForm() {
    const profile = getProfile();

    const editForm = document.getElementById('profile-edit-form');
    if (editForm) {
        editForm.querySelector('#edit-profile-name').value = profile.name || '';
        editForm.querySelector('#edit-profile-role').value = profile.role || '';
        editForm.querySelector('#edit-profile-usage').value = profile.usage || '';
        editForm.querySelector('#edit-profile-organization').value = profile.organization || '';
    }
}

function collectFormData(formPrefix = 'profile-') {
    return {
        name: document.getElementById(formPrefix + 'name')?.value || '',
        role: document.getElementById(formPrefix + 'role')?.value || '',
        usage: document.getElementById(formPrefix + 'usage')?.value || '',
        organization: document.getElementById(formPrefix + 'organization')?.value || ''
    };
}

// ==========================================
// ==========================================


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
            
            if (typeof onProfileCompleted === 'function' && !isOnboarded()) {
                onProfileCompleted();
            }
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
// INITIALIZATION
// ==========================================

function initializeProfile() {
    debugLog('Initializing profile system');

    if (profileBtn) {
        profileBtn.addEventListener('click', showProfilePanel);
    }

    if (profileCloseBtn) {
        profileCloseBtn.addEventListener('click', hideProfilePanel);
    }

    if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', handleSaveProfile);
    }

    if (clearProfileBtn) {
        clearProfileBtn.addEventListener('click', handleClearProfile);
    }

    debugLog('Profile system initialized');
}


// Initialize the profile system when the script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeProfile();
    });
} else {
    initializeProfile();
}

function initializeHelp() {
    const helpPanel = document.getElementById('help-panel');
    const helpCloseBtn = document.getElementById('help-close-btn');
    const helpBtn = document.getElementById('help-btn');

    if (!helpPanel || !helpCloseBtn || !helpBtn) {
        console.error('Mode d\'emploi modal elements not found');
        return;
    }

    helpCloseBtn.addEventListener('click', () => {
        helpPanel.hidden = true;
        helpBtn.hidden = false;
    });

    helpBtn.addEventListener('click', () => {
        helpPanel.hidden = false;
        helpBtn.hidden = true;
    });
}
