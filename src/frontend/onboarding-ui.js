const ONBOARDING_STAGES = ['question', 'feedback', 'help', 'profile'];

const onboardingHTML = `
<div id="onboarding-header">
    <h2>Guide de démarrage rapide</h2>
    <button id="onboarding-close-btn" class="close-button">✖️</button>
</div>
<div id="onboarding-content">
    <h3>Prise en main en 4 étapes:</h3>
    <ol>
        <li id="onboarding-stage-question">
            Posez une première question à Cirdi. Le champ de saisie est en haut au centre,
            le bouton bleu <button id="image-send-btn">➤</button> lance la requête.
            <button id="focus-input">Aller au champ de saisie</button>.
            <br />
            Première réponse: <span id="question-status">En attente.</span>
        </li>
        <li id="onboarding-stage-feedback">
            Partagez votre retour d'expérience sur le formulaire qui s'affichera sous la réponse, avec
            quelques mots et un choix entre <button class="feedback-button feedback-up" title="Bonne réponse.">👍</button>
            et <button class="feedback-button feedback-down" title="Réponse insuffisante.">👎</button> pour envoyer.
            <br />
            Retour d'expérience envoyé: <span id="feedback-status">En attente.</span>
        </li>
        <li id="onboarding-stage-help">
            Ouvrez le mode d'emploi. Le bouton
            <button type="button" id="open-help-btn" class="primary-button">Aide</button>
            est juste à côté du bouton de profil. Utilisez les boutons <button id="help-close-btn">✖️</button> pour refermer.
            <br />
            Mode d'emploi vu, refermé: <span id="help-status">En attente.</span>
        </li>
        <li id="onboarding-stage-profile">
            Complétez votre profil utilisateur en cliquant sur
            <button id="open-profile-btn">👤</button> dans le coin en haut à droite.
            <br />
            Profil: <span id="profile-status">En attente.</span>
        </li>
    </ol>
    <p id="onboarding-completed" class="onboarding-incomplete">
            🎉👏 Bravo, vous avez complété le parcours de prise en main !
            Ce panneau ne sera plus ouvert automatiquement lorsque vous reviendrez.
            Vous pourrez y réaccéder via le panneau de profil utilisateur.
            <br />
            Un bouton "Settings" <button id="show-config-btn">⚙️</button> pour utilisateurs avancés sera disponible en haut à gauche après la fermeture de ce guide de démarrage rapide.
    </p>
</div>
<div id="onboarding-footer">
    <button id="onboarding-pass-btn" class="primary-button">Fermer et passer.</button>
    <button id="onboarding-reset-btn" class="secondary-button">Réinitialiser le guide</button>
</div>
`;

function showCompleted(stageKey) {
    const stageLi = document.getElementById(`onboarding-stage-${stageKey}`);
    if(stageLi) {stageLi.className = 'onboarding-stage-complete'};

    const stageStatus = document.getElementById(`${stageKey}-status`);
    if(stageStatus) {stageStatus.textContent = '✅ Terminé'};
}

function showOnboardingCompleted() {
    const congratulations = document.getElementById("onboarding-completed");
    if (congratulations) {
        congratulations.classList.remove('onboarding-incomplete');
        congratulations.className = 'onboarding-complete';
    }
}
