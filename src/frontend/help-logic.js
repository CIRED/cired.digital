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
    debugLog('Initializing help panel');

    attach('help-btn', 'click', showHelpPanel)
    attach('help-close-btn', 'click', hideHelpPanel);
}
