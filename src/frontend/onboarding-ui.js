document.getElementById('onboarding-panel').innerHTML = `
<div id="onboarding-header">
    <h2>Guide de démarrage rapide</h2>
</div>
<div id="onboarding-content">
    <h3>Bienvenue dans l'assistant documentaire Cirdi !</h3>
    <p>Le parcours de prise en main comprend quatre étapes:</p>
    <ol>
        <li id="onboarding-stage-profile" class="onboarding-focus">
            Complétez votre profil utilisateur en cliquant sur
            <button id="open-profile-btn">👤</button> dans le coin en haut à droite.
            <br />
            Profil complété: <span id="profile-status">En attente.</span>
        </li>
        <li id="onboarding-stage-help" class="onboarding-inactive">
            Ouvrez le mode d'emploi. Le bouton
            <button type="button" id="open-help-btn" class="primary-button">Aide</button>
            est juste à côté du bouton de profil. Utilisez les boutons <button id="help-close-btn">✖️</button> pour refermer.
            <br />
            Mode d'emploi vu, refermé: <span id="help-status">En attente.</span>
        </li>
        <li id="onboarding-stage-first-question" class="onboarding-inactive">
            Posez une première question à Cirdi. Le champ de saisie est en haut au centre,
            le bouton bleu <button id="image-send-btn">➤</button> lance la requête.
            <button id="focus-input">Aller au champ de saisie</button>.
            <br />
            Première réponse: <span id="first-response-status">En attente.</span>
        </li>
        <li id="onboarding-stage-feedback" class="onboarding-inactive">
            Partagez votre retour d'expérience sur le formulaire qui s'affichera sous la réponse, avec
            quelques mots et un choix entre <button class="feedback-button feedback-up" title="Bonne réponse.">👍</button>
            et <button class="feedback-button feedback-down" title="Réponse insuffisante.">👎</button> pour envoyer.
        </li>
        <li id="onboarding-stage-completed" class="onboarding-inactive">
            🎉👏 Bravo, vous avez complété le parcours de prise en main !
            Ce panneau ne sera plus ouvert automatiquement lorsque vous reviendrez.
            Vous pourrez y réaccéder via le panneau de profil utilisateur.
            <br />
            Un bouton "Settings" <button id="show-config-btn">⚙️</button> pour utilisateurs avancés sera disponible en haut à gauche après la fermeture de ce guide de démarrage rapide.
        </li>
    </ol>
</div>
<div id="onboarding-footer">
    <button id="onboarding-close-btn" class="onboarding-inactive">Fermer le guide.</button>
</div>
`;
