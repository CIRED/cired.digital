// help-logic.js

const helpPanel = document.getElementById('help-panel');
const helpBtn = document.getElementById('help-btn');
const helpCloseBtn = document.getElementById('help-close-btn');


function showHelpPanel() {
    if (helpPanel && helpBtn) {
        helpPanel.hidden = false;
        helpBtn.hidden = true;
    }
}

function hideHelpPanel() {
    if (helpPanel && helpBtn) {
        helpPanel.hidden = true;
        helpBtn.hidden = false;

        if (typeof onHelpCompleted === 'function' && !isOnboarded()) {
            onHelpCompleted();
        }
    }
}

function initializeHelp() {
    if (!helpPanel || !helpCloseBtn || !helpBtn) {
        console.error('Help panel elements not found');
        return;
    }

    helpCloseBtn.addEventListener('click', () => hideHelpPanel());

    helpBtn.addEventListener('click', () => showHelpPanel());
}


if (document.readyState === 'loading') {
     document.addEventListener('DOMContentLoaded', () => {
         initializeHelp();
     });
} else {
    initializeHelp();
}
