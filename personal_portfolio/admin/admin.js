/**
 * Local CMS Client Logic
 * Handles Admin Authentication, CRUD, Version Restore, and Diagnostics
 */

let currentData = null;
let currentTab = 'dashboard';
let editingProjectIndex = -1;

async function checkAuth() {
  try {
    const res = await fetch('/api/admin/check-auth');
    const json = await res.json();
    if (json.authenticated) {
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('admin-layout').style.display = 'flex';
      loadData();
    } else {
      document.getElementById('login-screen').style.display = 'flex';
      document.getElementById('admin-layout').style.display = 'none';
    }
  } catch (err) {
    console.error('Auth check error:', err);
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const passcode = document.getElementById('login-passcode').value;
  const errorElem = document.getElementById('login-error');
  errorElem.textContent = '';

  try {
    const res = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ passcode })
    });
    const json = await res.json();
    if (res.ok && json.success) {
      checkAuth();
    } else {
      errorElem.textContent = json.error || 'Incorrect passcode';
    }
  } catch (err) {
    errorElem.textContent = 'Server connection failed';
  }
}

async function handleLogout() {
  await fetch('/api/admin/logout', { method: 'POST' });
  checkAuth();
}

async function loadData() {
  try {
    const res = await fetch('/api/content');
    currentData = await res.json();
    switchTab(currentTab);
  } catch (err) {
    alert('Error loading portfolio data: ' + err.message);
  }
}

async function saveContent(changeDesc) {
  try {
    const res = await fetch('/api/admin/content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data: currentData,
        changeDescription: changeDesc || 'CMS Content Update'
      })
    });
    const json = await res.json();
    if (res.ok && json.success) {
      showToast('Changes saved and version snapshot created.');
      loadData();
    } else {
      alert('Save failed: ' + (json.error || 'Unknown error'));
    }
  } catch (err) {
    alert('Save error: ' + err.message);
  }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.style.display = 'block';
  setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.admin-nav button').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });

  const views = ['dashboard', 'projects', 'profile', 'experience', 'history', 'diagnostics', 'settings'];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) el.style.display = (v === tabId) ? 'block' : 'none';
  });

  if (tabId === 'dashboard') renderDashboard();
  if (tabId === 'projects') renderProjects();
  if (tabId === 'profile') renderProfileForm();
  if (tabId === 'experience') renderExperienceView();
  if (tabId === 'history') loadHistoryView();
  if (tabId === 'diagnostics') runDiagnosticsView();
}

// ──────────────────────────────────────────
// Views
// ──────────────────────────────────────────

function renderDashboard() {
  if (!currentData) return;
  document.getElementById('stat-projects').textContent = (currentData.projects || []).length;
  document.getElementById('stat-exp').textContent = (currentData.experience || []).length;
  document.getElementById('stat-edu').textContent = (currentData.education || []).length;
  
  // Trigger lightweight health metric
  fetch('/api/admin/diagnostics')
    .then(r => r.json())
    .then(d => {
      document.getElementById('stat-health').textContent = `${d.healthScore || 100}%`;
      document.getElementById('stat-issues').textContent = d.counts ? d.counts.totalIssues : 0;
    })
    .catch(() => {});
}

function renderProjects() {
  const listElem = document.getElementById('projects-table-body');
  if (!listElem || !currentData) return;

  const projects = currentData.projects || [];
  listElem.innerHTML = projects.map((p, idx) => `
    <tr>
      <td style="font-weight: 600;">${escapeHtml(p.title)}</td>
      <td style="font-family: var(--font-mono); font-size: 0.8rem;">${escapeHtml(p.slug)}</td>
      <td><span style="font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; background: rgba(56,189,248,0.15); color: #38bdf8;">${escapeHtml(p.status || 'Active')}</span></td>
      <td>${p.year || ''}</td>
      <td>
        <button onclick="editProject(${idx})" class="btn-admin btn-admin-outline" style="padding: 4px 8px; font-size: 0.78rem;">Edit</button>
        <button onclick="moveProject(${idx}, -1)" class="btn-admin btn-admin-outline" style="padding: 4px 6px; font-size: 0.78rem;">↑</button>
        <button onclick="moveProject(${idx}, 1)" class="btn-admin btn-admin-outline" style="padding: 4px 6px; font-size: 0.78rem;">↓</button>
        <button onclick="deleteProject(${idx})" class="btn-admin btn-admin-danger" style="padding: 4px 8px; font-size: 0.78rem;">Delete</button>
      </td>
    </tr>
  `).join('');
}

