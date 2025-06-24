// ==========================================
// onboarding.js
// ==========================================

const onboardingPanel = document.getElementById('onboarding-panel');

onboardingPanel.innerHTML = `
<div id="onboarding-header">
    <button id="onboarding-close-btn">✖️</button>
    <h2>Guide de démarrage</h2>
</div>
<div id="onboarding-content">
    <h3>Bienvenue dans l'assistant documentaire Cirdi !</h3>
    <p>Merci de participer à l'évaluation de l'assistant documentaire Cirdi. Nous sommes en phase de test beta sur invitation.</p>
    <p>Puis-je vous inviter à:</p>
    <ol>
        <li>Remplir votre profil utilisateur.
        <button type="button" id="open-profile-panel" class="primary-button">Compléter mon profil</button>
        </li>
        <li>Consulter le guide de démarrage rapide.
        <button type="button" id="open-quick-start-guide" class="primary-button">Ouvrir le guide</button>
        </li>
        <li>Poser votre première question à Cirdi.
        <button type="button" id="open-first-question-guide" class="primary-button">Poser une question</button>
        </li>
        <li>Partager vos retours d'expérience.
        <button type="button" id="open-feedback-form" class="primary-button">Donner mon avis</button>
        </li>
    </ol>
    <p>Votre contribution est précieuse pour améliorer l'assistant.</p>
    Merci de votre aide, Minh !
</div>
`

const onboardingBtn = document.getElementById('onboarding-btn');
const onboardingCloseBtn = document.getElementById('onboarding-close-btn');

// ==========================================
// ==========================================

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
// Event Listeners
// ==========================================

// When the user clicks the "Fill profile" button, we open the profile panel.
// When the user clicks the "Ouvrir le guide" button, we show a Panel with the quick start guide content.
//

// ==========================================
// Onboarding stages
// ==========================================

// Initially, the div "input" is inactive and shown greyed out.
// Initially, the Settings button is inactive and shown greyed out.
// Stages 2-4 are also greyed out

// Stage 1: Welcome and Profile Setup
// When the user has saved their profile, we replace the open-profile-panel button
// with a thank you message indicating that the profile is complete
// it can be modified or deleted with the Profile button in the top right corner. Show an image of the button.

// Stage 2: Quick Start Guide
// The button "open-quick-start-guide" looks the same as the Aide button in the top right corner.
// At this stage, the help panel only displays only basic instructions on how to use the assistant.
// The stage completes upon opening the guide.
// The button is replaced with a thank you message indicating that the button will remain in the top right corner.

// Stage 3: First Question Guide
// The stage completes when the user receives its first answer.
// Upon completion, the Aide button will show additional tips on limits

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

    if (onboardingPanel) {
        onboardingPanel.addEventListener('click', (event) => {
            if (event.target === onboardingPanel) {
                hideOnboardingPanel();
            }
        });
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
