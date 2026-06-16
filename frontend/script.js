/**
 * script.js — Blood Bank Management System Frontend Logic
 *
 * Uses fetch() to communicate with the Flask API.
 * Updates the UI dynamically — no page reloads.
 */

const API = ""; // same-origin — served by Flask

// ── DOM References ──────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// Navigation
const navItems = $$(".nav-item");
const sections = $$(".section");
const headerTitle = $("#header-title");
const sidebar = $("#sidebar");
const mobileToggle = $("#mobile-toggle");

// Dashboard
const bloodGrid = $("#blood-grid");
const statTotalStock = $("#stat-total-stock");
const statDonorsQueue = $("#stat-donors-queue");
const statPending = $("#stat-pending");
const statLowStock = $("#stat-low-stock");

// Donor form
const donorForm = $("#donor-form");

// Donor queue
const queueVisual = $("#queue-visual");
const queueCountBadge = $("#queue-count-badge");
const donorsTbody = $("#donors-tbody");
const btnProcessDonor = $("#btn-process-donor");

// Requests
const requestForm = $("#request-form");
const requestsTbody = $("#requests-tbody");

// Match
const btnMatch = $("#btn-match");
const matchResults = $("#match-results");

// Report
const btnRefreshReport = $("#btn-refresh-report");

// Backup
const btnBackup = $("#btn-backup");
const btnRestore = $("#btn-restore");


// ═══════════════════════════════════════════════════════════════
//  NAVIGATION
// ═══════════════════════════════════════════════════════════════

const sectionTitles = {
    "dashboard": "Dashboard",
    "add-donor": "Add Donor",
    "donor-queue": "Donor Queue",
    "blood-requests": "Blood Requests",
    "match-donor": "Match Donor",
    "report": "Report",
    "backup-restore": "Backup & Restore",
};

function navigateTo(sectionName) {
    // Update nav
    navItems.forEach((item) => item.classList.remove("active"));
    const activeNav = document.querySelector(`[data-section="${sectionName}"]`);
    if (activeNav) activeNav.classList.add("active");

    // Update sections
    sections.forEach((s) => s.classList.remove("active"));
    const target = $(`#section-${sectionName}`);
    if (target) target.classList.add("active");

    // Update header
    headerTitle.textContent = sectionTitles[sectionName] || "Dashboard";

    // Close sidebar on mobile
    sidebar.classList.remove("open");

    // Load data for the section
    loadSectionData(sectionName);
}

navItems.forEach((item) => {
    item.addEventListener("click", () => {
        navigateTo(item.dataset.section);
    });
});

// Mobile toggle
mobileToggle.addEventListener("click", () => {
    sidebar.classList.toggle("open");
});

function loadSectionData(section) {
    switch (section) {
        case "dashboard":     loadDashboard(); break;
        case "donor-queue":   loadDonors(); break;
        case "blood-requests":loadRequests(); break;
        case "report":        loadReport(); break;
    }
}


// ═══════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════

