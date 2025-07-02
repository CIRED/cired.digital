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
    initializeOnBoarding(openAnyway = true);
}

function hideOnboardingPanel() {
    if (onboardingPanel) {
        onboardingPanel.hidden = true;
    }

    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn && isOnboarded()) {
        settingsBtn.style.display = '';
    }
}

function setStageCompleted(stage) {
    localStorage.setItem(`onboarding-stage-${stage}`, 'true');
}

function isStageCompleted(stage) {
    return localStorage.getItem(`onboarding-stage-${stage}`) === 'true';
}

function isOnboardingFullyCompleted() {
    return ONBOARDING_STAGES.every(isStageCompleted);
}

function clearOnboardingStages() {
    ONBOARDING_STAGES.forEach(stage => localStorage.removeItem(`onboarding-stage-${stage}`));
}

function completeStage(stage) {
    showCompleted(stage);
    if (isStageCompleted(stage)) {
        console.warn(`Stage ${stage} is already completed`);
        return;
    }
    if (stage) {
        setStageCompleted(stage);
    }
    debugLog('Onboarding stage completed', { stage });
    if (isOnboardingFullyCompleted()) {
        debugLog('Onboarding fully completed');
        showOnboardingCompleted();
        setOnboarded();
    }
}

// ==========================================
// ==========================================

function onFirstResponseCompleted() {
    completeStage('question');
}

function onFeedbackCompleted() {
    completeStage('feedback');
}

function onHelpCompleted() {
    completeStage('help');
}

function onProfileCompleted() {
    completeStage('profile');
}

function handleOnboardingCloseBtn() {
    hideOnboardingPanel();
}

function handleOnboardingPassBtn() {
    debugLog('Pass on onboarding');
    ONBOARDING_STAGES.forEach(setStageCompleted);
    setOnboarded();
    hideOnboardingPanel();
}

function restartOnboarding() {
    debugLog('Onboarding reset and relaunch');
    localStorage.removeItem(PROFILE_ONBOARDED_KEY);
    clearOnboardingStages();
    initializeOnBoarding();
}

function addHandlersToOnboarding() {
    // Add event listeners for onboarding actions
    const onboardingCloseBtn = document.getElementById('onboarding-close-btn');
    if (onboardingCloseBtn) {
        onboardingCloseBtn.addEventListener('click', handleOnboardingCloseBtn);
    }

    const onboardingPassBtn = document.getElementById('onboarding-pass-btn');
    if (onboardingPassBtn) {
        onboardingPassBtn.addEventListener('click', handleOnboardingPassBtn);
    }

    const onboardingResetBtn = document.getElementById('onboarding-reset-btn');
    if (onboardingResetBtn) {
        onboardingResetBtn.addEventListener('click', restartOnboarding);
    }

    const openProfileBtn = document.getElementById('open-profile-btn');
    if (openProfileBtn) {
        openProfileBtn.addEventListener('click', showProfileDialog);
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
}

// ==========================================
// =========== Initialization ===============
// Called on pageload and on Guide Reset
// ==========================================

function initializeOnBoarding(openAnyway = false) {
    debugLog('Initializing the onboarding panel');

    const onboardingPanel = document.getElementById('onboarding-panel');
    onboardingPanel.innerHTML = onboardingHTML;

    // Update for the completed stages
    ONBOARDING_STAGES.forEach(stageKey => {
        if (isStageCompleted(stageKey)) {
            showCompleted(stageKey);
        }
    });

    addHandlersToOnboarding();

    if (isOnboarded()) {
        debugLog('User already onboarded');
        showOnboardingCompleted();
    }

    if (!isOnboarded() || openAnyway) {
        onboardingPanel.hidden = false;
    }
}

// Initialize the onboarding system when the script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeOnBoarding();
    });
} else {
    initializeOnBoarding();
}
