/**
 * UAV Construction Monitor — Professional Platform JS
 * v2.0 — Project-Centric Architecture
 *
 * AppState → Router → ProjectManager → InspectionManager →
 * AnalysisPipeline → NotificationManager → UI utilities
 */

'use strict';

/* ══════════════════════════════════════════════════════════════
   CONFIG
   ══════════════════════════════════════════════════════════════ */
const API_BASE = '/api/v1';
const APP_VERSION = '2.0.0';

/* ══════════════════════════════════════════════════════════════
   STATE
   ══════════════════════════════════════════════════════════════ */
const State = {
  currentPage:       'dashboard',
  currentTab:        'overview',
  currentAiTab:      'levir',
  currentProject:    null,   // full project object
  currentInspection: null,   // full inspection object
  projects:          [],
  inspections:       [],
  notifications:     [],
  galleryPage:       1,
  galleryFilter:     'all',
  levirSplit:        'train',
  levirPage:         1,
  roboSplit:         'train',
  roboPage:          1,
  sidebarOpen:       true,
  lightMode:         false,
  apiOnline:         false,
  scurveChart:       null,
  timelineChart:     null,
  uploadQueue:       [],
};

/* ══════════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  const savedSidebar = localStorage.getItem('sidebarOpen');
  State.sidebarOpen = savedSidebar !== null ? savedSidebar === 'true' : true;

  initParticles();
  initSidebar();
  initTheme();
  initTopbar();
  initModals();
  initUploadZone();
  initWorkspaceTabs();
  initAiModelTabs();
  initMobile();
  checkAPIHealth();
  loadDashboard();
  
  updateSidebarState();

  window.addEventListener('resize', () => {
    updateSidebarState();
  });

  setInterval(checkAPIHealth, 30000);
});

/* ══════════════════════════════════════════════════════════════
   PARTICLES
   ══════════════════════════════════════════════════════════════ */
function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  for (let i = 0; i < 60; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      a: Math.random() * 0.5 + 0.1,
    });
  }

  (function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0,212,255,${p.a})`;
      ctx.fill();
    });
    requestAnimationFrame(animate);
  })();
}

/* ══════════════════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════════════════ */
function updateSidebarState() {
  const isMobile = window.innerWidth <= 768;
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobile-overlay');

  if (isMobile) {
    document.body.classList.remove('sidebar-collapsed');
    sidebar?.classList.remove('collapsed');
    
    if (State.sidebarOpen) {
      document.body.classList.add('mobile-sidebar-open');
      sidebar?.classList.add('mobile-open');
      overlay?.classList.add('visible');
    } else {
      document.body.classList.remove('mobile-sidebar-open');
      sidebar?.classList.remove('mobile-open');
      overlay?.classList.remove('visible');
    }
  } else {
    document.body.classList.remove('mobile-sidebar-open');
    sidebar?.classList.remove('mobile-open');
    overlay?.classList.remove('visible');

    if (State.sidebarOpen) {
      document.body.classList.remove('sidebar-collapsed');
      sidebar?.classList.remove('collapsed');
    } else {
      document.body.classList.add('sidebar-collapsed');
      sidebar?.classList.add('collapsed');
    }
  }

  // Toggler button accessibility
  const toggleBtn = document.getElementById('sidebar-toggle');
  if (toggleBtn) {
    toggleBtn.setAttribute('aria-expanded', State.sidebarOpen);
  }

  // Persist state in localStorage
  localStorage.setItem('sidebarOpen', State.sidebarOpen);
}

function initSidebar() {
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const workspaceToggle = document.getElementById('nav-workspace-toggle');
  const workspaceHeader = document.getElementById('nav-workspace-header');
  const workspaceMenu = document.getElementById('nav-workspace-menu');

  // Sidebar expanded / collapsed toggle
  sidebarToggle?.addEventListener('click', () => {
    State.sidebarOpen = !State.sidebarOpen;
    updateSidebarState();
  });

  // Workspace subnav menu expand / collapse toggle
  const toggleWorkspaceMenu = () => {
    const isExpanded = workspaceToggle?.getAttribute('aria-expanded') === 'true';
    const nextState = !isExpanded;
    workspaceToggle?.setAttribute('aria-expanded', nextState);
    workspaceMenu?.classList.toggle('submenu-collapsed', !nextState);
  };

  workspaceToggle?.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleWorkspaceMenu();
  });
  workspaceHeader?.addEventListener('click', () => {
    toggleWorkspaceMenu();
  });

  // Level 1: Page Nav Items
  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      navigate(item.dataset.page);
    });

    item.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        navigate(item.dataset.page);
      }
    });
  });

  // Level 2: Workspace Tab Nav Items
  document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      if (State.currentProject) {
        switchTab(item.dataset.tab);
      } else {
        toast('warning', 'No Active Project', 'Please select a project from the Projects page first.');
      }
    });

    item.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (State.currentProject) {
          switchTab(item.dataset.tab);
        } else {
          toast('warning', 'No Active Project', 'Please select a project from the Projects page first.');
        }
      }
    });
  });
}

function updateSidebarActiveState() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    item.removeAttribute('aria-current');
  });

  if (State.currentPage === 'workspace') {
    // Highlight the active L2 subnav tab
    const activeL2 = document.querySelector(`.nav-item[data-tab="${State.currentTab}"]`);
    if (activeL2) {
      activeL2.classList.add('active');
      activeL2.setAttribute('aria-current', 'page');
    }
  } else {
    // Highlight the active L1 main nav page
    const activeL1 = document.querySelector(`.nav-item[data-page="${State.currentPage}"]`);
    if (activeL1) {
      activeL1.classList.add('active');
      activeL1.setAttribute('aria-current', 'page');
    }
  }
}

/* ══════════════════════════════════════════════════════════════
   THEME
   ══════════════════════════════════════════════════════════════ */
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'light') applyTheme(true);
}

function applyTheme(light) {
  State.lightMode = light;
  document.body.classList.toggle('light-mode', light);
  const iconDark  = document.getElementById('theme-icon-dark');
  const iconLight = document.getElementById('theme-icon-light');
  if (iconDark)  iconDark.style.display  = light ? 'none' : '';
  if (iconLight) iconLight.style.display = light ? ''     : 'none';
  localStorage.setItem('theme', light ? 'light' : 'dark');
}

function initTopbar() {
  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    applyTheme(!State.lightMode);
  });

  document.getElementById('notif-btn')?.addEventListener('click', () => {
    document.getElementById('notif-panel')?.classList.toggle('open');
  });

  document.querySelectorAll('#btn-new-project, #btn-new-project-2, #btn-create-first').forEach(el => {
    el.addEventListener('click', () => openNewProjectModal());
  });
}

function closeNotifPanel() {
  document.getElementById('notif-panel')?.classList.remove('open');
}

/* ══════════════════════════════════════════════════════════════
   MOBILE
   ══════════════════════════════════════════════════════════════ */
function initMobile() {
  const menuBtn   = document.getElementById('mobile-menu-btn');
  const overlay   = document.getElementById('mobile-overlay');

  menuBtn?.addEventListener('click', () => {
    State.sidebarOpen = true;
    updateSidebarState();
  });

  overlay?.addEventListener('click', () => {
    State.sidebarOpen = false;
    updateSidebarState();
  });
}

/* ══════════════════════════════════════════════════════════════
   ROUTER / NAVIGATION
   ══════════════════════════════════════════════════════════════ */
function navigate(page) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

  // Show page
  const pageEl = document.getElementById(`page-${page}`);
  if (pageEl) pageEl.classList.add('active');

  State.currentPage = page;

  // Manage L2 Workspace submenu visibility based on active project existence
  const wsContainer = document.getElementById('nav-workspace');
  if (wsContainer) {
    if (State.currentProject) {
      wsContainer.style.display = 'block';
      wsContainer.setAttribute('aria-hidden', 'false');
    } else {
      wsContainer.style.display = 'none';
      wsContainer.setAttribute('aria-hidden', 'true');
    }
  }

  // Update sidebar active highlights
  updateSidebarActiveState();

  // Sync breadcrumbs and page titles
  updateBreadcrumb(page);
  updatePageTitle(page);

  // Load page data
  switch (page) {
    case 'dashboard':  loadDashboard();    break;
    case 'projects':   loadProjectsList(); break;
    case 'activity':   loadActivityLog();  break;
    case 'ai-models':  loadLevirDataset(); loadLogs(); break;
    case 'sys-settings':
      const apiStatusUrl = document.getElementById('sys-api-url');
      if (apiStatusUrl) apiStatusUrl.textContent = window.location.origin + API_BASE;
      break;
  }

  // Close mobile menu on navigate
  State.sidebarOpen = window.innerWidth > 768 ? State.sidebarOpen : false;
  updateSidebarState();
}

function openWorkspace(project) {
  State.currentProject = project;

  // Sync L2 Sidebar project details
  const wsProjName = document.getElementById('sidebar-project-name');
  if (wsProjName) wsProjName.textContent = project.name;

  const wsContainer = document.getElementById('nav-workspace');
  if (wsContainer) {
    wsContainer.style.display = 'block';
    wsContainer.setAttribute('aria-hidden', 'false');
  }

  // Ensure menu expanded on workspace entry
  const workspaceToggle = document.getElementById('nav-workspace-toggle');
  const workspaceMenu = document.getElementById('nav-workspace-menu');
  if (workspaceToggle) workspaceToggle.setAttribute('aria-expanded', 'true');
  if (workspaceMenu) workspaceMenu.classList.remove('submenu-collapsed');

  navigate('workspace');
  updateWorkspaceHeader(project);
  switchTab(State.currentTab || 'overview');
  loadWorkspaceOverview(project);
  loadInspectionsList(project.project_id);
  loadProjectImages(project.project_id);

  // Populate settings tab
  populateProjectSettings(project);
}

function switchTab(tab) {
  if (!State.currentProject) return;

  State.currentPage = 'workspace';
  State.currentTab = tab;

  // Show page workspace
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const pageEl = document.getElementById('page-workspace');
  if (pageEl) pageEl.classList.add('active');

  // Toggle active class on workspace tabs (top tabs inside workspace page)
  document.querySelectorAll('.workspace-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tab);
  });

  // Toggle active class on workspace tab panels
  document.querySelectorAll('.tab-panel').forEach(p => {
    // Some tabs might map differently or directly
    const targetId = `tab-${tab}`;
    p.classList.toggle('active', p.id === targetId);
  });

  // Update L2 active state in sidebar
  updateSidebarActiveState();

  // Sync breadcrumbs and page title
  updateBreadcrumb('workspace');

  const tabLabels = {
    overview:      'Overview',
    inspections:   'Inspections',
    images:        'Drone Images',
    analysis:      'AI Analysis',
    timeline:      'Progress Timeline',
    reports:       'Reports',
    'proj-settings': 'Project Settings'
  };

  const el = document.getElementById('page-title');
  if (el) el.textContent = `${State.currentProject.name} — ${tabLabels[tab] || tab}`;

  if (tab === 'timeline') initTimelineTab();
  if (tab === 'reports')  loadReportsTab();
}

function updateBreadcrumb(page) {
  const breadcrumb = document.getElementById('breadcrumb');
  if (!breadcrumb) return;

  const labels = {
    dashboard:    'Dashboard',
    projects:     'Projects',
    activity:     'Activity Log',
    'ai-models':  'AI Models',
    'sys-settings': 'System Settings',
  };

  const tabLabels = {
    overview:      'Overview',
    inspections:   'Inspections',
    images:        'Drone Images',
    analysis:      'AI Analysis',
    timeline:      'Progress Timeline',
    reports:       'Reports',
    'proj-settings': 'Project Settings'
  };

  if (page === 'workspace' && State.currentProject) {
    const tabName = tabLabels[State.currentTab] || 'Overview';
    breadcrumb.innerHTML = `
      <a href="#" onclick="navigate('dashboard')">Home</a>
      <span class="sep">›</span>
      <a href="#" onclick="navigate('projects')">Projects</a>
      <span class="sep">›</span>
      <a href="#" onclick="openWorkspace(State.projects.find(p => p.project_id === '${State.currentProject.project_id}') || State.currentProject)">${escHtml(State.currentProject.name)}</a>
      <span class="sep">›</span>
      <span class="current" id="breadcrumb-current">${tabName}</span>
    `;
  } else {
    const pageName = labels[page] || page;
    breadcrumb.innerHTML = `
      <a href="#" onclick="navigate('dashboard')">Home</a>
      <span class="sep">›</span>
      <span class="current" id="breadcrumb-current">${pageName}</span>
    `;
  }
}

function updatePageTitle(page) {
  const labels = {
    dashboard:    'Dashboard',
    projects:     'Projects',
    workspace:    State.currentProject?.name || 'Project Workspace',
    activity:     'Activity Log',
    'ai-models':  'AI Models',
    'sys-settings': 'System Settings',
  };
  const tabLabels = {
    overview:      'Overview',
    inspections:   'Inspections',
    images:        'Drone Images',
    analysis:      'AI Analysis',
    timeline:      'Progress Timeline',
    reports:       'Reports',
    'proj-settings': 'Project Settings'
  };

  const el = document.getElementById('page-title');
  if (el) {
    if (page === 'workspace' && State.currentProject) {
      el.textContent = `${State.currentProject.name} — ${tabLabels[State.currentTab] || 'Overview'}`;
    } else {
      el.textContent = labels[page] || page;
    }
  }
}

/* ══════════════════════════════════════════════════════════════
   API HELPERS
   ══════════════════════════════════════════════════════════════ */
async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  const json = await res.json().catch(() => ({ success: false, message: `HTTP ${res.status}` }));
  return { ok: res.ok, status: res.status, ...json };
}

async function checkAPIHealth() {
  const dot  = document.getElementById('api-status-dot');
  const text = document.getElementById('api-status-text');
  const sys  = document.getElementById('sys-api-status');
  try {
    const r = await apiFetch('/health');
    State.apiOnline = r.success;
    if (dot)  { dot.className = 'status-dot'; dot.style.background = 'var(--green)'; }
    if (text) text.textContent = 'Connected';
    if (sys)  sys.textContent  = '🟢 Online';
  } catch {
    State.apiOnline = false;
    if (dot)  { dot.className = 'status-dot error'; }
    if (text) text.textContent = 'Offline';
    if (sys)  sys.textContent  = '🔴 Offline';
  }
}

/* ══════════════════════════════════════════════════════════════
   DASHBOARD
   ══════════════════════════════════════════════════════════════ */
async function loadDashboard() {
  // Load platform stats
  try {
    const r = await apiFetch('/stats');
    if (r.success && r.data) {
      const d = r.data;
      setText('dash-total-projects',    d.total_projects || 0);
      setText('dash-total-inspections', d.total_inspections || 0);
      setText('dash-total-images',      d.total_images || 0);
      setText('dash-avg-progress',      d.avg_progress ? `${d.avg_progress}%` : '—');
    }
  } catch (e) { /* silent */ }

  // Load projects for grid
  await loadDashboardProjects();

  // Load activity
  await loadDashboardActivity();
}

async function loadDashboardProjects() {
  const r = await apiFetch('/projects');
  if (!r.success) return;
  const projects = (r.data?.projects || []).slice(0, 6);
  State.projects = r.data?.projects || [];
  renderDashboardProjects(projects);
}

function renderDashboardProjects(projects) {
  const el = document.getElementById('dash-projects-grid');
  if (!el) return;

  if (!projects.length) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-icon">🏗️</div>
      <h3>No Projects Yet</h3>
      <p>Create your first construction monitoring project to get started.</p>
      <button class="btn btn-primary" onclick="openNewProjectModal()">Create Project</button>
    </div>`;
    return;
  }

  el.innerHTML = `<div class="projects-grid">${projects.map(p => renderProjectCard(p)).join('')}</div>`;
}