function showToast(message, type = "info") {
    const container = $("#toast-container");
    const icons = { success: "✅", error: "❌", info: "ℹ️" };

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span> ${message}`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("hiding");
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}


// ═══════════════════════════════════════════════════════════════
//  API HELPERS
// ═══════════════════════════════════════════════════════════════

async function apiGet(url) {
    try {
        const res = await fetch(API + url);
        return await res.json();
    } catch (err) {
        showToast("Network error: " + err.message, "error");
        return null;
    }
}

async function apiPost(url, data = {}) {
    try {
        const res = await fetch(API + url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const json = await res.json();
        if (!res.ok) {
            showToast(json.error || "Request failed", "error");
            return null;
        }
        return json;
    } catch (err) {
        showToast("Network error: " + err.message, "error");
        return null;
    }
}


// ═══════════════════════════════════════════════════════════════
//  1. DASHBOARD
// ═══════════════════════════════════════════════════════════════

async function loadDashboard() {
    const [invData, reportData] = await Promise.all([
        apiGet("/inventory"),
        apiGet("/report"),
    ]);

    if (invData) {
        renderBloodGrid(invData.inventory);
    }

    if (reportData) {
        statTotalStock.textContent = reportData.total_stock;
        statDonorsQueue.textContent = reportData.total_donors_in_queue;
        statPending.textContent = reportData.pending_requests;
        const lowCount = Object.keys(reportData.low_stock_groups).length;
        statLowStock.textContent = lowCount;
    }
}

function renderBloodGrid(inventory) {
    bloodGrid.innerHTML = "";
    const groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"];

    groups.forEach((bg) => {
        const units = inventory[bg] || 0;
        const isLow = units < 5;

        const card = document.createElement("div");
        card.className = `blood-card${isLow ? " low-stock" : ""}`;
        card.innerHTML = `
            <div class="blood-type">${bg}</div>
            <div class="blood-units"><span>${units}</span> units</div>
            ${isLow ? '<div class="low-stock-badge">⚠ Low Stock</div>' : ""}
        `;
        bloodGrid.appendChild(card);
    });
}


// ═══════════════════════════════════════════════════════════════
//  2. ADD DONOR
// ═══════════════════════════════════════════════════════════════

donorForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
        name: $("#donor-name").value.trim(),
        age: parseInt($("#donor-age").value, 10),
        blood_group: $("#donor-blood-group").value,
        contact: $("#donor-contact").value.trim(),
        last_donation_date: $("#donor-date").value || null,
    };

    const result = await apiPost("/add-donor", data);
    if (result) {
        showToast(`Donor "${data.name}" added to queue (ID: ${result.donor.donor_id})`, "success");
        donorForm.reset();
    }
});


// ═══════════════════════════════════════════════════════════════
//  3. DONOR QUEUE
// ═══════════════════════════════════════════════════════════════

async function loadDonors() {
    const data = await apiGet("/all-donors");
    if (!data) return;

    const donors = data.donors;
    queueCountBadge.textContent = `${donors.length} donor${donors.length !== 1 ? "s" : ""}`;

    // Queue visual
    if (donors.length === 0) {
        queueVisual.innerHTML = `
            <div class="empty-state" style="width:100%">
                <div class="empty-icon">📭</div>
                <p>Queue is empty — no donors waiting</p>
            </div>`;
    } else {
        queueVisual.innerHTML = "";
        donors.forEach((d, i) => {
            if (i > 0) {
                const arrow = document.createElement("span");
                arrow.className = "queue-arrow";
                arrow.textContent = "→";
                queueVisual.appendChild(arrow);
            }
            const item = document.createElement("div");
            item.className = "queue-item";
            item.innerHTML = `
                <div class="q-name">${d.name}</div>
                <div class="q-blood">${d.blood_group}</div>
                <div class="q-id">ID #${d.donor_id}</div>`;
            queueVisual.appendChild(item);
        });
    }

    // Table
    if (donors.length === 0) {
        donorsTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--gray-400);padding:32px;">No donors registered yet</td></tr>`;
    } else {
        donorsTbody.innerHTML = donors.map((d) => `
            <tr>
                <td>${d.donor_id}</td>
                <td>${d.name}</td>
                <td>${d.age}</td>
                <td><span class="badge badge-blood">${d.blood_group}</span></td>
                <td>${d.contact}</td>
                <td>${d.last_donation_date || "—"}</td>
            </tr>`).join("");
    }
}

btnProcessDonor.addEventListener("click", async () => {
    const result = await apiPost("/process-donor");
    if (result) {
        showToast(result.message, "success");
        loadDonors();
    }
});


// ═══════════════════════════════════════════════════════════════
//  4. BLOOD REQUESTS
// ═══════════════════════════════════════════════════════════════

requestForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
        patient_name: $("#req-patient").value.trim(),
        blood_group: $("#req-blood-group").value,
        quantity: parseInt($("#req-quantity").value, 10),
        hospital_name: $("#req-hospital").value.trim(),
    };

    const result = await apiPost("/add-request", data);
    if (result) {
        showToast(`Request #${result.request.request_id} added for ${data.patient_name}`, "success");
        requestForm.reset();
        loadRequests();
    }
});

