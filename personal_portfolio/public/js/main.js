/**
 * Main Public Portfolio Client Engine
 * Vanilla JS · Data-Driven · Accessible · 100% Offline
 */

let portfolioData = null;
let activeCategory = 'all';
let searchQuery = '';
let webglInstance = null;

async function loadPortfolioData() {
  try {
    const res = await fetch('/api/content');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    portfolioData = await res.json();
    renderAll(portfolioData);
  } catch (err) {
    console.error('Error loading portfolio:', err);
    const main = document.getElementById('main-content');
    if (main) {
      main.innerHTML = `<div class="container" style="padding: 60px 0;"><p style="color: var(--accent);">Failed to load portfolio content. Ensure the local server is running at <code>127.0.0.1:3000</code>.</p></div>`;
    }
  }
}

function renderAll(data) {
  renderProfile(data.profile);
  renderProjects(data.projects);
  renderCapabilities(data.profile.capabilities);
  renderExperience(data.experience);
  renderEducation(data.education);
  renderContact(data.contact, data.profile);
  initWebGLToggle();
}

function renderProfile(profile) {
  if (!profile) return;

  // Header
  const logoName = document.getElementById('header-name');
  if (logoName) logoName.textContent = profile.name || '[YOUR NAME]';
  const logoStatus = document.getElementById('header-status');
  if (logoStatus) logoStatus.textContent = profile.status || 'Active';

  // Hero
  const heroName = document.getElementById('hero-name');
  if (heroName) heroName.textContent = profile.name || '[YOUR NAME]';
  const heroIdentity = document.getElementById('hero-identity');
  if (heroIdentity) heroIdentity.textContent = profile.identity || '[YOUR ACADEMIC / PROFESSIONAL IDENTITY]';
  const heroIntro = document.getElementById('hero-intro');
  if (heroIntro) heroIntro.textContent = profile.shortIntro || '';

  // Meta items
  const metaContainer = document.getElementById('hero-meta');
  if (metaContainer) {
    metaContainer.innerHTML = `
      <div class="hero-meta-item">
        <span class="status-dot"></span>
        <span>${escapeHtml(profile.status || 'Available')}</span>
      </div>
      <div class="hero-meta-item">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
        <span>${escapeHtml(profile.location || 'Localhost')}</span>
      </div>
      <div class="hero-meta-item">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
        <a href="mailto:${encodeURIComponent(profile.email || '')}">${escapeHtml(profile.email || '')}</a>
      </div>
    `;
  }
}

function renderProjects(projects) {
  const container = document.getElementById('projects-grid');
  const filterPillsContainer = document.getElementById('filter-pills');
  if (!container || !Array.isArray(projects)) return;

  // Build categories list
  const categories = ['all', ...new Set(projects.map(p => p.category).filter(Boolean))];
  
  if (filterPillsContainer && categories.length > 2) {
    filterPillsContainer.innerHTML = categories.map(cat => `
      <button class="pill ${cat === activeCategory ? 'active' : ''}" data-category="${escapeHtml(cat)}">
        ${escapeHtml(cat === 'all' ? 'All Areas' : cat)}
      </button>
    `).join('');

    filterPillsContainer.querySelectorAll('.pill').forEach(btn => {
      btn.addEventListener('click', () => {
        activeCategory = btn.getAttribute('data-category');
        filterPillsContainer.querySelectorAll('.pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        applyProjectFilters();
      });
    });
  }

  // Search input handler
  const searchInput = document.getElementById('project-search');
  if (searchInput && !searchInput.dataset.initialized) {
    searchInput.dataset.initialized = 'true';
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      applyProjectFilters();
    });
  }

  applyProjectFilters();
}

