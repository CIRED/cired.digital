document.getElementById("profile-panel").innerHTML = `
  <div id="profile-header">
    <h2>Mon Profil</h2>
    <button id="profile-close-btn">✖️</button>
  </div>

  <div class="settings-grid" id="profile-container">
    <div class="profile-info">
      <p>Profil spécifique à cet ordinateur</p>
    </div>

    <form id="profile-edit-form" class="settings-grid">
      <div class="form-group">
        <label class="form-label" for="edit-profile-name">Pseudonyme</label>
        <input type="text" id="edit-profile-name" class="form-input">
      </div>

      <div class="form-group">
        <label class="form-label" for="edit-profile-role">Rôle</label>
        <select id="edit-profile-role" class="form-select">
          <option value="">Sélectionnez votre rôle</option>
          <option value="researcher">Chercheur/Chercheuse</option>
          <option value="student">Étudiant(e)</option>
          <option value="policy-maker">Décideur politique</option>
          <option value="consultant">Consultant(e)</option>
          <option value="journalist">Journaliste</option>
          <option value="citizen">Citoyen(ne)</option>
          <option value="other">Autre</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label" for="edit-profile-usage">Contexte d'utilisation</label>
        <select id="edit-profile-usage" class="form-select">
          <option value="">Sélectionnez le contexte</option>
          <option value="research">Recherche académique</option>
          <option value="education">Enseignement/Formation</option>
          <option value="policy">Élaboration de politiques</option>
          <option value="business">Conseil/Business</option>
          <option value="personal">Intérêt personnel</option>
          <option value="journalism">Journalisme</option>
          <option value="other">Autre</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label" for="edit-profile-organization">Type d'organisation</label>
        <select id="edit-profile-organization" class="form-select">
          <option value="">Sélectionnez le type</option>
          <option value="university">Université/École</option>
          <option value="research-institute">Institut de recherche</option>
          <option value="government">Administration publique</option>
          <option value="ngo">ONG/Association</option>
          <option value="private-company">Entreprise privée</option>
          <option value="consulting">Cabinet de conseil</option>
          <option value="media">Média</option>
          <option value="individual">Particulier</option>
          <option value="other">Autre</option>
        </select>
      </div>
    </form>

    <div class="profile-actions">
      <button type="button" id="save-profile" class="primary-button">Sauvegarder</button>
      <button type="button" id="clear-profile" class="secondary-button">Effacer le profil</button>
    </div>
  </div>
`;
