// ==========================================
// onboarding-logic.js
// ==========================================

const onboardingPanel = document.getElementById('onboarding-panel');
const onboardingBtn = document.getElementById('onboarding-btn');

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
    if (onboardingBtn) {
        onboardingBtn.hidden = true;
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

function enableUIElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.disabled = false;
        element.style.opacity = '1';
        element.style.filter = 'none';
    }
}

function disableUIElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.disabled = true;
        element.style.opacity = '0.5';
        element.style.filter = 'blur(2px)';
    }
}

function blurMainArea(blur = true) {
    if (blur) {
        if (mainDiv) {
            mainDiv.style.opacity = '0.5';
            mainDiv.style.filter = 'blur(2px)';
            mainDiv.style.pointerEvents = 'none';
        }
        if (inputDiv) {
            inputDiv.style.opacity = '0.5';
            inputDiv.style.filter = 'blur(2px)';
            inputDiv.style.pointerEvents = 'none';
        }
    } else {
        if (mainDiv) {
            mainDiv.style.opacity = '1';
            mainDiv.style.filter = 'none';
            mainDiv.style.pointerEvents = 'auto';
        }
        if (inputDiv) {
            inputDiv.style.opacity = '1';
            inputDiv.style.filter = 'none';
            inputDiv.style.pointerEvents = 'auto';
        }
    }
}

// ==========================================
// ==========================================

function onProfileCompleted() {
    completeStage('onboarding-stage-profile', 'profile-status', 'onboarding-stage-help');
    enableUIElement('help-btn');
    debugLog('Profile stage completed, help button enabled');
}

function onHelpCompleted() {
    completeStage('onboarding-stage-help', 'help-status', 'onboarding-stage-first-question');
    blurMainArea(false);
    debugLog('Help stage completed, main area enabled');
}

function onFirstResponseCompleted() {
    completeStage('onboarding-stage-first-question', 'first-response-status', 'onboarding-stage-feedback');
    debugLog('First response stage completed');
}

function onFeedbackCompleted() {
    completeStage('onboarding-stage-feedback', null, 'onboarding-stage-completed');
    debugLog('Feedback stage completed, onboarding finished');
}

function finalizeOnboarding() {
    const onboardingCloseBtn = document.getElementById('onboarding-close-btn');
    if (onboardingCloseBtn) {
        onboardingCloseBtn.classList.remove('onboarding-inactive');
    }
    enableUIElement('config-btn');
    setOnboarded();
}

function handleOnboardingCloseBtn() {
    debugLog('Closing onboarding panel');
    // Shortcut: complete all stages of the onboarding flow
    onProfileCompleted();
    onHelpCompleted();
    onFirstResponseCompleted();
    onFeedbackCompleted();
    finalizeOnboarding();
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
    if (isOnboarded()) {
        if (onboardingBtn) {
            onboardingBtn.hidden = true;
        }
        debugLog('User already onboarded, skipping onboarding flow');
        return
    }

    debugLog('Initializing onboarding flow for new user');

    if (onboardingBtn) {
        onboardingBtn.addEventListener('click', showOnboardingPanel);
    }

    document.getElementById('onboarding-panel').innerHTML = onboardingHTML;

    const onboardingCloseBtn = document.getElementById('onboarding-close-btn');
    if (onboardingCloseBtn) {
        onboardingCloseBtn.addEventListener('click', handleOnboardingCloseBtn);
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

    disableUIElement('help-btn');
    disableUIElement('config-btn');
    blurMainArea(true);

    showOnboardingPanel();
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