function renderProjectCard(p) {
  const progress = p.progress_score ? Math.min(100, Math.round(p.progress_score)) : 0;
  const statusColor = { active: 'badge-green', 'on-hold': 'badge-amber', completed: 'badge-purple', archived: 'badge-ghost' };
  const riskColor   = { low: 'badge-green', medium: 'badge-amber', high: 'badge-red', critical: 'badge-red' };
  const status = p.status || 'active';
  const risk   = p.risk_level || '';

  return `<div class="project-card" onclick="openWorkspace(${JSON.stringify(p).replace(/"/g, '&quot;')})">
    <div class="project-card-top">
      <div>
        <div class="project-card-name">${escHtml(p.name)}</div>
        <div class="project-card-location">📍 ${escHtml(p.location || 'No location')}</div>
      </div>
      <div class="flex" style="gap:6px;flex-direction:column;align-items:flex-end">
        <span class="badge ${statusColor[status] || 'badge-ghost'}">${status}</span>
        ${risk ? `<span class="badge ${riskColor[risk] || 'badge-ghost'}">${risk} risk</span>` : ''}
      </div>
    </div>
    <div class="project-card-meta">
      <div class="project-meta-item"><strong>${p.image_count || 0}</strong> Images</div>
      <div class="project-meta-item"><strong>${p.inspection_count || 0}</strong> Inspections</div>
      <div class="project-meta-item"><strong>${progress}%</strong> Progress</div>
    </div>
    <div class="project-progress-bar">
      <div class="project-progress-fill" style="width:${progress}%"></div>
    </div>
    <div class="project-card-bottom">
      <span class="text-xs text-muted">${formatDate(p.updated_at)}</span>
      <div class="project-card-actions">
        <button class="btn btn-ghost btn-sm btn-icon" onclick="event.stopPropagation();openEditProjectModal(${JSON.stringify(p).replace(/"/g, '&quot;')})" title="Edit">✏️</button>
        <button class="btn btn-ghost btn-sm btn-icon" onclick="event.stopPropagation();confirmDeleteProject(${JSON.stringify(p.project_id).replace(/"/g, '&quot;')})" title="Delete">🗑️</button>
      </div>
    </div>
  </div>`;
}

async function loadDashboardActivity() {
  const el = document.getElementById('dash-activity-list');
  try {
    const r = await apiFetch('/activity?limit=8');
    if (r.success && r.data.events?.length) {
      el.innerHTML = r.data.events.map(e => renderActivityItem(e)).join('');
    }
  } catch { /* silent */ }
}

function renderActivityItem(e) {
  const icons = { upload: '📤', analyze: '🤖', create: '✅', delete: '🗑️', report: '📄', inspection: '📅' };
  const type  = e.event_type || 'create';
  return `<div class="activity-item">
    <div class="activity-dot ${type}"><span>${icons[type] || '●'}</span></div>
    <div class="activity-content">
      <div class="activity-desc">${escHtml(e.description)}</div>
      <div class="activity-time">${formatDate(e.timestamp)}</div>
    </div>
  </div>`;
}

/* ══════════════════════════════════════════════════════════════
   PROJECTS LIST
   ══════════════════════════════════════════════════════════════ */
