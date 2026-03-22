// AudiobookSeeker — Main App Module

const state = {
  token: localStorage.getItem('abs_token') || '',
  currentPage: 'search',
  absLibraryId: '',
};

// ── Helpers ──
const $ = (sel) => document.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const esc = (s) => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function showToast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 3000);
}

function fmtSize(bytes) {
  if (bytes > 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
  if (bytes > 1e6) return (bytes / 1e6).toFixed(0) + ' MB';
  return (bytes / 1e3).toFixed(0) + ' KB';
}

function fmtDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function fmtSpeed(bps) {
  if (bps > 1e6) return (bps / 1e6).toFixed(1) + ' MB/s';
  if (bps > 1e3) return (bps / 1e3).toFixed(0) + ' KB/s';
  return bps + ' B/s';
}

async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
  const resp = await fetch(path, { ...opts, headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
  if (resp.status === 401) { logout(); throw new Error('Session expired'); }
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.detail || `Error ${resp.status}`);
  }
  return resp.json();
}

// ── Auth ──
function logout() {
  state.token = '';
  localStorage.removeItem('abs_token');
  showPage('login');
  $('#navLinks').style.display = 'none';
  $('#pageLogin').classList.add('active');
}

async function doLogin() {
  const user = $('#loginUser').value.trim();
  const pass = $('#loginPass').value;
  if (!user || !pass) return;
  $('#loginError').textContent = '';
  try {
    const data = await api('/api/auth/login', { method: 'POST', body: { username: user, password: pass } });
    state.token = data.token;
    localStorage.setItem('abs_token', data.token);
    onLoggedIn();
  } catch (e) {
    $('#loginError').textContent = e.message;
  }
}

async function onLoggedIn() {
  $('#navLinks').style.display = 'flex';
  showPage('search');
  // Discover ABS library
  try {
    const libs = await api('/api/library/libraries');
    const bookLib = libs.find(l => l.mediaType === 'book') || libs[0];
    if (bookLib) state.absLibraryId = bookLib.id;
  } catch {}
}

// ── Navigation ──
function showPage(page) {
  state.currentPage = page;
  $$('.page').forEach(p => p.classList.remove('active'));
  const el = $(`#page${page[0].toUpperCase() + page.slice(1)}`);
  if (el) el.classList.add('active');
  $$('#navLinks button').forEach(b => b.classList.toggle('active', b.dataset.page === page));
  if (page === 'downloads') loadDownloads();
  if (page === 'library') loadLibrary();
}

// ── Search (Prowlarr) ──
async function doSearch() {
  const q = $('#searchInput').value.trim();
  if (!q) return;
  const container = $('#searchResults');
  container.innerHTML = Array(4).fill('<div class="skeleton" style="height:100px;margin-bottom:12px"></div>').join('');
  try {
    const data = await api(`/api/search?q=${encodeURIComponent(q)}`);
    if (!data.results.length) {
      container.innerHTML = '<div class="empty-state"><p>No results found</p></div>';
      return;
    }
    container.innerHTML = data.results.map(r => `
      <div class="card" data-result='${JSON.stringify(r).replace(/'/g, "&#39;")}'>
        <div class="card-title">${esc(r.title)}</div>
        <div class="card-meta">
          <span class="card-indexer">${esc(r.indexer)}</span>
          <span>${fmtSize(r.size)}</span>
          <span>${r.seeders} seeders</span>
          ${r.grabs ? `<span>${r.grabs} grabs</span>` : ''}
        </div>
        <div class="card-actions">
          <button class="btn btn-primary dl-btn">Download</button>
          ${r.info_url ? `<a href="${esc(r.info_url)}" target="_blank" class="btn btn-secondary" onclick="event.stopPropagation()">Info</a>` : ''}
        </div>
      </div>
    `).join('');
    $$('.dl-btn', container).forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const card = btn.closest('.card');
        const r = JSON.parse(card.dataset.result);
        startDownload(r);
      });
    });
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><p>Search failed: ${esc(e.message)}</p></div>`;
  }
}

async function startDownload(result) {
  try {
    await api('/api/download', {
      method: 'POST',
      body: {
        title: result.title,
        indexer: result.indexer,
        download_url: result.download_url,
        magnet_url: result.magnet_url,
        size: result.size,
        seeders: result.seeders,
      },
    });
    showToast('Download started!');
  } catch (e) {
    showToast('Download failed: ' + e.message);
  }
}

// ── Downloads ──
let dlInterval = null;
async function loadDownloads() {
  const container = $('#downloadsContent');
  try {
    const data = await api('/api/downloads');
    const torrents = data.torrents || [];
    const jobs = data.jobs || [];
    if (!torrents.length && !jobs.length) {
      container.innerHTML = '<div class="empty-state"><p>No downloads yet</p></div>';
      return;
    }
    let html = '';
    for (const t of torrents) {
      const pct = t.progress;
      const stateLabel = t.state === 'uploading' || t.state === 'stalledUP' ? 'Seeding'
        : t.state === 'downloading' ? 'Downloading'
        : t.state === 'pausedDL' ? 'Paused'
        : t.state === 'error' ? 'Error'
        : pct >= 100 ? 'Complete' : t.state;
      html += `
        <div class="dl-item">
          <div class="dl-name">${esc(t.name)}</div>
          <div class="dl-progress"><div class="dl-progress-fill" style="width:${pct}%"></div></div>
          <div class="dl-status">${pct >= 100 ? stateLabel : pct + '% ' + fmtSpeed(t.dlspeed)}</div>
        </div>
      `;
    }
    container.innerHTML = html || '<div class="empty-state"><p>No active downloads</p></div>';
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><p>Failed to load: ${esc(e.message)}</p></div>`;
  }
  // Auto-refresh while on downloads page
  clearInterval(dlInterval);
  if (state.currentPage === 'downloads') {
    dlInterval = setInterval(() => { if (state.currentPage === 'downloads') loadDownloads(); }, 5000);
  }
}

