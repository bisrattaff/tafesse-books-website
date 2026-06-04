document.addEventListener('DOMContentLoaded', function () {
  var btn    = document.getElementById('search-btn');
  var modal  = document.getElementById('search-modal');
  var closeBtn = document.getElementById('search-close');
  var input  = document.getElementById('search-input');
  var results = document.getElementById('search-results');

  if (!btn || !modal) return;

  btn.addEventListener('click', openModal);
  closeBtn.addEventListener('click', closeModal);

  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  input.addEventListener('input', function () {
    runSearch(this.value.trim().toLowerCase());
  });

  function openModal() {
    modal.style.display = 'flex';
    input.value = '';
    results.innerHTML = '';
    setTimeout(function () { input.focus(); }, 50);
  }

  function closeModal() {
    modal.style.display = 'none';
    input.value = '';
    results.innerHTML = '';
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
