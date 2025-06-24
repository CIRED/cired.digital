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
            Consultez le mode d'emploi. Vous trouverez le bouton
            <button type="button" id="open-help-btn" class="primary-button">Aide</button>
            juste à côté du bouton de profil.
            <br />
            Mode d'emploi vu, refermé: <span id="help-status">En attente.</span>
        </li>
        <li id="onboarding-stage-first-question" class="onboarding-inactive">
            Posez une première question à Cirdi. Le champ de saisie est en haut au centre,
            le bouton bleu <button id="image-send-btn">➤</button> lance la requête.
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
            Le bouton "Settings" <button id="show-config-btn">⚙️</button> sera désormais visible en haut à gauche.
            <br />
            <br />
            <button id="onboarding-close-btn">Fermer le guide de démarrage rapide</button>
        </li>
    </ol>
</div>
`
