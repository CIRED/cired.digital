// ==========================================
// CONTENT MANAGER
// ==========================================

function addMain(content) {
    debugLog('Adding article to main content zone', { contentLength: content.length });
    const article = document.createElement('article');
    article.id = `article-${articleIdCounter++}`;
    article.innerHTML = content;
    messagesContainer.appendChild(article);
    showLatestArticle();
    return article;
}

function addMainError(content) {
    debugLog('Adding error message to main content zone', { contentLength: content.length });
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = content;
    messagesContainer.prepend(errorDiv);
}

// ==========================================
// ==========================================

function uiProcessingStart() {
    debugLog('Setting up the UI for processing state');

    setLoadingState(true);
    // Hide greeting and input help if they exist
    const greetingDiv = document.getElementById('greeting');
    if (greetingDiv) {
        greetingDiv.style.display = 'none';
    }
    const inputHelpDiv = document.getElementById('input-help');
    if (inputHelpDiv) {
        inputHelpDiv.style.display = 'none';
    }
    // Hide the previous articles
    messagesContainer.querySelectorAll('article').forEach(el => el.classList.add('seen'));

    // Add the typing indicator if it doesn't already exist
    if (!document.getElementById('typing-indicator')) {
        const spinnerDiv = document.createElement('div');
        spinnerDiv.id = 'typing-indicator';
        mainDiv.appendChild(spinnerDiv);
        spinnerDiv.innerHTML = '<div id="loading-message"><span class="typing-spinner">⟳</span>Recherche dans la base documentaire…</div>';
    }
}

function uiProcessingUpdate(duration) {
    debugLog('Updating the UI with processing duration', { duration });

    const statusDiv = document.getElementById("loading-message");
    if (statusDiv) {
        seconds = duration / 1000;
        statusDiv.innerHTML = `<span class="typing-spinner-stopped">✔</span>Recherche documentaire terminée en ${seconds} secondes.`;
    }
}

function uiProcessingEnd() {
    debugLog('Finalizing the UI after processing');

    // Keep the stream results in debug mode
    if (typeof debugMode !== 'undefined' && debugMode) {
        const statusDiv = document.getElementById("loading-message");
        if (statusDiv) {
            statusDiv.innerHTML = '<span class="typing-spinner-stopped">✔✔</span>Recherche et Génération terminées.';
        }
    } else {
        // Remove the typing indicator
        const spinnerDiv = document.getElementById('typing-indicator');
        if (spinnerDiv) {
            spinnerDiv.remove();
        }
    }
    messagesContainer.querySelectorAll('article').forEach(el => el.classList.remove('seen'));
    setLoadingState(false);
    userInput.focus();
}

function setLoadingState(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    debugLog('Loading state set to ' + loading);
}

// ==========================================
// FEEDBACK
// ==========================================


function logFeedback(type, comment) {
    debugLog('Logging feedback', { type, comment });
    monitor(MonitorEventType.FEEDBACK, {
        type,
        comment: comment || ''
    });
}

function addFeedback(article) {
    debugLog('Adding feedback buttons to message');

    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-container';
    feedbackDiv.innerHTML = `
        <button class="ghost-button clipboard-button" title="Copier l'article dans le presse-papiers">📋</button>
        <input type="text" class="feedback-input" placeholder="Donnez votre avis sur cette réponse." maxlength="500">
        <button class="ghost-button feedback-up" title="Bonne réponse.">👍</button>
        <button class="ghost-button feedback-down" title="Réponse insuffisante.">👎</button>
    `;

    // Placer le feedback après le contenu de l'article
    article.appendChild(feedbackDiv);

    const commentInput = feedbackDiv.querySelector('input[type="text"]');
    const clipboardBtn = feedbackDiv.querySelector('.clipboard-button');

    clipboardBtn.addEventListener('click', () => {
        copyArticleToClipboard(article);
    });

    feedbackDiv.querySelector('.feedback-up').addEventListener('click', () => {
        logFeedback('up', commentInput.value.trim());
        showFeedbackSuccess(feedbackDiv);

        if (typeof onFeedbackCompleted === 'function' && !isOnboarded()) {
            onFeedbackCompleted();
        }
    });

    feedbackDiv.querySelector('.feedback-down').addEventListener('click', () => {
        logFeedback('down', commentInput.value.trim());
        showFeedbackSuccess(feedbackDiv);

        if (typeof onFeedbackCompleted === 'function' && !isOnboarded()) {
            onFeedbackCompleted();
        }
    });
}

