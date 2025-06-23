document.getElementById("mode-emploi-panel").innerHTML = `
  <div id="mode-emploi-header">
    <h2>Mode d'emploi</h2>
    <button id="mode-emploi-close-btn">✖️</button>
  </div>
  <div id="mode-emploi-content">
    <section>
      <h3>Comment utiliser (comme un moteur de recherche : tapez dans la boîte puis Entrée)</h3>

      <h4>Exemples de questions :</h4>
      <ul>
        <li><strong>"Quelle est la production alimentaire agricole par habitant en Andhra Prades actuellement ?"</strong> illustre la récupération précise de faits avec orthographe approximative (Pradesh manque le h final). Utile pour l'écriture et la recherche, avec une probabilité plus faible.</li>
        <li><strong>"Le CCS"</strong></li>
        <li>Une question en portugais pour illustrer les capacités multilingues.</li>
        <li><strong>"Pourquoi l'échec de Kyoto?"</strong> illustre la conscience du contexte et la spécificité du point de vue CIRED.</li>
        <li><strong>"Comment préparer ma présentation?"</strong> il y a quelques manuels de méthodes de recherche dans HAL</li>
        <li><strong>"Traduit: « De los diversos instrumentos inventados por el hombre, el más asombroso es el libro; todos los demás son extensiones de su cuerpo. Sólo el libro es una extensión de la imaginación y la memoria. » (Borges, 1978)"</strong> c'est un LLM</li>
        <li><strong>"Who is Ignacy Sachs?"</strong> Vous pouvez obtenir la courte biographie des auteurs.</li>
      </ul>
    </section>

    <section>
      <h3>Comment ça marche</h3>
      <p>Une explication de style bande dessinée, avec Cirdi personnalisé comme assistant :</p>

      <div class="comic-explanation">
        <div class="comic-step">
          <strong>📚 Intake :</strong> lire le corpus, diviser en segments de taille paragraphe et indexer les segments. Cirdi organisant les archives avant d'ouvrir boutique.
        </div>

        <div class="comic-step">
          <strong>🤔 Cirdi recevant une demande d'un visiteur.</strong>
        </div>

        <div class="comic-step">
          <strong>🔍 Retrieve :</strong> trouver les segments les plus pertinents pour la question. Cirdi dans les archives, trouvant des papiers dans des boîtes.
        </div>

        <div class="comic-step">
          <strong>✍️ Generate :</strong> Demander à un LLM de répondre à la question avec les segments pertinents. Cirdi donnant la pile de papiers à un écrivain. Cirdi récupérant la réponse.
        </div>

        <div class="comic-step">
          <strong>📝 Reformat :</strong> présenter comme un texte académique. Cirdi à son bureau, réécrivant la réponse. Cirdi la retournant à l'utilisateur.
        </div>
      </div>
    </section>

    <section>
      <h3>Limites du corpus</h3>
      <ul>
        <li>De nombreuses publications CIRED ne sont pas archivées en accès libre dans HAL (et Cirdi n'a pas cherché ailleurs pour le texte intégral).</li>
        <li>La plupart des anciennes publications CiRED ne sont pas dans Hal (encore ?)</li>
        <li>Quelques publications ne sont pas ingérées pour des raisons techniques (environ 1% de fichiers surdimensionnés)</li>
        <li>Hal archive la production scientifique, pas la communication institutionnelle (par exemple, utilisez le site web CIRED → <a href="https://www.centre-cired.fr" target="_blank">https://www.centre-cired.fr</a> pour connaître la recherche en cours, abonnez-vous à la newsletter pour connaître les événements actuels → <a href="https://tinyurl.com/z4sr8p6z" target="_blank">https://tinyurl.com/z4sr8p6z</a>).</li>
      </ul>
    </section>

    <section>
      <h3>Limites du système</h3>
      <ul>
        <li>Le LLM peut encore halluciner (Attention aux déclarations attribuées à des sources non trouvées.)</li>
        <li>Pas conversationnel (Cirdi ne se souvient pas des questions précédentes)</li>
        <li>Pas agentique (Cirdi ne stratégisera pas un plan en plusieurs étapes qui utilise des outils en ligne pour répondre à la question)</li>
        <li>En particulier, Cirdi ne recherche pas dans toute la littérature scientifique ou autre chose (il existe de nombreux outils pour la revue générale de littérature → <a href="https://www.google.com/search?q=Tools+conduct+scientific+literature+review" target="_blank">https://www.google.com/search?q=Tools+conduct+scientific+literature+review</a>)</li>
        <li>Pas persistant (Coupez et collez la réponse ailleurs avant de fermer la session.)</li>
        <li>La récolte de HAL est à la demande, pas périodique.</li>
      </ul>
    </section>
  </div>
`
