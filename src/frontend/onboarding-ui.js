document.getElementById('onboarding-panel').innerHTML = `
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
