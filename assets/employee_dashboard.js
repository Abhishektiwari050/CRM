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

            // Apply Default Sort: Overdue > Due Soon > Good (Priority), then Oldest Contact First (Round Robin)
            state.clients.sort((a, b) => {
                const statusA = calculateStatus(a.expiry_date, a.last_contact_date);
                const statusB = calculateStatus(b.expiry_date, b.last_contact_date);
                const pMap = { 'Overdue': 0, 'Due Soon': 1, 'Good': 2, 'Unknown': 3 };

                if (pMap[statusA] !== pMap[statusB]) {
                    return pMap[statusA] - pMap[statusB];
                }

                // If same status, sort by time since contact (Oldest first/Null first) to avoid starvation
                const timeA = a.last_contact_date ? new Date(a.last_contact_date).getTime() : 0;
                const timeB = b.last_contact_date ? new Date(b.last_contact_date).getTime() : 0;

                return timeA - timeB;
            });

            updateStats();
            renderCharts(state.clients); // Render Charts
            renderTable(state.clients);
        } catch (e) {
            console.error('Failed to load data', e);
            els.tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:red">Failed to load data. Please try again.</td></tr>`;
        }
    };

    // Render Charts
    const renderCharts = (clients) => {
        // Prepare Data
        const statusCounts = {
            good: clients.filter(c => calculateStatus(c.expiry_date, c.last_contact_date) === 'Good').length,
            due: clients.filter(c => calculateStatus(c.expiry_date, c.last_contact_date) === 'Due Soon').length,
            overdue: clients.filter(c => calculateStatus(c.expiry_date, c.last_contact_date) === 'Overdue').length
        };

        // Pie Chart: Client Status
        const ctxPie = document.getElementById('clientChart').getContext('2d');
        if (window.clientChartInstance) window.clientChartInstance.destroy();

        window.clientChartInstance = new Chart(ctxPie, {
            type: 'pie',
            data: {
                labels: ['Good', 'Due Soon', 'Overdue'],
                datasets: [{
                    data: [statusCounts.good, statusCounts.due, statusCounts.overdue],
                    backgroundColor: ['#22c55e', '#f97316', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: 'Client Status Distribution' }
                }
            }
        });

        // Bar Chart: Activity (Simulated based on last contact recency groups)
        // Since we don't have full activity history in client list, we'll bucket by "Days Since Contact"
        const buckets = { '< 7 Days': 0, '7-14 Days': 0, '15-30 Days': 0, '> 30 Days': 0 };
        clients.forEach(c => {
            if (!c.last_contact_date) { buckets['> 30 Days']++; return; }
            const diff = Math.floor((new Date() - new Date(c.last_contact_date)) / (1000 * 60 * 60 * 24));
            if (diff < 7) buckets['< 7 Days']++;
            else if (diff <= 14) buckets['7-14 Days']++;
            else if (diff <= 30) buckets['15-30 Days']++;
            else buckets['> 30 Days']++;
        });

        const ctxBar = document.getElementById('activityChart').getContext('2d');
        if (window.activityChartInstance) window.activityChartInstance.destroy();

        window.activityChartInstance = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: Object.keys(buckets),
                datasets: [{
                    label: 'Clients by Contact Recency',
                    data: Object.values(buckets),
                    backgroundColor: '#3b82f6',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Contact Recency' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
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

    // Helper: Calculate Status based on Recency only
    const calculateStatus = (expiryDate, lastContactDate) => {
        // Ignore expiryDate for status calculation as per new requirement
        if (!lastContactDate) return 'Overdue'; // Never contacted

        const daysSince = Math.floor((new Date() - new Date(lastContactDate)) / (1000 * 60 * 60 * 24));

        if (daysSince < 7) return 'Good';
        if (daysSince <= 14) return 'Due Soon';
        return 'Overdue'; // > 15 (covering gap of 15 if logic implies >= 15)
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
                        <button class="btn-primary" style="padding: 6px 12px; font-size: 12px;" onclick="Dashboard.openModal('${client.id}')">
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

    // Modal Logic
    const openModal = async (clientId) => {
        showLoading();
        try {
            // Fetch fresh details or find in state
            // Let's fetch to be safe and get full details if list is summary
            const client = await Auth.apiCall(`/api/clients/${clientId}`);
            if (!client) throw new Error("Client not found");

            const status = calculateStatus(client.expiry_date, client.last_contact_date);
            const statusBadge = `<span class="badge ${status === 'Good' ? 'active' : status === 'Overdue' ? 'red' : 'pending'}">${status}</span>`;

            const html = `
                <div class="detail-row"><div class="detail-label">Client Name</div><div class="detail-value">${client.name}</div></div>
                <div class="detail-row"><div class="detail-label">Status</div><div class="detail-value">${statusBadge}</div></div>
                <div class="detail-row"><div class="detail-label">Contact Email</div><div class="detail-value">${client.contact_email || '-'}</div></div>
                <div class="detail-row"><div class="detail-label">Contact Phone</div><div class="detail-value">${client.contact_phone || '-'}</div></div>
                <div class="detail-row"><div class="detail-label">City</div><div class="detail-value">${client.city || '-'}</div></div>
                <div class="detail-row"><div class="detail-label">Member ID</div><div class="detail-value">${client.member_id || '-'}</div></div>
                <div class="detail-row"><div class="detail-label">Products Posted</div><div class="detail-value">${client.products_posted || 0}</div></div>
                <div class="detail-row"><div class="detail-label">Expiry Date</div><div class="detail-value">${formatDate(client.expiry_date)}</div></div>
                <div class="detail-row"><div class="detail-label">Last Contact</div><div class="detail-value">${formatDate(client.last_contact_date)}</div></div>
                <div class="detail-row"><div class="detail-label">Joined On</div><div class="detail-value">${formatDate(client.created_at)}</div></div>
            `;

            document.getElementById('modalContent').innerHTML = html;
            document.getElementById('clientModal').classList.add('show');
            document.getElementById('modalTitle').textContent = client.name;
        } catch (e) {
            console.error(e);
            alert("Failed to load client details");
        }
        hideLoading();
    };

    const closeModal = () => {
        document.getElementById('clientModal').classList.remove('show');
    };

    // Close on background click
    document.getElementById('clientModal')?.addEventListener('click', (e) => {
        if (e.target === document.getElementById('clientModal')) closeModal();
    });

    // Public API
    return {
        init,
        refresh: async () => {
            showLoading();
            await loadData();
            hideLoading();
        },
        filterClients,
        sortData,
        openModal,
        closeModal
    };
})();

// Update button in renderTable to use Dashboard.openModal
// Hooking into logic by redefining renderTable internally or I need to update the big chunk again.
// Since I can't selectively patch inside a function easily without sending the whole function, I will rewrite the end of the file including the return block.

// Start
document.addEventListener('DOMContentLoaded', Dashboard.init);
