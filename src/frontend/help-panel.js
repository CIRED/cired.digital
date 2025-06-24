document.getElementById("mode-emploi-panel").innerHTML = `
  <div id="mode-emploi-header">
    <h2>Mode d'emploi - assistant documentaire Cirdi</h2>
    <button id="mode-emploi-close-btn">✖️</button>
  </div>

  <div id="mode-emploi-content">

  <p>
    Bienvenue dans l’interface de dialogue avec l’assistant Cirdi. Cet outil a été conçu pour vous aider à retrouver rapidement des informations issues des publications de notre centre de recherche.
  </p>

<section>
  <h3>Comment l’utiliser ?</h3>
  <ol>
    <li>
      <strong>Posez une question claire</strong><br>
      Par exemple :<br>
      <em>« Quels sont les effets du prix du carbone sur le secteur électrique ? »</em>
    </li>
    <li>
      <strong>Laissez l’assistant réfléchir</strong><br>
      L’assistant cherche dans les publications du CIRED les éléments de réponse pertinents.
    </li>
    <li>
      <strong>Consultez la réponse</strong><br>
      Le texte affiché est une synthèse rédigée automatiquement à partir de documents existants.<br>
      Les petits numéros entre crochets [1], [2], etc. renvoient aux sources utilisées.
    </li>
    <li>
      <strong>Vérifiez les sources</strong><br>
      En bas de la réponse, vous trouverez la bibliographie. Vous pouvez cliquer sur les références pour lire les publications complètes.
    </li>
    <li>
      <strong>Donnez votre sentiment sur la réponse</strong><br>
      Vos retours sont indispensables pour améliorer l’assistant. Merci d'avance pour votre aide !
    </li>
  </ol>

  <h3>Points importants</h3>
  <ul>
    <li>Cirdi <strong>ne donne pas son avis</strong> : il résume les publications du CIRED disponibles dans HAL.</li>
    <li>Il peut parfois <strong>se tromper</strong> : toujours vérifier les sources citées.</li>
    <li>Vos questions et les réponses sont <strong>enregistrées anonymement</strong>, afin d’améliorer l’outil.</li>
  </ul>
</section>

<section>
  <h3>Limites du corpus de documents</h3>
  <ul>
    <li>
      Toutes les publications du CIRED ne sont pas disponibles en accès libre dans l’archive HAL.
      L’assistant ne consulte que ce dépôt, il ne cherche pas les textes ailleurs.
    </li>
    <li>
      De nombreuses publications plus anciennes du CIRED ne sont pas encore présentes dans HAL.
    </li>
    <li>
      Quelques documents ne sont pas intégrés pour des raisons techniques, par exemple lorsqu’ils sont trop volumineux (environ 1 % des cas).
    </li>
    <li>
      HAL archive les publications scientifiques, mais pas les documents de communication institutionnelle.
      Pour connaître les recherches en cours ou les événements à venir :
      <ul>
        <li>Consultez le site web du CIRED : <a href="https://www.centre-cired.fr" target="_blank">www.centre-cired.fr</a></li>
        <li>Inscrivez-vous à la lettre d'information : <a href="https://tinyurl.com/z4sr8p6z" target="_blank">lien d’abonnement</a></li>
      </ul>
    </li>
  </ul>
</section>

<section>
  <h3>Limites du système</h3>
  <ul>
    <li>
      L’assistant peut parfois inventer des informations ou mal attribuer une citation. Il est donc important de vérifier les sources proposées.
    </li>
    <li>
      Il ne retient pas les échanges précédents : chaque question est traitée de manière indépendante.
    </li>
    <li>
      Il ne peut pas planifier une démarche complexe en plusieurs étapes ou utiliser d’autres outils en ligne pour répondre.
      Si vous avez besoin d'une analyse approfondie, procédez pas à pas. Demandez d'abord une synthèse ou un plan détaillé, puis posez des questions complémentaires.
    </li>
    <li>
      Il ne couvre pas toute la littérature scientifique mondiale.
      Pour une revue approfondie de la littérature, vous pouvez explorer d'autres outils :
      <a href="https://www.google.com/search?q=Tools+conduct+scientific+literature+review" target="_blank">Suggestions d’outils</a>.
    </li>
    <li>
      Le système n’enregistre pas les réponses : pensez à copier et sauvegarder ce qui vous intéresse avant de quitter la session.
    </li>
    <li>
      La base HAL est consultée ponctuellement, elle n’est pas mise à jour automatiquement de façon régulière.
    </li>
  </ul>
</section>

<section>
  <h3>Contact</h3>
  <p>
    Pour toute question ou suggestion, n’hésitez pas à nous contacter :
    <a href="mailto:minh.ha-duong@cnrs.fr">minh.ha-duong@cnrs.fr</a>
  </p>
</section>

</div>
`;

function initializeHelp() {
    const modeEmploiPanel = document.getElementById('mode-emploi-panel');
    const modeEmploiCloseBtn = document.getElementById('mode-emploi-close-btn');
    const helpBtn = document.getElementById('help-btn');

    if (!modeEmploiPanel || !modeEmploiCloseBtn || !helpBtn) {
        console.error('Mode d\'emploi modal elements not found');
        return;
    }

    modeEmploiCloseBtn.addEventListener('click', () => {
        modeEmploiPanel.hidden = true;
        helpBtn.hidden = false;
    });

    helpBtn.addEventListener('click', () => {
        modeEmploiPanel.hidden = false;
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