async function loadProjectsList() {
  const r = await apiFetch('/projects');
  if (!r.success) return;
  State.projects = r.data?.projects || [];
  renderProjectsList(State.projects);

  // Populate activity filter
  const actFilter = document.getElementById('activity-filter-project');
  if (actFilter) {
    const opts = State.projects.map(p => `<option value="${p.project_id}">${escHtml(p.name)}</option>`).join('');
    actFilter.innerHTML = `<option value="">All Projects</option>${opts}`;
  }
}

function renderProjectsList(projects) {
  const grid = document.getElementById('projects-grid');
  if (!grid) return;

  if (!projects.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <div class="empty-icon">🏗️</div>
      <h3>No Projects Found</h3>
      <p>Create your first project to start monitoring construction progress.</p>
      <button class="btn btn-primary" onclick="openNewProjectModal()">Create Project</button>
    </div>`;
    return;
  }

  grid.innerHTML = projects.map(p => renderProjectCard(p)).join('');
}

// Search + filter
document.getElementById('projects-search')?.addEventListener('input', filterProjects);
document.getElementById('projects-filter-status')?.addEventListener('change', filterProjects);

function filterProjects() {
  const q      = (document.getElementById('projects-search')?.value || '').toLowerCase();
  const status = document.getElementById('projects-filter-status')?.value || '';
  const filtered = State.projects.filter(p => {
    const matchQ = !q || p.name.toLowerCase().includes(q) || (p.location || '').toLowerCase().includes(q);
    const matchS = !status || p.status === status;
    return matchQ && matchS;
  });
  renderProjectsList(filtered);
}

/* ══════════════════════════════════════════════════════════════
   WORKSPACE HEADER / OVERVIEW
   ══════════════════════════════════════════════════════════════ */
function updateWorkspaceHeader(project) {
  setText('ws-project-name', project.name);
  setText('ws-project-location', `📍 ${project.location || 'No location'}`);
  const badge = document.getElementById('ws-status-badge');
  if (badge) {
    const colorMap = { active: 'badge-green', 'on-hold': 'badge-amber', completed: 'badge-purple', archived: 'badge-ghost' };
    badge.className = `badge ${colorMap[project.status] || 'badge-green'} badge-dot`;
    badge.textContent = project.status || 'active';
  }
  // Update page title & breadcrumb
  document.getElementById('page-title').textContent = project.name;
  document.getElementById('breadcrumb-current').textContent = project.name;
}

async function loadWorkspaceOverview(project) {
  const p = project;
  const progress = p.progress_score ? Math.min(100, Math.round(p.progress_score)) : 0;

  // KPI cards
  setText('ov-inspections', p.inspection_count || 0);
  setText('ov-images',      p.image_count || 0);
  setText('ov-progress',    progress ? `${progress}%` : '—');
  setText('ov-risk',        p.risk_level || '—');

  // Progress gauge arc
  const arc = document.getElementById('ov-gauge-arc');
  const txt = document.getElementById('ov-gauge-text');
  if (arc && txt) {
    const pct    = progress / 100;
    const total  = 251; // half-circle circumference
    const offset = total - pct * total;
    arc.style.strokeDashoffset = offset;
    txt.textContent = `${progress}%`;
  }

  // Details
  setText('ov-delay',          p.delay_days != null ? `${p.delay_days} days` : '—');
  setText('ov-confidence',     p.confidence ? `${Math.round(p.confidence * 100)}%` : '—');
  setText('ov-last-inspection', formatDate(p.updated_at));
  setText('ov-last-analysis',   formatDate(p.last_analysis_at));
  setText('ov-description',    p.description || '—');
  setText('ov-location',       p.location || '—');
  setText('ov-type',           p.project_type || '—');
  setText('ov-start-date',     p.start_date || '—');
  setText('ov-duration',       p.planned_duration ? `${p.planned_duration} days` : '—');
  setText('ov-status-val',     p.status || 'active');

  const schedBadge = document.getElementById('ov-schedule-badge');
  if (schedBadge) {
    const delay = p.delay_days || 0;
    if (delay <= 0) { schedBadge.className = 'badge badge-green'; schedBadge.textContent = 'On Track'; }
    else if (delay <= 14) { schedBadge.className = 'badge badge-amber'; schedBadge.textContent = 'At Risk'; }
    else { schedBadge.className = 'badge badge-red'; schedBadge.textContent = `${delay}d Delay`; }
  }

  // Load inspection count for tab badge
  await loadInspectionCount(p.project_id);
}

async function loadInspectionCount(projectId) {
  const r = await apiFetch(`/projects/${projectId}/inspections`);
  if (r.success) {
    const n = r.data?.total || 0;
    const countEl = document.getElementById('tab-count-inspections');
    if (countEl) countEl.textContent = n;
    const ovEl = document.getElementById('ov-inspections');
    if (ovEl) ovEl.textContent = n;

    // Sync sidebar inspections badge
    const wsCountEl = document.getElementById('ws-count-inspections');
    if (wsCountEl) {
      wsCountEl.textContent = n;
      wsCountEl.classList.toggle('hidden', n === 0);
    }
  }
}

/* ══════════════════════════════════════════════════════════════
   INSPECTIONS
   ══════════════════════════════════════════════════════════════ */
async function loadInspectionsList(projectId) {
  const r = await apiFetch(`/projects/${projectId}/inspections`);
  if (!r.success) return;

  State.inspections = r.data?.inspections || [];
  const n = State.inspections.length;
  const countEl = document.getElementById('tab-count-inspections');
  if (countEl) countEl.textContent = n;

  // Sync sidebar inspections badge
  const wsCountEl = document.getElementById('ws-count-inspections');
  if (wsCountEl) {
    wsCountEl.textContent = n;
    wsCountEl.classList.toggle('hidden', n === 0);
  }

  renderInspectionsList(State.inspections);
  populateInspectionSelects(State.inspections);
}

function renderInspectionsList(inspections) {
  const el = document.getElementById('inspections-list');
  if (!el) return;

  if (!inspections.length) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-icon">📅</div>
      <h3>No Inspections Yet</h3>
      <p>Create your first inspection to start uploading drone images and running AI analysis.</p>
      <button class="btn btn-primary" onclick="openNewInspectionModal()">Create Inspection</button>
    </div>`;
    return;
  }

  const statusColor = { pending: 'badge-ghost', images_uploaded: 'badge-cyan', running: 'badge-amber', completed: 'badge-green', error: 'badge-red' };
  const statusLabel = { pending: 'Pending', images_uploaded: 'Images Ready', running: 'Analyzing…', completed: 'Complete', error: 'Error' };

  el.innerHTML = inspections.map(insp => {
    const st    = insp.analysis_status || 'pending';
    const prog  = insp.analysis_result?.progress_score || 0;
    return `<div class="inspection-item" onclick="selectInspection('${insp.inspection_id}')">
      <div class="inspection-icon">📅</div>
      <div class="inspection-info">
        <div class="inspection-name">${escHtml(insp.name)}</div>
        <div class="inspection-meta">${insp.date} · ${insp.inspector || 'No inspector'} · ${insp.weather || 'No weather'}</div>
        ${insp.description ? `<div class="inspection-meta text-xs">${escHtml(insp.description)}</div>` : ''}
      </div>
      <div class="inspection-stats">
        <div class="inspection-stat"><strong>${insp.image_count || 0}</strong><span>Images</span></div>
        <div class="inspection-stat"><strong>${prog ? prog + '%' : '—'}</strong><span>Progress</span></div>
      </div>
      <span class="badge ${statusColor[st] || 'badge-ghost'}">${statusLabel[st] || st}</span>
      <div class="inspection-actions">
        <button class="btn btn-primary btn-sm" onclick="event.stopPropagation();startAnalysis('${insp.inspection_id}')" title="Run Analysis">⚡ Analyze</button>
        <button class="btn btn-ghost btn-sm btn-icon" onclick="event.stopPropagation();confirmDeleteInspection('${insp.inspection_id}')" title="Delete">🗑️</button>
      </div>
    </div>`;
  }).join('');
}

function populateInspectionSelects(inspections) {
  const opts = `<option value="">— Select inspection —</option>` +
    inspections.map(i => `<option value="${i.inspection_id}">${escHtml(i.name)} (${i.date})</option>`).join('');

  const selectors = ['img-inspection-select', 'analysis-inspection-select'];
  selectors.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts;
  });
}

function selectInspection(inspectionId) {
  const insp = State.inspections.find(i => i.inspection_id === inspectionId);
  if (!insp) return;
  State.currentInspection = insp;

  // Switch to images tab and pre-select this inspection
  switchTab('images');
  const sel = document.getElementById('img-inspection-select');
  if (sel) sel.value = inspectionId;
  showImgUploadArea(true);
}

document.getElementById('img-inspection-select')?.addEventListener('change', function() {
  const id = this.value;
  if (id) {
    const insp = State.inspections.find(i => i.inspection_id === id);
    State.currentInspection = insp || null;
    showImgUploadArea(true);
  } else {
    showImgUploadArea(false);
  }
});

function showImgUploadArea(show) {
  document.getElementById('img-upload-area')?.classList.toggle('hidden', !show);
}

/* ══════════════════════════════════════════════════════════════
   PROJECT IMAGES
   ══════════════════════════════════════════════════════════════ */
