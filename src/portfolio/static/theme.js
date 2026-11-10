// Light/dark toggle. Until the visitor clicks it, the site follows the system theme; after that the
// choice is remembered in this browser. The saved choice is applied by a one-line script in <head>
// so the page never flashes the wrong theme.
(function () {
  var root = document.documentElement;
  var button = document.querySelector('.theme-toggle');
  if (!button) return;
  var systemDark = window.matchMedia('(prefers-color-scheme: dark)');

  function current() {
    return root.dataset.theme || (systemDark.matches ? 'dark' : 'light');
  }

  // The button is an icon (a moon in light mode, a sun in dark mode, drawn by the stylesheet); this keeps
  // its accessible name and tooltip in step with the theme it would switch to.
  function label() {
    var text = current() === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    button.setAttribute('aria-label', text);
    button.title = text;
  }

  button.addEventListener('click', function () {
    var next = current() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
    label();
  });
  systemDark.addEventListener('change', label);
  button.hidden = false;
  label();
})();