function openAddProjectModal() {
  editingProjectIndex = -1;
  document.getElementById('project-modal-title').textContent = 'Add New Project';
  document.getElementById('proj-form').reset();
  document.getElementById('proj-status').value = 'Completed';
  document.getElementById('project-modal').style.display = 'flex';
}

function editProject(idx) {
  editingProjectIndex = idx;
  const p = currentData.projects[idx];
  document.getElementById('project-modal-title').textContent = `Edit Project: ${p.title}`;

  document.getElementById('proj-title').value = p.title || '';
  document.getElementById('proj-slug').value = p.slug || '';
  document.getElementById('proj-category').value = p.category || '';
  document.getElementById('proj-year').value = p.year || '';
  document.getElementById('proj-status').value = p.status || 'Completed';
  document.getElementById('proj-role').value = p.role || '';
  document.getElementById('proj-contribution').value = p.contribution || '';
  document.getElementById('proj-short-desc').value = p.shortDescription || '';
  document.getElementById('proj-full-desc').value = p.fullDescription || '';
  document.getElementById('proj-technologies').value = (p.technologies || []).join(', ');
  document.getElementById('proj-tools').value = (p.tools || []).join(', ');
  document.getElementById('proj-tags').value = (p.tags || []).join(', ');
  document.getElementById('proj-github').value = p.github || '';
  document.getElementById('proj-demo').value = p.demo || '';
  document.getElementById('proj-images').value = (p.images || []).join(', ');
  document.getElementById('proj-documents').value = (p.documents || []).join(', ');
  document.getElementById('proj-objectives').value = (p.objectives || []).join('\n');
  document.getElementById('proj-approach').value = p.approach || '';
  document.getElementById('proj-implementation').value = p.implementation || '';
  document.getElementById('proj-challenges').value = (p.challenges || []).join('\n');
  document.getElementById('proj-results').value = p.results || '';
  document.getElementById('proj-lessons').value = p.lessonsLearned || '';
  document.getElementById('proj-related').value = (p.relatedProjects || []).join(', ');

  document.getElementById('project-modal').style.display = 'flex';
}

function closeProjectModal() {
  document.getElementById('project-modal').style.display = 'none';
}

function handleSaveProject(e) {
  e.preventDefault();
  const title = document.getElementById('proj-title').value.trim();
  const slug = document.getElementById('proj-slug').value.trim();

  if (!title || !slug) {
    alert('Project Title and Slug are required.');
    return;
  }

  const projectObj = {
    id: editingProjectIndex >= 0 ? currentData.projects[editingProjectIndex].id : `proj-${Date.now()}`,
    title,
    slug,
    category: document.getElementById('proj-category').value.trim(),
    year: parseInt(document.getElementById('proj-year').value) || new Date().getFullYear(),
    status: document.getElementById('proj-status').value,
    role: document.getElementById('proj-role').value.trim(),
    contribution: document.getElementById('proj-contribution').value.trim(),
    shortDescription: document.getElementById('proj-short-desc').value.trim(),
    fullDescription: document.getElementById('proj-full-desc').value.trim(),
    technologies: document.getElementById('proj-technologies').value.split(',').map(s => s.trim()).filter(Boolean),
    tools: document.getElementById('proj-tools').value.split(',').map(s => s.trim()).filter(Boolean),
    tags: document.getElementById('proj-tags').value.split(',').map(s => s.trim()).filter(Boolean),
    github: document.getElementById('proj-github').value.trim(),
    demo: document.getElementById('proj-demo').value.trim(),
    images: document.getElementById('proj-images').value.split(',').map(s => s.trim()).filter(Boolean),
    documents: document.getElementById('proj-documents').value.split(',').map(s => s.trim()).filter(Boolean),
    objectives: document.getElementById('proj-objectives').value.split('\n').map(s => s.trim()).filter(Boolean),
    approach: document.getElementById('proj-approach').value.trim(),
    implementation: document.getElementById('proj-implementation').value.trim(),
    challenges: document.getElementById('proj-challenges').value.split('\n').map(s => s.trim()).filter(Boolean),
    results: document.getElementById('proj-results').value.trim(),
    lessonsLearned: document.getElementById('proj-lessons').value.trim(),
    relatedProjects: document.getElementById('proj-related').value.split(',').map(s => s.trim()).filter(Boolean)
  };

  if (!currentData.projects) currentData.projects = [];

  if (editingProjectIndex >= 0) {
    currentData.projects[editingProjectIndex] = projectObj;
  } else {
    currentData.projects.push(projectObj);
  }

  closeProjectModal();
  saveContent(`Updated project: ${projectObj.title}`);
}

