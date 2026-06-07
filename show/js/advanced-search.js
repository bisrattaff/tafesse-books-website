// Advanced Search — powered by Claude API via AWS Lambda
// Set ADVANCED_SEARCH_URL to your API Gateway endpoint after deployment.
var ADVANCED_SEARCH_URL = 'https://k0d8fif32g.execute-api.us-west-2.amazonaws.com/taf-book-search-stage/search';  // <-- paste your API Gateway URL here after setup

document.addEventListener('DOMContentLoaded', function () {
  var toggleBtn  = document.getElementById('adv-toggle-btn');
  var section    = document.getElementById('adv-search-section');
  var input      = document.getElementById('adv-input');
  var submitBtn  = document.getElementById('adv-submit-btn');
  var resultDiv  = document.getElementById('adv-result');

  if (!toggleBtn) return;

  // Show/hide the advanced search panel
  toggleBtn.addEventListener('click', function () {
    var hidden = section.style.display === 'none' || section.style.display === '';
    section.style.display = hidden ? 'block' : 'none';
    if (hidden) input.focus();
  });

  // Submit on button click or Enter key
  submitBtn.addEventListener('click', runSearch);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') runSearch();
  });

  function runSearch() {
    var query = input.value.trim();
    if (query.length < 3) return;

    if (!ADVANCED_SEARCH_URL) {
      resultDiv.innerHTML = '<p class="adv-error">Advanced search is not yet configured.</p>';
      return;
    }

    resultDiv.innerHTML = '<p class="adv-loading">Searching books …</p>';
    submitBtn.disabled = true;

    fetch(ADVANCED_SEARCH_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          resultDiv.innerHTML = '<p class="adv-error">' + escHtml(data.error) + '</p>';
          return;
        }
        var sourcesHtml = '';
        if (data.sources && data.sources.length) {
          sourcesHtml = '<p class="adv-sources">Sources: <em>' +
            data.sources.map(escHtml).join(', ') + '</em></p>';
        }
        resultDiv.innerHTML =
          '<div class="adv-answer">' + escHtml(data.answer) + '</div>' + sourcesHtml;
      })
      .catch(function () {
        resultDiv.innerHTML = '<p class="adv-error">Search unavailable. Please try again.</p>';
      })
      .finally(function () {
        submitBtn.disabled = false;
      });
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
});