async function loadProjectImages(projectId, page = 1) {
  const r = await apiFetch(`/projects/${projectId}/images?page=${page}&limit=20`);
  if (!r.success) return;

  const images = r.data?.images || [];
  const total  = r.data?.total || 0;
  const countEl = document.getElementById('tab-count-images');
  if (countEl) countEl.textContent = total;

  // Sync sidebar images badge
  const wsCountImgs = document.getElementById('ws-count-images');
  if (wsCountImgs) {
    wsCountImgs.textContent = total;
    wsCountImgs.classList.toggle('hidden', total === 0);
  }

  renderImageGallery(images, projectId);
}

function renderImageGallery(images, projectId) {
  const grid = document.getElementById('images-gallery');
  if (!grid) return;

  const filter = State.galleryFilter;
  const filtered = filter === 'all' ? images :
                   filter === 'accepted' ? images.filter(i => i.accepted) :
                   images.filter(i => !i.accepted);

  if (!filtered.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <div class="empty-icon">🖼️</div>
      <p>No ${filter !== 'all' ? filter + ' ' : ''}images found.</p>
    </div>`;
    return;
  }

  grid.innerHTML = filtered.map(img => {
    const previewUrl = `/api/v1/images/${projectId}/${img.image_id}/preview`;
    const accepted   = img.accepted;
    return `<div class="gallery-item" onclick="openImageDetail('${img.image_id}','${escHtml(img.filename || '')}','${projectId}')">
      <img src="${previewUrl}" alt="${escHtml(img.filename || '')}" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\\'gallery-placeholder\\'>🖼️</div>'" />
      <div class="gallery-item-badge">
        <span class="badge ${accepted ? 'badge-green' : 'badge-red'}">${accepted ? '✓' : '✗'}</span>
      </div>
      <div class="gallery-item-overlay">
        <div class="gallery-item-name">${escHtml(img.filename || '')}</div>
      </div>
    </div>`;
  }).join('');
}

// Gallery filters
document.querySelectorAll('#tab-images .filter-btn[data-filter]').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('#tab-images .filter-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    State.galleryFilter = this.dataset.filter;
    if (State.currentProject) {
      loadProjectImages(State.currentProject.project_id);
    }
  });
});

function openImageDetail(imageId, filename, projectId) {
  const img = document.getElementById('img-detail-src');
  const title = document.getElementById('img-detail-title');
  if (img)   img.src = `/api/v1/images/${projectId}/${imageId}/preview`;
  if (title) title.textContent = filename || 'Image Detail';
  openModal('modal-image');
}

/* ══════════════════════════════════════════════════════════════
   UPLOAD ZONE
   ══════════════════════════════════════════════════════════════ */
function initUploadZone() {
  const zone      = document.getElementById('upload-zone');
  const fileInput = document.getElementById('file-input');
  const uploadBtn = document.getElementById('btn-upload');

  if (!zone) return;

  zone.addEventListener('click', () => fileInput?.click());
  zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop',      e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    handleFiles(Array.from(e.dataTransfer.files));
  });

  fileInput?.addEventListener('change', () => handleFiles(Array.from(fileInput.files)));
  uploadBtn?.addEventListener('click', uploadImages);

  // Global drag-and-drop overlay
  const dropOverlay = document.getElementById('drop-overlay');
  document.addEventListener('dragover',  e => { e.preventDefault(); dropOverlay?.classList.add('visible'); });
  document.addEventListener('dragleave', e => { if (!e.relatedTarget) dropOverlay?.classList.remove('visible'); });
  document.addEventListener('drop',      e => {
    e.preventDefault();
    dropOverlay?.classList.remove('visible');
    if (State.currentPage === 'workspace' && State.currentInspection) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  });

  document.getElementById('btn-clear-queue')?.addEventListener('click', clearQueue);
}

function handleFiles(files) {
  const allowed = ['.jpg', '.jpeg', '.png', '.tiff', '.tif'];
  State.uploadQueue = files.filter(f => {
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    return allowed.includes(ext);
  });
  renderFileQueue();
}

function renderFileQueue() {
  const queue    = State.uploadQueue;
  const queueDiv = document.getElementById('file-queue');
  const listDiv  = document.getElementById('file-list');
  const countEl  = document.getElementById('queue-count');
  const controls = document.getElementById('upload-controls');
  const btn      = document.getElementById('btn-upload');

  if (!queue.length) {
    if (queueDiv) queueDiv.style.display = 'none';
    if (controls) controls.style.display = 'none';
    return;
  }

  if (queueDiv) queueDiv.style.display = 'block';
  if (controls) controls.style.display = 'block';
  if (countEl)  countEl.textContent = `${queue.length} file${queue.length !== 1 ? 's' : ''} selected`;
  if (btn)      btn.disabled = false;

  if (listDiv) {
    listDiv.innerHTML = queue.map((f, i) => `
      <div class="file-item" id="fitem-${i}">
        <span class="file-item-name">📄 ${escHtml(f.name)}</span>
        <span class="file-item-size">${formatBytes(f.size)}</span>
        <button class="file-item-remove" onclick="removeFile(${i})" title="Remove">✕</button>
      </div>`).join('');
  }
}

function removeFile(idx) {
  State.uploadQueue.splice(idx, 1);
  renderFileQueue();
}

function clearQueue() {
  State.uploadQueue = [];
  document.getElementById('file-queue').style.display   = 'none';
  document.getElementById('upload-controls').style.display = 'none';
  const fi = document.getElementById('file-input');
  if (fi) fi.value = '';
}

async function uploadImages() {
  if (!State.currentProject)    return toast('error', 'No project selected');
  if (!State.currentInspection) return toast('error', 'Please select an inspection first');
  if (!State.uploadQueue.length) return toast('error', 'No files queued');

  const pid  = State.currentProject.project_id;
  const iid  = State.currentInspection.inspection_id;
  const btn  = document.getElementById('btn-upload');
  const prog = document.getElementById('upload-progress');
  const bar  = document.getElementById('progress-bar');
  const lbl  = document.getElementById('upload-progress-label');

  btn.disabled = true;
  btn.textContent = 'Uploading...';
  if (prog) prog.style.display = 'block';
  if (bar)  bar.style.width = '10%';
  if (lbl)  lbl.textContent = 'Uploading images...';

  const formData = new FormData();
  State.uploadQueue.forEach(f => formData.append('images', f));

  try {
    if (bar) bar.style.width = '40%';
    const res = await fetch(`${API_BASE}/projects/${pid}/inspections/${iid}/upload`, {
      method: 'POST', body: formData
    });
    if (bar) bar.style.width = '80%';
    const data = await res.json();

    if (data.success) {
      if (bar) bar.style.width = '100%';
      if (lbl) lbl.textContent = `✅ Upload complete!`;
      toast('success', 'Upload Complete', `${data.data.uploaded} images uploaded, ${data.data.processed} processed`);

      // Show quality results
      if (data.data.quality_report) {
        renderQualityReport(data.data.quality_report);
      }

      // Refresh data
      clearQueue();
      await loadProjectImages(pid);
      await loadInspectionsList(pid);

      // Update inspection state
      const updatedInsp = State.inspections.find(i => i.inspection_id === iid);
      if (updatedInsp) State.currentInspection = updatedInsp;

    } else {
      if (lbl) lbl.textContent = `❌ Upload failed`;
      toast('error', 'Upload Failed', data.message);
    }
  } catch (e) {
    if (lbl) lbl.textContent = `❌ Network error`;
    toast('error', 'Upload Error', e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg> Upload & Validate Images`;
    setTimeout(() => { if (prog) prog.style.display = 'none'; }, 2000);
  }
}

function renderQualityReport(report) {
  const card    = document.getElementById('quality-results-card');
  const content = document.getElementById('quality-checks-content');
  const badge   = document.getElementById('quality-overall-badge');
  if (!card || !content) return;

  card.classList.remove('hidden');
  const accepted = report.accepted_count || 0;
  const total    = report.total_count || 1;
  const pct      = Math.round((accepted / total) * 100);

  if (badge) {
    badge.textContent = `${pct}% Passed`;
    badge.className   = pct >= 70 ? 'badge badge-green' : pct >= 40 ? 'badge badge-amber' : 'badge badge-red';
  }

  const checks = [
    { name: 'Total Uploaded', value: total, cls: 'pass', icon: '📁' },
    { name: 'Accepted',       value: accepted, cls: 'pass', icon: '✅' },
    { name: 'Rejected',       value: report.rejected_count || 0, cls: (report.rejected_count || 0) > 0 ? 'fail' : 'pass', icon: '❌' },
  ];

  content.innerHTML = checks.map(c => `
    <div class="quality-check ${c.cls}">
      <span class="quality-check-icon">${c.icon}</span>
      <span class="quality-check-name">${c.name}</span>
      <span class="quality-check-value">${c.value}</span>
    </div>`).join('');
}

/* ══════════════════════════════════════════════════════════════
   AI ANALYSIS PIPELINE
   ══════════════════════════════════════════════════════════════ */
function initWorkspaceTabs() {
  document.querySelectorAll('.workspace-tab[data-tab]').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  document.getElementById('btn-run-analysis')?.addEventListener('click', () => {
    const inspId = document.getElementById('analysis-inspection-select')?.value;
    if (!inspId) { toast('warning', 'Select Inspection', 'Please select an inspection to analyze'); return; }
    startAnalysis(inspId);
  });

  document.getElementById('analysis-inspection-select')?.addEventListener('change', function() {
    const insp = State.inspections.find(i => i.inspection_id === this.value);
    if (insp?.analysis_status === 'completed') {
      showExistingAnalysisResults(insp);
    }
  });
}

