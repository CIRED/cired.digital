const ONBOARDING_STAGES = ['question', 'feedback', 'help', 'profile'];

const onboardingHTML = `
<header>
    <h2>Guide de démarrage rapide</h2>
    <button id="onboarding-close-btn" class="ghost-button">✖️</button>
</header>

<main id="onboarding-content">
    <h3>Prise en main en 4 étapes:</h3>
    <ol>
        <li id="onboarding-stage-question">
            Posez une première question à Cirdi. Le champ de saisie est en haut au centre,
            le bouton <button class="ghost-button">➤</button> lance la requête.
            <button id="go-input-btn">Aller au champ de saisie</button>.
            <br />
            Première réponse: <span id="question-status">En attente.</span>
        </li>
        <li id="onboarding-stage-feedback">
            Partagez votre retour d'expérience sur le formulaire qui s'affichera sous la réponse, avec
            quelques mots et un choix entre <button class="ghost-button feedback-up" title="Bonne réponse.">👍</button>
            et <button class="ghost-button feedback-down" title="Réponse insuffisante.">👎</button> pour envoyer.
            <br />
            Retour d'expérience envoyé: <span id="cirdi-server-status">En attente.</span>
        </li>
        <li id="onboarding-stage-help">
            Ouvrez le mode d'emploi. Le bouton
            <button type="button" id="open-help-btn" class="secondary-button">Aide</button>
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
            Un bouton "Settings" <button id="show-settings-btn">⚙️</button> pour utilisateurs avancés sera disponible en haut à gauche après la fermeture de ce guide de démarrage rapide.
    </p>
</main>

<footer>
    <button id="onboarding-pass-btn" class="primary-button">Fermer et passer.</button>
    <button id="onboarding-reset-btn" class="secondary-button">Réinitialiser le guide</button>
</footer>
`;

function showAsCompleted(stageKey) {
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
