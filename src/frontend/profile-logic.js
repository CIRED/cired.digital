// ==========================================
// ==========================================

const PROFILE_STORAGE_KEY = 'user-profile';

const profilePanel = document.getElementById('profile-panel');
const profileBtn = document.getElementById('profile-btn');
const profileCloseBtn = document.getElementById('profile-close-btn');
const saveProfileBtn = document.getElementById('save-profile-btn');
const clearProfileBtn = document.getElementById('clear-profile-btn');
const restartOnboardingBtn = document.getElementById('restart-onboarding-btn');

const defaultProfile = {
    id: null,
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

function collectFormData(formPrefix = 'profile-') {
    return {
        role: document.querySelector('input[name="profile-role"]:checked')?.value || '',
        usage: document.querySelector('input[name="profile-usage"]:checked')?.value || '',
        organization: document.querySelector('input[name="profile-organization"]:checked')?.value || ''
    };
}

function saveProfile(profileData) {
    try {
        const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
        const existing = stored ? JSON.parse(stored) : {};
        const profile = {
            ...defaultProfile,
            ...existing,
            ...profileData,
            id: existing.id || generateUUID(),
            updatedAt: new Date().toISOString()
        };
        if (!profile.createdAt) {
            profile.createdAt = profile.updatedAt;
        }
        localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
        debugLog('Profile saved', profile);

        monitor(MonitorEventType.USER_PROFILE, {
            action: 'profile_updated',
            profile: profile
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


// ==========================================
// Button Handlers
// ==========================================


function showProfilePanel() {
    if (profilePanel) {
        updateProfilePanel();
        profilePanel.classList.remove('hidden');
    }
}

function hideProfilePanel() {
    if (profilePanel) {
        profilePanel.classList.add('hidden');
    }
}

function handleSaveProfile() {
    const profileData = collectFormData('edit-profile-');
    const savedProfile = saveProfile(profileData);
    if (savedProfile) {
        onProfileCompleted();
    }
}

function handleClearProfile() {
    debugLog('Clearing profile');
    if (clearProfile()) {
        debugLog('Profile cleared successfully');
    } else {
        debugLog('Failed to clear profile');
    }
    updateProfilePanel();
}

function handleRestartOnboarding() {
    debugLog('Restarting onboarding process');
    clearProfile();
    hideProfilePanel();
    restartOnboarding();      // defined in onboarding-logic.js
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

    if (restartOnboardingBtn) {
        restartOnboardingBtn.addEventListener('click', handleRestartOnboarding);
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
