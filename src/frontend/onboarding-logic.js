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
        onboardingBtn.hidden = true; // Onboarding shown only once, hide the button
    }}

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
// Event Listeners
// ==========================================


// ==========================================
// Onboarding stages
// ==========================================

// Initially, the div "input" is inactive and shown greyed out.
// Initially, the Settings button is hidden.

// Stage 1: Setup Profile
// When the user has saved their profile,
// - In stage 1, the "En attente" text is replaced with "[Checkmark emoji] Complete"
// - Stage 1 style becomes complete
// - Stage 2 style becomes focused

// Stage 2: Find the help panel
// When the user closes the help panel,
// - The "En attente" text is replaced with "[Checkmark emoji] Complete"
// - Stage 2 style becomes complete
// - Stage 3 style becomes focused

// Stage 3: First Question Guide
// Cliquer sur le button bleu dans le message le fait flasher.
// Ajouter un bouton "Aller à la question" dans le message qui met le focus dans le champ de saisie.
// When the user receives the answer to the first question,
// - The "En attente" text is replaced with "[Checkmark emoji] Complete"
// - Stage 3 style becomes complete
// - Stage 4 style becomes focused

// Stage 4: Completed Feedback Form
// Stage completes when the user submits the feedback form.
// This unlocks the "Settings" button in the top right corner.

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

    const firstQuestionGuideBtn = document.getElementById('open-first-question-guide');
    const feedbackFormBtn = document.getElementById('open-feedback-form');

    if (firstQuestionGuideBtn) {
        firstQuestionGuideBtn.addEventListener('click', showFirstQuestionGuide);
    }

    if (feedbackFormBtn) {
        feedbackFormBtn.addEventListener('click', showFeedbackForm);
    }

    if (onboardingPanel) {
        onboardingPanel.addEventListener('click', (event) => {
            if (event.target === onboardingPanel) {
                hideOnboardingPanel();
            }
        });
    }

    // TODO: Add a check if the user is already onboarded
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
