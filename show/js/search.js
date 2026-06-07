// Position search button just to the right of the nav bar on desktop
function positionSearchBtn() {
  var btn  = document.getElementById('search-btn');
  var menu = document.querySelector('.divMenu');
  if (!btn || !menu) return;

  if (window.innerWidth >= 769) {
    var rect = menu.getBoundingClientRect();
    btn.style.left = (rect.right + 12) + 'px';
    btn.style.top  = (rect.top + (rect.height - 40) / 2) + 'px';
    btn.style.right = 'auto';
  } else {
    btn.style.left  = '';
    btn.style.top   = '';
    btn.style.right = '';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  positionSearchBtn();
  window.addEventListener('resize', positionSearchBtn);

  var btn      = document.getElementById('search-btn');
  var modal    = document.getElementById('search-modal');
  var closeBtn = document.getElementById('search-close');
  var input    = document.getElementById('search-input');
  var clearBtn = document.querySelector('.search-clear-btn');
  var results  = document.getElementById('search-results');
  var advSection = document.getElementById('adv-search-section');

  if (!btn || !modal) return;

  btn.addEventListener('click', openModal);
  closeBtn.addEventListener('click', closeModal);

  // Close on backdrop click
  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });

  // Close on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  // Back button closes modal on mobile
  window.addEventListener('popstate', function () {
    if (modal.style.display === 'flex') closeModal(true);
  });

  // Clear button
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      input.value = '';
      results.innerHTML = '';
      clearBtn.style.display = 'none';
      input.focus();
    });
  }

  // Live search
  input.addEventListener('input', function () {
    var query = this.value.trim().toLowerCase();
    // Show/hide clear button
    if (clearBtn) clearBtn.style.display = query.length ? 'block' : 'none';
    // Collapse Ask AI when typing in quick search
    if (advSection && advSection.style.display === 'block') {
      advSection.style.display = 'none';
    }
    runSearch(query);
  });

  function openModal() {
    modal.style.display = 'flex';
    input.value = '';
    results.innerHTML = '';
    if (clearBtn) clearBtn.style.display = 'none';
    // Push state so back button can close the modal
    history.pushState({ searchModal: true }, '');
    setTimeout(function () { input.focus(); }, 50);
  }

  function closeModal(fromPopstate) {
    modal.style.display = 'none';
    input.value = '';
    results.innerHTML = '';
    if (clearBtn) clearBtn.style.display = 'none';
    if (advSection) advSection.style.display = 'none';
    // Re-enable quick search in case AI mode was active
    var titleInput = document.querySelector('.search-title-input');
    if (titleInput) titleInput.classList.remove('search-disabled');
    if (!fromPopstate && history.state && history.state.searchModal) {
      history.back();
    }
  }

  function runSearch(query) {
    results.innerHTML = '';
    if (query.length < 2) return;

    var matches = SEARCH_DATA.filter(function (book) {
      var haystack = book.title.toLowerCase() + ' ' +
                     book.description.toLowerCase() + ' ' +
                     book.keywords.join(' ');
      return haystack.indexOf(query) !== -1;
    });

    if (matches.length === 0) {
      results.innerHTML = '<p class="search-no-results">No books found for &ldquo;' + escHtml(query) + '&rdquo;</p>';
      return;
    }

    matches.forEach(function (book) {
      var item = document.createElement('div');
      item.className = 'search-result-item';
      item.innerHTML =
        '<img src="' + book.icon + '" alt="' + escHtml(book.title) + '">' +
        '<div class="search-result-info">' +
          '<div class="search-result-title">' + escHtml(book.title) + '</div>' +
          '<div class="search-result-desc">' + escHtml(book.description) + '</div>' +
          '<a href="' + book.download + '" target="_blank" class="search-result-link">Download PDF &rarr;</a>' +
        '</div>';
      results.appendChild(item);
    });
  }

  function escHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
});
