const Dashboard = (() => {
    // DOM Elements
    const els = {
        loading: document.getElementById('loadingOverlay'),
        userName: document.getElementById('userName'),
        stats: {
            total: document.getElementById('totalClients'),
            good: document.getElementById('goodClients'),
            due: document.getElementById('dueSoonClients'),
            overdue: document.getElementById('overdueClients')
        },
        tableBody: document.getElementById('clientsTableBody'),
        searchInput: document.getElementById('searchInput')
    };

    // State
    let state = {
        clients: [],
        user: null
    };

    // Utilities
    const showLoading = () => els.loading.classList.add('visible');
    const hideLoading = () => els.loading.classList.remove('visible');
    const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleDateString() : '-';

    // Initialization
    const init = async () => {
        showLoading();

        // 1. Check Auth & Get User
        const user = await Auth.checkAuth();
        if (!user) return; // Auth.checkAuth handles redirect

        // 2. Fetch Fresh User Data
        try {
            const freshUser = await Auth.apiCall('/api/auth/me');
            state.user = freshUser || user;
            Auth.setUser(state.user); // Update session
        } catch (e) {
            console.warn('Failed to refresh user profile', e);
            state.user = user;
        }

        // 3. Role Check
        if (state.user.role !== 'employee') {
            window.location.href = '/manager_dashboard_page/code.html';
            return;
        }

        // 4. Render UI
        els.userName.textContent = state.user.name || 'Employee';
        Sidebar.init('employee', 'dashboard');

        // 5. Load Data
        await loadData();

        hideLoading();
    };

    // Data Loading
    const loadData = async () => {
        try {
            const res = await Auth.apiCall('/api/clients');
            state.clients = res.data || [];

            updateStats();
            renderTable(state.clients);
        } catch (e) {
            console.error('Failed to load data', e);
            els.tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:red">Failed to load data. Please try again.</td></tr>`;
        }
    };

    // Render Stats
    const updateStats = () => {
        const total = state.clients.length;
        const good = state.clients.filter(c => calculateStatus(c.expiry_date, c.last_contact_date) === 'Good').length;
        const due = state.clients.filter(c => calculateStatus(c.expiry_date, c.last_contact_date) === 'Due Soon').length;
        const overdue = state.clients.filter(c => calculateStatus(c.expiry_date, c.last_contact_date) === 'Overdue').length;

        animateValue(els.stats.total, total);
        animateValue(els.stats.good, good);
        animateValue(els.stats.due, due);
        animateValue(els.stats.overdue, overdue);
    };

    // Helper: Calculate Status
    const calculateStatus = (expiryDate, lastContactDate) => {
        if (!expiryDate) return 'Unknown';
        const days = Math.ceil((new Date(expiryDate) - new Date()) / (1000 * 60 * 60 * 24));

        // Check 1: Expiry
        if (days < 0) return 'Overdue';

        // Check 2: Never Contacted (treat as Overdue for stats/display)
        if (!lastContactDate) return 'Overdue';

        if (days <= 30) return 'Due Soon';
        return 'Good';
    };

    // Helper: Animate Numbers
    const animateValue = (element, end) => {
        const start = parseInt(element.textContent) || 0;
        if (start === end) return;

        const duration = 1000;
        const startTime = performance.now();

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out quart
            const ease = 1 - Math.pow(1 - progress, 4);

            element.textContent = Math.floor(start + (end - start) * ease);

            if (progress < 1) requestAnimationFrame(update);
            else element.textContent = end;
        };

        requestAnimationFrame(update);
    };

    // Sorting
    const sortData = (field) => {
        const direction = state.sortField === field && state.sortDirection === 'asc' ? 'desc' : 'asc';
        state.sortField = field;
        state.sortDirection = direction;

        state.clients.sort((a, b) => {
            let valA = a[field] || '';
            let valB = b[field] || '';

            // Handle dates
            if (field === 'expiry_date' || field === 'last_contact_date') {
                valA = new Date(valA || 0).getTime();
                valB = new Date(valB || 0).getTime();
            }
            // Handle status priority
            if (field === 'status') {
                const priority = { 'Overdue': 1, 'Due Soon': 2, 'Good': 3, 'Unknown': 4 };
                valA = priority[calculateStatus(a.expiry_date, a.last_contact_date)] || 99;
                valB = priority[calculateStatus(b.expiry_date, b.last_contact_date)] || 99;
            }

            if (valA < valB) return direction === 'asc' ? -1 : 1;
            if (valA > valB) return direction === 'asc' ? 1 : -1;
            return 0;
        });

        renderTable(state.clients);
        updateSortIcons(field, direction);
    };

    const updateSortIcons = (field, direction) => {
        document.querySelectorAll('th i').forEach(i => i.className = 'fas fa-sort');
        const th = document.querySelector(`th[data-sort="${field}"]`);
        if (th) {
            const icon = th.querySelector('i');
            if (icon) icon.className = `fas fa-sort-${direction === 'asc' ? 'up' : 'down'}`;
        }
    };

    // Render Table
    const renderTable = (clients) => {
        if (clients.length === 0) {
            els.tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 32px;">No clients found.</td></tr>`;
            return;
        }

        els.tableBody.innerHTML = clients.map(client => {
            const status = calculateStatus(client.expiry_date, client.last_contact_date);
            const statusClass = status.toLowerCase().replace(' ', '-');
            const badgeClass = status === 'Good' ? 'active' : status === 'Overdue' ? 'red' : 'pending';

            return `
                <tr>
                    <td>
                        <div style="font-weight: 500;">${client.name}</div>
                        <div style="font-size: 12px; color: var(--text-muted);">ID: ${client.id.slice(0, 8)}</div>
                    </td>
                    <td>
                        <div>${client.contact_email || '-'}</div>
                        <div style="font-size: 12px; color: var(--text-muted);">${client.contact_phone || '-'}</div>
                    </td>
                    <td><span class="badge ${badgeClass}">${status}</span></td>
                    <td>${formatDate(client.last_contact_date)}</td>
                    <td>${formatDate(client.expiry_date)}</td>
                    <td>
                        <button class="btn-primary" style="padding: 6px 12px; font-size: 12px;" onclick="window.location.href='/client_details_page/code.html?id=${client.id}'">
                            View
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    };

    // Filter Clients
    const filterClients = () => {
        const term = els.searchInput.value.toLowerCase();
        const filtered = state.clients.filter(c =>
            c.name.toLowerCase().includes(term) ||
            (c.contact_email && c.contact_email.toLowerCase().includes(term))
        );
        renderTable(filtered);
    };

    // Public API
    return {
        init,
        refresh: async () => {
            showLoading();
            await loadData();
            hideLoading();
        },
        filterClients,
        sortData
    };
})();

// Start
document.addEventListener('DOMContentLoaded', Dashboard.init);
