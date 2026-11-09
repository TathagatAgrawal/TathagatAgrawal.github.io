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

  // The button names the theme it switches to.
  function label() {
    var dark = current() === 'dark';
    button.textContent = dark ? 'Light mode' : 'Dark mode';
    button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
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
