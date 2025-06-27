// profile-ui.js


document.getElementById("profile-panel").innerHTML = `
  <div id="profile-header">
    <h2>Renseigner mon Profil</h2>
    <button id="profile-close-btn">✖️</button>
  </div>

  <div class="settings-grid" id="profile-container">
    <div class="profile-introduction">
      <p>Je vous invite à ce questionnaire rapide: trois questions sur votre affiliation professionnelle, votre niveau d'expertise en environnement / développement, et votre familiarité avec les technologies d'intelligence artificielle.</p>

      <p>Vos réponses nous permettront d'adapter les contenus et fonctionnalités à votre niveau d'expertise et à vos besoins spécifiques. Ces données sont anonymes, ne sont pas redistribuées, et vous pouvez les modifier ou supprimer à tout moment ci-dessous.</p>

      <p><em>Temps estimé : moins de 1 minute.</em></p>

      <p id="questionnaire-signature">minh.ha-duong@cnrs.fr</p>
    </div>

    <form id="profile-edit-form" class="settings-grid">

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
        <label class="form-label" for="edit-profile-knowledge">Connaissance des questions d'environnement et/ou de développement</label>
        <div id="edit-profile-knowledge" style="display: flex; flex-direction: column; gap: 0.25em;">
          <label><input type="radio" name="profile-knowledge" value="expert"> Expert: des années de pratique ou de recherche dans le domaine</label>
          <label><input type="radio" name="profile-knowledge" value="engaged"> Engagé: journaliste, étudiant, militant...</label>
          <label><input type="radio" name="profile-knowledge" value="initial"> Initiale: souhaite en savoir plus sur le sujet</label>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label" for="edit-profile-usage">Niveau de familiarité avec les technologies IA</label>
        <div id="edit-profile-usage" style="display: flex; flex-direction: column; gap: 0.25em;">
          <label><input type="radio" name="profile-usage" value="expert"> Professionnel - Je trouve que Cirdi est un RAG simple.</label>
          <label><input type="radio" name="profile-usage" value="advanced"> Avancé - J'utilise au quotidien divers outils d'IA.</label>
          <label><input type="radio" name="profile-usage" value="intermediate"> Intermédiaire - J'ai une pratique répétée.</label>
          <label><input type="radio" name="profile-usage" value="beginner"> Débutant - J'ai peu ou pas utilisé de chatbot.</label>
        </div>
      </div>

      </form>

    <div id="profile-actions">
      <button type="button" id="save-profile-btn" class="primary-button">Enregistrer et Fermer</button>
    </div>

    <div id="stored-profile">
    <h3>Données stockées actuellement</h3>
      <div id="profile-data-display">Loading...</div>
      <button type="button" id="clear-profile-btn" class="secondary-button">Effacer les données</button>
    </div>

    <div id="profile-footer">
      <button type="button" id="onboarding-btn">Ouvrir le guide de démarrage rapide</button>
    </div>
  </div>
`;


/**
 * Updates the profile panel UI with the user's profile data from localStorage.
 *
 * - Displays profile information in the element with ID 'profile-data-display'.
 * - Updates the label of the save-profile button depending on whether a profile ID exists.
 * - Synchronizes the profile edit form fields with the stored profile data, or clears them if no profile is found.
 * - Handles errors gracefully and displays an error message if profile data cannot be read.
 *
 * Relies on the constants PROFILE_STORAGE_KEY and PROFILE_ONBOARDED_KEY being defined in the scope.
 */
function updateProfilePanel() {

    const display = document.getElementById('profile-data-display');
    if (!display) return;
    try {
        const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
        const onboarded = localStorage.getItem(PROFILE_ONBOARDED_KEY);
        let profile = null;
        if (stored) {
            profile = JSON.parse(stored);
            display.innerHTML = `
                <ul>
                    <li><b>Profile ID:</b> ${profile.id || ''}</li>
                    <li><b>Affiliation:</b> ${profile.organization || ''}</li>
                    <li><b>Expertise:</b> ${profile.knowledge || ''}</li>
                    <li><b>Familliarité IA:</b> ${profile.usage || ''}</li>
                    <li><b>Créé le:</b> ${profile.createdAt ? new Date(profile.createdAt).toLocaleString() : ''}</li>
                    <li><b>Modifié le:</b> ${profile.updatedAt ? new Date(profile.updatedAt).toLocaleString() : ''}</li>
                    <li><b>${PROFILE_ONBOARDED_KEY}:</b> ${onboarded !== null ? onboarded : ''}</li>
                </ul>
            `;
        } else {
            display.textContent = 'Aucune donnée de profil enregistrée.';
        }

        // Update save-profile button label depending on presence of ID
        const saveBtn = document.getElementById('save-profile');
        if (saveBtn) {
            saveBtn.textContent = profile && profile.id ? 'Mettre à jour' : 'Sauvegarder';
        }

        // Synchronize form fields with profile data or clear them if no profile
        const editForm = document.getElementById('profile-edit-form');
        if (editForm) {
            // Organization
            const orgInputs = editForm.querySelectorAll('input[name="profile-organization"]');
            orgInputs.forEach(input => {
                input.checked = profile && profile.organization === input.value;
            });
            // Expertise
            const expertiseInputs = editForm.querySelectorAll('input[name="profile-knowledge"]');
            expertiseInputs.forEach(input => {
                input.checked = profile && profile.knowledge === input.value;
            });
            // Familiarity
            const familiarityInputs = editForm.querySelectorAll('input[name="profile-usage"]');
            familiarityInputs.forEach(input => {
                input.checked = profile && profile.usage === input.value;
            });
        }
    } catch (e) {
        display.textContent = 'Erreur de lecture du profil.';
    }
}