async function startAnalysis(inspectionId) {
  if (!State.currentProject) return;

  const pid    = State.currentProject.project_id;
  const insp   = State.inspections.find(i => i.inspection_id === inspectionId);
  if (!insp)   return toast('error', 'Inspection not found');

  // Switch to analysis tab
  switchTab('analysis');

  // Set select
  const sel = document.getElementById('analysis-inspection-select');
  if (sel) sel.value = inspectionId;

  // Read config
  const planned = parseInt(document.getElementById('cfg-planned-duration')?.value || 365);
  const start   = document.getElementById('cfg-start-date')?.value || new Date().toISOString().slice(0, 10);
  const limit   = parseInt(document.getElementById('cfg-limit')?.value || 10);
  const wC      = parseInt(document.getElementById('cfg-w-change')?.value   || 40) / 100;
  const wA      = parseInt(document.getElementById('cfg-w-activity')?.value || 30) / 100;
  const wT      = parseInt(document.getElementById('cfg-w-temporal')?.value || 20) / 100;
  const wQ      = parseInt(document.getElementById('cfg-w-quality')?.value  || 10) / 100;

  // Show stepper
  const stepper = document.getElementById('analysis-stepper');
  const results = document.getElementById('analysis-results');
  const empty   = document.getElementById('analysis-empty');
  if (stepper) stepper.style.display = 'flex';
  if (results) results.style.display = 'none';
  if (empty)   empty.style.display   = 'none';

  // Reset stepper
  ['preprocessing', 'detection', 'change', 'prediction', 'xai'].forEach(s => {
    setPipelineStep(s, 'pending');
  });

  // Animate first step
  setPipelineStep('preprocessing', 'running', 'Extracting features...');

  const btn = document.getElementById('btn-run-analysis');
  if (btn) { btn.disabled = true; btn.textContent = '⚡ Running...'; }

  toast('info', 'Analysis Started', `Running full AI pipeline for ${insp.name}...`);

  try {
    // Animate steps as we go — we'll update after we get the response
    const animInterval = animatePipelineSteps(['preprocessing', 'detection', 'change', 'prediction', 'xai']);

    const r = await apiFetch(`/projects/${pid}/inspections/${inspectionId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({
        planned_duration: planned,
        start_date:       start,
        limit:            limit,
        w_change:         wC,
        w_activity:       wA,
        w_temporal:       wT,
        w_quality:        wQ,
      }),
    });

    clearInterval(animInterval);

    if (r.success) {
      const stages = r.data?.stages || {};

      // Update stepper from real results
      const stageMap = { preprocessing: stages.processing, detection: stages.detection, change: stages.change_detection, prediction: stages.prediction, xai: stages.xai };
      Object.entries(stageMap).forEach(([step, stage]) => {
        if (stage) setPipelineStep(step, stage.status === 'done' ? 'done' : stage.status === 'warning' ? 'done' : 'done', '✓');
      });

      // Refresh inspection data
      await loadInspectionsList(pid);
      const updatedInsp = State.inspections.find(i => i.inspection_id === inspectionId);

      // Show results
      setTimeout(() => {
        if (results) results.style.display = 'flex';
        if (stepper) stepper.style.display = 'none';
        renderAnalysisResults(r.data, updatedInsp);
        toast('success', 'Analysis Complete', 'All AI modules completed successfully!');
      }, 800);

      // Update overview tab
      if (updatedInsp) {
        const refreshedProj = State.projects.find(p => p.project_id === pid);
        if (refreshedProj) {
          const pr = await apiFetch(`/projects/${pid}`);
          if (pr.success) {
            State.currentProject = pr.data;
            loadWorkspaceOverview(pr.data);
          }
        }
      }

    } else {
      ['preprocessing', 'detection', 'change', 'prediction', 'xai'].forEach(s => setPipelineStep(s, 'error'));
      toast('error', 'Analysis Failed', r.message);
      if (empty) empty.style.display = 'flex';
      if (stepper) stepper.style.display = 'none';
    }
  } catch (e) {
    ['preprocessing', 'detection', 'change', 'prediction', 'xai'].forEach(s => setPipelineStep(s, 'error'));
    toast('error', 'Analysis Error', e.message);
    if (stepper) stepper.style.display = 'none';
    if (empty)   empty.style.display   = 'flex';
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/></svg> Run Complete AI Analysis Pipeline`;
    }
  }
}

function animatePipelineSteps(steps) {
  let idx = 0;
  return setInterval(() => {
    if (idx > 0) setPipelineStep(steps[idx - 1], 'done', '✓');
    if (idx < steps.length) setPipelineStep(steps[idx], 'running', 'Processing...');
    idx++;
    if (idx > steps.length) clearInterval();
  }, 1500);
}

function setPipelineStep(step, status, statusText) {
  const el = document.getElementById(`pstep-${step}`);
  if (!el) return;
  el.className = `pipeline-step ${status}`;
  const statusEl = el.querySelector('.pstep-status');
  if (statusEl) statusEl.textContent = statusText || (status === 'done' ? 'Done' : status === 'running' ? 'Running...' : '—');

  // Replace emoji for done/running
  const circle = el.querySelector('.pstep-circle');
  if (circle && status === 'done')    circle.textContent = '✅';
  if (circle && status === 'running') circle.innerHTML   = '<span class="spinning">⚙️</span>';
  if (circle && status === 'error')   circle.textContent = '❌';
}

function renderAnalysisResults(data, insp) {
  const stages = data?.stages || {};
  const pred   = stages.prediction || {};
  const det    = stages.detection  || {};
  const chg    = stages.change_detection || {};
  const xai    = stages.xai       || {};

  // Progress & schedule
  const progress = Math.round((pred.progress_score || 0) * 100);
  const delay    = pred.delay_days || 0;
  setText('res-progress',   `${progress}%`);
  setText('res-delay',      delay ? `${delay} days` : 'On Track');
  setText('res-confidence', pred.confidence ? `${Math.round(pred.confidence * 100)}%` : '—');
  setText('res-risk',       pred.risk_level || '—');

  const schedBadge = document.getElementById('res-schedule-badge');
  if (schedBadge) {
    if (delay <= 0) { schedBadge.className = 'badge badge-green result-card-status'; schedBadge.textContent = 'On Track'; }
    else if (delay <= 14) { schedBadge.className = 'badge badge-amber result-card-status'; schedBadge.textContent = 'At Risk'; }
    else { schedBadge.className = 'badge badge-red result-card-status'; schedBadge.textContent = `${delay}d Delay`; }
  }

  // Detection
  setText('res-detections',    det.detections || 0);
  setText('res-compliance',    det.avg_compliance ? `${Math.round(det.avg_compliance)}%` : '—');
  setText('res-detect-images', det.images || 0);

  const detectBadge = document.getElementById('res-detect-badge');
  if (detectBadge && det.status) {
    detectBadge.textContent = det.status === 'done' ? 'Done' : 'Warning';
    detectBadge.className   = `badge ${det.status === 'done' ? 'badge-cyan' : 'badge-amber'} result-card-status`;
  }

  // Change detection
  const avgChange = chg.avg_change ? `${Math.round(chg.avg_change * 10) / 10}%` : '—';
  setText('res-avg-change',    avgChange);
  setText('res-pairs-analyzed', chg.pairs || 0);

  // XAI
  if (xai.report_url) {
    const dlBtn = document.getElementById('res-download-report');
    if (dlBtn) dlBtn.href = xai.report_url;
  }
  const xaiBadge = document.getElementById('res-xai-badge');
  if (xaiBadge) {
    const done = xai.status === 'done' || xai.report_html;
    xaiBadge.textContent = done ? 'Done' : 'Info';
    xaiBadge.className   = `badge ${done ? 'badge-purple' : 'badge-ghost'} result-card-status`;
  }

  // GradCAM heatmaps — try to load them
  if (State.currentProject) {
    loadHeatmaps(State.currentProject.project_id);
  }
}

async function loadHeatmaps(projectId) {
  const grid = document.getElementById('res-heatmap-grid');
  if (!grid) return;

  const r = await apiFetch(`/projects/${projectId}/xai/status`);
  if (r.success && r.data.gradcam?.images?.length) {
    const imgs = r.data.gradcam.images.slice(0, 4);
    grid.innerHTML = imgs.map(fname =>
      `<div class="heatmap-item">
        <img class="heatmap-img" src="/api/v1/module6/${projectId}/gradcam/${fname}" alt="GradCAM Heatmap" onerror="this.parentElement.remove()" />
        <div class="heatmap-label">${fname.replace('_gradcam_overlay.png','')}</div>
      </div>`
    ).join('');
  }
}

function showExistingAnalysisResults(insp) {
  const result  = insp.analysis_result || {};
  const stepper = document.getElementById('analysis-stepper');
  const results = document.getElementById('analysis-results');
  const empty   = document.getElementById('analysis-empty');

  if (!Object.keys(result).length) { if (empty) empty.style.display = 'flex'; return; }

  if (stepper) stepper.style.display = 'none';
  if (results) results.style.display = 'flex';
  if (empty)   empty.style.display   = 'none';

  const progress = Math.round((result.progress_score || 0) * 100);
  const delay    = result.delay_days || 0;
  setText('res-progress',      `${progress}%`);
  setText('res-delay',         delay ? `${delay} days` : 'On Track');
  setText('res-confidence',    result.confidence ? `${Math.round(result.confidence * 100)}%` : '—');
  setText('res-risk',          result.risk_level || '—');
  setText('res-detections',    result.total_detections || 0);
  setText('res-compliance',    result.avg_compliance ? `${Math.round(result.avg_compliance)}%` : '—');
}

