document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initModals();
  initForms();
  initActions();
  initSorting();
  initSearch();
  initClock();
});

function initClock() {
  const el = document.getElementById('clockValue');
  if (!el) return;
  const tick = () => { el.textContent = new Date().toLocaleTimeString('en-GB'); };
  tick();
  setInterval(tick, 1000);
}

function initTheme() {
  const savedTheme = localStorage.getItem('builderos-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
}

function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = btn.getAttribute('data-modal-target');
      const modal = document.getElementById(modalId);
      if (modal) modal.classList.add('active');
    });
  });

  document.querySelectorAll('[data-close-modal], .modal-overlay').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay') || e.target.hasAttribute('data-close-modal')) {
        document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      }
    });
  });
}

function initForms() {
  const newProjectForm = document.getElementById('formNewProject');
  if (newProjectForm) {
    newProjectForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(newProjectForm));
      try {
        const res = await fetch('/api/project/create', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        const result = await res.json();
        if (res.ok) {
          showToast('Project created successfully');
          document.getElementById('modalNewProject').classList.remove('active');
          setTimeout(() => window.location.reload(), 1000);
        } else {
          showToast(result.error || 'Failed to create project', 'error');
        }
      } catch (err) { showToast('Network error', 'error'); }
    });
  }

  const githubForm = document.getElementById('formConnectGithub');
  if (githubForm) {
    githubForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(githubForm));
      try {
        const res = await fetch('/api/github/token', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        const result = await res.json();
        if (res.ok) {
          showToast('GitHub token saved and verified');
          document.getElementById('modalConnectGithub').classList.remove('active');
          setTimeout(() => window.location.reload(), 1000);
        } else {
          showToast(result.error || 'Failed to save token', 'error');
        }
      } catch (err) { showToast('Network error', 'error'); }
    });
  }
}

function initActions() {
  document.querySelectorAll('[data-copy]').forEach(el => {
    el.addEventListener('click', () => {
      const path = el.getAttribute('data-copy');
      navigator.clipboard.writeText(path).then(() => {
        showToast('Path copied to clipboard');
      }).catch(() => showToast('Failed to copy', 'error'));
    });
  });

  document.querySelectorAll('[data-kebab]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.kebab-menu').forEach(m => m.classList.remove('active'));
      const menu = btn.nextElementSibling;
      if (menu && menu.classList.contains('kebab-menu')) {
        menu.classList.toggle('active');
      }
    });
  });

  document.addEventListener('click', () => {
    document.querySelectorAll('.kebab-menu').forEach(m => m.classList.remove('active'));
  });

  const btnCopyBase = document.getElementById('btnCopyBasePath');
  if (btnCopyBase) {
    btnCopyBase.addEventListener('click', () => {
      navigator.clipboard.writeText('~/projects').then(() => showToast('Base path copied'));
    });
  }
}

function initSorting() {
  const table = document.querySelector('.projects-table');
  if (!table) return;

  const headers = table.querySelectorAll('th[data-sort]');
  headers.forEach(header => {
    header.addEventListener('click', () => {
      const key = header.getAttribute('data-sort');
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr[data-project-row]'));
      const isAsc = header.classList.contains('sort-asc');
      
      rows.sort((a, b) => {
        let valA = a.querySelector(`td:nth-child(${getColIndex(key)})`)?.textContent.trim().toLowerCase() || '';
        let valB = b.querySelector(`td:nth-child(${getColIndex(key)})`)?.textContent.trim().toLowerCase() || '';
        if (key === 'ahead') {
          valA = parseInt(a.querySelector('.plus')?.textContent.replace('+', '') || 0);
          valB = parseInt(b.querySelector('.plus')?.textContent.replace('+', '') || 0);
        }
        if (valA < valB) return isAsc ? 1 : -1;
        if (valA > valB) return isAsc ? -1 : 1;
        return 0;
      });

      headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      header.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
      rows.forEach(row => tbody.appendChild(row));
    });
  });
}

function getColIndex(key) {
  const map = { name: 2, path: 3, branch: 4, ui_status: 5, ahead: 6, last_commit: 7 };
  return map[key] || 1;
}

function initSearch() {
  const searchInput = document.querySelector('[data-project-search]');
  const statusFilter = document.querySelector('[data-status-filter]');
  
  function filterRows() {
    const query = searchInput?.value.toLowerCase() || '';
    const status = statusFilter?.value || 'all';
    
    document.querySelectorAll('tr[data-project-row]').forEach(row => {
      const name = row.getAttribute('data-name')?.toLowerCase() || row.querySelector('.proj-name')?.textContent.toLowerCase() || '';
      const isClean = row.querySelector('.badge')?.classList.contains('clean');
      
      const matchesSearch = name.includes(query);
      const matchesStatus = status === 'all' || (status === 'clean' && isClean) || (status === 'pending' && !isClean);
      
      row.style.display = matchesSearch && matchesStatus ? '' : 'none';
    });
  }

  searchInput?.addEventListener('input', filterRows);
  statusFilter?.addEventListener('change', filterRows);
}

function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}