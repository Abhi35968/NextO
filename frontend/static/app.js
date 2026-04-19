/* NestO — Shared JS Utilities */
const API = '';

// ── Theme ────────────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('sos_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('sos_theme', next);
  // Swap icon
  const btn = document.getElementById('theme-btn');
  if (btn) {
    btn.innerHTML = `<i data-lucide="${next === 'dark' ? 'sun' : 'moon'}"></i>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }
}
initTheme();

// ── Auth ─────────────────────────────────────────────────────
function getToken() { return localStorage.getItem('sos_token'); }
function getUser() { return JSON.parse(localStorage.getItem('sos_user') || 'null'); }
function setAuth(token, user) {
  localStorage.setItem('sos_token', token);
  localStorage.setItem('sos_user', JSON.stringify(user));
}
function clearAuth() {
  localStorage.removeItem('sos_token');
  localStorage.removeItem('sos_user');
}
function requireAuth(allowedRoles) {
  const user = getUser();
  const token = getToken();
  if (!user || !token) { window.location.href = '/'; return null; }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    window.location.href = '/dashboard.html'; return null;
  }
  return user;
}

// ── API Fetch ─────────────────────────────────────────────────
async function api(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (res.status === 401) { clearAuth(); window.location.href = '/'; return null; }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Error');
  }
  return res.json();
}

async function apiForm(method, path, formData) {
  const res = await fetch(API + path, {
    method,
    headers: { 'Authorization': `Bearer ${getToken()}` },
    body: formData,
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Error'); }
  return res.json();
}

// ── UI Helpers ────────────────────────────────────────────────
function showAlert(msg, type = 'success', containerId = 'alert-container') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
  setTimeout(() => el.innerHTML = '', 3500);
}

function showError(msg, cid = 'alert-container') { showAlert(msg, 'error', cid); }

function badge(status) {
  const map = {
    paid: 'green', pending: 'yellow', overdue: 'red',
    open: 'red', assigned: 'blue', in_progress: 'purple',
    resolved: 'green', closed: 'gray',
    high: 'red', medium: 'yellow', low: 'green',
    admin: 'purple', resident: 'blue', security: 'green', staff: 'yellow',
  };
  return `<span class="badge badge-${map[status] || 'gray'}">${status}</span>`;
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatCurrency(n) {
  return '₹' + Number(n).toLocaleString('en-IN');
}

// ── Sidebar rendering ─────────────────────────────────────────
function renderSidebar(activePage) {
  const user = getUser();
  if (!user) return;

  const allNav = [
    { page: 'dashboard', icon: 'layout-dashboard', label: 'Dashboard', roles: ['admin', 'resident', 'security', 'staff'] },
    { section: 'Management', roles: ['admin', 'staff'] },
    { page: 'residents', icon: 'building-2', label: 'Residents & Flats', roles: ['admin', 'staff'] },
    { page: 'maintenance', icon: 'receipt', label: 'Maintenance', roles: ['admin', 'resident', 'staff'] },
    { page: 'visitors', icon: 'user-check', label: 'Visitor Log', roles: ['admin', 'security', 'resident'] },
    { section: 'Community', roles: ['admin', 'resident', 'staff', 'security'] },
    { page: 'complaints', icon: 'alert-circle', label: 'Complaints', roles: ['admin', 'resident', 'staff'] },
    { page: 'notices', icon: 'megaphone', label: 'Notices & Polls', roles: ['admin', 'resident', 'staff', 'security'] },
  ];

  const initials = user.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);

  let navHtml = '';
  for (const item of allNav) {
    if (!item.roles.includes(user.role)) continue;
    if (item.section) {
      navHtml += `<div class="nav-section">${item.section}</div>`;
    } else {
      navHtml += `
        <a href="/${item.page}.html" class="nav-item ${activePage === item.page ? 'active' : ''}">
          <i data-lucide="${item.icon}" class="nav-icon"></i>${item.label}
        </a>`;
    }
  }

  document.getElementById('sidebar').innerHTML = `
    <div class="sidebar-logo">
      <h1><span class="logo-dot"></span> NestO</h1>
      <button class="theme-btn" id="theme-btn" onclick="toggleTheme()" title="Toggle theme">
        <i data-lucide="${document.documentElement.getAttribute('data-theme') === 'dark' ? 'sun' : 'moon'}"></i>
      </button>
    </div>
    <div class="sidebar-user">
      <div class="avatar">${initials}</div>
      <div class="sidebar-user-info">
        <strong>${user.name}</strong>
        <small>${user.role}</small>
      </div>
    </div>
    <nav class="sidebar-nav">${navHtml}</nav>
    <div class="sidebar-footer">
      <button class="nav-item w-full" onclick="logout()">
        <i data-lucide="log-out" class="nav-icon"></i>Sign out
      </button>
    </div>`;

  if (typeof lucide !== 'undefined') lucide.createIcons();
}

function logout() {
  clearAuth();
  window.location.href = '/';
}

// ── Modal helpers ─────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add('open');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}
// Close on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});