function deleteProject(idx) {
  const p = currentData.projects[idx];
  if (confirm(`Are you sure you want to delete project "${p.title}"?`)) {
    currentData.projects.splice(idx, 1);
    saveContent(`Deleted project: ${p.title}`);
  }
}

function moveProject(idx, dir) {
  const target = idx + dir;
  if (target < 0 || target >= currentData.projects.length) return;
  const temp = currentData.projects[idx];
  currentData.projects[idx] = currentData.projects[target];
  currentData.projects[target] = temp;
  saveContent(`Reordered projects`);
}

// ──────────────────────────────────────────
// Profile Editor
// ──────────────────────────────────────────
function renderProfileForm() {
  if (!currentData || !currentData.profile) return;
  const p = currentData.profile;

  document.getElementById('prof-name').value = p.name || '';
  document.getElementById('prof-identity').value = p.identity || '';
  document.getElementById('prof-tagline').value = p.tagline || '';
  document.getElementById('prof-intro').value = p.shortIntro || '';
  document.getElementById('prof-bio').value = p.fullBio || '';
  document.getElementById('prof-email').value = p.email || '';
  document.getElementById('prof-location').value = p.location || '';
  document.getElementById('prof-status').value = p.status || '';

  const links = p.links || {};
  document.getElementById('prof-github').value = links.github || '';
  document.getElementById('prof-scholar').value = links.scholar || '';
  document.getElementById('prof-linkedin').value = links.linkedin || '';
  document.getElementById('prof-orcid').value = links.orcid || '';
}

function handleSaveProfile(e) {
  e.preventDefault();
  currentData.profile.name = document.getElementById('prof-name').value.trim();
  currentData.profile.identity = document.getElementById('prof-identity').value.trim();
  currentData.profile.tagline = document.getElementById('prof-tagline').value.trim();
  currentData.profile.shortIntro = document.getElementById('prof-intro').value.trim();
  currentData.profile.fullBio = document.getElementById('prof-bio').value.trim();
  currentData.profile.email = document.getElementById('prof-email').value.trim();
  currentData.profile.location = document.getElementById('prof-location').value.trim();
  currentData.profile.status = document.getElementById('prof-status').value.trim();

  currentData.profile.links = {
    github: document.getElementById('prof-github').value.trim(),
    scholar: document.getElementById('prof-scholar').value.trim(),
    linkedin: document.getElementById('prof-linkedin').value.trim(),
    orcid: document.getElementById('prof-orcid').value.trim()
  };

  saveContent('Updated Profile information');
}

