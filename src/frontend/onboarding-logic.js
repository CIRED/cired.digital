// ==========================================
// onboarding-logic.js
// ==========================================

// =========== Onboarding State ==============
// Use localStorage to avoid showing the onboarding panel multiple times
// across page reloads or sessions.

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
    const onboardingPanel = document.getElementById('onboarding-panel');
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
    showAsCompleted(stage);
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

function restoreOnboardingStages() {
    ONBOARDING_STAGES.forEach(stageKey => {
        if (isStageCompleted(stageKey)) {
            showAsCompleted(stageKey);
        }
    });

    if (isOnboarded()) {
        debugLog('User already onboarded');
        showOnboardingCompleted();
    }
}

// =========== Onboarding Stages =============

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

function goInput() {
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.focus();
        userInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function addHandlersToOnboarding() {
    attach('onboarding-close-btn', 'click', handleOnboardingCloseBtn);
    attach('onboarding-pass-btn', 'click', handleOnboardingPassBtn);
    attach('onboarding-profile-btn', 'click', showProfileDialog);
    attach('onboarding-reset-btn', 'click', restartOnboarding);
    attach('open-help-btn', 'click', showHelpPanel);
    attach('help-close-btn', 'click', () => onHelpCompleted());
    attach('focus-input-btn', 'click', goInput);
}

// ==========================================
// =========== Initialization ===============
// Called on pageload and on Guide Reset
// ==========================================

function initializeOnBoarding(openAnyway = false) {
    debugLog('Initializing the onboarding panel');

    const onboardingPanel = document.getElementById('onboarding-panel');
    onboardingPanel.innerHTML = onboardingHTML;

    addHandlersToOnboarding();

    restoreOnboardingStages();

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
