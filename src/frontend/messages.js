// ==========================================
// MAIN CONTENTS CREATION AND DISPLAY
// ==========================================

function addMain(content) {
    debugLog('Adding article to main content zone', { contentLength: content.length });
    const articleEl = document.createElement('article');
    articleEl.id = `article-${articleIdCounter++}`;
    articleEl.innerHTML = content;
    messagesContainer.appendChild(articleEl);
    
    addCarouselControls(articleEl);
    showLatestArticle();
    
    return articleEl;
}

function addMainError(content) {
    debugLog('Adding error message to main content zone', { contentLength: content.length });
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = content;
    messagesContainer.prepend(errorDiv);
}

function showTyping() {
    debugLog('Showing typing indicator');
    hideTyping();
    const spinnerDiv = document.createElement('div');
    spinnerDiv.id = 'typing-indicator';
    spinnerDiv.innerHTML = '<span class="typing-spinner">⟳</span>Recherche dans la base documentaire (compter 6-20s)…';
    mainEl.appendChild(spinnerDiv);
}

function hideTyping() {
    debugLog('Hiding typing indicator');
    document.getElementById('typing-indicator')?.remove();
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
        <button class="clipboard-button" title="Copier l'article dans le presse-papiers">📋</button>
        <input type="text" class="feedback-input" placeholder="Donnez votre avis sur cette réponse." maxlength="500">
        <button class="feedback-button feedback-up" title="Bonne réponse.">👍</button>
        <button class="feedback-button feedback-down" title="Réponse insuffisante.">👎</button>
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

function addCarouselControls(articleEl) {
    const carouselDiv = document.createElement('div');
    carouselDiv.className = 'carousel-navigation';
    carouselDiv.innerHTML = `
        <button class="carousel-btn carousel-prev" title="Article précédent">←</button>
        <span class="carousel-indicator"></span>
        <button class="carousel-btn carousel-next" title="Article suivant">→</button>
    `;
    
    articleEl.appendChild(carouselDiv);
    
    const prevBtn = carouselDiv.querySelector('.carousel-prev');
    const nextBtn = carouselDiv.querySelector('.carousel-next');
    
    prevBtn.addEventListener('click', () => navigateToArticle('prev'));
    nextBtn.addEventListener('click', () => navigateToArticle('next'));
}

function navigateToArticle(direction) {
    const articles = Array.from(messagesContainer.children).filter(child => child.tagName === 'ARTICLE');
    const totalArticles = articles.length;
    
    if (totalArticles === 0) return;
    
    if (direction === 'prev' && currentArticleIndex > 0) {
        currentArticleIndex--;
    } else if (direction === 'next' && currentArticleIndex < totalArticles - 1) {
        currentArticleIndex++;
    }
    
    showArticleAtIndex(currentArticleIndex);
}

function showArticleAtIndex(index) {
    const articles = Array.from(messagesContainer.children).filter(child => child.tagName === 'ARTICLE');
    const totalArticles = articles.length;
    
    if (totalArticles === 0 || index < 0 || index >= totalArticles) return;
    
    articles.forEach((article, i) => {
        article.hidden = i !== index;
    });
    
    currentArticleIndex = index;
    updateCarouselControls();
    // Scroller le conteneur messages-container jusqu’à l’article affiché
    messagesContainer.scrollTo({ top: articles[index].offsetTop, behavior: 'smooth' });
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
    
    articles.forEach((article, i) => {
        const carouselNav = article.querySelector('.carousel-navigation');
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
    });
}
