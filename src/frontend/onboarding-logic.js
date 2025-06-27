// ==========================================
// onboarding-logic.js
// ==========================================

const onboardingPanel = document.getElementById('onboarding-panel');

// ==========================================
// =========== Onboarding State ==============

const PROFILE_ONBOARDED_KEY = 'profile-onboarded';

function isOnboarded() {
    return localStorage.getItem(PROFILE_ONBOARDED_KEY) === 'true';
}

function setOnboarded() {
    localStorage.setItem(PROFILE_ONBOARDED_KEY, 'true');
}

function showOnboardingPanel() {
    if (onboardingPanel) {
        onboardingPanel.hidden = false;
    }
}

function hideOnboardingPanel() {
    if (onboardingPanel) {
        onboardingPanel.hidden = true;
    }

    const configBtn = document.getElementById('config-btn');
    if (configBtn && isOnboarded()) {
        configBtn.style.display = '';
    }
}


// ==========================================
// ==========================================

function completeStage(stageId, statusId, nextStageId) {
    const stage = document.getElementById(stageId);
    const status = document.getElementById(statusId);
    const nextStage = document.getElementById(nextStageId);

    if (stage) {
        stage.className = 'onboarding-complete';
    }
    if (status) {
        status.textContent = '✅ Terminé';
    }
    if (nextStage) {
        nextStage.className = 'onboarding-focus';
    }

    debugLog('Onboarding stage completed', { stageId, nextStageId });
}


// ==========================================
// ==========================================

function onFirstResponseCompleted() {
    completeStage('onboarding-stage-first-question', 'first-response-status', 'onboarding-stage-feedback');
    debugLog('First response stage completed');
}

function onFeedbackCompleted() {
    completeStage('onboarding-stage-feedback', null, 'onboarding-stage-help');
    debugLog('Feedback stage completed');
}

function onHelpCompleted() {
    completeStage('onboarding-stage-help', 'help-status', 'onboarding-stage-profile');
    debugLog('Help stage completed');
}

function onProfileCompleted() {
    completeStage('onboarding-stage-profile', 'profile-status', 'onboarding-stage-completed');
    debugLog('Profile stage completed, onboarding finished');
}

function handleOnboardingCloseBtn() {
    debugLog('Closing onboarding panel');
    // Shortcut: complete all stages of the onboarding flow
    onFirstResponseCompleted();
    onFeedbackCompleted();
    onHelpCompleted();
    onProfileCompleted();
    setOnboarded();
    hideOnboardingPanel();
}

function restartOnboarding() {
    debugLog('Onboarding reset and relaunch');
    localStorage.removeItem(PROFILE_ONBOARDED_KEY);
    initializeOnBoarding();
}

// ==========================================
// =========== Initialization ===============
// ==========================================

function initializeOnBoarding() {
    debugLog('Initializing the onboarding panel');

    document.getElementById('onboarding-panel').innerHTML = onboardingHTML;

    const onboardingCloseBtn = document.getElementById('onboarding-close-btn');
    if (onboardingCloseBtn) {
        onboardingCloseBtn.addEventListener('click', handleOnboardingCloseBtn);
    }

    const onboardingResetBtn = document.getElementById('onboarding-reset-btn');
    if (onboardingResetBtn) {
        onboardingResetBtn.addEventListener('click', restartOnboarding);
    }

    const openProfileBtn = document.getElementById('open-profile-btn');
    if (openProfileBtn) {
        openProfileBtn.addEventListener('click', showProfilePanel);
    }

    const openHelpBtn = document.getElementById('open-help-btn');
    if (openHelpBtn) {
        openHelpBtn.addEventListener('click', showHelpPanel);
    }

    const helpCloseBtn = document.getElementById('help-close-btn');
    if (helpCloseBtn) {
        helpCloseBtn.addEventListener('click', () => onHelpCompleted());
    }

    const focusInputBtn = document.getElementById('focus-input');
    if (focusInputBtn) {
        focusInputBtn.addEventListener('click', () => {
            const userInput = document.getElementById('user-input');
            if (userInput) {
                userInput.focus();
                userInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    if (!isOnboarded()) {
        debugLog('User not onboarded, showing the onboarding panel');
        showOnboardingPanel();
    }
}

// Initialize the onboarding system when the script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeOnBoarding();
    });
}
else {
    initializeOnBoarding();
}