async function loadRequests() {
    const data = await apiGet("/all-requests");
    if (!data) return;

    const reqs = data.requests;

    if (reqs.length === 0) {
        requestsTbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--gray-400);padding:32px;">No blood requests yet</td></tr>`;
    } else {
        requestsTbody.innerHTML = reqs.map((r) => `
            <tr>
                <td>${r.request_id}</td>
                <td>${r.patient_name}</td>
                <td><span class="badge badge-blood">${r.blood_group}</span></td>
                <td>${r.quantity}</td>
                <td>${r.hospital_name}</td>
                <td><span class="badge badge-${r.status}">${r.status}</span></td>
                <td>
                    ${r.status === "pending"
                        ? `<button class="btn btn-success btn-sm" onclick="fulfillRequest(${r.request_id})">✓ Fulfill</button>`
                        : "—"}
                </td>
            </tr>`).join("");
    }
}

async function fulfillRequest(requestId) {
    const result = await apiPost("/fulfill-request", { request_id: requestId });
    if (result) {
        showToast(result.message, "success");
        loadRequests();
    }
}

// Expose to inline onclick
window.fulfillRequest = fulfillRequest;


// ═══════════════════════════════════════════════════════════════
//  5. MATCH DONOR
// ═══════════════════════════════════════════════════════════════

btnMatch.addEventListener("click", async () => {
    const bg = $("#match-blood-group").value;
    if (!bg) {
        showToast("Please select a blood group", "error");
        return;
    }

    const data = await apiGet(`/match-donor?blood_group=${encodeURIComponent(bg)}`);
    if (!data) return;

    matchResults.innerHTML = "";

    // Compatible stock card
    const stockCard = document.createElement("div");
    stockCard.className = "card";
    let stockHTML = `<div class="card-header"><h3>Compatible Blood Stock</h3>
        <span class="badge badge-blood">${data.total_compatible_units} total units</span></div>
        <div class="card-body"><div class="blood-grid">`;

    const stockEntries = Object.entries(data.compatible_stock);
    if (stockEntries.length === 0) {
        stockHTML += `<div class="empty-state"><div class="empty-icon">🚫</div><p>No compatible stock available</p></div>`;
    } else {
        stockEntries.forEach(([group, units]) => {
            stockHTML += `
                <div class="blood-card">
                    <div class="blood-type">${group}</div>
                    <div class="blood-units"><span>${units}</span> units</div>
                </div>`;
        });
    }
    stockHTML += `</div></div>`;
    stockCard.innerHTML = stockHTML;
    matchResults.appendChild(stockCard);

    // Compatible donors card
    const donorsCard = document.createElement("div");
    donorsCard.className = "card";
    let donorsHTML = `<div class="card-header"><h3>Compatible Donors in Queue</h3>
        <span class="badge badge-blood">${data.compatible_donors.length} donor(s)</span></div>
        <div class="card-body">`;

    if (data.compatible_donors.length === 0) {
        donorsHTML += `<div class="empty-state"><div class="empty-icon">👤</div><p>No matching donors in queue</p></div>`;
    } else {
        donorsHTML += `<div class="table-wrapper"><table><thead><tr>
            <th>ID</th><th>Name</th><th>Blood Group</th><th>Contact</th>
        </tr></thead><tbody>`;
        data.compatible_donors.forEach((d) => {
            donorsHTML += `<tr>
                <td>${d.donor_id}</td>
                <td>${d.name}</td>
                <td><span class="badge badge-blood">${d.blood_group}</span></td>
                <td>${d.contact}</td>
            </tr>`;
        });
        donorsHTML += `</tbody></table></div>`;
    }
    donorsHTML += `</div>`;
    donorsCard.innerHTML = donorsHTML;
    matchResults.appendChild(donorsCard);

    showToast(`Found ${data.total_compatible_units} compatible units and ${data.compatible_donors.length} donor(s) for ${bg}`, "info");
});


