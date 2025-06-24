// profile-ui.js


document.getElementById("profile-panel").innerHTML = `
  <div id="profile-header">
    <h2>Mon Profil</h2>
    <button id="profile-close-btn">✖️</button>
  </div>

  <div class="settings-grid" id="profile-container">
    <form id="profile-edit-form" class="settings-grid">
      <div class="form-group">
        <label class="form-label" for="edit-profile-name">Pseudonyme</label>
        <input type="text" id="edit-profile-name" class="form-input">
      </div>

      <div class="form-group">
        <label class="form-label" for="edit-profile-organization">Affiliation professionnelle</label>
        <div id="edit-profile-organization" style="display: flex; flex-direction: column; gap: 0.25em;">
          <label><input type="radio" name="profile-organization" value="CIRED"> CIRED</label>
          <label><input type="radio" name="profile-organization" value="university"> Enseignement et recherche</label>
          <label><input type="radio" name="profile-organization" value="media"> Media</label>
          <label><input type="radio" name="profile-organization" value="nonprofit"> ONG/Association</label>
          <label><input type="radio" name="profile-organization" value="public"> Secteur public</label>
          <label><input type="radio" name="profile-organization" value="private"> Secteur privé</label>
          <label><input type="radio" name="profile-organization" value="other"> Autre</label>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label" for="edit-profile-role">Connaissance des questions d'environnement et/ou de développement</label>
        <div id="edit-profile-role" style="display: flex; flex-direction: column; gap: 0.25em;">
          <label><input type="radio" name="profile-role" value="researcher"> Expert: des années de pratique ou de recherche dans le domaine</label>
          <label><input type="radio" name="profile-role" value="consultant"> Engagé: journaliste, étudiant, militant...</label>
          <label><input type="radio" name="profile-role" value="student"> Initiale: souhaite en savoir plus sur le sujet</label>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label" for="edit-profile-usage">Niveau de familiarité avec les technologies IA</label>
        <div id="edit-profile-usage" style="display: flex; flex-direction: column; gap: 0.25em;">
          <label><input type="radio" name="profile-usage" value="research"> Avancé - Utilisation au quotidien</label>
          <label><input type="radio" name="profile-usage" value="education"> Intermédiaire - Pratique répétée</label>
          <label><input type="radio" name="profile-usage" value="policy"> Débutant - Peu ou pas utilisé</label>
        </div>
      </div>

      </form>

    <div id="profile-actions">
      <button type="button" id="save-profile" class="primary-button">Sauvegarder et fermer</button>
    </div>


    <div id="stored-profile">
    <h3>Données stockées actuellement</h3>
      <div id="profile-data-display">Loading...</div>
    </div>

    <div id="profile-footer">
      <p>Votre profil nous aide à mieux comprendre comment les utilisateurs interagissent avec l'assistant et à améliorer ses réponses.
      Il est stocké localement dans votre navigateur et n'est pas partagé avec des tiers. Vous pouvez le modifier ou le supprimer à tout moment:
      <button type="button" id="clear-profile" class="secondary-button">Effacer les données</button></p>
      <p><button type="button" id="restart-onboarding">Relancer le guide de démarrage rapide</button></p>
    </div>
  </div>
`;