/* ══════════════════════════════════════════════════════════════
   TIMELINE TAB
   ══════════════════════════════════════════════════════════════ */
function initTimelineTab() {
  renderInspectionTimeline();
  tryLoadSCurve();
}

function renderInspectionTimeline() {
  const el = document.getElementById('inspection-timeline');
  if (!el) return;
  const inspections = State.inspections;
  if (!inspections.length) {
    el.innerHTML = `<div class="empty-state" style="padding:24px"><p>No inspections yet.</p></div>`;
    return;
  }
  el.innerHTML = [...inspections].reverse().map((insp, i) => {
    const isDone    = insp.analysis_status === 'completed';
    const isCurrent = i === inspections.length - 1;
    return `<div class="timeline-item ${isDone ? 'done' : isCurrent ? 'current' : ''}">
      <div class="timeline-dot"></div>
      <div class="timeline-label">${escHtml(insp.name)}</div>
      <div class="timeline-date">${insp.date}</div>
      <div class="timeline-desc">${insp.image_count || 0} images · ${insp.analysis_status}</div>
    </div>`;
  }).join('');
}

async function tryLoadSCurve() {
  if (!State.currentProject) return;
  const pid = State.currentProject.project_id;
  const r   = await apiFetch(`/projects/${pid}/predict/status`).catch(() => ({ success: false }));

  // If module 5 data available, draw the chart
  if (r.success && r.data?.processed) {
    drawSCurve(r.data);
  } else {
    // Draw demo S-curve
    drawDemoSCurve();
  }
}

function drawDemoSCurve() {
  const canvas = document.getElementById('timeline-scurve-chart');
  const empty  = document.getElementById('timeline-empty');
  if (!canvas) return;

  const project = State.currentProject;
  if (!project) { if (empty) empty.style.display = 'flex'; return; }

  canvas.style.display = 'block';
  if (empty) empty.style.display = 'none';

  const labels   = Array.from({length: 12}, (_, i) => `Month ${i + 1}`);
  const planned  = labels.map((_, i) => Math.round(100 * (1 - Math.exp(-0.4 * (i + 1)))));
  const progress = project.progress_score || 0;
  const actual   = labels.map((_, i) => {
    const val = Math.round(progress * (i + 1) / labels.length * 2);
    return Math.min(progress, val);
  });

  if (State.scurveChart) State.scurveChart.destroy();
  const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() || '#8892AA';

  State.scurveChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Planned', data: planned, borderColor: '#00D4FF', fill: false, tension: 0.4, pointRadius: 3 },
        { label: 'Actual',  data: actual,  borderColor: '#F59E0B', fill: false, tension: 0.4, pointRadius: 3 },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100, ticks: { callback: v => `${v}%`, color: textColor }, grid: { color: 'rgba(255,255,255,0.05)' } },
        x: { ticks: { color: textColor }, grid: { color: 'rgba(255,255,255,0.05)' } },
      },
    },
  });
}

/* ══════════════════════════════════════════════════════════════
   REPORTS TAB
   ══════════════════════════════════════════════════════════════ */