// ── Library (Audiobookshelf) ──
async function loadLibrary() {
  const container = $('#libraryContent');
  if (!state.absLibraryId) {
    container.innerHTML = '<div class="empty-state"><p>Audiobookshelf not connected or no library found</p></div>';
    return;
  }
  container.innerHTML = Array(4).fill('<div class="skeleton" style="height:80px;margin-bottom:12px"></div>').join('');
  try {
    const data = await api(`/api/library/libraries/${state.absLibraryId}/items?limit=100`);
    if (!data.items.length) {
      container.innerHTML = '<div class="empty-state"><p>Library is empty. Download some audiobooks first!</p></div>';
      return;
    }
    renderLibraryItems(data.items, container);
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><p>Failed to load: ${esc(e.message)}</p></div>`;
  }
}

async function searchLibrary() {
  const q = $('#libSearchInput').value.trim();
  if (!q || !state.absLibraryId) { loadLibrary(); return; }
  const container = $('#libraryContent');
  container.innerHTML = '<div class="skeleton" style="height:80px"></div>';
  try {
    const data = await api(`/api/library/libraries/${state.absLibraryId}/search?q=${encodeURIComponent(q)}`);
    if (!data.results.length) {
      container.innerHTML = '<div class="empty-state"><p>No results</p></div>';
      return;
    }
    renderLibraryItems(data.results, container);
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><p>Search failed: ${esc(e.message)}</p></div>`;
  }
}

function renderLibraryItems(items, container) {
  container.innerHTML = items.map(item => `
    <div class="lib-card" data-id="${esc(item.id)}">
      <img src="${item.cover ? esc(item.cover) + '?width=160' : ''}" alt="" loading="lazy"
           onerror="this.style.background='var(--bg-elevated)'">
      <div class="lib-card-body">
        <div class="lib-card-title">${esc(item.title)}</div>
        <div class="lib-card-author">${esc(item.author || '')}</div>
        <div class="lib-card-meta">
          ${item.duration ? `<span>${fmtDuration(item.duration)}</span>` : ''}
          ${item.year ? `<span>${item.year}</span>` : ''}
          ${item.num_tracks ? `<span>${item.num_tracks} files</span>` : ''}
          <span>${fmtSize(item.size)}</span>
        </div>
        ${item.description ? `<div style="font-size:12px;color:var(--text-dim);margin-top:6px;line-height:1.4">${esc(item.description.substring(0, 150))}${item.description.length > 150 ? '...' : ''}</div>` : ''}
      </div>
    </div>
  `).join('');
}

// ── Init ──
function init() {
  // Login
  $('#loginBtn').addEventListener('click', doLogin);
  $('#loginPass').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
  $('#loginUser').addEventListener('keydown', e => { if (e.key === 'Enter') $('#loginPass').focus(); });

  // Nav
  $$('#navLinks button').forEach(btn => {
    btn.addEventListener('click', () => showPage(btn.dataset.page));
  });

  // Search
  $('#searchBtn').addEventListener('click', doSearch);
  $('#searchInput').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

  // Library search
  $('#libSearchBtn').addEventListener('click', searchLibrary);
  $('#libSearchInput').addEventListener('keydown', e => { if (e.key === 'Enter') searchLibrary(); });

  // Auto-login if token exists
  if (state.token) {
    api('/api/auth/me').then(() => onLoggedIn()).catch(() => logout());
  }
}

init();
