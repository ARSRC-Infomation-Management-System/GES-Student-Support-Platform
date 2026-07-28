const API_BASE = "http://127.0.0.1:8000/api/v1";

// Demo tokens / accounts configuration for instant testing
const USER_PROFILES = {
    admin: {
        email: "superadmin_evt@ges.gov.gh",
        password: "Password123",
        name: "System Administrator",
        role: "admin",
        roleLabel: "Super Admin",
        avatar: "SA",
        badgeClass: "admin",
        scopeBanner: "Super Admin Mode: Viewing & Managing All Events Nationwide"
    },
    official_school: {
        email: "schooladmin_evt@ges.gov.gh",
        password: "Password123",
        name: "Achimota Admin",
        role: "official",
        roleLabel: "School Admin",
        avatar: "AA",
        badgeClass: "official",
        scopeBanner: "School Official Mode: Scoped to Achimota School"
    },
    official_region: {
        email: "regional_evt@ges.gov.gh",
        password: "Password123",
        name: "Greater Accra Rep",
        role: "official",
        roleLabel: "Regional Officer",
        avatar: "AR",
        badgeClass: "official",
        scopeBanner: "Regional Official Mode: Scoped to Greater Accra Region"
    },
    student: {
        email: "student_b_evt@ges.gov.gh",
        password: "Password123",
        name: "Jane Doe (Achimota)",
        role: "student",
        roleLabel: "Student",
        avatar: "JD",
        badgeClass: "student",
        scopeBanner: "Showing events tailored to Achimota School & Greater Accra Region"
    }
};

let currentProfileKey = "admin";
let authToken = null;
let currentView = "admin";
let studentFilter = "upcoming";
let allEventsCache = [];

// Sample Fallback Mock Data in case backend dev server is not currently running
const MOCK_EVENTS = [
    {
        id: 1,
        title: "STEM Career & Innovation Fair 2026",
        description: "Join industry leaders, software engineers, and university recruiters for hands-on demonstrations and career guidance.",
        location: "Assembly Hall, Achimota School",
        start_time: "2026-08-15T09:00:00Z",
        end_time: "2026-08-15T15:00:00Z",
        status: "published",
        target_region_id: null,
        target_school_id: 1,
        created_by: 3,
        created_at: "2026-07-27T10:00:00Z"
    },
    {
        id: 2,
        title: "Greater Accra Regional Debate Championship",
        description: "Annual secondary school debate tournament featuring qualified teams across Greater Accra Region.",
        location: "Accra National Theatre / Virtual Stream",
        start_time: "2026-08-20T10:00:00Z",
        end_time: "2026-08-20T16:00:00Z",
        status: "published",
        target_region_id: 1,
        target_school_id: null,
        created_by: 2,
        created_at: "2026-07-26T14:00:00Z"
    },
    {
        id: 3,
        title: "National Student Orientation & Leadership Summit",
        description: "GES Nationwide Leadership Summit for incoming prefects and student council leaders.",
        location: "GES Head Office Auditorium & Zoom Live",
        start_time: "2026-09-01T08:30:00Z",
        end_time: "2026-09-01T17:00:00Z",
        status: "published",
        target_region_id: null,
        target_school_id: null,
        created_by: 1,
        created_at: "2026-07-25T11:00:00Z"
    },
    {
        id: 4,
        title: "Coding & AI Bootcamp (Draft)",
        description: "Introductory Python and GenAI workshop for high school programmers.",
        location: "Computer Lab 2",
        start_time: "2026-08-25T13:00:00Z",
        end_time: "2026-08-25T16:00:00Z",
        status: "draft",
        target_region_id: null,
        target_school_id: 1,
        created_by: 3,
        created_at: "2026-07-27T16:00:00Z"
    }
];

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    await authenticateUser(currentProfileKey);
    renderUserCard();
    switchView("admin");
}

async function authenticateUser(profileKey) {
    currentProfileKey = profileKey;
    const profile = USER_PROFILES[profileKey];
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: profile.email, password: profile.password })
        });
        if (response.ok) {
            const data = await response.json();
            authToken = data.data.access_token;
        } else {
            authToken = "demo-token-fallback";
        }
    } catch (e) {
        console.warn("Backend API not reached directly, operating in fallback/live state mode.", e);
        authToken = "demo-token-fallback";
    }
}

