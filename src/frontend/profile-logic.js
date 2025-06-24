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
        displayStoredProfile(); // Affiche les données stockées
        profilePanel.classList.remove('hidden');
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
        editForm.querySelector('#edit-profile-role').value = profile.role || '';
        editForm.querySelector('#edit-profile-usage').value = profile.usage || '';
        editForm.querySelector('#edit-profile-organization').value = profile.organization || '';
    }
}

function collectFormData(formPrefix = 'profile-') {
    return {
        name: document.getElementById(formPrefix + 'name')?.value || '',
        role: document.querySelector('input[name="profile-role"]:checked')?.value || '',
        usage: document.querySelector('input[name="profile-usage"]:checked')?.value || '',
        organization: document.querySelector('input[name="profile-organization"]:checked')?.value || ''
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
            hideProfilePanel();
        }, 500);
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

function displayStoredProfile() {
    const display = document.getElementById('profile-data-display');
    if (!display) return;
    try {
        const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
        const onboarded = localStorage.getItem(PROFILE_ONBOARDED_KEY);
        if (stored) {
            const profile = JSON.parse(stored);
            display.innerHTML = `
                <ul>
                    <li><b>Pseudonyme:</b> ${profile.name || ''}</li>
                    <li><b>Affiliation:</b> ${profile.organization || ''}</li>
                    <li><b>Rôle:</b> ${profile.role || ''}</li>
                    <li><b>Usage IA:</b> ${profile.usage || ''}</li>
                    <li><b>Créé le:</b> ${profile.createdAt ? new Date(profile.createdAt).toLocaleString() : ''}</li>
                    <li><b>Modifié le:</b> ${profile.updatedAt ? new Date(profile.updatedAt).toLocaleString() : ''}</li>
                    <li><b>${PROFILE_ONBOARDED_KEY}:</b> ${onboarded !== null ? onboarded : ''}</li>
                </ul>
            `;
        } else {
            display.textContent = 'Aucune donnée de profil enregistrée.';
        }
    } catch (e) {
        display.textContent = 'Erreur de lecture du profil.';
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

    // Ajout du listener pour relancer le guide de démarrage rapide
    const restartOnboardingBtn = document.getElementById('restart-onboarding');
    if (restartOnboardingBtn) {
        restartOnboardingBtn.addEventListener('click', () => {
            if (typeof restartOnboarding === 'function') {
                restartOnboarding();
            }
        });
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
