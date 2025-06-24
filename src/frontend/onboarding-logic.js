// ==========================================
// onboarding-logic.js
// ==========================================

const onboardingPanel = document.getElementById('onboarding-panel');
const onboardingBtn = document.getElementById('onboarding-btn');
const onboardingCloseBtn = document.getElementById('onboarding-close-btn');

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

function handlePanelKeydown(event) {
    if (event.key === 'Escape') {
        hideOnboardingPanel();
        hideProfilePanel();
    }

    if (event.key === 'Tab') {
        const Panel = event.target.closest('.Panel-overlay, #profile-panel');
        if (Panel) {
            const focusableElements = Panel.querySelectorAll(
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
    const main = document.getElementById('messages-container');
    const inputContainer = document.getElementById('input-container');

    if (blur) {
        if (main) {
            main.style.opacity = '0.5';
            main.style.filter = 'blur(2px)';
            main.style.pointerEvents = 'none';
        }
        if (inputContainer) {
            inputContainer.style.opacity = '0.5';
            inputContainer.style.filter = 'blur(2px)';
            inputContainer.style.pointerEvents = 'none';
        }
    } else {
        if (main) {
            main.style.opacity = '1';
            main.style.filter = 'none';
            main.style.pointerEvents = 'auto';
        }
        if (inputContainer) {
            inputContainer.style.opacity = '1';
            inputContainer.style.filter = 'none';
            inputContainer.style.pointerEvents = 'auto';
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
    enableUIElement('config-btn');
    setOnboarded();
    debugLog('Feedback stage completed, onboarding finished');
}


function initializeOnBoarding() {
    if (onboardingBtn) {
        onboardingBtn.addEventListener('click', showOnboardingPanel);
    }

    if (onboardingCloseBtn) {
        onboardingCloseBtn.addEventListener('click', hideOnboardingPanel);
    }

    document.addEventListener('keydown', handlePanelKeydown);

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

    if (onboardingPanel) {
        onboardingPanel.addEventListener('click', (event) => {
            if (event.target === onboardingPanel) {
                hideOnboardingPanel();
            }
        });
    }

    if (isOnboarded()) {
        if (onboardingBtn) {
            onboardingBtn.hidden = true;
        }
        enableUIElement('config-btn');
        debugLog('User already onboarded, skipping onboarding flow');
    } else {
        showOnboardingPanel();
        setupInitialOnboardingState();
        debugLog('Starting onboarding flow for new user');
    }
}

function setupInitialOnboardingState() {
    disableUIElement('help-btn');
    disableUIElement('config-btn');
    blurMainArea(true);

    const configBtn = document.getElementById('config-btn');
    if (configBtn) {
        configBtn.style.display = 'none';
    }
}

// ==========================================
// Relancer le guide de démarrage rapide
// ==========================================

function restartOnboarding() {
    // Réinitialise l'état d'onboarding et relance le panneau d'onboarding
    localStorage.removeItem(PROFILE_ONBOARDED_KEY);
    if (typeof setupInitialOnboardingState === 'function') {
        setupInitialOnboardingState();
    }
    if (typeof showOnboardingPanel === 'function') {
        showOnboardingPanel();
    }
    debugLog('Onboarding reset and relaunched');
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