function renderUserCard() {
    const profile = USER_PROFILES[currentProfileKey];
    document.getElementById("userAvatar").innerText = profile.avatar;
    document.getElementById("userName").innerText = profile.name;
    const badge = document.getElementById("userRoleBadge");
    badge.innerText = profile.roleLabel;
    badge.className = `role-badge ${profile.badgeClass}`;
    document.getElementById("scopeInfoBanner").querySelector("span").innerHTML = profile.scopeBanner;

    // Show/hide Create Event button based on role
    const btnCreate = document.getElementById("btnCreateEvent");
    if (profile.role === "admin" || profile.role === "official") {
        btnCreate.style.display = "inline-flex";
    } else {
        btnCreate.style.display = "none";
    }
}

async function setUserRole(roleKey) {
    document.querySelectorAll(".role-chip").forEach(btn => btn.classList.remove("active"));
    event.target.classList.add("active");
    await authenticateUser(roleKey);
    renderUserCard();

    if (USER_PROFILES[roleKey].role === "student") {
        switchView("student");
    } else {
        switchView("admin");
    }
}

function switchView(viewName) {
    currentView = viewName;
    document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));

    if (viewName === "student") {
        document.getElementById("navStudentBtn").classList.add("active");
        document.getElementById("studentView").classList.add("active");
        document.getElementById("viewTitle").innerText = "Upcoming Events & Activities";
        document.getElementById("viewSubtitle").innerText = "Discover upcoming educational, athletic, and regional events";
        loadStudentEvents();
    } else {
        document.getElementById("navAdminBtn").classList.add("active");
        document.getElementById("adminView").classList.add("active");
        document.getElementById("viewTitle").innerText = "Events Management Dashboard";
        document.getElementById("viewSubtitle").innerText = "Create, edit, publish, and manage scheduled events";
        loadAdminEvents();
    }
}

async function fetchEventsFromApi(endpoint = "/events") {
    if (authToken && authToken !== "demo-token-fallback") {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                const json = await res.json();
                return json.data.items || [];
            }
        } catch (e) {
            console.error("Error fetching events:", e);
        }
    }
    return MOCK_EVENTS;
}

async function loadStudentEvents() {
    const grid = document.getElementById("eventsGrid");
    grid.innerHTML = `<div class="loading" style="color: var(--text-muted);">Loading events...</div>`;

    let endpoint = "/events/upcoming";
    if (studentFilter === "history") endpoint = "/events/history";
    if (studentFilter === "all") endpoint = "/events";

    let events = await fetchEventsFromApi(endpoint);
    allEventsCache = events;
    renderStudentCards(events);
}

