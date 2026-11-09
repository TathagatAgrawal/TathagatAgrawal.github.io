// Auto / Light / Dark switch. "Auto" follows the system; a choice is remembered in this browser.
// The saved choice is applied by a one-line script in <head> so the page never flashes the wrong theme.
(function () {
  var root = document.documentElement;
  var control = document.querySelector('.theme');
  if (!control) return;

  function current() {
    return root.dataset.theme || 'auto';
  }

  function apply(choice) {
    if (choice === 'auto') delete root.dataset.theme;
    else root.dataset.theme = choice;
    try {
      if (choice === 'auto') localStorage.removeItem('theme');
      else localStorage.setItem('theme', choice);
    } catch (e) {}
    control.querySelectorAll('button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.value === choice));
    });
  }

  control.addEventListener('click', function (event) {
    if (event.target.matches('button')) apply(event.target.value);
  });
  control.hidden = false;
  apply(current());
})();
