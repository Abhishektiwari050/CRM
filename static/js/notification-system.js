// Notification System - Modular Architecture
class NotificationService {
    constructor(api) {
        this.api = api;
        this.cache = new Map();
        this.listeners = new Set();
    }
    
    async fetch(endpoint, options = {}) {
        const cacheKey = `${endpoint}-${JSON.stringify(options)}`;
        
        if (this.cache.has(cacheKey) && Date.now() - this.cache.get(cacheKey).time < 300000) {
            return this.cache.get(cacheKey).data;
        }
        
        try {
            const data = await this.api(endpoint, options);
            this.cache.set(cacheKey, { data, time: Date.now() });
            this.notify('update', data);
            return data;
        } catch (error) {
            this.notify('error', error);
            return [];
        }
    }
    
    notify(event, data) {
        this.listeners.forEach(listener => listener(event, data));
    }
    
    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }
    
    clear() {
        this.cache.clear();
    }
}

class NotificationUI {
    constructor(container, config) {
        this.container = container;
        this.config = config;
        this.state = { items: [], filter: 'all', unread: 0 };
    }
    
    render(items) {
        this.state.items = items;
        this.state.unread = items.filter(item => !item.read).length;
        this.container.innerHTML = this.buildHTML();
    }
    
    buildHTML() {
        const { items, filter } = this.state;
        const filtered = filter === 'all' ? items : items.filter(item => item.type === filter);
        
        if (!filtered.length) {
            return `<div class="notif-empty"><i class="fas fa-inbox"></i><p>No notifications</p></div>`;
        }
        
        return filtered.map(item => this.buildItem(item)).join('');
    }
    
    buildItem(item) {
        const icon = this.config.icons[item.type] || 'bell';
        const color = this.config.colors[item.type] || '#3b82f6';
        
        return `<div class="notif-item ${item.read ? 'read' : ''}" data-id="${item.id}">
            <div class="notif-icon" style="background:${color}20;color:${color}">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="notif-content">
                <h4>${item.title}</h4>
                <p>${item.message}</p>
                <span class="notif-time">${this.formatTime(item.created_at)}</span>
            </div>
            ${item.action ? `<button class="notif-action" onclick="handleNotifAction('${item.id}')">${item.action}</button>` : ''}
        </div>`;
    }
    
    formatTime(timestamp) {
        const minutes = Math.floor((Date.now() - new Date(timestamp)) / (1000 * 60));
        
        if (minutes < 60) return `${minutes}m ago`;
        if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
        return `${Math.floor(minutes / 1440)}d ago`;
    }
    
    setFilter(filter) {
        this.state.filter = filter;
        this.render(this.state.items);
    }
    
    getUnread() {
        return this.state.unread;
    }
}

const NotificationConfig = {
    employee: {
        icons: {
            reminder: 'bell',
            alert: 'exclamation-triangle',
            info: 'info-circle'
        },
        colors: {
            reminder: '#f59e0b',
            alert: '#ef4444',
            info: '#3b82f6'
        }
    },
    manager: {
        icons: {
            reminder: 'bell',
            alert: 'exclamation-triangle',
            info: 'info-circle',
            report: 'file-alt'
        },
        colors: {
            reminder: '#f59e0b',
            alert: '#ef4444',
            info: '#6366f1',
            report: '#10b981'
        }
    }
};

async function initNotifications(role, containerId, endpoint) {
    const service = new NotificationService(async (endpoint, options) => {
        const token = localStorage.getItem('token');
        const response = await fetch(`${window.location.origin}/api/${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                ...options?.headers
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }
        
        const result = await response.json();
        return result.data || [];
    });
    
    const container = document.getElementById(containerId);
    const ui = new NotificationUI(container, NotificationConfig[role]);
    
    const data = await service.fetch(endpoint);
    ui.render(data);
    
    service.subscribe((event, data) => {
        if (event === 'update') {
            ui.render(data);
        }
    });
    
    // Refresh every 60 seconds
    setInterval(async () => {
        const data = await service.fetch(endpoint);
        ui.render(data);
    }, 60000);
    
    return { service, ui };
}

window.NotificationSystem = {
    init: initNotifications,
    Service: NotificationService,
    UI: NotificationUI,
    Config: NotificationConfig
};