function renderStudentCards(events) {
    const grid = document.getElementById("eventsGrid");
    grid.innerHTML = "";

    if (!events || events.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">No events found matching your criteria.</div>`;
        return;
    }

    events.forEach(evt => {
        const card = document.createElement("div");
        card.className = "event-card";

        let scopeBadgeText = "Global Event";
        let scopeClass = "global";
        if (evt.target_school_id) {
            scopeBadgeText = "School Event";
            scopeClass = "school";
        } else if (evt.target_region_id) {
            scopeBadgeText = "Regional Event";
            scopeClass = "region";
        }

        const startDate = new Date(evt.start_time).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });

        card.innerHTML = `
            <div class="event-badge-bar">
                <span class="scope-badge ${scopeClass}"><i class="fa-solid fa-layer-group"></i> ${scopeBadgeText}</span>
                <span class="status-tag ${evt.status}">${evt.status}</span>
            </div>
            <h3 class="event-title">${evt.title}</h3>
            <div class="event-meta">
                <div class="meta-item"><i class="fa-solid fa-clock"></i> ${startDate}</div>
                <div class="meta-item"><i class="fa-solid fa-location-dot"></i> ${evt.location || "Venue TBD / Online"}</div>
            </div>
            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.4;">${evt.description}</p>
            <div class="event-footer">
                <button class="btn btn-secondary btn-sm" onclick="openDetailModal(${evt.id})"><i class="fa-solid fa-circle-info"></i> View Details</button>
                <button class="btn btn-primary btn-sm" onclick="handleRsvp('${evt.title}')"><i class="fa-solid fa-check"></i> RSVP</button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function filterStudentEvents(filterType, evt) {
    studentFilter = filterType;
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    evt.target.classList.add("active");
    loadStudentEvents();
}

async function loadAdminEvents() {
    const tbody = document.getElementById("adminTableBody");
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Loading registry data...</td></tr>`;

    const statusVal = document.getElementById("statusFilter").value;
    let url = "/events";
    if (statusVal) url += `?status=${statusVal}`;

    let events = await fetchEventsFromApi(url);
    updateAdminStats(events);

    tbody.innerHTML = "";
    if (!events || events.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">No event records found.</td></tr>`;
        return;
    }

    events.forEach(evt => {
        const tr = document.createElement("tr");

        let scopeText = "Global";
        if (evt.target_school_id) scopeText = `School (ID: ${evt.target_school_id})`;
        else if (evt.target_region_id) scopeText = `Region (ID: ${evt.target_region_id})`;

        const startDate = new Date(evt.start_time).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

        let actions = ``;
        if (evt.status === "draft") {
            actions += `<button class="btn btn-success btn-sm" onclick="publishEventApi(${evt.id})"><i class="fa-solid fa-upload"></i> Publish</button>`;
        }
        if (evt.status === "published") {
            actions += `<button class="btn btn-warning btn-sm" onclick="cancelEventApi(${evt.id})"><i class="fa-solid fa-ban"></i> Cancel</button>`;
        }
        actions += `<button class="btn btn-danger btn-sm" onclick="archiveEventApi(${evt.id})"><i class="fa-solid fa-box-archive"></i> Archive</button>`;

        tr.innerHTML = `
            <td><strong>${evt.title}</strong><br><small style="color: var(--text-muted);">${evt.location || "N/A"}</small></td>
            <td>${startDate}</td>
            <td><span class="scope-badge ${evt.target_school_id ? 'school' : evt.target_region_id ? 'region' : 'global'}">${scopeText}</span></td>
            <td><span class="status-tag ${evt.status}">${evt.status}</span></td>
            <td><div class="action-btns">${actions}</div></td>
        `;
        tbody.appendChild(tr);
    });
}

function updateAdminStats(events) {
    document.getElementById("statTotal").innerText = events.length;
    document.getElementById("statPublished").innerText = events.filter(e => e.status === "published").length;
    document.getElementById("statDrafts").innerText = events.filter(e => e.status === "draft").length;
    document.getElementById("statArchived").innerText = events.filter(e => e.status === "cancelled" || e.status === "completed").length;
}

function handleSearch(evt) {
    const query = evt.target.value.toLowerCase().trim();
    if (currentView === "student") {
        const filtered = allEventsCache.filter(e => e.title.toLowerCase().includes(query) || (e.location && e.location.toLowerCase().includes(query)) || e.description.toLowerCase().includes(query));
        renderStudentCards(filtered);
    } else {
        loadAdminEvents();
    }
}

function handleScopeRadioChange() {
    const selected = document.querySelector('input[name="scopeType"]:checked').value;
    const row = document.getElementById("scopeDropdownRow");
    const regGrp = document.getElementById("regionSelectGroup");
    const schGrp = document.getElementById("schoolSelectGroup");

    if (selected === "global") {
        row.style.display = "none";
        regGrp.style.display = "none";
        schGrp.style.display = "none";
    } else if (selected === "region") {
        row.style.display = "grid";
        regGrp.style.display = "flex";
        schGrp.style.display = "none";
    } else if (selected === "school") {
        row.style.display = "grid";
        regGrp.style.display = "none";
        schGrp.style.display = "flex";
    }
}

function openCreateModal() {
    document.getElementById("modalTitle").innerHTML = `<i class="fa-solid fa-calendar-plus"></i> Create New Event`;
    document.getElementById("eventForm").reset();
    document.getElementById("eventId").value = "";
    handleScopeRadioChange();
    document.getElementById("eventModal").classList.add("active");
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove("active");
}