async function loadReportsTab() {
  const el = document.getElementById('reports-list');
  if (!el) return;

  const completedInspections = State.inspections.filter(i => i.analysis_status === 'completed');
  if (!completedInspections.length) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-icon">📄</div><h3>No Reports Yet</h3>
      <p>Run AI Analysis to automatically generate inspection reports.</p>
      <button class="btn btn-primary" onclick="switchTab('analysis')">Run Analysis</button>
    </div>`;
    return;
  }

  el.innerHTML = completedInspections.map(insp => {
    const res = insp.analysis_result || {};
    const progress = Math.round((res.progress_score || 0) * 100);
    return `<div class="report-card">
      <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border)">
        <div>
          <div style="font-size:15px;font-weight:700;margin-bottom:4px">📄 ${escHtml(insp.name)}</div>
          <div style="font-size:12px;color:var(--text-secondary)">${insp.date} · AI Analysis Complete</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <span class="badge badge-green">Completed</span>
          <button class="btn btn-secondary btn-sm" onclick="viewReport('${insp.inspection_id}')">View Report</button>
          <a class="btn btn-ghost btn-sm" href="${res.report_url || '#'}" target="_blank" title="Download XAI HTML">📥</a>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-bottom:1px solid var(--border)">
        ${[
          ['Progress', `${progress}%`, 'text-cyan'],
          ['Delay', res.delay_days ? `${res.delay_days}d` : 'On Track', res.delay_days > 0 ? 'text-red' : 'text-green'],
          ['Risk', res.risk_level || '—', ''],
          ['Confidence', res.confidence ? `${Math.round(res.confidence * 100)}%` : '—', ''],
        ].map(([label, val, cls]) => `<div style="padding:14px;text-align:center;border-right:1px solid var(--border)">
          <div style="font-size:20px;font-weight:800" class="${cls}">${val}</div>
          <div style="font-size:11px;color:var(--text-muted)">${label}</div>
        </div>`).join('')}
      </div>
    </div>`;
  }).join('');
}

async function viewReport(inspectionId) {
  if (!State.currentProject) return;
  const pid = State.currentProject.project_id;
  const r   = await apiFetch(`/projects/${pid}/inspections/${inspectionId}/report`);

  if (!r.success) { toast('error', 'Report unavailable', r.message); return; }

  const report = r.data;
  const body   = document.getElementById('report-modal-body');
  const title  = document.getElementById('report-modal-title');

  if (title) title.textContent = `Report — ${escHtml(report.project_name)} (${report.inspection_date})`;

  const dlBtn = document.getElementById('btn-download-report-html');
  if (dlBtn) dlBtn.href = report.xai_report_url || '#';

  if (body) {
    const es = report.executive_summary || {};
    const cs = report.construction_status || {};
    const sc = report.safety_compliance || {};
    body.innerHTML = `
      <div class="report-section">
        <div class="report-section-title">Executive Summary</div>
        <div class="grid-4" style="gap:12px;margin-bottom:12px">
          ${[
            ['Progress', `${Math.round(es.progress_pct || 0)}%`, 'text-cyan'],
            ['Delay', es.delay_days ? `${es.delay_days} days` : 'On Track', es.delay_days > 0 ? 'text-amber' : 'text-green'],
            ['Risk', es.risk_level || '—', ''],
            ['Confidence', es.ai_confidence ? `${Math.round(es.ai_confidence * 100)}%` : '—', ''],
          ].map(([l, v, c]) => `<div class="kpi-card"><div class="kpi-value ${c}">${v}</div><div class="kpi-label">${l}</div></div>`).join('')}
        </div>
      </div>
      <div class="report-section">
        <div class="report-section-title">✅ Completed Work</div>
        <div class="report-list">${(cs.completed_work || []).map(w => `<div class="report-list-item">${escHtml(w)}</div>`).join('')}</div>
      </div>
      <div class="report-section">
        <div class="report-section-title">🔨 In Progress</div>
        <div class="report-list">${(cs.in_progress || []).map(w => `<div class="report-list-item">${escHtml(w)}</div>`).join('')}</div>
      </div>
      <div class="report-section">
        <div class="report-section-title">⏳ Pending</div>
        <div class="report-list">${(cs.pending || []).map(w => `<div class="report-list-item">${escHtml(w)}</div>`).join('')}</div>
      </div>
      <div class="report-section">
        <div class="report-section-title">🛡️ Safety Compliance</div>
        <div style="font-size:13px;color:var(--text-secondary)">Score: <strong>${Math.round(sc.score || 0)}%</strong> · Violations: <strong>${sc.violations || 0}</strong></div>
      </div>
      <div class="report-section">
        <div class="report-section-title">💡 AI Recommendations</div>
        <div class="report-list">${(report.recommendations || []).map(r => `<div class="report-list-item">${escHtml(r)}</div>`).join('')}</div>
      </div>`;
  }

  openModal('modal-report');
}

/* ══════════════════════════════════════════════════════════════
   PROJECT CRUD MODALS
   ══════════════════════════════════════════════════════════════ */
function openNewProjectModal() {
  const idEl  = document.getElementById('modal-project-id');
  const title = document.getElementById('modal-project-title');
  const btn   = document.getElementById('btn-save-project');

  if (idEl)  idEl.value = '';
  if (title) title.textContent = 'Create New Project';
  if (btn)   btn.textContent   = 'Create Project';

  // Clear form
  ['modal-project-name','modal-project-description','modal-project-location',
   'modal-project-client','modal-project-contractor'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  const dateEl = document.getElementById('modal-project-start');
  if (dateEl) dateEl.value = new Date().toISOString().slice(0, 10);
  const durEl = document.getElementById('modal-project-duration');
  if (durEl) durEl.value = '365';

  openModal('modal-project');
}

function openEditProjectModal(project) {
  const p = project || State.currentProject;
  if (!p) return;

  const idEl  = document.getElementById('modal-project-id');
  const title = document.getElementById('modal-project-title');
  const btn   = document.getElementById('btn-save-project');

  if (idEl)  idEl.value = p.project_id;
  if (title) title.textContent = 'Edit Project';
  if (btn)   btn.textContent   = 'Save Changes';

  setValue('modal-project-name',        p.name        || '');
  setValue('modal-project-description', p.description || '');
  setValue('modal-project-location',    p.location    || '');
  setValue('modal-project-type',        p.project_type || 'residential');
  setValue('modal-project-start',       p.start_date   || '');
  setValue('modal-project-duration',    p.planned_duration || 365);
  setValue('modal-project-client',      p.client       || '');
  setValue('modal-project-contractor',  p.contractor   || '');

  openModal('modal-project');
}

function initModals() {
  document.getElementById('btn-save-project')?.addEventListener('click', saveProject);
  document.getElementById('btn-save-inspection')?.addEventListener('click', saveInspection);
  document.getElementById('btn-save-proj-settings')?.addEventListener('click', saveProjectSettings);
}

async function saveProject() {
  const id   = document.getElementById('modal-project-id')?.value;
  const name = document.getElementById('modal-project-name')?.value?.trim();
  if (!name) { toast('error', 'Name required', 'Project name cannot be empty'); return; }

  const body = {
    name,
    description:     document.getElementById('modal-project-description')?.value || '',
    location:        document.getElementById('modal-project-location')?.value || '',
    project_type:    document.getElementById('modal-project-type')?.value || 'residential',
    start_date:      document.getElementById('modal-project-start')?.value || '',
    planned_duration: parseInt(document.getElementById('modal-project-duration')?.value || 365),
    client:          document.getElementById('modal-project-client')?.value || '',
    contractor:      document.getElementById('modal-project-contractor')?.value || '',
  };

  const btn = document.getElementById('btn-save-project');
  if (btn) btn.disabled = true;

  try {
    let r;
    if (id) {
      r = await apiFetch(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
    } else {
      r = await apiFetch('/projects', { method: 'POST', body: JSON.stringify(body) });
    }

    if (r.success) {
      closeModal('modal-project');
      toast('success', id ? 'Project Updated' : 'Project Created', `"${name}" ${id ? 'updated' : 'created'} successfully`);
      await loadProjectsList();
      await loadDashboard();

      if (!id) {
        // Open the new project workspace
        openWorkspace(r.data);
        navigate('workspace');
      } else if (State.currentProject?.project_id === id) {
        State.currentProject = { ...State.currentProject, ...body };
        updateWorkspaceHeader(State.currentProject);
        loadWorkspaceOverview(State.currentProject);
      }
    } else {
      toast('error', 'Save Failed', r.message);
    }
  } catch (e) {
    toast('error', 'Error', e.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

function confirmDeleteProject(projectId) {
  const pid = projectId || State.currentProject?.project_id;
  if (!pid) return;

  const proj = State.projects.find(p => p.project_id === pid) || State.currentProject;
  showConfirm('Delete Project', `Are you sure you want to delete "${proj?.name || 'this project'}"? This action cannot be undone.`, '🗑️',
    async () => {
      const r = await apiFetch(`/projects/${pid}`, { method: 'DELETE' });
      if (r.success) {
        toast('success', 'Project Deleted');
        closeModal('modal-confirm');
        navigate('projects');
        await loadProjectsList();
        await loadDashboard();
      } else {
        toast('error', 'Delete Failed', r.message);
      }
    });
}

/* ══════════════════════════════════════════════════════════════
   INSPECTION MODALS
   ══════════════════════════════════════════════════════════════ */
function openNewInspectionModal() {
  if (!State.currentProject) { toast('warning', 'No Project', 'Please select a project first'); return; }
  setValue('modal-insp-name',      `Inspection ${new Date().toLocaleDateString()}`);
  setValue('modal-insp-date',      new Date().toISOString().slice(0, 10));
  setValue('modal-insp-weather',   'clear');
  setValue('modal-insp-inspector', '');
  setValue('modal-insp-desc',      '');
  openModal('modal-inspection');
}

async function saveInspection() {
  if (!State.currentProject) return;
  const pid = State.currentProject.project_id;
  const btn = document.getElementById('btn-save-inspection');

  const body = {
    name:        document.getElementById('modal-insp-name')?.value || '',
    date:        document.getElementById('modal-insp-date')?.value || new Date().toISOString().slice(0, 10),
    weather:     document.getElementById('modal-insp-weather')?.value || 'clear',
    inspector:   document.getElementById('modal-insp-inspector')?.value || '',
    description: document.getElementById('modal-insp-desc')?.value || '',
  };

  if (btn) btn.disabled = true;
  try {
    const r = await apiFetch(`/projects/${pid}/inspections`, { method: 'POST', body: JSON.stringify(body) });
    if (r.success) {
      closeModal('modal-inspection');
      toast('success', 'Inspection Created', `"${body.name}" created successfully`);
      await loadInspectionsList(pid);
      await loadWorkspaceOverview(State.currentProject);
      // Switch to images tab and select this inspection
      State.currentInspection = r.data;
      switchTab('images');
      const sel = document.getElementById('img-inspection-select');
      if (sel) { sel.value = r.data.inspection_id; showImgUploadArea(true); }
    } else {
      toast('error', 'Failed', r.message);
    }
  } catch (e) {
    toast('error', 'Error', e.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

function confirmDeleteInspection(inspectionId) {
  const insp = State.inspections.find(i => i.inspection_id === inspectionId);
  showConfirm('Delete Inspection', `Delete "${insp?.name || 'this inspection'}"?`, '📅',
    async () => {
      const r = await apiFetch(`/projects/${State.currentProject.project_id}/inspections/${inspectionId}`, { method: 'DELETE' });
      if (r.success) {
        toast('success', 'Inspection Deleted');
        closeModal('modal-confirm');
        await loadInspectionsList(State.currentProject.project_id);
      } else {
        toast('error', 'Delete Failed', r.message);
      }
    });
}

/* ══════════════════════════════════════════════════════════════
   PROJECT SETTINGS TAB
   ══════════════════════════════════════════════════════════════ */
function populateProjectSettings(project) {
  setValue('proj-settings-name',        project.name        || '');
  setValue('proj-settings-desc',        project.description || '');
  setValue('proj-settings-location',    project.location    || '');
  setValue('proj-settings-type',        project.project_type || 'residential');
  setValue('proj-settings-start',       project.start_date   || '');
  setValue('proj-settings-duration',    project.planned_duration || '');
  setValue('proj-settings-client',      project.client       || '');
  setValue('proj-settings-contractor',  project.contractor   || '');
  setValue('proj-settings-status',      project.status       || 'active');
}

async function saveProjectSettings() {
  if (!State.currentProject) return;
  const pid = State.currentProject.project_id;
  const body = {
    name:             document.getElementById('proj-settings-name')?.value,
    description:      document.getElementById('proj-settings-desc')?.value,
    location:         document.getElementById('proj-settings-location')?.value,
    project_type:     document.getElementById('proj-settings-type')?.value,
    start_date:       document.getElementById('proj-settings-start')?.value,
    planned_duration: parseInt(document.getElementById('proj-settings-duration')?.value || 365),
    client:           document.getElementById('proj-settings-client')?.value,
    contractor:       document.getElementById('proj-settings-contractor')?.value,
    status:           document.getElementById('proj-settings-status')?.value,
  };

  const r = await apiFetch(`/projects/${pid}`, { method: 'PATCH', body: JSON.stringify(body) });
  if (r.success) {
    State.currentProject = { ...State.currentProject, ...body };
    updateWorkspaceHeader(State.currentProject);
    toast('success', 'Settings Saved', 'Project updated successfully');
  } else {
    toast('error', 'Save Failed', r.message);
  }
}

/* ══════════════════════════════════════════════════════════════
   ACTIVITY LOG
   ══════════════════════════════════════════════════════════════ */
async function loadActivityLog() {
  const projectId = document.getElementById('activity-filter-project')?.value || '';
  const url = projectId ? `/activity?project_id=${projectId}&limit=100` : '/activity?limit=100';
  const r   = await apiFetch(url);
  const el  = document.getElementById('activity-full-list');
  if (!el) return;

  if (r.success && r.data.events?.length) {
    el.innerHTML = r.data.events.map(e => renderActivityItem(e)).join('');
  } else {
    el.innerHTML = `<div class="empty-state" style="padding:48px"><div class="empty-icon">📋</div><p>No activity recorded yet.</p></div>`;
  }
}

document.getElementById('activity-filter-project')?.addEventListener('change', loadActivityLog);

/* ══════════════════════════════════════════════════════════════
   AI MODELS PAGE (original module pages preserved)
   ══════════════════════════════════════════════════════════════ */
function initAiModelTabs() {
  document.querySelectorAll('#ai-model-tabs .workspace-tab[data-aitab]').forEach(tab => {
    tab.addEventListener('click', function() {
      document.querySelectorAll('#ai-model-tabs .workspace-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      document.querySelectorAll('[id^="aitab-"]').forEach(p => p.classList.remove('active'));
      const panel = document.getElementById(`aitab-${this.dataset.aitab}`);
      if (panel) panel.classList.add('active');
      State.currentAiTab = this.dataset.aitab;
      if (this.dataset.aitab === 'logs') loadLogs();
    });
  });

  // Logs buttons
  document.getElementById('btn-refresh-logs')?.addEventListener('click', loadLogs);
  document.getElementById('btn-clear-logs-view')?.addEventListener('click', () => {
    const t = document.getElementById('log-terminal');
    if (t) t.innerHTML = '';
  });
}

async function loadLevirDataset() {
  try {
    const r = await apiFetch('/datasets/levir');
    if (r.success) {
      const d = r.data;
      setText('levir-stat-total', d.total_pairs || 0);
      setText('levir-stat-train', d.splits?.train?.count || 0);
      setText('levir-stat-val',   d.splits?.val?.count   || 0);
      setText('levir-stat-test',  d.splits?.test?.count  || 0);
      loadLevirPairs('train');
    } else {
      toast('warning', 'LEVIR-CD', d.message || 'Dataset not available');
    }
  } catch (e) { toast('error', 'Error', e.message); }
}

async function loadLevirPairs(split) {
  const r = await apiFetch(`/datasets/levir/pairs?split=${split}&page=${State.levirPage}&limit=12`);
  if (!r.success) return;
  const grid = document.getElementById('levir-pairs-grid');
  const pag  = document.getElementById('levir-pagination');
  const pairs = r.data?.pairs || [];

  if (!pairs.length) {
    if (grid) grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><p>No pairs found for split: ${split}</p></div>`;
    return;
  }
  if (grid) {
    grid.innerHTML = pairs.map(pair => `
      <div class="gallery-item" style="aspect-ratio:16/9">
        <div class="gallery-placeholder" style="font-size:14px;text-align:center;padding:8px">
          <div style="font-size:10px;font-weight:600;margin-bottom:4px">${escHtml(pair.pair_id)}</div>
          <div style="font-size:10px;color:var(--text-muted)">Before / After Pair</div>
        </div>
      </div>`).join('');
  }
  if (pag) {
    const total = r.data?.total || 0;
    const pages = Math.ceil(total / 12);
    renderPagination(pag, State.levirPage, pages, p => { State.levirPage = p; loadLevirPairs(split); });
  }
}

