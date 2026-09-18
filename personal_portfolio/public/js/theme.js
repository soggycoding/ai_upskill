/**
 * Flash-free theme bootstrap & persistence
 */
(function () {
  try {
    const savedTheme = localStorage.getItem('portfolio-theme');
    const systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (systemDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
  } catch (e) {
    document.documentElement.setAttribute('data-theme', 'light');
  }
})();

function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;

  function updateToggleUI(currentTheme) {
    const isDark = currentTheme === 'dark';
    toggleBtn.setAttribute('aria-label', `Switch to ${isDark ? 'light' : 'dark'} theme`);
    toggleBtn.setAttribute('title', `Switch to ${isDark ? 'light' : 'dark'} theme`);
    
    // Sun for dark mode (click to light), Moon for light mode (click to dark)
    toggleBtn.innerHTML = isDark
      ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
      : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
  }

  const initial = document.documentElement.getAttribute('data-theme') || 'light';
  updateToggleUI(initial);

  toggleBtn.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const nextTheme = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    try {
      localStorage.setItem('portfolio-theme', nextTheme);
    } catch (e) {}
    updateToggleUI(nextTheme);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initThemeToggle);
} else {
  initThemeToggle();
}
