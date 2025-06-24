// help-logic.js

function initializeHelp() {
    const helpPanel = document.getElementById('help-panel');
    const helpCloseBtn = document.getElementById('help-close-btn');
    const helpBtn = document.getElementById('help-btn');

    if (!helpPanel || !helpCloseBtn || !helpBtn) {
        console.error('Mode d\'emploi modal elements not found');
        return;
    }

    helpCloseBtn.addEventListener('click', () => {
        helpPanel.hidden = true;
        helpBtn.hidden = false;
    });

    helpBtn.addEventListener('click', () => {
        helpPanel.hidden = false;
        helpBtn.hidden = true;
    });
}

if (document.readyState === 'loading') {
     document.addEventListener('DOMContentLoaded', () => {
         initializeHelp();
     });
} else {
    initializeHelp();
}
