/**
 * ISLA Builders Dashboard
 * Frontend JavaScript for data fetching and display
 */

// Utility functions
function formatCurrency(amount) {
  if (!amount && amount !== 0) return '-';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
}

function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  const now = new Date();
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatDateTime(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  });
}

function createBadge(status) {
  const badge = document.createElement('span');
  badge.className = `badge ${status.replace(/[^a-z]/gi, '_').toLowerCase()}`;
  badge.textContent = status.replace(/_/g, ' ');
  return badge;
}

// API calls
async function fetchOverview() {
  try {
    const response = await fetch('/api/overview');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching overview:', error);
    return null;
  }
}

async function fetchJobs() {
  try {
    const response = await fetch('/api/jobs');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching jobs:', error);
    return { jobs: [] };
  }
}

async function fetchProposals() {
  try {
    const response = await fetch('/api/proposals');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching proposals:', error);
    return { proposals: [], summary: {} };
  }
}

async function fetchLeads() {
  try {
    const response = await fetch('/api/leads');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching leads:', error);
    return { leads: [] };
  }
}

async function fetchStats() {
  try {
    const response = await fetch('/api/stats');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    return { jobs: { open: 0, total: 0 } };
  }
}

// UI update functions
function updatePipelineFlow(overview) {
  if (!overview) return;
  
  const statuses = overview.leads?.by_status || {};
  
  document.getElementById('flow-new').textContent = statuses.new || 0;
  document.getElementById('flow-contacted').textContent = statuses.contacted || 0;
  document.getElementById('flow-scheduled').textContent = statuses.site_scheduled || 0;
  document.getElementById('flow-estimate').textContent = statuses.estimate_sent || 0;
  document.getElementById('flow-won').textContent = statuses.won || 0;
}

function updateMetrics(overview, proposals, jobs, stats) {
  // Pending proposals
  if (proposals?.summary) {
    document.getElementById('metric-pending').textContent = formatCurrency(proposals.summary.pending_value);
    document.getElementById('metric-pending-count').textContent = `${proposals.summary.pending_count || 0} proposals`;
  }
  
  // Won this month
  if (proposals?.summary) {
    document.getElementById('metric-won').textContent = formatCurrency(proposals.summary.won_value);
    document.getElementById('metric-won-count').textContent = `${proposals.summary.won_count || 0} jobs`;
  }
  
  // Active jobs - use stats API for accurate count from server
  if (stats?.jobs) {
    document.getElementById('metric-jobs').textContent = stats.jobs.open || 0;
    document.getElementById('metric-jobs-trend').textContent = `${stats.jobs.closed || 0} completed`;
  } else if (jobs?.count !== undefined) {
    // Fallback to jobs endpoint count
    document.getElementById('metric-jobs').textContent = jobs.count;
  }
  
  // Leads
  if (overview?.leads) {
    document.getElementById('metric-leads').textContent = overview.leads.total || 0;
    document.getElementById('metric-leads-new').textContent = `${overview.leads.new_this_week || 0} new this week`;
  }
}

function updateProposalsTable(proposals) {
  const tbody = document.getElementById('proposalsTable');
  
  if (!proposals?.proposals?.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" class="empty-state">
          <div class="empty-state-icon">📄</div>
          <div class="empty-state-text">No proposals yet</div>
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = proposals.proposals.slice(0, 5).map(p => `
    <tr>
      <td class="table-client">${escapeHtml(p.client)}</td>
      <td class="table-value">$${formatCurrency(p.total)}</td>
      <td><span class="badge ${p.status}">${p.status}</span></td>
      <td class="table-date">${formatDate(p.created)}</td>
    </tr>
  `).join('');
}

function updateLeadsTable(leads) {
  const tbody = document.getElementById('leadsTable');
  
  if (!leads?.leads?.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" class="empty-state">
          <div class="empty-state-icon">👥</div>
          <div class="empty-state-text">No leads yet</div>
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = leads.leads.slice(0, 5).map(l => {
    const name = l.contact?.name || 'Unknown';
    const service = l.project?.service || 'Other';
    const status = l.status || 'new';
    const created = l.source?.capturedAt || null;
    
    return `
      <tr>
        <td class="table-client">${escapeHtml(name)}</td>
        <td>${escapeHtml(service)}</td>
        <td><span class="badge ${status}">${status.replace(/_/g, ' ')}</span></td>
        <td class="table-date">${formatDate(created)}</td>
      </tr>
    `;
  }).join('');
}

function updateJobsTable(jobs) {
  const tbody = document.getElementById('jobsTable');
  
  // Handle API errors
  if (jobs?.error) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <div class="empty-state-text">Could not load jobs</div>
          <div class="empty-state-sub">${escapeHtml(jobs.error)}</div>
        </td>
      </tr>
    `;
    return;
  }
  
  if (!jobs?.jobs?.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">
          <div class="empty-state-icon">🏗️</div>
          <div class="empty-state-text">No active jobs</div>
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = jobs.jobs.slice(0, 8).map(j => `
    <tr>
      <td class="table-value">#${j.number || '-'}</td>
      <td class="table-client">${escapeHtml(j.name)}</td>
      <td>${escapeHtml(j.client)}</td>
      <td class="table-address">${escapeHtml(truncate(j.address, 40))}</td>
      <td><span class="badge ${j.status}">${j.status}</span></td>
    </tr>
  `).join('');
}

function showError(message) {
  // Show a toast/notification for errors
  console.error('Dashboard error:', message);
}

function updateLastUpdated() {
  const now = new Date();
  document.getElementById('lastUpdated').textContent = 
    `Updated ${now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
}

// Helper functions
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function truncate(str, length) {
  if (!str) return '';
  if (str.length <= length) return str;
  return str.substring(0, length) + '...';
}

// Main data loading
async function loadDashboard() {
  // Fetch all data in parallel
  const [overview, proposals, jobs, leads, stats] = await Promise.all([
    fetchOverview(),
    fetchProposals(),
    fetchJobs(),
    fetchLeads(),
    fetchStats()
  ]);
  
  // Update UI
  updatePipelineFlow(overview);
  updateMetrics(overview, proposals, jobs, stats);
  updateProposalsTable(proposals);
  updateLeadsTable(leads);
  updateJobsTable(jobs);
  updateLastUpdated();
}

// Refresh function for button
async function refreshData() {
  const button = document.querySelector('.btn-secondary');
  button.disabled = true;
  button.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
      <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
    Refreshing...
  `;
  
  await loadDashboard();
  
  button.disabled = false;
  button.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
    Refresh
  `;
}

// Mobile Navigation
function toggleMobileNav() {
  const nav = document.querySelector('.mobile-nav');
  const overlay = document.querySelector('.mobile-nav-overlay');
  nav.classList.add('active');
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeMobileNav() {
  const nav = document.querySelector('.mobile-nav');
  const overlay = document.querySelector('.mobile-nav-overlay');
  nav.classList.remove('active');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

// Close mobile nav on escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeMobileNav();
  }
});

// Close mobile nav when clicking a link
document.querySelectorAll('.mobile-nav .nav-item').forEach(item => {
  item.addEventListener('click', closeMobileNav);
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Only run loadDashboard if we're on the dashboard page
  if (typeof loadDashboard === 'function' && document.getElementById('metric-jobs')) {
    loadDashboard();
  }
});

// Auto-refresh every 5 minutes (only on dashboard)
if (document.getElementById('metric-jobs')) {
  setInterval(loadDashboard, 5 * 60 * 1000);
}