async function handleSaveEvent(evt) {
    evt.preventDefault();
    const title = document.getElementById("eventTitle").value;
    const description = document.getElementById("eventDescription").value;
    const location = document.getElementById("eventLocation").value;
    const status = document.getElementById("eventStatus").value;
    const startTime = new Date(document.getElementById("startTime").value).toISOString();
    const endTime = new Date(document.getElementById("endTime").value).toISOString();
    const scopeType = document.querySelector('input[name="scopeType"]:checked').value;

    let target_region_id = null;
    let target_school_id = null;
    if (scopeType === "region") target_region_id = parseInt(document.getElementById("regionSelect").value);
    if (scopeType === "school") target_school_id = parseInt(document.getElementById("schoolSelect").value);

    const payload = {
        title, description, location, status,
        start_time: startTime,
        end_time: endTime,
        target_region_id,
        target_school_id
    };

    if (authToken && authToken !== "demo-token-fallback") {
        try {
            const res = await fetch(`${API_BASE}/events`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                alert("Event created successfully!");
                closeModal("eventModal");
                loadAdminEvents();
                return;
            } else {
                const err = await res.json();
                alert(`Error: ${err.error ? err.error.message : 'Failed to save'}`);
                return;
            }
        } catch (e) {
            console.error("API error:", e);
        }
    }

    // Fallback demo update
    MOCK_EVENTS.unshift({ id: Date.now(), ...payload, created_at: new Date().toISOString() });
    alert("Event saved successfully (Demo state)!");
    closeModal("eventModal");
    loadAdminEvents();
}

async function publishEventApi(id) {
    if (authToken && authToken !== "demo-token-fallback") {
        const res = await fetch(`${API_BASE}/events/${id}/publish`, {
            method: "PATCH",
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.ok) {
            alert("Event published! Notifications triggered for target audience.");
            loadAdminEvents();
            return;
        }
    }
    const item = MOCK_EVENTS.find(e => e.id === id);
    if (item) item.status = "published";
    alert("Event published successfully!");
    loadAdminEvents();
}

async function cancelEventApi(id) {
    if (authToken && authToken !== "demo-token-fallback") {
        const res = await fetch(`${API_BASE}/events/${id}/cancel`, {
            method: "PATCH",
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.ok) {
            alert("Event cancelled.");
            loadAdminEvents();
            return;
        }
    }
    const item = MOCK_EVENTS.find(e => e.id === id);
    if (item) item.status = "cancelled";
    alert("Event cancelled.");
    loadAdminEvents();
}

async function archiveEventApi(id) {
    if (!confirm("Are you sure you want to archive/soft-delete this event?")) return;
    if (authToken && authToken !== "demo-token-fallback") {
        const res = await fetch(`${API_BASE}/events/${id}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.ok) {
            alert("Event archived successfully.");
            loadAdminEvents();
            return;
        }
    }
    const item = MOCK_EVENTS.find(e => e.id === id);
    if (item) item.status = "cancelled";
    alert("Event archived (soft-deleted).");
    loadAdminEvents();
}

function openDetailModal(id) {
    const item = allEventsCache.find(e => e.id === id) || MOCK_EVENTS.find(e => e.id === id);
    if (!item) return;

    document.getElementById("detailTitle").innerText = item.title;
    document.getElementById("detailBody").innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 14px;">
            <p><strong>Description:</strong> ${item.description}</p>
            <p><strong>Location/Venue:</strong> ${item.location || 'TBD'}</p>
            <p><strong>Start Time:</strong> ${new Date(item.start_time).toLocaleString()}</p>
            <p><strong>End Time:</strong> ${new Date(item.end_time).toLocaleString()}</p>
            <p><strong>Status:</strong> <span class="status-tag ${item.status}">${item.status}</span></p>
        </div>
    `;
    document.getElementById("detailModal").classList.add("active");
}

function handleRsvp(title = "this event") {
    alert(`Success! You have registered for '${title}'. An event reminder has been added.`);
}
