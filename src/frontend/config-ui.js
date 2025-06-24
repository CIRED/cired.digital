document.getElementById("config-panel").innerHTML = `
  <div id="config-header">
    <button id="config-close-btn">✖️</button>
    <h2>Cirdi settings</h2>
  </div>

  <div class="settings-grid" id="settings-container">

    <div class="form-group">
      <div class="label-with-status">
        <label class="form-label">
          Server URL
          <span class="help-icon" title="Where to find the R2R API endpoint. Try http://cired.digital:7272">ℹ️</span>
        </label>
        <div class="status-text" id="api-status">Status: OK</div>
      </div>
      <input class="form-input" id="api-url" type="text"/>
    </div>

    <div class="form-group">
      <label class="form-label">
      Language model
      <span class="help-icon" title="The LLM used to generate replies. Commercial options disabled for cost control.">ℹ️</span>
      </label>
      <select class="form-select" id="model">
        <option>Chargement...</option>
      </select>
      <div id="model-info">
        Tariff: input <span id="input-tariff">...</span>&nbsp;$, output <span id="output-tariff">...</span>&nbsp;$ per 1M tokens
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">
        Temperature (response creativity)
        <span class="help-icon" title="Automatically set to model provider's recommendations.">ℹ️</span>
      </label>
      <input type="number" id="temperature" class="form-input" step="0.05"/>
    </div>

    <div class="form-group">
      <label class="form-label">
        Max tokens (response length)
        <span class="help-icon" title="Automatically set according to the model.">ℹ️</span>
      </label>
      <input type="number" id="max-tokens" class="form-input" step="100"/>
    </div>

    <div class="form-group">
      <label class="form-label">
        Nombre maximum de segments à récupérer
        <span class="help-icon" title="Entre 1 et 1000.">ℹ️</span>
      </label>
      <input type="number" id="chunk-limit" class="form-input" step="1"/>
    </div>

    <div class="form-group">
      <label class="form-label">
        Méthode pour pêcher les segments
        <span class="help-icon" title="Options: vanilla (recherche directe rapide - pour question précise), rag_fusion (reformule - pour question ambigüe), HyDE (prêche le faux pour pêcher le vrai - pour question ouverte, conceptuelle)">ℹ️</span>
      </label>
      <select id="search-strategy" class="form-select">
        <option value="vanilla">Vanilla</option>
        <option value="rag_fusion">RAG Fusion</option>
        <option value="hyde" selected>Hyde</option>
      </select>
    </div>

    <div class="checkbox-container web-search-container">
      <label class="checkbox-label">
        <input type="checkbox" id="include-web-search" class="checkbox-input"  disabled>
        <span class="web-search-text"><strong>Recherche Web</strong> – Inclure les résultats web (0.1 cent par question)</span>
      </label>
    </div>

    <div class="checkbox-container privacy-container">
      <label class="checkbox-label">
        <input type="checkbox" id="privacy-mode" class="checkbox-input">
        <span class="privacy-text"><strong>Privacy Mode</strong> – No logging</span>
      </label>
      <div class="form-group">
        <div class="label-with-status">
          <label class="form-label" for="feedback-url">URL du backend de journalisation</label>
          <div class="status-text" id="feedback-status">Chargement…</div>
        </div>
        <input class="form-input" id="feedback-url" type="text" readonly/>
      </div>
    </div>

    <div class="checkbox-container debug-container">
      <label class="checkbox-label">
        <input type="checkbox" id="debug-mode" class="checkbox-input">
        <span class="debug-text"><strong>Debug Mode</strong> – Show response logs in console</span>
      </label>
    </div>

  </div> <!-- id="settings-container"-->
`