function setLevirSplit(split, btn) {
  State.levirSplit = split;
  State.levirPage  = 1;
  document.querySelectorAll('[data-split]').forEach(b => b.classList.remove('active'));
  btn?.classList.add('active');
  loadLevirPairs(split);
}

async function processLevirBatch() {
  toast('info', 'Processing', 'Running LEVIR-CD batch processing...');
  const r = await apiFetch('/datasets/levir/process', { method: 'POST', body: JSON.stringify({ split: State.levirSplit, page: State.levirPage, limit: 3 }) });
  if (r.success) toast('success', 'Done', `Processed ${r.data?.results?.length || 0} pairs`);
  else toast('error', 'Failed', r.message);
}

async function loadRoboflowDataset() {
  const r = await apiFetch('/datasets/roboflow');
  if (!r.success) { toast('warning', 'Roboflow', r.message); return; }
  const d = r.data;
  const statsEl = document.getElementById('roboflow-stats');
  const classEl = document.getElementById('roboflow-classes');
  if (statsEl) statsEl.innerHTML = `
    <div class="detail-row"><span class="detail-key">Total Images</span><span class="detail-val">${d.total_images || 0}</span></div>
    <div class="detail-row"><span class="detail-key">Classes</span><span class="detail-val">${d.num_classes || 0}</span></div>
    ${Object.entries(d.splits || {}).map(([k, v]) => `<div class="detail-row"><span class="detail-key">${k}</span><span class="detail-val">${v.count || 0} images</span></div>`).join('')}`;
  if (classEl && d.classes) {
    classEl.innerHTML = d.classes.map(c => `<div class="detail-row"><span class="detail-key">${escHtml(c)}</span><span class="detail-val">${d.distribution?.[c] || 0}</span></div>`).join('');
  }
  loadRoboflowImages('train');
}

async function loadRoboflowImages(split) {
  const r = await apiFetch(`/datasets/roboflow/images?split=${split}&page=${State.roboPage}&limit=12`);
  if (!r.success) return;
  const grid = document.getElementById('roboflow-images-grid');
  const pag  = document.getElementById('roboflow-pagination');
  const imgs = r.data?.images || [];
  if (!imgs.length) { if (grid) grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><p>No images in ${split} split</p></div>`; return; }
  if (grid) {
    grid.innerHTML = imgs.map(img => `
      <div class="gallery-item">
        <div class="gallery-placeholder" style="font-size:10px;text-align:center;padding:4px">${escHtml(img.filename || 'Image')}</div>
      </div>`).join('');
  }
  if (pag) {
    const total = r.data?.total || 0;
    const pages = Math.ceil(total / 12);
    renderPagination(pag, State.roboPage, pages, p => { State.roboPage = p; loadRoboflowImages(split); });
  }
}

function setRoboSplit(split, btn) {
  State.roboSplit = split;
  State.roboPage  = 1;
  document.querySelectorAll('[data-rsplit]').forEach(b => b.classList.remove('active'));
  btn?.classList.add('active');
  loadRoboflowImages(split);
}

async function runUAVProcessing() {
  const pid   = document.getElementById('m2-project-select')?.value;
  const limit = document.getElementById('m2-limit')?.value || 10;
  if (!pid) { toast('warning', 'Select Project', 'Please select a project'); return; }
  toast('info', 'Processing', 'Running Module 2 processing pipeline...');
  const r = await apiFetch(`/projects/${pid}/process_module2`, { method: 'POST', body: JSON.stringify({ limit: parseInt(limit) }) });
  const el = document.getElementById('m2-results-content');
  if (r.success) {
    toast('success', 'Done', `Processed ${r.data.succeeded || 0}/${r.data.total || 0} images`);
    if (el) el.innerHTML = `<div class="detail-row"><span class="detail-key">Processed</span><span class="detail-val">${r.data.succeeded}/${r.data.total}</span></div>`;
  } else {
    toast('error', 'Failed', r.message);
  }
}

async function runLevirProcessing() {
  const split = document.getElementById('levir-process-split')?.value || 'train';
  const limit = document.getElementById('levir-process-limit')?.value || 3;
  toast('info', 'Processing', 'Running LEVIR pair processing...');
  const r = await apiFetch('/datasets/levir/process', { method: 'POST', body: JSON.stringify({ split, limit: parseInt(limit) }) });
  if (r.success) toast('success', 'Done', `Processed ${r.data?.results?.length || 0} pairs`);
  else toast('error', 'Failed', r.message);
}

async function loadLogs() {
  const r  = await apiFetch('/logs?n=100');
  const el = document.getElementById('log-terminal');
  if (!el) return;
  if (!r.success || !r.data.lines?.length) { el.innerHTML = '<div style="color:var(--text-muted)">No logs available</div>'; return; }
  el.innerHTML = r.data.lines.map(line => {
    let cls = '';
    if (line.includes('ERROR'))   cls = 'log-error';
    else if (line.includes('WARN')) cls = 'log-warn';
    else if (line.includes('INFO')) cls = 'log-info';
    return `<div class="${cls}">${escHtml(line.trim())}</div>`;
  }).join('');
  el.scrollTop = el.scrollHeight;
}

/* ══════════════════════════════════════════════════════════════
   PAGINATION HELPER
   ══════════════════════════════════════════════════════════════ */
function renderPagination(container, current, total, onPage) {
  if (total <= 1) { container.innerHTML = ''; return; }
  const btns = [];
  btns.push(`<button class="page-btn" onclick="(${onPage.toString()})(${Math.max(1, current - 1)})" ${current <= 1 ? 'disabled' : ''}>←</button>`);
  for (let p = Math.max(1, current - 2); p <= Math.min(total, current + 2); p++) {
    btns.push(`<button class="page-btn ${p === current ? 'active' : ''}" onclick="(${onPage.toString()})(${p})">${p}</button>`);
  }
  btns.push(`<button class="page-btn" onclick="(${onPage.toString()})(${Math.min(total, current + 1)})" ${current >= total ? 'disabled' : ''}>→</button>`);
  container.innerHTML = btns.join('');
}

/* ══════════════════════════════════════════════════════════════
   MODALS (open/close)
   ══════════════════════════════════════════════════════════════ */
function openModal(id) {
  const el = document.getElementById(id);
  if (el) { el.classList.remove('hidden'); }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('hidden');
}

function showConfirm(title, desc, icon, onConfirm) {
  setText('confirm-title', title);
  setText('confirm-desc',  desc);
  setText('confirm-icon',  icon || '⚠️');
  const btn = document.getElementById('btn-confirm-action');
  if (btn) {
    const newBtn = btn.cloneNode(true);
    btn.replaceWith(newBtn);
    newBtn.addEventListener('click', () => { onConfirm(); });
  }
  openModal('modal-confirm');
}

// Close modals on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// Close modals on ESC
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => closeModal(m.id));
    closeNotifPanel();
  }
});

/* ══════════════════════════════════════════════════════════════
   TOAST NOTIFICATIONS
   ══════════════════════════════════════════════════════════════ */
function toast(type, title, message = '', duration = 4000) {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const container = document.getElementById('toast-container');
  if (!container) return;

  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
    <div class="toast-content">
      <div class="toast-title">${escHtml(title)}</div>
      ${message ? `<div class="toast-msg">${escHtml(message)}</div>` : ''}
    </div>
    <button class="toast-close" onclick="this.closest('.toast').remove()">✕</button>`;
  container.appendChild(el);

  setTimeout(() => {
    el.classList.add('removing');
    setTimeout(() => el.remove(), 300);
  }, duration);
}

/* ══════════════════════════════════════════════════════════════
   POPULATE PROJECT SELECTS (for AI Models page)
   ══════════════════════════════════════════════════════════════ */
async function populateProjectSelects() {
  const r = await apiFetch('/projects');
  if (!r.success) return;
  const projects = r.data?.projects || [];
  const opts = `<option value="">— Select Project —</option>` +
    projects.map(p => `<option value="${p.project_id}">${escHtml(p.name)}</option>`).join('');

  ['m2-project-select'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts;
  });
}

/* ══════════════════════════════════════════════════════════════
   UTILITIES
   ══════════════════════════════════════════════════════════════ */
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setValue(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function escHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000)    return 'just now';
    if (diff < 3600000)  return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch { return iso.slice(0, 10); }
}

function formatBytes(bytes) {
  if (bytes < 1024)     return `${bytes} B`;
  if (bytes < 1048576)  return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}