function applyProjectFilters() {
  const container = document.getElementById('projects-grid');
  if (!container || !portfolioData) return;

  const projects = portfolioData.projects || [];
  const filtered = projects.filter(p => {
    const matchesCategory = activeCategory === 'all' || p.category === activeCategory;
    if (!matchesCategory) return false;

    if (!searchQuery) return true;
    const matchString = `${p.title} ${p.shortDescription} ${p.category} ${(p.tags || []).join(' ')} ${(p.technologies || []).join(' ')}`.toLowerCase();
    return matchString.includes(searchQuery);
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; padding: 40px; text-align: center; color: var(--text-muted); background: var(--bg-secondary); border-radius: var(--radius-md); border: 1px dashed var(--border);">
        <p>No projects match your current search query or filter selection.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(p => {
    const statusClass = `status-${(p.status || 'completed').toLowerCase()}`;
    const tagsHtml = (p.tags || []).slice(0, 3).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');
    
    return `
      <article class="project-card">
        <div class="project-card-header">
          <div class="project-meta-top">
            <span>${p.year || ''}</span>
            <span>·</span>
            <span>${escapeHtml(p.category || 'Engineering')}</span>
          </div>
          <span class="status-badge ${statusClass}">${escapeHtml(p.status || 'Active')}</span>
        </div>
        
        <h3 class="project-card-title">
          <a href="/project.html?slug=${encodeURIComponent(p.slug)}">${escapeHtml(p.title)}</a>
        </h3>
        
        <p class="project-card-desc">${escapeHtml(p.shortDescription || '')}</p>
        
        <div class="project-role-badge">
          Role: ${escapeHtml(p.role || 'Contributor')}
        </div>
        
        <div class="project-tags">
          ${tagsHtml}
        </div>
        
        <div class="project-card-footer">
          <span style="font-size: 0.8rem; font-family: var(--font-mono); color: var(--text-muted);">
            ${(p.technologies || []).slice(0, 2).join(', ')}
          </span>
          <a href="/project.html?slug=${encodeURIComponent(p.slug)}" class="project-card-link" aria-label="Read technical case study for ${escapeHtml(p.title)}">
            <span>Case Study</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
          </a>
        </div>
      </article>
    `;
  }).join('');
}

function renderCapabilities(capabilities) {
  const container = document.getElementById('capabilities-grid');
  if (!container || !Array.isArray(capabilities)) return;

  container.innerHTML = capabilities.map(cap => `
    <div class="capability-card">
      <h3 class="capability-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>
        ${escapeHtml(cap.category)}
      </h3>
      <ul class="capability-items">
        ${(cap.items || []).map(item => `<li class="capability-chip">${escapeHtml(item)}</li>`).join('')}
      </ul>
    </div>
  `).join('');
}

function renderExperience(experience) {
  const container = document.getElementById('experience-timeline');
  if (!container || !Array.isArray(experience)) return;

  container.innerHTML = experience.map(exp => `
    <div class="timeline-item">
      <div class="timeline-dot"></div>
      <div class="timeline-period">${escapeHtml(exp.period)} · ${escapeHtml(exp.location || '')}</div>
      <h3 class="timeline-role">${escapeHtml(exp.role)}</h3>
      <div class="timeline-org">${escapeHtml(exp.organization)}</div>
      <p class="timeline-desc">${escapeHtml(exp.description)}</p>
      ${exp.highlights && exp.highlights.length ? `
        <ul class="timeline-bullets">
          ${exp.highlights.map(h => `<li>${escapeHtml(h)}</li>`).join('')}
        </ul>
      ` : ''}
    </div>
  `).join('');
}

function renderEducation(education) {
  const container = document.getElementById('education-timeline');
  if (!container || !Array.isArray(education)) return;

  container.innerHTML = education.map(edu => `
    <div class="timeline-item">
      <div class="timeline-dot"></div>
      <div class="timeline-period">${escapeHtml(edu.period)} · ${escapeHtml(edu.location || '')}</div>
      <h3 class="timeline-role">${escapeHtml(edu.degree)}</h3>
      <div class="timeline-org">${escapeHtml(edu.institution)}</div>
      ${edu.focus ? `<p class="timeline-desc"><strong>Focus:</strong> ${escapeHtml(edu.focus)}</p>` : ''}
      ${edu.honors ? `<p class="timeline-desc" style="color: var(--accent); font-size: 0.85rem;"><strong>Recognition:</strong> ${escapeHtml(edu.honors)}</p>` : ''}
    </div>
  `).join('');
}

function renderContact(contact, profile) {
  const emailElem = document.getElementById('contact-email');
  if (emailElem && profile && profile.email) {
    emailElem.href = `mailto:${encodeURIComponent(profile.email)}`;
    emailElem.textContent = profile.email;
  }
  const noteElem = document.getElementById('contact-note');
  if (noteElem && contact && contact.note) {
    noteElem.textContent = contact.note;
  }
}

function initWebGLToggle() {
  const toggleBtn = document.getElementById('webgl-toggle');
  const container = document.getElementById('webgl-box');
  if (!toggleBtn || !container) return;

  let isEnabled = localStorage.getItem('webgl-experiment-enabled') === 'true';

  function updateState() {
    if (isEnabled) {
      container.style.display = 'block';
      toggleBtn.textContent = 'Hide 3D Experiment';
      toggleBtn.classList.add('active');
      if (!webglInstance && window.initWebGLExperiment) {
        webglInstance = window.initWebGLExperiment('hero-webgl-canvas');
      }
    } else {
      container.style.display = 'none';
      toggleBtn.textContent = 'View 3D Cluster Topology (Prototype)';
      toggleBtn.classList.remove('active');
      if (webglInstance) {
        webglInstance.destroy();
        webglInstance = null;
      }
    }
  }

  toggleBtn.addEventListener('click', () => {
    isEnabled = !isEnabled;
    localStorage.setItem('webgl-experiment-enabled', isEnabled ? 'true' : 'false');
    updateState();
  });

  updateState();
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', loadPortfolioData);
