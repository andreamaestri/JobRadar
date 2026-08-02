const fallbackJobs = [
  { source_id: "sample-1", company: "Northstar Studio", title: "Senior Product Designer", location: "Berlin · Hybrid", remote: false, tags: ["Design", "Full time"], url: "https://www.arbeitnow.com/", posted_at: new Date().toISOString() },
  { source_id: "sample-2", company: "Open Field Labs", title: "Frontend Engineer", location: "Remote · Europe", remote: true, tags: ["Engineering", "TypeScript"], url: "https://www.arbeitnow.com/", posted_at: new Date().toISOString() },
  { source_id: "sample-3", company: "Good Company", title: "Community & Partnerships Lead", location: "Amsterdam · Hybrid", remote: false, tags: ["Community", "Growth"], url: "https://www.arbeitnow.com/", posted_at: new Date().toISOString() },
];

const grid = document.querySelector("#jobs-grid");
const count = document.querySelector("#job-count");
const status = document.querySelector("#connection-status");
const banner = document.querySelector("#offline-banner");
const bannerMessage = document.querySelector("#offline-message");
const remoteToggle = document.querySelector("#remote-only");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function formatDate(value) {
  if (!value) return "Recently posted";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "Recently posted";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date);
}

function renderJobs(jobs) {
  count.textContent = jobs.length;
  if (!jobs.length) {
    grid.innerHTML = '<div class="col-12"><div class="empty-state">No roles match this filter yet. Try widening your search.</div></div>';
    return;
  }
  grid.innerHTML = jobs.map(job => `
    <div class="col-md-6 col-xl-4">
      <article class="job-card card">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-4">
            <span class="job-company">${escapeHtml(job.company)}</span>
            ${job.remote ? '<span class="remote-badge">REMOTE</span>' : ''}
          </div>
          <h3 class="job-title mb-3">${escapeHtml(job.title)}</h3>
          <div class="job-meta mb-4">⌖ ${escapeHtml(job.location || "Location flexible")}<br>◷ Posted ${formatDate(job.posted_at)}</div>
          <div class="d-flex flex-wrap gap-2 mb-4">${(job.tags || []).slice(0, 3).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>
          <a class="job-link mt-auto" href="${escapeHtml(job.url)}" target="_blank" rel="noreferrer">View opportunity <span aria-hidden="true">↗</span></a>
        </div>
      </article>
    </div>`).join("");
}

function setStatus(mode, label) {
  status.className = `status-pill status-${mode}`;
  status.innerHTML = `<span class="status-dot"></span> ${label}`;
}

async function loadJobs({ showLoading = true } = {}) {
  if (showLoading) grid.innerHTML = '<div class="col-12"><div class="loading-state">Loading your next possibilities<span class="loading-dots">...</span></div></div>';
  try {
    const params = new URLSearchParams({ limit: "12", remote_only: remoteToggle.checked ? "true" : "false" });
    const response = await fetch(`/api/jobs/preview?${params}`, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const data = await response.json();
    renderJobs(data.jobs || []);
    setStatus("online", "Live feed");
    banner.classList.add("d-none");
  } catch (error) {
    const jobs = remoteToggle.checked ? fallbackJobs.filter(job => job.remote) : fallbackJobs;
    renderJobs(jobs);
    setStatus("offline", "Offline mode");
    bannerMessage.textContent = "The live feed is unavailable, so you’re seeing a starter feed. We’ll keep the page useful.";
    banner.classList.remove("d-none");
  }
}

document.querySelector("#refresh-button").addEventListener("click", () => loadJobs());
document.querySelector("#retry-button").addEventListener("click", () => loadJobs());
remoteToggle.addEventListener("change", () => loadJobs());
document.querySelector("#theme-toggle").addEventListener("click", () => {
  const root = document.documentElement;
  const dark = root.getAttribute("data-bs-theme") === "dark";
  root.setAttribute("data-bs-theme", dark ? "light" : "dark");
  document.querySelector("#theme-toggle").textContent = dark ? "☼" : "☾";
});

loadJobs();
