// help-logic.js

function showHelpPanel() {
    const helpPanel = document.getElementById('help-panel');
    if (helpPanel) {
        helpPanel.hidden = false;
    }
}

function hideHelpPanel() {
    const helpPanel = document.getElementById('help-panel');
    if (helpPanel) {
        helpPanel.hidden = true;
    }
}

function initializeHelp() {
    const helpPanel = document.getElementById('help-panel');
    if (!helpPanel) {
        console.error('Help panel elements not found');
        return;
    }

    attach('help-btn', 'click', showHelpPanel)
    attach('help-close-btn', 'click', hideHelpPanel);
}