// ──────────────────────────────────────────
// Experience & Education
// ──────────────────────────────────────────
function renderExperienceView() {
  const expContainer = document.getElementById('exp-list-admin');
  const eduContainer = document.getElementById('edu-list-admin');

  if (expContainer) {
    const exp = currentData.experience || [];
    expContainer.innerHTML = exp.map((item, idx) => `
      <div style="padding: 14px; background: #0f172a; border: 1px solid var(--admin-border); border-radius: 6px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <div style="font-weight: 700;">${escapeHtml(item.role)}</div>
          <div style="color: var(--admin-accent); font-size: 0.88rem;">${escapeHtml(item.organization)} · ${escapeHtml(item.period)}</div>
          <div style="color: var(--admin-muted); font-size: 0.85rem; margin-top: 4px;">${escapeHtml(item.description)}</div>
        </div>
        <button onclick="deleteExperience(${idx})" class="btn-admin btn-admin-danger" style="padding: 3px 8px; font-size: 0.75rem;">Delete</button>
      </div>
    `).join('');
  }

  if (eduContainer) {
    const edu = currentData.education || [];
    eduContainer.innerHTML = edu.map((item, idx) => `
      <div style="padding: 14px; background: #0f172a; border: 1px solid var(--admin-border); border-radius: 6px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <div style="font-weight: 700;">${escapeHtml(item.degree)}</div>
          <div style="color: var(--admin-accent); font-size: 0.88rem;">${escapeHtml(item.institution)} · ${escapeHtml(item.period)}</div>
          ${item.focus ? `<div style="color: var(--admin-muted); font-size: 0.85rem;">Focus: ${escapeHtml(item.focus)}</div>` : ''}
        </div>
        <button onclick="deleteEducation(${idx})" class="btn-admin btn-admin-danger" style="padding: 3px 8px; font-size: 0.75rem;">Delete</button>
      </div>
    `).join('');
  }
}

function deleteExperience(idx) {
  if (confirm('Delete this experience entry?')) {
    currentData.experience.splice(idx, 1);
    saveContent('Deleted Experience item');
  }
}

function deleteEducation(idx) {
  if (confirm('Delete this education entry?')) {
    currentData.education.splice(idx, 1);
    saveContent('Deleted Education item');
  }
}

function addExperiencePrompt() {
  const role = prompt('Role / Title (e.g. Graduate Research Assistant):');
  if (!role) return;
  const org = prompt('Organization / University:');
  const period = prompt('Period (e.g. 2024 — Present):');
  const desc = prompt('Short description of responsibilities:');

  if (!currentData.experience) currentData.experience = [];
  currentData.experience.push({
    id: `exp-${Date.now()}`,
    role,
    organization: org || '',
    period: period || '',
    location: '',
    description: desc || '',
    highlights: []
  });

  saveContent(`Added experience: ${role}`);
}

function addEducationPrompt() {
  const degree = prompt('Degree (e.g. Master of Science in Computer Science):');
  if (!degree) return;
  const inst = prompt('Institution (University):');
  const period = prompt('Period (e.g. 2024 — 2026):');

  if (!currentData.education) currentData.education = [];
  currentData.education.push({
    id: `edu-${Date.now()}`,
    degree,
    institution: inst || '',
    period: period || '',
    location: '',
    focus: '',
    honors: ''
  });

  saveContent(`Added education: ${degree}`);
}

// ──────────────────────────────────────────
// Version History (Section 28 Compliance)
// ──────────────────────────────────────────
async function loadHistoryView() {
  const listElem = document.getElementById('history-list');
  if (!listElem) return;

  listElem.innerHTML = '<tr><td colspan="4" style="text-align: center;">Loading version snapshots...</td></tr>';

  try {
    const res = await fetch('/api/admin/history');
    const json = await res.json();
    const history = json.history || [];

    if (history.length === 0) {
      listElem.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--admin-muted);">No snapshots available yet. Snapshots are created automatically upon every save.</td></tr>';
      return;
    }

    listElem.innerHTML = history.map(snap => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.8rem;">${escapeHtml(snap.dateString)}</td>
        <td style="font-weight: 550;">${escapeHtml(snap.description)}</td>
        <td style="font-size: 0.82rem; color: var(--admin-muted);">
          ${snap.counts ? `${snap.counts.projects || 0} projects · ${snap.counts.experience || 0} exp` : 'Standard'}
        </td>
        <td>
          <button onclick="restoreVersion('${escapeHtml(snap.filename)}')" class="btn-admin btn-admin-primary" style="padding: 4px 10px; font-size: 0.78rem;">
            Restore This Version
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    listElem.innerHTML = `<tr><td colspan="4" style="color: #ef4444;">Error: ${err.message}</td></tr>`;
  }
}

async function restoreVersion(filename) {
  if (!confirm(`Are you sure you want to restore snapshot "${filename}"?\n\nThe current state will be automatically backed up before restoring.`)) {
    return;
  }

  try {
    const res = await fetch('/api/admin/history/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename })
    });
    const json = await res.json();
    if (res.ok && json.success) {
      showToast('Version restored successfully.');
      loadData();
    } else {
      alert('Restore failed: ' + (json.error || 'Unknown error'));
    }
  } catch (err) {
    alert('Restore error: ' + err.message);
  }
}