function showFeedbackSuccess(feedbackDiv) {
    // Hide the input and thumbs, keep the clipboard button
    const input = feedbackDiv.querySelector('.feedback-input');
    const upBtn = feedbackDiv.querySelector('.feedback-up');
    const downBtn = feedbackDiv.querySelector('.feedback-down');

    if (input) input.style.display = 'none';
    if (upBtn) upBtn.style.display = 'none';
    if (downBtn) downBtn.style.display = 'none';

    // Add or show the thank you note
    let thankYou = feedbackDiv.querySelector('.feedback-success');
    if (!thankYou) {
        thankYou = document.createElement('div');
        thankYou.className = 'feedback-success';
        thankYou.textContent = 'Merci pour votre retour';
        feedbackDiv.appendChild(thankYou);
    } else {
        thankYou.style.display = '';
    }
}

function copyArticleToClipboard(article) {
  const htmlContent = article.innerHTML;
  const plainText = article.innerText;

  const clipboardItem = new ClipboardItem({
    "text/plain": new Blob([plainText], { type: "text/plain" }),
    "text/html": new Blob([htmlContent], { type: "text/html" })
  });

  navigator.clipboard.write([clipboardItem]).then(() => {
    debugLog('Article copied to clipboard (rich content)');
    const clipboardBtn = article.querySelector('.clipboard-button');
    const originalText = clipboardBtn.textContent;
    clipboardBtn.textContent = '✓';
    setTimeout(() => clipboardBtn.textContent = originalText, 1000);
  }).catch(err => {
    console.error('Failed to copy to clipboard:', err);
    fallbackCopyToClipboard(plainText);
  });
}

// Fallback method for browsers that don't support ClipboardItem
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        debugLog('Article copied to clipboard (fallback)');
    } catch (err) {
        console.error('Fallback copy failed:', err);
    }
    document.body.removeChild(textArea);
}

function addCarouselControls() {
    const carouselDiv = document.querySelector('.carousel-navigation');
    if (!carouselDiv) return;
    carouselDiv.removeAttribute('hidden');
    carouselDiv.innerHTML = `
        <button class="carousel-btn carousel-prev" title="Article précédent">←</button>
        <span class="carousel-indicator"></span>
        <button class="carousel-btn carousel-next" title="Article suivant">→</button>
    `;
    const prevBtn = carouselDiv.querySelector('.carousel-prev');
    const nextBtn = carouselDiv.querySelector('.carousel-next');
    prevBtn.addEventListener('click', () => navigateToArticle('prev'));
    nextBtn.addEventListener('click', () => navigateToArticle('next'));
}

function navigateToArticle(direction) {
    const articles = Array.from(messagesContainer.children).filter(child => child.tagName === 'ARTICLE');
    debugLog('navigateToArticle start', { direction, currentIndex: currentArticleIndex, totalArticles: articles.length });
    const totalArticles = articles.length;

    if (totalArticles === 0) return;

    if (direction === 'prev' && currentArticleIndex > 0) {
        currentArticleIndex--;
    } else if (direction === 'next' && currentArticleIndex < totalArticles - 1) {
        currentArticleIndex++;
    }

    debugLog('navigateToArticle', { direction, newIndex: currentArticleIndex });
    showArticleAtIndex(currentArticleIndex);
}

function showArticleAtIndex(index) {
    const articles = Array.from(messagesContainer.children).filter(child => child.tagName === 'ARTICLE');
    const totalArticles = articles.length;

    if (totalArticles === 0 || index < 0 || index >= totalArticles) return;

    articles.forEach((article, i) => {
        if (i === index) {
            article.style.display = '';
            article.hidden = false;
        } else {
            article.style.display = 'none';
        }
    });

    currentArticleIndex = index;
    updateCarouselControls();
    // Scroller le conteneur messages-container jusqu’à l’article affiché
    articles[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showLatestArticle() {
    const articles = Array.from(messagesContainer.children).filter(child => child.tagName === 'ARTICLE');
    if (articles.length > 0) {
        currentArticleIndex = articles.length - 1;
        showArticleAtIndex(currentArticleIndex);
    }
}

function updateCarouselControls() {
    const articles = Array.from(messagesContainer.children).filter(child => child.tagName === 'ARTICLE');
    const totalArticles = articles.length;

    const carouselNav = document.querySelector('.carousel-navigation');
    if (!carouselNav) return;

    const prevBtn = carouselNav.querySelector('.carousel-prev');
    const nextBtn = carouselNav.querySelector('.carousel-next');
    const indicator = carouselNav.querySelector('.carousel-indicator');

    if (totalArticles <= 1) {
        carouselNav.style.display = 'none';
    } else {
        carouselNav.style.display = 'flex';
        prevBtn.disabled = currentArticleIndex === 0;
        nextBtn.disabled = currentArticleIndex === totalArticles - 1;
        indicator.textContent = `${currentArticleIndex + 1} / ${totalArticles}`;
    }
}
