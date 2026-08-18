(function () {
  // ---- theme ----
  const root = document.documentElement;
  const stored = localStorage.getItem('builderos-theme');
  if (stored) root.setAttribute('data-theme', stored);

  function currentTheme() {
    return root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }

  function applyToggleLabel() {
    document.querySelectorAll('[data-theme-toggle]').forEach(function (el) {
      const label = el.querySelector('[data-theme-label]');
      if (label) label.textContent = currentTheme() === 'light' ? 'LIGHT MODE' : 'DARK MODE';
    });
  }

  document.querySelectorAll('[data-theme-toggle]').forEach(function (el) {
    el.addEventListener('click', function () {
      const next = currentTheme() === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      localStorage.setItem('builderos-theme', next);
      applyToggleLabel();
    });
  });
  applyToggleLabel();

  // ---- table search / filter ----
  const searchInput = document.querySelector('[data-project-search]');
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      const q = searchInput.value.trim().toLowerCase();
      document.querySelectorAll('[data-project-row]').forEach(function (row) {
        const name = (row.getAttribute('data-name') || '').toLowerCase();
        const branch = (row.getAttribute('data-branch') || '').toLowerCase();
        row.style.display = (!q || name.includes(q) || branch.includes(q)) ? '' : 'none';
      });
    });
  }

  const statusFilter = document.querySelector('[data-status-filter]');
  if (statusFilter) {
    statusFilter.addEventListener('change', function () {
      const val = statusFilter.value;
      document.querySelectorAll('[data-project-row]').forEach(function (row) {
        const clean = row.getAttribute('data-clean');
        row.style.display = (val === 'all' || val === clean) ? '' : 'none';
      });
    });
  }

  // ---- kebab menus ----
  document.querySelectorAll('[data-kebab]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      const menu = btn.nextElementSibling;
      document.querySelectorAll('.kebab-menu.open').forEach(function (m) {
        if (m !== menu) m.classList.remove('open');
      });
      menu.classList.toggle('open');
    });
  });
  document.addEventListener('click', function () {
    document.querySelectorAll('.kebab-menu.open').forEach(function (m) { m.classList.remove('open'); });
  });

  // ---- copy to clipboard ----
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const text = btn.getAttribute('data-copy');
      navigator.clipboard.writeText(text).then(function () {
        const originalText = btn.textContent;
        btn.textContent = 'COPIED';
        btn.classList.add('copied');
        setTimeout(function () {
          btn.textContent = originalText;
          btn.classList.remove('copied');
        }, 1400);
      });
    });
  });

  // ---- flash dismiss ----
  document.querySelectorAll('[data-flash-dismiss]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.closest('.flash').remove();
    });
  });
})();