// ──────────────────────────────────────────
// Portfolio Health / Diagnostics (Section 36 Compliance)
// ──────────────────────────────────────────
async function runDiagnosticsView() {
  const container = document.getElementById('diagnostics-output');
  if (!container) return;

  container.innerHTML = '<p style="color: var(--admin-muted);">Executing comprehensive diagnostic audit...</p>';

  try {
    const res = await fetch('/api/admin/diagnostics');
    const report = await res.json();

    const scoreColor = report.healthScore >= 90 ? '#10b981' : report.healthScore >= 70 ? '#f59e0b' : '#ef4444';

    let html = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; padding: 20px; background: #0f172a; border: 1px solid var(--admin-border); border-radius: 8px;">
        <div>
          <div style="font-size: 0.85rem; font-family: var(--font-mono); color: var(--admin-muted); text-transform: uppercase;">Overall Health Score</div>
          <div style="font-size: 2.2rem; font-weight: 800; color: ${scoreColor};">${report.healthScore}%</div>
          <div style="font-size: 0.85rem; color: var(--admin-muted);">${report.checksPassed} of ${report.totalChecks} systemic checks verified</div>
        </div>
        <div style="display: flex; gap: 16px;">
          <div style="text-align: right;">
            <div style="color: #ef4444; font-weight: 700; font-size: 1.1rem;">${report.counts.errors}</div>
            <div style="font-size: 0.75rem; color: var(--admin-muted);">Errors</div>
          </div>
          <div style="text-align: right;">
            <div style="color: #f59e0b; font-weight: 700; font-size: 1.1rem;">${report.counts.warnings}</div>
            <div style="font-size: 0.75rem; color: var(--admin-muted);">Warnings</div>
          </div>
          <div style="text-align: right;">
            <div style="color: #38bdf8; font-weight: 700; font-size: 1.1rem;">${report.counts.info}</div>
            <div style="font-size: 0.75rem; color: var(--admin-muted);">Placeholders / Info</div>
          </div>
        </div>
      </div>
    `;

    if (report.issues.length === 0) {
      html += `
        <div class="issue-card issue-info">
          <div>✓ All systemic audits passed. Zero errors, broken references, or unreplaced placeholders.</div>
        </div>
      `;
    } else {
      html += report.issues.map(iss => {
        const typeClass = `issue-${iss.severity}`;
        return `
          <div class="issue-card ${typeClass}">
            <span style="font-family: var(--font-mono); font-weight: 700; font-size: 0.78rem; text-transform: uppercase;">[${iss.category}]</span>
            <div>${escapeHtml(iss.message)}</div>
          </div>
        `;
      }).join('');
    }

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<p style="color: #ef4444;">Diagnostic audit failed: ${err.message}</p>`;
  }
}

// ──────────────────────────────────────────
// Settings: Change Passcode
// ──────────────────────────────────────────
async function handleChangePasscode(e) {
  e.preventDefault();
  const newPass = document.getElementById('new-passcode').value;
  const confirmPass = document.getElementById('confirm-passcode').value;
  const msgElem = document.getElementById('passcode-msg');

  if (newPass !== confirmPass) {
    msgElem.textContent = 'Passcodes do not match.';
    msgElem.style.color = '#ef4444';
    return;
  }

  try {
    const res = await fetch('/api/admin/change-passcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ newPasscode: newPass })
    });
    const json = await res.json();
    if (res.ok && json.success) {
      msgElem.textContent = 'Passcode updated successfully.';
      msgElem.style.color = '#10b981';
      document.getElementById('new-passcode').value = '';
      document.getElementById('confirm-passcode').value = '';
    } else {
      msgElem.textContent = json.error || 'Failed to update passcode';
      msgElem.style.color = '#ef4444';
    }
  } catch (err) {
    msgElem.textContent = 'Error: ' + err.message;
    msgElem.style.color = '#ef4444';
  }
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

document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
  document.getElementById('login-form').addEventListener('submit', handleLogin);
});