// ═══════════════════════════════════════════════════════════════
//  6. REPORT
// ═══════════════════════════════════════════════════════════════

async function loadReport() {
    const data = await apiGet("/report");
    if (!data) return;

    // Stats row
    const reportStats = $("#report-stats");
    reportStats.innerHTML = `
        <div class="stat-card">
            <div class="stat-icon green">👤</div>
            <div class="stat-info">
                <h4>Donors in Queue</h4>
                <div class="stat-value">${data.total_donors_in_queue}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon red">🩸</div>
            <div class="stat-info">
                <h4>Total Blood Stock</h4>
                <div class="stat-value">${data.total_stock}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon blue">📋</div>
            <div class="stat-info">
                <h4>Total Requests</h4>
                <div class="stat-value">${data.total_requests}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon amber">⏳</div>
            <div class="stat-info">
                <h4>Pending</h4>
                <div class="stat-value">${data.pending_requests}</div>
            </div>
        </div>`;

    // Detail cards
    const reportDetails = $("#report-details");

    // Stock summary
    let stockTable = `<table><thead><tr><th>Blood Group</th><th>Units</th></tr></thead><tbody>`;
    Object.entries(data.stock_summary).forEach(([bg, units]) => {
        const isLow = units < 5;
        stockTable += `<tr style="${isLow ? "color:var(--danger);font-weight:700;" : ""}">
            <td>${bg}</td><td>${units}${isLow ? " ⚠" : ""}</td></tr>`;
    });
    stockTable += `</tbody></table>`;

    // Low stock
    const lowGroups = Object.entries(data.low_stock_groups);
    let lowHTML = "";
    if (lowGroups.length === 0) {
        lowHTML = `<p style="color:var(--success);font-weight:600;">✅ All blood groups have adequate stock</p>`;
    } else {
        lowHTML = `<div class="blood-grid">`;
        lowGroups.forEach(([bg, units]) => {
            lowHTML += `<div class="blood-card low-stock">
                <div class="blood-type">${bg}</div>
                <div class="blood-units"><span>${units}</span> units</div>
                <div class="low-stock-badge">⚠ Critical</div>
            </div>`;
        });
        lowHTML += `</div>`;
    }

    // Request breakdown
    let reqBreakdown = `
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div>
                <span style="font-size:2rem;font-weight:800;color:var(--success);">${data.fulfilled_requests}</span>
                <div style="font-size:0.8rem;color:var(--gray-500);font-weight:600;">Fulfilled</div>
            </div>
            <div>
                <span style="font-size:2rem;font-weight:800;color:var(--warning);">${data.pending_requests}</span>
                <div style="font-size:0.8rem;color:var(--gray-500);font-weight:600;">Pending</div>
            </div>
        </div>`;

    reportDetails.innerHTML = `
        <div class="report-item">
            <h4>📊 Stock Summary</h4>
            <div class="table-wrapper">${stockTable}</div>
        </div>
        <div class="report-item">
            <h4>⚠️ Low Stock Alerts (below 5 units)</h4>
            ${lowHTML}
        </div>
        <div class="report-item">
            <h4>📋 Request Breakdown</h4>
            ${reqBreakdown}
        </div>`;
}

btnRefreshReport.addEventListener("click", loadReport);


// ═══════════════════════════════════════════════════════════════
//  7. BACKUP & RESTORE
// ═══════════════════════════════════════════════════════════════

btnBackup.addEventListener("click", async () => {
    const result = await apiPost("/backup");
    if (result) {
        showToast(result.message, "success");
    }
});

btnRestore.addEventListener("click", async () => {
    if (!confirm("Are you sure? This will overwrite current data with the backup.")) return;

    const result = await apiPost("/restore");
    if (result) {
        showToast(result.message, "success");
        // Reload current section data
        const activeNav = document.querySelector(".nav-item.active");
        if (activeNav) loadSectionData(activeNav.dataset.section);
    }
});


// ═══════════════════════════════════════════════════════════════
//  INIT — Load dashboard on first load
// ═══════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
});
